#!/usr/bin/env python3
"""Resolve image URLs + short descriptions for a curated set of famous
paintings via the Wikipedia API, then inject the data straight into
index.html (between the PAINTINGS:START / PAINTINGS:END markers).

Inlining keeps the game a single self-contained file that works no matter
how it's opened (file://, any host, the preview panel).

Re-running PRESERVES any focal / startScale tuning already in index.html,
matched by title — so you can hand-tune crops and still add paintings later.

Curated list lives below. Each row:
    (en article, de article, display title, artist, year, period, [aliases])

Two articles per painting, on purpose: the image comes from the English
article (its pageimage is reliably the painting itself), the description from
the German one. Four paintings have no German article of their own — they only
appear inside survey articles — and carry None; those ship without a
description rather than with an invented or English one.

Titles, artists and periods are hardcoded in German. Aliases are the search
crutch, never displayed: English titles stay in so "The Scream" still finds
"Der Schrei".
"""
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request

CURATED = [
    ("Mona Lisa", "Mona Lisa", "Mona Lisa", "Leonardo da Vinci", "um 1503", "Italienische Renaissance", ["la gioconda", "la joconde"]),
    ("The Starry Night", "Sternennacht", "Sternennacht", "Vincent van Gogh", "1889", "Postimpressionismus", ["the starry night", "starry night", "sternenhimmel"]),
    ("The Scream", "Der Schrei", "Der Schrei", "Edvard Munch", "1893", "Expressionismus", ["the scream", "skrik"]),
    ("Girl with a Pearl Earring", "Das Mädchen mit dem Perlenohrring", "Das Mädchen mit dem Perlenohrring", "Johannes Vermeer", "um 1665", "Goldenes Zeitalter (Barock)", ["girl with a pearl earring", "perlenohrgehänge"]),
    ("The Birth of Venus", "Die Geburt der Venus (Botticelli)", "Die Geburt der Venus", "Sandro Botticelli", "um 1485", "Frührenaissance", ["the birth of venus", "nascita di venere"]),
    ("American Gothic", "American Gothic", "American Gothic", "Grant Wood", "1930", "Regionalismus", []),
    ("The Night Watch", "Die Nachtwache", "Die Nachtwache", "Rembrandt", "1642", "Goldenes Zeitalter (Barock)", ["the night watch", "nightwatch", "nachtwacht"]),
    ("Las Meninas", "Las Meninas", "Las Meninas", "Diego Velázquez", "1656", "Barock", ["die hoffräulein"]),
    ("The Great Wave off Kanagawa", "Die große Welle vor Kanagawa", "Die große Welle vor Kanagawa", "Hokusai", "um 1831", "Ukiyo-e (Edo-Zeit)", ["the great wave", "great wave", "kanagawa"]),
    ("The Kiss (Klimt)", "Der Kuss (Klimt)", "Der Kuss", "Gustav Klimt", "1908", "Symbolismus / Jugendstil", ["the kiss"]),
    ("The Creation of Adam", "Die Erschaffung Adams", "Die Erschaffung Adams", "Michelangelo", "um 1512", "Hochrenaissance", ["the creation of adam"]),
    ("The Garden of Earthly Delights", "Der Garten der Lüste (Bosch)", "Der Garten der Lüste", "Hieronymus Bosch", "um 1500", "Nordische Renaissance", ["the garden of earthly delights"]),
    ("Sunflowers (Van Gogh series)", "Sonnenblumen (van Gogh)", "Sonnenblumen", "Vincent van Gogh", "1888", "Postimpressionismus", ["sunflowers"]),
    ("The Last Supper (Leonardo)", "Das Abendmahl (Leonardo da Vinci)", "Das Abendmahl", "Leonardo da Vinci", "um 1495", "Hochrenaissance", ["the last supper", "letztes abendmahl", "cenacolo"]),
    ("The Arnolfini Portrait", "Arnolfini-Hochzeit", "Arnolfini-Hochzeit", "Jan van Eyck", "1434", "Altniederländische Malerei", ["the arnolfini portrait", "arnolfini"]),
    ("A Sunday Afternoon on the Island of La Grande Jatte", "Ein Sonntagnachmittag auf der Insel La Grande Jatte", "Ein Sonntagnachmittag auf La Grande Jatte", "Georges Seurat", "1886", "Pointillismus / Neoimpressionismus", ["la grande jatte", "a sunday afternoon"]),
    ("Café Terrace at Night", "Caféterrasse am Abend", "Caféterrasse am Abend", "Vincent van Gogh", "1888", "Postimpressionismus", ["café terrace at night"]),
    ("Bal du moulin de la Galette", "Bal du moulin de la Galette", "Bal du moulin de la Galette", "Pierre-Auguste Renoir", "1876", "Impressionismus", ["moulin de la galette", "tanz im moulin de la galette"]),
    ("Whistler's Mother", "Arrangement in Grau und Schwarz: Porträt der Mutter des Künstlers", "Whistlers Mutter", "James McNeill Whistler", "1871", "Realismus / Tonalismus", ["whistler's mother", "arrangement in grau und schwarz", "arrangement in grey and black"]),
    ("Impression, Sunrise", "Impression, Sonnenaufgang", "Impression, Sonnenaufgang", "Claude Monet", "1872", "Impressionismus", ["impression sunrise", "impression soleil levant"]),
    ("Liberty Leading the People", "Die Freiheit führt das Volk", "Die Freiheit führt das Volk", "Eugène Delacroix", "1830", "Romantik", ["liberty leading the people", "la liberté guidant le peuple"]),
    ("The Raft of the Medusa", "Das Floß der Medusa", "Das Floß der Medusa", "Théodore Géricault", "1819", "Romantik", ["the raft of the medusa", "le radeau de la méduse"]),
    ("Wanderer above the Sea of Fog", "Der Wanderer über dem Nebelmeer", "Der Wanderer über dem Nebelmeer", "Caspar David Friedrich", "1818", "Romantik", ["wanderer above the sea of fog", "nebelmeer"]),
    ("The Third of May 1808", "Die Erschießung der Aufständischen", "Die Erschießung der Aufständischen", "Francisco Goya", "1814", "Romantik", ["the third of may 1808", "el tres de mayo", "der 3. mai 1808"]),
    ("Saturn Devouring His Son", None, "Saturn verschlingt seinen Sohn", "Francisco Goya", "um 1823", "Romantik (Schwarze Gemälde)", ["saturn devouring his son", "saturno"]),
    ("The Fighting Temeraire", "The Fighting Temeraire", "The Fighting Temeraire", "J. M. W. Turner", "1839", "Romantik", ["temeraire", "die letzte fahrt der temeraire"]),
    ("A Bar at the Folies-Bergère", "Bar in den Folies Bergère", "Bar in den Folies-Bergère", "Édouard Manet", "1882", "Impressionismus / Realismus", ["a bar at the folies-bergère", "folies bergere"]),
    ("Olympia (Manet)", "Olympia (Gemälde)", "Olympia", "Édouard Manet", "1863", "Realismus", []),
    ("Luncheon of the Boating Party", "Das Frühstück der Ruderer", "Das Frühstück der Ruderer", "Pierre-Auguste Renoir", "1881", "Impressionismus", ["luncheon of the boating party"]),
    ("The Card Players", "Die Kartenspieler", "Die Kartenspieler", "Paul Cézanne", "um 1892", "Postimpressionismus", ["the card players", "les joueurs de cartes"]),
    ("Where Do We Come From? What Are We? Where Are We Going?", "Woher kommen wir? Wer sind wir? Wohin gehen wir?", "Woher kommen wir? Wer sind wir? Wohin gehen wir?", "Paul Gauguin", "1897", "Postimpressionismus", ["where do we come from", "woher kommen wir"]),
    ("Wheatfield with Crows", None, "Weizenfeld mit Krähen", "Vincent van Gogh", "1890", "Postimpressionismus", ["wheatfield with crows", "kornfeld mit krähen"]),
    ("The Sleeping Gypsy", "Die schlafende Zigeunerin", "Die schlafende Zigeunerin", "Henri Rousseau", "1897", "Naive Kunst / Primitivismus", ["the sleeping gypsy", "la bohémienne endormie"]),
    ("The Tower of Babel (Bruegel)", "Turmbau zu Babel (Bruegel)", "Turmbau zu Babel", "Pieter Bruegel d. Ä.", "1563", "Nordische Renaissance", ["the tower of babel", "tower of babel"]),
    ("The Hunters in the Snow", "Die Jäger im Schnee", "Die Jäger im Schnee", "Pieter Bruegel d. Ä.", "1565", "Nordische Renaissance", ["the hunters in the snow", "hunters in the snow"]),
    ("The Ambassadors (Holbein)", "Die Gesandten", "Die Gesandten", "Hans Holbein d. J.", "1533", "Nordische Renaissance", ["the ambassadors"]),
    ("Primavera (Botticelli)", "Primavera (Botticelli)", "Primavera", "Sandro Botticelli", "um 1480", "Frührenaissance", ["allegory of spring", "der frühling"]),
    ("The School of Athens", "Die Schule von Athen", "Die Schule von Athen", "Raffael", "1511", "Hochrenaissance", ["the school of athens", "scuola di atene"]),
    ("Sistine Madonna", "Sixtinische Madonna", "Sixtinische Madonna", "Raffael", "1512", "Hochrenaissance", ["sistine madonna", "cherubs", "engel"]),
    ("Lady with an Ermine", "Dame mit dem Hermelin", "Dame mit dem Hermelin", "Leonardo da Vinci", "um 1490", "Hochrenaissance", ["lady with an ermine"]),
    ("The Anatomy Lesson of Dr Nicolaes Tulp", "Die Anatomie des Dr. Tulp", "Die Anatomie des Dr. Tulp", "Rembrandt", "1632", "Goldenes Zeitalter (Barock)", ["the anatomy lesson", "anatomy lesson", "anatomiestunde"]),
    ("The Storm on the Sea of Galilee", "Christus im Sturm auf dem See Genezareth (Rembrandt)", "Christus im Sturm auf dem See Genezareth", "Rembrandt", "1633", "Goldenes Zeitalter (Barock)", ["the storm on the sea of galilee"]),
    ("The Milkmaid (Vermeer)", "Dienstmagd mit Milchkrug", "Dienstmagd mit Milchkrug", "Johannes Vermeer", "um 1658", "Goldenes Zeitalter (Barock)", ["the milkmaid", "das milchmädchen", "milchmagd"]),
    ("The Swing (Fragonard)", "Die Schaukel (Fragonard)", "Die Schaukel", "Jean-Honoré Fragonard", "1767", "Rokoko", ["the swing", "escarpolette"]),
    ("The Death of Marat", "Der Tod des Marat", "Der Tod des Marat", "Jacques-Louis David", "1793", "Klassizismus", ["the death of marat", "la mort de marat"]),
    ("Napoleon Crossing the Alps", "Bonaparte beim Überschreiten der Alpen am Großen Sankt Bernhard", "Napoleon beim Überschreiten der Alpen", "Jacques-Louis David", "1801", "Klassizismus", ["napoleon crossing the alps", "bonaparte crossing the alps"]),
    ("Grande Odalisque", None, "Die große Odaliske", "Jean-Auguste-Dominique Ingres", "1814", "Klassizismus", ["grande odalisque", "la grande odalisque"]),
    ("The Gleaners", None, "Die Ährenleserinnen", "Jean-François Millet", "1857", "Realismus", ["the gleaners", "des glaneuses"]),
    # nicht auf "Ophelia (painting)" ändern: leitet auf eine Begriffsklärung um, deren
    # deutscher Sprachlink ebenfalls eine Begriffsklärung ist (nicht das Gemälde)
    ("Ophelia (Millais)", "Ophelia (Millais)", "Ophelia", "John Everett Millais", "1852", "Präraffaeliten", ["ophelia"]),
    ("Portrait of Adele Bloch-Bauer I", "Adele Bloch-Bauer I", "Adele Bloch-Bauer I", "Gustav Klimt", "1907", "Symbolismus / Jugendstil", ["woman in gold", "die goldene adele", "adele bloch-bauer"]),
]

# Für die vier Gemälde ohne eigenen deutschen Wikipedia-Artikel: Übersetzungen der
# englischen Zusammenfassung, von Hand eingetragen (Stand Juli 2026). Fest im Skript
# statt zur Laufzeit übersetzt — das Spiel soll offline und ohne Dienste auskommen.
# Quelle bleibt die Wikipedia (CC BY-SA), die Übersetzung ist eine Bearbeitung davon.
DESC_DE = {
    "Saturn verschlingt seinen Sohn":
        "Saturn verschlingt seinen Sohn ist ein Gemälde des spanischen Künstlers Francisco "
        "Goya. Das Werk gehört zu den 14 sogenannten Schwarzen Gemälden, die Goya zwischen "
        "1820 und 1823 direkt auf die Wände seines Hauses malte.",
    "Weizenfeld mit Krähen":
        "Weizenfeld mit Krähen ist ein Gemälde von Vincent van Gogh aus dem Juli 1890. "
        "Mehrere Kritiker zählen es zu seinen größten Werken.",
    "Die große Odaliske":
        "Die große Odaliske, auch Une Odalisque oder La Grande Odalisque, ist ein Ölgemälde "
        "von Jean-Auguste-Dominique Ingres aus dem Jahr 1814. Es zeigt eine Odaliske, eine "
        "Haremsdame. Für Ingres’ Zeitgenossen markierte das Werk seinen Bruch mit dem "
        "Klassizismus und die Hinwendung zu einer exotischen Romantik.",
    "Die Ährenleserinnen":
        "Die Ährenleserinnen ist ein Ölgemälde von Jean-François Millet, das er 1857 "
        "vollendete. Es hängt im Musée d’Orsay in Paris.",
}

API = "https://en.wikipedia.org/w/api.php"
HTML = "index.html"
START = "<!-- PAINTINGS:START"
END = "<!-- PAINTINGS:END -->"


UA = {"User-Agent": "ZoomOut-game/0.1 (local prototype)"}


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


def trim(text, max_chars=300, min_chars=160):
    """Cut to a blurb that fits the reveal card: whole sentences, roughly
    min_chars..max_chars. Treats a closing quote/bracket after the end
    punctuation as part of the sentence (e.g. ... world.").

    Sentence COUNT is the wrong measure here. German Wikipedia opens with
    subordinate-clause monsters where the English one is brisk — "The Night
    Watch" leads with a single 347-character sentence — and a title full of
    question marks ("Woher kommen wir? Wer sind wir?") reads as three sentences,
    which once cut the blurb off mid-title. So: collect sentences until there's
    enough, stop before it gets too long, and hard-wrap on a word boundary if
    even the first sentence blows the budget.
    """
    text = " ".join(text.split())  # newlines out — they have no business in a one-line blurb
    ends = [m.end() for m in re.finditer(r'[.!?]["”’\')\]]*(?=\s|$)', text)]
    keep = None
    for e in ends:
        if e > max_chars:
            break
        keep = e
        if e >= min_chars:
            break
    if keep is None:
        return text[:max_chars].rsplit(" ", 1)[0].rstrip(" ,;:") + " …"
    return text[:keep].strip()


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
    for idx, (en_article, de_article, title, artist, year, period, aliases) in enumerate(CURATED):
        img = images.get(en_article)
        if not img:
            missing.append(en_article)
            continue
        prev = tuning.get(title, {})
        # German article if there is one, otherwise the hand-written translation
        desc = fetch_extract(de_article, lang="de") if de_article else DESC_DE.get(title, "")
        paintings.append({
            "id": idx, "title": title, "artist": artist, "year": year,
            "period": period, "aliases": aliases, "img": img,
            "description": desc or prev.get("description", ""),
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
