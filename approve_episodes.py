"""
approve_episodes.py — Flytter godkjente episoder fra pending til hoved-CSV.

Kjøres lokalt etter at du har satt rating manuelt i pending_episodes.csv:
  python approve_episodes.py

Behandling per episode:
  Rating 4–6 → flyttes til AI_KI_Podcasts.csv (Description-kolonnen fjernes)
  Rating 1–3 → flyttes til rejected_episodes.csv (aldri hentet igjen)
  Rating 0   → beholdes i pending til neste gjennomgang
"""

import csv
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

CSV_PATH      = os.path.join(os.path.dirname(__file__), "AI_KI_Podcasts.csv")
PENDING_PATH  = os.path.join(os.path.dirname(__file__), "pending_episodes.csv")
REJECTED_PATH = os.path.join(os.path.dirname(__file__), "rejected_episodes.csv")


def main():
    if not os.path.exists(PENDING_PATH):
        print("Ingen pending_episodes.csv funnet.")
        return

    with open(PENDING_PATH, encoding="utf-8", newline="") as f:
        rows = list(csv.reader(f))

    if len(rows) < 2:
        print("pending_episodes.csv er tom — ingenting å godkjenne.")
        return

    pending_header = rows[0]
    data_rows = rows[1:]

    with open(CSV_PATH, encoding="utf-8", newline="") as f:
        main_rows = list(csv.reader(f))
    main_header = main_rows[0]
    main_data   = main_rows[1:]

    approved, rejected_list, still_pending = [], [], []

    for row in data_rows:
        if len(row) < 8:
            still_pending.append(row)
            continue

        try:
            rating = int(row[7].strip())
        except ValueError:
            still_pending.append(row)
            continue

        podcast = row[0].strip()
        title   = row[1].strip()

        if rating >= 4:
            approved.append(row[:11])  # strip Description column
            print(f"  [✓] [{rating}] {podcast[:30]:<30} – {title[:55]}")
        elif 1 <= rating <= 3:
            needs_header = not os.path.exists(REJECTED_PATH)
            with open(REJECTED_PATH, "a", encoding="utf-8", newline="") as f:
                w = csv.writer(f)
                if needs_header:
                    w.writerow(["Podcast Name", "Episode Title"])
                w.writerow([podcast, title])
            rejected_list.append(f"  [✗] {podcast[:30]:<30} – {title[:55]}")
        else:
            still_pending.append(row)

    if approved:
        with open(CSV_PATH, "w", encoding="utf-8", newline="") as f:
            csv.writer(f).writerows([main_header] + main_data + approved)

    with open(PENDING_PATH, "w", encoding="utf-8", newline="") as f:
        csv.writer(f).writerows([pending_header] + still_pending)

    print(f"\nApprove fullført:")
    print(f"  {len(approved)} episoder lagt til i AI_KI_Podcasts.csv")
    print(f"  {len(rejected_list)} episoder avvist (→ rejected_episodes.csv)")
    print(f"  {len(still_pending)} episoder beholdt i pending (rating=0)\n")

    if rejected_list:
        print("Avviste:")
        print("\n".join(rejected_list))

    if not still_pending:
        print("✓ pending_episodes.csv er nå tom.")
    else:
        print(f"⚠  {len(still_pending)} episode(r) venter fortsatt på vurdering i pending_episodes.csv")


if __name__ == "__main__":
    main()
