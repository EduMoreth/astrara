from PIL import Image, ImageDraw, ImageFont
import os
import math
import random
from datetime import date

WIDTH, HEIGHT = 1080, 1350

# Colors
BG = (8, 8, 14)
GOLD = (201, 169, 110)
GOLD_BRIGHT = (225, 195, 130)
VIOLET = (150, 120, 200)
WHITE = (245, 242, 236)
GRAY = (170, 168, 180)
DARK_SURFACE = (16, 16, 24)


def _load_fonts():
    dirs = ["/app/fonts", os.path.join(os.path.dirname(__file__), "..", "fonts")]
    for d in dirs:
        if not os.path.isdir(d):
            continue
        try:
            f = {
                "logo": ImageFont.truetype(os.path.join(d, "CormorantGaramond-Bold.ttf"), 48),
                "date": ImageFont.truetype(os.path.join(d, "Inter-Regular.ttf"), 24),
                "title": ImageFont.truetype(os.path.join(d, "CormorantGaramond-Bold.ttf"), 64),
                "badge": ImageFont.truetype(os.path.join(d, "CormorantGaramond-Bold.ttf"), 32),
                "body": ImageFont.truetype(os.path.join(d, "Inter-Regular.ttf"), 32),
                "section": ImageFont.truetype(os.path.join(d, "Inter-Regular.ttf"), 20),
                "transit": ImageFont.truetype(os.path.join(d, "Inter-Regular.ttf"), 26),
                "cta": ImageFont.truetype(os.path.join(d, "CormorantGaramond-Bold.ttf"), 36),
                "url": ImageFont.truetype(os.path.join(d, "CormorantGaramond-Bold.ttf"), 44),
            }
            print(f"[IMAGE] Fonts loaded from {d}")
            return f
        except Exception as e:
            print(f"[IMAGE] Font load failed from {d}: {e}")
    print("[IMAGE] WARNING: Using fallback fonts")
    df = ImageFont.load_default()
    return {k: df for k in ["logo", "date", "title", "badge", "body", "section", "transit", "cta", "url"]}


def _center_text(draw, text, y, font, color, max_w=900):
    """Draw centered wrapped text. Returns height used."""
    if not text:
        return 0
    words = text.split()
    lines, cur = [], ""
    for w in words:
        t = f"{cur} {w}".strip()
        bb = draw.textbbox((0, 0), t, font=font)
        if bb[2] - bb[0] <= max_w:
            cur = t
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)

    h = 0
    for line in lines:
        bb = draw.textbbox((0, 0), line, font=font)
        lw = bb[2] - bb[0]
        lh = bb[3] - bb[1] + 12
        draw.text(((WIDTH - lw) // 2, y + h), line, font=font, fill=color)
        h += lh
    return h


def _gold_line(draw, y, w=0.65):
    m = int(WIDTH * (1 - w) / 2)
    draw.line([(m, y), (WIDTH - m, y)], fill=(*GOLD, 100), width=1)


def _draw_stars(draw):
    random.seed(42)
    for _ in range(300):
        x, y = random.randint(0, WIDTH), random.randint(0, HEIGHT)
        s = random.choice([0.5, 1, 1, 1.5])
        b = random.randint(60, 200)
        c = (*GOLD, b) if random.random() > 0.92 else (200, 200, 210, b)
        r = max(1, int(s))
        draw.ellipse([x-r, y-r, x+r, y+r], fill=c)


def _draw_zodiac_ring(draw, cx, cy, r):
    """Small decorative ring."""
    draw.ellipse([cx-r, cy-r, cx+r, cy+r], outline=(*GOLD, 50), width=1)
    draw.ellipse([cx-r+12, cy-r+12, cx+r-12, cy+r-12], outline=(*GOLD, 30), width=1)
    for a in range(0, 360, 30):
        rad = math.radians(a - 90)
        px = cx + r * math.cos(rad)
        py = cy + r * math.sin(rad)
        draw.ellipse([px-2, py-2, px+2, py+2], fill=(*GOLD, 120))


def generate_post_image(content: dict, target_date: date) -> str:
    img = Image.new("RGBA", (WIDTH, HEIGHT), BG + (255,))
    draw = ImageDraw.Draw(img, "RGBA")

    # Subtle warm gradient in upper portion only
    for y in range(HEIGHT // 3):
        a = int(12 * (1 - y / (HEIGHT // 3)))
        draw.line([(0, y), (WIDTH, y)], fill=(30, 15, 40, a))

    _draw_stars(draw)
    fonts = _load_fonts()

    # ═══════════════════════════════════════════════════
    # TOP: Logo + zodiac ring + date
    # ═══════════════════════════════════════════════════
    _draw_zodiac_ring(draw, WIDTH // 2, 85, 50)
    _center_text(draw, "ASTRARA", 55, fonts["logo"], GOLD_BRIGHT)

    MONTHS = {1:"janeiro",2:"fevereiro",3:"marco",4:"abril",5:"maio",6:"junho",
              7:"julho",8:"agosto",9:"setembro",10:"outubro",11:"novembro",12:"dezembro"}
    ds = f"{target_date.day} de {MONTHS[target_date.month]} de {target_date.year}"
    _center_text(draw, ds, 150, fonts["date"], GRAY)

    _gold_line(draw, 195)

    # ═══════════════════════════════════════════════════
    # TITLE — big and bold
    # ═══════════════════════════════════════════════════
    titulo = content.get("titulo", "Energia do Dia").upper()
    ht = _center_text(draw, titulo, 225, fonts["title"], WHITE)

    # Energy badge
    energia = content.get("energia_do_dia", "Transformacao")
    badge_y = 225 + ht + 8
    _center_text(draw, f"✦  {energia.upper()}  ✦", badge_y, fonts["badge"], GOLD_BRIGHT)

    _gold_line(draw, badge_y + 55)

    # ═══════════════════════════════════════════════════
    # HOROSCOPE — main body, large readable text
    # ═══════════════════════════════════════════════════
    horo_y = badge_y + 80
    horoscopo = content.get("horoscopo", "")
    hh = _center_text(draw, horoscopo, horo_y, fonts["body"], WHITE, max_w=880)

    # ═══════════════════════════════════════════════════
    # TRANSITS — secondary info
    # ═══════════════════════════════════════════════════
    trans_sep_y = horo_y + hh + 35
    _gold_line(draw, trans_sep_y, 0.4)

    _center_text(draw, "✦ TRANSITOS DO DIA ✦", trans_sep_y + 15, fonts["section"], VIOLET)

    transitos = content.get("transitos", "")
    _center_text(draw, transitos, trans_sep_y + 50, fonts["transit"], GRAY, max_w=860)

    # ═══════════════════════════════════════════════════
    # FOOTER — CTA
    # ═══════════════════════════════════════════════════
    # Gold accent bar
    draw.rectangle([(0, HEIGHT - 140), (WIDTH, HEIGHT)], fill=(*DARK_SURFACE, 200))
    _gold_line(draw, HEIGHT - 140)

    _center_text(draw, "Descubra seu mapa astral", HEIGHT - 120, fonts["date"], GRAY)
    _center_text(draw, "astrara.online", HEIGHT - 85, fonts["url"], GOLD_BRIGHT)

    # ═══════════════════════════════════════════════════
    # SAVE
    # ═══════════════════════════════════════════════════
    out = "/tmp/astrara_posts"
    os.makedirs(out, exist_ok=True)
    fp = os.path.join(out, f"astrara_{target_date.strftime('%Y%m%d')}.jpg")
    img.convert("RGB").save(fp, "JPEG", quality=95)
    print(f"[IMAGE] Saved: {fp} ({os.path.getsize(fp)} bytes)")
    return fp
