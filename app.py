import streamlit as st
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from datetime import datetime
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Page Setup
st.set_page_config(
    page_title="HBTU Timetable Portal",
    page_icon="📅",
    layout="wide"
)

HBTU_TIMETABLE_URL = "https://hbtu.ac.in/time-table/"

# 15 minutes cache taaki baar-baar reload karne par college website block na kare
@st.cache_data(ttl=900)
def fetch_timetables():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    try:
        response = requests.get(HBTU_TIMETABLE_URL, headers=headers, timeout=20, verify=False)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        extracted = []
        for a_tag in soup.find_all("a", href=True):
            text = a_tag.get_text(strip=True)
            href = a_tag["href"].strip()

            if not text or not href:
                continue

            lower_text = text.lower()
            if "timetable" in lower_text or "time table" in lower_text or "sheet" in href or "drive.google" in href:
                full_url = urljoin(HBTU_TIMETABLE_URL, href)
                
                tag = "General"
                if "b.tech" in lower_text:
                    tag = "BS / B.Tech"
                elif "mca" in lower_text:
                    tag = "MCA"
                elif "m.tech" in lower_text:
                    tag = "M.Tech"
                elif "msc" in lower_text or "m.sc" in lower_text or "bs" in lower_text:
                    tag = "M.Sc"

                extracted.append({
                    "title": text,
                    "url": full_url,
                    "tag": tag
                })

        return extracted, datetime.now().strftime("%d %b %Y, %I:%M %p")
    except Exception as e:
        return [], str(e)

# --- Header & Credits ---
st.title("📅 HBTU Timetable Hub")
st.caption("Live Sync with official hbtu.ac.in portal")

# Credits block
st.info('''**Created by Arham Hasan** 
1st Year, BS Mathematics & Data Science, HBTU Kanpur''')

timetables, sync_time = fetch_timetables()

if not timetables:
    st.error(f"Timetables fetch nahi ho paaye. Error / Portal Down: {sync_time}")
else:
    st.caption(f"🕒 Last Checked: `{sync_time}`")

    # Dropdown selector
    options = [f"[{item['tag']}] {item['title']}" for item in timetables]
    selected_idx = st.selectbox("Select Department / Course Timetable:", range(len(options)), format_func=lambda x: options[x])

    selected_item = timetables[selected_idx]
    target_url = selected_item["url"]

    col1, col2 = st.columns([3, 1])
    with col1:
        st.subheader(selected_item["title"])
    with col2:
        st.link_button("Open Original Link ↗", target_url, use_container_width=True)

    # Embed Google Sheet
    if "docs.google.com/spreadsheets" in target_url:
        embed_url = target_url.split("?")[0] + "?widget=true&headers=false"
        st.markdown(
            f'<iframe src="{embed_url}" width="100%" height="700" style="border: 1px solid #ddd; border-radius: 8px;"></iframe>',
            unsafe_allow_html=True
        )
    else:
        st.warning("Yeh Google Sheet nahi hai. Upar diye link se direct open karein.")

    # All Links Accordion
    with st.expander("📁 View All Available Course Links"):
        for item in timetables:
            st.markdown(f"- **[{item['tag']}]** [{item['title']}]({item['url']})")

# Footer
st.divider()
st.markdown(
    "<div style='text-align: center; color: gray; font-size: 0.85rem;'>"
    "Designed & Developed by <b>Arham Hasan</b> (1st Year, BS Mathematics & Data Science)"
    "</div>",
    unsafe_allow_html=True
)
