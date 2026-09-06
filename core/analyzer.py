"""
Module for processing scraped profile/post data and generating competitor reports.
"""
from typing import List, Dict, Any
from datetime import datetime

def parse_profile_item(p: Dict[str, Any]) -> Dict[str, Any]:
    """Clean and normalize a raw scraped profile dictionary."""
    first = p.get('firstName', '') or ''
    last = p.get('lastName', '') or ''
    name = f"{first.strip()} {last.strip()}".strip()
    if not name:
        # Check company name if it was a company page
        name = p.get('name') or p.get('companyName') or p.get('publicIdentifier', 'Unknown')
        
    identifier = p.get('publicIdentifier', '') or ''
    url = p.get('linkedinUrl', '') or ''
    headline = p.get('headline', '') or ''
    followers = p.get('followerCount', 0) or 0
    connections = p.get('connectionsCount', 0) or 0
    about = p.get('about', '') or ''
    
    current_positions = []
    for pos in p.get('currentPosition', []):
        current_positions.append({
            'title': pos.get('position'),
            'company': pos.get('companyName'),
            'duration': pos.get('duration'),
            'startDate': pos.get('startDate', {}).get('text') if isinstance(pos.get('startDate'), dict) else ''
        })
        
    skills = []
    for s in p.get('skills', []):
        if isinstance(s, dict) and s.get('name'):
            skills.append(s.get('name'))
        elif isinstance(s, str):
            skills.append(s)
            
    # Classify positioning style
    style = "מסורתי / תיאורי"
    about_lower = about.lower()
    if "what i do" in about_lower or "who we work with" in about_lower or "%" in about:
        style = "B2B מכירתי וממוקד ערך"
    elif len(about.strip()) < 80 and ("ceo" in about_lower or "founder" in about_lower):
        style = "סמכותי מינימליסטי (High Authority)"
    elif "after" in about_lower or "story" in about_lower or "journey" in about_lower or "passion" in about_lower:
        style = "סיפור אישי ורגשי (Storytelling)"
    elif "keynote" in headline.lower() or "author" in headline.lower() or "speaker" in headline.lower():
        style = "מוביל דעה ומרצה (Thought Leader)"
        
    return {
        'name': name,
        'identifier': identifier,
        'url': url,
        'headline': headline,
        'followers': followers,
        'connections': connections,
        'about': about,
        'currentPositions': current_positions,
        'topSkills': skills[:8],
        'style': style
    }

def generate_comparison_report(
    target_business_name: str,
    target_profile: Dict[str, Any],
    competitor_profiles: List[Dict[str, Any]],
    business_context: str = ""
) -> str:
    """
    Generate a comprehensive Hebrew comparison and positioning report.
    """
    date_str = datetime.now().strftime("%d-%m-%Y")
    
    lines = []
    lines.append(f"# מחקר מיצוב ומתחרים בלינקדאין — {target_business_name}")
    lines.append("")
    lines.append(f"**תאריך הפקה:** {date_str}  ")
    lines.append(f"**מקור הנתונים:** משיכה ישירה מ-Apify LinkedIn Scraper  ")
    lines.append(f"**פרופיל היעד להשוואה:** {target_profile.get('name', target_business_name)}  ")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 1. השורה התחתונה")
    lines.append("")
    
    # Generate bottom line synthesis
    target_name = target_profile.get('name', target_business_name)
    target_followers = target_profile.get('followers', 0)
    
    comp_names = [c.get('name') for c in competitor_profiles if c.get('name')]
    comp_list_str = ", ".join(comp_names) if comp_names else "המתחרים שנבדקו"
    
    lines.append(f"ניתוח המיצוב והנוכחות בלינקדאין מול {len(competitor_profiles)} מתחרים מובילים ({comp_list_str}) מצביע על נקודת פתיחה ייחודית עבור **{target_name}**.")
    lines.append(f"בעוד שחלק מהמתחרים מתבססים על מיתוג תאגידי רחב או פלטפורמות SaaS ממומנות, ישנה הזדמנות ברורה לבלוט באמצעות מיצוב אישי חד, התמקדות בפתרון בעיות מעשי בשטח, וחיבור אנושי.")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 2. טבלת השוואה מרכזית")
    lines.append("")
    
    # Header
    headers = ["מדד / פרופיל", f"★ {target_name}"] + [c.get('name', 'מתחרה') for c in competitor_profiles]
    lines.append("| " + " | ".join(headers) + " |")
    lines.append("| " + " | ".join([":---"] * len(headers)) + " |")
    
    # Row: Followers
    row_followers = ["**עוקבים**", f"{target_followers:,}"] + [f"{c.get('followers', 0):,}" for c in competitor_profiles]
    lines.append("| " + " | ".join(row_followers) + " |")
    
    # Row: Connections
    row_conn = ["**קשרים**", f"{target_profile.get('connections', 0):,}"] + [f"{c.get('connections', 0):,}" for c in competitor_profiles]
    lines.append("| " + " | ".join(row_conn) + " |")
    
    # Row: Style
    row_style = ["**סגנון מיצוב**", target_profile.get('style', '-')] + [c.get('style', '-') for c in competitor_profiles]
    lines.append("| " + " | ".join(row_style) + " |")
    
    # Row: Headline snippet
    row_headline = [
        "**כותרת (Headline)**", 
        target_profile.get('headline', '')[:50] + "..."
    ] + [c.get('headline', '')[:50] + "..." for c in competitor_profiles]
    lines.append("| " + " | ".join(row_headline) + " |")
    
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 3. פרופיל מעמיק והשראה מכל מתחרה")
    lines.append("")
    
    for i, c in enumerate(competitor_profiles, 1):
        name = c.get('name', f'מתחרה {i}')
        url = c.get('url', '')
        style = c.get('style', 'סטנדרטי')
        headline = c.get('headline', '')
        about_snippet = c.get('about', '')[:250].replace('\n', ' ')
        if len(c.get('about', '')) > 250:
            about_snippet += "..."
            
        lines.append(f"### {i}. {name}")
        if url:
            lines.append(f"* **קישור לפרופיל:** [{url}]({url})")
        lines.append(f"* **כותרת:** {headline}")
        lines.append(f"* **סגנון מיצוב עיקרי:** **{style}**")
        if about_snippet:
            lines.append(f"* **תקציר ה-About:** *\"{about_snippet}\"*")
        lines.append(f"* **מה לומדים ממנו:** המיצוב מדגים כיצד ניסוח ממוקד יוצר סמכות מול קהל היעד. כדאי לאמץ אלמנטים מהמבנה ומהבהירות של הצעת הערך שלו.")
        lines.append("")
        
    lines.append("---")
    lines.append("")
    lines.append(f"## 4. שלוש הזדמנויות תוכן ומיצוב עבור {target_name}")
    lines.append("")
    
    lines.append("### 1. חידוד הצעת הערך ב-About לפורמט פתרון בעיות (B2B Value Pitch)")
    lines.append("מומלץ לבנות את פסקת הפתיחה בפרופיל כך שתענה ישירות על השאלה: *'איזו בעיה מעשית אתה פותר ללקוח שלך ואיך זה חוסך לו זמן או כסף?'*. שימוש במבנה של 'מה אני עושה / עם מי אני עובד' מייצר המרה גבוהה משמעותית.")
    lines.append("")
    
    lines.append("### 2. שימוש בסיפור אישי וניסיון שטח מול קלישאות תוכנה (Authentic Storytelling)")
    lines.append("חברות טכנולוגיה רבות משתמשות בסיסמאות מופשטות. היתרון הגדול ביותר מולן הוא הבאת סיפורים אמיתיים מהשטח — אתגרים אמיתיים, שחיקת עובדים, והפתרונות המעשיים שיושמו. זה יוצר אמפתיה מיידית שתוכנה לבדה לא יכולה לייצר.")
    lines.append("")
    
    lines.append("### 3. הפצת מדריך סמכות או כתיבת פוסטים מבוססי ידע (Thought Leadership Asset)")
    lines.append("מתחרים מובילים מחזקים את מעמדם באמצעות הרצאות, ספרים או מאמרים בפורבס. ניתן לבסס מעמד מקביל במהירות על ידי כתיבת פוסטים שבועיים ממוקדים בלינקדאין והפצת מדריך מעשי (Playbook) שישמש כמגנט לידים איכותי.")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("*הדוח הופק אוטומטית באמצעות מערכת מחקר המתחרים — כל הזכויות שמורות לדנבר (DANBAR).*")
    
    return "\n".join(lines)
