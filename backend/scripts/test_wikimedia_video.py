import asyncio
import httpx
from typing import List

async def search_wikimedia_video(query: str) -> List[dict]:
    url = "https://commons.wikimedia.org/w/api.php"
    params = {
        "action": "query",
        "generator": "search",
        "gsrsearch": f"{query} filetype:video",
        "gsrnamespace": 6,
        "prop": "imageinfo",
        "iiprop": "url|mime|size",
        "format": "json",
        "gsrlimit": 5,
    }
    headers = {"User-Agent": "AIShortsFactory/1.0 (contact@shortsfactory.local)"}
    try:
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            res = await client.get(url, params=params, headers=headers)
            if res.status_code != 200:
                return []
            pages = res.json().get("query", {}).get("pages", {})
            results = []
            for pid, pdata in pages.items():
                info = pdata.get("imageinfo", [{}])[0]
                url_str = info.get("url", "")
                mime = info.get("mime", "")
                size = info.get("size", 0)
                if any(ext in url_str.lower() for ext in [".webm", ".mp4", ".ogv"]) or mime.startswith("video/"):
                    results.append({"title": pdata.get("title"), "url": url_str, "size": size})
            return results
    except Exception as e:
        print("Error:", e)
        return []

async def main():
    topics = ["nature wildlife", "stars galaxy", "underwater ocean", "robot technology", "ancient egypt pyramid", "storm lightning"]
    for t in topics:
        res = await search_wikimedia_video(t)
        print(f"Topic: '{t}' -> Found {len(res)} videos")
        if res:
            print(f"  First: {res[0]['title']} ({res[0]['size']} bytes)")

if __name__ == "__main__":
    asyncio.run(main())

