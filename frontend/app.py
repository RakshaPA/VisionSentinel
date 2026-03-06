"""
VisionGuard AI — Streamlit Dashboard
Industrial-terminal aesthetic: dark steel + amber warnings + cyan data
"""
import streamlit as st
import requests, base64, os, io, time
from typing import Optional, Dict, Any, List

# ── Page Config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="VisionGuard AI",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Stylesheet ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@300;400;600&family=Barlow+Condensed:wght@300;400;600;700;900&display=swap');

/* ── Base ────────────────────────────────────────────────────────────────── */
:root {
  --bg0:     #0b0d0f;
  --bg1:     #111418;
  --bg2:     #181c22;
  --bg3:     #1e242c;
  --border:  rgba(0,200,255,0.12);
  --cyan:    #00c8ff;
  --cyan2:   #00e5c8;
  --amber:   #ffb300;
  --red:     #ff3d3d;
  --orange:  #ff6d00;
  --green:   #00e676;
  --muted:   #546e7a;
  --text:    #b0bec5;
  --texthi:  #e0f2fe;
  --mono:    'IBM Plex Mono', monospace;
  --display: 'Barlow Condensed', sans-serif;
}

.stApp { background: var(--bg0); color: var(--text); font-family: var(--mono); }
.stApp > header { background: transparent !important; }

/* Sidebar */
[data-testid="stSidebar"] {
  background: var(--bg1) !important;
  border-right: 1px solid var(--border);
}
[data-testid="stSidebar"] * { font-family: var(--mono) !important; }

/* Hide default Streamlit chrome */
#MainMenu, footer { visibility: hidden; }

/* ── Components ──────────────────────────────────────────────────────────── */
.vg-masthead {
  position: relative; padding: 28px 36px 24px;
  background: linear-gradient(135deg, #090c10 0%, #111820 60%, #0d1520 100%);
  border: 1px solid var(--border);
  border-top: 3px solid var(--cyan);
  border-radius: 4px; margin-bottom: 28px; overflow: hidden;
}
.vg-masthead::before {
  content: "";
  position: absolute; top: 0; right: 0;
  width: 40%; height: 100%;
  background: radial-gradient(ellipse at right, rgba(0,200,255,0.05) 0%, transparent 70%);
  pointer-events: none;
}
.vg-logo {
  font-family: var(--display); font-weight: 900; font-size: 2.8rem;
  letter-spacing: 6px; text-transform: uppercase; line-height: 1;
  color: var(--texthi);
}
.vg-logo span { color: var(--cyan); }
.vg-tagline {
  font-family: var(--mono); font-size: 0.72rem;
  color: var(--muted); letter-spacing: 4px; text-transform: uppercase;
  margin-top: 8px;
}
.vg-badges { position: absolute; top: 28px; right: 36px; display: flex; gap: 8px; }
.vg-badge {
  font-family: var(--mono); font-size: 0.62rem; letter-spacing: 2px;
  padding: 4px 10px; border-radius: 2px;
  background: rgba(0,200,255,0.08); color: var(--cyan);
  border: 1px solid rgba(0,200,255,0.25);
}

/* Stat cards */
.stat-grid { display: grid; grid-template-columns: repeat(4,1fr); gap: 12px; margin: 16px 0; }
.stat-card {
  background: var(--bg2); border: 1px solid var(--border); border-radius: 4px;
  padding: 18px 20px; position: relative; overflow: hidden;
}
.stat-card::before {
  content: attr(data-accent);
  position: absolute; bottom: -10px; right: 10px;
  font-size: 4rem; opacity: 0.06; font-family: var(--display); font-weight: 900;
}
.stat-val {
  font-family: var(--display); font-weight: 700; font-size: 2.4rem;
  color: var(--cyan); line-height: 1; letter-spacing: 1px;
}
.stat-val.amber { color: var(--amber); }
.stat-val.red   { color: var(--red); }
.stat-val.green { color: var(--green); }
.stat-lbl {
  font-family: var(--mono); font-size: 0.65rem;
  color: var(--muted); letter-spacing: 3px; text-transform: uppercase;
  margin-top: 6px;
}

/* Risk badges */
.rbadge {
  display: inline-block; padding: 3px 12px; border-radius: 2px;
  font-family: var(--mono); font-size: 0.72rem; font-weight: 600;
  letter-spacing: 2px; text-transform: uppercase;
}
.rbadge-low      { background: rgba(0,230,118,0.1);  color: #00e676; border: 1px solid #00e676; }
.rbadge-medium   { background: rgba(255,179,0,0.1);  color: #ffb300; border: 1px solid #ffb300; }
.rbadge-high     { background: rgba(255,109,0,0.1);  color: #ff6d00; border: 1px solid #ff6d00; }
.rbadge-critical { background: rgba(255,61,61,0.12); color: #ff3d3d; border: 1px solid #ff3d3d; }
.rbadge-unknown  { background: rgba(84,110,122,0.1); color: #546e7a; border: 1px solid #546e7a; }

/* Alert cards */
.alert-block {
  border-left: 3px solid #ff3d3d; background: rgba(255,61,61,0.04);
  border-radius: 0 4px 4px 0; padding: 12px 16px; margin: 8px 0;
}
.alert-block.medium { border-left-color: var(--amber); background: rgba(255,179,0,0.04); }
.alert-block.high   { border-left-color: var(--orange); background: rgba(255,109,0,0.04); }
.alert-block.low    { border-left-color: var(--green); background: rgba(0,230,118,0.04); }
.alert-type  { font-family: var(--mono); font-size: 0.78rem; font-weight: 600; letter-spacing: 2px; text-transform: uppercase; }
.alert-desc  { font-family: var(--mono); font-size: 0.8rem; color: var(--text); margin-top: 6px; line-height: 1.5; }

/* Scene boxes */
.scene-panel {
  background: var(--bg2); border: 1px solid var(--border); border-radius: 4px;
  padding: 18px 22px; margin: 10px 0;
}
.scene-hdr {
  font-family: var(--mono); font-size: 0.65rem; color: var(--cyan);
  letter-spacing: 4px; text-transform: uppercase; margin-bottom: 10px;
  display: flex; align-items: center; gap: 8px;
}
.scene-hdr::after {
  content: ""; flex: 1; height: 1px; background: var(--border);
}
.scene-body { font-family: var(--mono); font-size: 0.84rem; color: var(--texthi); line-height: 1.7; }

/* Detection rows */
.det-row {
  display: flex; align-items: center; gap: 8px;
  background: var(--bg3); border: 1px solid var(--border);
  border-radius: 3px; padding: 8px 14px; margin: 3px 0;
}
.det-cls  { font-family: var(--mono); color: var(--cyan); font-size: 0.82rem; flex: 1; }
.det-cnt  { font-family: var(--display); font-weight: 700; color: var(--amber); font-size: 1.1rem; width: 32px; text-align: center; }
.det-conf { font-family: var(--mono); color: var(--green); font-size: 0.75rem; width: 44px; text-align: right; }

/* Buttons */
.stButton > button {
  background: linear-gradient(135deg, rgba(0,200,255,0.15), rgba(0,200,255,0.08)) !important;
  color: var(--cyan) !important; border: 1px solid rgba(0,200,255,0.4) !important;
  border-radius: 3px !important; font-family: var(--mono) !important;
  font-size: 0.78rem !important; letter-spacing: 2px !important;
  text-transform: uppercase !important; padding: 0.55rem 1.8rem !important;
  transition: all 0.2s !important;
}
.stButton > button:hover {
  background: linear-gradient(135deg, rgba(0,200,255,0.25), rgba(0,200,255,0.15)) !important;
  box-shadow: 0 0 16px rgba(0,200,255,0.2) !important;
}

/* Tabs */
.stTabs [data-baseweb="tab"] {
  font-family: var(--mono) !important; font-size: 0.72rem !important;
  color: var(--muted) !important; letter-spacing: 3px !important;
  text-transform: uppercase !important;
}
.stTabs [aria-selected="true"] {
  color: var(--cyan) !important;
  border-bottom: 2px solid var(--cyan) !important;
}

/* File uploader */
[data-testid="stFileUploader"] section {
  background: rgba(0,200,255,0.02) !important;
  border: 1.5px dashed rgba(0,200,255,0.25) !important;
  border-radius: 4px !important;
}

/* Radio */
.stRadio label { font-family: var(--mono) !important; font-size: 0.78rem !important; }

/* Progress / metrics */
hr { border-color: var(--border) !important; }
.stMetric label { font-family: var(--mono) !important; font-size: 0.65rem !important; letter-spacing: 2px !important; }

/* Scrollbar */
::-webkit-scrollbar { width: 5px; }
::-webkit-scrollbar-track { background: var(--bg0); }
::-webkit-scrollbar-thumb { background: rgba(0,200,255,0.2); border-radius: 2px; }
</style>
""", unsafe_allow_html=True)


# ── Config ────────────────────────────────────────────────────────────────────
BACKEND = os.getenv("BACKEND_URL", "http://localhost:8000")
API     = f"{BACKEND}/api/v1"


# ── API Helpers ───────────────────────────────────────────────────────────────
def api_get(path: str) -> Optional[Any]:
    try:
        r = requests.get(f"{API}{path}", timeout=30)
        r.raise_for_status()
        return r.json()
    except Exception as exc:
        st.error(f"[API] {exc}")
        return None


def api_upload(path: str, data: bytes, name: str, ctype: str) -> Optional[Dict]:
    try:
        r = requests.post(f"{API}{path}",
                          files={"file": (name, io.BytesIO(data), ctype)},
                          timeout=180)
        r.raise_for_status()
        return r.json()
    except requests.HTTPError as exc:
        msg = exc.response.json().get("detail", str(exc)) if exc.response else str(exc)
        st.error(f"[API {exc.response.status_code if exc.response else '?'}] {msg}")
        return None
    except Exception as exc:
        st.error(f"[Connection] {exc}")
        return None


def backend_alive() -> bool:
    try:
        return requests.get(f"{BACKEND}/health", timeout=4).status_code == 200
    except Exception:
        return False


# ── UI Helpers ────────────────────────────────────────────────────────────────
_RISK_COLORS = {"low":"#00e676","medium":"#ffb300","high":"#ff6d00","critical":"#ff3d3d"}
_SEV_ICON    = {"low":"○","medium":"◆","high":"▲","critical":"⬡"}

def risk_badge(lvl: Optional[str]) -> str:
    l = (lvl or "unknown").lower()
    return f'<span class="rbadge rbadge-{l}">{l.upper()}</span>'

def rcolor(lvl: Optional[str]) -> str:
    return _RISK_COLORS.get((lvl or "").lower(), "#546e7a")

def fmt_time(ms: Optional[int]) -> str:
    if ms is None: return "—"
    return f"{ms} ms" if ms < 1000 else f"{ms/1000:.2f} s"

def sev_icon(s: str) -> str:
    return _SEV_ICON.get(s, "·")


# ── Result Renderer ───────────────────────────────────────────────────────────
def render_report(r: Dict, is_video: bool = False) -> None:
    st.markdown("---")
    rl    = r.get("risk_level") or "unknown"
    rs    = r.get("risk_score")  or 0.0
    color = rcolor(rl)

    # ── Stat row ─────────────────────────────────────────────────────────────
    c1,c2,c3,c4 = st.columns(4)
    def stat_card(col, val, lbl, accent_cls="", accent_char=""):
        col.markdown(
            f'<div class="stat-card" data-accent="{accent_char}">'
            f'<div class="stat-val {accent_cls}">{val}</div>'
            f'<div class="stat-lbl">{lbl}</div></div>',
            unsafe_allow_html=True
        )
    with c1:
        st.markdown(
            f'<div class="stat-card"><div style="margin-top:4px;">{risk_badge(rl)}</div>'
            f'<div class="stat-lbl">Risk Level</div></div>',
            unsafe_allow_html=True
        )
    with c2:
        cls = "red" if rs >= 0.8 else ("amber" if rs >= 0.5 else "green")
        stat_card(c2, f"{rs:.3f}", "Risk Score", cls, "RISK")
    with c3:
        stat_card(c3, r.get("total_objects",0), "Objects Detected", "", "OBJ")
    with c4:
        ac = r.get("alert_count",0)
        stat_card(c4, ac, "Active Alerts", "red" if ac>0 else "green", "ALT")

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Two-column body ───────────────────────────────────────────────────────
    left, right = st.columns([1, 1], gap="large")

    with left:
        st.markdown("#### 🧠 Scene Intelligence")
        sd = r.get("scene_description","")
        ar = r.get("ai_reasoning","")
        if sd:
            st.markdown(
                f'<div class="scene-panel"><div class="scene-hdr">Scene Description</div>'
                f'<div class="scene-body">{sd}</div></div>',
                unsafe_allow_html=True
            )
        if ar:
            st.markdown(
                f'<div class="scene-panel"><div class="scene-hdr">Security Reasoning</div>'
                f'<div class="scene-body">{ar}</div></div>',
                unsafe_allow_html=True
            )

        meta = r.get("metadata", {})
        tags = []
        if r.get("processing_time_ms"):
            tags.append(f"⏱ {fmt_time(r['processing_time_ms'])}")
        if r.get("file_size_bytes"):
            tags.append(f"📦 {r['file_size_bytes']//1024} KB")
        if is_video and meta.get("video_info"):
            vi = meta["video_info"]
            tags.append(f"🎞 {vi.get('frames_processed','?')} frames / {vi.get('resolution','')}")
        if tags:
            st.markdown(
                f'<p style="font-size:0.68rem;color:var(--muted,#546e7a);letter-spacing:2px;margin-top:4px;">'
                f'{" &nbsp;·&nbsp; ".join(tags)}</p>',
                unsafe_allow_html=True
            )

    with right:
        alerts = r.get("alerts", [])
        st.markdown(f"#### ⚠️ Security Alerts ({len(alerts)})")
        if alerts:
            for a in alerts:
                sev  = a.get("severity","low")
                icon = sev_icon(sev)
                atype = a.get("alert_type","").replace("_"," ").upper()
                st.markdown(
                    f'<div class="alert-block {sev}">'
                    f'<div class="alert-type" style="color:{rcolor(sev)};">'
                    f'{icon} {atype} &nbsp;<span style="opacity:.5">|</span>&nbsp; {sev.upper()}</div>'
                    f'<div class="alert-desc">{a.get("description","")}</div>'
                    f'</div>',
                    unsafe_allow_html=True
                )
        else:
            st.markdown(
                '<div class="scene-panel" style="border-color:rgba(0,230,118,0.2);">'
                '<div class="scene-hdr" style="color:#00e676;">All Clear</div>'
                '<div class="scene-body" style="color:#00e676;">No security alerts triggered. '
                'Scene is within normal parameters.</div></div>',
                unsafe_allow_html=True
            )

        objs = r.get("detected_objects", [])
        if objs:
            counts: Dict[str,int] = {}
            confs:  Dict[str,list] = {}
            for o in objs:
                cls = o.get("object_class","?")
                counts[cls] = counts.get(cls, 0) + 1
                confs.setdefault(cls,[]).append(o.get("confidence",0))
            st.markdown(f"#### 📦 Detections ({r.get('total_objects',0)})")
            for cls, cnt in sorted(counts.items(), key=lambda x:-x[1])[:12]:
                avg_c = sum(confs[cls])/len(confs[cls])
                st.markdown(
                    f'<div class="det-row"><span class="det-cls">▸ {cls}</span>'
                    f'<span class="det-cnt">{cnt}</span>'
                    f'<span class="det-conf">{avg_c:.0%}</span></div>',
                    unsafe_allow_html=True
                )

    # ── Annotated image ───────────────────────────────────────────────────────
    if not is_video and r.get("id"):
        ann = api_get(f"/analyze/image/{r['id']}/annotated")
        if ann and ann.get("image_base64"):
            st.markdown("#### 🖼️ Annotated Output — YOLOv8 Detections")
            img_bytes = base64.b64decode(ann["image_base64"])
            st.image(img_bytes, caption="Bounding boxes drawn by YOLOv8", use_column_width=True)


# ═══════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ═══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    alive = backend_alive()
    dot   = "🟢" if alive else "🔴"
    stxt  = "ONLINE" if alive else "OFFLINE"
    scol  = "#00e676" if alive else "#ff3d3d"

    st.markdown(f"""
    <div style="padding:20px 0 16px; border-bottom:1px solid rgba(0,200,255,0.12); margin-bottom:20px; text-align:center;">
        <div style="font-family:'Barlow Condensed',sans-serif;font-weight:900;font-size:1.4rem;
                    letter-spacing:6px;color:#e0f2fe;">VISION<span style="color:#00c8ff;">GUARD</span></div>
        <div style="font-family:'IBM Plex Mono',monospace;font-size:0.58rem;color:#546e7a;
                    letter-spacing:4px;margin-top:4px;">AI SURVEILLANCE SYSTEM</div>
        <div style="margin-top:12px;font-family:'IBM Plex Mono',monospace;font-size:0.65rem;
                    color:{scol};letter-spacing:3px;">{dot} BACKEND {stxt}</div>
    </div>
    """, unsafe_allow_html=True)

    page = st.radio(
        "NAVIGATION",
        ["ANALYZE", "DASHBOARD", "REPORTS", "ABOUT"],
        label_visibility="visible"
    )

    st.markdown("---")
    st.markdown("""
    <div style="font-family:'IBM Plex Mono',monospace;font-size:0.62rem;color:#37474f;
                line-height:1.8; padding-top:4px;">
        <div>STACK</div>
        <div style="color:#546e7a;">
            YOLOv8 · OpenCV<br>FastAPI · SQLAlchemy<br>
            HuggingFace · Streamlit<br>PostgreSQL · Docker
        </div>
    </div>
    """, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# MASTHEAD
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<div class="vg-masthead">
    <div class="vg-logo">🛡 <span>VISION</span>GUARD AI</div>
    <div class="vg-tagline">▸ Scene Understanding &amp; Risk Detection System — Powered by YOLOv8 + LLM</div>
    <div class="vg-badges">
        <span class="vg-badge">YOLOv8</span>
        <span class="vg-badge">FASTAPI</span>
        <span class="vg-badge">LLM</span>
        <span class="vg-badge">DOCKER</span>
    </div>
</div>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: ANALYZE
# ═══════════════════════════════════════════════════════════════════════════════
if page == "ANALYZE":
    tab_img, tab_vid = st.tabs(["  📷  IMAGE ANALYSIS  ", "  🎬  VIDEO ANALYSIS  "])

    # ── Image ─────────────────────────────────────────────────────────────────
    with tab_img:
        st.markdown("""
        <p style="font-family:'IBM Plex Mono',monospace;font-size:0.78rem;color:#546e7a;margin-bottom:16px;">
        Upload a surveillance image (JPEG / PNG / WEBP). YOLOv8 detects all objects,
        the risk engine evaluates security conditions, and the LLM generates scene reasoning.
        </p>""", unsafe_allow_html=True)

        upload_img = st.file_uploader(
            " ", type=["jpg","jpeg","png","webp"], key="upl_img",
            label_visibility="collapsed"
        )
        if upload_img:
            col_prev, col_meta = st.columns([1, 1], gap="large")
            with col_prev:
                st.markdown("**INPUT IMAGE**")
                st.image(upload_img, use_column_width=True)
            with col_meta:
                sz = upload_img.size
                st.markdown(f"""
                <div class="scene-panel">
                    <div class="scene-hdr">File Info</div>
                    <div class="scene-body">
                        <span style="color:#546e7a;">NAME &nbsp;</span> {upload_img.name}<br>
                        <span style="color:#546e7a;">SIZE &nbsp;</span> {sz/1024:.1f} KB<br>
                        <span style="color:#546e7a;">TYPE &nbsp;</span> {upload_img.type}
                    </div>
                </div>""", unsafe_allow_html=True)
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("⚡  RUN ANALYSIS", key="btn_img", use_container_width=True):
                    with st.spinner("Running YOLOv8 · Risk Engine · LLM Reasoning …"):
                        upload_img.seek(0)
                        data  = upload_img.read()
                        ext   = upload_img.name.rsplit(".",1)[-1].lower()
                        ct    = "image/jpeg" if ext in ("jpg","jpeg") else f"image/{ext}"
                        res   = api_upload("/analyze/image", data, upload_img.name, ct)
                    if res:
                        st.session_state["img_result"] = res
                        st.success("Analysis complete.")

        if "img_result" in st.session_state:
            render_report(st.session_state["img_result"], is_video=False)

    # ── Video ─────────────────────────────────────────────────────────────────
    with tab_vid:
        st.markdown("""
        <p style="font-family:'IBM Plex Mono',monospace;font-size:0.78rem;color:#546e7a;margin-bottom:16px;">
        Upload CCTV footage (MP4 / AVI / MOV). Frames are sampled at configurable intervals,
        YOLOv8 runs on each, and results are aggregated into a unified risk report.
        </p>""", unsafe_allow_html=True)

        upload_vid = st.file_uploader(
            " ", type=["mp4","avi","mov","mkv"], key="upl_vid",
            label_visibility="collapsed"
        )
        if upload_vid:
            mb = upload_vid.size / 1024 / 1024
            st.markdown(f"""
            <div class="scene-panel" style="margin-bottom:16px;">
                <div class="scene-hdr">Video File</div>
                <div class="scene-body">
                    {upload_vid.name} &nbsp;·&nbsp; {mb:.1f} MB &nbsp;·&nbsp; {upload_vid.type}
                </div>
            </div>""", unsafe_allow_html=True)
            if st.button("⚡  ANALYZE VIDEO", key="btn_vid", use_container_width=True):
                with st.spinner("Sampling frames · Running detection · Building report …"):
                    upload_vid.seek(0)
                    data = upload_vid.read()
                    ext  = upload_vid.name.rsplit(".",1)[-1].lower()
                    cmap = {"mp4":"video/mp4","avi":"video/avi","mov":"video/quicktime","mkv":"video/mkv"}
                    ct   = cmap.get(ext, "video/mp4")
                    res  = api_upload("/analyze/video", data, upload_vid.name, ct)
                if res:
                    st.session_state["vid_result"] = res
                    st.success("Video analysis complete.")

        if "vid_result" in st.session_state:
            render_report(st.session_state["vid_result"], is_video=True)


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: DASHBOARD
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "DASHBOARD":
    st.markdown("### 📊 Operations Dashboard")
    if st.button("↻  Refresh Stats"):
        st.rerun()

    stats = api_get("/reports/stats")
    if stats:
        # ── KPI row ───────────────────────────────────────────────────────────
        c1,c2,c3,c4 = st.columns(4)
        for col, val, lbl, cls, acc in [
            (c1, stats["total_analyses"],        "Total Analyses",     "",      "TOT"),
            (c2, stats["total_alerts"],           "Total Alerts",       "amber", "ALT"),
            (c3, stats.get("analyses_today",0),  "Analyses Today",     "cyan",  "DAY"),
            (c4, stats["recent_critical_alerts"], "Critical Alerts",    "red",   "CRI"),
        ]:
            col.markdown(
                f'<div class="stat-card" data-accent="{acc}">'
                f'<div class="stat-val {cls}">{val}</div>'
                f'<div class="stat-lbl">{lbl}</div></div>',
                unsafe_allow_html=True
            )

        st.markdown("<br>", unsafe_allow_html=True)
        left, right = st.columns(2, gap="large")

        # ── Risk distribution bar chart ───────────────────────────────────────
        with left:
            st.markdown("#### 🎯 Risk Distribution")
            rd  = stats.get("risk_distribution", {})
            if rd:
                order = ["critical","high","medium","low"]
                max_v = max(rd.values()) or 1
                for lvl in order:
                    cnt = rd.get(lvl, 0)
                    pct = cnt / max_v * 100
                    col = _RISK_COLORS.get(lvl, "#546e7a")
                    st.markdown(f"""
                    <div style="margin:8px 0;">
                      <div style="display:flex;justify-content:space-between;margin-bottom:4px;">
                        <span style="font-family:'IBM Plex Mono',monospace;font-size:0.75rem;color:{col};letter-spacing:2px;">{lvl.upper()}</span>
                        <span style="font-family:'IBM Plex Mono',monospace;font-size:0.75rem;color:{col};">{cnt}</span>
                      </div>
                      <div style="background:rgba(255,255,255,0.04);border-radius:2px;height:8px;">
                        <div style="background:{col};width:{pct}%;height:100%;border-radius:2px;opacity:0.75;"></div>
                      </div>
                    </div>""", unsafe_allow_html=True)
            else:
                st.info("No risk data yet. Run some analyses first.")

        # ── Top object classes ────────────────────────────────────────────────
        with right:
            st.markdown("#### 📦 Top Detected Object Classes")
            tobj = stats.get("top_detected_objects", {})
            if tobj:
                items = list(tobj.items())[:8]
                max_v = max(v for _, v in items) or 1
                for cls, cnt in items:
                    pct = cnt / max_v * 100
                    st.markdown(f"""
                    <div style="margin:8px 0;">
                      <div style="display:flex;justify-content:space-between;margin-bottom:4px;">
                        <span style="font-family:'IBM Plex Mono',monospace;font-size:0.75rem;color:#00c8ff;">{cls}</span>
                        <span style="font-family:'IBM Plex Mono',monospace;font-size:0.75rem;color:#546e7a;">{cnt}</span>
                      </div>
                      <div style="background:rgba(255,255,255,0.04);border-radius:2px;height:6px;">
                        <div style="background:linear-gradient(90deg,#00c8ff,#00e5c8);width:{pct}%;height:100%;border-radius:2px;opacity:0.6;"></div>
                      </div>
                    </div>""", unsafe_allow_html=True)
            else:
                st.info("No object detection data yet.")

        # ── Avg processing time ───────────────────────────────────────────────
        if stats.get("avg_processing_time_ms"):
            st.markdown("---")
            avg_ms = stats["avg_processing_time_ms"]
            st.markdown(
                f'<div class="scene-panel" style="text-align:center;">'
                f'<div class="scene-hdr" style="justify-content:center;">Average Processing Time</div>'
                f'<div style="font-family:\'Barlow Condensed\',sans-serif;font-weight:700;font-size:2.8rem;color:#00c8ff;">'
                f'{fmt_time(int(avg_ms))}</div></div>',
                unsafe_allow_html=True
            )


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: REPORTS
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "REPORTS":
    st.markdown("### 📋 Analysis Reports")

    fc1, fc2, fc3 = st.columns([2, 2, 1])
    with fc1:
        rf = st.selectbox("Filter — Risk Level", ["All","critical","high","medium","low"])
    with fc2:
        tf = st.selectbox("Filter — File Type", ["All","image","video"])
    with fc3:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("↻  Refresh"):
            st.rerun()

    parts = []
    if rf != "All": parts.append(f"risk_level={rf}")
    if tf != "All": parts.append(f"file_type={tf}")
    ep = "/reports/?" + "&".join(parts) if parts else "/reports/"
    reps = api_get(ep)

    if reps is not None:
        if not reps:
            st.markdown("""
            <div class="scene-panel" style="text-align:center;padding:32px;">
              <div style="font-family:'IBM Plex Mono',monospace;color:#546e7a;font-size:0.85rem;letter-spacing:2px;">
              NO REPORTS FOUND<br>
              <span style="font-size:0.72rem;">Upload an image or video to begin analysis.</span>
              </div>
            </div>""", unsafe_allow_html=True)
        else:
            for rep in reps:
                rl    = rep.get("risk_level","unknown") or "unknown"
                score = rep.get("risk_score",0) or 0
                ts    = rep.get("created_at","")[:19].replace("T"," ") if rep.get("created_at") else "—"
                icon  = "📷" if rep["file_type"] == "image" else "🎬"

                with st.expander(
                    f"{icon}  {rep['filename']}   ·   [{rl.upper()}]   ·   {ts}",
                    expanded=False,
                ):
                    mc1,mc2,mc3,mc4 = st.columns(4)
                    mc1.metric("Objects",    rep.get("total_objects",0))
                    mc2.metric("Alerts",     rep.get("alert_count",0))
                    mc3.metric("Risk Score", f"{score:.3f}")
                    mc4.metric("Processing", fmt_time(rep.get("processing_time_ms")))

                    bc1, bc2 = st.columns([5, 1])
                    with bc1:
                        if st.button("View Full Report", key=f"v_{rep['id']}"):
                            full = api_get(f"/reports/{rep['id']}")
                            if full:
                                st.session_state[f"rpt_{rep['id']}"] = full
                    with bc2:
                        if st.button("🗑 Delete", key=f"d_{rep['id']}"):
                            try:
                                r = requests.delete(f"{API}/reports/{rep['id']}", timeout=10)
                                if r.status_code == 200:
                                    st.success("Deleted.")
                                    st.rerun()
                            except Exception as exc:
                                st.error(str(exc))

                    if f"rpt_{rep['id']}" in st.session_state:
                        render_report(
                            st.session_state[f"rpt_{rep['id']}"],
                            rep["file_type"] == "video"
                        )


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: ABOUT
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "ABOUT":
    st.markdown("### ℹ️ About VisionGuard AI")
    st.markdown("""
    <div class="scene-panel">
      <div class="scene-hdr">System Overview</div>
      <div class="scene-body">
        VisionGuard AI is an intelligent surveillance analysis platform that combines
        <span style="color:#00c8ff;">YOLOv8</span> computer vision with
        <span style="color:#00c8ff;">Large Language Model</span> reasoning to automatically
        understand visual scenes and detect security threats. The system converts raw
        surveillance footage into structured, actionable intelligence reports.
      </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("#### 🔧 Technology Stack")
    stack = [
        ("🎯 YOLOv8",           "Ultralytics real-time object detection (80 COCO classes)"),
        ("🧠 HuggingFace / GPT","LLM scene understanding and security reasoning"),
        ("⚡ FastAPI",           "Async Python REST API with automatic OpenAPI docs"),
        ("🗄️ PostgreSQL",       "Relational DB for report storage and analytics"),
        ("🔬 OpenCV",            "Video frame extraction and image annotation"),
        ("🐳 Docker Compose",   "One-command containerised deployment"),
    ]
    cols = st.columns(3)
    for i, (name, desc) in enumerate(stack):
        with cols[i % 3]:
            st.markdown(
                f'<div class="scene-panel" style="margin:4px 0;">'
                f'<div style="font-family:\'Barlow Condensed\',sans-serif;font-weight:700;'
                f'font-size:1.05rem;color:#e0f2fe;">{name}</div>'
                f'<div style="font-size:0.78rem;color:#546e7a;margin-top:4px;">{desc}</div>'
                f'</div>',
                unsafe_allow_html=True
            )

    st.markdown("#### 🚦 Risk Level Reference")
    st.markdown("""
    | Level | Score Range | Description |
    |-------|-------------|-------------|
    | 🟢 LOW | 0.00 – 0.29 | No anomalies; routine monitoring |
    | 🟡 MEDIUM | 0.30 – 0.54 | Potentially suspicious; increased vigilance |
    | 🟠 HIGH | 0.55 – 0.79 | Security action recommended |
    | 🔴 CRITICAL | 0.80 – 1.00 | Immediate response required |
    """)

    st.markdown("#### 🔍 Detection Rules")
    rules_info = [
        ("unattended_bag",              "HIGH",     "Bag detected without a nearby owner"),
        ("crowd_gathering",             "MEDIUM",   "People count exceeds configured threshold"),
        ("weapon_detected",             "CRITICAL", "Knife or sharp implement visible in scene"),
        ("suspicious_loitering",        "MEDIUM",   "Person(s) present without purpose or belongings"),
        ("vehicle_in_restricted_zone",  "HIGH",     "Vehicle detected alongside pedestrians"),
        ("multiple_unattended_items",   "HIGH",     "≥2 bags with ≤1 person in scene"),
        ("person_with_concealed_device","LOW",      "Electronic device carried by person(s)"),
    ]
    for rule_id, sev, desc in rules_info:
        col = _RISK_COLORS.get(sev.lower(), "#546e7a")
        st.markdown(
            f'<div class="det-row">'
            f'<span class="det-cls">{rule_id}</span>'
            f'<span style="font-family:\'IBM Plex Mono\',monospace;font-size:0.7rem;'
            f'color:{col};width:72px;text-align:center;">{sev}</span>'
            f'<span style="font-family:\'IBM Plex Mono\',monospace;font-size:0.76rem;'
            f'color:#546e7a;flex:2;">{desc}</span>'
            f'</div>',
            unsafe_allow_html=True
        )

    st.markdown("#### 📡 API Endpoints")
    endpoints = [
        ("POST", "/api/v1/analyze/image",                    "Upload & analyse surveillance image"),
        ("POST", "/api/v1/analyze/video",                    "Upload & analyse CCTV video"),
        ("GET",  "/api/v1/analyze/image/{id}/annotated",     "Retrieve annotated image (base64)"),
        ("GET",  "/api/v1/reports/",                         "List reports (filter by risk/type)"),
        ("GET",  "/api/v1/reports/stats",                    "System-wide statistics"),
        ("GET",  "/api/v1/reports/{id}",                     "Fetch complete report"),
        ("DEL",  "/api/v1/reports/{id}",                     "Delete report + associated data"),
        ("GET",  "/health",                                   "Backend health check"),
        ("GET",  "/docs",                                     "Interactive Swagger UI"),
    ]
    for method, path, desc in endpoints:
        mcol = {"POST":"#00c8ff","GET":"#00e676","DEL":"#ff3d3d"}.get(method,"#546e7a")
        st.markdown(
            f'<div class="det-row">'
            f'<span style="font-family:\'IBM Plex Mono\',monospace;font-size:0.7rem;'
            f'color:{mcol};width:36px;font-weight:600;">{method}</span>'
            f'<span style="font-family:\'IBM Plex Mono\',monospace;font-size:0.78rem;'
            f'color:#00c8ff;flex:2;">{path}</span>'
            f'<span style="font-family:\'IBM Plex Mono\',monospace;font-size:0.74rem;'
            f'color:#546e7a;flex:2;">{desc}</span>'
            f'</div>',
            unsafe_allow_html=True
        )