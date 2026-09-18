from fastapi import APIRouter, FastAPI
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.sessions import SessionMiddleware
from starlette.requests import Request

from shared.config import settings
from shared.database import init_db
from web.auth import get_optional_user
from web.routes import auth, dashboard, legal

BASE_PATH = settings.web_base_path

ERROR_MESSAGES = {
    401: ("No iniciaste sesión", "Necesitás iniciar sesión con Discord para ver esta página."),
    403: ("Sin permisos", "No tenés permisos suficientes para acceder a este recurso."),
    404: ("Página no encontrada", "La página que buscás no existe o fue movida."),
}

app = FastAPI(title="Peluso Bot - Panel")
app.add_middleware(SessionMiddleware, secret_key=settings.web_secret_key)
app.mount(f"{BASE_PATH}/static", StaticFiles(directory="web/static"), name="static")

templates = Jinja2Templates(directory="web/templates")
templates.env.globals["base_path"] = BASE_PATH


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    title, default_message = ERROR_MESSAGES.get(exc.status_code, ("Ocurrió un error", ""))
    user = get_optional_user(request)

    if exc.status_code == 401:
        action_url, action_label = f"{BASE_PATH}/auth/login", "Iniciar sesión con Discord"
    elif user is not None:
        action_url, action_label = f"{BASE_PATH}/dashboard", "Volver al panel"
    else:
        action_url, action_label = f"{BASE_PATH}/", "Volver al inicio"

    return templates.TemplateResponse(
        request,
        "error.html",
        {
            "user": user,
            "status_code": exc.status_code,
            "title": title,
            "message": exc.detail if isinstance(exc.detail, str) and exc.detail else default_message,
            "action_url": action_url,
            "action_label": action_label,
        },
        status_code=exc.status_code,
    )

root_router = APIRouter(prefix=BASE_PATH)


@root_router.get("/")
async def home(request: Request):
    user = get_optional_user(request)
    if user is not None:
        return RedirectResponse(f"{BASE_PATH}/dashboard")
    return templates.TemplateResponse(request, "login.html")


root_router.include_router(auth.router)
root_router.include_router(dashboard.router)
root_router.include_router(legal.router)
app.include_router(root_router)


@app.on_event("startup")
def on_startup() -> None:
    init_db()
