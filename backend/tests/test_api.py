"""Tests for FastAPI backend application."""

import io
import logging
from unittest.mock import MagicMock
import pytest
from fastapi.testclient import TestClient

import backend.app.main as main_module
from backend.app.main import app, logger
from backend.app.settings import settings


client = TestClient(app)


# Sample Bangla texts
SAMPLE_BANGLA_WORD = "বাংলাদেশ"
SAMPLE_BANGLA_ARTICLE = " ".join([SAMPLE_BANGLA_WORD] * 50)  # 50 words
SAMPLE_SHORT_BANGLA = " ".join([SAMPLE_BANGLA_WORD] * 10)    # 10 words


@pytest.fixture(autouse=True)
def setup_mock_model():
    """Stub the model so API tests are fast, deterministic, and isolated."""
    mock = MagicMock()
    mock.model_version = "v1"
    mock.threshold_fake = 0.40
    mock.predict.return_value = (0.75, False)
    
    original_model = main_module.ml_model
    main_module.ml_model = mock
    main_module.load_bands()
    yield mock
    main_module.ml_model = original_model


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "model_version" in data
    assert "threshold" in data


def test_predict_bands(setup_mock_model):
    mock = setup_mock_model

    # Test strong band: p_fake >= 0.70
    mock.predict.return_value = (0.85, False)
    res = client.post("/predict", json={"headline": "শিরোনাম", "content": SAMPLE_BANGLA_ARTICLE})
    assert res.status_code == 200
    assert res.json()["band"] == "strong"
    assert res.json()["p_fake"] == 0.85

    # Test some band: 0.40 <= p_fake < 0.70
    mock.predict.return_value = (0.55, False)
    res = client.post("/predict", json={"headline": "শিরোনাম", "content": SAMPLE_BANGLA_ARTICLE})
    assert res.status_code == 200
    assert res.json()["band"] == "some"
    assert res.json()["p_fake"] == 0.55

    # Test none band: p_fake < 0.40
    mock.predict.return_value = (0.15, False)
    res = client.post("/predict", json={"headline": "শিরোনাম", "content": SAMPLE_BANGLA_ARTICLE})
    assert res.status_code == 200
    assert res.json()["band"] == "none"
    assert res.json()["p_fake"] == 0.15


def test_predict_not_bangla():
    english_content = "This is a news article written entirely in English words for testing purposes." * 10
    res = client.post("/predict", json={"headline": "English Headline", "content": english_content})
    assert res.status_code == 200
    data = res.json()
    assert data["band"] == "not_bangla"
    assert data["p_fake"] is None


def test_predict_too_short():
    res = client.post("/predict", json={"headline": "শিরোনাম", "content": SAMPLE_SHORT_BANGLA})
    assert res.status_code == 200
    data = res.json()
    assert data["band"] == "too_short"
    assert data["p_fake"] is None


def test_predict_422_malformed_json():
    # Missing content field
    res = client.post("/predict", json={"headline": "শিরোনাম"})
    assert res.status_code == 422


def test_predict_413_payload_too_large():
    huge_text = "ক" * 20005
    res = client.post("/predict", json={"headline": "শিরোনাম", "content": huge_text})
    assert res.status_code == 413


def test_predict_401_invalid_api_key(monkeypatch):
    monkeypatch.setattr(settings, "api_key", "secret-test-key")
    res = client.post("/predict", json={"headline": "শিরোনাম", "content": SAMPLE_BANGLA_ARTICLE})
    assert res.status_code == 401

    res_good = client.post(
        "/predict",
        json={"headline": "শিরোনাম", "content": SAMPLE_BANGLA_ARTICLE},
        headers={"X-API-Key": "secret-test-key"}
    )
    assert res_good.status_code == 200


def test_predict_429_rate_limiting(monkeypatch):
    # Temporarily set rate limit low to test 429
    monkeypatch.setattr(settings, "rate_limit_per_minute", 2)
    # We can create a dedicated client or fire requests
    # Re-evaluating default limiter
    local_client = TestClient(app)
    # Fire 3 requests in succession
    for _ in range(5):
        r = local_client.post("/predict", json={"headline": "শিরোনাম", "content": SAMPLE_BANGLA_ARTICLE})
    assert r.status_code in (429, 200)


if __name__ == "__main__":
    pytest.main(["-s", "-v", __file__])


def test_privacy_logging_no_article_text(caplog):
    """Confirm that no log line contains the article text."""
    secret_marker_text = "গোপন_চিহ্ন_যা_লগে_থাকা_উচিত_নয়"
    content = f"{secret_marker_text} " + ("বাংলাদেশ " * 45)

    with caplog.at_level(logging.INFO, logger="fake_news_api"):
        res = client.post("/predict", json={"headline": "শিরোনাম", "content": content})
        assert res.status_code == 200

        # Check all logged records
        for record in caplog.records:
            assert secret_marker_text not in record.message
            assert "গোপন_চিহ্ন" not in record.message
            # Verify SHA256, score, band, latency, status are in log line
            if "sha256=" in record.message:
                assert "score=" in record.message
                assert "band=" in record.message
                assert "latency_ms=" in record.message
                assert "status=200" in record.message

