"""
rate_episodes.py — Automatisk vurdering av urangerte episoder (Rating=0).

Regelbasert nøkkelordscoring:
  - Rene AI-podcaster: vurderes alltid videre for rating
  - Blandede podcaster: sjekker tittel + beskrivelse for AI-signal
      score 0     →  reject  (→ rejected_episodes.csv)
      score 1–2   →  review  (beholdes som 0, manuell gjennomgang)
      score >= 3  →  rate    (fortsetter til rating-logikk)

Rating-logikk (gjelder alle AI-bekreftet episoder):
  Kjente AI-eksperter nevnt  →  6
  Teknisk dybde + mange AI-signal  →  5
  Ellers  →  4
"""

import csv
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

CSV_PATH          = os.path.join(os.path.dirname(__file__), "AI_KI_Podcasts_2026.csv")
REJECTED_PATH     = os.path.join(os.path.dirname(__file__), "rejected_episodes.csv")
DESCRIPTIONS_PATH = os.path.join(os.path.dirname(__file__), "pending_descriptions.json")

# Podcaster der alle/nesten alle episoder er AI-relevante
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

# AI-signal for å bekrefte at episoden handler om AI
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

# Kjente eksperter/grunnleggere — trigger rating 6
KNOWN_EXPERTS = [
    # Researchers
    "ilya sutskever", "andrej karpathy", "yann lecun", "geoffrey hinton",
    "yoshua bengio", "demis hassabis", "shane legg", "oriol vinyals",
    "noam shazeer", "jeff dean", "fei-fei li", "andrew ng", "john schulman",
    "jan leike", "paul christiano", "chris olah", "adam d'angelo",
    # OpenAI
    "sam altman", "greg brockman", "mira murati", "kevin weil",
    # Anthropic
    "dario amodei", "daniela amodei", "amanda askell", "jared kaplan",
    # Google / DeepMind
    "sundar pichai", "jeff dean", "koray kavukcuoglu",
    # Meta
    "mark zuckerberg",
    # Microsoft
    "satya nadella", "mustafa suleyman",
    # Others
    "elon musk", "george hotz", "emmet shear", "reid hoffman",
    "jensen huang", "lisa su",
    # Norwegian AI voices
    "audun kvitland", "niclas kvanvig", "celine haaland",
]

# Signaler på teknisk dybde — bidrar til rating 5
DEPTH_SIGNALS = [
    "research", "paper", "technical", "deep dive", "architecture",
    "pretraining", "pre-training", "training run", "interpretability",
    "alignment", "safety", "benchmark", "evaluation", "reasoning",
    "multimodal", "agentic", "chain-of-thought", "rlhf", "dpo",
    "scaling law", "emergent", "inference time", "test-time compute",
    # Norwegian
    "forskning", "teknisk", "arkitektur", "sikkerhet",
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


def auto_rating(podcast: str, title: str, description: str) -> tuple[int, str]:
    """Returns (rating, note). Rating 4/5/6 for confirmed AI episodes."""
    text = " " + (title + " " + description).lower() + " "

    # Rating 6: known expert guest in title or description
    for expert in KNOWN_EXPERTS:
        if expert in text:
            return 6, f"Auto-vurdert: ekspertgjest ({expert.title()})"

    # Rating 5: technical depth signals OR many strong AI keywords
    depth_hits  = sum(1 for s in DEPTH_SIGNALS if s in text)
    strong_hits = sum(1 for kw in STRONG_AI if kw in text)
    if depth_hits >= 2 or strong_hits >= 4:
        return 5, "Auto-vurdert: AI-fokusert med teknisk dybde"
    if depth_hits >= 1 and strong_hits >= 2:
        return 5, "Auto-vurdert: AI-fokusert med teknisk dybde"

    return 4, "Auto-vurdert: AI-relevant"


def classify(podcast: str, title: str, description: str) -> tuple[str, int, str]:
    """Returns (decision, rating, note). Decision: 'keep', 'review', 'reject'."""
    if podcast not in PURE_AI_PODCASTS:
        score = ai_score(title, description)
        if score == 0:
            return "reject", 1, ""
        if score <= 2:
            return "review", 0, ""

    rating, note = auto_rating(podcast, title, description)
    return "keep", rating, note


def read_csv():
    with open(CSV_PATH, encoding="utf-8", newline="") as f:
        rows = list(csv.reader(f))
    return rows[0], rows[1:]


def load_descriptions() -> dict:
    if not os.path.exists(DESCRIPTIONS_PATH):
        return {}
    with open(DESCRIPTIONS_PATH, encoding="utf-8") as f:
        return json.load(f)


def append_rejected(name: str, title: str):
    needs_header = not os.path.exists(REJECTED_PATH)
    with open(REJECTED_PATH, "a", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        if needs_header:
            w.writerow(["Podcast Name", "Episode Title"])
        w.writerow([name, title])


def main():
    header, rows = read_csv()
    descriptions = load_descriptions()

    updated_rows = []
    kept, rejected_list, review_list = [], [], []

    for row in rows:
        if len(row) < 8 or row[7].strip() != "0":
            updated_rows.append(row)
            continue

        podcast = row[0].strip()
        title   = row[1].strip()
        desc    = descriptions.get(f"{podcast}||{title}", "")

        decision, rating, note = classify(podcast, title, desc)

        if decision == "keep":
            row = list(row)
            row[7] = str(rating)
            if not row[8].strip() or row[8].strip() == "Ny episode — ikke vurdert ennå":
                row[8] = note
            updated_rows.append(row)
            kept.append(f"  [{rating}] {podcast[:30]:<30} – {title[:55]}")
        elif decision == "reject":
            append_rejected(podcast, title)
            rejected_list.append(f"  [✗] {podcast[:30]:<30} – {title[:55]}")
        else:
            updated_rows.append(row)
            review_list.append(f"  [?] {podcast[:30]:<30} – {title[:55]}")

    with open(CSV_PATH, "w", encoding="utf-8", newline="") as f:
        csv.writer(f).writerows([header] + updated_rows)

    if os.path.exists(DESCRIPTIONS_PATH):
        os.remove(DESCRIPTIONS_PATH)

    ratings_summary = {}
    for line in kept:
        r = line.strip()[1]
        ratings_summary[r] = ratings_summary.get(r, 0) + 1

    print(f"\nAuto-vurdering fullført:")
    for r in sorted(ratings_summary, reverse=True):
        print(f"  {ratings_summary[r]} episoder → rating {r}")
    print(f"  {len(rejected_list)} episoder avvist (→ rejected_episodes.csv)")
    print(f"  {len(review_list)} episoder til manuell gjennomgang (rating=0)\n")

    if kept:
        print("Godkjente:")
        print("\n".join(kept))
    if rejected_list:
        print("\nAvviste:")
        print("\n".join(rejected_list))
    if review_list:
        print("\nTil gjennomgang:")
        print("\n".join(review_list))


if __name__ == "__main__":
    main()
