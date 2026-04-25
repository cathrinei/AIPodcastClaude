# AI Podcast Tracker 2026

A curated list of podcast episodes on artificial intelligence (AI / KI) published in 2026 — both English and Norwegian.

**[Open interactive episode browser →](https://cathrinei.github.io/AIPodcastClaude/AI_KI_Podcasts.html)**

## What's in here

- **164 episodes** across **26 shows** (116 English, 48 Norwegian)
- Ratings 4–6 only — surface-level or off-topic episodes are excluded
- Tags for recurring themes: `vibe` (vibe coding), `openclaw`, `agents`
- Norwegian sources: AI-Snakk, AI Forklart, Heis, Kode24-podkasten, Shifter, and more
- English sources: Latent Space, Lex Fridman, Hard Fork, No Priors, The Cognitive Revolution, and more

## Files

| File | Description |
|---|---|
| `AI_KI_Podcasts.html` | Interactive browser — filter, sort, search, load CSV |
| `AI_KI_Podcasts.csv` | Master data — one row per episode |
| `update_podcasts.py` | RSS fetcher — adds new episodes since last known date |
| `rejected_episodes.csv` | Denylist — off-topic episodes that won't be re-fetched |

## Rating scale

| Score | Meaning |
|---|---|
| 6 | Exceptional — deep AI focus, expert guests, high value |
| 5 | Very useful — solid AI content, clear focus |
| 4 | Useful — relevant AI coverage |

## Usage

```bash
# Fetch new episodes from RSS feeds
python update_podcasts.py
```

Then open `AI_KI_Podcasts.html` in a browser and click **↑ Last inn CSV** to load the updated data.
