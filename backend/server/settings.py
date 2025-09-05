from typing import List, Union
import os
from pydantic_settings import BaseSettings
from pydantic import field_validator

class Settings(BaseSettings):
    app_name: str = "SIEM Security System"
    allowed_origins: Union[List[str], str] = ["*"]
    database_url: str = os.getenv("DATABASE_URL", "postgresql+psycopg://user:pass@postgres:5432/db")
    jwt_secret: str = os.getenv("JWT_SECRET", "change_me")
    jwt_algorithm: str = "HS256"
    jwt_ttl_min: int = int(os.getenv("JWT_TTL_MIN", "60"))

    @field_validator("allowed_origins", mode="before")
    @classmethod
    def _coerce_allowed_origins(cls, v):
        if v is None: return ["*"]
        if isinstance(v, list): return v
        if isinstance(v, str):
            parts = [s.strip() for s in v.split(",") if s.strip()]
            return parts or ["*"]
        return ["*"]

settings = Settings()
