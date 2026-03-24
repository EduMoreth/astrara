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

    # Check saved charts limit based on plan
    cur.execute("SELECT plan, max_saved_charts FROM users WHERE id = %s", (user["sub"],))
    user_row = cur.fetchone()
    plan = user_row["plan"] if user_row else "free"

    # Plan-based limits
    if plan in ("superadmin", "admin"):
        max_charts = 999999  # unlimited
    elif plan == "pro" or plan == "premium":
        max_charts = user_row.get("max_saved_charts", 10) if user_row else 10
    else:
        max_charts = 1  # free users

    cur.execute("SELECT COUNT(*) as count FROM charts WHERE user_id = %s", (user["sub"],))
    current_count = cur.fetchone()["count"]

    if current_count >= max_charts:
        cur.close()
        conn.close()
        if plan == "free":
            raise HTTPException(
                status_code=403,
                detail="Voce atingiu o limite de 1 mapa salvo no plano gratuito. Delete o mapa atual ou faca upgrade para o plano Premium (ate 10 mapas)."
            )
        else:
            raise HTTPException(
                status_code=403,
                detail=f"Limite de {max_charts} mapas salvos atingido. Delete um mapa para salvar outro."
            )

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

    return {"id": str(row["id"]), "message": "Mapa salvo com sucesso", "saved_count": current_count + 1, "max_charts": max_charts}


@router.get("/charts/limit")
async def get_charts_limit(user: dict = Depends(get_current_user)):
    """Get current saved charts count and limit for the user."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT plan, max_saved_charts FROM users WHERE id = %s", (user["sub"],))
    user_row = cur.fetchone()
    plan = user_row["plan"] if user_row else "free"

    if plan in ("superadmin", "admin"):
        max_charts = 999999
    elif plan in ("pro", "premium"):
        max_charts = user_row.get("max_saved_charts", 10) if user_row else 10
    else:
        max_charts = 1

    cur.execute("SELECT COUNT(*) as count FROM charts WHERE user_id = %s", (user["sub"],))
    count = cur.fetchone()["count"]
    cur.close()
    conn.close()

    return {"saved_count": count, "max_charts": max_charts, "can_save": count < max_charts}


@router.delete("/charts/{chart_id}")
async def delete_saved_chart(chart_id: str, user: dict = Depends(get_current_user)):
    """Delete a saved chart to free up a slot."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM charts WHERE id = %s AND user_id = %s", (chart_id, user["sub"]))
    deleted = cur.rowcount
    conn.commit()
    cur.close()
    conn.close()
    if deleted == 0:
        raise HTTPException(status_code=404, detail="Mapa nao encontrado")
    return {"success": True}


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
