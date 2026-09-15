"""JWT + bcrypt. Password truncated to 72 bytes (bcrypt limit)."""
import os
import time
import secrets
from jose import jwt, JWTError
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, Header
from sqlalchemy.orm import Session
from database import get_db
from models import User

_ENV = os.getenv("ENV", "dev").lower()
_SECRET_FROM_ENV = os.getenv("JWT_SECRET")

if _SECRET_FROM_ENV:
    SECRET = _SECRET_FROM_ENV
    if len(SECRET) < 32:
        raise RuntimeError("JWT_SECRET too short. Use at least 32 characters.")
    print(f"[auth] ✅ JWT_SECRET loaded from environment ({len(SECRET)} chars)")
elif _ENV == "prod":
    raise RuntimeError("JWT_SECRET is required in production. Set it in .env.")
else:
    SECRET = secrets.token_hex(64)
    print("[auth] ⚠️  No JWT_SECRET — using ephemeral dev secret (tokens expire on restart)")

ALGO = "HS256"
EXPIRE_MIN = 720  # 12 hours

pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(p: str) -> str:
    return pwd.hash(p[:72])


def verify_password(p: str, h: str) -> bool:
    try:
        return pwd.verify(p[:72], h)
    except Exception:
        return False


def make_token(user_id: str) -> str:
    payload = {
        "sub": user_id,
        "exp": int(time.time()) + EXPIRE_MIN * 60,
        "iat": int(time.time()),
    }
    return jwt.encode(payload, SECRET, algorithm=ALGO)


def current_user(authorization: str = Header(None), db: Session = Depends(get_db)) -> User:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(401, "Missing or invalid authorization header")
    token = authorization.split(" ", 1)[1].strip()
    try:
        payload = jwt.decode(token, SECRET, algorithms=[ALGO])
    except JWTError:
        raise HTTPException(401, "Invalid or expired token")
    uid = payload.get("sub")
    if not uid:
        raise HTTPException(401, "Malformed token")
    u = db.query(User).filter(User.id == uid).first()
    if not u:
        raise HTTPException(401, "User not found")
    return u