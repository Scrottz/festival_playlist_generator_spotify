import re
from pathlib import Path

def parse_summerbreeze_lineup(html_path: str | Path) -> list[str]:
    """
    Extrahiert Bandnamen aus einer Summer Breeze Lineup-HTML-Datei.
    Erwartet das Muster: <h3 class="teaser__title">{BAND}</h3>
    """
    html_path = Path(html_path)
    if not html_path.exists():
        raise FileNotFoundError(f"Datei nicht gefunden: {html_path}")

    html = html_path.read_text(encoding="utf-8")
    bands = re.findall(r'<h3 class="teaser__title">\s*(.*?)\s*</h3>', html, re.IGNORECASE)
    return [b.strip() for b in bands if b.strip()]

def main():
    # Beispiel: Bands aus einer HTML-Datei extrahieren und ausgeben
    lineup_file = "res/lineups/summerbreeze/2026/summerbreeze_2026.html"
    bands = parse_summerbreeze_lineup(lineup_file)
    for band in bands:
        print(band)

if __name__ == "__main__":
    main()
