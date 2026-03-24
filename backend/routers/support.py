from typing import Optional
from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel
from database import get_connection
from routers.auth import verify_token

router = APIRouter(prefix="/support", tags=["support"])


def get_current_user(authorization: Optional[str] = Header(None)) -> dict:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Login necessario")
    return verify_token(authorization.replace("Bearer ", ""))


class CreateTicketRequest(BaseModel):
    subject: str
    message: str
    priority: str = "normal"


class ReplyTicketRequest(BaseModel):
    message: str


@router.post("/tickets")
async def create_ticket(data: CreateTicketRequest, authorization: Optional[str] = Header(None)):
    user = get_current_user(authorization)
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO tickets (user_id, subject, priority)
        VALUES (%s, %s, %s) RETURNING id
    """, (user["sub"], data.subject, data.priority))
    ticket_id = str(cur.fetchone()["id"])

    # Get user name
    cur.execute("SELECT name FROM users WHERE id = %s", (user["sub"],))
    user_row = cur.fetchone()
    sender_name = user_row["name"] if user_row else "Usuario"

    cur.execute("""
        INSERT INTO ticket_messages (ticket_id, sender_type, sender_id, sender_name, message)
        VALUES (%s, 'user', %s, %s, %s)
    """, (ticket_id, user["sub"], sender_name, data.message))

    conn.commit()
    cur.close()
    conn.close()

    return {"success": True, "ticket_id": ticket_id}


@router.get("/tickets")
async def list_my_tickets(authorization: Optional[str] = Header(None)):
    user = get_current_user(authorization)
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT t.*, (SELECT COUNT(*) FROM ticket_messages tm WHERE tm.ticket_id = t.id) as message_count
        FROM tickets t
        WHERE t.user_id = %s
        ORDER BY t.updated_at DESC
    """, (user["sub"],))
    tickets = cur.fetchall()
    cur.close()
    conn.close()

    return [{**t, "id": str(t["id"])} for t in tickets]


@router.get("/tickets/{ticket_id}")
async def get_ticket(ticket_id: str, authorization: Optional[str] = Header(None)):
    user = get_current_user(authorization)
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT * FROM tickets WHERE id = %s AND user_id = %s", (ticket_id, user["sub"]))
    ticket = cur.fetchone()
    if not ticket:
        cur.close()
        conn.close()
        raise HTTPException(status_code=404, detail="Ticket nao encontrado")

    cur.execute("SELECT * FROM ticket_messages WHERE ticket_id = %s ORDER BY created_at ASC", (ticket_id,))
    messages = cur.fetchall()
    cur.close()
    conn.close()

    return {
        "ticket": {**ticket, "id": str(ticket["id"])},
        "messages": [{**m, "id": str(m["id"])} for m in messages],
    }


@router.post("/tickets/{ticket_id}/reply")
async def reply_to_ticket(ticket_id: str, data: ReplyTicketRequest, authorization: Optional[str] = Header(None)):
    user = get_current_user(authorization)
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT * FROM tickets WHERE id = %s AND user_id = %s", (ticket_id, user["sub"]))
    ticket = cur.fetchone()
    if not ticket:
        cur.close()
        conn.close()
        raise HTTPException(status_code=404, detail="Ticket nao encontrado")

    cur.execute("SELECT name FROM users WHERE id = %s", (user["sub"],))
    user_row = cur.fetchone()
    sender_name = user_row["name"] if user_row else "Usuario"

    cur.execute("""
        INSERT INTO ticket_messages (ticket_id, sender_type, sender_id, sender_name, message)
        VALUES (%s, 'user', %s, %s, %s)
    """, (ticket_id, user["sub"], sender_name, data.message))

    cur.execute("UPDATE tickets SET updated_at = NOW() WHERE id = %s", (ticket_id,))
    conn.commit()
    cur.close()
    conn.close()

    return {"success": True}
