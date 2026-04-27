"""
update_podcasts.py — Henter nye podcast-episoder siden forrige oppdatering.

Bruk:
  python update_podcasts.py

Skriptet:
  1. Leser AI_KI_Podcasts.csv og pending_episodes.csv, finner siste kjente dato per podcast.
  2. Henter RSS-feed for hver kjent podcast.
  3. Legger nye episoder (nyere enn siste kjente dato) til pending_episodes.csv — IKKE hoved-CSV.
  4. Kjør rate_episodes.py for å filtrere åpenbar ikke-AI, deretter approve_episodes.py for å godkjenne.
"""

import csv
import re
import urllib.request
import urllib.error
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

CSV_PATH     = os.path.join(os.path.dirname(__file__), "AI_KI_Podcasts.csv")
PENDING_PATH = os.path.join(os.path.dirname(__file__), "pending_episodes.csv")
REJECTED_PATH = os.path.join(os.path.dirname(__file__), "rejected_episodes.csv")

UNRATED = "0"

# Podcaster der gjest typisk er oppgitt i tittelen på formen «Tittel – Gjest»
# eller «Tittel – Gjest | Podcast». Regex forsøker å trekke ut gjest automatisk.
# Kun aktivert for podcaster der dette mønsteret er konsistent nok til å være nyttig.
GUEST_FROM_TITLE = {
    "Lex Fridman Podcast",
    "Gradient Dissent (W&B)",
    "The Cognitive Revolution",
    "No Priors",
    "TWIML AI Podcast",
    "Latent Space",
    "Hard Fork (NYT)",
}

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


def read_csv(path):
    if not os.path.exists(path):
        return None, []
    with open(path, encoding="utf-8", newline="") as f:
        rows = list(csv.reader(f))
    if not rows:
        return None, []
    return rows[0], rows[1:]


def load_rejected():
    if not os.path.exists(REJECTED_PATH):
        return set()
    with open(REJECTED_PATH, encoding="utf-8", newline="") as f:
        return {(r[0].strip().lower(), r[1].strip().lower())
                for r in csv.reader(f) if len(r) >= 2}


def latest_date_per_podcast(rows):
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


def strip_html(text):
    return re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', text)).strip()


def extract_guest_from_title(title, podcast_name):
    """
    Forsøker å trekke ut gjest fra episodetittel.
    Mønstrene er podcast-spesifikke — returnerer tom streng ved usikkerhet.
    Resultatet bør alltid verifiseres manuelt i pending_episodes.csv.
    """
    if podcast_name not in GUEST_FROM_TITLE:
        return ""

    if podcast_name == "Lex Fridman Podcast":
        # Mønster A: «#NNN – Gjest: Emne» — gjest er 2-4 ord rett etter episodenummer
        m = re.match(r'^#\d+\s*[–-]\s*(.+?):', title)
        if m:
            candidate = m.group(1).strip()
            words = candidate.split()
            if 2 <= len(words) <= 4 and all(w[0].isupper() for w in words):
                return candidate
        # Mønster B: «#NNN – Emne – Gjest» — gjest er siste segment
        parts = re.split(r'\s[–-]\s', title)
        if len(parts) >= 3:
            candidate = parts[-1].strip()
            if len(candidate) > 3 and not re.match(r'^#?\d+', candidate):
                return candidate

    elif podcast_name == "TWIML AI Podcast":
        # Mønster: «Emne with Gjest - #NNN»
        m = re.search(r'\bwith\s+(.+?)(?:\s+-\s+#\d+|$)', title)
        if m:
            candidate = m.group(1).strip()
            if len(candidate) > 3 and not re.match(r'^#?\d+', candidate):
                return candidate

    elif podcast_name == "The Cognitive Revolution":
        # Mønster A: «Emne, with Gjest» (komma + "with" som eget ord)
        m = re.search(r',\s*with\s+(.+?)(?:,|$)', title, re.IGNORECASE)
        if m:
            candidate = m.group(1).strip()
            if len(candidate) > 3:
                return candidate
        # Mønster B: «w/ Gjest»
        m = re.search(r'\bw/\s*(.+?)(?:,|$)', title)
        if m:
            candidate = m.group(1).strip()
            if len(candidate) > 3:
                return candidate
        # Mønster C: «Emne? Gjest on topic» — stort navn etter spørsmålstegn
        m = re.search(r'[?!]\s+([A-Z][a-z]+(?: [A-Z][a-z]+)+) on \b', title)
        if m:
            candidate = m.group(1).strip()
            if len(candidate) > 3:
                return candidate

    elif podcast_name == "No Priors":
        # Mønster: «Gjest on Emne» — tittelen starter med gjestens navn
        # (mange No Priors-episoder har ikke gjest i tittelen — fanges ikke opp)
        m = re.match(r'^([A-Z][a-z]+(?: [A-Z][a-z]+)+) on \b', title)
        if m:
            candidate = m.group(1).strip()
            if len(candidate) > 3:
                return candidate

    elif podcast_name == "Gradient Dissent (W&B)":
        # Mønster: «Emne | Gjest» — siste segment etter ' | '
        if ' | ' in title:
            candidate = title.rsplit(' | ', 1)[-1].strip()
            if len(candidate) > 3:
                return candidate

    elif podcast_name == "Latent Space":
        # Mønster A: «Emne — with Gjest, Tittel» (eksplisitt "with")
        m = re.search(r'\s[—–]\s+with\s+(.+?)$', title)
        if m:
            candidate = m.group(1).strip()
            if len(candidate) > 3:
                return candidate
        # Mønster B: «Emne — Gjest (Selskap)» eller «Emne — Gjest & Gjest, Selskap»
        # Bruker em/en-strek som separator; [AINews]-titler bruker aldri denne.
        m = re.search(r'\s[—–]\s+(?!with\s)(.+?)$', title)
        if m:
            candidate = m.group(1).strip()
            words = candidate.split()
            # Må se ut som navn: 1–6 ord, starter med stor bokstav, ikke bare akronymer
            if (1 <= len(words) <= 6
                    and len(candidate) < 60
                    and candidate[0].isupper()
                    and not re.match(r'^[A-Z]{2,}\b', candidate)):
                return candidate

    elif podcast_name == "Hard Fork (NYT)":
        # Mønster: «Emne With Gjest + ...» — stor W indikerer gjest, ikke "with" i setning
        m = re.search(r'\bWith\s+(.+?)(?:\s+\+|$)', title)
        if m:
            candidate = m.group(1).strip()
            if len(candidate) > 3:
                return candidate

    return ""


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

        desc_el = item.find("description")
        desc_raw = desc_el.text if desc_el is not None and desc_el.text else ""
        description = strip_html(desc_raw)[:600]

        guest = extract_guest_from_title(title, podcast_name)

        new_eps.append([
            podcast_name,
            title,
            language,
            pub_dt.strftime("%Y-%m-%d"),
            "",        # Host(s) — fylles manuelt (kan variere per episode)
            guest,     # Guest(s) — forsøkt utledet fra tittel, verifiser manuelt
            "",        # Main Topic(s)
            UNRATED,   # Rating
            "",        # Rating Notes
            "",        # Tags
            link,
            description,  # col 11 — kun i pending, fjernes ved approve
        ])

    new_eps.sort(key=lambda r: r[3])
    return new_eps, None


def is_gha():
    """Er vi i GitHub Actions?"""
    return os.environ.get("GITHUB_ACTIONS") == "true"


def gha_group(title):
    if is_gha():
        print(f"::group::{title}", flush=True)


def gha_endgroup():
    if is_gha():
        print("::endgroup::", flush=True)


def gha_notice(msg):
    if is_gha():
        print(f"::notice::{msg}", flush=True)


def gha_warning(msg):
    if is_gha():
        print(f"::warning::{msg}", flush=True)


def gha_error(msg):
    if is_gha():
        print(f"::error::{msg}", flush=True)


def main():
    main_header, main_rows = read_csv(CSV_PATH)
    if main_header is None:
        sys.exit(f"FEIL: Finner ikke {CSV_PATH}")

    pending_header, pending_rows = read_csv(PENDING_PATH)

    # Kombiner hoved + pending for duplikatsjekk og siste dato
    all_known_rows = main_rows + pending_rows
    latest = latest_date_per_podcast(all_known_rows)
    rejected = load_rejected()
    default_from = datetime(2026, 1, 1, tzinfo=timezone.utc)

    existing_keys = {(r[0].strip().lower(), r[1].strip().lower()) for r in all_known_rows if len(r) >= 2}
    existing_podcast_dates = {(r[0].strip().lower(), r[3].strip()) for r in all_known_rows if len(r) >= 4}

    all_new = []
    feeds_with_errors = []
    feeds_with_new = []

    gha_group(f"Sjekker {len(FEEDS)} podcast-feeder")
    print(f"\nSjekker {len(FEEDS)} podcast-feeder...\n")

    for podcast_name, feed_url in FEEDS.items():
        after_dt = latest.get(podcast_name, default_from)
        print(f"  {podcast_name[:45]:<45} (etter {after_dt.strftime('%Y-%m-%d')}) ", end="", flush=True)

        episodes, error = fetch_new_episodes(podcast_name, feed_url, after_dt)

        if episodes is None:
            print(f"! Feil: {error}")
            feeds_with_errors.append((podcast_name, error))
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
                        gha_warning(f"Mulig duplikat ({podcast_name}): [{ep[3]}] {ep[1][:80]}")
                feeds_with_new.append((podcast_name, filtered))
            else:
                print(f"– ingen nye ({skipped} allerede vurdert)" if skipped else "– ingen nye")
            all_new.extend(filtered)

    print()
    gha_endgroup()

    # Oppsummering av nye episoder
    if feeds_with_new:
        gha_group(f"Nye episoder ({len(all_new)} stk)")
        for podcast_name, eps in feeds_with_new:
            print(f"\n  📻 {podcast_name} — {len(eps)} ny(e):")
            for ep in eps:
                print(f"     [{ep[3]}] {ep[1][:80]}")
        print()
        gha_endgroup()

    # Feil-oppsummering
    if feeds_with_errors:
        gha_group(f"Feil ved henting ({len(feeds_with_errors)} feeder)")
        for podcast_name, error in feeds_with_errors:
            print(f"  ✗ {podcast_name}: {error}")
            gha_error(f"{podcast_name}: {error}")
        print()
        gha_endgroup()

    # Sluttresultat
    if not all_new:
        print("Ingen nye episoder funnet.\n")
        gha_notice("Ingen nye episoder funnet.")
    else:
        new_pending_header = main_header + ["Description"]
        combined_pending = pending_rows + all_new
        with open(PENDING_PATH, "w", encoding="utf-8", newline="") as f:
            csv.writer(f).writerows([new_pending_header] + combined_pending)
        summary = f"{len(all_new)} ny(e) episode(r) lagt til i pending_episodes.csv"
        print(f"{summary}.")
        print("Kjør: python rate_episodes.py   (filtrerer åpenbar ikke-AI)")
        print("Sett rating manuelt i pending_episodes.csv, kjør deretter:")
        print("      python approve_episodes.py  (flytter godkjente til hoved-CSV)\n")
        gha_notice(summary + " — klar for gjennomgang.")


if __name__ == "__main__":
    main()
