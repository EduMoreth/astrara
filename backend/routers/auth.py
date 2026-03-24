import os
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException
from jose import jwt
import bcrypt
from models.user import UserRegister, UserLogin
from database import get_connection

router = APIRouter(prefix="/auth", tags=["auth"])

SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-in-production")
ALGORITHM = "HS256"
TOKEN_EXPIRE_HOURS = 72


def hash_password(password: str) -> str:
    pwd_bytes = password.encode("utf-8")[:72]
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pwd_bytes, salt).decode("utf-8")


def verify_password(password: str, hashed: str) -> bool:
    pwd_bytes = password.encode("utf-8")[:72]
    hashed_bytes = hashed.encode("utf-8")
    return bcrypt.checkpw(pwd_bytes, hashed_bytes)


def create_token(user_id: str, name: str, email: str) -> str:
    payload = {
        "sub": user_id,
        "name": name,
        "email": email,
        "exp": datetime.utcnow() + timedelta(hours=TOKEN_EXPIRE_HOURS),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def verify_token(token: str) -> dict:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except Exception:
        raise HTTPException(status_code=401, detail="Token invalido ou expirado")


@router.post("/register")
async def register(data: UserRegister):
    conn = get_connection()
    cur = conn.cursor()

    # Check if email exists
    cur.execute("SELECT id FROM users WHERE email = %s", (data.email,))
    if cur.fetchone():
        cur.close()
        conn.close()
        raise HTTPException(status_code=400, detail="Email ja cadastrado")

    hashed = hash_password(data.password)
    cur.execute(
        "INSERT INTO users (name, email, password_hash) VALUES (%s, %s, %s) RETURNING id, name, email",
        (data.name, data.email, hashed),
    )
    user = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()

    token = create_token(str(user["id"]), user["name"], user["email"])
    return {"access_token": token, "token_type": "bearer"}


@router.post("/login")
async def login(data: UserLogin):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        "SELECT id, name, email, password_hash FROM users WHERE email = %s",
        (data.email,),
    )
    user = cur.fetchone()
    cur.close()
    conn.close()

    if not user or not verify_password(data.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Email ou senha incorretos")

    token = create_token(str(user["id"]), user["name"], user["email"])
    return {"access_token": token, "token_type": "bearer"}
