"""
news.mn entertainment scraper -> Supabase upsert
GitHub Actions cron-оор автоматаар ажиллана (хэн ч аппыг нээгээгүй ч).

Локалаар турших:
    pip install -r requirements_scraper.txt
    export SUPABASE_URL="https://xxx.supabase.co"
    export SUPABASE_KEY="eyJ..."
    python scraper.py
"""
import os
import requests
from bs4 import BeautifulSoup
from supabase import create_client

URL = "https://news.mn/angilal/entertainment/"
HEADERS = {
    "User-Agent": ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                   "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"),
    "Accept-Language": "mn,en;q=0.9",
}

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_KEY"]
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


def scrape():
    res = requests.get(URL, headers=HEADERS, timeout=30)
    res.raise_for_status()
    soup = BeautifulSoup(res.text, "html.parser")

    rows = []
    for art in soup.find_all("article"):
        title_el = art.select_one("h1.entry-title a")
        if not title_el or not title_el.get("href"):
            continue
        img_el = art.select_one(".tw-thumbnail img")
        excerpt_el = art.select_one(".entry-content p")
        date_el = art.select_one(".tw-meta.entry-date")

        rows.append({
            "link": title_el["href"],                          # primary key
            "title": title_el.get_text(strip=True),
            "image": img_el.get("src") if img_el else None,
            "excerpt": excerpt_el.get_text(strip=True) if excerpt_el else "",
            "category": "entertainment",
            "date_text": date_el.get_text(strip=True) if date_el else "",
            # first_seen-ийг ИЛГЭЭХГҮЙ → шинэ мэдээнд автоматаар now() орно,
            # хуучин мэдээний first_seen хөдлөхгүй (дараалал хадгалагдана)
        })
    return rows


def save(rows):
    if not rows:
        print("⚠️ Мэдээ олдсонгүй — selector шалга")
        return
    # link давхцвал шинэчилнэ, шинэ бол нэмнэ
    supabase.table("news").upsert(rows, on_conflict="link").execute()
    print(f"✅ {len(rows)} мэдээ Supabase-д шинэчлэгдлээ")


if __name__ == "__main__":
    try:
        rows = scrape()
        save(rows)
    except Exception as e:
        print(f"❌ Алдаа: {type(e).__name__}: {e}")
        raise   # GitHub Actions дээр алдааг улаанаар харуулна
