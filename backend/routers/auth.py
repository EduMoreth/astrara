import os
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Request
from jose import jwt
from pydantic import BaseModel, Field
import bcrypt
from slowapi import Limiter
from slowapi.util import get_remote_address
from models.user import UserRegister, UserLogin
from database import get_connection

limiter = Limiter(key_func=get_remote_address)

router = APIRouter(prefix="/auth", tags=["auth"])

SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError(
        "SECRET_KEY environment variable is required. "
        "Set it to a strong random string before starting the server."
    )
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
@limiter.limit("5/minute")
async def register(request: Request, data: UserRegister):
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

    # Send welcome email (non-blocking)
    try:
        from services.email_service import send_welcome_email
        send_welcome_email(user["email"], user["name"])
    except Exception as e:
        print(f"Welcome email error: {e}")

    return {"access_token": token, "token_type": "bearer"}


@router.post("/login")
@limiter.limit("10/minute")
async def login(request: Request, data: UserLogin):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        "SELECT id, name, email, password_hash, force_password_reset, status FROM users WHERE email = %s",
        (data.email,),
    )
    user = cur.fetchone()
    cur.close()
    conn.close()

    try:
        password_ok = bool(user) and verify_password(data.password, user["password_hash"])
    except Exception:
        # Malformed/empty hash (e.g. anonymized account) — treat as wrong password
        password_ok = False

    if not user or not password_ok:
        raise HTTPException(status_code=401, detail="Email ou senha incorretos")

    # Banned/deleted accounts cannot log in
    if user.get("status") in ("banned", "deleted"):
        raise HTTPException(status_code=403, detail="Conta desativada. Entre em contato com o suporte.")

    # Check if forced password reset
    if user.get("force_password_reset"):
        return {
            "force_password_reset": True,
            "email": user["email"],
            "message": "Voce precisa redefinir sua senha antes de continuar.",
        }

    token = create_token(str(user["id"]), user["name"], user["email"])
    return {"access_token": token, "token_type": "bearer"}


# ── Password Recovery ────────────────────────────────────

class ForgotPasswordRequest(BaseModel):
    email: str


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(min_length=8)


@router.post("/forgot-password")
@limiter.limit("3/minute")
async def forgot_password(request: Request, data: ForgotPasswordRequest):
    import secrets as sec
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT id, name FROM users WHERE email = %s", (data.email,))
    user = cur.fetchone()

    if not user:
        # Don't reveal if email exists
        return {"message": "Se o email existir, voce recebera um link para redefinir sua senha."}

    # Generate reset token
    reset_token = sec.token_urlsafe(32)
    cur.execute("""
        UPDATE users SET reset_token = %s, reset_token_expires = NOW() + INTERVAL '1 hour'
        WHERE email = %s
    """, (reset_token, data.email))
    conn.commit()
    cur.close()
    conn.close()

    # Send reset email
    try:
        from services.email_service import _send_email, _base_template, FRONTEND_URL
        reset_url = f"{FRONTEND_URL}/auth/reset-password?token={reset_token}"
        content = f"""
        <h2 style="color:#F0EDE8;font-size:22px;text-align:center;">Redefinir sua senha</h2>
        <p style="color:#8B8A9B;font-size:14px;text-align:center;line-height:1.7;">
          Ola, {user['name']}. Recebemos uma solicitacao para redefinir sua senha.
          Clique no botao abaixo para criar uma nova senha.
        </p>
        <div style="text-align:center;margin:32px 0;">
          <a href="{reset_url}"
             style="background:linear-gradient(135deg,#C9A96E,#A07840);color:#0A0A0F;
                    padding:14px 40px;border-radius:100px;text-decoration:none;
                    font-weight:600;font-size:15px;display:inline-block;">
            Redefinir senha &rarr;
          </a>
        </div>
        <p style="color:#555;font-size:11px;text-align:center;">
          Este link expira em 1 hora. Se voce nao solicitou, ignore este email.
        </p>
        """
        _send_email(data.email, "Redefinir senha — Astrara", _base_template(content), "password_reset")
    except Exception as e:
        print(f"Reset email error: {e}")

    return {"message": "Se o email existir, voce recebera um link para redefinir sua senha."}


@router.post("/reset-password")
@limiter.limit("5/minute")
async def reset_password(request: Request, data: ResetPasswordRequest):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT id FROM users
        WHERE reset_token = %s AND reset_token_expires > NOW()
    """, (data.token,))
    user = cur.fetchone()

    if not user:
        cur.close()
        conn.close()
        raise HTTPException(status_code=400, detail="Token invalido ou expirado. Solicite um novo link.")

    hashed = hash_password(data.new_password)
    cur.execute("""
        UPDATE users SET password_hash = %s, reset_token = NULL, reset_token_expires = NULL,
                         force_password_reset = false, updated_at = NOW()
        WHERE id = %s
    """, (hashed, user["id"]))
    conn.commit()
    cur.close()
    conn.close()

    return {"message": "Senha redefinida com sucesso. Voce ja pode fazer login."}
