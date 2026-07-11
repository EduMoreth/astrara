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

    # Known section keywords that should be styled as headings
    SECTION_KEYWORDS = [
        "essencia", "emocoes", "emocional", "comunicacao", "amor", "acao",
        "expansao", "disciplina", "inovacao", "intuicao", "transformacao",
        "identidade", "carreira", "sintese", "conclusao", "ascendente",
        "meio do ceu", "sol ", "lua ", "mercurio", "venus", "marte",
        "jupiter", "saturno", "urano", "netuno", "plutao",
    ]

    def _is_section_title(line: str) -> bool:
        """Detect if a line is a section title."""
        stripped = line.strip().rstrip(':')
        lower = stripped.lower()

        # All-uppercase lines are titles (e.g., "COMUNICACAO - MERCURIO EM LEAO A 26 GRAUS:")
        if stripped.isupper() and len(stripped) > 3:
            return True

        # Lines ending with : that contain known keywords
        if line.strip().endswith(':'):
            for kw in SECTION_KEYWORDS:
                if kw in lower:
                    return True

        # Lines starting with known section patterns
        for kw in SECTION_KEYWORDS:
            if lower.startswith(kw):
                # Must be short-ish (title, not a paragraph starting with keyword)
                if len(stripped) < 80:
                    return True

        # Lines with " - " separator that are title-like
        if ' - ' in line and len(stripped) < 80 and ':' in line:
            return True

        return False

    # Split interpretation into lines and process
    lines = interpretation.strip().split('\n')
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue

        if _is_section_title(line):
            # Remove trailing colon for cleaner display
            title = line.rstrip(':').strip()
            story.append(Paragraph(title, section_style))
        else:
            # Collect consecutive non-empty, non-title lines as one paragraph
            para_lines = [line]
            while i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                if not next_line or _is_section_title(next_line):
                    break
                para_lines.append(next_line)
                i += 1
            story.append(Paragraph(' '.join(para_lines), body_style))

        i += 1

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


# ── Synastry (sinastria) ─────────────────────────────────────

def generate_synastry_interpretation(
    name_a: str, positions_a: dict,
    name_b: str, positions_b: dict,
    inter_aspects: list, scores: dict,
) -> str:
    """Generate the synastry (couple compatibility) interpretation using Claude AI."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        return _generate_fallback_synastry(name_a, positions_a, name_b, positions_b, scores)

    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
        model = os.getenv("AI_MODEL", "claude-sonnet-4-6")

        def _fmt_positions(positions: dict) -> str:
            return "\n".join(
                f"- {k.capitalize()}: {v['sign']} a {v['deg']} graus"
                for k, v in positions.items()
                if isinstance(v, dict) and "sign" in v
            )

        aspects_text = "\n".join(
            f"- {a['p1']} de {name_a} em {a['aspect']} com {a['p2']} de {name_b} (orbe {a['orbit']})"
            for a in inter_aspects[:40]
        ) or "- Nenhum aspecto maior encontrado"

        dims = scores.get("dimensions", {})
        scores_text = "\n".join(
            f"- {d['label']}: {d['score']}/100"
            for d in dims.values()
        )

        message = client.messages.create(
            model=model,
            max_tokens=4000,
            messages=[{
                "role": "user",
                "content": f"""Voce e um astrologo profissional especializado em sinastria (astrologia de relacionamentos). Gere uma analise de compatibilidade completa entre {name_a} e {name_b}.

Posicoes de {name_a}:
{_fmt_positions(positions_a)}

Posicoes de {name_b}:
{_fmt_positions(positions_b)}

Aspectos entre os dois mapas (sinastria):
{aspects_text}

Indices de afinidade calculados:
- Afinidade geral: {scores.get('overall', 50)}/100
{scores_text}

Escreva em portugues do Brasil. A analise deve ser:
1. Profunda e baseada nos aspectos reais entre os dois mapas
2. Organizada por secoes: Visao Geral da Conexao, Amor e Atracao, Conexao Emocional, Comunicacao e Ideias, Identidade e Proposito, Compromisso e Estabilidade, Intensidade e Transformacao, Desafios do Relacionamento, Conselhos para o Casal
3. Em cada secao, cite os aspectos concretos entre os planetas dos dois mapas e o que significam na pratica do relacionamento
4. Seja honesto sobre tensoes (quadraturas, oposicoes) sem ser fatalista — mostre como trabalha-las
5. Termine com uma sintese acolhedora

Formato: paragrafos bem escritos, sem markdown. Cada secao com titulo simples seguido de dois pontos."""
            }]
        )
        return message.content[0].text
    except Exception as e:
        print(f"AI synastry interpretation error: {e}")
        return _generate_fallback_synastry(name_a, positions_a, name_b, positions_b, scores)


def _generate_fallback_synastry(name_a, positions_a, name_b, positions_b, scores) -> str:
    sun_a = (positions_a or {}).get("sun", {}).get("sign", "N/A")
    sun_b = (positions_b or {}).get("sun", {}).get("sign", "N/A")
    moon_a = (positions_a or {}).get("moon", {}).get("sign", "N/A")
    moon_b = (positions_b or {}).get("moon", {}).get("sign", "N/A")
    overall = (scores or {}).get("overall", 50)
    return f"""Sinastria de {name_a} e {name_b}

Visao Geral da Conexao:
A afinidade geral calculada entre os dois mapas e de {overall}/100. {name_a} tem Sol em {sun_a} e Lua em {moon_a}; {name_b} tem Sol em {sun_b} e Lua em {moon_b}. A combinacao dessas energias define o tom essencial do relacionamento.

Para a analise completa e detalhada de todos os aspectos entre os dois mapas, configure a chave ANTHROPIC_API_KEY nas variaveis de ambiente."""


def generate_synastry_pdf(
    name_a: str, positions_a: dict,
    name_b: str, positions_b: dict,
    scores: dict, interpretation: str,
) -> bytes:
    """Generate the synastry PDF: header, both charts summary, affinity scores,
    full interpretation. Reuses the visual identity of the natal PDF."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        rightMargin=25*mm, leftMargin=25*mm, topMargin=30*mm, bottomMargin=25*mm,
    )
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'AstraraTitle', parent=styles['Title'], fontName='Helvetica-Bold',
        fontSize=28, textColor=GOLD, alignment=TA_CENTER, spaceAfter=5*mm,
    )
    subtitle_style = ParagraphStyle(
        'AstraraSubtitle', parent=styles['Normal'], fontName='Helvetica',
        fontSize=12, textColor=MUTED, alignment=TA_CENTER, spaceAfter=10*mm,
    )
    section_style = ParagraphStyle(
        'AstraraSection', parent=styles['Heading2'], fontName='Helvetica-Bold',
        fontSize=16, textColor=GOLD, spaceBefore=8*mm, spaceAfter=3*mm,
    )
    body_style = ParagraphStyle(
        'AstraraBody', parent=styles['Normal'], fontName='Helvetica',
        fontSize=11, textColor=HexColor('#333333'), leading=16,
        alignment=TA_JUSTIFY, spaceAfter=3*mm,
    )
    footer_style = ParagraphStyle(
        'AstraraFooter', parent=styles['Normal'], fontName='Helvetica-Oblique',
        fontSize=9, textColor=MUTED, alignment=TA_CENTER, spaceBefore=15*mm,
    )

    story = []
    story.append(Paragraph("\u2726 ASTRARA", title_style))
    story.append(Paragraph("O cosmos, decifrado.", subtitle_style))
    story.append(Paragraph(f"Sinastria de {name_a} & {name_b}", ParagraphStyle(
        'Name', parent=styles['Heading1'], fontName='Helvetica-Bold',
        fontSize=22, textColor=HexColor('#1a1a2e'), alignment=TA_CENTER, spaceAfter=8*mm,
    )))

    overall = (scores or {}).get("overall", 50)
    story.append(Paragraph(
        f"Afinidade geral: {overall}/100",
        ParagraphStyle('Summary', parent=styles['Normal'], fontName='Helvetica-Bold',
                       fontSize=14, textColor=VIOLET, alignment=TA_CENTER, spaceAfter=8*mm)
    ))

    # Side-by-side planet positions
    planet_names = {
        "sun": "Sol", "moon": "Lua", "mercury": "Mercurio", "venus": "Venus",
        "mars": "Marte", "jupiter": "Jupiter", "saturn": "Saturno",
        "uranus": "Urano", "neptune": "Netuno", "pluto": "Plutao",
        "ascendant": "Ascendente", "midheaven": "Meio do Ceu",
    }

    def _cell(positions, key):
        pos = (positions or {}).get(key) or {}
        deg = pos.get("deg", 0) or 0
        return f"{pos.get('sign', '-')} {int(deg)}\u00b0"

    table_data = [["Planeta", name_a[:18], name_b[:18]]]
    for key, label in planet_names.items():
        table_data.append([label, _cell(positions_a, key), _cell(positions_b, key)])

    table = Table(table_data, colWidths=[50*mm, 50*mm, 50*mm])
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
    story.append(Spacer(1, 8*mm))

    # Affinity scores table
    dims = (scores or {}).get("dimensions", {})
    if dims:
        score_data = [["Dimensao", "Afinidade"]]
        for d in dims.values():
            score_data.append([d.get("label", ""), f"{d.get('score', 0)}/100"])
        score_table = Table(score_data, colWidths=[100*mm, 50*mm])
        score_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), VIOLET),
            ('TEXTCOLOR', (0, 0), (-1, 0), WHITE),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ALIGN', (1, 0), (1, -1), 'CENTER'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('TEXTCOLOR', (0, 1), (-1, -1), HexColor('#333333')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [HexColor('#F8F6F3'), WHITE]),
            ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#E0D8CE')),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(score_table)
        story.append(Spacer(1, 10*mm))

    story.append(Paragraph("Analise Completa da Sinastria", section_style))

    _SYN_SECTION_KEYWORDS = [
        "visao geral", "amor", "atracao", "conexao emocional", "comunicacao",
        "identidade", "proposito", "compromisso", "estabilidade", "intensidade",
        "transformacao", "desafios", "conselhos", "sintese", "conclusao",
    ]

    def _is_syn_title(line: str) -> bool:
        stripped = line.strip().rstrip(':')
        lower = stripped.lower()
        if stripped.isupper() and len(stripped) > 3:
            return True
        if line.strip().endswith(':') and len(stripped) < 80:
            for kw in _SYN_SECTION_KEYWORDS:
                if kw in lower:
                    return True
        for kw in _SYN_SECTION_KEYWORDS:
            if lower.startswith(kw) and len(stripped) < 80:
                return True
        return False

    lines = (interpretation or "").strip().split('\n')
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue
        if _is_syn_title(line):
            story.append(Paragraph(line.rstrip(':').strip(), section_style))
        else:
            para_lines = [line]
            while i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                if not next_line or _is_syn_title(next_line):
                    break
                para_lines.append(next_line)
                i += 1
            story.append(Paragraph(' '.join(para_lines), body_style))
        i += 1

    story.append(Spacer(1, 10*mm))
    story.append(Paragraph("\u2014", ParagraphStyle('Divider', parent=styles['Normal'],
                                                 alignment=TA_CENTER, textColor=GOLD, fontSize=14)))
    story.append(Spacer(1, 3*mm))
    story.append(Paragraph(
        f"Gerado por Astrara em {datetime.now().strftime('%d/%m/%Y')}",
        footer_style
    ))
    story.append(Paragraph("www.astrara.online \u2014 O cosmos, decifrado.", footer_style))

    doc.build(story)
    buffer.seek(0)
    return buffer.read()
