"""Aspect keyword lists. Keyword matching is a lightweight fallback. It can miss or mismatch aspects.

No aspect extraction exists in the project (phase 1 findings), so these lists are used as-is.
"""

ASPECTS = {
    "battery life": ["battery", "battery life", "lasts", "backup"],
    "camera quality": ["camera", "photo", "photos", "picture", "pictures"],
    "performance": ["performance", "fast", "slow", "lag", "speed"],
    "sound quality": ["sound", "audio", "bass", "volume", "treble"],
    "connectivity": ["bluetooth", "wifi", "wi-fi", "connect", "connection", "pairing", "pair"],
    "comfort": ["comfort", "comfortable", "uncomfortable", "fit", "ear", "ears"],
    "durability": ["durable", "durability", "broke", "broken", "sturdy", "flimsy", "lasted"],
    "display quality": ["display", "screen", "resolution", "brightness"],
    "charging": ["charge", "charging", "charger", "charged"],
    "delivery": ["delivery", "shipping", "arrived", "shipped"],
}

CONTEXT = {
    "usage": ["gaming", "normal use", "daily", "heavy use", "video", "calls", "travel"],
    "time": ["after a week", "after a month", "months", "year", "first day"],
    "software": ["update", "version", "firmware", "software"],
    "environment": ["heat", "cold", "outdoor", "humid", "indoor"],
}
