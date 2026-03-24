import os
import httpx
from database import get_connection

RESEND_API_KEY = os.getenv("RESEND_API_KEY")
FROM_EMAIL = os.getenv("FROM_EMAIL", "Astrara <noreply@astrara.online>")
FRONTEND_URL = os.getenv("FRONTEND_URL", "https://www.astrara.online")


def _log_email(to_email: str, subject: str, template: str, resend_id: str = None, status: str = "sent"):
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO email_logs (to_email, subject, template, status, resend_id)
            VALUES (%s, %s, %s, %s, %s)
        """, (to_email, subject, template, status, resend_id))
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Email log error: {e}")


def _send_email(to: str, subject: str, html: str, template: str = "generic") -> bool:
    if not RESEND_API_KEY:
        print(f"[EMAIL SKIP] No RESEND_API_KEY. Would send to {to}: {subject}")
        _log_email(to, subject, template, status="skipped")
        return False

    try:
        res = httpx.post(
            "https://api.resend.com/emails",
            headers={"Authorization": f"Bearer {RESEND_API_KEY}"},
            json={
                "from": FROM_EMAIL,
                "to": [to],
                "subject": subject,
                "html": html,
            },
            timeout=10,
        )
        data = res.json()
        resend_id = data.get("id", "")
        success = res.status_code == 200
        _log_email(to, subject, template, resend_id, "sent" if success else "failed")
        return success
    except Exception as e:
        print(f"Email send error: {e}")
        _log_email(to, subject, template, status="error")
        return False


def _base_template(content: str) -> str:
    return f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="utf-8"><meta name="viewport" content="width=device-width"></head>
    <body style="margin:0;padding:0;background:#0A0A0F;font-family:'Helvetica Neue',Arial,sans-serif;">
      <div style="max-width:600px;margin:0 auto;padding:40px 24px;">
        <!-- Header -->
        <div style="text-align:center;padding-bottom:32px;border-bottom:1px solid rgba(201,169,110,0.2);">
          <h1 style="color:#C9A96E;font-size:28px;margin:0;letter-spacing:2px;">✦ ASTRARA</h1>
          <p style="color:#8B8A9B;font-size:13px;margin:8px 0 0;">O cosmos, decifrado.</p>
        </div>

        <!-- Content -->
        <div style="padding:32px 0;">
          {content}
        </div>

        <!-- Footer -->
        <div style="border-top:1px solid rgba(201,169,110,0.15);padding-top:24px;text-align:center;">
          <p style="color:#8B8A9B;font-size:12px;margin:0;">
            <a href="{FRONTEND_URL}" style="color:#C9A96E;text-decoration:none;">www.astrara.online</a>
          </p>
          <p style="color:#555;font-size:11px;margin:8px 0 0;">
            Voce recebeu este email porque tem uma conta na Astrara.
          </p>
        </div>
      </div>
    </body>
    </html>
    """


# ── Welcome Email ────────────────────────────────────────

def send_welcome_email(to: str, name: str) -> bool:
    content = f"""
    <h2 style="color:#F0EDE8;font-size:24px;text-align:center;margin:0 0 16px;">
      Bem-vindo(a), {name}! ✨
    </h2>
    <p style="color:#8B8A9B;font-size:15px;line-height:1.7;text-align:center;">
      Sua conta na Astrara foi criada com sucesso. Agora voce pode gerar mapas astrais
      com precisao profissional e desbloquear interpretacoes detalhadas com inteligencia artificial.
    </p>
    <div style="text-align:center;margin:32px 0;">
      <a href="{FRONTEND_URL}/chart"
         style="background:linear-gradient(135deg,#C9A96E,#A07840);color:#0A0A0F;
                padding:14px 40px;border-radius:100px;text-decoration:none;
                font-weight:600;font-size:15px;display:inline-block;">
        Gerar meu mapa astral &rarr;
      </a>
    </div>
    <div style="background:rgba(18,18,26,0.7);border:1px solid rgba(201,169,110,0.15);
                border-radius:16px;padding:24px;margin:24px 0;">
      <h3 style="color:#C9A96E;font-size:14px;margin:0 0 12px;">O que voce pode fazer:</h3>
      <p style="color:#8B8A9B;font-size:13px;line-height:1.8;margin:0;">
        🌙 Calcular seu mapa natal com Swiss Ephemeris<br>
        ✨ Visualizar sua mandala astrologica personalizada<br>
        🔮 Desbloquear interpretacao completa com IA<br>
        📄 Baixar seu mapa em PDF
      </p>
    </div>
    """
    return _send_email(to, "Bem-vindo(a) a Astrara! ✨", _base_template(content), "welcome")


# ── Refund Confirmation Email ────────────────────────────

def send_refund_email(to: str, name: str, amount_cents: int, reason: str = "") -> bool:
    amount_str = f"R$ {(amount_cents / 100):.2f}".replace(".", ",")
    content = f"""
    <h2 style="color:#F0EDE8;font-size:22px;text-align:center;margin:0 0 16px;">
      Reembolso processado
    </h2>
    <p style="color:#8B8A9B;font-size:15px;line-height:1.7;text-align:center;">
      Ola, {name}. Confirmamos que seu reembolso foi processado com sucesso.
    </p>
    <div style="background:rgba(18,18,26,0.7);border:1px solid rgba(201,169,110,0.15);
                border-radius:16px;padding:24px;margin:24px 0;text-align:center;">
      <p style="color:#C9A96E;font-size:28px;font-weight:700;margin:0;">{amount_str}</p>
      <p style="color:#8B8A9B;font-size:13px;margin:8px 0 0;">Valor reembolsado</p>
      {f'<p style="color:#8B8A9B;font-size:12px;margin:12px 0 0;">Motivo: {reason}</p>' if reason else ''}
    </div>
    <p style="color:#8B8A9B;font-size:13px;line-height:1.7;text-align:center;">
      O valor sera estornado na sua forma de pagamento original em ate 10 dias uteis,
      dependendo da sua operadora de cartao.
    </p>
    """
    return _send_email(to, "Seu reembolso foi processado — Astrara", _base_template(content), "refund")


# ── Ticket Notification Email ────────────────────────────

def send_ticket_reply_email(to: str, name: str, ticket_subject: str, reply_text: str) -> bool:
    content = f"""
    <h2 style="color:#F0EDE8;font-size:20px;margin:0 0 16px;">
      Nova resposta no seu ticket
    </h2>
    <p style="color:#8B8A9B;font-size:14px;">
      Assunto: <strong style="color:#F0EDE8;">{ticket_subject}</strong>
    </p>
    <div style="background:rgba(18,18,26,0.7);border:1px solid rgba(201,169,110,0.15);
                border-radius:12px;padding:20px;margin:16px 0;">
      <p style="color:#F0EDE8;font-size:14px;line-height:1.7;margin:0;white-space:pre-wrap;">{reply_text}</p>
    </div>
    <div style="text-align:center;margin:24px 0;">
      <a href="{FRONTEND_URL}/support"
         style="background:linear-gradient(135deg,#C9A96E,#A07840);color:#0A0A0F;
                padding:12px 32px;border-radius:100px;text-decoration:none;
                font-weight:600;font-size:14px;display:inline-block;">
        Ver ticket completo
      </a>
    </div>
    """
    return _send_email(to, f"Resposta no ticket: {ticket_subject} — Astrara", _base_template(content), "ticket_reply")


# ── Purchase Confirmation Email ──────────────────────────

def send_purchase_email(to: str, name: str, product_name: str, amount_cents: int) -> bool:
    amount_str = f"R$ {(amount_cents / 100):.2f}".replace(".", ",")
    content = f"""
    <h2 style="color:#F0EDE8;font-size:22px;text-align:center;margin:0 0 16px;">
      Compra confirmada! ✨
    </h2>
    <p style="color:#8B8A9B;font-size:15px;line-height:1.7;text-align:center;">
      Ola, {name}. Sua compra foi processada com sucesso.
    </p>
    <div style="background:rgba(18,18,26,0.7);border:1px solid rgba(201,169,110,0.15);
                border-radius:16px;padding:24px;margin:24px 0;">
      <p style="color:#F0EDE8;font-size:16px;margin:0 0 8px;"><strong>{product_name}</strong></p>
      <p style="color:#C9A96E;font-size:22px;font-weight:700;margin:0;">{amount_str}</p>
    </div>
    <div style="text-align:center;margin:24px 0;">
      <a href="{FRONTEND_URL}/chart"
         style="background:linear-gradient(135deg,#C9A96E,#A07840);color:#0A0A0F;
                padding:12px 32px;border-radius:100px;text-decoration:none;
                font-weight:600;font-size:14px;display:inline-block;">
        Acessar meu mapa &rarr;
      </a>
    </div>
    """
    return _send_email(to, f"Compra confirmada: {product_name} — Astrara", _base_template(content), "purchase")
