"""
rate_episodes.py — Filtrerer åpenbar ikke-AI fra pending_episodes.csv.

Kjøres lokalt etter update_podcasts.py:
  python rate_episodes.py

Scriptet:
  - Leser pending_episodes.csv
  - Rene AI-podcaster: beholdes alltid (ingen sjekk nødvendig)
  - Blandede podcaster: sjekker tittel + beskrivelse for AI-nøkkelord
      score 0  → forkastes (→ rejected_episodes.csv, fjernes fra pending)
      score >0 → beholdes i pending for manuell vurdering
  - Setter IKKE rating — det gjøres manuelt av bruker
  - Kjør approve_episodes.py når du har satt rating i pending_episodes.csv
"""

import csv
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PENDING_PATH  = os.path.join(os.path.dirname(__file__), "pending_episodes.csv")
REJECTED_PATH = os.path.join(os.path.dirname(__file__), "rejected_episodes.csv")

# Podcaster der alle/nesten alle episoder er AI-relevante — beholdes alltid
PURE_AI_PODCASTS = {
    "Latent Space",
    "No Priors",
    "The AI Daily Brief",
    "TWIML AI Podcast",
    "The Cognitive Revolution",
    "Practical AI",
    "Gradient Dissent (W&B)",
    "The Artificial Intelligence Show",
    "The AI Breakdown (Andy Dumbell)",
    "The Implement AI Podcast",
    "Accounting Technology Lab Podcast",
    "AI-Snakk",
    "AI Forklart",
    "KI til Kaffen",
}

STRONG_AI = [
    "openai", "anthropic", "deepmind", "google ai", "meta ai",
    "chatgpt", "claude", "gemini", "grok", "copilot", "mistral", "llama",
    "gpt-3", "gpt-4", "gpt-5", "gpt4", "gpt3",
    "large language model", "llm", "language model",
    "machine learning", "deep learning", "neural network",
    "artificial intelligence", "generative ai", "gen ai",
    "natural language processing", "computer vision",
    "reinforcement learning", "fine-tuning", "fine tuning",
    "foundation model", "frontier model",
    "ai agent", "ai safety", "ai alignment", "ai research",
    "agi", "artificial general intelligence", "superintelligence",
    "vibe cod",
    # Norwegian
    "kunstig intelligens", "maskinlæring", "dyp læring",
    "språkmodell", "generativ ai", "generativ ki",
]

MEDIUM_AI = [
    " ai ", " ai,", " ai.", " ai:", " ai?", " ai!", "\"ai\"", "(ai)",
    "a.i.",
    " ml ", " ml,", " ml.",
    " ki ", " ki,", " ki.", " ki:", " ki?", " ki!", "(ki)",
    "automation", "robotics", "algorithm", "data science",
    "benchmark", "inference", "training data",
]


def ai_score(title: str, description: str) -> int:
    title_l = " " + title.lower() + " "
    desc_l  = " " + description.lower() + " "
    score = 0
    for kw in STRONG_AI:
        if kw in title_l:
            score += 3
        elif kw in desc_l:
            score += 2
    for kw in MEDIUM_AI:
        if kw in title_l:
            score += 2
        elif kw in desc_l:
            score += 1
    return score


def append_rejected(name: str, title: str):
    needs_header = not os.path.exists(REJECTED_PATH)
    with open(REJECTED_PATH, "a", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        if needs_header:
            w.writerow(["Podcast Name", "Episode Title"])
        w.writerow([name, title])


def main():
    if not os.path.exists(PENDING_PATH):
        print("Ingen pending_episodes.csv funnet. Kjør update_podcasts.py først.")
        return

    with open(PENDING_PATH, encoding="utf-8", newline="") as f:
        rows = list(csv.reader(f))

    if len(rows) < 2:
        print("pending_episodes.csv er tom — ingen episoder å filtrere.")
        return

    header = rows[0]
    data_rows = rows[1:]

    kept, rejected_list = [], []

    for row in data_rows:
        if len(row) < 2:
            kept.append(row)
            continue

        podcast = row[0].strip()
        title   = row[1].strip()
        desc    = row[11].strip() if len(row) > 11 else ""

        if podcast in PURE_AI_PODCASTS:
            kept.append(row)
            continue

        score = ai_score(title, desc)
        if score == 0:
            append_rejected(podcast, title)
            rejected_list.append(f"  [✗] {podcast[:30]:<30} – {title[:55]}")
        else:
            kept.append(row)

    with open(PENDING_PATH, "w", encoding="utf-8", newline="") as f:
        csv.writer(f).writerows([header] + kept)

    print(f"\nFiltrering fullført:")
    print(f"  {len(kept)} episoder beholdt i pending (krever manuell vurdering)")
    print(f"  {len(rejected_list)} episoder auto-avvist (→ rejected_episodes.csv)\n")

    if rejected_list:
        print("Avviste:")
        print("\n".join(rejected_list))

    if kept:
        print(f"\nNeste steg:")
        print(f"  1. Åpne pending_episodes.csv og sett rating (4–6) på episoder du vil beholde")
        print(f"     Rating 1–3 = avvis, Rating 0 = utsett til neste gjennomgang")
        print(f"  2. Kjør: python approve_episodes.py")


if __name__ == "__main__":
    main()
