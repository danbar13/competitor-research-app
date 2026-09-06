import json
import urllib.request
import urllib.error
import time
from datetime import datetime
from typing import List, Dict, Any, Optional
from .settings import RAW_DIR

def validate_apify_token(token: str) -> Dict[str, Any]:
    """Verify Apify token and return user information or error."""
    if not token or not token.strip():
        return {"valid": False, "error": "טוקן ריק"}
        
    url = f"https://api.apify.com/v2/users/me?token={token.strip()}"
    try:
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=10) as response:
            if response.status == 200:
                data = json.loads(response.read().decode("utf-8"))
                user_info = data.get("data", {})
                return {
                    "valid": True,
                    "username": user_info.get("username", "Unknown"),
                    "email": user_info.get("email", ""),
                    "plan": user_info.get("plan", {}).get("name", "Standard")
                }
    except urllib.error.HTTPError as e:
        return {"valid": False, "error": f"שגיאת הרשאה או טוקן שגוי (HTTP {e.code})"}
    except Exception as e:
        return {"valid": False, "error": f"שגיאת תקשורת: {str(e)}"}
        
    return {"valid": False, "error": "אימות נכשל"}

def scrape_linkedin_profiles(urls: List[str], token: str) -> List[Dict[str, Any]]:
    """
    Scrape LinkedIn profiles in bulk using harvestapi/linkedin-profile-scraper.
    Accepts both personal profile URLs and company URLs.
    """
    if not urls:
        return []
        
    clean_urls = [u.strip() for u in urls if u and u.strip()]
    if not clean_urls:
        return []
        
    actor_id = "harvestapi~linkedin-profile-scraper"
    api_url = f"https://api.apify.com/v2/acts/{actor_id}/run-sync-get-dataset-items?token={token.strip()}"
    
    payload = {"urls": clean_urls}
    data_bytes = json.dumps(payload).encode("utf-8")
    
    req = urllib.request.Request(
        api_url,
        data=data_bytes,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    
    try:
        with urllib.request.urlopen(req, timeout=180) as response:
            if response.status in (200, 201):
                body = response.read().decode("utf-8")
                data = json.loads(body)
                
                # Save raw output if filesystem is writable
                try:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    raw_path = RAW_DIR / f"profiles_{timestamp}.json"
                    with open(raw_path, "w", encoding="utf-8") as f:
                        json.dump(data, f, ensure_ascii=False, indent=2)
                except Exception:
                    pass
                    
                return data
            else:
                raise RuntimeError(f"Apify returned HTTP status {response.status}")
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8") if e.fp else str(e)
        raise RuntimeError(f"HTTP Error {e.code} from Apify: {err_body}")
    except Exception as e:
        raise RuntimeError(f"Error executing profile scraper: {str(e)}")

def scrape_linkedin_posts(urls: List[str], max_posts: int = 5, token: str = "") -> List[Dict[str, Any]]:
    """
    Scrape recent LinkedIn posts using harvestapi/linkedin-profile-posts.
    """
    if not urls:
        return []
        
    clean_urls = [u.strip() for u in urls if u and u.strip()]
    if not clean_urls:
        return []
        
    actor_id = "harvestapi~linkedin-profile-posts"
    api_url = f"https://api.apify.com/v2/acts/{actor_id}/run-sync-get-dataset-items?token={token.strip()}"
    
    payload = {
        "targetUrls": clean_urls,
        "maxPosts": max_posts
    }
    data_bytes = json.dumps(payload).encode("utf-8")
    
    req = urllib.request.Request(
        api_url,
        data=data_bytes,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    
    try:
        with urllib.request.urlopen(req, timeout=180) as response:
            if response.status in (200, 201):
                body = response.read().decode("utf-8")
                data = json.loads(body)
                
                try:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    raw_path = RAW_DIR / f"posts_{timestamp}.json"
                    with open(raw_path, "w", encoding="utf-8") as f:
                        json.dump(data, f, ensure_ascii=False, indent=2)
                except Exception:
                    pass
                    
                return data
            else:
                raise RuntimeError(f"Apify returned HTTP status {response.status}")
    except Exception as e:
        raise RuntimeError(f"Error executing posts scraper: {str(e)}")
