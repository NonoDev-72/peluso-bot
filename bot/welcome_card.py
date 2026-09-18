import os
import re
from io import BytesIO

from PIL import Image, ImageDraw, ImageFont

# El avatar circular ocupa esta fracción del lado más chico del fondo
AVATAR_SIZE_RATIO = 0.32

FONT_PATH = os.path.join(os.path.dirname(__file__), "assets", "fonts", "PressStart2P-Regular.ttf")
MAX_FONT_SIZE = 36
MIN_FONT_SIZE = 14

PANEL_FILL = (0, 0, 0, 140)
PANEL_PADDING_X_RATIO = 0.04
PANEL_PADDING_Y_RATIO = 0.025

_MARKDOWN_PATTERN = re.compile(r"[*_`~]")


def _strip_markdown(text: str) -> str:
    """Los caracteres de Markdown de Discord (**, _, etc.) no tienen sentido dibujados en la imagen."""
    return _MARKDOWN_PATTERN.sub("", text)


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
    measure: ImageDraw.ImageDraw, text: str, max_width: int, max_height: int
) -> tuple[ImageFont.FreeTypeFont, list[str], int]:
    for size in range(MAX_FONT_SIZE, MIN_FONT_SIZE - 1, -2):
        font = ImageFont.truetype(FONT_PATH, size)
        lines = _wrap_text(measure, text, font, max_width)
        line_height = int(size * 1.6)
        if line_height * len(lines) <= max_height:
            return font, lines, line_height

    font = ImageFont.truetype(FONT_PATH, MIN_FONT_SIZE)
    lines = _wrap_text(measure, text, font, max_width)
    return font, lines, int(MIN_FONT_SIZE * 1.6)


def build_welcome_card(background_path: str, avatar_bytes: bytes, message: str = "") -> BytesIO:
    """Compone el avatar del usuario y el mensaje de bienvenida en letras arcade, agrupados sobre un panel
    semitransparente para que se distingan del fondo."""
    background = Image.open(background_path).convert("RGBA")
    measure = ImageDraw.Draw(Image.new("RGBA", (1, 1)))

    avatar_size = int(min(background.size) * AVATAR_SIZE_RATIO)
    avatar_top = int(background.height * 0.08)
    text_gap = int(background.height * 0.015)

    text = _strip_markdown(message).strip()
    font = None
    lines: list[str] = []
    line_height = 0
    text_width = 0
    if text:
        text_top_guess = avatar_top + avatar_size + text_gap
        max_width = int(background.width * 0.85)
        max_height = background.height - text_top_guess - int(background.height * 0.05)
        if max_height > MIN_FONT_SIZE:
            font, lines, line_height = _fit_text(measure, text, max_width, max_height)
            text_width = max((measure.textlength(line, font=font) for line in lines), default=0)

    text_block_height = line_height * len(lines)
    text_top = avatar_top + avatar_size + text_gap if lines else avatar_top + avatar_size

    content_width = max(avatar_size, text_width)
    content_bottom = text_top + text_block_height if lines else avatar_top + avatar_size

    padding_x = int(background.width * PANEL_PADDING_X_RATIO)
    padding_y = int(background.height * PANEL_PADDING_Y_RATIO)
    panel_box = (
        max(0, (background.width - content_width) // 2 - padding_x),
        max(0, avatar_top - padding_y),
        min(background.width, (background.width + content_width) // 2 + padding_x),
        min(background.height, content_bottom + padding_y),
    )

    overlay = Image.new("RGBA", background.size, (0, 0, 0, 0))
    ImageDraw.Draw(overlay).rounded_rectangle(panel_box, radius=padding_y * 2, fill=PANEL_FILL)
    background = Image.alpha_composite(background, overlay)

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
            draw.text((x, y), line, font=font, fill="white", stroke_width=2, stroke_fill="black")
            y += line_height

    buffer = BytesIO()
    background.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer
