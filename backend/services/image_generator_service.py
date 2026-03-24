from PIL import Image, ImageDraw, ImageFont
import os
import math
import random
from datetime import date

WIDTH, HEIGHT = 1080, 1350  # Instagram 4:5 portrait format

COLOR_COSMOS   = (10, 10, 15)
COLOR_SURFACE  = (18, 18, 26)
COLOR_GOLD     = (201, 169, 110)
COLOR_VIOLET   = (123, 94, 167)
COLOR_STARDUST = (240, 237, 232)
COLOR_MUTED    = (139, 138, 155)


def draw_stars(draw, count=220):
    random.seed(42)
    for _ in range(count):
        x = random.randint(0, WIDTH)
        y = random.randint(0, HEIGHT)
        size = random.choice([1, 1, 1, 2, 2, 3])
        opacity = random.randint(80, 220)
        color = (*COLOR_GOLD[:3], opacity) if random.random() > 0.85 else (240, 237, 232, opacity)
        draw.ellipse([x - size, y - size, x + size, y + size], fill=color)


def draw_mandala_decorativa(draw, cx, cy, radius):
    for i, r in enumerate([radius, radius + 20, radius + 35]):
        opacity = [60, 40, 25][i]
        color = (*COLOR_GOLD, opacity)
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline=color, width=1)

    for angle_deg in range(0, 360, 30):
        angle = math.radians(angle_deg)
        x = cx + (radius + 8) * math.cos(angle)
        y = cy + (radius + 8) * math.sin(angle)
        draw.ellipse([x - 2, y - 2, x + 2, y + 2], fill=(*COLOR_GOLD, 180))


def _load_fonts():
    """Try to load custom fonts, fallback to default."""
    font_dirs = ["/app/fonts", os.path.join(os.path.dirname(__file__), "..", "fonts")]

    for font_dir in font_dirs:
        try:
            return {
                "title": ImageFont.truetype(os.path.join(font_dir, "CormorantGaramond-Bold.ttf"), 56),
                "subtitle": ImageFont.truetype(os.path.join(font_dir, "CormorantGaramond-Italic.ttf"), 34),
                "body": ImageFont.truetype(os.path.join(font_dir, "Inter-Regular.ttf"), 30),
                "small": ImageFont.truetype(os.path.join(font_dir, "Inter-Regular.ttf"), 24),
                "logo": ImageFont.truetype(os.path.join(font_dir, "CormorantGaramond-Bold.ttf"), 42),
                "energia": ImageFont.truetype(os.path.join(font_dir, "Inter-Regular.ttf"), 26),
                "cta": ImageFont.truetype(os.path.join(font_dir, "Inter-Regular.ttf"), 22),
            }
        except Exception:
            continue

    # Fallback
    default = ImageFont.load_default()
    return {k: default for k in ["title", "subtitle", "body", "small", "logo", "energia", "cta"]}


def _draw_centered_text(draw, text, y, font, color, max_width=840):
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
    for i, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=font)
        line_height = bbox[3] - bbox[1] + 10
        x = (WIDTH - (bbox[2] - bbox[0])) // 2
        draw.text((x, y + i * line_height), line, font=font, fill=color)
        total_height += line_height

    return total_height


def generate_post_image(content: dict, target_date: date) -> str:
    img = Image.new("RGBA", (WIDTH, HEIGHT), COLOR_COSMOS + (255,))
    draw = ImageDraw.Draw(img, "RGBA")

    # Gradient background
    for y in range(HEIGHT):
        alpha = int(25 * (y / HEIGHT))
        draw.line([(0, y), (WIDTH, y)], fill=(*COLOR_VIOLET, alpha))

    draw_stars(draw)

    # Top mandala decoration
    draw_mandala_decorativa(draw, WIDTH // 2, 180, 80)

    fonts = _load_fonts()

    # Logo
    _draw_centered_text(draw, "ASTRARA", 120, fonts["logo"], COLOR_GOLD)

    # Date
    MONTH_NAMES = {
        1: "janeiro", 2: "fevereiro", 3: "marco", 4: "abril",
        5: "maio", 6: "junho", 7: "julho", 8: "agosto",
        9: "setembro", 10: "outubro", 11: "novembro", 12: "dezembro",
    }
    date_str = f"{target_date.day} de {MONTH_NAMES[target_date.month]} de {target_date.year}"
    _draw_centered_text(draw, date_str, 220, fonts["small"], COLOR_MUTED)

    # Gold separator
    draw.line([(120, 290), (960, 290)], fill=(*COLOR_GOLD, 120), width=1)
    draw.line([(120, 292), (960, 292)], fill=(*COLOR_GOLD, 40), width=1)

    # Title
    titulo = content.get("titulo", "Energia do Dia").upper()
    h = _draw_centered_text(draw, titulo, 320, fonts["title"], COLOR_STARDUST)

    # Energy badge
    energia = content.get("energia_do_dia", "Transformacao").upper()
    _draw_centered_text(draw, f"✦  {energia}  ✦", 320 + h + 15, fonts["energia"], COLOR_GOLD)

    # Separator
    badge_y = 320 + h + 65
    draw.line([(180, badge_y), (900, badge_y)], fill=(*COLOR_GOLD, 60), width=1)

    # Horoscope section
    horoscopo_y = badge_y + 30
    horoscopo = content.get("horoscopo", "")
    h2 = _draw_centered_text(draw, horoscopo, horoscopo_y, fonts["body"], COLOR_STARDUST, max_width=820)

    # Violet separator
    sep2_y = horoscopo_y + h2 + 30
    draw.line([(180, sep2_y), (900, sep2_y)], fill=(*COLOR_VIOLET, 80), width=1)

    # Transits section
    transit_label_y = sep2_y + 20
    _draw_centered_text(draw, "TRANSITOS DO DIA", transit_label_y, fonts["small"], (*COLOR_VIOLET, 220))

    transitos = content.get("transitos", "")
    _draw_centered_text(draw, transitos, transit_label_y + 40, fonts["small"], COLOR_MUTED, max_width=820)

    # Bottom section - CTA
    draw.line([(120, HEIGHT - 130), (960, HEIGHT - 130)], fill=(*COLOR_GOLD, 80), width=1)

    # CTA text
    _draw_centered_text(draw, "Descubra seu mapa astral em", HEIGHT - 100, fonts["cta"], COLOR_MUTED)
    _draw_centered_text(draw, "astrara.online", HEIGHT - 70, fonts["logo"], COLOR_GOLD)

    # Small mandala at bottom
    draw_mandala_decorativa(draw, WIDTH // 2, HEIGHT - 40, 25)

    # Save as JPEG (required by Meta API)
    output_dir = "/tmp/astrara_posts"
    os.makedirs(output_dir, exist_ok=True)
    filename = f"astrara_{target_date.strftime('%Y%m%d')}.jpg"
    filepath = os.path.join(output_dir, filename)

    final = img.convert("RGB")
    final.save(filepath, "JPEG", quality=95)

    return filepath
