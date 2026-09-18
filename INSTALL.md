# Instalación

## 1. Crear la aplicación en Discord

1. Entrá a https://discord.com/developers/applications y creá una nueva aplicación.
2. En **Bot**:
   - Generá el token (`Reset Token`) y guardalo — es tu `DISCORD_TOKEN`.
   - Activá los intents privilegiados **Server Members Intent** y **Message Content Intent** (el bot los
     necesita para el rol automático de bienvenida y los comandos con prefijo).
3. En **OAuth2 → General**:
   - Anotá el **Client ID** y **Client Secret** (`DISCORD_CLIENT_ID` / `DISCORD_CLIENT_SECRET`).
   - Agregá como Redirect URI la URL de callback del panel, por ejemplo `http://localhost:8000/auth/callback`
     en desarrollo, o `https://tu-dominio.com/auth/callback` en producción. Tiene que coincidir exactamente con
     `DISCORD_REDIRECT_URI`.
4. Invitá el bot a tu servidor con el **OAuth2 URL Generator**:
   - Scopes: `bot`, `applications.commands`.
   - Permisos mínimos recomendados: `Manage Roles`, `Manage Channels`, `Send Messages`, `Move Members`,
     `Connect`.
   - **Importante para el rol automático:** el rol del *bot* en la jerarquía de roles del servidor tiene que
     quedar **por encima** del rol que querés que asigne, si no Discord rechaza la asignación.
   - **Importante para las salas de voz temporales:** el bot necesita `Manage Channels` también a nivel de la
     categoría donde estén los canales "Crear Sala" (los permisos de categoría pueden estar sobreescritos
     respecto a los del servidor).

## 2. Entorno local

Requisitos: Python 3.12+.

```bash
git clone <tu-fork-o-repo>
cd peluso-bot

python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

pip install -r requirements.txt
```

## 3. Variables de entorno

Copiá `.env.example` a `.env` y completá los valores:

```bash
cp .env.example .env
```

| Variable | Descripción |
| --- | --- |
| `DISCORD_TOKEN` | Token del bot (Discord Developer Portal → Bot). |
| `DISCORD_CLIENT_ID` | Client ID de la aplicación. |
| `DISCORD_CLIENT_SECRET` | Client Secret de la aplicación. |
| `DISCORD_REDIRECT_URI` | URL de callback OAuth2, debe coincidir con la configurada en Discord. |
| `WEB_BASE_PATH` | Prefijo de ruta si el panel se sirve detrás de un proxy en un subpath (ej. `/peluso`). Vacío = raíz del dominio (recomendado). |
| `DATABASE_URL` | Cadena de conexión SQLAlchemy. Por defecto SQLite local (`sqlite:///./peluso.db`). En Docker usá una ruta dentro del volumen compartido, ej. `sqlite:////data/peluso.db`. |
| `UPLOADS_DIR` | Carpeta donde se guardan las imágenes de fondo subidas para la tarjeta de bienvenida. Por defecto `/data/uploads` (pensado para el volumen de Docker); en local podés apuntarlo a una carpeta propia. |
| `WEB_SECRET_KEY` | Clave para firmar las cookies de sesión del panel. Generá una propia y secreta (ej. `python -c "import secrets; print(secrets.token_hex(32))"`). |
| `BOT_OWNER_IDS` | IDs de Discord (separados por coma) con acceso al panel sin importar los roles que tengan en cada servidor. |

## 4. Correr en desarrollo

En dos terminales separadas (son dos procesos independientes):

```bash
# Terminal 1 — el bot
python -m bot.main

# Terminal 2 — el panel web
uvicorn web.main:app --reload --port 8000
```

Abrí http://localhost:8000, iniciá sesión con Discord y vas a ver los servidores donde tenés permiso de
*Manage Server*.

## 5. Despliegue con Docker

El repo incluye `Dockerfile` y `docker-compose.yml` con dos servicios (`bot` y `web`) que comparten un volumen
persistente (`peluso_data`, montado en `/data`) para la base de datos SQLite y las imágenes subidas.

```bash
cp .env.example .env   # completar valores de producción
docker compose up -d --build
```

- `bot` corre `python -m bot.main`.
- `web` corre `uvicorn web.main:app --host 0.0.0.0 --port 8000` (exponé ese puerto con tu proxy reverso
  favorito — Nginx, Traefik, Dokploy, etc. — y apuntale TLS ahí).
- Asegurate de que `DATABASE_URL` y `UPLOADS_DIR` apunten dentro de `/data` para que persistan entre
  reinicios y sean visibles para ambos contenedores.

### Actualizar tras un cambio de código

```bash
git pull
docker compose up -d --build
```

Las migraciones de columnas nuevas en SQLite se aplican solas al arrancar (`init_db()`), no hace falta correr
nada manualmente.
