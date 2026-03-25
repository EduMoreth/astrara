import os
import re
import anthropic
from database import get_connection

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# SEO topics for astrology blog
BLOG_TOPICS = [
    "O que e mapa astral e como ele funciona",
    "Como interpretar seu signo solar, lunar e ascendente",
    "Os 12 signos do zodiaco: caracteristicas completas",
    "Casas astrologicas: significado de cada uma das 12 casas",
    "Aspectos planetarios: conjuncao, oposicao, trigono e quadratura",
    "Mapa astral de {sign}: personalidade, amor e carreira",
    "Lua em {sign}: como suas emocoes se manifestam",
    "Ascendente em {sign}: a mascara que voce usa no mundo",
    "Venus em {sign}: como voce ama e se relaciona",
    "Marte em {sign}: sua energia, motivacao e desejo",
    "Saturno retrogrado: o que significa e como te afeta",
    "Jupiter em transito: oportunidades e expansao",
    "Sinastria: como comparar dois mapas astrais",
    "Revolucao solar: seu mapa do ano",
    "Planetas retrogrados: guia completo",
    "Nodos lunares: seu proposito de vida na astrologia",
    "Quiron no mapa astral: a ferida e a cura",
    "Plutao em Aquario: transformacao coletiva",
    "Como a Lua influencia seu dia a dia",
    "Astrologia e autoconhecimento: um guia pratico",
]

SIGNS = ["Aries", "Touro", "Gemeos", "Cancer", "Leao", "Virgem",
         "Libra", "Escorpiao", "Sagitario", "Capricornio", "Aquario", "Peixes"]


def generate_blog_post(topic: str = None) -> dict:
    """Generate a complete SEO blog post about astrology."""
    if not topic:
        # Pick a random topic
        import random
        topic = random.choice(BLOG_TOPICS)
        # Replace {sign} with random sign
        if "{sign}" in topic:
            topic = topic.replace("{sign}", random.choice(SIGNS))

    prompt = f"""Voce e um astrologo experiente e escritor de blog SEO. Escreva um artigo completo sobre:

"{topic}"

REQUISITOS:
- Titulo otimizado para SEO (H1) com a palavra-chave principal
- Meta description de 150-160 caracteres
- Slug amigavel para URL (sem acentos, separado por hifens)
- Conteudo com 1500-2500 palavras
- Use H2 e H3 para subtitulos
- Linguagem acessivel mas com profundidade astrologica
- Inclua exemplos praticos
- Termine com um CTA para "Calcule seu mapa astral gratuitamente em astrara.online"
- Tom: inspirador, poetico mas informativo
- Formato: Markdown

Retorne APENAS um JSON valido:
{{
  "title": "titulo do artigo",
  "slug": "slug-do-artigo-sem-acentos",
  "meta_description": "meta description de 150-160 chars",
  "category": "categoria (ex: signos, planetas, casas, aspectos, transitos, guias)",
  "tags": "tag1, tag2, tag3",
  "content": "conteudo completo em Markdown"
}}"""

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4000,
        messages=[{"role": "user", "content": prompt}],
    )

    import json
    raw = message.content[0].text.strip()
    raw = raw.replace("```json", "").replace("```", "").strip()
    return json.loads(raw)


def save_blog_post(post_data: dict, publish: bool = True) -> str:
    """Save blog post to database. Returns post ID."""
    conn = get_connection()
    cur = conn.cursor()

    status = "published" if publish else "draft"

    cur.execute("""
        INSERT INTO blog_posts (slug, title, meta_description, content, category, tags, status, published_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
        ON CONFLICT (slug) DO UPDATE SET
            title = EXCLUDED.title,
            content = EXCLUDED.content,
            meta_description = EXCLUDED.meta_description,
            updated_at = NOW()
        RETURNING id
    """, (
        post_data["slug"],
        post_data["title"],
        post_data["meta_description"],
        post_data["content"],
        post_data.get("category", ""),
        post_data.get("tags", ""),
        status,
    ))
    post_id = str(cur.fetchone()["id"])
    conn.commit()
    cur.close()
    conn.close()
    return post_id


def generate_and_publish_blog_post(topic: str = None) -> dict:
    """Full flow: generate + save + publish."""
    post_data = generate_blog_post(topic)
    post_id = save_blog_post(post_data, publish=True)
    return {"id": post_id, **post_data}
