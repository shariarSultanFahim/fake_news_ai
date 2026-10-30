"""Parity and unit tests for Model loader and Preprocessor."""

import csv
from pathlib import Path
import pytest
import numpy as np
from backend.app.model import BanglaFakeNewsModel
from backend.app.preprocess import preprocess_inputs, bangla_ratio, count_words


MODEL_DIR = Path(__file__).resolve().parent.parent / "model"
GOLDEN_CSV = Path(__file__).resolve().parent / "golden.csv"


@pytest.fixture(scope="session")
def model():
    return BanglaFakeNewsModel(MODEL_DIR)


def test_label_order_assertion(model):
    """Assert id2label is {0: 'fake', 1: 'authentic'}."""
    assert model.hf_config.id2label[0] == "fake"
    assert model.hf_config.id2label[1] == "authentic"


def test_empty_headline(model):
    """Test inference with empty headline and valid content."""
    content = "এটি একটি পরীক্ষামূলক সংবাদ প্রতিবেদন যেখানে ঘটনার বিস্তারিত বর্ণনা দেওয়া হয়েছে।" * 5
    p_fake, truncated = model.predict("", content)
    assert 0.0 <= p_fake <= 1.0
    assert truncated is False


def test_headline_longer_than_max_length(model):
    """Test edge case where headline has > 100 words."""
    long_headline = "শব্দ " * 120
    content = "এটি সাধারণ খবরের বিবরণ।" * 10
    p_fake, truncated = model.predict(long_headline, content)
    assert 0.0 <= p_fake <= 1.0
    assert truncated is True


def test_bangla_ratio():
    assert bangla_ratio("বাংলাদেশ একটি সুন্দর দেশ") == 1.0
    assert bangla_ratio("This is completely English") == 0.0
    # Mixed text
    assert bangla_ratio("বাংলাদেশ Bangladesh") == 8 / (8 + 10)  # 8 Bangla letters, 10 English


def test_parity_against_golden_set(model):
    """
    Parity test: Runs every row from golden.csv through predict.
    Requires:
      - Mean absolute difference <= 0.02
      - Maximum difference <= 0.05
    """
    assert GOLDEN_CSV.exists(), f"Golden CSV not found at {GOLDEN_CSV}"

    rows = []
    with open(GOLDEN_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append(r)

    assert len(rows) > 0, "Golden CSV has no rows"

    diffs = []
    diff_details = []

    for idx, row in enumerate(rows):
        headline = row["headline"]
        content = row["content"]
        expected_p_fake = float(row["p_fake"])

        actual_p_fake, _ = model.predict(headline, content)
        diff = abs(actual_p_fake - expected_p_fake)
        diffs.append(diff)
        diff_details.append((idx, expected_p_fake, actual_p_fake, diff))

    mean_diff = float(np.mean(diffs))
    max_diff = float(np.max(diffs))

    print(f"\n[Parity Test] Rows evaluated: {len(diffs)}")
    print(f"[Parity Test] Mean absolute difference: {mean_diff:.6f} (target <= 0.02)")
    print(f"[Parity Test] Max absolute difference: {max_diff:.6f} (target <= 0.05)")

    if max_diff > 0.05:
        failing_rows = [d for d in diff_details if d[3] > 0.05]
        print(f"Failing rows (diff > 0.05): {failing_rows}")

    assert mean_diff <= 0.02, f"Mean difference {mean_diff:.6f} exceeded 0.02 tolerance"
    assert max_diff <= 0.05, f"Max difference {max_diff:.6f} exceeded 0.05 tolerance"

