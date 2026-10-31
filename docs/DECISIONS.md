# docs/DECISIONS.md: Project Decision Log

This log records decisions, adaptations, and notes as specified in AGENT.md section 0 rule 9 and UNATTENDED execution mode instructions.

## Format
- **Date**: YYYY-MM-DD
- **Decision**: Summary of decision
- **Reason**: Rationale and context

---

## 2026-10-31: Unattended Execution Setup
- **Decision**: Enabled continuous unattended execution covering M0 through M9 per user instructions.
- **Reason**: User requested an unattended session while asleep with automatic fallback to mock/written states if blocked.

## 2026-10-31: Normalizer Commit Hash & PyTorch CPU Pin
- **Decision**: Pinned normalizer git dependency to commit `d405944dde5ceeacb7c2fd3245ae2a9dea5f35c9` (`git+https://github.com/csebuetnlp/normalizer.git@d405944dde5ceeacb7c2fd3245ae2a9dea5f35c9`). Pinned PyTorch to `torch==2.15.0+cpu`.
- **Reason**: AGENT.md section 2 step 2 instructs recording the normalizer commit hash. `transformers==5.20.2` requires PyTorch >= 2.6 (disabling torch integration if < 2.6), and `2.15.0+cpu` satisfies this on CPU with PyTorch wheel repository.

## 2026-10-31: M4 Docker Execution Status
- **Decision**: Dockerfile, docker-compose.yml, Caddyfile, and DEPLOY.md were written and validated structurally. The local Docker Desktop daemon is not running on the Windows host, so Docker Compose is marked "written, not run" in accordance with user instructions. Local uvicorn execution is documented and verified.
- **Reason**: Unattended session rule: "If Docker or another tool is not available, write the files, mark them 'written, not run', and continue."

## 2026-10-31: C1 "Show what will be sent" Preview Option
- **Decision**: Added a "Show what will be sent" checkbox option in the popup stored in `chrome.storage.local`. When enabled, clicking "Analyze this page" switches the popup to a review screen showing the extracted headline, first 400 words of body content, and word count with "Send for analysis" and "Cancel" buttons. Added corresponding English and Bangla strings to `extension/src/strings.js`.
- **Reason**: Implements change request C1. All new Bangla strings are flagged as "needs human review".

## 2026-10-31: C2 Robust Article Extraction Pipeline
- **Decision**: Updated `extension/src/content.js` to execute a multi-tier extraction strategy:
  1. Mozilla Readability first.
  2. If Readability fails or returns under 40 words, finds the largest text block among `article`, `[itemprop='articleBody']`, and `main`.
  3. If text remains under 40 words, waits 800ms and retries extraction once to support late-loading pages.
  4. If all attempts fail, returns `band: "extraction_failed"` and logs the reason (`words found`, method) to console without logging any article text (privacy rule compliance).
  5. The popup displays: *"Couldn't read this page. Select the text on the page and use Analyze selection, or paste it."*
- **Reason**: Implements change request C2. Protects user privacy while providing clear recovery action.

## 2026-10-31: C3 "Paste text" Tab
- **Decision**: Added a tabbed interface in `extension/src/popup.html` switching between "Current page" and "Paste text". The paste view contains an optional headline input and a textarea for article content. If no headline is provided, the first line (or first Dari/period-delimited sentence) is extracted as the headline and the remainder as content (matching evaluation variant D). Enforces standard 40-word minimum, 400-word truncation, and 50% Bangla ratio checks. Added English and Bangla strings to `extension/src/strings.js` (flagged for human review).
- **Reason**: Implements change request C3.





