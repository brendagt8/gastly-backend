from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import httpx
from app.core.config import settings
from app.core.database import get_db
from app.core.security import create_access_token, get_current_user
from app.models.user import User
from app.schemas.user import TokenOut, UserOut

router = APIRouter(prefix="/auth", tags=["auth"])

GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"
MOBILE_REDIRECT_SCHEME = "gastly://auth"


@router.get("/google/login")
async def google_login(platform: str = "web"):
    """
    Devuelve la URL de autorización de Google.
    platform=mobile → el callback redirigirá a gastly://auth?token=...
    platform=web    → el callback devuelve JSON con el token
    """
    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": "openid email profile https://www.googleapis.com/auth/gmail.readonly",
        "access_type": "offline",
        "prompt": "consent",
        "state": platform,  # "mobile" o "web"
    }
    query = "&".join(f"{k}={v}" for k, v in params.items())
    url = f"https://accounts.google.com/o/oauth2/v2/auth?{query}"
    return {"url": url}


@router.get("/google/callback")
async def google_callback(code: str, state: str = "web", db: AsyncSession = Depends(get_db)):
    """
    Recibe el código de Google, obtiene tokens y crea/actualiza al usuario.
    Si state=mobile redirige a gastly://auth?token=... en lugar de devolver JSON.
    """
    async with httpx.AsyncClient() as client:
        token_res = await client.post(GOOGLE_TOKEN_URL, data={
            "code": code,
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "redirect_uri": settings.GOOGLE_REDIRECT_URI,
            "grant_type": "authorization_code",
        })
        if token_res.status_code != 200:
            raise HTTPException(status_code=400, detail="Error al obtener token de Google")

        tokens = token_res.json()
        access_token = tokens["access_token"]
        refresh_token = tokens.get("refresh_token")

        user_res = await client.get(GOOGLE_USERINFO_URL, headers={"Authorization": f"Bearer {access_token}"})
        if user_res.status_code != 200:
            raise HTTPException(status_code=400, detail="Error al obtener info del usuario")
        info = user_res.json()

    result = await db.execute(select(User).where(User.email == info["email"]))
    user = result.scalar_one_or_none()

    if user:
        user.google_access_token = access_token
        if refresh_token:
            user.google_refresh_token = refresh_token
        user.name = info.get("name", user.name)
        user.picture = info.get("picture")
    else:
        user = User(
            email=info["email"],
            name=info.get("name", info["email"]),
            picture=info.get("picture"),
            google_access_token=access_token,
            google_refresh_token=refresh_token,
        )
        db.add(user)

    await db.commit()
    await db.refresh(user)

    jwt = create_access_token(user.id)

    if state == "mobile":
        return RedirectResponse(url=f"{MOBILE_REDIRECT_SCHEME}?token={jwt}")

    return TokenOut(
        access_token=jwt,
        user=UserOut.model_validate(user),
    )


@router.get("/me", response_model=UserOut)
async def me(current_user: User = Depends(get_current_user)):
    return current_user
