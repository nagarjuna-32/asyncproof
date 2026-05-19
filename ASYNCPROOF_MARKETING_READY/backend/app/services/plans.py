PLANS = {
    "free": {
        "name": "Free",
        "price_inr": 0,
        "meetings_per_month": 3,
        "features": ["3 meetings/month", "Summary", "Action items"],
        "recording_playback": False,
        "analytics": False,
        "ai_search": False,
        "memory": False,
        "translation": False,
        "calendar": False,
        "storage_gb": 1,
    },
    "premium": {
        "name": "Premium",
        "price_inr_range": "199-499",
        "meetings_per_month": 50,
        "features": ["Full audio/video playback", "Translation", "AI search", "Meeting memory", "Productivity analytics"],
        "recording_playback": True,
        "analytics": True,
        "ai_search": True,
        "memory": True,
        "translation": True,
        "calendar": False,
        "storage_gb": 25,
    },
    "team": {
        "name": "Team",
        "price_inr_from": 999,
        "meetings_per_month": 500,
        "features": ["Admin dashboard", "Team analytics", "Calendar integration", "More storage", "Team controls"],
        "recording_playback": True,
        "analytics": True,
        "ai_search": True,
        "memory": True,
        "translation": True,
        "calendar": True,
        "storage_gb": 250,
    },
}


def normalize_plan(plan: str) -> str:
    plan = (plan or "free").lower().strip()
    return plan if plan in PLANS else "free"


def has_feature(plan: str, feature: str) -> bool:
    return bool(PLANS[normalize_plan(plan)].get(feature, False))
