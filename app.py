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
from google import genai

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


# ── Gemini чатбот (шинэ google-genai SDK) ──
@st.cache_resource
def get_gemini():
    """Gemini client. GEMINI_API_KEY байхгүй бол None."""
    key = st.secrets.get("GEMINI_API_KEY")
    if not key:
        return None
    return genai.Client(api_key=key)


def ask_ai(question, news_items):
    """Одоогийн мэдээг контекст болгон Gemini-ээс хариу авна."""
    client = get_gemini()
    if client is None:
        return "⚠️ Чатбот тохируулагдаагүй байна. secrets.toml-д GEMINI_API_KEY нэмнэ үү."

    # Одоогийн мэдээний гарчиг + хураангуйг контекст болгоно
    context = "\n".join(
        f"- {n.get('title','')} ({n.get('date_text','')}): {(n.get('excerpt') or '')[:120]}"
        for n in news_items[:30]
    )
    prompt = (
        "Чи news.mn-ийн энтертайнмент мэдээний AI туслах. "
        "Зөвхөн монголоор, товч бөгөөд найрсаг хариул. "
        "Доорх мэдээний жагсаалтад тулгуурлан хариул. Хэрэв жагсаалтад байхгүй бол ерөнхий мэдлэгээрээ хариулж болно.\n\n"
        f"=== Одоогийн мэдээ ===\n{context}\n\n"
        f"=== Хэрэглэгчийн асуулт ===\n{question}"
    )
    try:
        resp = client.models.generate_content(model="gemini-2.0-flash", contents=prompt)
        return resp.text
    except Exception as e:
        msg = str(e)
        if "RESOURCE_EXHAUSTED" in msg or "429" in msg:
            return "⚠️ Gemini-ийн өнөөдрийн үнэгүй квот дууссан байна. Маргааш дахин оролдоно уу."
        return f"⚠️ AI алдаа: {type(e).__name__}: {msg[:150]}"


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

/* ── Floating чат — баруун доод буланд ── */
div[data-testid="stPopover"] {
    position: fixed !important;
    bottom: 28px !important;
    right: 28px !important;
    left: auto !important;
    width: auto !important;
    min-width: 0 !important;
    max-width: none !important;
    z-index: 99999;
}
/* контейнер доторх бүх wrapper-ийг агшаах */
div[data-testid="stPopover"] > div {
    width: auto !important;
}
/* товчийг бүтэн өргөнөөс татгалзуулж дугуй pill болгох */
div[data-testid="stPopover"] button {
    width: auto !important;
    border-radius: 50px !important;
    background: linear-gradient(135deg, #1e3a8a, #2563eb) !important;
    color: #fff !important; font-weight: 700 !important;
    border: none !important;
    padding: 12px 24px !important;
    white-space: nowrap !important;
    box-shadow: 0 8px 24px rgba(37,99,235,.45) !important;
}
div[data-testid="stPopover"] button:hover {
    transform: translateY(-2px);
    box-shadow: 0 12px 30px rgba(37,99,235,.55) !important;
}
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

# ── Floating AI чатбот (баруун доод буланд) ──
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []


@st.fragment
def floating_chat(news_items):
    # popover нь rerun дээр хаагддаг тул fragment дотор тавьж нээлттэй байлгана
    with st.popover("💬 AI Туслах", use_container_width=False):
        st.markdown("#### 🤖 AI Туслах")
        st.caption("Мэдээний талаар асуу · Gemini")

        chat_box = st.container(height=320)
        for m in st.session_state.chat_history:
            with chat_box.chat_message(m["role"]):
                st.write(m["content"])

        if prompt := st.chat_input("Жишээ: өнөөдөр ямар мэдээ байна?"):
            st.session_state.chat_history.append({"role": "user", "content": prompt})
            with chat_box.chat_message("user"):
                st.write(prompt)
            with chat_box.chat_message("assistant"):
                with st.spinner("..."):
                    answer = ask_ai(prompt, news_items)
                st.write(answer)
            st.session_state.chat_history.append({"role": "assistant", "content": answer})

        if st.session_state.chat_history:
            if st.button("🗑️ Цэвэрлэх", use_container_width=True):
                st.session_state.chat_history = []
                st.rerun(scope="fragment")


floating_chat(news)

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
