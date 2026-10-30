# HUMAN_TODO.md: Unattended Run Action Items for User

This file lists every item requiring human action after the unattended overnight build, ordered by execution priority.

---

### Priority Checklist

1. **Bangla Text Review (M7 / docs/DECISIONS.md)**
   - **Context**: All Bangla strings written in `extension/src/strings.js` are currently flagged as `"needs human review"`.
   - **Action**: Check `extension/src/strings.js` and verify translation accuracy and nuance for all UI states and notices.

2. **Load and Test Unpacked Chrome Extension (M5, M6, M7)**
   - **Action**:
     1. Open Google Chrome and navigate to `chrome://extensions/`.
     2. Enable **Developer mode** (toggle in upper right).
     3. Click **Load unpacked** and select the folder `E:\CODES\fake_news_ai\extension`.
     4. Open extension Options page, verify default backend URL (`http://127.0.0.1:8000`).
     5. Test consent screen, language switch, and article analysis.

3. **Manual Page Tests (M6 / M8 / docs/TEST_PLAN.md)**
   - **Context**: Verification across live web pages requires a running browser session with human observation.
   - **Action**: Run through the checklist in `docs/TEST_PLAN.md` (sample Bangla news sites, Rumor Scanner fact-checks, English pages, very short pages).

4. **Fact-Check Domain List Extension (M7)**
   - **Context**: `extension/config/factcheck_domains.json` currently includes `rumorscanner.com` and initial domains.
   - **Action**: Add any additional known Bangladeshi or regional fact-checking outlets (e.g. `fact-watch.org`, `boomlive.in`, `dismislab.com`).

5. **Server & Domain Setup & Deployment (M4)**
   - **Context**: Antigravity runs locally and cannot access remote hosts or provision DNS.
   - **Action**:
     1. Provision an Ubuntu VPS (e.g., Hostinger KVM 2).
     2. Point your domain or subdomain DNS A record to the VPS IP.
     3. Follow step-by-step instructions in `deploy/DEPLOY.md`.
     4. Copy `backend/model/` to `/opt/fake_news/backend/model/` on the VPS.
     5. Run `docker compose up -d` in `/opt/fake_news/deploy`.

6. **Screenshots for Project Book (M9)**
   - **Action**: Take screenshots of:
     - Extension popup in "idle" state
     - Consent dialog
     - Analysis loading state
     - "Strong resemblance" result
     - "Some resemblance" result
     - "No strong fake-news signals" result
     - Fact-check bypass banner (`rumorscanner.com`)
     - Options page

