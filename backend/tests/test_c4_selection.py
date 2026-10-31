"""
Unit tests for Change Request C4: Analyze Selected Text.
Validates:
- All C4 strings exist in strings.js for en and bn (analyze_selection_button, no_selection_error).
- popup.html contains analyze-selection-btn.
- popup.js contains performSelectionAnalysis and window.getSelection call.
- manifest.json does NOT add any permissions beyond activeTab, scripting, storage.
"""

import json
from pathlib import Path
import subprocess
import pytest


STRINGS_JS = Path(__file__).resolve().parent.parent.parent / "extension" / "src" / "strings.js"
POPUP_HTML = Path(__file__).resolve().parent.parent.parent / "extension" / "src" / "popup.html"
POPUP_JS = Path(__file__).resolve().parent.parent.parent / "extension" / "src" / "popup.js"
MANIFEST_JSON = Path(__file__).resolve().parent.parent.parent / "extension" / "manifest.json"


def load_strings():
    node_script = f"const strings = require('{str(STRINGS_JS).replace(chr(92), '/')}'); process.stdout.write(Buffer.from(JSON.stringify(strings), 'utf8'));"
    res = subprocess.run(["node", "-e", node_script], capture_output=True, check=True)
    return json.loads(res.stdout.decode("utf-8"))


def test_c4_strings():
    strings = load_strings()
    required_keys = [
        "analyze_selection_button",
        "no_selection_error"
    ]
    for lang in ["en", "bn"]:
        assert lang in strings
        for k in required_keys:
            assert k in strings[lang], f"Missing key {k} in locale {lang}"
            assert len(strings[lang][k]) > 0


def test_popup_html_elements_c4():
    with open(POPUP_HTML, "r", encoding="utf-8") as f:
        html = f.read()

    assert 'id="analyze-selection-btn"' in html


def test_popup_js_selection_implementation():
    with open(POPUP_JS, "r", encoding="utf-8") as f:
        code = f.read()

    assert "performSelectionAnalysis" in code
    assert "window.getSelection()" in code
    assert "parsePasteText" in code


def test_manifest_no_new_permissions():
    """Verify strictly NO new permissions added per user instructions."""
    with open(MANIFEST_JSON, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    expected_permissions = {"activeTab", "scripting", "storage"}
    assert set(manifest["permissions"]) == expected_permissions, f"Permissions modified: {manifest['permissions']}"


if __name__ == "__main__":
    pytest.main(["-s", "-v", __file__])

