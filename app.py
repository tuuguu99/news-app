"""
news.mn — Entertainment мэдээ (Supabase-аас уншина)
Дата нь GitHub Actions cron-оор scraper.py-аар автоматаар шинэчлэгддэг.

Ажиллуулах:
    pip install -r requirements.txt
    streamlit run app.py

Локалаар Supabase-д холбогдохын тулд .streamlit/secrets.toml файлд:
    SUPABASE_URL = "https://xxx.supabase.co"
    SUPABASE_KEY = "eyJ..."
"""
import streamlit as st
from supabase import create_client

# ── Supabase холболт ──
@st.cache_resource
def get_client():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])


@st.cache_data(ttl=120)  # 2 мин кэш — Supabase-аас уншихад л хамаарна (хурдан)
def load_news():
    sb = get_client()
    res = (sb.table("news")
             .select("*")
             .eq("category", "entertainment")
             .order("first_seen", desc=True)   # шинэ мэдээ дээрээ
             .limit(60)
             .execute())
    return res.data or []


# ── Хуудасны тохиргоо ──
st.set_page_config(page_title="news.mn — Энтертайнмент", page_icon="📰", layout="wide")

st.markdown("""
<style>
/* ── Streamlit-ийн дээд toolbar / GitHub / menu-г нуух ── */
#MainMenu {visibility: hidden;}
header {visibility: hidden;}
footer {visibility: hidden;}
[data-testid="stToolbar"] {display: none !important;}
[data-testid="stDecoration"] {display: none !important;}
[data-testid="stStatusWidget"] {display: none !important;}
.stDeployButton {display: none !important;}
[data-testid="stHeader"] {display: none !important;}

/* Дээд талын хоосон зайг багасгах */
[data-testid="stMainBlockContainer"] {padding-top: 1.5rem !important;}

/* ── Header banner ── */
.app-header {
    background: linear-gradient(120deg, #1e3a8a 0%, #2563eb 55%, #0ea5e9 100%);
    border-radius: 18px;
    padding: 28px 32px;
    margin-bottom: 8px;
    box-shadow: 0 10px 30px rgba(37,99,235,.25);
    position: relative;
    overflow: hidden;
}
.app-header::after {
    content: '📰';
    position: absolute; right: 24px; top: 50%;
    transform: translateY(-50%);
    font-size: 5rem; opacity: .15;
}
.app-header h1 {
    color: #fff !important; font-size: 2rem; font-weight: 800;
    margin: 0 0 6px 0; letter-spacing: -.5px;
}
.app-header p {
    color: rgba(255,255,255,.85) !important; font-size: .95rem; margin: 0;
}
.app-badge {
    display: inline-block; background: rgba(255,255,255,.2);
    color: #fff; font-size: .72rem; font-weight: 700;
    padding: 4px 12px; border-radius: 20px; margin-bottom: 12px;
    border: 1px solid rgba(255,255,255,.3);
}

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

# ── Толгой (gradient banner) ──
st.markdown("""
<div class="app-header">
    <span class="app-badge">🔄 30 мин тутам автоматаар шинэчлэгддэг</span>
    <h1>news.mn — Энтертайнмент</h1>
    <p>Монголын энтертайнмент мэдээ нэг дороос · Эх сурвалж: news.mn</p>
</div>
""", unsafe_allow_html=True)

col1, col2 = st.columns([5, 1])
with col2:
    if st.button("🔄 Шинэчлэх", use_container_width=True):
        load_news.clear()
        st.rerun()

# ── Дата унших ──
try:
    news = load_news()
except Exception as e:
    st.error(f"Supabase-аас унших алдаа: {type(e).__name__}: {e}")
    st.info("secrets.toml дотор SUPABASE_URL ба SUPABASE_KEY зөв эсэхийг шалга.")
    st.stop()

if not news:
    st.warning("Мэдээ алга. scraper.py ажилласан эсэх, Supabase-д дата байгаа эсэхийг шалга.")
    st.stop()

st.success(f"Нийт {len(news)} мэдээ")

# ── Хайлт ──
q = st.text_input("🔍 Гарчигаар хайх", placeholder="түлхүүр үг...")
if q:
    news = [n for n in news if q.lower() in (n.get("title") or "").lower()]
    st.caption(f"{len(news)} мэдээ олдлоо")

# ── Картаар харуулах (3 баганаар) ──
cols = st.columns(3)
for i, n in enumerate(news):
    with cols[i % 3]:
        img = n.get("image")
        excerpt = n.get("excerpt") or ""
        img_html = f'<img src="{img}" alt="">' if img else ""
        st.markdown(f"""
        <div class="news-card">
            {img_html}
            <div class="news-body">
                <div class="news-title"><a href="{n['link']}" target="_blank">{n['title']}</a></div>
                <div class="news-excerpt">{excerpt[:120]}{'...' if len(excerpt) > 120 else ''}</div>
                <div class="news-date">🕒 {n.get('date_text', '')}</div>
            </div>
        </div>
        <div style="height:18px"></div>
        """, unsafe_allow_html=True)
