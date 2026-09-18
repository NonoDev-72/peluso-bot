# 🎀 Peluso Bot

Bot de Discord (Python + [discord.py](https://discordpy.readthedocs.io/)) con un panel web propio (FastAPI) para
configurar todo sin tocar código: bienvenidas con tarjeta de imagen, despedidas, rol automático y salas de voz
temporales, todo administrable server por server con tu login de Discord.

[![Licencia: MIT](https://img.shields.io/badge/Licencia-MIT-yellow.svg)](LICENSE)
[![Python 3.12+](https://img.shields.io/badge/Python-3.12%2B-blue.svg)](requirements.txt)
[![discord.py](https://img.shields.io/badge/discord.py-2.4%2B-5865F2.svg)](https://discordpy.readthedocs.io/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115%2B-009688.svg)](https://fastapi.tiangolo.com/)

---

## ✨ Qué hace

| Área | Funcionalidad |
| --- | --- |
| 👋 **Bienvenida** | Mensaje configurable (`{member}`, `{guild}`, `{member_count}`) y **tarjeta de imagen** generada al vuelo: avatar del usuario recortado en círculo sobre un fondo que vos subís, con el mensaje escrito debajo en una de **5 tipografías arcade** seleccionables, agrupado en un panel semitransparente. Incluye **vista previa en vivo** desde el propio panel. |
| 👋 **Despedida** | Mensaje configurable cuando alguien se va del servidor. |
| 🎭 **Rol automático** | Asigna un rol a cada miembro nuevo apenas entra, elegible desde un desplegable con los roles reales del servidor. |
| 🔊 **Salas de voz temporales** | Configurá uno o varios canales "Crear Sala": al entrar alguien, el bot le crea una sala de voz nueva (nombre configurable, ej. `Sala {n}`), lo mueve adentro, y la borra sola cuando queda vacía. |
| 🌐 **Panel web** | Login con Discord OAuth2, un dashboard por servidor (solo para quienes tengan permiso de *Manage Server*), páginas de error propias (401/403/404) y Términos/Privacidad públicos. |
| 🤖 **Comandos slash** | `/ping` y `/info` como base, listo para sumar más cogs. |

## 🧱 Arquitectura

El bot y el panel web son **dos procesos independientes** que comparten la misma base de datos (SQLite por
defecto) y el mismo volumen de archivos subidos (imágenes de fondo). El panel escribe la configuración; el bot
la lee en cada evento.

```
peluso-bot/
├── bot/                  # Proceso del bot (discord.py)
│   ├── cogs/             # welcome, voice_rooms, general
│   ├── assets/fonts/     # Tipografías arcade (OFL) para la tarjeta de bienvenida
│   ├── welcome_card.py   # Generador de la tarjeta (Pillow)
│   └── main.py
├── web/                  # Panel web (FastAPI)
│   ├── routes/           # auth, dashboard, legal
│   ├── templates/        # Jinja2
│   └── main.py
├── shared/               # Config y modelos de base de datos compartidos
│   ├── config.py
│   └── database.py
├── requirements.txt
├── Dockerfile / docker-compose.yml
└── .env.example
```

## 🚀 Empezar

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # completar con tus credenciales de Discord

python -m bot.main                                  # proceso del bot
uvicorn web.main:app --reload --port 8000            # proceso del panel web
```

Guía completa paso a paso (incluye cómo crear la app en Discord, permisos necesarios y Docker/Dokploy) en
**[INSTALL.md](INSTALL.md)**.

## 📖 Documentación

- **[INSTALL.md](INSTALL.md)** — instalación local, variables de entorno y despliegue con Docker.
- **[USAGE.md](USAGE.md)** — cómo usar el panel web y el bot una vez instalado.
- **[LICENSE](LICENSE)** — licencia MIT.

## 🛠️ Stack

Python 3.12 · [discord.py](https://discordpy.readthedocs.io/) · [FastAPI](https://fastapi.tiangolo.com/) ·
[SQLAlchemy](https://www.sqlalchemy.org/) · [Pillow](https://pillow.readthedocs.io/) · Jinja2 · Discord OAuth2

## 🗺️ Próximos pasos sugeridos

- Migrar la persistencia del bot a llamadas async (por ejemplo con SQLAlchemy async) si el volumen de
  servidores crece.
- Agregar refresco automático del token OAuth cuando expire.
- Sumar más cogs (moderación, niveles, etc.) siguiendo el patrón de `bot/cogs/`.

## Licencia

Este proyecto está bajo licencia [MIT](LICENSE).
