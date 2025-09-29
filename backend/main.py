import os
from datetime import datetime
from typing import Any, Dict

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from dotenv import load_dotenv
import boto3
from boto3.dynamodb.conditions import Key
import qrcode
import io

from schemas import (
    Consent, UploadUrlRequest, SubmissionRequest,
    AnonAuthResponse, UploadUrlResponse
)
from utils import generate_participant_id, build_object_key, env

load_dotenv()

REGION = os.getenv("AWS_REGION", "ap-southeast-2")
S3_BUCKET = env("S3_BUCKET")
DDB_TABLE = env("DDB_TABLE")
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*")

session = boto3.session.Session(region_name=REGION)
s3 = session.client('s3')
ddb = session.resource('dynamodb').Table(DDB_TABLE)

app = FastAPI(title="Iris Data Collection API")

# CORS (lock this down in production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in ALLOWED_ORIGINS.split(',')] if ALLOWED_ORIGINS != "*" else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/v1/health")
def health():
    return {"ok": True, "time": datetime.utcnow().isoformat()}

@app.post("/v1/auth/anon", response_model=AnonAuthResponse)
def auth_anon():
    pid = generate_participant_id()
    return {"participant_id": pid}

@app.post("/v1/upload-url", response_model=UploadUrlResponse)
def get_upload_url(req: UploadUrlRequest):
    if not req.participant_id:
        raise HTTPException(400, "participant_id required")
    key = build_object_key(req.participant_id, req.filename)

    # Use POST policy to allow form-data upload; expires in 120s
    conditions = [
        {"bucket": S3_BUCKET},
        ["starts-with", "$key", key.split('/')[0] + "/"],
        {"acl": "private"},
        ["content-length-range", 0, 8 * 1024 * 1024],  # 8 MB cap (adjust)
        {"Content-Type": req.contentType}
    ]
    resp = s3.generate_presigned_post(
        Bucket=S3_BUCKET,
        Key=key,
        Fields={"acl": "private", "Content-Type": req.contentType},
        Conditions=conditions,
        ExpiresIn=120,
    )
    return {"url": resp["url"], "fields": resp["fields"], "object_key": key}

@app.post("/v1/submissions")
def create_submission(body: SubmissionRequest, request: Request):
    if not (body.consent.over18 and body.consent.data_storage):
        raise HTTPException(400, "Explicit consent (over18 + data_storage) is required")

    now = datetime.utcnow().isoformat()
    ip_hash = hash(request.client.host) if request.client else None

    item: Dict[str, Any] = {
        "participant_id": body.participant_id,
        "submission_id": now + "#" + os.urandom(4).hex(),
        "s3_key": body.object_key,
        "self_reports": body.self_reports,
        "free_text_note": (body.free_text_note or "")[:500],
        "meta": {
            "device_type": body.meta.device_type if body.meta else None,
            "lighting": body.meta.lighting if body.meta else None,
            "capture_quality_score": body.meta.capture_quality_score if body.meta else None,
        },
        "consent": body.consent.model_dump(),
        "created_at": now,
        "ip_hash": ip_hash,
        "user_agent": request.headers.get("user-agent", "")[:200]
    }

    ddb.put_item(Item=item)
    return {"ok": True, "submission_id": item["submission_id"]}

@app.post("/v1/withdraw")
def withdraw_all(data: Dict[str, str]):
    pid = data.get("participant_id")
    if not pid:
        raise HTTPException(400, "participant_id required")

    resp = ddb.query(KeyConditionExpression=Key('participant_id').eq(pid))
    to_delete = resp.get('Items', [])

    for it in to_delete:
        key = it.get("s3_key")
        if key:
            try:
                s3.delete_object(Bucket=S3_BUCKET, Key=key)
            except Exception:
                pass
        ddb.delete_item(Key={"participant_id": pid, "submission_id": it["submission_id"]})

    return {"ok": True, "deleted": len(to_delete)}

@app.get("/v1/qr")
def qr(url: str):
    """Return a PNG QR code for the provided URL."""
    qr_img = qrcode.make(url)
    buf = io.BytesIO()
    qr_img.save(buf, format='PNG')
    buf.seek(0)
    return StreamingResponse(buf, media_type="image/png")
