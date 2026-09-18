from fastapi import APIRouter, FastAPI
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from starlette.requests import Request

from shared.config import settings
from shared.database import init_db
from web.auth import get_optional_user
from web.routes import auth, dashboard, legal

BASE_PATH = settings.web_base_path

app = FastAPI(title="Peluso Bot - Panel")
app.add_middleware(SessionMiddleware, secret_key=settings.web_secret_key)
app.mount(f"{BASE_PATH}/static", StaticFiles(directory="web/static"), name="static")

templates = Jinja2Templates(directory="web/templates")
templates.env.globals["base_path"] = BASE_PATH

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
