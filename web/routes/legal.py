from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

from shared.config import settings
from web.auth import get_optional_user

router = APIRouter(prefix="/legal", tags=["legal"])
templates = Jinja2Templates(directory="web/templates")
templates.env.globals["base_path"] = settings.web_base_path

LAST_UPDATED = "18 de septiembre de 2026"


@router.get("/terms")
async def terms(request: Request):
    user = get_optional_user(request)
    return templates.TemplateResponse(request, "legal_terms.html", {"user": user, "last_updated": LAST_UPDATED})


@router.get("/privacy")
async def privacy(request: Request):
    user = get_optional_user(request)
    return templates.TemplateResponse(request, "legal_privacy.html", {"user": user, "last_updated": LAST_UPDATED})
