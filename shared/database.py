from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, String, create_engine, text
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

    goodbye_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    goodbye_channel_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    goodbye_message: Mapped[str] = mapped_column(String(2000), default="{member} dejó **{guild}**. ¡Hasta pronto!")

    default_role_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


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
