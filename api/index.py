import os
import sys
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import List, Optional

# Add project root to sys.path so core modules can be imported
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from core.settings import get_apify_token
from core.scraper import validate_apify_token, scrape_linkedin_profiles
from core.discovery import discover_competitors
from core.analyzer import parse_profile_item, generate_comparison_report

app = FastAPI(title="Competitor Research API", version="1.0.0")

class ResearchRequest(BaseModel):
    target_name: str
    target_url: str
    target_desc: Optional[str] = ""
    target_website: Optional[str] = ""
    competitor_urls: List[str] = []
    apify_token: Optional[str] = ""

@app.get("/", response_class=HTMLResponse)
def home():
    token = get_apify_token()
    token_status = "מחובר ומאומת" if token else "נדרש מפתח"
    
    html = f"""<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>מנוע מחקר ומיצוב מתחרים בלינקדאין — דנבר</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Assistant:wght@300;400;600;700&display=swap" rel="stylesheet">
    <style>
        body {{ font-family: 'Assistant', sans-serif; background-color: #0f172a; color: #f8fafc; }}
    </style>
</head>
<body class="min-h-screen p-4 md:p-8">
    <div class="max-w-4xl mx-auto bg-slate-800 border border-slate-700 rounded-2xl shadow-2xl p-6 md:p-10">
        <header class="border-b border-slate-700 pb-6 mb-8 text-center md:text-right flex flex-col md:flex-row justify-between items-center gap-4">
            <div>
                <h1 class="text-3xl md:text-4xl font-bold text-teal-400">🎯 מנוע מחקר ומיצוב מתחרים בלינקדאין</h1>
                <p class="text-slate-400 mt-2">פותח על ידי דנבר (DANBAR) — אסטרטגיה, הון אנושי ובינה מלאכותית</p>
            </div>
            <div class="bg-slate-900 border border-slate-700 px-4 py-2 rounded-xl text-xs text-slate-300">
                סטטוס ענן Vercel: <span class="text-emerald-400 font-bold">פעיל (Live)</span>
            </div>
        </header>

        <section class="space-y-6">
            <div class="bg-slate-900/60 p-5 rounded-xl border border-slate-700/60">
                <h2 class="text-xl font-semibold text-teal-300 mb-4">1. פרטי העסק שלך / הלקוח להשוואה</h2>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                        <label class="block text-sm text-slate-300 mb-1">שם העסק או המנהל</label>
                        <input id="targetName" type="text" value="דנבר (DANBAR)" class="w-full bg-slate-800 border border-slate-600 rounded-lg p-2.5 text-white focus:ring-2 focus:ring-teal-400 focus:outline-none">
                    </div>
                    <div>
                        <label class="block text-sm text-slate-300 mb-1">פרופיל לינקדאין ראשי (URL)</label>
                        <input id="targetUrl" type="text" value="https://www.linkedin.com/in/danny-barkai/" class="w-full bg-slate-800 border border-slate-600 rounded-lg p-2.5 text-white focus:ring-2 focus:ring-teal-400 focus:outline-none">
                    </div>
                    <div class="md:col-span-2">
                        <label class="block text-sm text-slate-300 mb-1">תיאור קצר של התחום וקהל היעד</label>
                        <input id="targetDesc" type="text" value="ייעוץ אסטרטגי, הטמעת כלי Gen AI מעשיים, וניהול HR במלונאות וטרוול-טק" class="w-full bg-slate-800 border border-slate-600 rounded-lg p-2.5 text-white focus:ring-2 focus:ring-teal-400 focus:outline-none">
                    </div>
                </div>
            </div>

            <div class="bg-slate-900/60 p-5 rounded-xl border border-slate-700/60">
                <h2 class="text-xl font-semibold text-teal-300 mb-4">2. מתחרים להשוואה</h2>
                <p class="text-sm text-slate-400 mb-3">הזן קישורי לינקדאין של מתחרים (אחד בכל שורה):</p>
                <textarea id="competitorUrls" rows="4" class="w-full bg-slate-800 border border-slate-600 rounded-lg p-3 text-white focus:ring-2 focus:ring-teal-400 focus:outline-none font-mono text-sm" placeholder="https://www.linkedin.com/in/dorkrubiner/&#10;https://www.linkedin.com/in/amiadsoto/&#10;https://www.linkedin.com/in/itaigreen/">https://www.linkedin.com/in/dorkrubiner/
https://www.linkedin.com/in/amiadsoto/
https://www.linkedin.com/in/itaigreen/</textarea>
            </div>

            <div class="text-center pt-2">
                <button id="runBtn" onclick="runResearch()" class="w-full md:w-auto px-8 py-3.5 bg-gradient-to-r from-teal-500 to-emerald-600 hover:from-teal-400 hover:to-emerald-500 text-slate-950 font-bold rounded-xl shadow-lg transition duration-200">
                    🚀 הפעל מחקר והשוואת מתחרים
                </button>
            </div>

            <div id="loader" class="hidden text-center py-6 text-teal-300 font-semibold animate-pulse">
                ⏳ סורק נתונים מ-Apify ומעבד את הדוח... אנא המתן כדקה.
            </div>

            <div id="results" class="hidden mt-8 border-t border-slate-700 pt-6">
                <div class="flex justify-between items-center mb-4">
                    <h2 class="text-2xl font-bold text-teal-300">📊 תוצאות המחקר</h2>
                    <button onclick="downloadMarkdown()" class="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-sm font-semibold rounded-lg">📥 הורד דוח MD</button>
                </div>
                <div id="reportContent" class="bg-slate-900 p-6 rounded-xl border border-slate-700 whitespace-pre-wrap text-sm leading-relaxed text-slate-200"></div>
            </div>
        </section>
    </div>

    <script>
        let lastReport = "";
        async function runResearch() {{
            const btn = document.getElementById('runBtn');
            const loader = document.getElementById('loader');
            const results = document.getElementById('results');
            const content = document.getElementById('reportContent');

            const targetName = document.getElementById('targetName').value.trim();
            const targetUrl = document.getElementById('targetUrl').value.trim();
            const targetDesc = document.getElementById('targetDesc').value.trim();
            const compText = document.getElementById('competitorUrls').value.trim();

            if (!targetUrl) {{
                alert('אנא הזן פרופיל לינקדאין ראשי');
                return;
            }}

            const compUrls = compText.split('\\n').map(u => u.trim()).filter(u => u.length > 0);
            if (compUrls.length === 0) {{
                alert('אנא הזן לפחות מתחרה אחד');
                return;
            }}

            btn.disabled = true;
            btn.classList.add('opacity-50');
            loader.classList.remove('hidden');
            results.classList.add('hidden');

            try {{
                const res = await fetch('/api/research', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{
                        target_name: targetName,
                        target_url: targetUrl,
                        target_desc: targetDesc,
                        competitor_urls: compUrls
                    }})
                }});

                const data = await res.json();
                if (res.ok) {{
                    lastReport = data.report_md;
                    content.innerText = data.report_md;
                    results.classList.remove('hidden');
                }} else {{
                    alert('שגיאה: ' + (data.detail || 'נכשל בהפעלת המחקר'));
                }}
            }} catch (err) {{
                alert('שגיאת תקשורת: ' + err.message);
            }} finally {{
                btn.disabled = false;
                btn.classList.remove('opacity-50');
                loader.classList.add('hidden');
            }}
        }}

        function downloadMarkdown() {{
            if (!lastReport) return;
            const blob = new Blob([lastReport], {{ type: 'text/markdown;charset=utf-8;' }});
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'competitor-research-report.md';
            a.click();
        }}
    </script>
</body>
</html>"""
    return html

@app.post("/api/research")
def perform_research(req: ResearchRequest):
    token = req.apify_token.strip() if req.apify_token else get_apify_token()
    if not token:
        raise HTTPException(status_code=400, detail="נדרש מפתח Apify API תקין. הגדר אותו ב-Environment Variables.")
        
    all_urls = [req.target_url.strip()] + [u.strip() for u in req.competitor_urls if u.strip()]
    unique_urls = list(dict.fromkeys(all_urls))
    
    try:
        raw_profiles = scrape_linkedin_profiles(unique_urls, token)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"שגיאת סריקה ב-Apify: {str(e)}")
        
    if not raw_profiles:
        raise HTTPException(status_code=500, detail="לא התקבלו נתונים מ-Apify.")
        
    parsed_all = [parse_profile_item(p) for p in raw_profiles]
    target_parsed = parsed_all[0]
    competitors_parsed = parsed_all[1:]
    
    report_md = generate_comparison_report(
        target_business_name=req.target_name or target_parsed.get("name", "העסק שלך"),
        target_profile=target_parsed,
        competitor_profiles=competitors_parsed,
        business_context=req.target_desc or ""
    )
    
    return {
        "success": True,
        "report_md": report_md,
        "profiles_count": len(parsed_all)
    }

@app.get("/api/discover")
def discover_endpoint(business_name: str = "", description: str = "", limit: int = 4):
    peers = discover_competitors(business_name, description, limit=limit)
    return {"results": peers}
