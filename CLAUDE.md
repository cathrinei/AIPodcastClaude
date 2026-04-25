# AIPodcastClaude – Project Context

## Purpose
This project collects and curates podcast episodes on artificial intelligence (AI / KI / kunstig intelligens), including the sub-topic of vibe coding, published in 2026. Both Norwegian-language and English-language podcasts are in scope.

## Files
- `AI_KI_Podcasts_2026.csv` — master data, one row per episode (kun godkjente episoder, rating 4–6)
- `AI_KI_Podcasts_2026.html` — interactive table with filtering, sorting, stats, CSV import
- `index.html` — redirect fra rot-URL til `AI_KI_Podcasts_2026.html` (GitHub Pages)
- `pending_episodes.csv` — staging-fil: nye episoder som venter på manuell vurdering (12 kolonner inkl. Description)
- `update_podcasts.py` — RSS fetcher; legger nye episoder i `pending_episodes.csv`, ikke hoved-CSV
- `rate_episodes.py` — filtrerer åpenbar ikke-AI fra pending (score=0 → rejected); setter ingen rating
- `approve_episodes.py` — flytter manuelt ratede episoder fra pending til hoved-CSV
- `show_pending.py` — viser pending_episodes.csv i lesbar form i terminalen; kjøres lokalt
- `rejected_episodes.csv` — denylist of already-reviewed non-AI episodes; prevents re-fetching noise

## Live URL
`https://cathrinei.github.io/AIPodcastClaude/` — serves the latest committed HTML + CSV automatically. GitHub Actions updates the CSV daily at 11:00 CEST; Pages rebuilds on every push to `main`.

## CSV columns

| Column | Description |
|---|---|
| Podcast Name | Official show name |
| Episode Title | Specific episode title |
| Language | English or Norwegian |
| Published Date | YYYY-MM-DD |
| Host(s) | Host names |
| Guest(s) | Guest names (if notable) |
| Main Topic(s) | Key AI/KI subjects covered |
| Rating (1–6) | See rubric below |
| Rating Notes | 1–2 sentence justification |
| Tags | vibe / openclaw / agents / combinations (or empty) |
| Platform / Link | URL to episode or show |

## CSV policy
- **Only episodes rated 4–6 are kept.** Episodes rated 1–3 are removed entirely.
- **Unrated episodes (Rating=0)** lagres i `pending_episodes.csv` — aldri i hoved-CSV.
- Always update the CSV **before** the HTML when making data changes. CSV is the source of truth.
- Do not add short videos, teasers, trailers, or highlight compilations — full-length episodes only.

## Rating rubric (1–6)

| Score | Label | Meaning |
|---|---|---|
| 6 | Exceptional | Deep AI focus, expert guests/hosts, high practical or research value |
| 5 | Very useful | Solid AI content, clear focus, reliable and informative |
| 4 | Useful | Relevant AI coverage; may be surface-level or AI is one of several topics |
| 3 | Somewhat relevant | Not kept — removed from CSV |
| 2 | Marginal | Not kept — removed from CSV |
| 1 | Not relevant | Not kept — removed from CSV |

## Standardiserte vertnavn
Bruk disse navnene konsekvent ved rating av nye episoder:
- **Latent Space**: Shawn Wang, Alessio Fanelli *(ikke swyx eller Swyx)*
- **Hard Fork (NYT)**: Kevin Roose, Casey Newton
- **The Cognitive Revolution**: Nathan Labenz
- **No Priors**: Sarah Guo, Elad Gil
- **AI-Snakk**: Audun Kvitland Røstad
- **AI Forklart**: Niclas Kvanvig, Celine Haaland-Johansen

## False positive filtering
- **KI** must mean *kunstig intelligens* (artificial intelligence), not a company abbreviation or person's name.
- **AI** must refer to artificial intelligence technology, not Amnesty International or other uses.
- When in doubt about relevance, keep the episode and let the user decide. Only remove episodes that are obviously off-topic.

## Search sources used
- **English**: Latent Space, Lex Fridman, Hard Fork (NYT), No Priors, The AI Daily Brief, TWIML AI Podcast, The Cognitive Revolution, Practical AI, Gradient Dissent (W&B), The Artificial Intelligence Show, The AI Breakdown, The Journal (WSJ), Today Explained (Vox), Agile Mentors Podcast, Win-Win with Liv Boeree, The Implement AI Podcast
- **Norwegian**: AI-Snakk (aisnakk.no), E24-podden, Shifter, Digi.no, lorn.tech, nora.ai, HR-podden, Teknologi og mennesker (Atea), Bouvet Bobler
- **Podcast directories**: Apple Podcasts, Spotify, listennotes.com, podchaser.com

## Key findings (Jan 2026 – 21.04.26)
- **164 episodes** across **26 shows** (116 English, 48 Norwegian) — 164 rated (4–6)
- **Vibe coding** was a dominant cross-show theme — tagged across multiple series
- **OpenClaw** (formerly Clawdbot/Moltbot) emerged as a major cross-show topic — 10+ episodes tagged
- **Top-rated English episodes (6/6):** Latent Space × 5, Lex Fridman #490 + #491, No Priors (Karpathy), TWIML × 2 — 10 total
- **Best Norwegian source:** AI-Snakk — weekly episodes Jan–Apr, consistent quality, Norwegian AI news with local relevance
- **Norwegian sources:** AI Forklart (Niclas Kvanvig & Celine Haaland-Johansen), Heis, KI til Kaffen, Shifter, Kode24-podkasten
- **Anthropic vs. Pentagon**, **SaaSpocalypse** and **OpenClaw** were recurring cross-show news events

## HTML – tekniske noter

### Data array
The `data` array in the HTML is populated from the CSV. When changes are made to episode data, update the CSV first, then sync the HTML data array. Unrated episodes (Rating=0) display as **N/A** in the rating badge and always pass through the rating filter regardless of the minimum rating setting.

### Stats
`updateStats()` computes all stats automatically from the `data` array:
- Total episodes, English count, Norwegian count, top-rated (6/6) count
- "Podkastserier" and "episoder uten rating" cards removed
- Each stat card is clickable: applies a corresponding filter and marks itself `.active`; clicking "total" resets all filters
- `applyStatFilter(action)` handles card clicks — sets `langFilter`/`ratingFilter` and calls `buildPodcastFilter()` + `refresh()`
- Active state clears automatically when the user touches any manual filter control (`input` event)

### Auto-fetch CSV (GitHub Pages)
- On page load, an async IIFE calls `fetch('./AI_KI_Podcasts_2026.csv')` (same-origin)
- If successful: parses CSV, replaces `data` array, calls `buildPodcastFilter()` + `updateStats()` + `refresh()`
- Status bar shows `✓ X episoder lastet inn automatisk [· Y nye]` — men kun første gang etter at CSV er endret
- Fingeravtrykk: `Last-Modified`-headeren fra fetch-svaret lagres i `localStorage.csvLastModified`; melding vises bare når den er endret siden sist besøk; fallback til antall rader hvis headeren mangler
- Silently falls back to the built-in `data` array when opened as `file://` (fetch fails due to CORS) or on network error
- CSP `connect-src 'self'` already allows same-origin fetch — no changes needed

### "↑ Last inn CSV"-knappen
Skjult (`style="display:none"` på `#updateBtn`) — CSV lastes automatisk via fetch() på GitHub Pages.
For å vise igjen: fjern `style="display:none"` fra `#updateBtn` i HTML-en (kommentar i koden forklarer dette).
Manuell fallback for lokal bruk (`file://`) eller testing med en spesifikk CSV-fil:
1. Opens a file picker (`<input type="file" accept=".csv">`)
2. Reads file with `FileReader` (UTF-8)
3. `parseCSV()` parses content — handles commas in quoted fields and CRLF/LF
4. `data` array is cleared and refilled; header row skipped
5. Rating field (column 7) parsed with `parseInt` + `isNaN` fallback to 0
6. `updateStats()` and `refresh()` run immediately

### Dark mode
- Toggle button (☾ Mørk / ☀ Lys) in the top-right of the header
- Preference persisted in `localStorage` (`darkMode` key: `'1'` = dark, `'0'` = light)
- Implemented via CSS custom properties on `:root`; `body.dark` overrides all color variables
- Light mode is the default

### Design / visuell stil
- **Accent**: `--accent: #6366f1` (lys: indigo, mørk: `#818cf8`) — brukes på knapp, focus-outline, rad-hover-kant
- **Header**: `var(--surface)` (hvit/mørk via variabel) + `border-top: 3px solid var(--accent)` + `border-bottom: 1px solid var(--border)`; ingen dark-mode-override nødvendig — CSS-variabler håndterer det automatisk
- **Mørk-toggle**: bruker `var(--border)` / `var(--text-muted)` — ingen hardkodede dark-overrides
- **Stats-bokser**: hvit bakgrunn, `border: 1px solid var(--border)`, `border-radius: 12px`; tall i `font-size: 2rem / font-weight: 800`; klikkbare — hover gir accent-kant, `.active` gir `box-shadow: 0 0 0 3px rgba(99,102,241,0.18)`
- **Tabelloverskrift**: `background: #f0f1f5` (nøytral off-white); tekst `#6b7280`; kolonner skilt med `border-right: 1px solid var(--border)`; sortert kolonne får `color: var(--accent)`; dark mode: `#252840`
- **Kontrollfelt**: `background: var(--bg)` (litt mørkere enn `--surface`) — visuelt skilt fra stat-raden over
- **Radhovering**: leaderboard-stil — `inset 4px 0 0 var(--accent)` + lys lilla bakgrunn; smooth `0.12s ease` transisjon
- **Zebrastriping**: annenhver rad bruker `--row-alt` (`#f5f7fc` lys / `#1f2235` mørk)
- **Rating-badge**: `32px`, `font-weight: 800`; r4/r5/r6 har glow (`box-shadow: 0 0 0 3px rgba(...)`)
- **"Last inn CSV"-knapp**: gradient + glow (`box-shadow: 0 2px 8px rgba(99,102,241,0.45)`)
- **Episodetittel**: klikkbar lenke (`a.episode-title-link`) — åpner episodelenken i ny fane; hover gir accent-farge + understreking; «Lytt»-kolonne fjernet
- Ingen eksterne fonter eller ressurser — holder CSP intakt

### Ny-markering av episoder
- Nye episoder markeres med amber venstrekant (`inset 3px 0 0 #f59e0b`) + svak amber bakgrunn ved CSV-innlasting
- Implementert via `localStorage.seenEpisodeKeys` (JSON-array av `"podcast||title"`-nøkler fra forrige innlasting)
- `newEpisodeKeys` (global `Set`) populeres ved CSV-innlasting: episoder ikke i `prevSeenKeys` legges til
- Første innlasting (ingen `localStorage`): ingen markering (`hasPrevData = false`)
- `localStorage` oppdateres med alle nøkler fra ny CSV etter hver innlasting — så neste runde starter ferskt
- Statuslinjen viser f.eks. `✓ 160 episoder lastet inn … · 4 nye` når nye episoder finnes
- `renderTable` sjekker `newEpisodeKeys` og setter `tr.classList.add('ep-new')` der det passer
- Hover på `ep-new`-rad: lilla accent-stripe tar over (`.ep-new:hover` overstyrer amber)
- Dark mode: `rgba(245,158,11,0.10)` + `#fbbf24` stripe
- CSS-klasser: `tbody tr.ep-new`, `body.dark tbody tr.ep-new`, `tbody tr.ep-new:hover`

### Favoritter
- ☆/★ stjerne-knapp mellom Podkast- og Episode-kolonnen (desktop) og øverst i mobilkort — klikk for å toggle
- `favoriteKeys` (global `Set`) lastet fra `localStorage.favEpisodeKeys` (JSON-array av `"podcast||title"`-nøkler) ved oppstart
- `toggleFavorite(key)` legger til/fjerner nøkkel og kaller `saveFavorites()` + `refresh()`
- `saveFavorites()` skriver `[...favoriteKeys]` til `localStorage.favEpisodeKeys`
- `showFavoritesOnly` (global boolean) — slås på/av av «☆ Favoritter»-knappen i kontrollpanelet
- `getFiltered()` sjekker `showFavoritesOnly` og filtrerer bort ikke-favoriterte rader
- Rad-teller viser `· Favoritter (N)` når filteret er aktivt
- Favoritterte rader/kort får svak amber bakgrunn (`rgba(245,158,11,0.05/0.06)`)
- Event delegation på `tableBody`/`cardList` for `[data-fav]`-knapper — overlever re-render
- `resetFilters()` slår av favorittfilter og tilbakestiller knapp-tekst/aria-pressed
- CSS-klasser: `tbody tr.ep-fav`, `.ep-card.ep-fav`, `.fav-btn`, `.fav-filter-btn.active`

### Del-lenke
- «🔗 Del»-knapp i kontrollpanelet bygger en URL med aktive filtre og kopierer til utklippstavlen
- Støttede query-parametre: `search`, `lang`, `podcast`, `rating` (utelates hvis 4), `tag`, `favs=1`
- `buildShareUrl()` leser alle filterverdier og bygger `URLSearchParams`
- `applyUrlParams()` kjøres ved oppstart etter `buildPodcastFilter()` — setter alle filtre fra URL
- Kopiering via `navigator.clipboard.writeText()`; fallback til `prompt()` for eldre nettlesere
- Knapp viser «✓ Kopiert!» i 2 sek, tilbakestilles automatisk

### Swipe-til-favoritt (mobil)
- På touch-enheter: sveip høyre (≥ 60 px, klart horisontalt) på et mobilkort for å toggle favoritt
- Implementert i en IIFE med `touchstart` / `touchmove` / `touchend` / `touchcancel` på `#cardList`
- Under sveip: kortet forskyves (`translateX`) og amber venstrekant vokser proporsjonalt med distansen
- Ved `touchend`: kort snapper tilbake med ease-transisjon; favoritt toggles hvis terskel nådd
- Avbrytes hvis `|dy| / |dx| > 0.5` — vertikal scrolling forstyrres ikke
- `will-change: transform` på `.ep-card` for ytelse
- Hint-tekst `sveip → ★` vises på første kort kun på touch-enheter (`@media (hover: none) and (pointer: coarse)`)

### Øvrige tekniske noter
- Sort state: `sort` object (`col`, `asc`); `RATING_COL = 7`, `DATE_COL = 3`, `CSV_MAX_BYTES` constants
- Default sort: date descending (nyeste øverst); rating og dato starter begge med synkende rekkefølge ved klikk
- Column sort handlers use `data-col` attributes + click + keydown (Enter/Space) event listeners — no inline `onclick`
- Tags whitelisted via `tagMeta` object — unknown tag values ignored; current tags: `vibe`, `openclaw`, `agents`
- `safeUrl()` blocks non-HTTP(S) URLs to prevent `javascript:` injection
- CSP: `default-src 'none'; style-src 'unsafe-inline'; script-src 'unsafe-inline'; connect-src 'self'`
- `parseCSV` trims only unquoted fields — preserves whitespace in quoted titles
- Default filter on load: rating 4+; N/A episodes always shown regardless of filter
- Search is fuzzy: exact substring match first, then subsequence fallback (e.g. `"krpthy"` matches `"Karpathy"`)
- Tag filter uses exact split match — `tags.split(',').map(t => t.trim()).includes(tagFilter)` — prevents substring false positives
- Rating class injection hardened: `'r'+rating` only applied when rating is strictly in `[1,2,3,4,5,6]`
- CSV upload capped at 5 MB — `CSV_MAX_BYTES` constant; `reader.onerror` handler added
- `parseInt` called with explicit radix 10 throughout

### WCAG AA – tilgjengelighet
Alle kjente WCAG AA-problemer er fikset. Gjeldende status:

**Kontrast (1.4.3):**
- `thead th`: `#4b5563` på `#f0f1f5` (~5.9:1) ✅ — var `#6b7280` (4.3:1, feilet)
- `--text-faint: #595959`, `--no-tags: #767676` på hvit — begge ≥ 4.5:1 ✅
- `.r6` badge `#15803d` på hvit tekst — 4.8:1 ✅
- Alle tag-badges (`tag-vibe`, `tag-openclaw`, `tag-agents`) og språk-badges (`lang-en`, `lang-no`) — alle ≥ 4.5:1 ✅

**Semantikk / ARIA (1.3.1):**
- Alle `<th>` har `scope="col"` ✅
- Sortérbare `<th>` har `aria-sort="none/ascending/descending"` — oppdateres dynamisk i `sortTable()` ✅
- `<table>` har `aria-label="Podkast-episoder om kunstig intelligens"` ✅
- Karakter-kolonne (`★`) har `aria-label="Karakter"` ✅
- `.sort-icon`-span har `aria-hidden="true"` — dekorative ikoner skjult for skjermlesere ✅

**Tilstand (4.1.2):**
- Stat-kort: `aria-pressed="true/false"` — oppdateres i `applyStatFilter()` ✅
- `#darkToggle`: `aria-pressed="true/false"` — oppdateres i `applyDark()` ✅
- Tags: `aria-pressed="${tagFilter === key}"` — settes ved `renderTags()` ✅

**Fokus (2.4.7):**
- `:focus-visible` dekker: `button`, `input`, `select`, `a`, `[role="button"]`, `thead th` ✅
- Mørk modus: outline-farge `#818cf8` ✅

**Tastatur (2.1.1):**
- Alle `<th data-col>`: keydown-handler (Enter/Space) for sortering ✅
- Stat-kort, tags: Enter/Space aktiverer filteret ✅

## update_podcasts.py – tekniske noter
- `FEEDS` dict: add new podcasts with name (must match CSV) and RSS URL — 26 feeds currently
- Fetches only episodes newer than last known date per podcast (`latest_date_per_podcast`)
- New episodes written to **`pending_episodes.csv`** (staging file) — never to main CSV directly
- Extracts RSS `<description>` for each new episode (HTML stripped, truncated to 600 chars); written as column 12 in `pending_episodes.csv`
- `read_csv(path)` takes a path argument and returns `(None, [])` if file doesn't exist
- Reads both `CSV_PATH` and `PENDING_PATH`; combines rows for duplicate/date checking (`all_known_rows`)
- New episodes appended to existing pending rows (not overwritten) — so pending accumulates until reviewed
- Loads `rejected_episodes.csv` at startup via `load_rejected()` — returns `set` of `(podcast.lower(), title.lower())` pairs
- Fetched episodes filtered against both `existing_keys` and `rejected` before being added — skipped count reported in output
- GitHub Actions runs this script daily; commits only `pending_episodes.csv`

### Regler mot duplikater og feil språk
- **`LANGUAGE_OVERRIDE`-dict**: Tvinger riktig språk for kjente norske podcaster uavhengig av RSS-feedens `<language>`-tag. Heis og andre norske feeder kan mangle eller returnere feil kode — overriden sikrer at episodene alltid får "Norwegian". Legg til nye norske podcaster her ved behov.
- **Samme-dato-advarsel**: Når en ny episode har samme (podcast, dato) som en allerede eksisterende episode i CSV-en, skrives `⚠  Mulig duplikat (samme dato finnes)` i output. Krever manuell sjekk — noen podcaster publiserer legitimt flere episoder samme dag.

### Kjente fallgruver ved episodefetching
- **Gamle «siste kjente dato»**: Dersom en podcast ikke har blitt kjørt på en stund (eller har få episoder i CSV), kan `latest_date_per_podcast()` returnere en gammel dato — og hele gapet siden da hentes inn som «nye» episoder. Eksempel: Lex Fridman siste i CSV: 2026-02-12 → episodene #492–#495 (mars/april) fanget opp først ved neste kjøring.
- **RSS-titteldrift gir duplikater**: Noen feeder endrer tittelformatering over tid (em-strek vs bindestrek, apostrof-encoding, mellomrom vs bindestrek). `existing_keys` bruker eksakt match på `title.lower()`, så minimale titteldifferanser sniker seg gjennom som nye episoder. Løsning: kjør duplikatsjekk etter `update_podcasts.py` og fjern eventuelle dobbeltoppføringer manuelt.

## rate_episodes.py – tekniske noter
- Kjøres lokalt etter `git pull`; leser `pending_episodes.csv` og filtrerer åpenbar ikke-AI
- **Setter ingen rating** — det gjøres manuelt av bruker etterpå
- **Pure AI podcasts** (`PURE_AI_PODCASTS` set): skip AI check, beholdes alltid i pending
- **Mixed podcasts**: `ai_score()` sjekker tittel (høyere vekt) og description (kolonne 12) for `STRONG_AI` / `MEDIUM_AI` keywords
  - score 0 → avvis automatisk (→ `rejected_episodes.csv`, fjernes fra pending)
  - score > 0 → beholdes i pending med Rating=0 for manuell vurdering
- Output viser antall beholdt og antall avvist med titler

## approve_episodes.py – tekniske noter
- Kjøres lokalt etter at rating er satt manuelt i `pending_episodes.csv`
- Leser alle rader fra `pending_episodes.csv` og behandler etter rating:
  - **Rating 4–6** → `row[:11]` (Description-kolonnen strippes) legges til i `AI_KI_Podcasts_2026.csv`
  - **Rating 1–3** → legges til i `rejected_episodes.csv` (kun Podcast Name + Episode Title)
  - **Rating 0** → beholdes i `pending_episodes.csv` til neste gjennomgang
- Skriver oppdatert `AI_KI_Podcasts_2026.csv` (eksisterende rader + nye godkjente)
- Skriver oppdatert `pending_episodes.csv` (kun rating=0-rader igjen)
- Output viser tydelig antall godkjent, avvist og gjenværende i pending

## show_pending.py – tekniske noter
- Kjøres lokalt for å lese `pending_episodes.csv` i lesbar form: `python show_pending.py`
- Viser alle ventende episoder nummerert med: podcast, tittel, språk, dato, vertskap, gjest, emner, rating, lenke og beskrivelse
- Beskrivelse brytes over flere linjer (maks 76 tegn per linje)
- Viser neste-steg-instruksjoner nederst (sett rating → kjør approve_episodes.py)
- Ingen endringer i filer — kun lesing og visning

## rejected_episodes.csv – format og bruk
- Columns: `Podcast Name`, `Episode Title` (header row required)
- Each row is an episode that has been reviewed and rejected as off-topic/non-AI
- Matching is case-insensitive: `(podcast_name.lower(), title.lower())`
- To reject an episode permanently: add a row with exact podcast name and episode title
- `update_podcasts.py` will never re-add a rejected episode, even if it reappears in the RSS feed
- Pre-populated with ~75 rejected entries from: Lex Fridman, No Priors, The Journal (WSJ), Today Explained (Vox), Shifter, HR-podden, Teknologi og mennesker, Heis, Big Take Asia

## Podcasts without RSS (check manually)
These shows are in the episode list but have no RSS feed in `update_podcasts.py` — check periodically for new episodes:
- **Norske:** Bouvet Bobler *(no RSS feed found)*
- **Engelske:** The Journal (WSJ) *(has RSS but produces many off-topic episodes — manual curation needed)*

## Git workflow
Bruk feature-brancher for alle endringer — aldri commit direkte til `main`.

```bash
# Start ny arbeidsøkt
git checkout main && git pull
git checkout -b session/YYYY-MM-DD   # eller feature/kort-beskrivelse

# Etter endringer
git add <filer>
git commit -m "kort beskrivelse av hva og hvorfor"
git push -u origin session/YYYY-MM-DD
gh pr create --base main --title "..." --body "..."
```

Branch-navnekonvensjon:
- `session/YYYY-MM-DD` — vanlig oppdateringsøkt (episoder, rydding)
- `feature/beskrivelse` — ny funksjonalitet i HTML eller skript

**PR-regler (Claude):**
- Sjekk alltid `gh pr list` og `git status` før ny branch eller PR opprettes
- Ikke opprett ny branch for hver småendring — samle relaterte endringer på én branch
- CLAUDE.md-oppdatering skal alltid inkluderes i samme PR som feature-endringen
- Ny session-branch opprettes ved starten av hver arbeidsdag

## Workflow

**GitHub Actions (automatisk, daglig kl. 11:00):**
1. `update_podcasts.py` henter nye episoder → legger dem i `pending_episodes.csv` → committer

**Lokalt (manuell gjennomgang):**
1. `git pull` — hent oppdatert `pending_episodes.csv`
2. `python rate_episodes.py` — fjerner åpenbar ikke-AI (score=0 → rejected); resten beholdes i pending med Rating=0
3. Åpne `pending_episodes.csv` og sett rating manuelt:
   - **4–6**: behold (sett passende rating, fyll inn Host(s), Guest(s), Main Topic(s), Tags)
   - **1–3**: avvis (flyttes til rejected av approve-scriptet)
   - **0**: utsett til neste gjennomgang
4. `python approve_episodes.py` — rating 4–6 → hoved-CSV, rating 1–3 → rejected, rating 0 → blir i pending
5. `git add AI_KI_Podcasts_2026.csv pending_episodes.csv rejected_episodes.csv`
6. `git commit -m "..."` og `git push`
7. Åpne `https://cathrinei.github.io/AIPodcastClaude/` — siden lastes automatisk med ny data

**Legge til ny podcast:**
- Legg til RSS-feed i `FEEDS`-dicten i `update_podcasts.py`
- Legg til i `PURE_AI_PODCASTS` i `rate_episodes.py` hvis det er en ren AI-podcast

**Sjekk duplikater i hoved-CSV:**
`python3 -c "import csv; rows=list(csv.reader(open('AI_KI_Podcasts_2026.csv',encoding='utf-8')))[1:]; seen={}; [print(f'DUP: {r[0]} – {r[1][:60]}') or seen.update({(r[0].lower(),r[1].lower()):1}) for r in rows if (r[0].lower(),r[1].lower()) in seen]"`
