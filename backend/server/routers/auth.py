from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy import text
from ...common.db import get_session
from ..repositories.users_repo import get_password_hash_by_username
import bcrypt, jwt, os, secrets, hashlib

SECRET = os.getenv("JWT_SECRET", "dev-secret-please-change")
ALGO = "HS256"
TTL_MIN = int(os.getenv("JWT_TTL_MIN", "60"))

router = APIRouter()

class LoginIn(BaseModel):
    username: str
    password: str

class TokenOut(BaseModel):
    access_token: str
    expires_at: datetime

@router.post("/login", response_model=TokenOut)
def login(data: LoginIn):
    if not data.username or not data.password:
        raise HTTPException(status_code=400, detail="Username and password required")
    with get_session() as s:
        ph = get_password_hash_by_username(s, data.username)
    if not ph or not bcrypt.checkpw(data.password.encode(), ph.encode() if isinstance(ph, str) else ph):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    exp = datetime.now(timezone.utc) + timedelta(minutes=TTL_MIN)
    token = jwt.encode({"sub": data.username, "exp": exp}, SECRET, algorithm=ALGO)
    return TokenOut(access_token=token, expires_at=exp)


class RegisterIn(BaseModel):
    username: str
    password: str


@router.post("/register")
def register(data: RegisterIn):
    if not data.username or not data.password:
        raise HTTPException(status_code=400, detail="Username and password required")
    password_hash = bcrypt.hashpw(data.password.encode(), bcrypt.gensalt()).decode()
    
    with get_session() as s:
        # создать пользователя
        try:
            result = s.execute(text(
                """
                INSERT INTO security_system.users (username, password_hash, role)
                VALUES (:u, :ph, 'user')
                RETURNING id
                """
            ), {"u": data.username, "ph": password_hash})
            user_id = result.scalar()
            
            # Автоматически создаем API ключ для нового пользователя
            raw_token = secrets.token_hex(32)
            now = datetime.now(timezone.utc)
            
            s.execute(text(
                """
                INSERT INTO security_system.api_keys (user_id, name, token, created_at)
                VALUES (:uid, :name, :token, :ts)
                """
            ), {"uid": user_id, "name": "default", "token": raw_token, "ts": now})
            
            # Автоматически создаем агента для нового пользователя
            import socket
            import platform
            import uuid
            
            # Определяем реальную информацию об агенте
            try:
                real_hostname = socket.gethostname()
            except:
                real_hostname = f"agent-{data.username}"
            
            try:
                # Пытаемся получить IP адрес
                s_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s_socket.connect(("8.8.8.8", 80))
                real_ip = s_socket.getsockname()[0]
                s_socket.close()
            except:
                real_ip = "unknown"
            
            # Определяем ОС
            os_name = platform.system()
            if os_name == "Windows":
                os_version = f"Windows {platform.release()}"
            elif os_name == "Linux":
                try:
                    os_version = f"Linux {platform.release()}"
                    with open("/etc/os-release", "r") as f:
                        for line in f:
                            if line.startswith("PRETTY_NAME"):
                                os_version = line.split("=")[1].strip().strip('"')
                                break
                except:
                    os_version = f"Linux {platform.release()}"
            else:
                os_version = f"{os_name} {platform.release()}"
            
            agent_uuid = str(uuid.uuid4())
            s.execute(text("""
                INSERT INTO security_system.agents (agent_uuid, hostname, ip_address, os, version, owner_id, status, last_seen, created_at)
                VALUES (:agent_uuid, :hostname, :ip_address, :os, :version, :owner_id, :status, NOW(), NOW())
            """), {
                "agent_uuid": agent_uuid,
                "hostname": real_hostname,
                "ip_address": real_ip,
                "os": os_version,
                "version": "2.0.0",
                "owner_id": user_id,
                "status": "offline"  # Агент создается в offline статусе
            })
            
            return {"ok": True, "api_key": raw_token, "message": "Пользователь зарегистрирован, API ключ и агент созданы"}
            
        except Exception as e:
            if "already exists" in str(e).lower():
                raise HTTPException(status_code=409, detail="Username already exists")
            raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")


class ApiKeyOut(BaseModel):
    token: str | None = None
    name: str | None = None
    created_at: datetime

class ApiKeyRequest(BaseModel):
    username: str

@router.get("/api-keys", response_model=ApiKeyOut)
def get_api_key(username: str):
    # Получение API ключа для пользователя (по username)
    if not username:
        raise HTTPException(status_code=400, detail="username required")
    
    with get_session() as s:
        # найти пользователя
        user_row = s.execute(text("SELECT id FROM security_system.users WHERE username=:u"), {"u": username}).first()
        if not user_row:
            raise HTTPException(status_code=404, detail="User not found")
        user_id = int(user_row[0])
        
        # найти последний активный API ключ
        key_row = s.execute(text(
            """
            SELECT name, created_at FROM security_system.api_keys
            WHERE user_id = :uid AND revoked_at IS NULL
            ORDER BY created_at DESC
            LIMIT 1
            """
        ), {"uid": user_id}).first()
        
        if not key_row:
            raise HTTPException(status_code=404, detail="API key not found")
        
        # Возвращаем информацию о ключе (но не сам ключ по соображениям безопасности)
        return ApiKeyOut(name=key_row[0], created_at=key_row[1])

@router.get("/api-keys/current", response_model=ApiKeyOut)
def get_current_api_key(username: str):
    # Получение текущего API ключа для пользователя (возвращает сам ключ)
    if not username:
        raise HTTPException(status_code=400, detail="username required")
    
    with get_session() as s:
        # найти пользователя
        user_row = s.execute(text("SELECT id FROM security_system.users WHERE username=:u"), {"u": username}).first()
        if not user_row:
            raise HTTPException(status_code=404, detail="User not found")
        user_id = int(user_row[0])
        
        # найти последний активный API ключ
        key_row = s.execute(text(
            """
            SELECT name, token, created_at FROM security_system.api_keys
            WHERE user_id = :uid AND revoked_at IS NULL
            ORDER BY created_at DESC
            LIMIT 1
            """
        ), {"uid": user_id}).first()
        
        if not key_row:
            # Если ключа нет, создаем новый
            raw = secrets.token_hex(32)
            now = datetime.now(timezone.utc)
            
            s.execute(text(
                """
                INSERT INTO security_system.api_keys (user_id, name, token, created_at)
                VALUES (:uid, :name, :token, :ts)
                """
            ), {"uid": user_id, "name": "default", "token": raw, "ts": now})
            
            return ApiKeyOut(token=raw, name="default", created_at=now)
        
        # Возвращаем существующий ключ
        return ApiKeyOut(token=key_row[1], name=key_row[0], created_at=key_row[2])

@router.post("/api-keys", response_model=ApiKeyOut)
def create_api_key(request: ApiKeyRequest):
    # Генерация нового API ключа для текущего пользователя (по username)
    if not request.username:
        raise HTTPException(status_code=400, detail="username required")
    
    raw = secrets.token_hex(32)
    now = datetime.now(timezone.utc)
    
    with get_session() as s:
        # найти пользователя
        row = s.execute(text("SELECT id FROM security_system.users WHERE username=:u"), {"u": request.username}).first()
        if not row:
            raise HTTPException(status_code=404, detail="User not found")
        user_id = int(row[0])
        
        # Отзываем старый ключ если есть
        s.execute(text(
            """
            UPDATE security_system.api_keys 
            SET revoked_at = :now 
            WHERE user_id = :uid AND revoked_at IS NULL
            """
        ), {"uid": user_id, "now": now})
        
        # Создаем новый ключ
        s.execute(text(
            """
            INSERT INTO security_system.api_keys (user_id, name, token, created_at)
            VALUES (:uid, :name, :token, :ts)
            """
        ), {"uid": user_id, "name": "default", "token": raw, "ts": now})
        
    return ApiKeyOut(token=raw, name="default", created_at=now)
