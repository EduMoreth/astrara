import hashlib
import json
from typing import Optional
from fastapi import APIRouter, HTTPException, Header, Request
from fastapi.responses import Response
from pydantic import BaseModel
from models.chart import ChartRequest
from services.astro_service import generate_chart
from services.geocoding_service import geocode, search_cities
from services.interpretation_service import (
    generate_interpretation,
    generate_pdf,
    generate_synastry_interpretation,
    generate_synastry_pdf,
)
from services.synastry_service import compute_synastry
from database import get_connection

router = APIRouter(prefix="/chart", tags=["chart"])


@router.get("/search-city")
async def search_city(q: str = "", country: str = ""):
    """Search cities for autocomplete. Returns multiple matches with coordinates."""
    if len(q) < 2:
        return []
    try:
        results = search_cities(q, country if country else None, limit=5)
        return results
    except Exception as e:
        print(f"City search error: {e}")
        return []


def get_optional_user(authorization: Optional[str] = Header(None)) -> Optional[dict]:
    """Get user if token provided, None otherwise."""
    if not authorization or not authorization.startswith("Bearer "):
        return None
    try:
        from routers.auth import verify_token
        return verify_token(authorization.replace("Bearer ", ""))
    except Exception:
        return None


@router.post("/generate")
async def generate(data: ChartRequest, request: Request = None, authorization: Optional[str] = Header(None)):
    try:
        coords = geocode(data.city, data.country)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    try:
        result = generate_chart(
            data.name,
            data.year,
            data.month,
            data.day,
            data.hour,
            data.minute,
            coords["lat"],
            coords["lng"],
            coords["tz_str"],
        )
    except Exception as e:
        print(f"Chart calculation error: {e}")
        raise HTTPException(
            status_code=500,
            detail="Erro ao calcular o mapa astral. Tente novamente.",
        )

    # Log chart generation (tracks ALL generations for admin metrics)
    try:
        user = get_optional_user(authorization)
        user_id = user["sub"] if user else None
        ip = request.client.host if request and request.client else None
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO chart_generations (user_id, name, birth_date, birth_time, birth_city, birth_country, lat, lng, ip_address)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            user_id, data.name,
            f"{data.year}-{data.month:02d}-{data.day:02d}",
            f"{data.hour:02d}:{data.minute:02d}",
            data.city, data.country,
            coords["lat"], coords["lng"], ip,
        ))
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Chart gen log error: {e}")

    return {
        "positions": result["positions"],
        "houses": result["houses"],
        "aspects": result.get("aspects", []),
        "location": {
            "lat": coords["lat"],
            "lng": coords["lng"],
            "tz_str": coords["tz_str"],
            "display_name": coords.get("display_name", ""),
        },
    }


@router.get("/interpretation-product")
async def get_interpretation_product():
    """Get the default interpretation product info for the CTA button."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, name, description, price_cents
        FROM products
        WHERE type = 'one_time' AND active = true AND name ILIKE '%%interpreta%%'
        ORDER BY created_at ASC LIMIT 1
    """)
    product = cur.fetchone()
    cur.close()
    conn.close()

    if not product:
        return {"id": None, "name": "Interpretacao Completa", "price_cents": 2990}

    return {
        "id": str(product["id"]),
        "name": product["name"],
        "description": product["description"],
        "price_cents": product["price_cents"],
    }


@router.post("/interpretation/{chart_id}/pdf")
async def get_interpretation_pdf(chart_id: str, authorization: Optional[str] = Header(None)):
    """Generate and return the interpretation PDF. Requires auth + credits/purchase.
    If already generated for this user+chart, serve cached version without deducting credits."""
    user = get_optional_user(authorization)
    if not user:
        raise HTTPException(status_code=401, detail="Login necessario")

    user_id = user["sub"]
    conn = get_connection()
    cur = conn.cursor()

    # Get the chart — scoped to the requesting user (IDOR guard: never serve
    # another user's birth data / interpretation)
    cur.execute("SELECT * FROM charts WHERE id = %s AND user_id = %s", (chart_id, user_id))
    chart_data = cur.fetchone()
    if not chart_data:
        cur.close()
        conn.close()
        raise HTTPException(status_code=404, detail="Mapa nao encontrado")

    positions = chart_data.get("positions_json") or {}
    name = chart_data.get("name", "")
    pos_hash = _positions_hash(positions)

    # ── Check cache first ──
    cur.execute("""
        SELECT interpretation_text FROM chart_interpretations
        WHERE user_id = %s AND positions_hash = %s
    """, (user_id, pos_hash))
    cached = cur.fetchone()

    if cached:
        cur.close()
        conn.close()
        interpretation_text = cached["interpretation_text"]
        pdf_bytes = generate_pdf(name, positions, interpretation_text)
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="astrara-mapa-{name.lower().replace(" ", "-")}.pdf"'
            },
        )

    # ── No cache — a NEW interpretation always consumes a credit ──
    # (Re-downloads of an already-generated interpretation are served free from
    # the cache above. A past completed purchase does NOT grant unlimited new
    # interpretations — each generation costs 1 credit.)
    cur.execute("""
        UPDATE user_credits SET credits_balance = credits_balance - 1,
                                total_used = total_used + 1,
                                updated_at = NOW()
        WHERE user_id = %s AND credits_balance > 0
        RETURNING credits_balance
    """, (user_id,))
    updated = cur.fetchone()
    if not updated:
        conn.rollback()
        cur.close()
        conn.close()
        raise HTTPException(status_code=402, detail="Creditos insuficientes. Adquira creditos para desbloquear a interpretacao.")
    cur.execute("""
        INSERT INTO credit_transactions (user_id, type, amount, description)
        VALUES (%s, 'use', -1, 'Interpretacao do mapa astral')
    """, (user_id,))
    conn.commit()

    # Generate interpretation
    interpretation_text = generate_interpretation(positions, name)

    # ── Cache the interpretation ──
    try:
        cur.execute("""
            INSERT INTO chart_interpretations (user_id, positions_hash, name, interpretation_text)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (user_id, positions_hash) DO NOTHING
        """, (user_id, pos_hash, name, interpretation_text))
        conn.commit()
    except Exception as e:
        print(f"Cache save error: {e}")

    cur.close()
    conn.close()

    # Generate PDF
    pdf_bytes = generate_pdf(name, positions, interpretation_text)

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="astrara-mapa-{name.lower().replace(" ", "-")}.pdf"'
        },
    )


@router.get("/check-interpretation-access")
async def check_interpretation_access(authorization: Optional[str] = Header(None)):
    """Check if user can access interpretation (has credits or purchase).
    Returns: { has_access: bool, credits: int, reason: str }
    """
    user = get_optional_user(authorization)
    if not user:
        return {"has_access": False, "credits": 0, "reason": "not_logged_in"}

    conn = get_connection()
    cur = conn.cursor()

    # Check credits
    cur.execute("SELECT credits_balance FROM user_credits WHERE user_id = %s", (user["sub"],))
    credits_row = cur.fetchone()
    credits = credits_row["credits_balance"] if credits_row else 0

    if credits > 0:
        cur.close()
        conn.close()
        return {"has_access": True, "credits": credits, "reason": "has_credits"}

    # Check purchases
    cur.execute("""
        SELECT id FROM purchases WHERE user_id = %s AND status = 'completed' LIMIT 1
    """, (user["sub"],))
    has_purchase = cur.fetchone() is not None

    cur.close()
    conn.close()

    if has_purchase:
        return {"has_access": True, "credits": 0, "reason": "has_purchase"}

    return {"has_access": False, "credits": 0, "reason": "no_credits"}


class PdfRequest(BaseModel):
    positions: dict
    name: str = "Meu Mapa Astral"


def _positions_hash(positions: dict) -> str:
    """Generate a stable hash from chart positions for cache lookup."""
    canonical = json.dumps(positions, sort_keys=True, ensure_ascii=True)
    return hashlib.sha256(canonical.encode()).hexdigest()


@router.post("/interpretation/generate-pdf")
async def generate_interpretation_pdf_direct(data: PdfRequest, authorization: Optional[str] = Header(None)):
    """Generate PDF directly from positions sent by frontend. Requires auth + credits/purchase.
    If the interpretation was already generated for this user+positions, serve cached version
    without deducting another credit."""
    user = get_optional_user(authorization)
    if not user:
        raise HTTPException(status_code=401, detail="Login necessario para baixar o PDF")

    user_id = user["sub"]
    pos_hash = _positions_hash(data.positions)

    conn = get_connection()
    cur = conn.cursor()

    # ── Check cache: if this user already generated this interpretation, reuse it ──
    cur.execute("""
        SELECT interpretation_text FROM chart_interpretations
        WHERE user_id = %s AND positions_hash = %s
    """, (user_id, pos_hash))
    cached = cur.fetchone()

    if cached:
        # Already paid before — serve cached PDF without deducting credits
        cur.close()
        conn.close()
        interpretation_text = cached["interpretation_text"]
        pdf_bytes = generate_pdf(data.name, data.positions, interpretation_text)
        safe_name = data.name.lower().replace(" ", "-")[:30]
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="astrara-interpretacao-{safe_name}.pdf"'
            },
        )

    # ── No cache — a NEW interpretation always consumes a credit ──
    # (Cached interpretations are re-downloadable for free above. A past completed
    # purchase does NOT grant unlimited new interpretations.)
    cur.execute("""
        UPDATE user_credits
        SET credits_balance = credits_balance - 1,
            total_used = total_used + 1,
            updated_at = NOW()
        WHERE user_id = %s AND credits_balance > 0
        RETURNING credits_balance
    """, (user_id,))
    updated = cur.fetchone()
    if not updated:
        conn.rollback()
        cur.close()
        conn.close()
        raise HTTPException(
            status_code=402,
            detail="Voce precisa comprar a interpretacao antes de baixar o PDF."
        )

    cur.execute("""
        INSERT INTO credit_transactions (user_id, type, amount, description)
        VALUES (%s, 'use', -1, 'Interpretacao completa do mapa astral (PDF)')
    """, (user_id,))

    conn.commit()

    # Generate interpretation with AI
    interpretation_text = generate_interpretation(data.positions, data.name)

    # ── Cache the interpretation for future re-downloads ──
    try:
        cur.execute("""
            INSERT INTO chart_interpretations (user_id, positions_hash, name, interpretation_text)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (user_id, positions_hash) DO NOTHING
        """, (user_id, pos_hash, data.name, interpretation_text))
        conn.commit()
    except Exception as e:
        print(f"Cache save error: {e}")

    cur.close()
    conn.close()

    # Generate beautiful PDF
    pdf_bytes = generate_pdf(data.name, data.positions, interpretation_text)

    safe_name = data.name.lower().replace(" ", "-")[:30]
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="astrara-interpretacao-{safe_name}.pdf"'
        },
    )


# ── Sinastria (synastry) ─────────────────────────────────────

class SynastryPerson(BaseModel):
    name: str
    year: int
    month: int
    day: int
    hour: int = 12
    minute: int = 0
    city: str
    country: Optional[str] = None


class SynastryRequest(BaseModel):
    person_a: SynastryPerson
    person_b: SynastryPerson


class SynastryPdfPerson(BaseModel):
    name: str = "Pessoa"
    positions: dict


class SynastryPdfRequest(BaseModel):
    person_a: SynastryPdfPerson
    person_b: SynastryPdfPerson


def _synastry_credits_cost() -> int:
    """Credits consumed per synastry analysis (system_config, default 2)."""
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT value FROM system_config WHERE key = 'credits_per_synastry'")
        row = cur.fetchone()
        cur.close()
        conn.close()
        if row and str(row["value"]).strip().isdigit():
            return max(1, int(row["value"]))
    except Exception as e:
        print(f"Synastry cost config error: {e}")
    return 2


def _synastry_hash(positions_a: dict, positions_b: dict) -> str:
    """Stable cache hash for a pair of charts — order-independent, so
    (A, B) and (B, A) hit the same cached interpretation."""
    canon_a = json.dumps(positions_a, sort_keys=True, ensure_ascii=True)
    canon_b = json.dumps(positions_b, sort_keys=True, ensure_ascii=True)
    pair = "|synastry|".join(sorted([canon_a, canon_b]))
    return hashlib.sha256(pair.encode()).hexdigest()


@router.get("/synastry-product")
async def get_synastry_product():
    """Get the synastry product info for the CTA button."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, name, description, price_cents, credits
        FROM products
        WHERE active = true AND name ILIKE '%%sinastria%%'
        ORDER BY created_at ASC LIMIT 1
    """)
    product = cur.fetchone()
    cur.close()
    conn.close()

    if not product:
        return {"id": None, "name": "Sinastria", "price_cents": 7800, "credits": 0}

    return {
        "id": str(product["id"]),
        "name": product["name"],
        "description": product["description"],
        "price_cents": product["price_cents"],
        "credits": product["credits"],
    }


@router.post("/synastry")
async def generate_synastry(data: SynastryRequest, request: Request = None,
                            authorization: Optional[str] = Header(None)):
    """Generate both natal charts and the free synastry preview:
    inter-chart aspects + affinity scores. The deep AI analysis (PDF) is paid."""
    charts = {}
    for label, person in (("a", data.person_a), ("b", data.person_b)):
        try:
            coords = geocode(person.city, person.country)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        try:
            charts[label] = generate_chart(
                person.name, person.year, person.month, person.day,
                person.hour, person.minute,
                coords["lat"], coords["lng"], coords["tz_str"],
            )
            charts[label]["coords"] = coords
        except Exception as e:
            print(f"Synastry chart calculation error ({label}): {e}")
            raise HTTPException(
                status_code=500,
                detail="Erro ao calcular os mapas astrais. Tente novamente.",
            )

    synastry = compute_synastry(
        charts["a"]["positions"], charts["b"]["positions"]
    )

    # Log both generations for admin metrics (best-effort)
    try:
        user = get_optional_user(authorization)
        user_id = user["sub"] if user else None
        ip = request.client.host if request and request.client else None
        conn = get_connection()
        cur = conn.cursor()
        for person, chart in ((data.person_a, charts["a"]), (data.person_b, charts["b"])):
            cur.execute("""
                INSERT INTO chart_generations (user_id, name, birth_date, birth_time, birth_city, birth_country, lat, lng, ip_address)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                user_id, person.name,
                f"{person.year}-{person.month:02d}-{person.day:02d}",
                f"{person.hour:02d}:{person.minute:02d}",
                person.city, person.country,
                chart["coords"]["lat"], chart["coords"]["lng"], ip,
            ))
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Synastry gen log error: {e}")

    return {
        "chart_a": {k: charts["a"][k] for k in ("positions", "houses", "aspects")},
        "chart_b": {k: charts["b"][k] for k in ("positions", "houses", "aspects")},
        "inter_aspects": synastry["inter_aspects"],
        "scores": synastry["scores"],
        "credits_cost": _synastry_credits_cost(),
    }


@router.post("/synastry/generate-pdf")
async def generate_synastry_pdf_endpoint(data: SynastryPdfRequest,
                                         authorization: Optional[str] = Header(None)):
    """Generate the full synastry analysis PDF. Requires auth + credits.
    Cached per user+pair: re-downloads are free and don't deduct again."""
    user = get_optional_user(authorization)
    if not user:
        raise HTTPException(status_code=401, detail="Login necessario para baixar a analise")

    user_id = user["sub"]
    pos_a = data.person_a.positions or {}
    pos_b = data.person_b.positions or {}
    if not pos_a or not pos_b:
        raise HTTPException(status_code=400, detail="Dados dos mapas incompletos.")

    pair_hash = _synastry_hash(pos_a, pos_b)
    pair_name = f"{data.person_a.name} & {data.person_b.name}"

    conn = get_connection()
    cur = conn.cursor()

    # ── Cache first: already generated for this user+pair → free re-download ──
    cur.execute("""
        SELECT interpretation_text FROM chart_interpretations
        WHERE user_id = %s AND positions_hash = %s
    """, (user_id, pair_hash))
    cached = cur.fetchone()

    synastry = compute_synastry(pos_a, pos_b)

    if cached:
        cur.close()
        conn.close()
        pdf_bytes = generate_synastry_pdf(
            data.person_a.name, pos_a, data.person_b.name, pos_b,
            synastry["scores"], cached["interpretation_text"],
        )
        safe = pair_name.lower().replace(" ", "-")[:40]
        return Response(
            content=pdf_bytes, media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="astrara-sinastria-{safe}.pdf"'},
        )

    # ── New analysis: consume credits atomically ──
    cost = _synastry_credits_cost()
    cur.execute("""
        UPDATE user_credits
        SET credits_balance = credits_balance - %s,
            total_used = total_used + %s,
            updated_at = NOW()
        WHERE user_id = %s AND credits_balance >= %s
        RETURNING credits_balance
    """, (cost, cost, user_id, cost))
    updated = cur.fetchone()
    if not updated:
        conn.rollback()
        cur.close()
        conn.close()
        raise HTTPException(
            status_code=402,
            detail=f"A sinastria consome {cost} credito(s). Adquira o produto Sinastria para desbloquear.",
        )
    cur.execute("""
        INSERT INTO credit_transactions (user_id, type, amount, description)
        VALUES (%s, 'use', %s, 'Analise de sinastria (PDF)')
    """, (user_id, -cost))
    conn.commit()

    # Generate the AI analysis
    interpretation_text = generate_synastry_interpretation(
        data.person_a.name, pos_a, data.person_b.name, pos_b,
        synastry["inter_aspects"], synastry["scores"],
    )

    # Cache for future free re-downloads
    try:
        cur.execute("""
            INSERT INTO chart_interpretations (user_id, positions_hash, name, interpretation_text)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (user_id, positions_hash) DO NOTHING
        """, (user_id, pair_hash, pair_name[:100], interpretation_text))
        conn.commit()
    except Exception as e:
        print(f"Synastry cache save error: {e}")

    cur.close()
    conn.close()

    pdf_bytes = generate_synastry_pdf(
        data.person_a.name, pos_a, data.person_b.name, pos_b,
        synastry["scores"], interpretation_text,
    )
    safe = pair_name.lower().replace(" ", "-")[:40]
    return Response(
        content=pdf_bytes, media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="astrara-sinastria-{safe}.pdf"'},
    )
