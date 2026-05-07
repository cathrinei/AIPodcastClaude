"""
auto_rate.py — Automatisk vurdering av uraterte episoder (Rating=0) via GitHub Models.

Bruk:
  python auto_rate.py

Krever:
  pip install openai
  Miljøvariabel GITHUB_TOKEN satt (tilgjengelig automatisk i GitHub Actions)

Hva skriptet gjør:
  1. Leser pending_episodes.csv og finner episoder med Rating=0
  2. Kaller gpt-4o-mini via GitHub Models for å vurdere hver episode
  3. Episoder med rating 4-6 legges til AI_KI_Podcasts.csv (uten Description-kolonnen)
  4. Episoder med rating 1-3 skrives til rejected_episodes.csv
  5. Episoder uten gyldig respons telles i failed_attempts.csv;
     etter MAX_ATTEMPTS mislykkede forsøk sendes de til rejected_episodes.csv
  6. pending_episodes.csv oppdateres med kun gjenværende rating=0-episoder
"""

import csv
import json
import os
import sys

from openai import OpenAI

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE_DIR      = os.path.dirname(os.path.abspath(__file__))
PENDING_PATH  = os.path.join(BASE_DIR, "pending_episodes.csv")
CSV_PATH      = os.path.join(BASE_DIR, "AI_KI_Podcasts.csv")
REJECTED_PATH = os.path.join(BASE_DIR, "rejected_episodes.csv")
FAILED_PATH   = os.path.join(BASE_DIR, "failed_attempts.csv")
MAX_ATTEMPTS  = 3

SYSTEM_PROMPT = """Du er en ekspert på podkaster om kunstig intelligens (AI/KI). Din oppgave er å vurdere om en podkastepisode handler om AI og gi den en karakter.

Karakterskala (1–6):
6 = Eksepsjonelt: Dypdykk i AI, ekspertgjester/-verter, høy faglig eller praktisk verdi
5 = Svært nyttig: Solid AI-innhold, tydelig fokus, pålitelig og informativt
4 = Nyttig: Relevant AI-dekning; kan være overflatenivå eller AI er ett av flere temaer
3 = Delvis relevant: Berører AI, men primærfokus er noe annet
2 = Marginal: Svak kobling til AI
1 = Ikke relevant: Handler ikke om AI

Kjente verter (bruk disse navnene eksakt):
- Latent Space: Shawn Wang, Alessio Fanelli
- Hard Fork (NYT): Kevin Roose, Casey Newton
- The Cognitive Revolution: Nathan Labenz
- No Priors: Sarah Guo, Elad Gil
- AI-Snakk: Audun Kvitland Røstad
- AI Forklart: Niclas Kvanvig, Celine Haaland-Johansen
- Andre podkaster: utled fra beskrivelse eller la feltet stå tomt
- Bruk aldri podcastens navn, mediehus eller forkortelse (f.eks. WSJ, NYT, Bloomberg) som vertnavn — la heller stå tomt

Tagger (kun disse, kommaseparert; la stå tomt hvis ingen passer):
- vibe: vibe coding, AI-assistert programmering
- openclaw: OpenClaw (tidl. Clawdbot/Moltbot)
- agents: AI-agenter, agentisk AI, autonome AI-systemer

Språk — følg dette strengt:
- Norske episoder (Language=Norwegian): skriv main_topics og rating_notes på norsk (bokmål)
- Engelske episoder (Language=English): skriv main_topics og rating_notes på engelsk
- Bruk alltid korrekte tegn: æ, ø, å — aldri erstatt dem med ae, oe, aa eller utelat dem

Viktig: "AI" betyr kunstig intelligens, ikke Amnesty International. "KI" betyr kunstig intelligens, ikke firmanavnforkortelse. Episoder som handler om noe annet enn AI, for eksempel nyheter, politikk, økonomi, sport, får karakter 1–2.

Svar alltid med gyldig JSON, ingen annen tekst:

{
  "host": "vertnavn eller tom streng",
  "guest": "fullt navn på gjest(er), kommaseparert — søk aktivt i BÅDE tittel og beskrivelse etter mønstre som 'with [Navn]', 'w/ [Navn]', 'featuring [Navn]', 'interview with [Navn]', '[Navn] joins', '[Navn] on [emne]' — la stå tomt KUN hvis ingen konkret person er nevnt som gjest",
  "main_topics": "korte emneord, kommaseparert",
  "rating": <heltall 1-6>,
  "rating_notes": "1–2 setninger som begrunner karakteren — fokuser på innholdet (hva tas opp, hvilken verdi har det), ikke på gjestens status eller personlighet; unngå fraser som 'fremragende gjest', 'gjestevennlig', 'eksepsjonell gjest' o.l.; ikke begynn med 'The episode', 'This episode', 'Episoden' eller 'Denne episoden' — start heller med hva som faktisk diskuteres, hvem som deltar, eller hva som gjør episoden verdifull",
  "tags": "kommaseparerte tagger eller tom streng"
}"""


def normalize(s: str) -> str:
    return s.strip().lower()


def load_failed_attempts() -> dict[tuple[str, str], int]:
    if not os.path.exists(FAILED_PATH):
        return {}
    result: dict[tuple[str, str], int] = {}
    with open(FAILED_PATH, encoding="utf-8", newline="") as f:
        for r in csv.reader(f):
            if len(r) >= 3 and r[0] != "Podcast Name":
                try:
                    result[(normalize(r[0]), normalize(r[1]))] = int(r[2])
                except ValueError:
                    pass
    return result


def save_failed_attempts(attempts: dict[tuple[str, str], int]) -> None:
    with open(FAILED_PATH, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Podcast Name", "Episode Title", "Attempts"])
        for (podcast, title), count in attempts.items():
            w.writerow([podcast, title, count])


def append_rejected(rows: list[list[str]]) -> None:
    existing: set[tuple[str, str]] = set()
    if os.path.exists(REJECTED_PATH):
        with open(REJECTED_PATH, encoding="utf-8", newline="") as f:
            for r in csv.reader(f):
                if len(r) >= 2 and r[0] != "Podcast Name":
                    existing.add((normalize(r[0]), normalize(r[1])))

    new_entries = [r for r in rows if (normalize(r[0]), normalize(r[1])) not in existing]
    if not new_entries:
        return

    write_header = not os.path.exists(REJECTED_PATH) or os.path.getsize(REJECTED_PATH) == 0
    with open(REJECTED_PATH, "a", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        if write_header:
            w.writerow(["Podcast Name", "Episode Title"])
        for row in new_entries:
            w.writerow([row[0], row[1]])


def append_approved(rows: list[list[str]]) -> None:
    with open(CSV_PATH, "a", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        for row in rows:
            w.writerow(row[:11])


def _handle_failure(
    failed_attempts: dict, key: tuple, row: list, i: int,
    reason: str, rejected_rows: list, rows_to_remove: set,
) -> bool:
    attempts = failed_attempts.get(key, 0) + 1
    if attempts >= MAX_ATTEMPTS:
        print(f"    FORKASTES  {reason}, {attempts} forsøk — sendes til rejected_episodes.csv\n")
        rejected_rows.append(row)
        rows_to_remove.add(i)
        failed_attempts.pop(key, None)
        return True
    print(f"    VENTER  {reason} — forsøk {attempts}/{MAX_ATTEMPTS}, re-prøves neste kjøring\n")
    failed_attempts[key] = attempts
    return False


def _build_user_msg(podcast: str, title: str, language: str,
                    pub_date: str, link: str, description: str) -> str:
    parts = [
        f"Podcast: {podcast}",
        f"Tittel: {title}",
        f"Språk: {language}",
        f"Publisert: {pub_date}",
        f"Lenke: {link}",
    ]
    if description:
        parts.append(f"Beskrivelse: {description}")
    return "\n".join(parts)


def _call_api(client: OpenAI, user_msg: str) -> dict | None:
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_msg},
        ],
        max_tokens=512,
    )
    text = (response.choices[0].message.content or "").strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
        text = text.strip()
    return json.loads(text)


def rate_episode(
    client: OpenAI, podcast: str, title: str,
    language: str, pub_date: str, link: str, description: str,
) -> dict | None:
    """Kaller API med beskrivelse; ved content_filter-feil prøves uten beskrivelse."""
    user_msg = _build_user_msg(podcast, title, language, pub_date, link, description)
    try:
        return _call_api(client, user_msg)
    except json.JSONDecodeError as e:
        print(f"WARN JSON-feil for '{title[:60]}': {e}")
        return None
    except Exception as e:
        err_str = str(e)
        if "content_filter" in err_str and description:
            # Prøv på nytt uten beskrivelse — Azure-filteret reagerte på RSS-teksten
            print(f"WARN Content-filter på beskrivelse, prøver uten for '{title[:60]}'")
            try:
                return _call_api(client, _build_user_msg(
                    podcast, title, language, pub_date, link, ""))
            except json.JSONDecodeError as e2:
                print(f"WARN JSON-feil (retry) for '{title[:60]}': {e2}")
                return None
            except Exception as e2:
                print(f"WARN API-feil (retry) for '{title[:60]}': {e2}")
                return None
        print(f"WARN API-feil for '{title[:60]}': {e}")
        return None


def read_csv(path: str) -> tuple[list[str], list[list[str]]]:
    if not os.path.exists(path):
        return [], []
    with open(path, encoding="utf-8", newline="") as f:
        reader = csv.reader(f)
        header = next(reader, [])
        rows = list(reader)
    return header, rows


def main() -> None:
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        print("FEIL: Miljøvariabel GITHUB_TOKEN er ikke satt.")
        sys.exit(1)

    client = OpenAI(
        base_url="https://models.inference.ai.azure.com",
        api_key=token,
    )

    pending_header, pending_rows = read_csv(PENDING_PATH)
    if not pending_header:
        print("OK pending_episodes.csv finnes ikke eller er tom.")
        return

    unrated = [(i, r) for i, r in enumerate(pending_rows)
               if len(r) > 7 and r[7].strip() == "0"]

    if not unrated:
        print("OK Ingen uraterte episoder i pending_episodes.csv.")
        return

    print(f"OK Fant {len(unrated)} uraterte episode(r) — starter vurdering...\n")

    approved_rows: list[list[str]] = []
    rejected_rows: list[list[str]] = []
    rows_to_remove: set[int] = set()
    failed_attempts = load_failed_attempts()
    failed_initial = dict(failed_attempts)
    auto_rejected = 0

    for i, row in unrated:
        while len(row) < 12:
            row.append("")

        podcast     = row[0]
        title       = row[1]
        language    = row[2]
        pub_date    = row[3]
        link        = row[10]
        description = row[11]
        key         = (normalize(podcast), normalize(title))

        print(f"  → [{pub_date}] {podcast[:30]} — {title[:60]}")

        result = rate_episode(client, podcast, title, language, pub_date, link, description)
        if result is None:
            if _handle_failure(failed_attempts, key, row, i, "Ingen gyldig respons",
                               rejected_rows, rows_to_remove):
                auto_rejected += 1
            continue

        rating_raw = result.get("rating", 0)
        try:
            rating = int(rating_raw)
        except (ValueError, TypeError):
            rating = 0

        if rating <= 0 or rating > 6:
            if _handle_failure(failed_attempts, key, row, i, f"Ugyldig rating ({rating_raw})",
                               rejected_rows, rows_to_remove):
                auto_rejected += 1
            continue

        failed_attempts.pop(key, None)
        rows_to_remove.add(i)

        if rating <= 3:
            print(f"    FJERNES  Rating {rating} — {result.get('rating_notes', '')[:80]}\n")
            rejected_rows.append(row)
        else:
            row[4] = row[4] or result.get("host", "") or ""
            row[5] = result.get("guest", row[5]) or row[5]
            row[6] = result.get("main_topics", row[6]) or row[6]
            row[7] = str(rating)
            row[8] = result.get("rating_notes", "")
            row[9] = result.get("tags", "")
            approved_rows.append(row)
            print(f"    OK  Rating {rating} — {result.get('rating_notes', '')[:80]}\n")

    # Skriv godkjente episoder til hoved-CSV (uten Description-kolonnen)
    if approved_rows:
        append_approved(approved_rows)

    # Skriv avviste til rejected_episodes.csv
    if rejected_rows:
        append_rejected(rejected_rows)

    # Oppdater pending_episodes.csv — fjern alle behandlede rader
    remaining = [r for i, r in enumerate(pending_rows) if i not in rows_to_remove]
    with open(PENDING_PATH, "w", encoding="utf-8", newline="") as f:
        csv.writer(f).writerows([pending_header] + remaining)

    if failed_attempts != failed_initial:
        save_failed_attempts(failed_attempts)

    n_rejected = len(rejected_rows) - auto_rejected
    print(f"OK {len(approved_rows)} episoder godkjent (rating 4–6) → AI_KI_Podcasts.csv")
    print(f"OK {n_rejected} episoder avvist (rating 1–3) → rejected_episodes.csv")
    if auto_rejected:
        print(f"OK {auto_rejected} episoder forkastet etter {MAX_ATTEMPTS} mislykkede forsøk")
    print(f"OK {len(remaining)} episoder igjen i pending_episodes.csv")


if __name__ == "__main__":
    main()
