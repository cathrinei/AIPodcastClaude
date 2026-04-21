"""
update_podcasts.py — Henter nye podcast-episoder siden forrige oppdatering.

Bruk:
  python update_podcasts.py

Skriptet:
  1. Leser AI_KI_Podcasts_2026.csv og finner siste kjente dato per podcast.
  2. Henter RSS-feed for hver kjent podcast.
  3. Legger til nye episoder (nyere enn siste kjente dato) med Rating=0 og tomme felt.
  4. Skriver oppdatert CSV — klar til å lastes inn via HTML-knappen.
"""

import csv
import urllib.request
import urllib.error
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime
import os
import sys

# Sikre UTF-8 output i alle terminaler (Windows/Mac/Linux)
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

CSV_PATH      = os.path.join(os.path.dirname(__file__), "AI_KI_Podcasts_2026.csv")
REJECTED_PATH = os.path.join(os.path.dirname(__file__), "rejected_episodes.csv")

UNRATED = "0"  # Markør for episoder som mangler manuell vurdering
REVIEW_AFTER_DAYS = 2  # Antall dager før urangerte episoder flagges for vurdering

# Språk-override: tvinger riktig språk uavhengig av hva RSS-feedens <language>-tag sier.
# Bruk for podcaster der feeden mangler tag eller returnerer feil språkkode (f.eks. Heis).
LANGUAGE_OVERRIDE = {
    "AI-Snakk":               "Norwegian",
    "AI Forklart":            "Norwegian",
    "Shifter":                "Norwegian",
    "Heis":                   "Norwegian",
    "KI til Kaffen":          "Norwegian",
    "E24-podden":             "Norwegian",
    "HR-podden":              "Norwegian",
    "Teknologi og mennesker": "Norwegian",
}

# RSS-feeds per podcast. Legg til nye her for å utvide dekningen.
FEEDS = {
    # Engelske
    "Latent Space":                     "https://www.latent.space/feed",
    "Hard Fork (NYT)":                  "https://feeds.simplecast.com/l2i9YnTd",
    "Lex Fridman Podcast":              "https://lexfridman.com/feed/podcast/",
    "No Priors":                        "https://feeds.simplecast.com/4T39_jAj",
    "The AI Daily Brief":               "https://feeds.buzzsprout.com/2025180.rss",
    "TWIML AI Podcast":                 "https://twimlai.com/feed",
    "The Cognitive Revolution":         "https://feeds.megaphone.fm/RINTP3108857801",
    "Practical AI":                     "https://changelog.com/practicalai/feed",
    "Gradient Dissent (W&B)":           "https://feeds.captivate.fm/gradient-dissent/",
    "The Artificial Intelligence Show": "https://feeds.megaphone.fm/marketingai",
    "The AI Breakdown (Andy Dumbell)":  "https://theaibreakdown.podbean.com/feed.xml",
    "The Journal (WSJ)":                "https://video-api.wsj.com/podcast/rss/wsj/the-journal",
    "Today Explained (Vox)":            "https://feeds.megaphone.fm/VMP5705694065",
    # Norske
    "AI-Snakk":                         "https://anchor.fm/s/1057a9044/podcast/rss",
    "AI Forklart":                      "https://anchor.fm/s/10d8bff0c/podcast/rss",
    "Shifter":                          "https://feeds.acast.com/public/shows/5b1a5a6364d9356d1af279f5",
    "Heis":                             "https://feeds.acast.com/public/shows/heis-en-podcast-om-teknolgi-og-ledelse",
    "KI til Kaffen":                    "https://rss.buzzsprout.com/2489083.rss",
    "E24-podden":                       "https://podcast.stream.schibsted.media/vgtv/100414?podcast",
    "HR-podden":                        "https://rss.buzzsprout.com/1929646.rss",
    "Teknologi og mennesker":           "https://feeds.acast.com/public/shows/teknologi-av-og-for-mennesker",
    # Engelske
    "Agile Mentors Podcast":            "https://feed.podbean.com/agilementors/feed.xml",
    "Win-Win with Liv Boeree":          "https://anchor.fm/s/eefcd0ac/podcast/rss",
    "The Implement AI Podcast":         "https://feeds.acast.com/public/shows/677ed1ee3888e2bd7e3a5a54",
    "Accounting Technology Lab Podcast":"https://feeds.transistor.fm/the-accounting-technology-lab",
    "Big Take Asia (Bloomberg)":        "https://omny.fm/shows/big-take-asia/playlists/big-take-asia.rss",
}


def read_csv():
    if not os.path.exists(CSV_PATH):
        print(f"FEIL: Finner ikke {CSV_PATH}")
        sys.exit(1)
    with open(CSV_PATH, encoding="utf-8", newline="") as f:
        rows = list(csv.reader(f))
    if not rows:
        sys.exit("FEIL: CSV-filen er tom.")
    return rows[0], rows[1:]


def load_rejected():
    """Returnerer set av (podcast_name.lower(), title.lower()) som allerede er forkastet."""
    if not os.path.exists(REJECTED_PATH):
        return set()
    with open(REJECTED_PATH, encoding="utf-8", newline="") as f:
        return {(r[0].strip().lower(), r[1].strip().lower())
                for r in csv.reader(f) if len(r) >= 2}


def latest_date_per_podcast(rows):
    """Returnerer {podcast_name: datetime} med siste kjente dato per podcast."""
    latest = {}
    for row in rows:
        if len(row) < 4:
            continue
        name = row[0].strip()
        try:
            dt = datetime.strptime(row[3].strip(), "%Y-%m-%d").replace(tzinfo=timezone.utc)
        except ValueError:
            continue
        if name not in latest or dt > latest[name]:
            latest[name] = dt
    return latest


def fetch_feed(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.read(), None
    except urllib.error.HTTPError as e:
        return None, f"HTTP {e.code}"
    except urllib.error.URLError as e:
        return None, str(e.reason)


def parse_date(date_str):
    if not date_str:
        return None
    try:
        return parsedate_to_datetime(date_str).astimezone(timezone.utc)
    except Exception:
        return None


def fetch_new_episodes(podcast_name, feed_url, after_dt):
    """Returnerer (episoder, feilmelding). Episoder er None ved feil, [] hvis ingen nye."""
    raw, error = fetch_feed(feed_url)
    if raw is None:
        return None, error

    try:
        root = ET.fromstring(raw)
    except ET.ParseError as e:
        return None, f"XML-feil: {e}"

    channel = root.find("channel")
    if channel is None:
        return None, "Ugyldig RSS-format (mangler <channel>)"

    if podcast_name in LANGUAGE_OVERRIDE:
        language = LANGUAGE_OVERRIDE[podcast_name]
    else:
        lang_el = channel.find("language")
        lang_code = lang_el.text.strip().lower() if lang_el is not None else ""
        language = "Norwegian" if lang_code.startswith("no") else "English"

    new_eps = []
    for item in channel.findall("item"):
        title_el = item.find("title")
        title = title_el.text.strip() if title_el is not None else ""

        pub_el = item.find("pubDate")
        pub_dt = parse_date(pub_el.text if pub_el is not None else None)
        if pub_dt is None or pub_dt <= after_dt:
            continue

        link_el = item.find("link")
        link = link_el.text.strip() if link_el is not None and link_el.text else ""
        if not link:
            enclosure = item.find("enclosure")
            link = enclosure.attrib.get("url", "") if enclosure is not None else ""

        new_eps.append([
            podcast_name,
            title,
            language,
            pub_dt.strftime("%Y-%m-%d"),
            "",        # Host(s)
            "",        # Guest(s)
            "",        # Main Topic(s)
            UNRATED,   # Rating — krever manuell vurdering
            "Ny episode — ikke vurdert ennå",
            "",        # Tags
            link,
        ])

    new_eps.sort(key=lambda r: r[3])
    return new_eps, None


def pending_review(rows):
    """Returnerer urangerte episoder publisert for mer enn REVIEW_AFTER_DAYS siden."""
    cutoff = datetime.now(tz=timezone.utc) - timedelta(days=REVIEW_AFTER_DAYS)
    pending = []
    for row in rows:
        if len(row) < 8:
            continue
        if row[7].strip() != UNRATED:
            continue
        try:
            pub = datetime.strptime(row[3].strip(), "%Y-%m-%d").replace(tzinfo=timezone.utc)
        except ValueError:
            continue
        if pub <= cutoff:
            pending.append(row)
    return pending


def main():
    header, existing_rows = read_csv()
    latest = latest_date_per_podcast(existing_rows)
    rejected = load_rejected()
    default_from = datetime(2026, 1, 1, tzinfo=timezone.utc)

    # Bygg sett av eksisterende episoder for å unngå duplikater
    existing_keys = {(r[0].strip().lower(), r[1].strip().lower()) for r in existing_rows if len(r) >= 2}
    # Bygg sett av (podcast, dato)-par for å oppdage mulige duplikater med ulik tittel
    existing_podcast_dates = {(r[0].strip().lower(), r[3].strip()) for r in existing_rows if len(r) >= 4}

    all_new = []
    print(f"\nSjekker {len(FEEDS)} podcast-feeder...\n")

    for podcast_name, feed_url in FEEDS.items():
        after_dt = latest.get(podcast_name, default_from)
        print(f"  {podcast_name[:45]:<45} (etter {after_dt.strftime('%Y-%m-%d')}) ", end="", flush=True)

        episodes, error = fetch_new_episodes(podcast_name, feed_url, after_dt)

        if episodes is None:
            print(f"! Feil: {error}")
        elif not episodes:
            print("– ingen nye")
        else:
            filtered = [
                ep for ep in episodes
                if (ep[0].lower(), ep[1].lower()) not in rejected
                and (ep[0].lower(), ep[1].lower()) not in existing_keys
            ]
            skipped = len(episodes) - len(filtered)
            if filtered:
                print(f"+ {len(filtered)} ny(e)" + (f" ({skipped} hoppet over)" if skipped else ""))
                for ep in filtered:
                    if (ep[0].lower(), ep[3]) in existing_podcast_dates:
                        print(f"    ⚠  Mulig duplikat (samme dato finnes): [{ep[3]}] {ep[1][:55]}")
            else:
                print(f"– ingen nye ({skipped} allerede vurdert)" if skipped else "– ingen nye")
            all_new.extend(filtered)

    if not all_new:
        print("\nIngen nye episoder funnet.\n")
    else:
        with open(CSV_PATH, "w", encoding="utf-8", newline="") as f:
            csv.writer(f).writerows([header] + existing_rows + all_new)
        print(f"\n{len(all_new)} nye episode(r) lagt til i CSV.")
        print("Åpne HTML-siden og klikk 'Last inn CSV' for å laste inn oppdaterte data.")
        print(f"NB: Nye episoder har Rating={UNRATED} og må vurderes manuelt.\n")

    _, current_rows = read_csv()
    pending = pending_review(current_rows)
    if pending:
        print(f"⚠  {len(pending)} episode(r) ikke vurdert etter {REVIEW_AFTER_DAYS}+ dager:\n")
        for row in pending:
            print(f"  [{row[3]}] {row[0][:30]:<30} – {row[1][:55]}")
        print()


if __name__ == "__main__":
    main()
