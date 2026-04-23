"""
show_pending.py — Viser pending_episodes.csv i lesbar form.

Kjøres lokalt:
  python show_pending.py
"""

import csv
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PENDING_PATH = os.path.join(os.path.dirname(__file__), "pending_episodes.csv")

COLS = {
    "podcast":  0,
    "title":    1,
    "lang":     2,
    "date":     3,
    "hosts":    4,
    "guests":   5,
    "topics":   6,
    "rating":   7,
    "notes":    8,
    "tags":     9,
    "link":     10,
    "desc":     11,
}

W = 90  # linje-bredde


def hr(char="─"):
    return char * W


def fmt(label, value, width=76):
    if not value or not value.strip():
        return ""
    return f"  {label:<10} {value.strip()[:width]}"


def main():
    if not os.path.exists(PENDING_PATH):
        print("Ingen pending_episodes.csv funnet. Kjør update_podcasts.py først.")
        return

    with open(PENDING_PATH, encoding="utf-8", newline="") as f:
        rows = list(csv.reader(f))

    if len(rows) < 2:
        print("pending_episodes.csv er tom — ingen episoder å vise.")
        return

    data = rows[1:]

    print()
    print(hr("═"))
    print(f"  PENDING EPISODER ({len(data)} stk)")
    print(hr("═"))

    for i, row in enumerate(data, 1):
        podcast = row[COLS["podcast"]].strip() if len(row) > COLS["podcast"] else ""
        title   = row[COLS["title"]].strip()   if len(row) > COLS["title"]   else ""
        lang    = row[COLS["lang"]].strip()     if len(row) > COLS["lang"]    else ""
        date    = row[COLS["date"]].strip()     if len(row) > COLS["date"]    else ""
        hosts   = row[COLS["hosts"]].strip()    if len(row) > COLS["hosts"]   else ""
        guests  = row[COLS["guests"]].strip()   if len(row) > COLS["guests"]  else ""
        topics  = row[COLS["topics"]].strip()   if len(row) > COLS["topics"]  else ""
        rating  = row[COLS["rating"]].strip()   if len(row) > COLS["rating"]  else "0"
        notes   = row[COLS["notes"]].strip()    if len(row) > COLS["notes"]   else ""
        link    = row[COLS["link"]].strip()     if len(row) > COLS["link"]    else ""
        desc    = row[COLS["desc"]].strip()     if len(row) > COLS["desc"]    else ""

        rating_display = rating if rating and rating != "0" else "0 (ikke satt)"
        lang_flag = "🇳🇴" if lang.lower() == "norwegian" else "🇬🇧"

        print()
        print(f"  [{i:>2}] {podcast}  {lang_flag}  {date}")
        print(f"       {title[:80]}")
        print(hr())
        lines = [
            fmt("Rating:",  rating_display),
            fmt("Vertskap:", hosts),
            fmt("Gjest:",    guests),
            fmt("Emner:",    topics),
            fmt("Notater:",  notes),
            fmt("Lenke:",    link),
        ]
        for line in lines:
            if line:
                print(line)
        if desc:
            print()
            # Bryt beskrivelsen over flere linjer
            words = desc.split()
            line_buf, max_w = [], 76
            for word in words:
                if sum(len(w) + 1 for w in line_buf) + len(word) > max_w:
                    print("  " + " ".join(line_buf))
                    line_buf = [word]
                else:
                    line_buf.append(word)
            if line_buf:
                print("  " + " ".join(line_buf))

    print()
    print(hr("═"))
    print(f"  Neste steg:")
    print(f"    1. Åpne pending_episodes.csv — sett Rating (4–6 / 1–3 / 0)")
    print(f"    2. Fyll inn Host(s), Guest(s), Main Topic(s), Tags")
    print(f"    3. python approve_episodes.py")
    print(hr("═"))
    print()


if __name__ == "__main__":
    main()
