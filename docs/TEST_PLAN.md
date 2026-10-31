# docs/TEST_PLAN.md: Quality Assurance & Manual Test Plan

This test plan defines manual and automated validation procedures for the Bangla Fake News Detector Chrome Extension and Backend API.

---

## 1. Automated Checks Overview

- **M1 Parity Check**: `pytest backend/tests/test_parity.py` (mean abs diff <= 0.02, max diff <= 0.05 against `golden.csv`).
- **M2 API Suite**: `pytest backend/tests/test_api.py` (health check, all response bands, error codes 422/413/401/429, privacy log validation).
- **M3 Benchmark**: `python backend/scripts/benchmark.py` (CPU 2-thread and default thread latency and RSS memory ceiling).
- **M8 End-to-End Evaluation**: `python backend/scripts/score_via_api.py` (bootstrap confidence intervals, metrics calculation).

---

## 2. Chrome Extension Manual Test Checklist

To be completed by human tester in Google Chrome (`chrome://extensions` with Developer Mode enabled):

### Category A: Authentic Bangla News Outlets (Expected: "none" or "some", valid score)
1. **Prothom Alo** (e.g. `https://www.prothomalo.com/bangladesh/...`)
   - Headline: Extracted via `og:title` or `h1`.
   - Content: First 400 words extracted via Readability.
   - Result: Model score displayed; disclaimers visible.
2. **The Daily Ittefaq** (`https://www.ittefaq.com.bd/...`)
   - Verification: Body text extracted cleanly without navigation clutter.
3. **bdnews24 Bangla** (`https://bangla.bdnews24.com/...`)
   - Verification: Correct Bangla ratio detection (> 0.50).
4. **Jugantor** (`https://www.jugantor.com/...`)
   - Verification: Headline fallback hierarchy tested.
5. **Kaler Kantho** (`https://www.kalerkantho.com/...`)
   - Verification: First 400 words truncation verified.

### Category B: Fact-Checking Outlets (Expected: Instant "factcheck" notice without backend call)
6. **Rumor Scanner** (`https://rumorscanner.com/...`)
   - Expected: Green/neutral card stating: *"This looks like a fact-check article. This tool does not score fact-checks."*
   - Verify: Backend network request is NOT triggered in DevTools network tab.
7. **Boom Bangladesh / Fact-Watch** (if added to `factcheck_domains.json`)
   - Expected: Domain match triggers instant fact-check state.

### Category C: Non-Bangla & Edge Cases
8. **English News Article** (e.g., `https://www.bbc.com/news/...`)
   - Expected Result: *"This page does not appear to be in Bangla."* (Band: `not_bangla`).
9. **Short Notice or Category Landing Page** (under 40 words)
   - Expected Result: *"Not enough text to analyze."* (Band: `too_short`).
10. **Empty / Non-Article Page** (e.g., Google Search homepage `https://www.google.com`)
    - Expected Result: *"Not enough text to analyze."* or *"This page does not appear to be in Bangla."*

---

## 3. UI State & Consent Verification Matrix

| State | Trigger | Expected UI Appearance |
|---|---|---|
| **First-Use Consent** | Fresh installation or after clicking "Withdraw Consent" | Consent prompt box with "I Agree" and "Decline" buttons. Analysis blocked until agreed. |
| **Idle** | Consented, extension opened | Single clean button: "Analyze this page" and "Show what will be sent" checkbox |
| **Paste Text Tab (C3)** | Click "Paste text" tab in popup | Shows optional headline input, content textarea, "Show what will be sent" toggle, and "Analyze text" button. |
| **Analyze Selected Text (C4)** | Highlight text on page and click "Analyze selected text" | Reads `window.getSelection()`, applies variant D parsing (first sentence/line as headline), checks 40-word limit and Bangla ratio, and analyzes or previews. |
| **No Selection Warning (C4)** | Click "Analyze selected text" without highlighting text | Shows warning card: "No text selected on page. Highlight text with your mouse and try again." |
| **Preview (C1)** | Checked "Show what will be sent" and clicked "Analyze this page" | Preview box displaying extracted headline, first 400 words of content, word count, "Send for analysis" and "Cancel" buttons. |
| **Loading** | Clicked "Analyze this page" (or "Send for analysis" from preview) | Animated spinner with "Analyzing article..." label |
| **Band: Strong** | High fake-like score (>= 0.70) | Red alert card with exact AGENT.md text + model score |
| **Band: Some** | Moderate score (0.40 - 0.69) | Orange warning card with exact AGENT.md text + model score |
| **Band: None** | Low fake score (< 0.40) | Blue informative card with exact AGENT.md text + model score |
| **Band: Fact-check** | URL matches factcheck_domains.json | Green informational card with fact-check disclaimer |
| **Extraction Failed (C2)** | Page has no article elements or under 40 words after retry | Orange warning card: "Couldn't read this page. Select the text on the page and use Analyze selection, or paste it." with console log of failure reason (no article text). |
| **Error: Offline** | Backend server stopped | Red error card: "Could not reach the analysis server." |
| **Error: Server** | Backend returns 500 | Red error card: "The analysis server returned an error." |
| **Language Toggle** | Click language toggle in header | All strings instantly switch between English and Bangla. |

