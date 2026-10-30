# Bangla Fake News Detector (Backend + Chrome Extension)

A Chrome extension (Manifest V3) that extracts the headline and body of a Bangla news article on the active browser tab, sends them to a FastAPI backend service, and returns an estimate of how strongly the article resembles fake or misleading news. The backend executes a fine-tuned BanglaBERT classifier (Electra architecture) trained on BanFakeNews-2.0.

---

## 1. Important Limits of the Model

The UI and application strictly respect the following characteristics:
- **Trained on BanFakeNews-2.0**: Held-out test split results: macro-F1 `0.885`, accuracy `0.936`, fake precision `0.98`, fake recall `0.69`, AUC `0.906`.
- **False Negatives**: The model misses approximately 31% of fake articles; therefore, a "no signal" result is weak evidence. The UI **NEVER** characterizes an article as *authentic*, *true*, *verified*, or *safe*.
- **Small In-House Test Set**: On a small team-collected set (Prothom Alo real news vs Rumor Scanner fact-checks, October 2026), it scored AUC `0.98` to `0.996`, but that data has one source per class and does not prove general performance.
- **Fact-Check Article Handling**: Fact-checking articles often cite disinformation; to prevent false positives, known fact-checking domains (configured in `extension/config/factcheck_domains.json`) are bypassed by the extension with an explicit notice.

---

## 2. Architecture Diagram (Text Representation)

```
[ User Browser / Chrome Tab ]
            │
            ▼ (Active Tab)
[ Mozilla Readability (vendor/Readability.js) + content.js ]
  - Extracts headline (og:title -> h1 -> document.title)
  - Extracts first 400 words of content
  - Checks client-side Bangla ratio (>= 50%)
  - Checks length (>= 40 words)
            │
            ▼ (chrome.runtime.sendMessage)
[ Service Worker: background.js ]
  - Checks user consent (chrome.storage.local)
  - Checks fact-check domain bypass
            │
            ▼ (HTTP POST /predict over HTTPS or localhost)
[ Reverse Proxy: Caddy ] (deploy/Caddyfile)
  - TLS termination & security headers
            │
            ▼ (Reverse proxy to :8000)
[ FastAPI Backend ] (backend/app/main.py)
  - Input length check (max 20,000 chars)
  - Bangla ratio check (>= 50% Bangla characters)
  - Word count check (>= 40 words)
  - Per-IP rate limiting (slowapi)
  - Privacy-safe logging (SHA-256 hash, score, latency, no article text)
            │
            ▼
[ Preprocessor & Model ] (preprocess.py & model.py)
  - Whitespace strip
  - csebuetnlp normalizer (default settings)
  - Sentence-pair tokenization (max 256 tokens, truncation='only_second')
  - Eval mode fp32 on CPU
  - p_fake = softmax(logits)[0]
  - Bands: strong (>= 0.70), some (0.40 - 0.69), none (< 0.40)
```

---

## 3. Quick Start & Setup

### 3.1 Backend Setup
Requirements: Python 3.10 - 3.12, Git.

```bash
# 1. Create and activate a virtual environment
python -m venv .venv
# Windows:
.\.venv\Scripts\Activate.ps1
# Linux / macOS:
source .venv/bin/activate

# 2. Install pinned dependencies
pip install -r backend/requirements.txt

# 3. Model directory
# Ensure backend/model/ contains config.json, inference_config.json,
# model.safetensors, tokenizer.json, and tokenizer_config.json.

# 4. Run tests
python -m pytest backend/tests/test_parity.py
python -m pytest backend/tests/test_api.py

# 5. Start the local server
uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

Verify the health check:
```bash
curl http://127.0.0.1:8000/health
# {"status":"ok","model_version":"v1","threshold":0.4}
```

### 3.2 Chrome Extension Setup
1. Open Google Chrome and navigate to `chrome://extensions/`.
2. Enable **Developer mode** (toggle in top right).
3. Click **Load unpacked** and select the `extension/` directory.
4. Click the extension icon on any Bangla news article page.
5. Review the first-use consent prompt and click **I Agree**.
6. Click **Analyze this page** to receive the model evaluation.

---

## 4. Retraining or Replacing the Model

To deploy an updated model weights checkpoint:
1. Export the fine-tuned Electra weights in HuggingFace format (`config.json`, `model.safetensors`, `tokenizer.json`, `tokenizer_config.json`).
2. Include an updated `inference_config.json` with keys:
   - `threshold_fake` (e.g. `0.40`)
   - `max_length` (e.g. `256`)
   - `uses_normalizer` (boolean `true`)
   - `model_version` (e.g. `"v2"`)
3. Place these files inside `backend/model/`.
4. Update `backend/tests/golden.csv` with updated validation predictions from your training notebook.
5. Re-run `pytest backend/tests/test_parity.py` to verify parity tolerances (mean diff <= 0.02, max diff <= 0.05).
6. Adjust `backend/app/bands.json` cut-offs if your probability distribution changes.

---

## 5. Required Screenshots for Project Book

The following screenshots should be taken by the human reviewer:
1. **Extension Idle State**: Clean popup with the "Analyze this page" button.
2. **First-Use Consent Prompt**: Notice informing user about sending headline/text.
3. **Analysis Loading State**: Spinner during inference.
4. **Band: Strong Resemblance**: High fake score alert on a known false article.
5. **Band: Some Resemblance**: Moderate fake score alert.
6. **Band: No Strong Signals**: Informational card showing score < 0.40 with strict disclaimers.
7. **Fact-Check Bypass**: Green notice when browsing `rumorscanner.com`.
8. **Settings / Options Page**: Form with backend URL, API key, language switch, and consent withdrawal.
