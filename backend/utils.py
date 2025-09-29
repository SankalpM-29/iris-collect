import os
import uuid

def generate_participant_id() -> str:
    return str(uuid.uuid4())

# Object key helper: raw/{participant}/{uuid}.{ext}
def build_object_key(participant_id: str, filename: str) -> str:
    base, dot, ext = filename.rpartition('.')
    ext = ext.lower() if dot else 'jpg'
    return f"raw/{participant_id}/{uuid.uuid4()}.{ext}"

def env(name: str, default: str = "") -> str:
    val = os.getenv(name, default)
    if not val:
        raise RuntimeError(f"Missing required env var: {name}")
    return val
