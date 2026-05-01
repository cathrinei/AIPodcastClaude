"""
archive_episodes.py — Arkiverer episoder eldre enn 4 måneder.

Bruk:
  python archive_episodes.py

Hva skriptet gjør:
  1. Beregner cutoff = date.today() minus 4 måneder (rullerende daglig)
  2. Leser AI_KI_Podcasts.csv og skiller ut episoder der Published Date < cutoff
  3. Arkiverte episoder flyttes til AI_KI_Podcasts_arkiv.csv (deduplicert)
  4. AI_KI_Podcasts.csv overskrives med gjenværende episoder
  5. Kjører sync_html.py automatisk hvis episoder ble arkivert
"""

import csv
import os
import subprocess
import sys
from datetime import date

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE_DIR      = os.path.dirname(os.path.abspath(__file__))
CSV_PATH      = os.path.join(BASE_DIR, "AI_KI_Podcasts.csv")
ARCHIVE_PATH  = os.path.join(BASE_DIR, "AI_KI_Podcasts_arkiv.csv")


def archive_cutoff() -> str:
    today = date.today()
    month = today.month - 4
    year = today.year
    if month <= 0:
        month += 12
        year -= 1
    return date(year, month, today.day).isoformat()


def load_archive_keys() -> set[tuple[str, str]]:
    if not os.path.exists(ARCHIVE_PATH):
        return set()
    keys: set[tuple[str, str]] = set()
    with open(ARCHIVE_PATH, encoding="utf-8", newline="") as f:
        reader = csv.reader(f)
        next(reader, None)  # skip header
        for row in reader:
            if len(row) >= 2:
                keys.add((row[0].strip().lower(), row[1].strip().lower()))
    return keys


def append_to_archive(rows: list[list[str]], header: list[str]) -> None:
    existing_keys = load_archive_keys()
    new_rows = [r for r in rows
                if (r[0].strip().lower(), r[1].strip().lower()) not in existing_keys]
    if not new_rows:
        return

    write_header = not os.path.exists(ARCHIVE_PATH) or os.path.getsize(ARCHIVE_PATH) == 0
    with open(ARCHIVE_PATH, "a", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        if write_header:
            w.writerow(header)
        for row in new_rows:
            w.writerow(row)


def main() -> None:
    if not os.path.exists(CSV_PATH):
        print("OK AI_KI_Podcasts.csv finnes ikke — ingenting å arkivere.")
        return

    cutoff = archive_cutoff()
    print(f"OK Cutoff: {cutoff}")

    with open(CSV_PATH, encoding="utf-8", newline="") as f:
        reader = csv.reader(f)
        header = next(reader, [])
        rows = list(reader)

    if not header:
        print("OK Hoved-CSV er tom — ingenting å arkivere.")
        return

    to_archive = []
    to_keep = []

    for row in rows:
        if len(row) < 4:
            to_keep.append(row)
            continue
        pub_date = row[3].strip()
        if pub_date and pub_date < cutoff:
            to_archive.append(row)
        else:
            to_keep.append(row)

    if not to_archive:
        print(f"OK Ingen episoder eldre enn {cutoff} — ingenting å arkivere.")
        return

    # Flytt til arkiv
    append_to_archive(to_archive, header)

    # Overskriv hoved-CSV
    with open(CSV_PATH, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        for row in to_keep:
            w.writerow(row)

    print(f"OK {len(to_archive)} episoder arkivert (cutoff: {cutoff}) — {len(to_keep)} igjen i hoved-CSV")

    # Synkroniser HTML
    sync_script = os.path.join(BASE_DIR, "sync_html.py")
    if os.path.exists(sync_script):
        print("OK Kjører sync_html.py...")
        subprocess.run([sys.executable, sync_script], check=True)


if __name__ == "__main__":
    main()
