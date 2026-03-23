import json
from fastapi import APIRouter, HTTPException, Depends, Header
from typing import Optional
from database import get_connection
from routers.auth import verify_token

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
