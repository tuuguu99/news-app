"""
news.mn — Entertainment мэдээ (нэг хуудастай локал апп)
Ажиллуулах:
    pip install -r requirements.txt
    streamlit run app.py
"""
import requests
import streamlit as st
from bs4 import BeautifulSoup

URL = "https://news.mn/angilal/entertainment/"
HEADERS = {
    "User-Agent": ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                   "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"),
    "Accept-Language": "mn,en;q=0.9",
}


@st.cache_data(ttl=600)  # 10 минут кэшлэнэ — refresh товчоор шинэчилнэ
def fetch_news():
    res = requests.get(URL, headers=HEADERS, timeout=30)
    res.raise_for_status()
    soup = BeautifulSoup(res.text, "html.parser")

    items = []
    for art in soup.find_all("article"):
        title_el = art.select_one("h1.entry-title a")
        if not title_el or not title_el.get("href"):
            continue
        img_el = art.select_one(".tw-thumbnail img")
        excerpt_el = art.select_one(".entry-content p")
        date_el = art.select_one(".tw-meta.entry-date")

        items.append({
            "title": title_el.get_text(strip=True),
            "link": title_el["href"],
            "image": img_el.get("src") if img_el else None,
            "excerpt": excerpt_el.get_text(strip=True) if excerpt_el else "",
            "date": date_el.get_text(strip=True) if date_el else "",
        })
    return items


# ── Хуудасны тохиргоо ──
st.set_page_config(page_title="news.mn — Энтертайнмент", page_icon="📰", layout="wide")

st.markdown("""
<style>
.news-card {
    background: #fff; border: 1px solid #e5e7eb; border-radius: 14px;
    overflow: hidden; height: 100%; transition: all .2s;
}
.news-card:hover { box-shadow: 0 8px 24px rgba(0,0,0,.1); transform: translateY(-3px); }
.news-card img { width: 100%; height: 180px; object-fit: cover; }
.news-body { padding: 14px 16px; }
.news-title { font-size: 1rem; font-weight: 700; color: #111827; line-height: 1.4; margin-bottom: 6px; }
.news-title a { color: #111827; text-decoration: none; }
.news-title a:hover { color: #2563eb; }
.news-excerpt { font-size: .85rem; color: #6b7280; line-height: 1.5; margin-bottom: 8px; }
.news-date { font-size: .75rem; color: #9ca3af; }
</style>
""", unsafe_allow_html=True)

# ── Толгой ──
col1, col2 = st.columns([4, 1])
with col1:
    st.title("📰 news.mn — Энтертайнмент")
    st.caption("Эх сурвалж: news.mn/angilal/entertainment")
with col2:
    st.write("")
    if st.button("🔄 Шинэчлэх", use_container_width=True):
        fetch_news.clear()   # кэш цэвэрлээд дахин татна
        st.rerun()

# ── Дата татах ──
try:
    news = fetch_news()
except Exception as e:
    st.error(f"Мэдээ татахад алдаа гарлаа: {type(e).__name__}: {e}")
    st.stop()

if not news:
    st.warning("Мэдээ олдсонгүй. Сайтын бүтэц өөрчлөгдсөн байж магадгүй.")
    st.stop()

st.success(f"Нийт {len(news)} мэдээ ачааллаа")

# ── Хайлт ──
q = st.text_input("🔍 Гарчигаар хайх", placeholder="түлхүүр үг...")
if q:
    news = [n for n in news if q.lower() in n["title"].lower()]
    st.caption(f"{len(news)} мэдээ олдлоо")

# ── Картаар харуулах (3 баганаар) ──
cols = st.columns(3)
for i, n in enumerate(news):
    with cols[i % 3]:
        img_html = f'<img src="{n["image"]}" alt="">' if n["image"] else ""
        st.markdown(f"""
        <div class="news-card">
            {img_html}
            <div class="news-body">
                <div class="news-title"><a href="{n['link']}" target="_blank">{n['title']}</a></div>
                <div class="news-excerpt">{n['excerpt'][:120]}{'...' if len(n['excerpt']) > 120 else ''}</div>
                <div class="news-date">🕒 {n['date']}</div>
            </div>
        </div>
        <div style="height:18px"></div>
        """, unsafe_allow_html=True)
