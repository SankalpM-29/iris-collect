from pydantic import BaseModel, Field
from typing import List, Optional, Dict

class Consent(BaseModel):
    over18: bool
    data_storage: bool
    future_research: bool = False
    recontact_ok: bool = False
    consent_version: str = "v1"

class UploadUrlRequest(BaseModel):
    filename: str
    contentType: str
    participant_id: str

class SubmissionMeta(BaseModel):
    device_type: Optional[str] = None
    lighting: Optional[str] = None
    capture_quality_score: Optional[float] = None

class SubmissionRequest(BaseModel):
    participant_id: str
    object_key: str
    self_reports: List[str] = Field(default_factory=list)
    free_text_note: Optional[str] = None
    meta: Optional[SubmissionMeta] = None
    consent: Consent

class AnonAuthResponse(BaseModel):
    participant_id: str

class UploadUrlResponse(BaseModel):
    url: str
    fields: Dict[str, str]
    object_key: str
