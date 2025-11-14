import os

def get_emblem_path(tier: str) -> str:
    """
    Returns the absolute path to the emblem for the given tier.
    Assumes files are lowercase and .webp
    """
    tier = tier.lower()  # e.g., 'platinum' -> 'platinum.webp'
    base = os.path.join(os.path.dirname(__file__), "..", "assets", "ranked_emblems")
    return os.path.abspath(os.path.join(base, f"{tier}.webp"))