from io import BytesIO

from PIL import Image, ImageDraw

# El avatar circular ocupa esta fracción del lado más chico del fondo
AVATAR_SIZE_RATIO = 0.35


def build_welcome_card(background_path: str, avatar_bytes: bytes) -> BytesIO:
    """Compone el avatar del usuario, recortado en círculo, centrado sobre la imagen de fondo."""
    background = Image.open(background_path).convert("RGBA")

    avatar_size = int(min(background.size) * AVATAR_SIZE_RATIO)
    avatar = Image.open(BytesIO(avatar_bytes)).convert("RGBA").resize((avatar_size, avatar_size))

    mask = Image.new("L", (avatar_size, avatar_size), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, avatar_size, avatar_size), fill=255)

    circular_avatar = Image.new("RGBA", (avatar_size, avatar_size))
    circular_avatar.paste(avatar, (0, 0), mask=mask)

    position = ((background.width - avatar_size) // 2, (background.height - avatar_size) // 2)
    background.paste(circular_avatar, position, circular_avatar)

    buffer = BytesIO()
    background.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer
