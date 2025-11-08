import asyncio
import httpx
import feedparser
from datetime import datetime
from typing import Dict, Set

from app.core.state import users

feed_history: Dict[str, Set[str]] = {}

async def fetch_feed(url: str) -> dict:
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url)
            response.raise_for_status()
            feed_content = response.text
            return feedparser.parse(feed_content)
        except Exception as e:
            print(f"Error fetching feed {url}: {str(e)}")
            return None

async def send_to_webhook(webhook_url: str, content: dict, color: int = 0x00ff00) -> bool:
    async with httpx.AsyncClient() as client:
        try:
            embed = {
                "title": content.get("title", "New Feed Update"),
                "description": content.get("description", ""),
                "url": content.get("link", ""),
                "color": color,  
                "timestamp": datetime.utcnow().isoformat()
            }
            
            data = {
                "embeds": [embed]
            }
            
            response = await client.post(webhook_url, json=data)
            response.raise_for_status()
            return True
        except Exception as e:
            print(f"Error sending to webhook {webhook_url}: {str(e)}")
            return False

async def send_welcome_message(webhook_url: str, feed_title: str) -> bool:
    content = {
        "title": "🎉 RSS Feed Bot Initialized!",
        "description": (
            f"Your RSS feed **{feed_title}** has been successfully set up!\n\n"
            "I will start checking for updates in the next minute and notify you "
            "of any new posts. The first update will include the latest post from your feed."
        ),
        "url": ""
    }
    return await send_to_webhook(webhook_url, content, color=0x3498db)

async def send_latest_entry(user_id: str, feed: dict) -> bool:
    if not feed.get("rssUrl") or not feed.get("webhookUrl") or not feed.get("enabled", False):
        return False

    feed_data = await fetch_feed(feed["rssUrl"])
    if not feed_data or not feed_data.entries:
        return False

    latest_entry = feed_data.entries[0]
    
    feed_title = feed_data.feed.get("title", feed.get("title", "RSS Feed"))
    
    content = {
        "title": f"🆕 Latest from {feed_title}: {latest_entry.get('title', 'No Title')}",
        "description": latest_entry.get("description", "No Description"),
        "link": latest_entry.get("link", ""),
    }
    
    return await send_to_webhook(feed["webhookUrl"], content, color=0x9b59b6)

async def check_feed_updates(user_id: str, feed: dict, send_latest: bool = False):
    if not feed.get("rssUrl") or not feed.get("webhookUrl") or not feed.get("enabled", False):
        return

    feed_data = await fetch_feed(feed["rssUrl"])
    if not feed_data:
        return

    feed_key = f"{user_id}_{feed['rssUrl']}"
    is_new_feed = feed_key not in feed_history
    
    if is_new_feed:
        feed_history[feed_key] = set()
        feed_title = feed_data.feed.get("title", feed.get("title", "RSS Feed"))
        await send_welcome_message(feed["webhookUrl"], feed_title)
        
        if send_latest:
            [feed_history[feed_key].add(entry.get("guid", entry.get("link", entry.get("title")))) for entry in feed_data.entries]
            await send_latest_entry(user_id, feed)
            return  
    
    for entry in feed_data.entries:
        entry_id = entry.get("guid", entry.get("link", entry.get("title")))
        
        if entry_id and entry_id not in feed_history[feed_key]:
            content = {
                "title": entry.get("title", "No Title"),
                "description": entry.get("description", "No Description"),
                "link": entry.get("link", ""),
            }
            
            success = await send_to_webhook(feed["webhookUrl"], content)
            if success:
                feed_history[feed_key].add(entry_id)
                if len(feed_history[feed_key]) > 1000:
                    feed_history[feed_key] = set(list(feed_history[feed_key])[-500:])

async def check_all_feeds():
    tasks = []
    for user_id, user_data in users.items():
        if "feeds" in user_data:
            for feed in user_data["feeds"]:
                if isinstance(feed, dict):
                    tasks.append(check_feed_updates(user_id, feed, send_latest=True))
    
    if tasks:
        await asyncio.gather(*tasks, return_exceptions=True)

async def start_feed_checker(interval_seconds: int = 30):
    while True:
        try:
            await check_all_feeds()
        except Exception as e:
            print(f"Error in feed checker: {str(e)}")
        
        await asyncio.sleep(interval_seconds)
