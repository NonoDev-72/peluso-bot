# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Setup
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in Discord credentials, see INSTALL.md

# Run (two independent processes, run in separate terminals)
python -m bot.main
uvicorn web.main:app --reload --port 8000

# Docker (bot + web share a volume mounted at /data)
docker compose up -d --build
```

There is no test suite, linter, or formatter configured in this repo. Verify changes by importing the
touched modules (`python -c "import bot.cogs.welcome"`, etc.) and, for template/route changes, rendering the
Jinja2 template directly or hitting the route with an ad-hoc script — see recent commits for examples of this
pattern (e.g. `bot/welcome_card.py` was iterated on by rendering test images with PIL directly).

## Architecture

**Two independent processes sharing state, not a monolith.** `bot/main.py` (discord.py bot) and
`web/main.py` (FastAPI panel) are separate entry points, typically separate containers (see
`docker-compose.yml`: services `bot` and `web`). They share:
- The same SQLite database via `DATABASE_URL` (`shared/database.py`) — the web panel writes
  `GuildConfig`/`VoiceRoomTrigger`/`TempVoiceChannel` rows, the bot reads them on each relevant Discord event.
- The same uploads directory via `UPLOADS_DIR` (default `/data/uploads`) for welcome-card background images.

There is **no Alembic**. Schema changes to existing tables are hand-rolled: add the column to the model in
`shared/database.py`, then add a matching `ALTER TABLE ... ADD COLUMN` in `_run_migrations()` guarded by
`if "column_name" not in existing_columns`. This only runs for `sqlite` URLs — a non-sqlite `DATABASE_URL`
skips migrations entirely, so don't rely on `_run_migrations` for anything beyond local/sqlite deployments.

**Bot side** (`bot/`): cogs are registered in the `INITIAL_COGS` tuple in `bot/main.py` and loaded via
`load_extension`. Each cog has its own `async def setup(bot)`. Notable pieces:
- `bot/cogs/welcome.py` — on member join/remove, reads `GuildConfig`, optionally builds a welcome card image
  (via `bot/welcome_card.py`) and sends either the image alone or a plain-text fallback if no background is
  configured.
- `bot/cogs/voice_rooms.py` — listens to `on_voice_state_update`; when a member joins a channel registered as
  a `VoiceRoomTrigger`, creates a new voice channel in the same category (copying its permission sync),
  tracks it in `TempVoiceChannel`, and deletes it once empty.
- `bot/welcome_card.py` — Pillow-based image compositor. `FONT_CHOICES` / `DEFAULT_FONT_KEY` define the
  selectable arcade fonts (bundled under `bot/assets/fonts/`, each with a `size_ratio` since fonts differ
  wildly in how "point size" maps to visual height); text fit/wrap uses **measured** font metrics
  (`font.getbbox`), not an estimated multiplier, so it stays correct across very different font shapes.
  `bot/__init__.py` is intentionally empty — `web/routes/dashboard.py` imports `FONT_CHOICES` and
  `build_welcome_card` straight from `bot.welcome_card` for the font picker and live preview, so nothing in
  that import path may require a running bot connection or `DISCORD_TOKEN`.

**Web side** (`web/`): each router module (`web/routes/dashboard.py`, `web/routes/legal.py`) creates its
**own** `Jinja2Templates` instance rather than sharing the one in `web/main.py`. Every new router's instance
must explicitly set `templates.env.globals["base_path"] = settings.web_base_path` (already done for the
existing ones) — otherwise `{{ base_path }}` silently renders as an empty string in that router's templates,
and any `| tojson` filter on it (e.g. inline `<script>` blocks) raises a hard `TypeError` instead.
`web/discord_oauth.py` caches `fetch_manageable_guilds` per access token (`GUILDS_CACHE_TTL_SECONDS`) because
Discord's `/users/@me/guilds` has an unusually aggressive rate limit — any new feature that calls it on a
tight loop (e.g. a live-updating preview) needs to reuse/extend this cache rather than call it per keystroke.

**Discord snowflake IDs and JavaScript.** Guild/channel IDs are 64-bit and routinely exceed
`Number.MAX_SAFE_INTEGER` (2^53). Never embed one as a bare numeric literal in an inline `<script>` block
(`var guildId = {{ config.guild_id }};`) — it silently rounds to a different, often invalid, ID. Always emit
it as a quoted string (`{{ config.guild_id | string | tojson }}`).

**Auth model**: `web/auth.py` reads `discord_id` from the signed session cookie and loads the `User` row;
`web/routes/dashboard.py` additionally calls `fetch_manageable_guilds` and checks the requested `guild_id` is
in that list before allowing access to a guild's settings — this authorization check must not be removed or
bypassed for new dashboard routes, even read-only ones, without an explicit reason (it exists to stop one
authenticated user from viewing/acting on another server's configuration).

## Documentation map

- `README.md` — feature overview and stack.
- `INSTALL.md` — Discord application setup, environment variables, local/Docker install.
- `USAGE.md` — how to use the web panel and bot slash commands once running.
