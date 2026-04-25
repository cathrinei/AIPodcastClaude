# Backlog — AIPodcastClaude

Foreslåtte forbedringer, sortert etter prioritet. Ikke tidsbestemt.

---

## 🔴 Høy prioritet

### 1. Implementer llm-tag
Se `llm_tag_plan.md` for fullstendig plan (16 episoder + HTML-endringer).
- CSS-badge: `#ede9fe / #5b21b6` (lilla)
- `tagMeta`: `llm: { label: 'LLM', cls: 'tag-llm' }`
- Oppdater 16 episoder i CSV
- Oppdater CLAUDE.md

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
