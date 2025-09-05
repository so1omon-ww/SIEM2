from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import text

def get_password_hash_by_username(session: Session, username: str) -> Optional[str]:
    row = session.execute(
        text("SELECT password_hash FROM security_system.users WHERE username=:u LIMIT 1"),
        {"u": username},
    ).first()
    return row[0] if row else None
