"""
Module for discovering competitors based on business category and niche.
"""
from typing import List, Dict, Any

# Curated ecosystem database of known leaders and competitors across hospitality, travel tech, and HR
ECOSYSTEM_CATALOG: List[Dict[str, Any]] = [
    {
        "name": "Dor Krubiner",
        "company": "Mize (formerly Hotelmize)",
        "category": "Travel Tech / Revenue Optimization",
        "linkedin_url": "https://www.linkedin.com/in/dorkrubiner/",
        "description": "AI & Big Data for hotel booking profit margin optimization",
        "keywords": ["hotelmize", "mize", "travel tech", "revenue management", "hotel", "booking", "pricing", "fintech"]
    },
    {
        "name": "Amiad Soto",
        "company": "Guesty",
        "category": "Hospitality / Property Management (PMS)",
        "linkedin_url": "https://www.linkedin.com/in/amiadsoto/",
        "description": "Leading PMS and operations automation for short-term rentals and hotels",
        "keywords": ["guesty", "pms", "property management", "hospitality", "short-term rental", "vacation rental", "operations"]
    },
    {
        "name": "Itai Green",
        "company": "Innovate Israel / ITTS",
        "category": "Corporate Innovation / Travel Tech Community",
        "linkedin_url": "https://www.linkedin.com/in/itaigreen/",
        "description": "Corporate open innovation expert, keynote speaker, and founder of Israel Travel Tech Startups (ITTS)",
        "keywords": ["itts", "innovate israel", "innovation", "keynote", "open innovation", "speaker", "travel tech", "consulting"]
    },
    {
        "name": "David Mezuman",
        "company": "Duve",
        "category": "Guest Experience & Digital Hotel Operations",
        "linkedin_url": "https://www.linkedin.com/in/david-mezuman/",
        "description": "Holistic guest management, contactless check-in, upselling & communication platform",
        "keywords": ["duve", "guest experience", "hotel", "hospitality", "check-in", "upselling", "guest messaging", "smartbutler"]
    },
    {
        "name": "Luka Berger",
        "company": "Flexkeeping (Mews)",
        "category": "Hotel Operations & Housekeeping Tech",
        "linkedin_url": "https://www.linkedin.com/in/lukaberger/",
        "description": "Housekeeping and staff workflow automation platform for hospitality",
        "keywords": ["flexkeeping", "mews", "housekeeping", "staff", "operations", "hotel", "workflow", "workforce", "hr"]
    },
    {
        "name": "Eran Peretz",
        "company": "Hoteliers Tech",
        "category": "Hotel Systems Integration & Consulting",
        "linkedin_url": "https://www.linkedin.com/company/hoteliers-tech/",
        "description": "Integration and implementation of advanced technological systems for hotels",
        "keywords": ["hoteliers", "integration", "hotel tech", "pms", "hospitality systems", "hotel systems", "consulting"]
    },
    {
        "name": "Tiago Araújo",
        "company": "HiJiffy",
        "category": "Conversational AI for Hotels",
        "linkedin_url": "https://www.linkedin.com/company/hijiffy/",
        "description": "Conversational AI guest communication hub for hotels and resorts",
        "keywords": ["hijiffy", "conversational ai", "guest communication", "hotel ai", "chatbot", "guest messaging"]
    },
    {
        "name": "Justin Effron",
        "company": "ALICE (Actabl)",
        "category": "Hotel Operations Management",
        "linkedin_url": "https://www.linkedin.com/company/alice-app/",
        "description": "Hotel operations, dispatch, task management and staff collaboration platform",
        "keywords": ["alice", "actabl", "operations", "task management", "dispatch", "concierge", "guest requests"]
    }
]

def discover_competitors(business_name: str, description: str, website: str = "", limit: int = 4) -> List[Dict[str, Any]]:
    """
    Suggest relevant competitors from the ecosystem based on keyword matching and relevance.
    """
    text_corpus = f"{business_name} {description} {website}".lower()
    
    scored_candidates = []
    for item in ECOSYSTEM_CATALOG:
        score = 0
        for kw in item["keywords"]:
            if kw in text_corpus:
                score += 2
        # Company name match
        if item["company"].lower() in text_corpus:
            score += 5
            
        # Give baseline score so we can always suggest diverse peers if corpus is short
        scored_candidates.append((score, item))
        
    # Sort by score descending
    scored_candidates.sort(key=lambda x: x[0], reverse=True)
    
    # Return top matches (filtered out if it's the target business itself)
    results = []
    for _, item in scored_candidates:
        if business_name and (business_name.lower() in item["name"].lower() or business_name.lower() in item["company"].lower()):
            continue
        results.append(item)
        if len(results) >= limit:
            break
            
    return results
