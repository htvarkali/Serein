"""The Brief word counter (scripts/check_brief.py)."""

import importlib.util
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "check_brief.py"
spec = importlib.util.spec_from_file_location("check_brief", SCRIPT)
check_brief = importlib.util.module_from_spec(spec)
spec.loader.exec_module(check_brief)


def brief(bodies: dict[int, str]) -> str:
    parts = ["# Draft\n\nStatus line, not counted.\n\n---\n"]
    for number in check_brief.LIMITS:
        body = bodies.get(number, "word")
        parts.append(f"## {number}. Section {number} (limit words)\n\n{body}\n")
    parts.append("---\n\n## References (attachment)\n\nnot counted at all\n")
    return "\n".join(parts)


def test_team_notes_links_and_table_marks_are_not_counted():
    text = (
        "Serein warned on **72%** of days. [TEAM: add the interview\ncount here.] "
        "See [the record](../FILE.md).\n\n| A | B |\n|---|---|\n| one | two |\n"
    )
    # Serein warned on 72% of days. See the record. A B one two
    assert check_brief.count_words(text) == 13


def test_symbols_alone_are_not_words_but_units_and_numbers_are():
    assert check_brief.count_words("7.8 µg/m³ vs. 11.0 → - $5,000") == 5


def test_sections_stop_at_the_next_heading_and_at_a_rule():
    found = check_brief.sections(brief({10: "ten words here"}))
    assert set(found) == set(check_brief.LIMITS)
    assert check_brief.count_words(found[10][1]) == 3
    assert "References" not in found[10][1]


def test_report_flags_a_section_over_its_limit():
    lines, over = check_brief.report(brief({2: "word " * 151}))
    assert over
    assert any(line.startswith(" 2") and "OVER by 1" in line for line in lines)


def test_report_passes_when_every_section_fits():
    lines, over = check_brief.report(brief({}))
    assert not over
    assert lines[-1].split()[0] == "10"  # ten one-word sections


def test_a_missing_section_fails_the_check():
    text = brief({}).replace("## 7. Section 7 (limit words)", "## Seven")
    lines, over = check_brief.report(text)
    assert over
    assert any("MISSING" in line for line in lines)
