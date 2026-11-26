"""Count the words in each Innovation Brief section against the Conrad limits.

    python3 scripts/check_brief.py                 # docs/drafts/innovation_brief.md
    python3 scripts/check_brief.py path/to/brief.md

`[TEAM ...]` notes are not counted because they are removed before submitting. Markdown
marks (table bars, bold stars, link addresses) are not counted either. A word is anything
between spaces that contains a letter or a digit, which is how a plain text box counts.
The exit code is 1 when a section or the whole Brief is over its limit, so the Brief can
be checked the day it is submitted. Limits: 2026-27 Student Guide (docs/CONRAD.md).
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

LIMITS = {1: 150, 2: 150, 3: 300, 4: 750, 5: 450, 6: 300, 7: 300, 8: 150, 9: 300, 10: 150}
TOTAL_LIMIT = 3000
DEFAULT = Path(__file__).resolve().parents[1] / "docs" / "drafts" / "innovation_brief.md"

HEADING = re.compile(r"^## (\d+)\. (.+)$", re.MULTILINE)
TEAM_NOTE = re.compile(r"\[TEAM\b.*?\]", re.DOTALL)
LINK = re.compile(r"\[([^\]]*)\]\([^)]*\)")
TABLE_RULE = re.compile(r"^\|[-:| ]+\|\s*$", re.MULTILINE)


def count_words(text: str) -> int:
    text = TEAM_NOTE.sub(" ", text)
    text = LINK.sub(r"\1", text)
    text = TABLE_RULE.sub(" ", text)
    text = re.sub(r"[|*`#>]", " ", text)
    return sum(1 for token in text.split() if re.search(r"[0-9A-Za-zÀ-ÿµ]", token))


def sections(text: str) -> dict[int, tuple[str, str]]:
    """Map section number to (title, body). A section ends at the next `## ` or `---`."""
    found = {}
    matches = list(HEADING.finditer(text))
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        body = text[match.end() : end]
        for stop in ("\n## ", "\n---"):
            cut = body.find(stop)
            if cut != -1:
                body = body[:cut]
        found[int(match.group(1))] = (match.group(2).strip(), body)
    return found


def report(text: str) -> tuple[list[str], bool]:
    found = sections(text)
    lines, over, total = [], False, 0
    for number, limit in LIMITS.items():
        if number not in found:
            lines.append(f"{number:>2}  MISSING")
            over = True
            continue
        title, body = found[number]
        words = count_words(body)
        total += words
        open_slots = len(TEAM_NOTE.findall(body))
        flag = "OVER by " + str(words - limit) if words > limit else "ok"
        over = over or words > limit
        title = re.sub(r"\s*\(\d+ words\).*$", "", title)
        lines.append(f"{number:>2}  {words:>4} / {limit:<4} {flag:<12} {open_slots} open  {title}")
    flag = "OVER by " + str(total - TOTAL_LIMIT) if total > TOTAL_LIMIT else "ok"
    over = over or total > TOTAL_LIMIT
    lines.append(f"    {total:>4} / {TOTAL_LIMIT:<4} {flag}")
    return lines, over


def main(argv: list[str]) -> int:
    path = Path(argv[1]) if len(argv) > 1 else DEFAULT
    lines, over = report(path.read_text(encoding="utf-8"))
    print(f"{path}\n sec words  limit status       [TEAM] slots")
    print("\n".join(lines))
    return 1 if over else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
