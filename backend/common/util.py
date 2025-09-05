import hashlib
import uuid

def new_uuid() -> str:
    return str(uuid.uuid4())

def dedupe_key(*parts) -> str:
    """Хеш-ключ для дедупликации."""
    return hashlib.sha256("|".join(map(str, parts)).encode()).hexdigest()
