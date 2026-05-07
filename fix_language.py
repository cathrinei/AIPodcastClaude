"""
fix_language.py — Fikser feil språk i main_topics og rating_notes.

Bruk:
  python fix_language.py [--dry-run]

Hva skriptet gjør:
  1. Leser AI_KI_Podcasts.csv og AI_KI_Podcasts_arkiv.csv
  2. Finner engelske episoder med norsk tekst, og norske episoder med engelsk tekst
  3. Kaller gpt-4o-mini for å regenerere feltene på riktig språk
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

BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
CSV_PATH   = os.path.join(BASE_DIR, "AI_KI_Podcasts.csv")
ARKIV_PATH = os.path.join(BASE_DIR, "AI_KI_Podcasts_arkiv.csv")

# Norske ord som aldri opptrer som engelske ord (unngår «for», «at», «over» osv.)
NORWEGIAN_ONLY_RE = re.compile(
    r'\b(og|er|på|med|som|til|fra|ikke|eller|dette|ble|var|seg|sin|sitt|sine|'
    r'han|hun|vi|dem|gir|hvilke|hvilken|hvem|hva|hvor|hvorfor|hvordan|mens|samt|'
    r'uten|gjennom|rundt|blant|Diskuterer|Utforsker|analyserer|vurderer|Forklarer|'
    r'episoden|episoder|temaer|fremtiden|bruken|rollen|emner|aspekter|'
    r'siste|første|egne|viktige|sentrale)\b',
    re.IGNORECASE,
)

# Engelske ord typiske i metadata som ikke opptrer i norsk tekst
ENGLISH_ONLY_RE = re.compile(
    r'\b(episode|covers|discusses|explores|provides|presents|examines|features|'
    r'highlights|offers|introduces|focuses|addresses|delivers|shares|'
    r'insights|overview|discussion|analysis|interview|practical|'
    r'valuable|comprehensive|significant|strong|solid|excellent|'
    r'notable|remarkable|impressive|thorough|covering|discussing|'
    r'exploring|providing|presenting|examining|featuring)\b',
    re.IGNORECASE,
)

SYSTEM_PROMPT_EN = """You are a podcast metadata editor. Fix metadata for English-language AI/tech podcast episodes where main_topics or rating_notes were accidentally written in Norwegian.

Rules:
- main_topics: short comma-separated topic keywords in English
- rating_notes: 1-2 sentences in English — focus on content value; avoid phrases like "exceptional guest" or "guest-friendly"
- Keep the same factual content, just in English
- Never mix languages

Respond with valid JSON only:
{"main_topics": "...", "rating_notes": "..."}"""

SYSTEM_PROMPT_NO = """Du er en podkast-metadataeditor. Rett opp metadata for norskspråklige AI-podkast-episoder der main_topics eller rating_notes ved en feil er skrevet på engelsk.

Regler:
- main_topics: korte kommaseparerte emneord på norsk (bokmål)
- rating_notes: 1-2 setninger på norsk (bokmål) — fokuser på innholdsverdi; unngå fraser som «fremragende gjest» eller «gjestevennlig»
- Behold det faktiske innholdet, bare på norsk
- Aldri bland språk
- Bruk alltid korrekte tegn: æ, ø, å

Svar alltid med gyldig JSON:
{"main_topics": "...", "rating_notes": "..."}"""


def needs_fix_english(row: list) -> bool:
    if len(row) < 9 or row[2].strip().lower() != "english":
        return False
    return bool(NORWEGIAN_ONLY_RE.search(row[6]) or NORWEGIAN_ONLY_RE.search(row[8]))


def needs_fix_norwegian(row: list) -> bool:
    if len(row) < 9 or row[2].strip().lower() != "norwegian":
        return False
    return bool(ENGLISH_ONLY_RE.search(row[6]) or ENGLISH_ONLY_RE.search(row[8]))


def _call_api(client: OpenAI, row: list, target_lang: str) -> dict | None:
    podcast = row[0]
    title   = row[1]
    host    = row[4] if len(row) > 4 else ""
    guest   = row[5] if len(row) > 5 else ""
    topics  = row[6] if len(row) > 6 else ""
    rating  = row[7] if len(row) > 7 else ""
    notes   = row[8] if len(row) > 8 else ""

    if target_lang == "english":
        system = SYSTEM_PROMPT_EN
        user_msg = (
            f"Podcast: {podcast}\nTitle: {title}\nHost: {host}\nGuest: {guest}\n"
            f"Rating: {rating}\n"
            f"Current main_topics (fix to English): {topics}\n"
            f"Current rating_notes (fix to English): {notes}"
        )
    else:
        system = SYSTEM_PROMPT_NO
        user_msg = (
            f"Podkast: {podcast}\nTittel: {title}\nVert: {host}\nGjest: {guest}\n"
            f"Karakter: {rating}\n"
            f"Gjeldende main_topics (rett til norsk): {topics}\n"
            f"Gjeldende rating_notes (rett til norsk): {notes}"
        )

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system},
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

    to_fix = []
    for i, r in enumerate(rows):
        if needs_fix_english(r):
            to_fix.append((i, r, "english"))
        elif needs_fix_norwegian(r):
            to_fix.append((i, r, "norwegian"))

    print(f"  {os.path.basename(path)}: {len(to_fix)} episoder å fikse\n")

    updated = 0
    for i, row, target_lang in to_fix:
        direction = "→ EN" if target_lang == "english" else "→ NO"
        print(f"  {direction} [{row[3]}] {row[0][:25]:<25} {row[1][:50]}")
        print(f"    topics : {row[6][:80]}")
        print(f"    notes  : {row[8][:80]}")

        if dry_run:
            print("    -> (dry-run, hopper over)\n")
            continue

        result = _call_api(client, row, target_lang)
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
