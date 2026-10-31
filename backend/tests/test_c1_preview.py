"""
Unit tests for extension strings and UI structure validation for Change Request C1.
Validates:
- All C1 strings exist for both 'en' and 'bn' locales using node with utf-8 encoding.
- popup.html contains preview-state, show-preview-checkbox, preview-headline, preview-body, and preview-word-count.
"""

import json
from pathlib import Path
import subprocess
import pytest


STRINGS_JS = Path(__file__).resolve().parent.parent.parent / "extension" / "src" / "strings.js"
POPUP_HTML = Path(__file__).resolve().parent.parent.parent / "extension" / "src" / "popup.html"


def load_strings():
    node_script = f"const strings = require('{str(STRINGS_JS).replace(chr(92), '/')}'); process.stdout.write(Buffer.from(JSON.stringify(strings), 'utf8'));"
    res = subprocess.run(["node", "-e", node_script], capture_output=True, check=True)
    return json.loads(res.stdout.decode("utf-8"))


def test_c1_strings_exist():
    strings = load_strings()
    required_keys = [
        "show_preview_label",
        "preview_title",
        "preview_headline_label",
        "preview_body_label",
        "preview_word_count_label",
        "send_analysis_button",
        "cancel_button"
    ]
    for lang in ["en", "bn"]:
        assert lang in strings, f"Missing locale {lang}"
        for key in required_keys:
            assert key in strings[lang], f"Missing key {key} in locale {lang}"
            assert len(strings[lang][key]) > 0


def test_popup_html_elements_c1():
    with open(POPUP_HTML, "r", encoding="utf-8") as f:
        html = f.read()

    assert 'id="show-preview-checkbox"' in html
    assert 'id="preview-state"' in html
    assert 'id="preview-headline"' in html
    assert 'id="preview-body"' in html
    assert 'id="preview-word-count"' in html
    assert 'id="preview-send-btn"' in html
    assert 'id="preview-cancel-btn"' in html


if __name__ == "__main__":
    pytest.main(["-s", "-v", __file__])
