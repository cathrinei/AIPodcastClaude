# AIPodcastClaude – Project Context

## Purpose
This project collects and curates podcast episodes on artificial intelligence (AI / KI / kunstig intelligens), including the sub-topic of vibe coding, published in 2026. Both Norwegian-language and English-language podcasts are in scope.

## Files
- `AI_KI_Podcasts.csv` — master data, one row per episode (kun godkjente episoder, rating 4–6)
- `AI_KI_Podcasts.html` — interactive table with filtering, sorting, stats, CSV import
- `index.html` — redirect fra rot-URL til `AI_KI_Podcasts.html` (GitHub Pages)
- `pending_episodes.csv` — staging-fil: nye episoder som venter på vurdering (12 kolonner inkl. Description)
- `update_podcasts.py` — RSS fetcher; legger nye episoder i `pending_episodes.csv`, ikke hoved-CSV
- `rate_episodes.py` — filtrerer åpenbar ikke-AI fra pending (score=0 → rejected); setter ingen rating
- `auto_rate.py` — setter rating og metadata automatisk via GitHub Models (gpt-4o-mini); kjøres av GitHub Actions etter rate_episodes.py; fyller inn Host(s), Guest(s), Main Topic(s), Tags, Rating, Rating Notes for alle rating=0-episoder i pending; godkjente (4–6) flyttes til hoved-CSV, avviste (1–3) til rejected
- `approve_episodes.py` — manuell override: flytter manuelt ratede episoder fra pending til hoved-CSV
- `show_pending.py` — viser pending_episodes.csv i lesbar form i terminalen; kjøres lokalt
- `sync_html.py` — synkroniserer det innebygde `data[]`-arrayet i HTML-en med CSV-en
- `archive_episodes.py` — flytter episoder eldre enn 3 måneder fra hoved-CSV til `AI_KI_Podcasts_arkiv.csv`; kjøres daglig av GitHub Actions etter `auto_rate.py`; cutoff = rullerende daglig (`date.today() - relativedelta(months=3)` fra `python-dateutil`)
- `AI_KI_Podcasts_arkiv.csv` — arkiv-CSV: episoder eldre enn 3 måneder; identisk kolonneformat som hoved-CSV; lastes runtime av HTML ved klikk på «Vis arkiv»-knappen
- `rejected_episodes.csv` — denylist of already-reviewed non-AI episodes; prevents re-fetching noise
- `failed_attempts.csv` — sporer API-feil per episode (Podcast Name, Episode Title, Attempts); episoder som feiler 3 ganger auto-forkastes til rejected_episodes.csv

## Live URL
`https://cathrinei.github.io/AIPodcastClaude/` — serves the latest committed HTML + CSV automatically. GitHub Actions updates the CSV daily at 23:00 CEST; Pages rebuilds on every push to `main`.

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

## Key findings (Jan 2026 – 28.04.26)
- **180 episodes** across **27 shows** (133 English, 47 Norwegian) — 180 rated (4–6)
- **Vibe coding** was a dominant cross-show theme — tagged across multiple series
- **OpenClaw** (formerly Clawdbot/Moltbot) emerged as a major cross-show topic — 10+ episodes tagged
- **Top-rated English episodes (6/6):** Latent Space × 5, Lex Fridman #490 + #491, No Priors (Karpathy), TWIML × 2 — 10 total
- **Best Norwegian source:** AI-Snakk — weekly episodes Jan–Apr, consistent quality, Norwegian AI news with local relevance
- **Norwegian sources:** AI Forklart (Niclas Kvanvig & Celine Haaland-Johansen), Heis, KI til Kaffen, Shifter, Kode24-podkasten
- **Anthropic vs. Pentagon**, **SaaSpocalypse** and **OpenClaw** were recurring cross-show news events

## HTML – tekniske noter

- `data[]`-arrayet i HTML er en innebygd kopi av CSV — alltid oppdater CSV først, kjør deretter `sync_html.py`
- På GitHub Pages lastes CSV automatisk via `fetch('./AI_KI_Podcasts.csv')` ved sidestart og erstatter `data[]`; faller stille tilbake til innebygd array ved `file://` eller nettverksfeil
- `sync_html.py` bruker regex til å erstatte hele `const data = [...]`-blokken i HTML-filen
- «Last inn CSV»-knappen er skjult (`style="display:none"`) — fjern attributtet for å aktivere manuell fallback
- Filter-rad (én linje): Søk · Språk · Podkast · Min. karakter · Favoritter · Nullstill · Vis arkiv. «Del», «Eksporter CSV» og «Siste 3 mnd» er skjult (`display:none`) men beholdt i DOM for JS
- Header-subtitle viser rullerende 3-månedersperiode beregnet i JS: `today - 3 måneder` → `today`, format `dd.mm.yy – dd.mm.yy`
- Tags whitelisted via `tagMeta`-objekt — ukjente tag-verdier ignoreres; aktive tags: `vibe`, `openclaw`, `agents`
- `safeUrl()` blokkerer ikke-HTTP(S)-URLer for å hindre `javascript:`-injeksjon
- CSP: `default-src 'none'; style-src 'unsafe-inline'; script-src 'unsafe-inline'; connect-src 'self'`
- Søk er fuzzy: eksakt substring-match først, deretter subsequence-fallback (f.eks. `"krpthy"` → `"Karpathy"`)
- Uraterte episoder (Rating=0) vises som **N/A** og passerer alltid gjennom ratingfilteret
- WCAG AA: alle kjente problemer er fikset — kontrast, ARIA-roller, `aria-sort`, `aria-pressed`, `:focus-visible`
- **`<main>`-landmark:** hoved-innholdet (`.summary` → `#cardList`) er wrappert i `<main>`; `#backToTop` (fixed-positioned) er utenfor `<main>`
- **`<meta name="description">`:** SEO-metatag lagt til i `<head>` — beskriver siden for søkemotorer
- **`--no-tags` kontrast:** endret fra `#767676` (3.99:1 på hvit — FAILS WCAG AA) til `#5f5f5f` (5.1:1 — PASSES); dark mode `#8a94b8` beholdes uendret
- **Mobilbrekkpunkter:** `(hover:none)` touch-hint, `≤900px` redusert padding, `≤600px` kortlayout (tabell skjult), `≤400px` kompakt fontstørrelse
- **Kortlayout (≤600px):** tabellen erstattes av `#cardList .ep-card`-elementer; `.card-list` vises, `.table-wrap` skjules; kortene viser emner (`card-topics`) i kursiv under vertsnavn
- **Sortering på mobil:** `#mobileSortSelect` (skjult på desktop via `.mobile-sort-label { display: none }`); synkroniseres med `sort`-objektet; `sortTable()` kaller `syncMobileSortSelect()` for å holde desktop- og mobilsortering i sync
- **`setToggleBtn(btn, active, labelOn?, labelOff?)`** — felles hjelpefunksjon for toggle-knapper; setter `.active`-klasse, `aria-pressed` og valgfritt `innerHTML`; brukes av `favFilterBtn`, `archiveBtn`, `recentBtn` i click-handlers, `resetFilters()` og `applyUrlParams()`
- **`FILTER_DEFS`** — éngangs-definisjon av alle URL-synkroniserte filtre (`search`, `lang`, `rating`, `tag`, `favs`, `recent`, `podcast`); hvert filter har `param`, `default`, `get()` og `set(v)`; `afterBuild: true` på `podcast` sikrer at dropdown er populert før verdien settes; `buildShareUrl()` og `applyUrlParams()` itererer begge over denne listen — nytt filter = én ny rad
- **`buildEpisodeUrl(podcast, title)`** — bygger direktelenke til én episode via `?search=title&podcast=podcast`; bruker eksisterende `FILTER_DEFS`-parametere uten ny parameterlogikk; kalles fra `.ep-share-btn`-handler
- **`.ep-share-btn`** — 🔗-ikon per episode; i tabellen gruppert med `fav-btn` i ★-kolonnen (`white-space:nowrap`), i mobilkort gruppert med `fav-btn` i en `flex`-span med `margin-left:auto`; klikk kopierer `buildEpisodeUrl()`-URL til utklippstavlen og viser ✓ i 1,5 sek; event delegation på `document`
- **`label::after`-chevron på mobil:** labels får `flex-direction: column` (tekst over select), så chevron-pilen bruker `bottom: 0.6rem` i stedet for `top: 50%` for å sentrere i select-feltet
- **Header på mobil:** beholder `flex-direction: row; justify-content: space-between` — ikke `column` med negativ margin
- **Arkivvisning:** arkiv-rader vises med varm amber-bakgrunn (`#fffbeb`/`#1c150a`); brun skillerrad (`tr.archive-divider` / `.card-archive-divider`) skilles inn automatisk i `renderTable()` ved første arkivrad; `#archiveBtn[aria-pressed="true"]` har mørkere amber-aktiv-stil; row count viser «X av Y episoder + Z arkiverte»

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
- **GitHub Actions-logg**: bruker `::group::`, `::notice::`, `::warning::`, `::error::` workflow-kommandoer for strukturert logg
  - Tre sammenleggbare seksjoner: «Sjekker N feeder», «Nye episoder», «Feil ved henting»
  - `::notice::` viser sluttoppsummering øverst i jobben («N nye episoder — klar for gjennomgang»)
  - `::error::` markerer feeder som ikke svarer (rødt i GitHub UI)
  - `::warning::` ved mulige duplikater (gult i GitHub UI)
  - `is_gha()` sjekker `GITHUB_ACTIONS`-miljøvariabelen — lokalt kjøring er uendret

### Metadata-utfylling
- **Dato**: alltid fra RSS `<pubDate>` — alltid `YYYY-MM-DD`
- **Host(s)**: hentes fra `HOST_OVERRIDES`-dict (18 kjente podkaster) → deretter RSS `itunes:author`/`dc:creator` på item- og kanalnivå (kun hvis det ser ut som et personnavn). `auto_rate.py` kan korrigere ved behov. Legg nye faste verter til i `HOST_OVERRIDES` i `update_podcasts.py`.
- **Guest(s)**: utledes fra tittelen via `extract_guest_from_title()` for utvalgte podcaster (`GUEST_FROM_TITLE`-settet). Verifiser alltid manuelt — kan gi feil.
- **`LANGUAGE_OVERRIDE`-dict**: tvinger riktig språk for norske podcaster der RSS-feeden mangler eller returnerer feil `<language>`-tag. Legg til nye norske podcaster her ved behov.

### Kjente fallgruver ved episodefetching
- **Gamle «siste kjente dato»**: Dersom en podcast ikke har blitt kjørt på en stund (eller har få episoder i CSV), kan `latest_date_per_podcast()` returnere en gammel dato — og hele gapet siden da hentes inn som «nye» episoder. Eksempel: Lex Fridman siste i CSV: 2026-02-12 → episodene #492–#495 (mars/april) fanget opp først ved neste kjøring.
- **RSS-titteldrift gir duplikater**: Noen feeder endrer tittelformatering over tid (em-strek vs bindestrek, apostrof-encoding, mellomrom vs bindestrek). `existing_keys` bruker eksakt match på `title.lower()`, så minimale titteldifferanser sniker seg gjennom som nye episoder. Løsning: kjør duplikatsjekk etter `update_podcasts.py` og fjern eventuelle dobbeltoppføringer manuelt.
- **TimeoutError krasjer jobben**: Python 3.12 kan kaste `TimeoutError` direkte (ikke pakket i `urllib.error.URLError`) ved treg feed. `fetch_feed()` fanger nå `(TimeoutError, OSError)` i tillegg til `HTTPError`/`URLError` — uten denne fiksen vil én treg feed stoppe hele kjøringen og ingen episoder skrives til pending.
- **No Priors-feeden henter inn StarTalk-episoder**: RSS-feeden for No Priors inneholder av og til episoder fra Neil deGrasse Tysons StarTalk-podcast (f.eks. «Cosmic Queries – Take Me To Your Leader»). Disse er ikke AI-relevante — avvis dem med rating 1 ved gjennomgang.

## rate_episodes.py – tekniske noter
- Kjøres lokalt etter `git pull`; leser `pending_episodes.csv` og filtrerer åpenbar ikke-AI
- **Setter ingen rating** — det gjøres manuelt av bruker etterpå
- **Pure AI podcasts** (`PURE_AI_PODCASTS` set): skip AI check, beholdes alltid i pending
- **Mixed podcasts**: `ai_score()` sjekker tittel (høyere vekt) og description (kolonne 12) for `STRONG_AI` / `MEDIUM_AI` keywords
  - score 0 → avvis automatisk (→ `rejected_episodes.csv`, fjernes fra pending)
  - score > 0 → beholdes i pending med Rating=0 for manuell vurdering
- Output viser antall beholdt og antall avvist med titler

## auto_rate.py – tekniske noter
- Kjøres automatisk av GitHub Actions etter `rate_episodes.py`; kan også kjøres lokalt med `GITHUB_TOKEN`
- Kaller `gpt-4o-mini` via GitHub Models (`https://models.inference.ai.azure.com`)
- `SYSTEM_PROMPT` inneholder karakterskala, vertsnavn og tag-definisjoner; svar alltid JSON
- **`user_msg` skal kun inneholde data** (podcast, tittel, språk, dato, lenke, beskrivelse) — ingen instruksjoner om format eller respons; instruksjonstekst i user-meldingen trigger Azures jailbreak-filter
- Beskrivelse fra RSS (kolonne 12) inkluderes alltid i prompten for bedre ratingkvalitet
- **Azure content_filter-feil**: ved `content_filter`-feil (kode 400) prøves automatisk retry uten beskrivelse — RSS-teksten kan inneholde ord som trigger Azures filter
- `failed_attempts.csv` sporer feil per episode; etter `MAX_ATTEMPTS` (3) auto-forkastes episoden til `rejected_episodes.csv`

## approve_episodes.py – tekniske noter
- Kjøres lokalt etter at rating er satt manuelt i `pending_episodes.csv`
- Leser alle rader fra `pending_episodes.csv` og behandler etter rating:
  - **Rating 4–6** → `row[:11]` (Description-kolonnen strippes) legges til i `AI_KI_Podcasts.csv`
  - **Rating 1–3** → legges til i `rejected_episodes.csv` (kun Podcast Name + Episode Title)
  - **Rating 0** → beholdes i `pending_episodes.csv` til neste gjennomgang
- Skriver oppdatert `AI_KI_Podcasts.csv` (eksisterende rader + nye godkjente)
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

**Episodeoppdateringer (CSV + HTML)** — commit og push direkte til `main`:
```bash
git checkout main && git pull
# ... rate og godkjenn episoder ...
git add AI_KI_Podcasts.csv AI_KI_Podcasts.html pending_episodes.csv rejected_episodes.csv
git commit -m "session: kort beskrivelse"
git push
```

**Kode- og feature-endringer** — alltid branch + PR:
```bash
git checkout main && git pull
git checkout -b feature/kort-beskrivelse

# Etter endringer
git add <filer>
git commit -m "feat/fix/chore: beskrivelse"
git push -u origin feature/kort-beskrivelse
gh pr create --base main --title "..." --body "..."
```

Branch-navnekonvensjon:
- `feature/beskrivelse` — ny funksjonalitet i HTML eller skript
- `fix/beskrivelse` — bugfiks
- `chore/beskrivelse` — rydding, avhengigheter, konfig

**Regler (Claude):**
- **Episodeoppdateringer** (kun `AI_KI_Podcasts.csv`, `AI_KI_Podcasts.html`, `pending_episodes.csv`, `rejected_episodes.csv`, `failed_attempts.csv`) → direkte push til `main`
- **Alt annet** (HTML-kode, skript, GitHub Actions, CLAUDE.md alene) → branch + PR
- **CLAUDE.md** oppdateres i samme commit/PR som feature-endringen — ingen unntak
- Sjekk alltid `git branch` før commit — aldri commit uten å bekrefte at du er på riktig branch

**Opprydding av branches og PRs (ukentlig):**
Mergede branches hoper seg opp raskt. Claude skal minne om dette ved oppstart av en arbeidsøkt hvis det har gått mer enn 7 dager siden forrige opprydding.
Sjekk og slett med:
```bash
# Slett alle mergede remote branches unntatt main og aktiv branch
git branch -r | grep "origin/" | grep -v "HEAD\|main\|$(git branch --show-current)" | sed 's/origin\///' | xargs -I{} git push origin --delete {}

# Slett tilsvarende lokale branches
git branch --merged main | grep -v "main\|$(git branch --show-current)" | xargs git branch -d
```

## Workflow

**GitHub Actions (automatisk, daglig kl. 23:00):**
1. `update_podcasts.py` henter nye episoder → legger dem i `pending_episodes.csv`
2. `rate_episodes.py` kjøres automatisk — filtrerer åpenbar ikke-AI (score=0 → `rejected_episodes.csv`); resten beholdes i pending
3. `auto_rate.py` kjøres automatisk — setter rating og metadata (Host, Guest, Topics, Tags, Rating Notes) via gpt-4o-mini; godkjente (4–6) → `AI_KI_Podcasts.csv`; avviste (1–3) → `rejected_episodes.csv`
4. `archive_episodes.py` kjøres automatisk — episoder eldre enn 3 måneder flyttes fra `AI_KI_Podcasts.csv` til `AI_KI_Podcasts_arkiv.csv`
5. `sync_html.py` synkroniserer HTML med oppdatert CSV
6. Committer `AI_KI_Podcasts.csv`, `AI_KI_Podcasts.html`, `AI_KI_Podcasts_arkiv.csv`, `pending_episodes.csv`, `rejected_episodes.csv`, `failed_attempts.csv` hvis endret
7. Skriver kjøreoppsummering til `$GITHUB_STEP_SUMMARY` — vises som «update summary» under hver workflow-kjøring i GitHub; inneholder output fra alle 4 skript (fetch, filter, auto-rate, arkivering)

**GHA tekniske noter:**
- Script-output fanges med `2>&1 | tee /tmp/<skript>_output.txt` og skrives til `$GITHUB_STEP_SUMMARY` i siste steg
- Commit-steget bruker `git pull --rebase` før `git push` for å unngå push-avvisning ved samtidige commits til `main`
- Actions-versjoner: `actions/checkout@v5`, `actions/setup-python@v6` (Node.js 24-native — ingen `FORCE_JAVASCRIPT_ACTIONS_TO_NODE24` workaround)

**Lokalt (manuell override ved behov):**
1. `git pull` — hent oppdatert `pending_episodes.csv`
2. `python show_pending.py` — inspiser episoder som venter
3. Rediger `pending_episodes.csv` manuelt (sett rating 4–6 eller 1–3)
4. `python approve_episodes.py` — rating 4–6 → hoved-CSV, rating 1–3 → rejected, rating 0 → blir i pending
5. `python sync_html.py` — synkroniserer HTML-ens innebygde `data[]`-array med CSV-en
6. `git add AI_KI_Podcasts.csv AI_KI_Podcasts.html pending_episodes.csv rejected_episodes.csv`
7. `git commit -m "..."` og `git push`

**Kjøre auto_rate.py lokalt (med GITHUB_TOKEN):**
```bash
export GITHUB_TOKEN=<ditt_token>
python auto_rate.py
```

**Kjøre archive_episodes.py lokalt:**
```bash
python archive_episodes.py
```

**Legge til ny podcast:**
- Legg til RSS-feed i `FEEDS`-dicten i `update_podcasts.py`
- Legg til i `PURE_AI_PODCASTS` i `rate_episodes.py` hvis det er en ren AI-podcast

**Sjekk duplikater i hoved-CSV:**
`python3 -c "import csv; rows=list(csv.reader(open('AI_KI_Podcasts.csv',encoding='utf-8')))[1:]; seen={}; [print(f'DUP: {r[0]} – {r[1][:60]}') or seen.update({(r[0].lower(),r[1].lower()):1}) for r in rows if (r[0].lower(),r[1].lower()) in seen]"`
