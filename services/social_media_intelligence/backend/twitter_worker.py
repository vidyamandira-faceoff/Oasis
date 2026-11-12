import os
import sys
import re
import asyncio
import time
from pathlib import Path
from typing import Dict, Any, List, Optional

# Add twscrape to sys.path
TWSCRAPE_DIR = Path("/mnt/devdata/works/VivekMedha/twscrape_OSINT")
if str(TWSCRAPE_DIR) not in sys.path:
    sys.path.insert(0, str(TWSCRAPE_DIR))

try:
    from twscrape import API, gather
    from twscrape.accounts_pool import NoAccountError
    from twscrape.models import Tweet, User
except ImportError:
    API = None
    gather = None
    NoAccountError = Exception
    Tweet = None
    User = None

DATA_DIR = Path(__file__).resolve().parent / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DATA_DIR / "twscrape_accounts.db"

def get_twscrape_api(proxy: Optional[str] = None) -> Any:
    """Returns an instance of twscrape.API bound to OASIS SQLite database."""
    if not API:
        raise RuntimeError("twscrape library could not be imported.")
    return API(pool=str(DB_PATH), raise_when_no_account=True, proxy=proxy or None)

def sanitize_x_target(target: str) -> str:
    """Sanitizes handle, stripping @ or URL prefixes."""
    cleaned = target.strip()
    # Check if full URL
    if "x.com/" in cleaned or "twitter.com/" in cleaned:
        parts = cleaned.rstrip("/").split("/")
        if "status" in parts:
            # Tweet URL
            status_idx = parts.index("status")
            if status_idx + 1 < len(parts):
                return parts[status_idx + 1].split("?")[0]
        cleaned = parts[-1].split("?")[0]
    if cleaned.startswith("@"):
        cleaned = cleaned[1:]
    return cleaned.strip()

def format_user_dict(u: Any) -> Dict[str, Any]:
    """Formats twscrape User model into OASIS standard schema."""
    if not u:
        return {}
    return {
        "id": getattr(u, "id", None),
        "username": getattr(u, "username", ""),
        "displayname": getattr(u, "displayname", ""),
        "bio": getattr(u, "rawDescription", ""),
        "location": getattr(u, "location", "") or "Unspecified",
        "created": getattr(u, "created", None).strftime("%Y-%m-%d %H:%M:%S UTC") if getattr(u, "created", None) else "N/A",
        "followers_count": getattr(u, "followersCount", 0),
        "following_count": getattr(u, "friendsCount", 0),
        "statuses_count": getattr(u, "statusesCount", 0),
        "favourites_count": getattr(u, "favouritesCount", 0),
        "media_count": getattr(u, "mediaCount", 0),
        "profile_image_url": getattr(u, "profileImageUrl", ""),
        "profile_banner_url": getattr(u, "profileBannerUrl", "") or "",
        "verified": bool(getattr(u, "verified", False) or getattr(u, "blue", False)),
        "is_blue": bool(getattr(u, "blue", False)),
        "url": getattr(u, "url", f"https://x.com/{getattr(u, 'username', '')}")
    }

def format_tweet_dict(t: Any) -> Dict[str, Any]:
    """Formats twscrape Tweet model into OASIS standard schema."""
    if not t:
        return {}
    
    media_list = []
    if hasattr(t, "media") and t.media:
        # photos
        if hasattr(t.media, "photos"):
            for p in t.media.photos:
                if hasattr(p, "url"):
                    media_list.append({"type": "photo", "url": p.url})
        # videos
        if hasattr(t.media, "videos"):
            for v in t.media.videos:
                thumb = getattr(v, "thumbnailUrl", "")
                media_list.append({"type": "video", "thumbnail": thumb, "url": thumb})

    user_info = {}
    if hasattr(t, "user") and t.user:
        user_info = {
            "username": getattr(t.user, "username", ""),
            "displayname": getattr(t.user, "displayname", ""),
            "profile_image_url": getattr(t.user, "profileImageUrl", ""),
            "verified": bool(getattr(t.user, "verified", False) or getattr(t.user, "blue", False))
        }

    return {
        "id": str(getattr(t, "id", "")),
        "url": getattr(t, "url", ""),
        "date": getattr(t, "date", None).strftime("%Y-%m-%d %H:%M:%S UTC") if getattr(t, "date", None) else "",
        "text": getattr(t, "rawContent", ""),
        "user": user_info,
        "reply_count": getattr(t, "replyCount", 0),
        "retweet_count": getattr(t, "retweetCount", 0),
        "like_count": getattr(t, "likeCount", 0),
        "quote_count": getattr(t, "quoteCount", 0),
        "view_count": getattr(t, "viewCount", None) or 0,
        "source": getattr(t, "sourceLabel", "") or "Web",
        "lang": getattr(t, "lang", "en"),
        "hashtags": getattr(t, "hashtags", []) or [],
        "media": media_list
    }

async def get_accounts_pool_info() -> List[Dict[str, Any]]:
    """Returns active accounts currently saved in the twscrape pool."""
    api = get_twscrape_api()
    try:
        return await api.pool.accounts_info()
    except Exception:
        return []

async def add_session_cookies_to_pool(cookie_str: str, account_name: str = "oasis_user") -> bool:
    """Adds or updates session cookies (auth_token & ct0) into twscrape pool."""
    if not cookie_str or "auth_token=" not in cookie_str:
        return False
    api = get_twscrape_api()
    await api.pool.add_account_cookies(account_name, cookie_str)
    return True

async def scrape_twitter_async(
    target: str,
    count: int = 10,
    target_type: str = "user",
    session_cookie: str = "",
    proxy: str = ""
) -> Dict[str, Any]:
    """
    Executes async Twitter/X reconnaissance via twscrape.
    """
    clean_target = sanitize_x_target(target)
    start_t = time.time()
    api = get_twscrape_api(proxy=proxy)

    # 1. If user supplied a session cookie, update it in pool
    if session_cookie and "auth_token=" in session_cookie:
        await api.pool.add_account_cookies("oasis_session", session_cookie)

    # 2. Check if accounts pool has active accounts
    pool_accs = await api.pool.accounts_info()
    active_accs = [a for a in pool_accs if a.get("active") and a.get("logged_in")]
    if not active_accs:
        raise NoAccountError(
            "An authorized X/Twitter session cookie (auth_token and ct0) is required to query Twitter GraphQL endpoints directly. "
            "Please supply your session cookie in Advanced Configuration, or click 'Pro Mode' to route through the dedicated cluster at http://xintel.rkmvcse.in/."
        )

    profile_data = {}
    tweets_data = []

    # 3. Route according to target_type
    if target_type == "user":
        # Profile lookup
        user_obj = await api.user_by_login(clean_target)
        if not user_obj:
            raise ValueError(f"User @{clean_target} not found on X/Twitter.")
        profile_data = format_user_dict(user_obj)

        # Timeline tweets
        raw_tweets = await gather(api.user_tweets(user_obj.id, limit=count))
        tweets_data = [format_tweet_dict(t) for t in raw_tweets if t]

    elif target_type in ["search", "hashtag"]:
        # Search query
        query = clean_target if target_type == "search" else f"#{clean_target.lstrip('#')}"
        raw_tweets = await gather(api.search(query, limit=count))
        tweets_data = [format_tweet_dict(t) for t in raw_tweets if t]
        if tweets_data and tweets_data[0].get("user"):
            profile_data = {
                "username": query,
                "displayname": f"Search Query: {query}",
                "bio": f"Extracted {len(tweets_data)} live tweets matching search criteria.",
                "followers_count": len(tweets_data),
                "url": f"https://x.com/search?q={query}"
            }

    elif target_type == "tweet":
        # Tweet ID details and replies
        tweet_id = int(re.sub(r'\D', '', clean_target))
        main_tweet = await api.tweet_details(tweet_id)
        if main_tweet:
            formatted_main = format_tweet_dict(main_tweet)
            tweets_data.append(formatted_main)
            profile_data = formatted_main.get("user", {})

        raw_replies = await gather(api.tweet_replies(tweet_id, limit=count))
        for r in raw_replies:
            if r and str(r.id) != str(tweet_id):
                tweets_data.append(format_tweet_dict(r))

    else:
        raise ValueError(f"Unsupported Twitter target type: '{target_type}'. Use 'user', 'search', or 'tweet'.")

    elapsed = round(time.time() - start_t, 2)

    total_likes = sum(t.get("like_count", 0) for t in tweets_data)
    total_retweets = sum(t.get("retweet_count", 0) for t in tweets_data)
    total_replies = sum(t.get("reply_count", 0) for t in tweets_data)

    return {
        "target": clean_target,
        "target_type": target_type,
        "duration": elapsed,
        "profile": profile_data,
        "tweets": tweets_data,
        "stats": {
            "total_tweets": len(tweets_data),
            "total_likes": total_likes,
            "total_retweets": total_retweets,
            "total_replies": total_replies
        },
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())
    }

def scrape_twitter(
    target: str,
    count: int = 10,
    target_type: str = "user",
    session_cookie: str = "",
    proxy: str = ""
) -> Dict[str, Any]:
    """Synchronous entry point that runs scrape_twitter_async in an event loop."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(scrape_twitter_async(
            target=target,
            count=count,
            target_type=target_type,
            session_cookie=session_cookie,
            proxy=proxy
        ))
    finally:
        loop.close()
