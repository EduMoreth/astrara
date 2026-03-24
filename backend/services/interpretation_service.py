import os
import io
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.colors import HexColor
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY

# Colors
COSMOS = HexColor('#0A0A0F')
SURFACE = HexColor('#12121A')
GOLD = HexColor('#C9A96E')
VIOLET = HexColor('#7B5EA7')
STARDUST = HexColor('#F0EDE8')
MUTED = HexColor('#8B8A9B')
WHITE = HexColor('#FFFFFF')


def generate_interpretation(positions: dict, name: str) -> str:
    """Generate astrological interpretation using Claude AI."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        return _generate_fallback_interpretation(positions, name)

    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)

        # Get AI model from system config or default
        model = os.getenv("AI_MODEL", "claude-sonnet-4-6")

        planets_text = "\n".join([
            f"- {k.capitalize()}: {v['sign']} a {v['deg']}graus"
            for k, v in positions.items()
        ])

        message = client.messages.create(
            model=model,
            max_tokens=4000,
            messages=[{
                "role": "user",
                "content": f"""Voce e um astrologo profissional. Gere uma interpretacao completa do mapa astral natal de {name}.

Posicoes planetarias:
{planets_text}

Escreva em portugues do Brasil. A interpretacao deve ser:
1. Profunda e personalizada baseada nas posicoes reais
2. Organizada por secoes: Essencia (Sol), Emocoes (Lua), Comunicacao (Mercurio), Amor (Venus), Acao (Marte), Expansao (Jupiter), Disciplina (Saturno), Inovacao (Urano), Intuicao (Netuno), Transformacao (Plutao), Identidade Publica (Ascendente), Carreira (Meio do Ceu)
3. Para cada planeta, explique o significado no signo e como isso impacta a vida da pessoa
4. Termine com uma sintese geral e conselhos

Formato: Use paragrafos bem escritos, sem markdown. Cada secao com titulo simples seguido de dois pontos."""
            }]
        )
        return message.content[0].text
    except Exception as e:
        print(f"AI interpretation error: {e}")
        return _generate_fallback_interpretation(positions, name)


def _generate_fallback_interpretation(positions: dict, name: str) -> str:
    """Fallback interpretation when AI is not available."""
    sun = positions.get("sun", {})
    moon = positions.get("moon", {})
    asc = positions.get("ascendant", {})

    return f"""Interpretacao do Mapa Astral de {name}

Essencia Solar: {sun.get('sign', 'N/A')}
Com o Sol em {sun.get('sign', 'N/A')}, voce possui uma essencia vital marcada pela energia deste signo. Sua identidade fundamental se expressa atraves das qualidades solares, trazendo luz e proposito a sua jornada.

Mundo Emocional: Lua em {moon.get('sign', 'N/A')}
A Lua em {moon.get('sign', 'N/A')} revela como voce processa emocoes e encontra seguranca emocional. Suas necessidades intimas e instintivas sao coloridas por esta posicao lunar.

Identidade Publica: Ascendente em {asc.get('sign', 'N/A')}
O Ascendente em {asc.get('sign', 'N/A')} e a mascara que voce apresenta ao mundo. E a primeira impressao que causa nas pessoas e como aborda novas situacoes.

Para uma interpretacao completa e detalhada de todos os planetas, casas e aspectos do seu mapa, configure a chave ANTHROPIC_API_KEY nas variaveis de ambiente."""


def generate_pdf(name: str, positions: dict, interpretation: str) -> bytes:
    """Generate a beautiful PDF with the chart interpretation."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=25*mm,
        leftMargin=25*mm,
        topMargin=30*mm,
        bottomMargin=25*mm,
    )

    # Styles
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'AstraraTitle',
        parent=styles['Title'],
        fontName='Helvetica-Bold',
        fontSize=28,
        textColor=GOLD,
        alignment=TA_CENTER,
        spaceAfter=5*mm,
    )

    subtitle_style = ParagraphStyle(
        'AstraraSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=12,
        textColor=MUTED,
        alignment=TA_CENTER,
        spaceAfter=10*mm,
    )

    section_style = ParagraphStyle(
        'AstraraSection',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=16,
        textColor=GOLD,
        spaceBefore=8*mm,
        spaceAfter=3*mm,
    )

    body_style = ParagraphStyle(
        'AstraraBody',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=11,
        textColor=HexColor('#333333'),
        leading=16,
        alignment=TA_JUSTIFY,
        spaceAfter=3*mm,
    )

    footer_style = ParagraphStyle(
        'AstraraFooter',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=9,
        textColor=MUTED,
        alignment=TA_CENTER,
        spaceBefore=15*mm,
    )

    # Build content
    story = []

    # Header
    story.append(Paragraph("✦ ASTRARA", title_style))
    story.append(Paragraph("O cosmos, decifrado.", subtitle_style))
    story.append(Spacer(1, 5*mm))

    # Name and date
    story.append(Paragraph(f"Mapa Astral de {name}", ParagraphStyle(
        'Name', parent=styles['Heading1'], fontName='Helvetica-Bold',
        fontSize=22, textColor=HexColor('#1a1a2e'), alignment=TA_CENTER, spaceAfter=8*mm,
    )))

    # Positions table
    sun_sign = positions.get("sun", {}).get("sign", "")
    asc_sign = positions.get("ascendant", {}).get("sign", "")
    moon_sign = positions.get("moon", {}).get("sign", "")

    story.append(Paragraph(
        f"Sol em {sun_sign} · Lua em {moon_sign} · Ascendente em {asc_sign}",
        ParagraphStyle('Summary', parent=styles['Normal'], fontName='Helvetica',
                       fontSize=12, textColor=VIOLET, alignment=TA_CENTER, spaceAfter=8*mm)
    ))

    # Planet positions table
    planet_names = {
        "sun": "Sol", "moon": "Lua", "mercury": "Mercurio", "venus": "Venus",
        "mars": "Marte", "jupiter": "Jupiter", "saturn": "Saturno",
        "uranus": "Urano", "neptune": "Netuno", "pluto": "Plutao",
        "ascendant": "Ascendente", "midheaven": "Meio do Ceu",
    }

    table_data = [["Planeta", "Signo", "Grau"]]
    for key, label in planet_names.items():
        pos = positions.get(key, {})
        deg = pos.get("deg", 0)
        deg_int = int(deg)
        deg_min = int((deg - deg_int) * 60)
        table_data.append([label, pos.get("sign", "-"), f"{deg_int}°{deg_min:02d}'"])

    table = Table(table_data, colWidths=[60*mm, 50*mm, 40*mm])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), GOLD),
        ('TEXTCOLOR', (0, 0), (-1, 0), WHITE),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('TEXTCOLOR', (0, 1), (-1, -1), HexColor('#333333')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [HexColor('#F8F6F3'), WHITE]),
        ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#E0D8CE')),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(table)
    story.append(Spacer(1, 10*mm))

    # Interpretation text
    story.append(Paragraph("Interpretacao Completa", section_style))

    # Split interpretation into paragraphs
    paragraphs = interpretation.strip().split('\n\n')
    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        # Check if it's a section title (ends with : and is short)
        if ':' in para and len(para.split(':')[0]) < 40 and '\n' not in para.split(':')[0]:
            parts = para.split(':', 1)
            story.append(Paragraph(parts[0].strip(), section_style))
            if len(parts) > 1 and parts[1].strip():
                story.append(Paragraph(parts[1].strip(), body_style))
        else:
            # Regular paragraph
            for line in para.split('\n'):
                line = line.strip()
                if line:
                    story.append(Paragraph(line, body_style))

    # Footer
    story.append(Spacer(1, 10*mm))
    story.append(Paragraph("—", ParagraphStyle('Divider', parent=styles['Normal'],
                                                 alignment=TA_CENTER, textColor=GOLD, fontSize=14)))
    story.append(Spacer(1, 3*mm))
    story.append(Paragraph(
        f"Gerado por Astrara em {datetime.now().strftime('%d/%m/%Y')}",
        footer_style
    ))
    story.append(Paragraph("www.astrara.online — O cosmos, decifrado.", footer_style))

    doc.build(story)
    buffer.seek(0)
    return buffer.read()
