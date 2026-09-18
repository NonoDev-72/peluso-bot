from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Integer, String, create_engine, text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

from shared.config import settings

engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False} if settings.database_url.startswith("sqlite") else {},
)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


class User(Base):
    """Usuario de Discord que inicio sesion alguna vez en el panel web."""

    __tablename__ = "users"

    discord_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    username: Mapped[str] = mapped_column(String(64))
    avatar_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    access_token: Mapped[str] = mapped_column(String(128))
    refresh_token: Mapped[str] = mapped_column(String(128))
    token_expires_at: Mapped[datetime] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class GuildConfig(Base):
    """Configuracion por servidor, editable desde el panel web y leida por el bot."""

    __tablename__ = "guild_configs"

    guild_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    guild_name: Mapped[str] = mapped_column(String(128), default="")

    welcome_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    welcome_channel_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    welcome_message: Mapped[str] = mapped_column(
        String(2000), default="¡Bienvenido/a {member} a **{guild}**! Ya somos {member_count}."
    )
    welcome_background_path: Mapped[str | None] = mapped_column(String(255), nullable=True)
    welcome_font: Mapped[str] = mapped_column(String(50), default="press_start_2p")

    goodbye_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    goodbye_channel_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    goodbye_message: Mapped[str] = mapped_column(String(2000), default="{member} dejó **{guild}**. ¡Hasta pronto!")

    default_role_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class VoiceRoomTrigger(Base):
    """Canal de voz 'Crear Sala' configurado desde el panel web: al entrar, genera una sala temporal."""

    __tablename__ = "voice_room_triggers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    guild_id: Mapped[int] = mapped_column(BigInteger, index=True)
    trigger_channel_id: Mapped[int] = mapped_column(BigInteger, unique=True)
    name_template: Mapped[str] = mapped_column(String(100), default="Sala {n}")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class TempVoiceChannel(Base):
    """Sala de voz temporal creada por el bot, borrada automáticamente cuando queda vacía."""

    __tablename__ = "temp_voice_channels"

    channel_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    guild_id: Mapped[int] = mapped_column(BigInteger, index=True)
    trigger_id: Mapped[int] = mapped_column(ForeignKey("voice_room_triggers.id"))
    number: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


def init_db() -> None:
    Base.metadata.create_all(engine)
    _run_migrations()


def _run_migrations() -> None:
    """Agrega columnas nuevas a tablas ya existentes (no hay Alembic en este proyecto)."""
    if not settings.database_url.startswith("sqlite"):
        return
    with engine.connect() as conn:
        existing_columns = {row[1] for row in conn.execute(text("PRAGMA table_info(guild_configs)"))}
        if "default_role_id" not in existing_columns:
            conn.execute(text("ALTER TABLE guild_configs ADD COLUMN default_role_id BIGINT"))
            conn.commit()
        if "welcome_background_path" not in existing_columns:
            conn.execute(text("ALTER TABLE guild_configs ADD COLUMN welcome_background_path VARCHAR(255)"))
            conn.commit()
        if "welcome_font" not in existing_columns:
            conn.execute(
                text("ALTER TABLE guild_configs ADD COLUMN welcome_font VARCHAR(50) DEFAULT 'press_start_2p'")
            )
            conn.commit()


def get_or_create_guild_config(session, guild_id: int, guild_name: str = "") -> GuildConfig:
    config = session.get(GuildConfig, guild_id)
    if config is None:
        config = GuildConfig(guild_id=guild_id, guild_name=guild_name)
        session.add(config)
        session.commit()
        session.refresh(config)
    elif guild_name and config.guild_name != guild_name:
        config.guild_name = guild_name
        session.commit()
    return config


def list_voice_room_triggers(session, guild_id: int) -> list[VoiceRoomTrigger]:
    return (
        session.query(VoiceRoomTrigger)
        .filter_by(guild_id=guild_id)
        .order_by(VoiceRoomTrigger.id)
        .all()
    )


def get_voice_room_trigger_by_channel(session, guild_id: int, channel_id: int) -> VoiceRoomTrigger | None:
    return (
        session.query(VoiceRoomTrigger)
        .filter_by(guild_id=guild_id, trigger_channel_id=channel_id)
        .first()
    )


def create_voice_room_trigger(session, guild_id: int, trigger_channel_id: int, name_template: str) -> VoiceRoomTrigger:
    trigger = VoiceRoomTrigger(guild_id=guild_id, trigger_channel_id=trigger_channel_id, name_template=name_template)
    session.add(trigger)
    session.commit()
    session.refresh(trigger)
    return trigger


def delete_voice_room_trigger(session, guild_id: int, trigger_id: int) -> None:
    trigger = session.get(VoiceRoomTrigger, trigger_id)
    if trigger is None or trigger.guild_id != guild_id:
        return
    session.query(TempVoiceChannel).filter_by(trigger_id=trigger_id).delete()
    session.delete(trigger)
    session.commit()


def next_room_number(session, trigger_id: int) -> int:
    used = {row.number for row in session.query(TempVoiceChannel).filter_by(trigger_id=trigger_id).all()}
    number = 1
    while number in used:
        number += 1
    return number


def create_temp_voice_channel(session, channel_id: int, guild_id: int, trigger_id: int, number: int) -> None:
    session.add(TempVoiceChannel(channel_id=channel_id, guild_id=guild_id, trigger_id=trigger_id, number=number))
    session.commit()


def get_temp_voice_channel(session, channel_id: int) -> TempVoiceChannel | None:
    return session.get(TempVoiceChannel, channel_id)


def delete_temp_voice_channel(session, channel_id: int) -> None:
    temp_channel = session.get(TempVoiceChannel, channel_id)
    if temp_channel is not None:
        session.delete(temp_channel)
        session.commit()
