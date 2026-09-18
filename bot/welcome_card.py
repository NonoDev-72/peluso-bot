import os
import re
from io import BytesIO

from PIL import Image, ImageDraw, ImageFont

# El avatar circular ocupa esta fracción del lado más chico del fondo
AVATAR_SIZE_RATIO = 0.32

FONT_PATH = os.path.join(os.path.dirname(__file__), "assets", "fonts", "PressStart2P-Regular.ttf")
MAX_FONT_SIZE = 36
MIN_FONT_SIZE = 14

_MARKDOWN_PATTERN = re.compile(r"[*_`~]")


def _strip_markdown(text: str) -> str:
    """Los caracteres de Markdown de Discord (**, _, etc.) no tienen sentido dibujados en la imagen."""
    return _MARKDOWN_PATTERN.sub("", text)


def _wrap_text(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont, max_width: int) -> list[str]:
    lines: list[str] = []
    for paragraph in text.splitlines() or [""]:
        words = paragraph.split()
        current = ""
        for word in words:
            candidate = f"{current} {word}".strip()
            if draw.textlength(candidate, font=font) <= max_width or not current:
                current = candidate
            else:
                lines.append(current)
                current = word
        lines.append(current)
    return lines


def _fit_text(
    draw: ImageDraw.ImageDraw, text: str, max_width: int, max_height: int
) -> tuple[ImageFont.FreeTypeFont, list[str], int]:
    for size in range(MAX_FONT_SIZE, MIN_FONT_SIZE - 1, -2):
        font = ImageFont.truetype(FONT_PATH, size)
        lines = _wrap_text(draw, text, font, max_width)
        line_height = int(size * 1.6)
        if line_height * len(lines) <= max_height:
            return font, lines, line_height

    font = ImageFont.truetype(FONT_PATH, MIN_FONT_SIZE)
    lines = _wrap_text(draw, text, font, max_width)
    return font, lines, int(MIN_FONT_SIZE * 1.6)


def build_welcome_card(background_path: str, avatar_bytes: bytes, message: str = "") -> BytesIO:
    """Compone el avatar del usuario (circular, centrado) y el mensaje de bienvenida en letras arcade."""
    background = Image.open(background_path).convert("RGBA")
    draw = ImageDraw.Draw(background)

    avatar_size = int(min(background.size) * AVATAR_SIZE_RATIO)
    avatar_top = int(background.height * 0.08)
    avatar = Image.open(BytesIO(avatar_bytes)).convert("RGBA").resize((avatar_size, avatar_size))

    mask = Image.new("L", (avatar_size, avatar_size), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, avatar_size, avatar_size), fill=255)

    circular_avatar = Image.new("RGBA", (avatar_size, avatar_size))
    circular_avatar.paste(avatar, (0, 0), mask=mask)

    avatar_position = ((background.width - avatar_size) // 2, avatar_top)
    background.paste(circular_avatar, avatar_position, circular_avatar)

    text = _strip_markdown(message).strip()
    if text:
        text_top = avatar_top + avatar_size + int(background.height * 0.05)
        max_width = int(background.width * 0.85)
        max_height = background.height - text_top - int(background.height * 0.05)

        if max_height > MIN_FONT_SIZE:
            font, lines, line_height = _fit_text(draw, text, max_width, max_height)
            total_height = line_height * len(lines)
            y = text_top + max(0, (max_height - total_height) // 2)
            for line in lines:
                width = draw.textlength(line, font=font)
                x = (background.width - width) // 2
                draw.text(
                    (x, y),
                    line,
                    font=font,
                    fill="white",
                    stroke_width=2,
                    stroke_fill="black",
                )
                y += line_height

    buffer = BytesIO()
    background.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer
