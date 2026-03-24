from PIL import Image, ImageDraw, ImageFont
import os
import math
import random
from datetime import date

WIDTH, HEIGHT = 1080, 1350  # Instagram 4:5 portrait format

# Astrara color palette
COLOR_COSMOS   = (10, 10, 15)
COLOR_SURFACE  = (18, 18, 26)
COLOR_GOLD     = (201, 169, 110)
COLOR_GOLD_DIM = (161, 135, 88)
COLOR_VIOLET   = (123, 94, 167)
COLOR_STARDUST = (240, 237, 232)
COLOR_MUTED    = (160, 158, 170)


def _draw_stars(draw, count=250):
    """Draw twinkling stars on the background."""
    random.seed(42)
    for _ in range(count):
        x = random.randint(0, WIDTH)
        y = random.randint(0, HEIGHT)
        size = random.choice([0.5, 1, 1, 1, 1.5, 2])
        brightness = random.randint(100, 255)
        if random.random() > 0.9:
            # Gold star
            color = (201, 169, 110, brightness)
        else:
            color = (220, 220, 230, brightness)
        r = int(size)
        if r < 1:
            draw.point((x, y), fill=color)
        else:
            draw.ellipse([x - r, y - r, x + r, y + r], fill=color)


def _draw_decorative_circles(draw, cx, cy, radius):
    """Draw decorative concentric circles."""
    for i, r in enumerate([radius, radius + 15, radius + 28]):
        opacity = max(15, 50 - i * 15)
        draw.ellipse([cx - r, cy - r, cx + r, cy + r],
                     outline=(*COLOR_GOLD, opacity), width=1)

    # 12 dots around the circle (zodiac markers)
    for angle_deg in range(0, 360, 30):
        angle = math.radians(angle_deg - 90)
        x = cx + (radius + 5) * math.cos(angle)
        y = cy + (radius + 5) * math.sin(angle)
        draw.ellipse([x - 1.5, y - 1.5, x + 1.5, y + 1.5], fill=(*COLOR_GOLD, 120))


def _load_fonts():
    """Try to load custom fonts from multiple locations."""
    font_dirs = [
        "/app/fonts",
        os.path.join(os.path.dirname(__file__), "..", "fonts"),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "fonts"),
    ]

    for font_dir in font_dirs:
        if not os.path.isdir(font_dir):
            continue
        try:
            fonts = {
                "title": ImageFont.truetype(os.path.join(font_dir, "CormorantGaramond-Bold.ttf"), 54),
                "title_sm": ImageFont.truetype(os.path.join(font_dir, "CormorantGaramond-Bold.ttf"), 40),
                "body": ImageFont.truetype(os.path.join(font_dir, "Inter-Regular.ttf"), 28),
                "small": ImageFont.truetype(os.path.join(font_dir, "Inter-Regular.ttf"), 22),
                "tiny": ImageFont.truetype(os.path.join(font_dir, "Inter-Regular.ttf"), 18),
                "logo": ImageFont.truetype(os.path.join(font_dir, "CormorantGaramond-Bold.ttf"), 36),
                "badge": ImageFont.truetype(os.path.join(font_dir, "Inter-Regular.ttf"), 20),
            }
            print(f"[IMAGE] Fonts loaded from {font_dir}")
            return fonts
        except Exception as e:
            print(f"[IMAGE] Failed to load fonts from {font_dir}: {e}")
            continue

    print("[IMAGE] WARNING: Using fallback fonts - image quality will be poor")
    default = ImageFont.load_default()
    return {k: default for k in ["title", "title_sm", "body", "small", "tiny", "logo", "badge"]}


def _draw_text_centered(draw, text, y, font, color, max_width=860):
    """Draw centered text with word wrapping. Returns total height used."""
    if not text:
        return 0

    words = text.split()
    lines = []
    current = ""
    for word in words:
        test = f"{current} {word}".strip()
        bbox = draw.textbbox((0, 0), test, font=font)
        if bbox[2] - bbox[0] <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)

    total_height = 0
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        line_w = bbox[2] - bbox[0]
        line_h = bbox[3] - bbox[1] + 8
        x = (WIDTH - line_w) // 2
        draw.text((x, y + total_height), line, font=font, fill=color)
        total_height += line_h

    return total_height


def _draw_gold_line(draw, y, width_pct=0.7):
    """Draw a centered gold decorative line."""
    margin = int(WIDTH * (1 - width_pct) / 2)
    draw.line([(margin, y), (WIDTH - margin, y)], fill=(*COLOR_GOLD, 80), width=1)


def generate_post_image(content: dict, target_date: date) -> str:
    """Generate the daily horoscope post image with Astrara branding."""
    img = Image.new("RGBA", (WIDTH, HEIGHT), COLOR_COSMOS + (255,))
    draw = ImageDraw.Draw(img, "RGBA")

    # Subtle gradient - very dark, almost invisible
    for y in range(HEIGHT):
        progress = y / HEIGHT
        # Slight warm tint in the middle
        r_add = int(8 * math.sin(progress * math.pi))
        b_add = int(5 * math.sin(progress * math.pi))
        if r_add > 0 or b_add > 0:
            draw.line([(0, y), (WIDTH, y)],
                      fill=(10 + r_add, 10, 15 + b_add, 30))

    # Stars
    _draw_stars(draw)

    fonts = _load_fonts()

    # ── TOP SECTION ──────────────────────────────────────
    # Decorative circle
    _draw_decorative_circles(draw, WIDTH // 2, 120, 55)

    # Logo
    _draw_text_centered(draw, "✦ ASTRARA ✦", 88, fonts["logo"], COLOR_GOLD)

    # Date
    MONTHS = {
        1: "janeiro", 2: "fevereiro", 3: "marco", 4: "abril",
        5: "maio", 6: "junho", 7: "julho", 8: "agosto",
        9: "setembro", 10: "outubro", 11: "novembro", 12: "dezembro",
    }
    date_str = f"{target_date.day} de {MONTHS[target_date.month]} de {target_date.year}"
    _draw_text_centered(draw, date_str, 190, fonts["small"], COLOR_MUTED)

    # Gold separator
    _draw_gold_line(draw, 235)

    # ── TITLE SECTION ────────────────────────────────────
    titulo = content.get("titulo", "Energia do Dia").upper()
    h_title = _draw_text_centered(draw, titulo, 270, fonts["title"], COLOR_STARDUST)

    # Energy badge
    energia = content.get("energia_do_dia", "Transformacao").upper()
    badge_y = 270 + h_title + 10
    _draw_text_centered(draw, f"✦  {energia}  ✦", badge_y, fonts["badge"], COLOR_GOLD)

    # Separator
    sep1_y = badge_y + 45
    _draw_gold_line(draw, sep1_y)

    # ── HOROSCOPE SECTION ────────────────────────────────
    horoscopo_y = sep1_y + 30
    horoscopo = content.get("horoscopo", "")
    h_horo = _draw_text_centered(draw, horoscopo, horoscopo_y, fonts["body"],
                                  COLOR_STARDUST, max_width=820)

    # ── TRANSITS SECTION ─────────────────────────────────
    transit_sep_y = horoscopo_y + h_horo + 30
    _draw_gold_line(draw, transit_sep_y, 0.5)

    transit_label_y = transit_sep_y + 18
    _draw_text_centered(draw, "TRANSITOS DO DIA", transit_label_y,
                        fonts["tiny"], (*COLOR_VIOLET, 220))

    transitos = content.get("transitos", "")
    _draw_text_centered(draw, transitos, transit_label_y + 35, fonts["small"],
                        COLOR_MUTED, max_width=800)

    # ── FOOTER ───────────────────────────────────────────
    _draw_gold_line(draw, HEIGHT - 120)

    _draw_text_centered(draw, "Descubra seu mapa astral", HEIGHT - 95,
                        fonts["tiny"], COLOR_MUTED)
    _draw_text_centered(draw, "astrara.online", HEIGHT - 65,
                        fonts["title_sm"], COLOR_GOLD)

    # Small dots at very bottom
    for i in range(5):
        x = WIDTH // 2 - 20 + i * 10
        draw.ellipse([x - 1, HEIGHT - 25, x + 1, HEIGHT - 23],
                     fill=(*COLOR_GOLD, 100))

    # ── SAVE ─────────────────────────────────────────────
    output_dir = "/tmp/astrara_posts"
    os.makedirs(output_dir, exist_ok=True)
    filename = f"astrara_{target_date.strftime('%Y%m%d')}.jpg"
    filepath = os.path.join(output_dir, filename)

    final = img.convert("RGB")
    final.save(filepath, "JPEG", quality=95)

    print(f"[IMAGE] Post image saved: {filepath} ({os.path.getsize(filepath)} bytes)")
    return filepath
