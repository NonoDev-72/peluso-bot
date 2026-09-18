from fastapi import HTTPException, Request

from shared.database import SessionLocal, User


def get_current_user(request: Request) -> User:
    discord_id = request.session.get("discord_id")
    if discord_id is None:
        raise HTTPException(status_code=401, detail="No autenticado")

    with SessionLocal() as session:
        user = session.get(User, discord_id)
        if user is None:
            raise HTTPException(status_code=401, detail="No autenticado")
        return user


def get_optional_user(request: Request) -> User | None:
    try:
        return get_current_user(request)
    except HTTPException:
        return None
