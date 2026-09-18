# Peluso Bot

Bot de Discord en Python (discord.py) con panel web de configuración (FastAPI + login OAuth2 de Discord).

## Estructura

```
peluso-bot/
├── bot/            # Bot de Discord (discord.py, cogs)
├── web/            # Panel web (FastAPI, login con Discord)
├── shared/         # Config y modelos de base de datos compartidos
└── requirements.txt
```

El bot y el panel web son dos procesos independientes que comparten la misma base de datos SQLite (`shared/database.py`). El bot lee la configuración (canales de bienvenida/despedida, mensajes) que se edita desde el panel.

## Setup

1. Crear una aplicación en https://discord.com/developers/applications
   - En **Bot**, generar el token y activar los intents `Server Members Intent` y `Message Content Intent`.
   - En **OAuth2 > General**, agregar como Redirect URI: `http://localhost:8000/auth/callback`.
   - Anotar el `Client ID` y `Client Secret`.

2. Crear entorno virtual e instalar dependencias:

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

3. Copiar `.env.example` a `.env` y completar los valores (token, client id/secret, etc).

4. Invitar el bot al servidor con permisos de `Manage Server`, `Send Messages` y scope `bot applications.commands`.

## Correr el bot

```bash
python -m bot.main
```

## Correr el panel web

```bash
uvicorn web.main:app --reload --port 8000
```

Abrir http://localhost:8000, iniciar sesión con Discord y configurar los servidores donde tengas permiso de `Manage Server`.

## Próximos pasos sugeridos

- Migrar la persistencia del bot a llamadas async (por ejemplo con `run_in_executor` o SQLAlchemy async) si el volumen de servidores crece.
- Agregar refresco automático del token OAuth cuando expire.
- Sumar más cogs (moderación, niveles, etc.) siguiendo el patrón de `bot/cogs/`.
