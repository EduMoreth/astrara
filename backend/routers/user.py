import json
from fastapi import APIRouter, HTTPException, Depends, Header
from fastapi.responses import Response
from typing import Optional
from pydantic import BaseModel
from database import get_connection
from routers.auth import verify_token, hash_password

router = APIRouter(prefix="/user", tags=["user"])


def get_current_user(authorization: Optional[str] = Header(None)) -> dict:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token não fornecido")
    token = authorization.split(" ")[1]
    return verify_token(token)


@router.get("/me")
async def get_me(user: dict = Depends(get_current_user)):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, name, email, plan, created_at FROM users WHERE id = %s",
        (user["sub"],),
    )
    row = cur.fetchone()
    cur.close()
    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    return {
        "id": str(row["id"]),
        "name": row["name"],
        "email": row["email"],
        "plan": row["plan"],
        "created_at": str(row["created_at"]),
    }


@router.get("/charts")
async def get_charts(user: dict = Depends(get_current_user)):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """SELECT id, name, birth_date, birth_time, birth_city,
                  positions_json, svg_data, created_at
           FROM charts WHERE user_id = %s ORDER BY created_at DESC""",
        (user["sub"],),
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()

    return [
        {
            "id": str(r["id"]),
            "name": r["name"],
            "birth_date": str(r["birth_date"]),
            "birth_time": str(r["birth_time"]),
            "birth_city": r["birth_city"],
            "positions_json": r["positions_json"],
            "svg_data": r["svg_data"],
            "created_at": str(r["created_at"]),
        }
        for r in rows
    ]


@router.post("/charts/save")
async def save_chart(
    data: dict,
    user: dict = Depends(get_current_user),
):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """INSERT INTO charts
           (user_id, name, birth_date, birth_time, birth_city, birth_country,
            lat, lng, tz_str, positions_json, svg_data)
           VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
           RETURNING id""",
        (
            user["sub"],
            data["name"],
            data["birth_date"],
            data["birth_time"],
            data["birth_city"],
            data.get("birth_country"),
            data.get("lat"),
            data.get("lng"),
            data.get("tz_str"),
            json.dumps(data.get("positions_json", {})),
            data.get("svg_data", ""),
        ),
    )
    row = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()

    return {"id": str(row["id"]), "message": "Mapa salvo com sucesso"}


@router.get("/credits")
async def get_user_credits(user: dict = Depends(get_current_user)):
    """Get current user's credit balance."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM user_credits WHERE user_id = %s", (user["sub"],))
    row = cur.fetchone()
    cur.close()
    conn.close()

    if not row:
        return {"credits_balance": 0, "total_purchased": 0, "total_used": 0}

    return {
        "credits_balance": row["credits_balance"],
        "total_purchased": row["total_purchased"],
        "total_used": row["total_used"],
    }


@router.get("/has-purchase")
async def check_has_purchase(user: dict = Depends(get_current_user)):
    """Check if user has any completed purchase."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT id FROM purchases WHERE user_id = %s AND status = 'completed' LIMIT 1",
        (user["sub"],),
    )
    row = cur.fetchone()
    cur.close()
    conn.close()

    return {"has_purchase": row is not None}


# ── LGPD Data Rights ─────────────────────────────────────

@router.get("/export-data")
async def export_user_data(user: dict = Depends(get_current_user)):
    """LGPD Art. 18 — Right to data portability. Returns all user data as JSON."""
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT id, name, email, plan, status, created_at, updated_at FROM users WHERE id = %s", (user["sub"],))
    user_data = cur.fetchone()

    cur.execute("SELECT * FROM charts WHERE user_id = %s ORDER BY created_at DESC", (user["sub"],))
    charts = cur.fetchall()

    cur.execute("SELECT * FROM purchases WHERE user_id = %s ORDER BY created_at DESC", (user["sub"],))
    purchases = cur.fetchall()

    cur.execute("SELECT * FROM user_credits WHERE user_id = %s", (user["sub"],))
    credits = cur.fetchone()

    cur.execute("SELECT * FROM credit_transactions WHERE user_id = %s ORDER BY created_at DESC", (user["sub"],))
    credit_tx = cur.fetchall()

    cur.execute("SELECT * FROM tickets WHERE user_id = %s ORDER BY created_at DESC", (user["sub"],))
    tickets = cur.fetchall()

    cur.close()
    conn.close()

    def serialize(rows):
        if not rows:
            return []
        if isinstance(rows, dict):
            return {k: str(v) for k, v in rows.items()}
        return [{k: str(v) for k, v in r.items()} for r in rows]

    export = {
        "usuario": serialize(user_data) if user_data else {},
        "mapas_astrais": serialize(charts),
        "compras": serialize(purchases),
        "creditos": serialize(credits) if credits else {},
        "transacoes_creditos": serialize(credit_tx),
        "tickets_suporte": serialize(tickets),
        "exportado_em": str(__import__('datetime').datetime.now()),
    }

    return Response(
        content=json.dumps(export, ensure_ascii=False, indent=2),
        media_type="application/json",
        headers={"Content-Disposition": 'attachment; filename="astrara-meus-dados.json"'},
    )


class DeleteAccountRequest(BaseModel):
    password: str
    confirmation: str = "EXCLUIR"


@router.post("/delete-account")
async def delete_account(data: DeleteAccountRequest, user: dict = Depends(get_current_user)):
    """LGPD Art. 18 — Right to deletion. Permanently deletes user account and all data."""
    if data.confirmation != "EXCLUIR":
        raise HTTPException(status_code=400, detail="Digite EXCLUIR para confirmar a exclusao")

    from routers.auth import verify_password

    conn = get_connection()
    cur = conn.cursor()

    # Verify password
    cur.execute("SELECT password_hash FROM users WHERE id = %s", (user["sub"],))
    row = cur.fetchone()
    if not row or not verify_password(data.password, row["password_hash"]):
        cur.close()
        conn.close()
        raise HTTPException(status_code=401, detail="Senha incorreta")

    # Delete all user data (CASCADE handles related records)
    cur.execute("DELETE FROM users WHERE id = %s", (user["sub"],))
    conn.commit()
    cur.close()
    conn.close()

    return {"message": "Conta excluida com sucesso. Todos os seus dados foram removidos."}


class UpdateProfileRequest(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None


@router.patch("/me")
async def update_profile(data: UpdateProfileRequest, user: dict = Depends(get_current_user)):
    """LGPD Art. 18 — Right to correction."""
    conn = get_connection()
    cur = conn.cursor()

    updates = []
    params = []
    if data.name:
        updates.append("name = %s")
        params.append(data.name)
    if data.email:
        updates.append("email = %s")
        params.append(data.email)

    if not updates:
        cur.close()
        conn.close()
        raise HTTPException(status_code=400, detail="Nenhum campo para atualizar")

    updates.append("updated_at = NOW()")
    params.append(user["sub"])
    cur.execute(f"UPDATE users SET {', '.join(updates)} WHERE id = %s", params)
    conn.commit()
    cur.close()
    conn.close()

    return {"message": "Dados atualizados com sucesso"}


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


@router.post("/change-password")
async def change_password(data: ChangePasswordRequest, user: dict = Depends(get_current_user)):
    from routers.auth import verify_password

    if len(data.new_password) < 6:
        raise HTTPException(status_code=400, detail="Nova senha deve ter pelo menos 6 caracteres")

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT password_hash FROM users WHERE id = %s", (user["sub"],))
    row = cur.fetchone()
    if not row or not verify_password(data.current_password, row["password_hash"]):
        cur.close()
        conn.close()
        raise HTTPException(status_code=401, detail="Senha atual incorreta")

    new_hash = hash_password(data.new_password)
    cur.execute("UPDATE users SET password_hash = %s, updated_at = NOW() WHERE id = %s", (new_hash, user["sub"]))
    conn.commit()
    cur.close()
    conn.close()

    return {"message": "Senha alterada com sucesso"}
