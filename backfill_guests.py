"""
backfill_guests.py — Fyller inn manglende gjester for episoder i hoved-CSV.

Bruk:
  python backfill_guests.py [--dry-run]

Hva skriptet gjør:
  1. Leser AI_KI_Podcasts.csv og finner rader med tom Guest(s)-kolonne
  2. Kaller gpt-4o-mini med podcast-navn, tittel og språk
  3. Skriver gjest tilbake til CSV (kun rader som faktisk får et ikke-tomt svar)
  4. Kjører sync_html.py automatisk hvis noe ble oppdatert

Merk: RSS-beskrivelsen er ikke lagret for godkjente episoder — modellen
jobber kun på tittel og podcast-navn. Episoder uten gjest i tittelen
vil trolig forbli tomme.
"""

import csv
import json
import os
import subprocess
import sys

from openai import OpenAI

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(BASE_DIR, "AI_KI_Podcasts.csv")

SYSTEM_PROMPT = """Du er en ekspert på podkaster om kunstig intelligens.
Din oppgave er å identifisere gjesten i en podkastepisode basert på tittel og podcast-navn.

Regler:
- Søk etter mønstre som 'with [Navn]', 'w/ [Navn]', 'feat. [Navn]', '| [Navn]', '[Navn] on [emne]'
- Returner fullt navn på gjesten (kommaseparert hvis flere)
- Returner tom streng hvis ingen konkret gjest er nevnt i tittelen
- Ikke returner vertsnavn som gjest
- Ikke returner organisasjonsnavn eller produktnavn

Svar alltid med gyldig JSON, ingen annen tekst:
{"guest": "gjestenavn eller tom streng"}"""


def _call_api(client: OpenAI, podcast: str, title: str, language: str) -> str | None:
    user_msg = f"Podcast: {podcast}\nTittel: {title}\nSpråk: {language}"
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_msg},
            ],
            max_tokens=64,
        )
        text = (response.choices[0].message.content or "").strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
            text = text.strip()
        data = json.loads(text)
        return data.get("guest", "").strip()
    except Exception as e:
        print(f"  WARN API-feil: {e}")
        return None


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

    with open(CSV_PATH, encoding="utf-8", newline="") as f:
        reader = csv.reader(f)
        header = next(reader)
        rows = list(reader)

    missing = [(i, r) for i, r in enumerate(rows)
               if len(r) >= 6 and not r[5].strip()]

    print(f"Fant {len(missing)} episoder uten gjest — starter oppslag...\n")

    updated = 0
    for i, row in missing:
        podcast  = row[0]
        title    = row[1]
        language = row[2] if len(row) > 2 else "English"

        print(f"  [{row[3]}] {podcast[:25]:<25} {title[:55]}")

        guest = _call_api(client, podcast, title, language)
        if guest is None:
            print("    -> FEIL, hopper over\n")
            continue
        if not guest:
            print("    -> (ingen gjest)\n")
            continue

        # Forkast enkeltord-svar (vertsnavn som «Nathan», «Celine»)
        if all(' ' not in name.strip() for name in guest.split(',')):
            print(f"    -> forkastet (enkeltord): {guest}\n")
            continue

        # Forkast hvis gjestnavnet matcher vertsnavnet
        host_lower = row[4].lower()
        if any(part.strip() in host_lower for part in guest.lower().split(',')):
            print(f"    -> forkastet (er vert): {guest}\n")
            continue

        print(f"    -> {guest}\n")
        if not dry_run:
            rows[i][5] = guest
            updated += 1

    if dry_run:
        print(f"Dry-run: {updated} ville blitt oppdatert.")
        return

    if updated == 0:
        print("Ingen oppdateringer — CSV uendret.")
        return

    with open(CSV_PATH, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)

    print(f"\nOK {updated} episoder oppdatert med gjest.")

    sync_script = os.path.join(BASE_DIR, "sync_html.py")
    if os.path.exists(sync_script):
        print("OK Kjører sync_html.py...")
        subprocess.run([sys.executable, sync_script], check=True)


if __name__ == "__main__":
    main()
