import re

def schema_name(festival_key: str, year_val: str) -> str:
    """
    Converts festival key and year to a standardized schema name (e.g., for filenames).
    """
    return f"{festival_key.strip().lower().replace(' ', '_')}_{year_val}"


def slug(text: str) -> str:
    """
    Generates a slug from text (only lowercase letters, numbers, and hyphens).
    """
    s = re.sub(r"[^\w\s-]", "", text.strip().lower())
    s = re.sub(r"\s+", " ", s)  # Mehrere Leerzeichen zu einem
    return s.strip() or "unknown"
