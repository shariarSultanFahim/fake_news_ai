# AGENT.md: Bangla Fake News Detector (backend + Chrome extension)

Read this whole file before writing any code. Follow the milestones in order. This file is the source of truth for decisions. If the code you want to write conflicts with this file, stop and ask the human.

## 0. Working rules

1. Work on ONE milestone at a time. When its acceptance checks pass, summarize what you did (files changed, how you checked it) and WAIT for the human to say "go" before starting the next milestone.
2. Write tests with the code. A milestone is not done until its checks run and pass. Show the command and its output.
3. Never change these without asking the human: the preprocessing in section 2, the threshold, the band cut-offs, the user-facing wording in section 5, the API contract in section 3.
4. Never invent data. Files marked HUMAN-SUPPLIED (section 8) come from the human. If one is missing, say so and continue with what you can do; do not fabricate it.
5. Never commit model weights, `.env` files, API keys or server credentials. Keep `backend/model/` and `.env` in `.gitignore`.
6. Never log article text. Logs may contain only: a SHA-256 hash of the text, the score, the band, the latency and the status code.
7. Keep the code simple and readable. Prefer the standard library and well-known packages. Tell the human before adding any new dependency, and say why.
8. If something is ambiguous, ask one clear question instead of guessing.
9. Record each decision that is not in this file in `docs/DECISIONS.md` (date, decision, reason).

## 1. What this project is

A Chrome extension (Manifest V3) that reads a Bangla news article on the current page, sends the headline and the first part of the text to a backend, and shows a machine-learning estimate of how much the article resembles fake or misleading news. The backend runs a fine-tuned BanglaBERT classifier.

Important limits of the model (the UI must respect them):

- Trained on BanFakeNews-2.0. On its held-out test split: macro-F1 0.885, accuracy 0.936, fake precision 0.98, fake recall 0.69, AUC 0.906. It misses about 31% of fake articles, so a "no signal" result is weak evidence. The UI must NEVER call an article authentic, true, verified or safe.
- On a small team-collected set (Prothom Alo real news vs Rumor Scanner fact-checks, October 2026) it scored AUC 0.98 to 0.996, but that data has one source per class, so it does not prove general performance.
- It may flag fact-check pages. The extension handles that (milestone M7).

## 2. The model and how to run it (must match training exactly)

Model folder: `backend/model/` (HUMAN-SUPPLIED, copied from Google Drive `bangla_fn/banglabert-fakenews`). It contains `config.json`, `model.safetensors`, `tokenizer.json`, `tokenizer_config.json` and `inference_config.json`.

`inference_config.json` keys you must read at startup (do not hard-code them): `threshold_fake` (currently 0.40), `max_length` (256), `uses_normalizer` (true).

Label order: `id2label` is `{0: "fake", 1: "authentic"}`. At load time, assert this from the model config. `p_fake` is the softmax probability at index 0.

Preprocessing, in this order, for every request:

1. Strip whitespace from `headline` and `content`.
2. If `uses_normalizer` is true: `from normalizer import normalize` (the csebuetnlp normalizer, installed from `git+https://github.com/csebuetnlp/normalizer`), then call `normalize(text)` with DEFAULT arguments on the headline and on the content separately. Record the normalizer commit hash in `docs/DECISIONS.md`.
3. Tokenize as a sentence pair: `tokenizer(headline, content, truncation="only_second", max_length=max_length, return_tensors="pt")`. Headline is the first sentence, content the second. Only the content is truncated.
4. Edge case: if the headline alone is longer than `max_length`, cap the headline at 100 words before tokenizing (this only affects pathological input; mention it in the response as `truncated: true`).
5. Run the model in eval mode with no gradients. Use fp32 on CPU. Use fp16 autocast only on GPU.
6. `p_fake = softmax(logits)[0]`. A prediction is "fake-like" when `p_fake >= threshold_fake`.

Software: Python 3.10 to 3.12. Pin `transformers==5.20.2` (the version recorded in the saved config). On the server use CPU-only PyTorch wheels (`--index-url https://download.pytorch.org/whl/cpu`).

Hardware targets:

- Production (maybe): Hostinger KVM 2 VPS, 2 vCPU, 8 GB RAM, NO GPU. Use `torch.set_num_threads(2)` there.
- Development and fallback demo: the human's laptop, 16 GB RAM and a 4 GB GPU. Use CPU by default for tests so results match the server; allow GPU only through an explicit setting.
- Measure and report peak memory. It must stay well under 8 GB.

## 3. API contract (do not change without asking)

Base path has no version prefix. JSON only.

`GET /health` returns `{"status": "ok", "model_version": "<string>", "threshold": <float>}`.

`POST /predict`

Request: `{"headline": "<string>", "content": "<string>"}`. `headline` may be an empty string; `content` must be non-empty.

Response (HTTP 200):

```json
{
  "band": "strong | some | none | too_short | not_bangla",
  "p_fake": 0.0,
  "threshold": 0.40,
  "model_version": "v1",
  "word_count": 0,
  "truncated": false,
  "latency_ms": 0
}
```

Rules, applied in this order:

1. `not_bangla`: fewer than 50% of the letters in headline + content are Bangla (Unicode block U+0980 to U+09FF). Return `p_fake: null`. Do not run the model.
2. `too_short`: fewer than 40 words in content. Return `p_fake: null`. Do not run the model.
3. Otherwise run the model and set `band` from `p_fake`: `p_fake >= 0.70` is `strong`; `0.40 <= p_fake < 0.70` is `some`; `p_fake < 0.40` is `none`.

The band cut-offs live in `backend/app/bands.json` (not in code) so the human can change them after the second evaluation set. The 0.40 cut-off must equal `threshold_fake` from `inference_config.json`; if they differ, log a warning at startup.

Errors: HTTP 422 for malformed JSON or missing fields; HTTP 413 when headline + content is over 20,000 characters; HTTP 401 when an API key is required and wrong; HTTP 429 when rate-limited; HTTP 500 with a generic message otherwise (never include the text in an error).

Security and abuse control (required, because the server will be public):

- Optional API key: if the env var `API_KEY` is set, require the header `X-API-Key`. Note in the docs that a key shipped in an extension is not secret; it only deters casual misuse.
- Simple per-IP rate limit (default 30 requests per minute, configurable by env var).
- CORS: allow the origin of the extension (`chrome-extension://<id>`) from an env var. Calls from the extension background script do not need CORS if `host_permissions` is set, but keep the setting.
- Production must use HTTPS (see M4). Article text must not travel over plain HTTP.

## 4. Repository layout

```
.
├── AGENT.md
├── backend/
│   ├── app/            # main.py, model.py, preprocess.py, bands.json, settings.py
│   ├── model/          # HUMAN-SUPPLIED, git-ignored
│   ├── tests/          # includes golden.csv (HUMAN-SUPPLIED)
│   ├── requirements.txt
│   ├── Dockerfile
│   └── scripts/        # benchmark.py, score_via_api.py
├── extension/
│   ├── manifest.json
│   ├── src/            # background.js, content.js, popup.html/js/css, options.html/js, strings.js
│   ├── vendor/         # third-party libraries with their licenses
│   └── config/         # factcheck_domains.json
├── deploy/             # docker-compose.yml, Caddyfile, DEPLOY.md
└── docs/               # DECISIONS.md, TEST_PLAN.md
```

## 5. User-facing wording (use exactly; keep all strings in `extension/src/strings.js`, English and Bangla)

English (the human will review the Bangla; mark any Bangla you write as "needs human review" in `docs/DECISIONS.md`):

- `strong`: "Strong resemblance to content previously found to be false or misleading."
- `some`: "Some resemblance to false or misleading content."
- `none`: "No strong fake-news signals found. This does not mean the article is true."
- `too_short`: "Not enough text to analyze."
- `not_bangla`: "This page does not appear to be in Bangla."
- `factcheck`: "This looks like a fact-check article. This tool does not score fact-checks."
- `error_offline`: "Could not reach the analysis server."
- `error_server`: "The analysis server returned an error. Try again later."
- Disclaimer shown with every result: "Automated estimate from a machine-learning model. It is not a fact-check. Verify with trusted sources."
- First-use consent: "To analyze an article, this extension sends its headline and the first part of its text to the project's server. The text is not stored. Do you agree?"

Never use the words authentic, real, true, verified or safe as a verdict anywhere in the UI. Show the probability only as supporting detail, e.g. "Model score: 0.83".

## 6. Milestones

### M0: Scaffold

Do: create the layout in section 4, `.gitignore` (model, `.env`, caches), `backend/requirements.txt` with pinned versions, a README stub, and `docs/DECISIONS.md`.
Check: `pip install -r backend/requirements.txt` works in a fresh virtual environment; `python -c "import transformers; print(transformers.__version__)"` prints 5.20.2.

### M1: Model loader and parity test

Do: implement `preprocess.py` and `model.py` exactly as in section 2: load once at startup, expose `predict(headline, content) -> p_fake`. Assert the label order. Read the threshold and max length from `inference_config.json`.
Parity test: the human supplies `backend/tests/golden.csv` with columns `headline`, `content`, `p_fake` (about 20 rows from the evaluation notebook's saved predictions, computed in Colab). The test runs every row through `predict` and requires mean absolute difference <= 0.02 and maximum difference <= 0.05. Differences come from fp16 vs fp32.
Check: `pytest backend/tests/test_parity.py` passes. If the maximum difference is above 0.05, STOP and report which rows differ; do not "fix" it by changing the tolerance. Likely causes are a preprocessing mismatch.
Also test: label-order assertion, headline longer than `max_length`, empty headline.

### M2: API

Do: FastAPI app implementing section 3, with the band logic from `bands.json`, input validation, the Bangla-ratio and length checks, privacy-safe logging, optional API key, rate limit and CORS setting.
Check: tests for each band (use stored sample texts; stub the model for the band logic), 422, 413, 401, 429, `not_bangla`, `too_short`, and `/health`. A test must confirm that no log line contains the article text.

### M3: Performance

Do: `scripts/benchmark.py` that sends 50 requests of realistic length and prints p50 and p95 latency and peak memory (CPU, 2 threads and the default). Add a result cache keyed by the SHA-256 of the normalized text.
Optional experiment: PyTorch dynamic INT8 quantization. If tried, rerun the parity test and report the score differences. Do NOT enable it by default; the human decides from your report.
Check: benchmark output saved to `docs/benchmark.md` with the machine description.

### M4: Packaging and deployment

Do: `backend/Dockerfile` (CPU PyTorch, non-root user, the model folder mounted as a volume, never baked into the image), `deploy/docker-compose.yml` with the API and a Caddy reverse proxy that gets a free HTTPS certificate for a domain or subdomain the human supplies, environment variables in `.env.example`, a healthcheck, and `deploy/DEPLOY.md` with exact step-by-step commands for a fresh Ubuntu VPS (install Docker, copy the model, set the domain, start, verify). You do not have server access; the human runs the commands. Also write the local-demo alternative (run uvicorn on the laptop; use a tunnel if another device must reach it).
Check: `docker compose up` works locally and `/health` answers; `DEPLOY.md` is complete enough that every command can be copied.

### M5: Extension skeleton

Do: Manifest V3 with only these permissions: `activeTab`, `scripting`, `storage`, and `host_permissions` for the backend URL. No broad site access. A popup with an "Analyze this page" button, a background service worker that makes the HTTP call (not the content script), and an options page for the backend URL and the optional API key. Use `chrome.storage.local`.
Check: loads without errors through `chrome://extensions` (developer mode, Load unpacked); the popup opens; the settings save.

### M6: Article extraction

Do: a content script that returns `{headline, content}`. Headline order: `og:title`, then the first `h1`, then `document.title`. Body: use Mozilla's Readability library (put it in `vendor/` with its license file; tell the human before adding it). Send the first 400 words of the body. Check that at least 50% of the letters are Bangla before sending (same rule as the backend). Handle pages that load content late (wait briefly, then retry once).
Check: manual test on at least five Bangla article pages and three non-article or non-Bangla pages; results documented in `docs/TEST_PLAN.md`.

### M7: UI states, consent, fact-check handling

Do: all states from section 5 (idle, loading, each band, too short, not Bangla, offline, server error). First-use consent screen (store the agreement; allow withdrawing it in the options page). Fact-check detection: if the page host is in `config/factcheck_domains.json` (HUMAN-SUPPLIED list, start with `rumorscanner.com`), show the `factcheck` message and do not call the server. Strings in Bangla and English with a language switch. Readable at small popup width.
Check: each state can be reached and screenshotted (use a mock-backend switch for testing offline and error states).

### M8: End-to-end evaluation script and tests

Do: `backend/scripts/score_via_api.py` that reads a CSV with columns `headline`, `content`, `label` (`fake` or `real`), calls the live `/predict`, and writes a CSV of results plus a summary: for rows that got a model score, fake recall, real recall and AUC with bootstrap 95% confidence intervals, and counts of `too_short` and `not_bangla`. This is how the second evaluation set (HUMAN-SUPPLIED later) gets scored through the real service. Write `docs/TEST_PLAN.md` with the manual checklist (10 to 15 real pages: several news sites, one fact-check page, one non-Bangla page, one very short page, one page with no headline).
Check: the script runs on a small sample and produces the summary.

### M9: Finish

Do: README with setup, the architecture diagram described in text, how to retrain or replace the model, known limits (copy section 1), and a tagged release. List the screenshots the human should take for the project book.
Check: a new person can follow the README from a clean machine.

## 7. Do not

- Do not train or modify the model.
- Do not add analytics, tracking or any third-party network calls.
- Do not send article text anywhere except the configured backend.
- Do not describe the model as accurate or reliable in the UI or README beyond the facts in section 1.
- Do not change the band cut-offs, threshold or wording to make results look better.

## 8. HUMAN-SUPPLIED items (ask for them when needed)

1. `backend/model/` (the model folder from Drive).
2. `backend/tests/golden.csv` (headline, content, p_fake from Colab; about 20 rows).
3. The domain or subdomain for HTTPS on the server, and the server itself (the human runs the deploy commands).
4. `extension/config/factcheck_domains.json` (the human extends the list).
5. Review of Bangla UI strings.
6. Later: the second evaluation set CSV for M8.
