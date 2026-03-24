import os
import json
import anthropic
from datetime import date
from kerykeion import AstrologicalSubject


def get_daily_transits(target_date: date) -> dict:
    """Calculate planetary positions for the day using Kerykeion."""
    subject = AstrologicalSubject(
        "Daily Transit",
        target_date.year,
        target_date.month,
        target_date.day,
        12, 0,
        lng=-47.9292,
        lat=-15.7801,
        tz_str="America/Sao_Paulo",
        online=False,
    )

    return {
        "date": target_date.strftime("%d/%m/%Y"),
        "sun":     {"sign": subject.sun.sign,     "deg": round(subject.sun.position, 1)},
        "moon":    {"sign": subject.moon.sign,    "deg": round(subject.moon.position, 1)},
        "mercury": {"sign": subject.mercury.sign, "deg": round(subject.mercury.position, 1)},
        "venus":   {"sign": subject.venus.sign,   "deg": round(subject.venus.position, 1)},
        "mars":    {"sign": subject.mars.sign,    "deg": round(subject.mars.position, 1)},
        "jupiter": {"sign": subject.jupiter.sign, "deg": round(subject.jupiter.position, 1)},
        "saturn":  {"sign": subject.saturn.sign,  "deg": round(subject.saturn.position, 1)},
    }


def generate_daily_content(transits: dict) -> dict:
    """Generate daily horoscope content using Claude."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise Exception("ANTHROPIC_API_KEY not configured")

    client = anthropic.Anthropic(api_key=api_key)

    prompt = f"""Voce e um astrologo sofisticado e poetico. Com base nos transitos planetarios de hoje ({transits['date']}), gere o conteudo para o post diario do Instagram da Astrara.

TRANSITOS DE HOJE:
- Sol: {transits['sun']['deg']} em {transits['sun']['sign']}
- Lua: {transits['moon']['deg']} em {transits['moon']['sign']}
- Mercurio: {transits['mercury']['deg']} em {transits['mercury']['sign']}
- Venus: {transits['venus']['deg']} em {transits['venus']['sign']}
- Marte: {transits['mars']['deg']} em {transits['mars']['sign']}
- Jupiter: {transits['jupiter']['deg']} em {transits['jupiter']['sign']}
- Saturno: {transits['saturn']['deg']} em {transits['saturn']['sign']}

Retorne APENAS um JSON valido com esta estrutura exata, sem texto adicional:
{{
  "titulo": "titulo poetico curto do dia (max 8 palavras)",
  "horoscopo": "horoscopo geral do dia (3-4 frases, tom contemplativo e inspirador, em portugues)",
  "transitos": "contexto dos transitos mais relevantes do dia (2-3 frases tecnicas mas acessiveis)",
  "energia_do_dia": "uma palavra ou expressao curta (ex: Transformacao, Clareza Interior, Impulso Criativo)",
  "legenda_instagram": "legenda completa para o post (horoscopo + transitos + CTA para astrara.online, max 2200 chars)",
  "hashtags": "#astrologia #horoscopo #transitos #mapanatal #astrara #cosmos #signos #energiadodia"
}}"""

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1500,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = message.content[0].text.strip()
    raw = raw.replace("```json", "").replace("```", "").strip()
    return json.loads(raw)
