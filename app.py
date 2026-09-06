import streamlit as st
import os
import json
from pathlib import Path
from datetime import datetime

from core.settings import get_apify_token, save_apify_token, RESEARCH_DIR
from core.scraper import validate_apify_token, scrape_linkedin_profiles
from core.discovery import discover_competitors, ECOSYSTEM_CATALOG
from core.analyzer import parse_profile_item, generate_comparison_report
from core.pdf_exporter import export_report_to_pdf

# 1. Page Configuration
st.set_page_config(
    page_title="מחקר מתחרים ומיצוב בלינקדאין — דנבר",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. RTL & Modern Styling
st.markdown("""
<style>
    /* Target content containers without breaking Streamlit's sidebar layout */
    .block-container {
        direction: rtl;
        text-align: right;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    
    /* Markdown & text containers */
    div[data-testid="stMarkdownContainer"] {
        direction: rtl;
        text-align: right;
    }
    
    /* Headers styling */
    h1, h2, h3, h4 {
        text-align: right;
        color: #0f4c61;
    }
    
    /* Tabs alignment */
    div[data-testid="stTabs"] {
        direction: rtl;
    }
    
    /* Metrics and cards */
    [data-testid="stMetricValue"] {
        text-align: right;
        direction: ltr;
    }
    [data-testid="stMetricLabel"] {
        text-align: right;
    }
    
    /* Sidebar content without breaking container position */
    section[data-testid="stSidebar"] div[data-testid="stVerticalBlock"] {
        direction: rtl;
        text-align: right;
    }
    
    /* Form inputs and labels */
    label, .stTextInput, .stTextArea, .stSelectbox, .stCheckbox {
        direction: rtl;
        text-align: right;
    }
    
    /* Card box container */
    .report-box {
        background-color: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 20px;
        margin-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)

# 3. Session State Initialization
if "known_competitors" not in st.session_state:
    st.session_state.known_competitors = [""]
if "last_report_md" not in st.session_state:
    st.session_state.last_report_md = None
if "last_report_pdf" not in st.session_state:
    st.session_state.last_report_pdf = None
if "last_report_name" not in st.session_state:
    st.session_state.last_report_name = ""

# 4. Sidebar: Settings & Token Status
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/bullish.png", width=64)
    st.title("הגדרות מערכת")
    
    current_token = get_apify_token()
    token_status = validate_apify_token(current_token) if current_token else {"valid": False, "error": "לא הוגדר טוקן"}
    
    st.subheader("מפתח Apify API")
    if token_status.get("valid"):
        st.success(f"מחובר: {token_status.get('username')}")
        st.caption(f"תוכנית: {token_status.get('plan')}")
    else:
        st.error(f"סטטוס: {token_status.get('error')}")
        
    with st.expander("🔑 עדכון טוקן Apify"):
        new_token = st.text_input("הזן Apify Token", value=current_token, type="password")
        if st.button("שמור ואמת מפתח"):
            if new_token:
                save_apify_token(new_token)
                st.success("הטוקן נשמר!")
                st.rerun()

    st.markdown("---")
    st.subheader("📚 ארכיון דוחות קודמים")
    
    # List previous PDF and MD files in research/
    md_files = list(RESEARCH_DIR.glob("*.md"))
    if md_files:
        for f in md_files:
            pdf_match = RESEARCH_DIR / f"{f.stem}.pdf"
            st.markdown(f"**📄 {f.stem}**")
            cols = st.columns(2)
            with cols[0]:
                with open(f, "r", encoding="utf-8") as file_read:
                    st.download_button(
                        label="הורד MD",
                        data=file_read.read(),
                        file_name=f.name,
                        mime="text/markdown",
                        key=f"dl_md_{f.stem}"
                    )
            with cols[1]:
                if pdf_match.exists():
                    with open(pdf_match, "rb") as pdf_read:
                        st.download_button(
                            label="הורד PDF",
                            data=pdf_read.read(),
                            file_name=pdf_match.name,
                            mime="application/pdf",
                            key=f"dl_pdf_{f.stem}"
                        )
            st.markdown("<hr style='margin:8px 0;'>", unsafe_allow_html=True)
    else:
        st.caption("טרם הופקו דוחות היסטוריים.")

# 5. Main Application Header
st.title("🎯 מנוע מחקר ומיצוב מתחרים בלינקדאין")
st.markdown("אפליקציה חכמה למיפוי, ניתוח והשוואת נוכחות לינקדאין של העסק שלך מול מתחרים ידועים ומאותרים.")

tab_research, tab_archive = st.tabs(["🚀 מחקר חדש", "📑 צפייה בדוחות קודמים"])

# --- TAB 1: NEW RESEARCH ---
with tab_research:
    st.markdown("### שלב 1: פרטי העסק שלך / הלקוח")
    col1, col2 = st.columns(2)
    with col1:
        target_name = st.text_input(
            "שם העסק או המנהל (Target Business / Executive)",
            placeholder="למשל: דנבר (DANBAR) או דני ברקאי"
        )
        target_url = st.text_input(
            "קישור לפרופיל הלינקדאין הראשי להשוואה (URL)",
            placeholder="https://www.linkedin.com/in/..."
        )
    with col2:
        target_website = st.text_input(
            "כתובת אתר (אופציונלי)",
            placeholder="https://www.danbar.biz"
        )
        target_desc = st.text_area(
            "תיאור קצר של הפעילות, התחום וקהל היעד",
            placeholder="סוכנות ייעוץ אסטרטגי, הטמעת כלי Gen AI מעשיים, וניהול HR בעולמות המלונאות והטרוול-טק."
        )

    st.markdown("---")
    st.markdown("### שלב 2: הוספת מתחרים ידועים (Known Competitors)")
    st.caption("הוסף קישורי לינקדאין של מתחרים ספציפיים שברצונך לכלול בהשוואה.")

    # Dynamic competitor inputs
    competitor_inputs = []
    for i, comp_url in enumerate(st.session_state.known_competitors):
        col_c1, col_c2 = st.columns([5, 1])
        with col_c1:
            val = st.text_input(
                f"מתחרה ידוע #{i+1} (קישור לפרופיל לינקדאין)",
                value=comp_url,
                key=f"comp_{i}",
                placeholder="https://www.linkedin.com/in/... או https://www.linkedin.com/company/..."
            )
            competitor_inputs.append(val)
        with col_c2:
            st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
            if st.button("🗑️", key=f"del_{i}", help="הסר מתחרה זה"):
                st.session_state.known_competitors.pop(i)
                st.rerun()

    if st.button("➕ הוסף מתחרה ידוע נוסף"):
        st.session_state.known_competitors.append("")
        st.rerun()

    st.markdown("---")
    st.markdown("### שלב 3: איתור מתחרים אוטומטי מהאקוסיסטם (Auto-Discovery)")
    st.caption("המערכת מזהה ומציעה מתחרים ומובילי שוק רלוונטיים על בסיס תחום הפעילות שהזנת.")

    discovered_peers = discover_competitors(target_name, target_desc, target_website, limit=6)
    selected_discovered_urls = []

    if discovered_peers:
        st.markdown("**בחר מתחרים מומלצים להוספה למחקר:**")
        cols = st.columns(2)
        for idx, peer in enumerate(discovered_peers):
            col_target = cols[idx % 2]
            with col_target:
                is_selected = st.checkbox(
                    f"**{peer['name']}** — {peer['company']} ({peer['category']})",
                    value=False,
                    key=f"discovered_{idx}",
                    help=f"{peer['description']}\nקישור: {peer['linkedin_url']}"
                )
                if is_selected:
                    selected_discovered_urls.append(peer['linkedin_url'])
    else:
        st.info("הזן תיאור עסק כדי לקבל הצעות אוטומטיות למתחרים מהמאגר.")

    st.markdown("---")
    
    # Execute button
    run_col1, run_col2 = st.columns([2, 1])
    with run_col1:
        start_research = st.button("🚀 הפעל מחקר והשוואת מתחרים מלאה", use_container_width=True, type="primary")

    if start_research:
        # Validate inputs
        if not target_url:
            st.error("אנא הזן קישור לפרופיל הלינקדאין הראשי של העסק/המנהל להשוואה.")
        elif not current_token or not token_status.get("valid"):
            st.error("נדרש טוקן Apify תקין כדי להפעיל את הסריקה. הגדר אותו בפאנל הצד.")
        else:
            # Gather all URLs
            all_competitor_urls = [u.strip() for u in competitor_inputs if u.strip()]
            all_competitor_urls.extend(selected_discovered_urls)
            # Remove duplicates and avoid target URL
            unique_comp_urls = list(dict.fromkeys(all_competitor_urls))
            unique_comp_urls = [u for u in unique_comp_urls if u != target_url.strip()]

            if not unique_comp_urls:
                st.warning("אנא הגדר לפחות מתחרה אחד (ידוע או מתוך הרשימה המאותמת).")
            else:
                st.info(f"נבחרו {len(unique_comp_urls)} מתחרים להשוואה מול {target_name or 'פרופיל היעד'}.")
                
                with st.spinner("1/4 מתחבר ל-Apify ושואב את נתוני הפרופיל הראשי והמתחרים..."):
                    all_targets = [target_url.strip()] + unique_comp_urls
                    try:
                        raw_profiles = scrape_linkedin_profiles(all_targets, current_token)
                    except Exception as err:
                        st.error(f"שגיאה במהלך הסריקה: {err}")
                        raw_profiles = None

                if raw_profiles:
                    with st.spinner("2/4 מעבד מדדים ומנתח סגנונות מיצוב..."):
                        # Parse each profile
                        parsed_all = [parse_profile_item(p) for p in raw_profiles]
                        target_parsed = parsed_all[0]
                        competitors_parsed = parsed_all[1:]

                    with st.spinner("3/4 מגבש דוח השוואה מובנה והזדמנויות אסטרטגיות..."):
                        report_md = generate_comparison_report(
                            target_business_name=target_name or target_parsed.get("name", "העסק שלך"),
                            target_profile=target_parsed,
                            competitor_profiles=competitors_parsed,
                            business_context=target_desc
                        )

                    with st.spinner("4/4 מייצא לקובץ PDF מעוצב עם תמיכת RTL..."):
                        now_str = datetime.now().strftime("%Y-%m-%d")
                        safe_title = f"{now_str}-מחקר-מתחרים-{target_name or 'עסק'}"
                        pdf_path = export_report_to_pdf(report_md, filename_base=safe_title, title=f"מחקר מתחרים - {target_name}")

                    # Save to state
                    st.session_state.last_report_md = report_md
                    st.session_state.last_report_pdf = pdf_path
                    st.session_state.last_report_name = safe_title
                    st.success("המחקר הושלם בהצלחה! הדוח מוכן לצפייה ולהורדה למטה.")

    # Display results if available
    if st.session_state.last_report_md:
        st.markdown("---")
        st.subheader("📊 תוצאות המחקר ודוח ההשוואה")

        res_col1, res_col2 = st.columns(2)
        with res_col1:
            if st.session_state.last_report_pdf and Path(st.session_state.last_report_pdf).exists():
                with open(st.session_state.last_report_pdf, "rb") as pdf_file:
                    st.download_button(
                        label="📥 הורד דוח PDF מעוצב (RTL)",
                        data=pdf_file.read(),
                        file_name=f"{st.session_state.last_report_name}.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )
        with res_col2:
            st.download_button(
                label="📥 הורד דוח בפורמט Markdown",
                data=st.session_state.last_report_md,
                file_name=f"{st.session_state.last_report_name}.md",
                mime="text/markdown",
                use_container_width=True
            )

        with st.expander("📖 צפה בדוח המלא בתוך האפליקציה", expanded=True):
            st.markdown(st.session_state.last_report_md)

# --- TAB 2: ARCHIVE ---
with tab_archive:
    st.markdown("### דוחות היסטוריים שמורים")
    all_mds = list(RESEARCH_DIR.glob("*.md"))
    if not all_mds:
        st.info("אין דוחות שמורים בתיקיית המחקר.")
    else:
        selected_report = st.selectbox(
            "בחר דוח להצגה:",
            options=all_mds,
            format_func=lambda x: x.stem
        )
        if selected_report:
            with open(selected_report, "r", encoding="utf-8") as f:
                content = f.read()
            
            pdf_version = RESEARCH_DIR / f"{selected_report.stem}.pdf"
            arc_col1, arc_col2 = st.columns(2)
            with arc_col1:
                if pdf_version.exists():
                    with open(pdf_version, "rb") as pdf_f:
                        st.download_button(
                            label="📥 הורד גרסת PDF",
                            data=pdf_f.read(),
                            file_name=pdf_version.name,
                            mime="application/pdf",
                            key=f"archive_pdf_{selected_report.stem}"
                        )
            with arc_col2:
                st.download_button(
                    label="📥 הורד גרסת Markdown",
                    data=content,
                    file_name=selected_report.name,
                    mime="text/markdown",
                    key=f"archive_md_{selected_report.stem}"
                )
                
            st.markdown("---")
            st.markdown(content)
