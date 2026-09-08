import time
import threading
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from datetime import datetime
from flask import Flask, render_template_string, jsonify
import urllib3

# SSL warning disable
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

app = Flask(__name__)

HBTU_TIMETABLE_URL = "https://hbtu.ac.in/time-table/"

DATA_STORE = {
    "latest": None,
    "all_tables": [],
    "last_updated": "Not fetched yet",
    "status": "pending"
}

def clean_google_link(url):
    if "docs.google.com/spreadsheets" in url:
        base = url.split("?")[0]
        return f"{base}?widget=true&headers=false"
    return url

def scrape_hbtu():
    global DATA_STORE
    headers = {
        "User-Agent": "Mozilla/5.0 (Linux; Android 10) AppleWebKit/537.36 Chrome/120.0.0.0 Mobile Safari/537.36"
    }

    try:
        response = requests.get(HBTU_TIMETABLE_URL, headers=headers, timeout=20, verify=False)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        extracted_items = []

        for a_tag in soup.find_all("a", href=True):
            text = a_tag.get_text(strip=True)
            href = a_tag["href"].strip()

            if not text or not href:
                continue

            lower_text = text.lower()
            if "timetable" in lower_text or "time table" in lower_text or "sheet" in href or "drive.google" in href:
                full_url = urljoin(HBTU_TIMETABLE_URL, href)
                embed_url = clean_google_link(full_url)
                
                tag = "General"
                if "b.tech" in lower_text:
                    tag = "B.Tech"
                elif "mca" in lower_text:
                    tag = "MCA"
                elif "m.tech" in lower_text:
                    tag = "M.Tech"
                elif "msc" in lower_text or "m.sc" in lower_text or "bs" in lower_text:
                    tag = "BS / M.Sc"

                extracted_items.append({
                    "title": text,
                    "url": full_url,
                    "embed_url": embed_url,
                    "tag": tag,
                    "is_google_sheet": "spreadsheets" in full_url
                })

        if extracted_items:
            btech_first = next((item for item in extracted_items if item["tag"] == "B.Tech"), extracted_items[0])
            DATA_STORE["latest"] = btech_first
            DATA_STORE["all_tables"] = extracted_items
            DATA_STORE["status"] = "success"
        else:
            DATA_STORE["status"] = "empty"

        DATA_STORE["last_updated"] = datetime.now().strftime("%d %b %Y, %I:%M %p")
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Found {len(extracted_items)} links from HBTU")

    except Exception as e:
        print(f"Scrape error: {e}")
        DATA_STORE["status"] = "error"
        DATA_STORE["last_updated"] = datetime.now().strftime("%d %b %Y, %I:%M %p")

def background_worker():
    while True:
        scrape_hbtu()
        time.sleep(1800)

worker_thread = threading.Thread(target=background_worker, daemon=True)
worker_thread.start()

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>HBTU Timetable Portal</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-slate-950 text-slate-100 min-h-screen p-4 flex flex-col justify-between">

    <div class="max-w-4xl mx-auto w-full space-y-5">
        
        <!-- Header -->
        <header class="flex flex-col sm:flex-row sm:items-center justify-between border-b border-slate-800 pb-4 gap-2">
            <div>
                <div class="flex items-center gap-2">
                    <span class="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-ping"></span>
                    <h1 class="text-xl font-bold text-white tracking-tight">HBTU Timetable Hub</h1>
                </div>
                <p class="text-xs text-slate-400 mt-0.5">Live Sync with hbtu.ac.in/time-table</p>
            </div>
            
            <!-- Creator Badge in Header -->
            <div class="flex flex-col sm:items-end">
                <span class="text-[11px] text-slate-400">Created by <span class="text-indigo-400 font-semibold">Arham Hasan</span></span>
                <span class="text-[10px] text-slate-500">1st Year, BS Mathematics & Data Science</span>
            </div>
        </header>

        {% if data.status == 'success' and data.latest %}
        <!-- Active Spotlight -->
        <div class="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-lg space-y-3">
            <div class="flex items-center justify-between">
                <span class="px-2 py-0.5 text-xs font-semibold rounded bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                    Active: {{ data.latest.tag }}
                </span>
                <a href="{{ data.latest.url }}" target="_blank" class="px-3 py-1.5 text-xs font-medium bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg transition">
                    Open Google Sheet &nearr;
                </a>
            </div>
            <h2 class="text-base font-semibold text-white">{{ data.latest.title }}</h2>

            <div class="rounded-lg overflow-hidden border border-slate-800 bg-white">
                <iframe src="{{ data.latest.embed_url }}" class="w-full h-[450px] border-0"></iframe>
            </div>
        </div>

        <!-- All Sheets Section -->
        <div class="space-y-2">
            <div class="flex justify-between items-center">
                <h3 class="text-xs font-bold text-slate-400 uppercase tracking-wider">All Department Sheets</h3>
                <span class="text-[11px] text-slate-500 font-mono">Last Synced: {{ data.last_updated }}</span>
            </div>
            <div class="space-y-2">
                {% for item in data.all_tables %}
                <div class="bg-slate-900 border border-slate-800 p-3 rounded-lg flex items-center justify-between hover:border-slate-700 transition">
                    <div class="pr-2">
                        <span class="text-[10px] bg-slate-800 px-1.5 py-0.5 rounded text-slate-400 font-mono">{{ item.tag }}</span>
                        <p class="text-xs text-slate-200 mt-1 font-medium">{{ item.title }}</p>
                    </div>
                    <a href="{{ item.url }}" target="_blank" class="text-indigo-400 hover:text-indigo-300 text-xs font-medium shrink-0">Open &rarr;</a>
                </div>
                {% endfor %}
            </div>
        </div>

        {% elif data.status == 'pending' %}
            <div class="p-8 text-center text-slate-400 text-sm">Fetching links from HBTU... Please wait 3 seconds and refresh.</div>
        {% else %}
            <div class="p-8 text-center text-rose-400 text-sm">Failed to connect to HBTU. Please check internet connection.</div>
        {% endif %}

    </div>

    <!-- Footer Credits -->
    <footer class="mt-8 border-t border-slate-800/80 pt-4 pb-2 text-center">
        <p class="text-xs text-slate-400">
            Designed & Developed by <span class="text-slate-200 font-medium">Arham Hasan</span>
        </p>
        <p class="text-[11px] text-slate-500 mt-0.5">
            1st Year, BS in Mathematics and Data Science &bull; HBTU Kanpur
        </p>
    </footer>

</body>
</html>
"""

@app.route("/")
def home():
    return render_template_string(HTML_TEMPLATE, data=DATA_STORE)

@app.route("/api/timetables")
def api():
    return jsonify(DATA_STORE)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
