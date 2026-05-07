"""
fix_language.py — Fikser norsk tekst i main_topics og rating_notes for engelske episoder.

Bruk:
  python fix_language.py [--dry-run]

Hva skriptet gjør:
  1. Leser AI_KI_Podcasts.csv og AI_KI_Podcasts_arkiv.csv
  2. Finner engelske episoder der main_topics eller rating_notes inneholder norske ord
  3. Kaller gpt-4o-mini for å regenerere de aktuelle feltene på engelsk
  4. Skriver endringer tilbake til CSV
  5. Kjører sync_html.py automatisk hvis hoved-CSV ble endret
"""

import csv
import json
import os
import re
import subprocess
import sys

from openai import OpenAI

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE_DIR  = os.path.dirname(os.path.abspath(__file__))
CSV_PATH  = os.path.join(BASE_DIR, "AI_KI_Podcasts.csv")
ARKIV_PATH = os.path.join(BASE_DIR, "AI_KI_Podcasts_arkiv.csv")

NORWEGIAN_RE = re.compile(
    r'\b(og|er|det|en|av|på|med|som|til|fra|om|at|for|kan|har|ikke|eller|dette|ble|var|'
    r'men|seg|han|hun|vi|de|dem|tar|opp|ser|gir|sin|sitt|sine|hvilke|hvilken|hvem|hva|'
    r'hvor|hvorfor|hvordan|mens|samt|bare|uten|over|mot|under|gjennom|rundt|etter|blant|'
    r'når|inn|Diskuterer|Utforsker|analyserer|vurderer|Forklarer|Gir|Tar|Har|Ser|'
    r'episoden|episoder|temaer|fremtiden|bruken|rollen|delen|emner|aspekter|'
    r'siste|første|egne|nye|store|viktige|sentrale|tekniske)\b',
    re.IGNORECASE,
)

SYSTEM_PROMPT = """You are a podcast metadata editor. Your task is to correct metadata for English-language AI/tech podcast episodes.

The fields main_topics and rating_notes were accidentally written in Norwegian instead of English.
Regenerate them in English based on the episode information provided.

Rules:
- main_topics: short comma-separated topic keywords, all in English
- rating_notes: 1-2 sentences in English explaining the rating — focus on content (what is covered, what value it has); avoid phrases like "exceptional guest" or "guest-friendly"
- Keep the same factual content as the original Norwegian text, just translate/rewrite in English
- Never mix languages within a field

Respond with valid JSON only, no other text:
{"main_topics": "...", "rating_notes": "..."}"""


def has_norwegian(text: str) -> bool:
    return bool(NORWEGIAN_RE.search(text))


def needs_fix(row: list) -> bool:
    if len(row) < 9:
        return False
    language = row[2].strip().lower()
    if language != "english":
        return False
    topics = row[6].strip()
    notes  = row[8].strip()
    return has_norwegian(topics) or has_norwegian(notes)


def _call_api(client: OpenAI, row: list) -> dict | None:
    podcast  = row[0]
    title    = row[1]
    host     = row[4] if len(row) > 4 else ""
    guest    = row[5] if len(row) > 5 else ""
    topics   = row[6] if len(row) > 6 else ""
    rating   = row[7] if len(row) > 7 else ""
    notes    = row[8] if len(row) > 8 else ""

    user_msg = (
        f"Podcast: {podcast}\n"
        f"Title: {title}\n"
        f"Host: {host}\n"
        f"Guest: {guest}\n"
        f"Rating: {rating}\n"
        f"Current main_topics (Norwegian — fix to English): {topics}\n"
        f"Current rating_notes (Norwegian — fix to English): {notes}"
    )
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": user_msg},
            ],
            max_tokens=256,
        )
        text = (response.choices[0].message.content or "").strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
            text = text.strip()
        return json.loads(text)
    except json.JSONDecodeError as e:
        print(f"  WARN JSON-feil: {e}")
        return None
    except Exception as e:
        print(f"  WARN API-feil: {e}")
        return None


def fix_csv(client: OpenAI, path: str, dry_run: bool) -> int:
    if not os.path.exists(path):
        print(f"  (ikke funnet: {path})")
        return 0

    with open(path, encoding="utf-8", newline="") as f:
        reader = csv.reader(f)
        header = next(reader)
        rows   = list(reader)

    to_fix = [(i, r) for i, r in enumerate(rows) if needs_fix(r)]
    print(f"  {os.path.basename(path)}: {len(to_fix)} episoder å fikse\n")

    updated = 0
    for i, row in to_fix:
        print(f"  [{row[3]}] {row[0][:25]:<25} {row[1][:55]}")
        print(f"    topics : {row[6][:80]}")
        print(f"    notes  : {row[8][:80]}")

        if dry_run:
            print("    -> (dry-run, hopper over)\n")
            continue

        result = _call_api(client, row)
        if result is None:
            print("    -> FEIL, hopper over\n")
            continue

        new_topics = result.get("main_topics", "").strip()
        new_notes  = result.get("rating_notes", "").strip()

        if not new_topics or not new_notes:
            print("    -> tomt svar, hopper over\n")
            continue

        print(f"    -> topics : {new_topics[:80]}")
        print(f"    -> notes  : {new_notes[:80]}\n")

        rows[i][6] = new_topics
        rows[i][8] = new_notes
        updated += 1

    if not dry_run and updated > 0:
        with open(path, "w", encoding="utf-8", newline="") as f:
            w = csv.writer(f)
            w.writerow(header)
            w.writerows(rows)
        print(f"  OK {updated} episoder oppdatert i {os.path.basename(path)}\n")

    return updated


def main() -> None:
    dry_run = "--dry-run" in sys.argv

    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        print("FEIL: Miljøvariabel GITHUB_TOKEN er ikke satt.")
        sys.exit(1)

    client = OpenAI(
        base_url="https://models.inference.ai.azure.com",
        api_key=token,
    )

    print("=== Hoved-CSV ===")
    main_updated = fix_csv(client, CSV_PATH, dry_run)

    print("=== Arkiv-CSV ===")
    arkiv_updated = fix_csv(client, ARKIV_PATH, dry_run)

    if dry_run:
        print("Dry-run fullført — ingen filer endret.")
        return

    if main_updated > 0:
        sync_script = os.path.join(BASE_DIR, "sync_html.py")
        if os.path.exists(sync_script):
            print("OK Kjører sync_html.py...")
            subprocess.run([sys.executable, sync_script], check=True)

    total = main_updated + arkiv_updated
    print(f"\nOK Totalt {total} episoder korrigert ({main_updated} hoved + {arkiv_updated} arkiv)")


if __name__ == "__main__":
    main()
