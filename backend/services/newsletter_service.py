import os
import anthropic
from datetime import date, timedelta
from database import get_connection
from services.email_service import send_email
from services.astral_content_service import get_daily_transits

anthropic_client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))


def generate_weekly_newsletter() -> dict:
    """Generate weekly horoscope newsletter content."""
    today = date.today()
    week_start = today - timedelta(days=today.weekday())  # Monday
    week_end = week_start + timedelta(days=6)  # Sunday

    # Get transits for the week
    mid_week = week_start + timedelta(days=3)
    transits = get_daily_transits(mid_week)

    prompt = f"""Voce e um astrologo renomado escrevendo a newsletter semanal da Astrara.

SEMANA: {week_start.strftime('%d/%m')} a {week_end.strftime('%d/%m/%Y')}

TRANSITOS DA SEMANA:
- Sol: {transits['sun']['deg']} em {transits['sun']['sign']}
- Lua: {transits['moon']['deg']} em {transits['moon']['sign']}
- Mercurio: {transits['mercury']['deg']} em {transits['mercury']['sign']}
- Venus: {transits['venus']['deg']} em {transits['venus']['sign']}
- Marte: {transits['mars']['deg']} em {transits['mars']['sign']}
- Jupiter: {transits['jupiter']['deg']} em {transits['jupiter']['sign']}
- Saturno: {transits['saturn']['deg']} em {transits['saturn']['sign']}

Escreva a newsletter em HTML com o seguinte formato:
1. Saudacao calorosa
2. Panorama astrologico da semana (3-4 paragrafos)
3. Destaques: 3 aspectos mais importantes
4. Dica da semana (pratica, baseada nos transitos)
5. CTA para calcular o mapa em astrara.online

ESTILO:
- Tom poetico, inspirador, acolhedor
- Em portugues brasileiro
- HTML formatado (use <h2>, <p>, <strong>, <em>)
- Nao inclua <html>, <head>, <body> — apenas o conteudo interno
- Use cores: dourado (#C9A96E) para destaques

Retorne APENAS um JSON:
{{
  "subject": "assunto do email (maximo 60 chars, com emoji)",
  "content_html": "conteudo HTML da newsletter"
}}"""

    message = anthropic_client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=3000,
        messages=[{"role": "user", "content": prompt}],
    )

    import json
    raw = message.content[0].text.strip()
    raw = raw.replace("```json", "").replace("```", "").strip()
    return json.loads(raw)


def send_weekly_newsletter():
    """Generate and send weekly newsletter to all active subscribers."""
    conn = get_connection()
    cur = conn.cursor()

    # Get active subscribers
    cur.execute("SELECT email FROM newsletter_subscribers WHERE status = 'active'")
    subscribers = cur.fetchall()

    if not subscribers:
        print("No active subscribers. Skipping newsletter.")
        cur.close()
        conn.close()
        return

    # Generate content
    newsletter = generate_weekly_newsletter()

    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6)

    # Wrap in email template
    html_content = f"""
    <div style="max-width:600px;margin:0 auto;background:#0A0A0F;color:#F0EDE8;font-family:Arial,sans-serif;padding:40px 30px;">
        <div style="text-align:center;margin-bottom:30px;">
            <h1 style="color:#C9A96E;font-size:28px;margin:0;">&#10022; Astrara</h1>
            <p style="color:#8B8A9B;font-size:13px;margin-top:5px;">O cosmos, decifrado.</p>
        </div>
        <div style="line-height:1.7;font-size:15px;">
            {newsletter['content_html']}
        </div>
        <div style="text-align:center;margin-top:40px;padding-top:20px;border-top:1px solid rgba(201,169,110,0.2);">
            <a href="https://www.astrara.online/chart" style="background:linear-gradient(135deg,#C9A96E,#A07840);color:#0A0A0F;padding:14px 32px;border-radius:100px;text-decoration:none;font-weight:600;display:inline-block;">
                Calcular meu mapa astral &#8594;
            </a>
        </div>
        <div style="text-align:center;margin-top:30px;padding-top:20px;border-top:1px solid rgba(255,255,255,0.05);">
            <p style="color:#8B8A9B;font-size:11px;">
                Voce recebeu este email por ser assinante da newsletter Astrara.<br>
                <a href="https://www.astrara.online/unsubscribe?email={{{{email}}}}&token={{{{unsub_token}}}}" style="color:#8B8A9B;">Cancelar inscricao</a>
            </p>
        </div>
    </div>
    """

    # Save edition
    cur.execute("""
        INSERT INTO newsletter_editions (subject, content_html, week_start, week_end, status)
        VALUES (%s, %s, %s, %s, 'sending') RETURNING id
    """, (newsletter["subject"], html_content, week_start, week_end))
    edition_id = str(cur.fetchone()["id"])
    conn.commit()

    # Send to all subscribers
    import hmac, hashlib
    secret_key = os.getenv("SECRET_KEY", "")

    sent_count = 0
    for sub in subscribers:
        try:
            unsub_token = hmac.new(secret_key.encode(), sub["email"].encode(), hashlib.sha256).hexdigest()
            personalized_html = html_content.replace("{{email}}", sub["email"]).replace("{{unsub_token}}", unsub_token)
            send_email(
                to_email=sub["email"],
                subject=newsletter["subject"],
                html_content=personalized_html,
                template="weekly_newsletter",
            )
            sent_count += 1
        except Exception as e:
            print(f"Failed to send to {sub['email']}: {e}")

    # Update edition
    cur.execute("""
        UPDATE newsletter_editions SET sent_count = %s, status = 'sent', sent_at = NOW()
        WHERE id = %s
    """, (sent_count, edition_id))
    conn.commit()
    cur.close()
    conn.close()

    print(f"Newsletter sent to {sent_count}/{len(subscribers)} subscribers")
    return {"sent": sent_count, "total": len(subscribers)}


def subscribe_user(email: str, user_id: str = None):
    """Add email to newsletter subscribers."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO newsletter_subscribers (email, user_id, status)
        VALUES (%s, %s, 'active')
        ON CONFLICT (email) DO UPDATE SET status = 'active', unsubscribed_at = NULL
    """, (email, user_id))
    conn.commit()
    cur.close()
    conn.close()


def unsubscribe_user(email: str):
    """Remove email from newsletter."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        UPDATE newsletter_subscribers SET status = 'unsubscribed', unsubscribed_at = NOW()
        WHERE email = %s
    """, (email,))
    conn.commit()
    cur.close()
    conn.close()
