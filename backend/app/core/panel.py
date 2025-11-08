from fastapi import APIRouter, HTTPException, Depends, status, Cookie, Request
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
import httpx
import feedparser

from app.core.state import users
from app.core.jwt import verify_token

router = APIRouter()
security = HTTPBearer(auto_error=False)

async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    access_token: Optional[str] = Cookie(None)
):
    if credentials and credentials.credentials:
        token = credentials.credentials
    elif access_token:
        token = access_token
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No valid authentication token found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id = verify_token(token)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user_id

@router.get("/getdata")
async def get_panel_data(user_id: str = Depends(get_current_user)):
    user = users.get(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return JSONResponse({
        "data": user,
    })

async def validate_webhook_url(webhook_url: str) -> bool:
    if not webhook_url.startswith('https://discord.com/api/webhooks/'):
        return False
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(webhook_url)
            return response.status_code == 200
        except Exception:
            return False

async def validate_rss_feed(rss_url: str) -> bool:
    if not rss_url:
        return False

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(rss_url)
            response.raise_for_status()
            feed = feedparser.parse(response.text)
            
            return bool(feed.get('feed') and feed.get('entries') is not None)
        except Exception:
            return False

@router.post("/updatefeeds")
async def update_panel_data(request: Request, user_id: str = Depends(get_current_user)):
    user = users.get(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    update_data = await request.json()
    new_feeds = update_data.get('feeds', [])
    
    validation_errors = []
    for i, feed in enumerate(new_feeds):
        if feed.get('enabled', False):  
            webhook_url = feed.get('webhookUrl')
            rss_url = feed.get('rssUrl')
            
            if webhook_url:
                if not await validate_webhook_url(webhook_url):
                    validation_errors.append(f"Feed {i + 1}: Invalid Discord webhook URL")
            else:
                validation_errors.append(f"Feed {i + 1}: Webhook URL is required for enabled feeds")
            
            if rss_url:
                if not await validate_rss_feed(rss_url):
                    validation_errors.append(f"Feed {i + 1}: Invalid RSS feed URL")
            else:
                validation_errors.append(f"Feed {i + 1}: RSS feed URL is required for enabled feeds")
    
    if validation_errors:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": "Validation failed",
                "errors": validation_errors
            }
        )
    
    user['feeds'] = new_feeds
    
    return JSONResponse({
        "message": "Panel data updated successfully",
        "data": user,
    })