import re
import os

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


def find_lineup_path(festival: str, year: str) -> str | None:
    """
    Searches for a lineup file (CSV or JSON) for the given festival and year.
    Returns the path to the first matching file, or None if not found.

    Args:
        festival (str): Festival name/key.
        year (str): Year of the festival.

    Returns:
        str | None: Path to the lineup file, or None if not found.
    """
    from conf.config import DATA_DIR

    base_dir = os.path.join(DATA_DIR, festival.lower(), str(year))
    csv_path = os.path.join(base_dir, f"{festival.lower()}_{year}.csv")
    json_path = os.path.join(base_dir, f"{festival.lower()}_{year}.json")

    if os.path.exists(csv_path):
        return csv_path
    if os.path.exists(json_path):
        return json_path

    if os.path.isdir(base_dir):
        for f in os.listdir(base_dir):
            if f.lower().endswith((".csv", ".json")):
                return os.path.join(base_dir, f)
    return None