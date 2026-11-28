"""Build the review packets for the clinician (C-8) and the Spanish reviewer (C-7).

Everything is generated from the code and message files that families would see, so
the packets cannot drift from what Serein actually says:

    uv run python scripts/build_review_packets.py

writes docs/review/clinician_packet.html, docs/review/spanish_review.html and
docs/review/spanish_review.csv. To make PDFs to email, open each .html in a browser
and print to PDF (or run the same command with --pdf, which needs Playwright).
"""

from __future__ import annotations

import argparse
import csv
import html
import re
from pathlib import Path

from serein.personal.action_plan import choose_zone, load_messages, render, render_sms

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "review"

# Three example days for a fictional child. Numbers are illustrative, chosen so each
# zone appears; the zone shown is the one the real rule picks for these inputs.
EXAMPLES = [
    # pm median, upper end of range, child's risk, same child with clean air
    ("green", 8.0, 15.0, 0.10, 0.09),
    ("yellow", 40.0, 70.0, 0.22, 0.12),
    ("red", 66.0, 155.0, 0.63, 0.14),
]
CHILD = "Maya"
CATEGORY_INDEX = {"green": 0, "yellow": 2, "red": 3}

CSS = """
body { font: 11pt/1.45 -apple-system, "Segoe UI", Helvetica, Arial, sans-serif; color: #111;
       max-width: 46rem; margin: 2rem auto; padding: 0 1rem; }
h1 { font-size: 20pt; margin: 0 0 .3rem; } h2 { font-size: 14pt; margin: 1.6rem 0 .4rem;
  border-bottom: 1px solid #ccc; padding-bottom: .2rem; } h3 { font-size: 11.5pt; margin: 1rem 0 .3rem; }
.note { color: #555; font-size: 10pt; } table { border-collapse: collapse; width: 100%; font-size: 9.5pt; }
th, td { border: 1px solid #bbb; padding: .3rem .4rem; text-align: left; vertical-align: top; }
th { background: #f2f2f2; } pre { white-space: pre-wrap; font: 10pt/1.4 inherit; background: #fafafa;
  border-left: 4px solid var(--z, #999); padding: .5rem .7rem; margin: .3rem 0 .8rem; }
.green { --z: #2e9e4f; } .yellow { --z: #d9a400; } .red { --z: #d6333a; }
.blank { height: 3.2rem; } .page { page-break-before: always; }
@media print { body { margin: 0 auto; } }
"""


def page(title: str, body: str) -> str:
    return (f"<!doctype html><html lang=\"en\"><head><meta charset=\"utf-8\">"
            f"<title>{html.escape(title)}</title><style>{CSS}</style></head><body>{body}</body></html>")


def esc(s: str) -> str:
    return html.escape(s)


def plans(language: str) -> str:
    out = []
    for expected, pm, hi, risk, base in EXAMPLES:
        zone, reason = choose_zone(risk, base, pm, hi)
        assert zone == expected, (zone, expected)
        full = render(zone, reason, CHILD, "tomorrow", pm, hi, risk, CATEGORY_INDEX[zone], language)
        sms = render_sms(zone, CHILD, "tomorrow", pm, CATEGORY_INDEX[zone], language)
        out.append(f"<h3>{zone.upper()}: full plan</h3><pre class=\"{zone}\">{esc(full)}</pre>"
                   f"<h3>{zone.upper()}: text message</h3><pre class=\"{zone}\">{esc(sms)}</pre>")
    return "".join(out)


def priors_table() -> str:
    text = (ROOT / "docs" / "METHODS.md").read_text(encoding="utf-8")
    block = text.split("### Priors", 1)[1]
    rows = [line for line in block.splitlines() if line.startswith("|")]
    cells = [[c.strip() for c in r.strip("|").split("|")] for r in rows if not set(r) <= set("|- ")]
    head, body = cells[0], cells[1:]
    strip = lambda s: re.sub(r"\*(.+?)\*", r"\1", s)
    th = "".join(f"<th>{esc(strip(h))}</th>" for h in head)
    trs = "".join("<tr>" + "".join(f"<td>{esc(strip(c))}</td>" for c in r) + "</tr>" for r in body)
    return f"<table><tr>{th}</tr>{trs}</table>"


def clinician_packet() -> str:
    body = f"""
<h1>Serein: smoke-day asthma plans for review</h1>
<p class="note">Student project for the Conrad Challenge (Foothill High School, Pleasanton, CA).
Generated from the code on the date of printing. Maya is a made-up child and the numbers are
illustrative. Nothing here has been sent to a real family.</p>

<h2>What we are asking</h2>
<p>About 20 minutes, in writing. The five questions are on the last page; "fine" is a complete
answer. We will make every change you ask for or tell you why not.</p>

<h2>What Serein does</h2>
<p>It forecasts wildfire smoke (daily average PM2.5) for a family's neighborhood one to three
days ahead, with a range. For a child with asthma it turns tomorrow's forecast into a green,
yellow or red plan the evening before, in English or Spanish, by text message with a link to
the full plan. It never diagnoses, never changes medication, and always defers to the child's
own asthma action plan.</p>

<h2>How the zone is chosen</h2>
<table>
<tr><th>Rule</th><th>Zone</th></tr>
<tr><td>Forecast median "Unhealthy for Sensitive Groups" or worse (PM2.5 at or above 35.5 µg/m³),
or the upper end of the forecast range "Unhealthy" or worse</td><td>at least YELLOW</td></tr>
<tr><td>Forecast median "Very Unhealthy" or worse</td><td>RED</td></tr>
<tr><td>The child's own log: estimated chance of symptoms tomorrow at least 1.3 times, or 5
percentage points above, the same child on a clean-air day</td><td>at least YELLOW</td></tr>
<tr><td>The same, at least 2 times or 15 points above</td><td>RED</td></tr>
</table>
<p>The child's log can only make a plan stricter than the public guidance, never looser. The
1.3x / 5-point and 2x / 15-point cut-offs are our design choices and the main thing we would
like a clinician to judge. Only the smoke differs between "tomorrow" and the clean-air
comparison, so a cold or a high-pollen day by itself does not trigger a smoke warning.</p>

<h2>The evening check-in (six taps)</h2>
<ol>
<li>Any asthma symptoms today? none / mild / moderate / severe</li>
<li>Rescue (quick-relief) inhaler puffs today, not counting before exercise? 0 / 1-2 / 3-4 / 5+</li>
<li>Woke up at night because of asthma? yes / no</li>
<li>Time outdoors today? little (under 1 h) / some (1-3 h) / a lot (3 h+)</li>
<li>Has a cold or is sick? yes / no</li>
<li>Took daily controller medicine? yes / no / doesn't have one</li>
</ol>
<p>A "symptom day", the outcome the model learns, is any symptoms, any rescue puffs, or night
waking. The model is a Bayesian logistic regression that starts from published effect sizes
(next section) and updates them for each child as days are logged. So far it has been tested
only on 300 simulated children.</p>

<h2>The messages, in English</h2>
{plans("en")}

<h2 class="page">The same messages, in Spanish</h2>
<p class="note">A native-speaker review is a separate request; we include these so you can
flag anything medical.</p>
{plans("es")}

<h2 class="page">Starting assumptions (priors)</h2>
<p class="note">From docs/METHODS.md. Odds ratios per day; the model updates them for each
child.</p>
{priors_table()}

<h2 class="page">Review sheet</h2>
<p>Reviewer role and affiliation: ______________________ &nbsp; May we name you?
yes / role and affiliation only / anonymously / no</p>
<ol>
<li><b>Safety floor.</b> Plans can only be stricter than EPA's guidance for sensitive groups,
always say to follow the child's asthma action plan, and list emergency signs. Is anything
missing?<div class="blank"></div></li>
<li><b>Wording.</b> Is there any sentence you would not want a parent to read? Please mark it
and say why.<div class="blank"></div></li>
<li><b>Zone rules.</b> Do the yellow and red rules on page 1, including the 1.3x / 5-point and
2x / 15-point cut-offs, make clinical sense?<div class="blank"></div></li>
<li><b>Starting assumptions.</b> Is any effect size in the priors table implausible for
children?<div class="blank"></div></li>
<li><b>Check-in.</b> What would make a smoke-sensitivity estimate from the six-tap check-in
misleading? What should we never infer from it?<div class="blank"></div></li>
</ol>
"""
    return page("Serein: plans for clinical review", body)


def flatten(d, prefix=""):
    for k, v in d.items():
        key = f"{prefix}{k}"
        if isinstance(v, dict):
            yield from flatten(v, key + ".")
        elif isinstance(v, list):
            for i, item in enumerate(v, 1):
                yield f"{key}.{i}", str(item)
        else:
            yield key, str(v)


def spanish_rows() -> list[tuple[str, str, str]]:
    en, es = load_messages("en"), load_messages("es")
    skip = {"language", "review_status"}
    es_flat = dict(flatten(es))
    return [(k, v, es_flat.get(k, "(missing)")) for k, v in flatten(en) if k not in skip]


def spanish_sheet(rows) -> str:
    trs = "".join(f"<tr><td>{esc(k)}</td><td>{esc(e)}</td><td lang=\"es\">{esc(s)}</td><td></td></tr>"
                  for k, e, s in rows)
    body = f"""
<h1>Serein: Spanish messages for review</h1>
<p class="note">Student project for the Conrad Challenge. These are the messages a family would
receive, generated from <code>src/serein/personal/messages/</code>. Words in braces, such as
{{name}} and {{pm}}, are filled in automatically (the child's name, a number) and must stay as they
are. Category names follow EPA's official Spanish AQI names.</p>
<p>What we ask: does each Spanish line read naturally to a parent, say the same thing as the
English, and avoid anything confusing or alarming? Write any change in the last column; a blank
means fine. The same table is in <code>spanish_review.csv</code> for a spreadsheet.</p>
<p>Reviewer (first name or initials only): __________ &nbsp; Native language/variety: __________</p>
<table><tr><th>Key</th><th>English</th><th>Spanish now</th><th style="width:28%">Suggested change</th></tr>{trs}</table>
<h2>Full plans as a family would see them</h2>
{plans("es")}
"""
    return page("Serein: Spanish review", body)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--pdf", action="store_true", help="also print PDFs (needs Playwright)")
    args = ap.parse_args(argv)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "clinician_packet.html").write_text(clinician_packet(), encoding="utf-8")
    rows = spanish_rows()
    (OUT / "spanish_review.html").write_text(spanish_sheet(rows), encoding="utf-8")
    with open(OUT / "spanish_review.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["key", "english", "spanish_now", "suggested_change"])
        w.writerows([(k, e, s, "") for k, e, s in rows])
    print(f"wrote {OUT}/clinician_packet.html, spanish_review.html, spanish_review.csv ({len(rows)} lines)")
    if args.pdf:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            browser = p.chromium.launch()
            for name in ("clinician_packet", "spanish_review"):
                pg = browser.new_page()
                pg.goto((OUT / f"{name}.html").as_uri())
                pg.pdf(path=str(OUT / f"{name}.pdf"), format="Letter",
                       margin={"top": "0.6in", "bottom": "0.6in", "left": "0.5in", "right": "0.5in"})
            browser.close()
        print("PDFs written")


if __name__ == "__main__":
    main()
