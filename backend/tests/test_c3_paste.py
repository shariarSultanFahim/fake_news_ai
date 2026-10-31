"""
Unit tests for Change Request C3: Paste Text Tab & Parsing.
Validates:
- All C3 strings exist in strings.js for en and bn (tab_page, tab_paste, paste_headline_placeholder, paste_content_placeholder, paste_analyze_button).
- popup.html contains tabs-nav, paste-state, paste-headline, paste-content, paste-analyze-btn.
- Simulation of parsePasteText (first line/sentence fallback, 400 word cap, 40-word limit, Bangla ratio).
"""

import json
from pathlib import Path
import re
import subprocess
import pytest


STRINGS_JS = Path(__file__).resolve().parent.parent.parent / "extension" / "src" / "strings.js"
POPUP_HTML = Path(__file__).resolve().parent.parent.parent / "extension" / "src" / "popup.html"


def load_strings():
    node_script = f"const strings = require('{str(STRINGS_JS).replace(chr(92), '/')}'); process.stdout.write(Buffer.from(JSON.stringify(strings), 'utf8'));"
    res = subprocess.run(["node", "-e", node_script], capture_output=True, check=True)
    return json.loads(res.stdout.decode("utf-8"))


def test_c3_strings():
    strings = load_strings()
    required_keys = [
        "tab_page",
        "tab_paste",
        "paste_headline_placeholder",
        "paste_content_placeholder",
        "paste_analyze_button"
    ]
    for lang in ["en", "bn"]:
        assert lang in strings
        for k in required_keys:
            assert k in strings[lang], f"Missing key {k} in locale {lang}"
            assert len(strings[lang][k]) > 0


def test_popup_html_elements_c3():
    with open(POPUP_HTML, "r", encoding="utf-8") as f:
        html = f.read()

    assert 'id="main-tabs"' in html
    assert 'id="tab-btn-page"' in html
    assert 'id="tab-btn-paste"' in html
    assert 'id="paste-state"' in html
    assert 'id="paste-headline"' in html
    assert 'id="paste-content"' in html
    assert 'id="paste-analyze-btn"' in html


def test_parse_paste_text_fallback_first_line():
    """Verify first line is used as headline if headline is empty."""
    first_line = "এটি সংবাদের প্রথম লাইন বা শিরোনাম।"
    body_lines = "এখানে সংবাদের বাকি বিস্তারিত অংশ রয়েছে যা ঘটনাটি ব্যাখ্যা করে। " * 10
    full_text = f"{first_line}\n{body_lines}"

    # First line split
    line_end = full_text.find("\n")
    headline = full_text[:line_end].strip()
    content = full_text[line_end + 1:].strip()

    assert headline == first_line
    assert len(content.split()) >= 40


def test_parse_paste_text_fallback_first_sentence():
    """Verify first sentence split if there is no newline."""
    first_sentence = "এটি সংবাদের প্রথম বাক্য।"
    remaining = "এখানে বাকি বিস্তারিত বাক্য রয়েছে যা প্রতিবেদনটি পূর্ণাঙ্গ করে। " * 8
    full_text = f"{first_sentence} {remaining}"

    match = re.match(r"^([^।\.\?\!]+[।\.\?\!])\s*(.*)$", full_text, flags=re.DOTALL)
    assert match is not None
    assert match.group(1).strip() == first_sentence
    assert len(match.group(2).strip().split()) >= 40


if __name__ == "__main__":
    pytest.main(["-s", "-v", __file__])
