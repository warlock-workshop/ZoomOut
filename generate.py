#!/usr/bin/env python3
"""Resolve image URLs + short descriptions for a curated set of famous
paintings via the Wikipedia API, then inject the data straight into
index.html (between the PAINTINGS:START / PAINTINGS:END markers).

Inlining keeps the game a single self-contained file that works no matter
how it's opened (file://, any host, the preview panel).

Re-running PRESERVES any focal / startScale tuning already in index.html,
matched by title — so you can hand-tune crops and still add paintings later.

Curated list lives below. Each row:
    (wikipedia article title, display title, artist, year, period, [aliases])
The period (art movement) is hardcoded; the description is fetched live.
"""
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request

CURATED = [
    ("Mona Lisa", "Mona Lisa", "Leonardo da Vinci", "c. 1503", "Italian Renaissance", ["la gioconda", "la joconde"]),
    ("The Starry Night", "The Starry Night", "Vincent van Gogh", "1889", "Post-Impressionism", ["starry night"]),
    ("The Scream", "The Scream", "Edvard Munch", "1893", "Expressionism", []),
    ("Girl with a Pearl Earring", "Girl with a Pearl Earring", "Johannes Vermeer", "c. 1665", "Dutch Golden Age (Baroque)", []),
    ("The Birth of Venus", "The Birth of Venus", "Sandro Botticelli", "c. 1485", "Early Renaissance", []),
    ("American Gothic", "American Gothic", "Grant Wood", "1930", "Regionalism", []),
    ("The Night Watch", "The Night Watch", "Rembrandt", "1642", "Dutch Golden Age (Baroque)", ["nightwatch"]),
    ("Las Meninas", "Las Meninas", "Diego Velázquez", "1656", "Baroque", []),
    ("The Great Wave off Kanagawa", "The Great Wave off Kanagawa", "Hokusai", "c. 1831", "Ukiyo-e (Edo period)", ["great wave"]),
    ("The Kiss (Klimt)", "The Kiss", "Gustav Klimt", "1908", "Symbolism / Art Nouveau", []),
    ("The Creation of Adam", "The Creation of Adam", "Michelangelo", "c. 1512", "High Renaissance", []),
    ("The Garden of Earthly Delights", "The Garden of Earthly Delights", "Hieronymus Bosch", "c. 1500", "Northern Renaissance", []),
    ("Sunflowers (Van Gogh series)", "Sunflowers", "Vincent van Gogh", "1888", "Post-Impressionism", []),
    ("The Last Supper (Leonardo)", "The Last Supper", "Leonardo da Vinci", "c. 1495", "High Renaissance", []),
    ("The Arnolfini Portrait", "The Arnolfini Portrait", "Jan van Eyck", "1434", "Early Netherlandish", []),
    ("A Sunday Afternoon on the Island of La Grande Jatte", "A Sunday on La Grande Jatte", "Georges Seurat", "1886", "Pointillism / Neo-Impressionism", ["la grande jatte"]),
    ("Café Terrace at Night", "Café Terrace at Night", "Vincent van Gogh", "1888", "Post-Impressionism", []),
    ("Bal du moulin de la Galette", "Bal du moulin de la Galette", "Pierre-Auguste Renoir", "1876", "Impressionism", ["moulin de la galette"]),
    ("Whistler's Mother", "Whistler's Mother", "James McNeill Whistler", "1871", "Realism / Tonalism", ["arrangement in grey and black"]),
    ("Impression, Sunrise", "Impression, Sunrise", "Claude Monet", "1872", "Impressionism", ["impression soleil levant"]),
    ("Liberty Leading the People", "Liberty Leading the People", "Eugène Delacroix", "1830", "Romanticism", []),
    ("The Raft of the Medusa", "The Raft of the Medusa", "Théodore Géricault", "1819", "Romanticism", []),
    ("Wanderer above the Sea of Fog", "Wanderer above the Sea of Fog", "Caspar David Friedrich", "1818", "Romanticism", ["wanderer above the mist"]),
    ("The Third of May 1808", "The Third of May 1808", "Francisco Goya", "1814", "Romanticism", []),
    ("Saturn Devouring His Son", "Saturn Devouring His Son", "Francisco Goya", "c. 1823", "Romanticism (Black Paintings)", []),
    ("The Fighting Temeraire", "The Fighting Temeraire", "J. M. W. Turner", "1839", "Romanticism", ["temeraire"]),
    ("A Bar at the Folies-Bergère", "A Bar at the Folies-Bergère", "Édouard Manet", "1882", "Impressionism / Realism", ["folies bergere"]),
    ("Olympia (Manet)", "Olympia", "Édouard Manet", "1863", "Realism", []),
    ("Luncheon of the Boating Party", "Luncheon of the Boating Party", "Pierre-Auguste Renoir", "1881", "Impressionism", []),
    ("The Card Players", "The Card Players", "Paul Cézanne", "c. 1892", "Post-Impressionism", []),
    ("Where Do We Come From? What Are We? Where Are We Going?", "Where Do We Come From? What Are We? Where Are We Going?", "Paul Gauguin", "1897", "Post-Impressionism", ["where do we come from"]),
    ("Wheatfield with Crows", "Wheatfield with Crows", "Vincent van Gogh", "1890", "Post-Impressionism", []),
    ("The Sleeping Gypsy", "The Sleeping Gypsy", "Henri Rousseau", "1897", "Naïve art / Primitivism", []),
    ("The Tower of Babel (Bruegel)", "The Tower of Babel", "Pieter Bruegel the Elder", "1563", "Northern Renaissance", []),
    ("The Hunters in the Snow", "The Hunters in the Snow", "Pieter Bruegel the Elder", "1565", "Northern Renaissance", ["hunters in the snow"]),
    ("The Ambassadors (Holbein)", "The Ambassadors", "Hans Holbein the Younger", "1533", "Northern Renaissance", []),
    ("Primavera (Botticelli)", "Primavera", "Sandro Botticelli", "c. 1480", "Early Renaissance", ["allegory of spring"]),
    ("The School of Athens", "The School of Athens", "Raphael", "1511", "High Renaissance", []),
    ("Sistine Madonna", "Sistine Madonna", "Raphael", "1512", "High Renaissance", ["cherubs"]),
    ("Lady with an Ermine", "Lady with an Ermine", "Leonardo da Vinci", "c. 1490", "High Renaissance", []),
    ("The Anatomy Lesson of Dr Nicolaes Tulp", "The Anatomy Lesson of Dr Nicolaes Tulp", "Rembrandt", "1632", "Dutch Golden Age (Baroque)", ["anatomy lesson"]),
    ("The Storm on the Sea of Galilee", "The Storm on the Sea of Galilee", "Rembrandt", "1633", "Dutch Golden Age (Baroque)", []),
    ("The Milkmaid (Vermeer)", "The Milkmaid", "Johannes Vermeer", "c. 1658", "Dutch Golden Age (Baroque)", []),
    ("The Swing (Fragonard)", "The Swing", "Jean-Honoré Fragonard", "1767", "Rococo", []),
    ("The Death of Marat", "The Death of Marat", "Jacques-Louis David", "1793", "Neoclassicism", []),
    ("Napoleon Crossing the Alps", "Napoleon Crossing the Alps", "Jacques-Louis David", "1801", "Neoclassicism", ["bonaparte crossing the alps"]),
    ("Grande Odalisque", "La Grande Odalisque", "Jean-Auguste-Dominique Ingres", "1814", "Neoclassicism", ["grande odalisque"]),
    ("The Gleaners", "The Gleaners", "Jean-François Millet", "1857", "Realism", []),
    ("Ophelia (painting)", "Ophelia", "John Everett Millais", "1852", "Pre-Raphaelite", []),
    ("Portrait of Adele Bloch-Bauer I", "Portrait of Adele Bloch-Bauer I", "Gustav Klimt", "1907", "Symbolism / Art Nouveau", ["woman in gold", "adele bloch-bauer"]),
]

API = "https://en.wikipedia.org/w/api.php"
HTML = "index.html"
START = "<!-- PAINTINGS:START"
END = "<!-- PAINTINGS:END -->"


UA = {"User-Agent": "Bilderkennung-game/0.1 (local prototype)"}


def api_query(params):
    """One action-API call with 429 backoff. Returns parsed JSON."""
    req = urllib.request.Request(API + "?" + urllib.parse.urlencode(params), headers=UA)
    for attempt in range(6):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt < 5:
                time.sleep(2 * (attempt + 1))
                continue
            raise


def unmap(data):
    """Map normalized/redirected page titles back to the titles we asked for."""
    norm = {n["to"]: n["from"] for n in data["query"].get("normalized", [])}
    redir = {n["to"]: n["from"] for n in data["query"].get("redirects", [])}
    return lambda t: norm.get(redir.get(t, t), redir.get(t, t))


def fetch_images(titles):
    """Return {article_title: 3500px image url} via one batched pageimages call."""
    data = api_query({
        "action": "query", "format": "json", "prop": "pageimages",
        "piprop": "thumbnail", "pithumbsize": "3500",
        "titles": "|".join(titles), "redirects": "1",
    })
    original = unmap(data)
    out = {}
    for page in data["query"]["pages"].values():
        thumb = page.get("thumbnail", {}).get("source")
        if thumb:
            out[original(page["title"])] = thumb
    return out


def trim(text, n=2):
    """Keep first n sentences. Treats a closing quote/bracket after the
    end punctuation as part of the sentence (e.g. ... world.")."""
    text = text.strip()
    ends = [m.end() for m in re.finditer(r'[.!?]["”’\')\]]*(?=\s|$)', text)]
    return text[:ends[n - 1]].strip() if len(ends) >= n else text


def fetch_extract(article, lang="en", retries=5):
    """One REST summary call per title (exlimit caps batch extracts to 1).
    Throttled + retried because the REST endpoint 429s on rapid calls."""
    url = (f"https://{lang}.wikipedia.org/api/rest_v1/page/summary/"
           + urllib.parse.quote(article.replace(" ", "_"), safe="()"))
    for attempt in range(retries):
        time.sleep(0.8)  # be polite — stay under the rate limit
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30) as r:
                return trim((json.load(r).get("extract") or "").strip())
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return ""  # no such article — retrying won't conjure one
        except Exception:
            pass  # timeout, reset connection, bad JSON — all worth another try
        # anything else is worth retrying: giving up on the first hiccup silently
        # dropped five descriptions that were there all along
        if attempt < retries - 1:
            time.sleep(1.5 * (attempt + 1))
    return ""


def load_existing_tuning(html):
    """Return {title: {'focal':..., 'startScale':...}} from current index.html."""
    m = re.search(r"window\.PAINTINGS\s*=\s*(\[.*?\]);", html, re.S)
    if not m:
        return {}
    try:
        arr = json.loads(m.group(1))
    except Exception:
        return {}
    return {p["title"]: {"focal": p.get("focal"), "startScale": p.get("startScale"),
                         "description": p.get("description", "")}
            for p in arr if "title" in p}


def main():
    with open(HTML, encoding="utf-8") as f:
        html = f.read()
    tuning = load_existing_tuning(html)

    images = fetch_images([row[0] for row in CURATED])

    paintings, missing = [], []
    for idx, (article, title, artist, year, period, aliases) in enumerate(CURATED):
        img = images.get(article)
        if not img:
            missing.append(article)
            continue
        prev = tuning.get(title, {})
        paintings.append({
            "id": idx, "title": title, "artist": artist, "year": year,
            "period": period, "aliases": aliases, "img": img,
            "description": fetch_extract(article) or prev.get("description", ""),
            "focal": prev.get("focal") or {"x": 0.5, "y": 0.5},
            "startScale": prev.get("startScale") or 12,
        })

    block = (
        f"{START} (generated by generate.py — do not edit by hand except focal/startScale) -->\n"
        f"<script>window.PAINTINGS = {json.dumps(paintings, ensure_ascii=False)};</script>\n"
        f"{END}"
    )
    # Replacement als Funktion, nicht als String: re.sub deutet sonst Escape-Sequenzen
    # darin. Ein von json.dumps sauber escaptes \n wäre wieder zu einem echten
    # Zeilenumbruch geworden — mitten in ein JS-String-Literal, und das Spiel lädt nicht mehr.
    new_html = re.sub(re.escape(START) + r".*?" + re.escape(END), lambda _: block, html, count=1, flags=re.S)
    with open(HTML, "w", encoding="utf-8") as f:
        f.write(new_html)

    kept = sum(1 for p in paintings if p["title"] in tuning)
    nodesc = [p["title"] for p in paintings if not p["description"]]
    print(f"Injected {len(paintings)} paintings into {HTML} (preserved tuning for {kept}).")
    if nodesc:
        print("No description fetched for:", ", ".join(nodesc))
    if missing:
        print("MISSING image:", ", ".join(missing))


if __name__ == "__main__":
    main()
