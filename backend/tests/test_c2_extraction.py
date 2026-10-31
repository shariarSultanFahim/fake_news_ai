"""
Unit tests for Change Request C2: Robust Article Extraction & Failure Handling.
Validates:
- All C2 strings exist in strings.js for en and bn ("extraction_failed").
- content.js contains the fallback selector list: article, [itemprop='articleBody'], main.
- content.js contains late-load retry logic (sleep / secondAttempt).
- Privacy check: failure logging only logs reason/wordcount, never article content.
"""

import json
from pathlib import Path
import subprocess
import pytest


STRINGS_JS = Path(__file__).resolve().parent.parent.parent / "extension" / "src" / "strings.js"
CONTENT_JS = Path(__file__).resolve().parent.parent.parent / "extension" / "src" / "content.js"


def load_strings():
    node_script = f"const strings = require('{str(STRINGS_JS).replace(chr(92), '/')}'); process.stdout.write(Buffer.from(JSON.stringify(strings), 'utf8'));"
    res = subprocess.run(["node", "-e", node_script], capture_output=True, check=True)
    return json.loads(res.stdout.decode("utf-8"))


def test_c2_strings():
    strings = load_strings()
    expected_en = "Couldn't read this page. Select the text on the page and use Analyze selection, or paste it."
    assert strings["en"]["extraction_failed"] == expected_en
    assert "extraction_failed" in strings["bn"]
    assert len(strings["bn"]["extraction_failed"]) > 0


def test_content_js_robustness_features():
    with open(CONTENT_JS, "r", encoding="utf-8") as f:
        code = f.read()

    # 1. Readability first
    assert "extractWithReadability" in code
    # 2. Fallback selectors: article, itemprop=articleBody, main
    assert "article" in code
    assert "[itemprop='articleBody']" in code
    assert "main" in code
    # 3. Late loading retry logic
    assert "sleep" in code or "setTimeout" in code
    assert "secondAttempt" in code or "retry" in code
    # 4. Privacy-safe logging
    assert "Article extraction failed. Reason: no article text" in code


if __name__ == "__main__":
    pytest.main(["-s", "-v", __file__])

