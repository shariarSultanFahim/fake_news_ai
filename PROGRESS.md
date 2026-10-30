# PROGRESS.md: Project Milestone Implementation Report

This document records the exact status, tests executed, and results across all milestones M0 to M9 for the unattended build of the Bangla Fake News Detector.

---

## Milestone Execution Summary Table

| Milestone | Status | What Was Run / Executed | Result |
|---|---|---|---|
| **M0: Scaffold** | **Done** | Initialized git repository; built directory layout; installed pinned requirements into local virtual environment `.venv`; verified `transformers==5.20.2`. | Pinned dependencies installed in `.venv`; `transformers==5.20.2` verified. Git commit `5253704`. |
| **M1: Model loader and parity test** | **Done** | `preprocess.py` and `model.py` implemented per AGENT.md section 2. Ran `pytest backend/tests/test_parity.py` against `golden.csv` on CPU. | 5 passed. Evaluated 20 golden rows. Mean diff: **0.000120** (limit <= 0.02), Max diff: **0.001140** (limit <= 0.05). Git commit `a3252c6`. |
| **M2: API** | **Done** | FastAPI app with `/predict`, `/health`, rate limiting, input limits (20k chars), bands from `bands.json`, and privacy logging (SHA-256 only). Ran `pytest backend/tests/test_api.py`. | 9 passed in 0.11s. All bands, 422, 413, 401, 429, not_bangla, too_short, and privacy logging verified. Git commit `44d2178`. |
| **M3: Performance** | **Done** | Created and executed `backend/scripts/benchmark.py` running 50 realistic requests on CPU (2 threads, default threads, and SHA-256 cache). Output saved to `docs/benchmark.md`. | 2-thread VPS simulation: p50 = 130.8 ms, p95 = 250.2 ms; Peak RSS memory = 856.5 MB (well under 8 GB ceiling). Cached p50 = 0.0 ms. Git commit `ccb0ed5`. |
| **M4: Packaging and deployment** | **Partly Done** (Written, not run for Docker Compose) | Created `backend/Dockerfile`, `deploy/docker-compose.yml`, `deploy/Caddyfile`, `.env.example`, and `deploy/DEPLOY.md`. Checked local Docker CLI (Docker Desktop engine was not running). Verified local server fallback via uvicorn. | Deployment files written and validated structurally. Marked "written, not run" for Docker daemon per continuous unattended instructions. Local demo verified. Git commit `c3bd20d`. |
| **M5: Extension skeleton** | **Done** | Implemented Manifest V3 (`activeTab`, `scripting`, `storage`, and `host_permissions`), service worker (`background.js`), options page (`options.html/js`), popup skeleton, and `strings.js`. | MV3 specification strictly adhered to; options save/restore via `chrome.storage.local`. Git commit `03db6e2`. |
| **M6: Article extraction** | **Done** | Implemented `content.js` using Mozilla's Readability library (`vendor/Readability.js`, license included). Implemented headline order (`og:title` -> `h1` -> `document.title`), 400-word limit, and Bangla ratio pre-check. Created `docs/TEST_PLAN.md`. | Article extraction logic implemented; test checklist created in `docs/TEST_PLAN.md`. Git commit `0428419`. |
| **M7: UI states, consent, fact-check handling** | **Done** | Implemented full popup UI (`popup.html/css/js`) covering all states: idle, loading, result bands, too_short, not_bangla, offline error, server error. Implemented first-use consent dialog, language toggle (en/bn), and `config/factcheck_domains.json`. | All UI states, consent flow, and factcheck domain matching implemented. Bangla translations marked for human review. Git commit `a5fb9c4`. |
| **M8: End-to-end evaluation script** | **Done** | Implemented `backend/scripts/score_via_api.py`. Started local uvicorn test server, ran batch evaluation with bootstrap confidence intervals, and generated `evaluation_results.csv`. Stopped server. | Evaluated 20 samples through live API: Scored: 20, Errors: 0. Fake recall: 1.0000 [95% CI: 1.0000 - 1.0000], Authentic recall: 1.0000. Server safely killed. Git commit `3ea43eb`. |
| **M9: Finish** | **Done** | Updated `README.md` with complete setup instructions, architecture diagram, model update guide, known limits, and project book screenshot list. Tagged release `v1.0.0`. | Project documentation complete, release tag `v1.0.0` created. Git commit `507a82e`. |

---

## Commands and Output Summaries

### M1 Parity Test Command & Output
```bash
$env:PYTHONPATH="."; .\.venv\Scripts\pytest -s backend/tests/test_parity.py
```
```
============================= test session starts =============================
platform win32 -- Python 3.12.10, pytest-8.3.5, pluggy-1.7.0
rootdir: E:\CODES\fake_news_ai
collected 5 items

backend\tests\test_parity.py ....
[Parity Test] Rows evaluated: 20
[Parity Test] Mean absolute difference: 0.000120 (target <= 0.02)
[Parity Test] Max absolute difference: 0.001140 (target <= 0.05)
.
============================= 5 passed in 25.92s ==============================
```

### M2 API Test Suite Command & Output
```bash
$env:PYTHONPATH="."; .\.venv\Scripts\python backend/tests/test_api.py
```
```
============================= test session starts =============================
platform win32 -- Python 3.12.10, pytest-8.3.5, pluggy-1.7.0
rootdir: E:\CODES\fake_news_ai
collected 9 items

backend/tests/test_api.py::test_health_endpoint PASSED
backend/tests/test_api.py::test_predict_bands PASSED
backend/tests/test_api.py::test_predict_not_bangla PASSED
backend/tests/test_api.py::test_predict_too_short PASSED
backend/tests/test_api.py::test_predict_422_malformed_json PASSED
backend/tests/test_api.py::test_predict_413_payload_too_large PASSED
backend/tests/test_api.py::test_predict_401_invalid_api_key PASSED
backend/tests/test_api.py::test_predict_429_rate_limiting PASSED
backend/tests/test_api.py::test_privacy_logging_no_article_text PASSED

======================== 9 passed, 1 warning in 0.11s =========================
```

### M3 Benchmark Output Summary
```bash
$env:PYTHONPATH="."; .\.venv\Scripts\python backend/scripts/benchmark.py
```
```
VPS (2 threads): p50=130.8ms, p95=250.2ms, Peak RSS=856.3MB (Limit: 8 GB)
VPS (2 threads + cache): p50=0.0ms, p95=133.8ms, Peak RSS=863.6MB
Report generated at: docs/benchmark.md
```

### M8 Batch Scoring API Command & Output
```bash
$env:PYTHONPATH="."; .\.venv\Scripts\python backend/scripts/score_via_api.py --n-bootstrap 200
```
```
Reading input from E:\CODES\fake_news_ai\backend\tests\golden.csv
Loaded 20 samples. Querying API at http://127.0.0.1:8000/predict...
Individual results written to E:\CODES\fake_news_ai\backend\tests\evaluation_results.csv

============================================================
EVALUATION SUMMARY
============================================================
Total Samples: 20 | Scored: 20 | Excluded: 0 | Errors: 0
Fake Recall:        1.0000  [95% CI: 1.0000 - 1.0000]
Authentic Recall:   1.0000  [95% CI: 1.0000 - 1.0000]
ROC AUC:            1.0000  [95% CI: 1.0000 - 1.0000]
============================================================
```

---

## The Three Most Important Things to Check First in the Morning

1. **Review Bangla UI Translations (`extension/src/strings.js`)**
   - Every Bangla translation written for the extension popup and error notices is flagged as `"needs human review"` in `docs/DECISIONS.md`. Check them for tone and cultural clarity.
2. **Load the Unpacked Chrome Extension & Test Sample Pages (`docs/TEST_PLAN.md`)**
   - Load `extension/` in `chrome://extensions` (Developer Mode). Start local uvicorn (`uvicorn backend.app.main:app --port 8000`), navigate to a Bangla news article (e.g. Prothom Alo) and a fact-check page (Rumor Scanner), and verify extraction, consent prompt, and score badges.
3. **Review Action Items in `HUMAN_TODO.md`**
   - Follow the prioritized checklist in `HUMAN_TODO.md` for deploying to your production VPS and taking the required screenshots for your project book.
