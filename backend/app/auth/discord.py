import httpx
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse

from app.core.state import users
from app.core.config import *
from app.core.jwt import create_access_token
from app.schemas.auth import CodeRequest

router = APIRouter()


@router.post("/login")
async def login(request: CodeRequest):
    code = request.code

    if not code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Authorization code is required",
        )

    token_url = "https://discord.com/api/v10/oauth2/token"

    data = {
        "client_id": DISCORD_CLIENT_ID,
        "client_secret": DISCORD_CLIENT_SECRET,
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": DISCORD_REDIRECT_URI,
    }

    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    async with httpx.AsyncClient() as client:
        try:
            token_response = await client.post(token_url, data=data, headers=headers)
            token_response.raise_for_status()
            token_data = token_response.json()
            discord_access_token = token_data.get("access_token")

            if not discord_access_token:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Failed to obtain Discord access token",
                )

            user_url = "https://discord.com/api/v10/users/@me"
            user_headers = {"Authorization": f"Bearer {discord_access_token}"}

            user_response = await client.get(user_url, headers=user_headers)
            user_response.raise_for_status()
            discord_user = user_response.json()

            if users.get(str(discord_user["id"])) is None:
                users[str(discord_user["id"])] = {
                    "username":discord_user.get("username"),
                    "pfp": f"https://cdn.discordapp.com/avatars/{discord_user['id']}/{discord_user['avatar']}.png" if discord_user.get("avatar") else None,
                    "feeds": [
                    ]
                    }
                
            jwt_token = create_access_token(user_id=str(discord_user["id"]))

            response = JSONResponse(
                {
                    "message": "Login successful",
                }
            )
            response.set_cookie(
                key="access_token",
                value=jwt_token,
                httponly=True,
                secure=True,
                samesite="none",
            )
            return response

        except Exception:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Internal server error",
            )
