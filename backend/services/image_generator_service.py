from PIL import Image, ImageDraw, ImageFont
import os
import math
import random
from datetime import date

WIDTH, HEIGHT = 1080, 1080

COLOR_COSMOS   = (10, 10, 15)
COLOR_GOLD     = (201, 169, 110)
COLOR_VIOLET   = (123, 94, 167)
COLOR_STARDUST = (240, 237, 232)
COLOR_MUTED    = (139, 138, 155)


def draw_stars(draw, count=180):
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
                "title": ImageFont.truetype(os.path.join(font_dir, "CormorantGaramond-Bold.ttf"), 52),
                "subtitle": ImageFont.truetype(os.path.join(font_dir, "CormorantGaramond-Italic.ttf"), 32),
                "body": ImageFont.truetype(os.path.join(font_dir, "Inter-Regular.ttf"), 28),
                "small": ImageFont.truetype(os.path.join(font_dir, "Inter-Regular.ttf"), 22),
                "logo": ImageFont.truetype(os.path.join(font_dir, "CormorantGaramond-Bold.ttf"), 38),
                "energia": ImageFont.truetype(os.path.join(font_dir, "Inter-Regular.ttf"), 24),
            }
        except Exception:
            continue

    # Fallback
    default = ImageFont.load_default()
    return {k: default for k in ["title", "subtitle", "body", "small", "logo", "energia"]}


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
        line_height = bbox[3] - bbox[1] + 8
        x = (WIDTH - (bbox[2] - bbox[0])) // 2
        draw.text((x, y + i * line_height), line, font=font, fill=color)
        total_height += line_height

    return total_height


def generate_post_image(content: dict, target_date: date) -> str:
    img = Image.new("RGBA", (WIDTH, HEIGHT), COLOR_COSMOS + (255,))
    draw = ImageDraw.Draw(img, "RGBA")

    # Gradient background
    for y in range(HEIGHT):
        alpha = int(30 * (y / HEIGHT))
        draw.line([(0, y), (WIDTH, y)], fill=(*COLOR_VIOLET, alpha))

    draw_stars(draw)
    draw_mandala_decorativa(draw, WIDTH // 2, 200, 80)

    # Separator
    draw.line([(120, 310), (960, 310)], fill=(*COLOR_GOLD, 120), width=1)

    fonts = _load_fonts()

    # Logo
    _draw_centered_text(draw, "ASTRARA", 140, fonts["logo"], COLOR_GOLD)

    # Date
    MONTH_NAMES = {
        1: "janeiro", 2: "fevereiro", 3: "marco", 4: "abril",
        5: "maio", 6: "junho", 7: "julho", 8: "agosto",
        9: "setembro", 10: "outubro", 11: "novembro", 12: "dezembro",
    }
    date_str = f"{target_date.day} de {MONTH_NAMES[target_date.month]} de {target_date.year}"
    _draw_centered_text(draw, date_str, 230, fonts["small"], COLOR_MUTED)

    # Title
    titulo = content.get("titulo", "Energia do Dia").upper()
    _draw_centered_text(draw, titulo, 340, fonts["title"], COLOR_STARDUST)

    # Energy badge
    energia = f"  {content.get('energia_do_dia', 'Transformacao').upper()}  "
    _draw_centered_text(draw, energia, 420, fonts["energia"], COLOR_GOLD)

    # Separator
    draw.line([(200, 480), (880, 480)], fill=(*COLOR_GOLD, 60), width=1)

    # Horoscope
    horoscopo = content.get("horoscopo", "")
    _draw_centered_text(draw, horoscopo, 510, fonts["body"], COLOR_STARDUST, max_width=820)

    # Separator
    draw.line([(200, 760), (880, 760)], fill=(*COLOR_VIOLET, 80), width=1)

    # Transits
    _draw_centered_text(draw, "TRANSITOS DO DIA", 785, fonts["small"], (*COLOR_VIOLET, 200))
    transitos = content.get("transitos", "")
    _draw_centered_text(draw, transitos, 820, fonts["small"], COLOR_MUTED, max_width=820)

    # Footer
    draw.line([(120, 980), (960, 980)], fill=(*COLOR_GOLD, 60), width=1)
    _draw_centered_text(draw, "astrara.online", 995, fonts["small"], (*COLOR_GOLD, 180))

    # Save
    output_dir = "/tmp/astrara_posts"
    os.makedirs(output_dir, exist_ok=True)
    filename = f"astrara_{target_date.strftime('%Y%m%d')}.png"
    filepath = os.path.join(output_dir, filename)

    final = img.convert("RGB")
    final.save(filepath, "PNG", quality=95)

    return filepath
