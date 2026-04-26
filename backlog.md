# Backlog — AIPodcastClaude

Foreslåtte forbedringer, sortert etter prioritet. Ikke tidsbestemt.

---

## 🔴 Høy prioritet

### 1. Implementer llm-tag
- CSS-badge: `.tag-llm { background: #ede9fe; color: #5b21b6; }` (lilla)
- `tagMeta`: `llm: { label: 'LLM', cls: 'tag-llm' }`
- Legg til LLM-knapp i tag-filterpanelet
- Oppdater 16 episoder i CSV (se tabell under)
- Oppdater CLAUDE.md (legg til `llm` i Tags-kolonnen)

**Episoder som får llm-tag:**

| Podcast | Tittel | Nåværende tag → Ny |
|---------|--------|--------------------|
| AI Forklart | Det rundt spørsmålet: Valgene som gir bedre svar | (ingen) → `llm` |
| AI Forklart | Når språkmodellen får deg inn i en spiral av feil | (ingen) → `llm` |
| AI Forklart | Prompting del 1: Samtalen med AI | (ingen) → `llm` |
| AI Forklart | Prompting del 2: RASK-modellen | (ingen) → `llm` |
| AI Forklart | Hvordan tilpasse AI-chatboten til meg? | (ingen) → `llm` |
| AI-Snakk | Ep 35 – GPT-5.2 Løser 30 År Gammelt Matematikkproblem | (ingen) → `llm` |
| Win-Win with Liv Boeree | #53 – John Schultz – Why Google Made ChatGPT, Gemini & Claude Play 900,000 Hands | (ingen) → `llm` |
| Latent Space | Anthropic Distillation & How Models Cheat (SWE-Bench Dead) | (ingen) → `llm` |
| TWIML AI Podcast | The Race to Production-Grade Diffusion LLMs with Stefano Ermon | (ingen) → `llm` |
| Latent Space | Training Transformers to solve 95% failure rate of Cancer Trials | (ingen) → `llm` |
| Latent Space | [AINews] Gemma 4 crosses 2 million downloads | (ingen) → `llm` |
| Latent Space | [AINews] Top Local Models List - April 2026 | (ingen) → `llm` |
| Latent Space | [AINews] Anthropic Claude Opus 4.7 | (ingen) → `llm` |
| Latent Space | [AINews] Moonshot Kimi K2.6 | (ingen) → `llm` |
| Lex Fridman Podcast | #490 – State of AI in 2026: LLMs / Coding / Scaling / China | `vibe` → `vibe,llm` |
| TWIML AI Podcast | #762 – AI Trends 2026 | `openclaw` → `openclaw,llm` |

---

## 🟡 Middels prioritet

### 2. Legg til Kode24-podkasten i RSS-feeder
Nevnt i CLAUDE.md som norsk kilde, men mangler i `FEEDS`-dicten i `update_podcasts.py`.
Finn RSS-URL og legg til. Sjekk om den er ren AI-podcast (→ `PURE_AI_PODCASTS`).

### 3. Tag-knapper: vis episodeantall
Eks: «Vibe coding (28)» i stedet for bare «Vibe coding».
Beregnes dynamisk fra filtrert datasett i `renderTags()`/kontrollpanelet.
Gir brukeren bedre oversikt over taggens omfang.

### 4. Tomt-tilstand ved ingen søkeresultater
Når filtrering gir 0 treff: vis en tydelig melding i tabellen/kortvisningen
(f.eks. «Ingen episoder matcher filteret — prøv å justere søket»).
Hindrer forvirring ved tomme resultater.

---

## 🟢 Lav prioritet / nice to have

### 5. Eksporter filtrert visning som CSV
Knapp som laster ned gjeldende filtrert datasett som CSV.
Nyttig for egne analyser eller deling.
Implementeres med `Blob` + `URL.createObjectURL`.

~~### 6. «Tilbake til toppen»-knapp~~ ✅ implementert

### 7. rate_episodes.py: legg til llm-nøkkelord
Når llm-tag er implementert: legg til LLM-relaterte nøkkelord
(`llm`, `language model`, `prompting`, `transformer`, `benchmark`) i `MEDIUM_AI`-lista
for bedre automatisk scoring av pending-episoder.

### 8. GitHub Actions: kjør rate_episodes.py automatisk
Etter `update_podcasts.py` i workflow: kjør `python rate_episodes.py` automatisk.
Filtrerer åpenbar ikke-AI fra pending før manuell gjennomgang.
Krever at `rate_episodes.py` ikke har interaktive spørsmål (det har den ikke).
Merk: øker risiko for falske positiver — vurder nøye.

---

## ✅ Fullført

- **«Tilbake til toppen»-knapp** — fast posisjonert, vises etter 300px scroll (PR #26)
- **Tomt-tilstand ved 0 søkeresultater** — allerede implementert (ikke i backlog)

- **Fyll inn Host(s) og Main Topic(s)** — 26 episoder oppdatert (PR #24)
- **`/`-snarvei for søkefelt** — implementert i HTML (PR #24)
- **Upreis dato på 3 episoder** — fikset (PR #24):
  - E24-podden «AI og cybersikkerhet» → 2026-02-18
  - Practical AI «AI in 2025 & What's Coming in 2026» → 2026-01-09
  - The Cognitive Revolution «AI 2025→2026 Live Show Part 1» → 2025-12-18
