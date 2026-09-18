import os
import re
from io import BytesIO

from PIL import Image, ImageDraw, ImageFont

FONTS_DIR = os.path.join(os.path.dirname(__file__), "assets", "fonts")

# size_ratio ajusta el rango de tamaños de fuente probados para que distintas fuentes
# (con proporciones de "em" muy distintas entre sí) terminen con una altura visual similar.
FONT_CHOICES: dict[str, dict[str, object]] = {
    "press_start_2p": {
        "label": "Press Start 2P (arcade clásico)",
        "file": "PressStart2P-Regular.ttf",
        "size_ratio": 1.0,
    },
    "vt323": {
        "label": "VT323 (terminal retro)",
        "file": "VT323-Regular.ttf",
        "size_ratio": 1.6,
    },
    "silkscreen": {
        "label": "Silkscreen (pixel compacto)",
        "file": "Silkscreen-Regular.ttf",
        "size_ratio": 1.0,
    },
    "bungee": {
        "label": "Bungee (arcade urbano)",
        "file": "Bungee-Regular.ttf",
        "size_ratio": 1.0,
    },
    "monoton": {
        "label": "Monoton (neón)",
        "file": "Monoton-Regular.ttf",
        "size_ratio": 1.3,
    },
}
DEFAULT_FONT_KEY = "press_start_2p"

# El avatar circular ocupa esta fracción del lado más chico del fondo
AVATAR_SIZE_RATIO = 0.32
MAX_FONT_SIZE = 36
MIN_FONT_SIZE = 14
STROKE_WIDTH = 2

PANEL_FILL = (0, 0, 0, 140)
PANEL_PADDING_X_RATIO = 0.06
PANEL_PADDING_Y_RATIO = 0.05
AVATAR_TEXT_GAP_RATIO = 0.03

_MARKDOWN_PATTERN = re.compile(r"[*_`~]")
_LINE_HEIGHT_PROBE = "AÁÑÓgjpqy!¡"


def _strip_markdown(text: str) -> str:
    """Los caracteres de Markdown de Discord (**, _, etc.) no tienen sentido dibujados en la imagen."""
    return _MARKDOWN_PATTERN.sub("", text)


def _font_choice(font_key: str) -> dict[str, object]:
    return FONT_CHOICES.get(font_key, FONT_CHOICES[DEFAULT_FONT_KEY])


def _line_height(font: ImageFont.FreeTypeFont) -> int:
    """Altura real de línea para esta fuente y tamaño, medida en vez de estimada, para que
    el cálculo funcione igual de bien con fuentes de proporciones muy distintas."""
    _, top, _, bottom = font.getbbox(_LINE_HEIGHT_PROBE, stroke_width=STROKE_WIDTH)
    return int((bottom - top) * 1.3)


def _wrap_text(measure: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont, max_width: int) -> list[str]:
    lines: list[str] = []
    for paragraph in text.splitlines() or [""]:
        words = paragraph.split()
        current = ""
        for word in words:
            candidate = f"{current} {word}".strip()
            if measure.textlength(candidate, font=font) <= max_width or not current:
                current = candidate
            else:
                lines.append(current)
                current = word
        lines.append(current)
    return lines


def _fit_text(
    measure: ImageDraw.ImageDraw, text: str, max_width: int, max_height: int, font_path: str, size_ratio: float
) -> tuple[ImageFont.FreeTypeFont, list[str], int]:
    max_size = max(MIN_FONT_SIZE, int(MAX_FONT_SIZE * size_ratio))
    min_size = max(8, int(MIN_FONT_SIZE * size_ratio))
    step = max(1, int(2 * size_ratio))

    for size in range(max_size, min_size - 1, -step):
        font = ImageFont.truetype(font_path, size)
        lines = _wrap_text(measure, text, font, max_width)
        line_height = _line_height(font)
        if line_height * len(lines) <= max_height:
            return font, lines, line_height

    font = ImageFont.truetype(font_path, min_size)
    lines = _wrap_text(measure, text, font, max_width)
    return font, lines, _line_height(font)


def build_welcome_card(
    background_path: str, avatar_bytes: bytes, message: str = "", font_key: str = DEFAULT_FONT_KEY
) -> BytesIO:
    """Compone el avatar del usuario y el mensaje de bienvenida en letras arcade, agrupados sobre un panel
    semitransparente para que se distingan del fondo."""
    background = Image.open(background_path).convert("RGBA")
    measure = ImageDraw.Draw(Image.new("RGBA", (1, 1)))

    choice = _font_choice(font_key)
    font_path = os.path.join(FONTS_DIR, choice["file"])
    size_ratio = choice["size_ratio"]

    avatar_size = int(min(background.size) * AVATAR_SIZE_RATIO)
    text_gap = int(background.height * AVATAR_TEXT_GAP_RATIO)
    padding_x = int(background.width * PANEL_PADDING_X_RATIO)
    padding_y = int(background.height * PANEL_PADDING_Y_RATIO)

    text = _strip_markdown(message).strip()
    font = None
    lines: list[str] = []
    line_height = 0
    text_width = 0
    if text:
        max_width = int(background.width * 0.85)
        max_height = background.height - avatar_size - text_gap - 2 * padding_y
        if max_height > MIN_FONT_SIZE:
            font, lines, line_height = _fit_text(measure, text, max_width, max_height, font_path, size_ratio)
            text_width = max((measure.textlength(line, font=font) for line in lines), default=0)

    text_block_height = line_height * len(lines)
    content_width = max(avatar_size, text_width)
    content_height = avatar_size + (text_gap + text_block_height if lines else 0)

    panel_width = content_width + 2 * padding_x
    panel_height = content_height + 2 * padding_y
    panel_left = (background.width - panel_width) // 2
    panel_top = (background.height - panel_height) // 2
    panel_box = (
        max(0, panel_left),
        max(0, panel_top),
        min(background.width, panel_left + panel_width),
        min(background.height, panel_top + panel_height),
    )

    overlay = Image.new("RGBA", background.size, (0, 0, 0, 0))
    ImageDraw.Draw(overlay).rounded_rectangle(panel_box, radius=padding_y * 2, fill=PANEL_FILL)
    background = Image.alpha_composite(background, overlay)

    avatar_top = panel_top + padding_y
    text_top = avatar_top + avatar_size + text_gap

    avatar = Image.open(BytesIO(avatar_bytes)).convert("RGBA").resize((avatar_size, avatar_size))
    mask = Image.new("L", (avatar_size, avatar_size), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, avatar_size, avatar_size), fill=255)
    circular_avatar = Image.new("RGBA", (avatar_size, avatar_size))
    circular_avatar.paste(avatar, (0, 0), mask=mask)
    avatar_position = ((background.width - avatar_size) // 2, avatar_top)
    background.paste(circular_avatar, avatar_position, circular_avatar)

    if lines:
        draw = ImageDraw.Draw(background)
        y = text_top
        for line in lines:
            width = draw.textlength(line, font=font)
            x = (background.width - width) // 2
            draw.text((x, y), line, font=font, fill="white", stroke_width=STROKE_WIDTH, stroke_fill="black")
            y += line_height

    buffer = BytesIO()
    background.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer
