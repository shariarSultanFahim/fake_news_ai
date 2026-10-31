/**
 * extension/src/popup.js
 * Controls popup UI states: idle, consent, loading, result bands, and errors.
 */

let currentLang = "en";

document.addEventListener("DOMContentLoaded", async () => {
  const idleState = document.getElementById("idle-state");
  const consentState = document.getElementById("consent-state");
  const loadingState = document.getElementById("loading-state");
  const resultState = document.getElementById("result-state");

  const appTitle = document.getElementById("app-title");
  const langSwitchBtn = document.getElementById("lang-switch-btn");
  const analyzeBtn = document.getElementById("analyze-btn");
  const reanalyzeBtn = document.getElementById("reanalyze-btn");

  const consentText = document.getElementById("consent-text");
  const consentAgreeBtn = document.getElementById("consent-agree-btn");
  const consentDeclineBtn = document.getElementById("consent-decline-btn");

  const resultCard = document.getElementById("result-card");
  const resultMessage = document.getElementById("result-message");
  const resultScore = document.getElementById("result-score");
  const disclaimerText = document.getElementById("disclaimer-text");
  const openOptions = document.getElementById("open-options");

  // Load language and consent state from storage
  chrome.storage.local.get(["language", "consentGiven"], (items) => {
    currentLang = items.language || "en";
    updateTexts();

    if (!items.consentGiven) {
      showState("consent");
    } else {
      showState("idle");
    }
  });

  // Language switch
  langSwitchBtn.addEventListener("click", () => {
    currentLang = currentLang === "en" ? "bn" : "en";
    chrome.storage.local.set({ language: currentLang }, () => {
      updateTexts();
    });
  });

  // Open settings
  openOptions.addEventListener("click", (e) => {
    e.preventDefault();
    chrome.runtime.openOptionsPage();
  });

  // Consent actions
  consentAgreeBtn.addEventListener("click", () => {
    chrome.storage.local.set({ consentGiven: true }, () => {
      showState("idle");
    });
  });

  consentDeclineBtn.addEventListener("click", () => {
    window.close();
  });

  // Analyze button triggers extraction and background inference
  analyzeBtn.addEventListener("click", performAnalysis);
  reanalyzeBtn.addEventListener("click", performAnalysis);

  async function performAnalysis() {
    showState("loading");

    try {
      const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
      if (!tab || !tab.id) {
        showError("error_offline");
        return;
      }

      // Check fact-check domains list (M7)
      const tabUrl = new URL(tab.url || "about:blank");
      const host = tabUrl.hostname.toLowerCase();

      // Read factcheck domains config
      const factcheckDomains = await loadFactcheckDomains();
      const isFactCheck = factcheckDomains.some(domain => host === domain || host.endsWith("." + domain));

      if (isFactCheck) {
        showResult({
          band: "factcheck",
          p_fake: null
        });
        return;
      }

      // Execute extraction content script in the active tab (M6)
      const extractionResults = await chrome.scripting.executeScript({
        target: { tabId: tab.id },
        files: ["vendor/Readability.js", "src/content.js"]
      });

      const extracted = extractionResults && extractionResults[0] && extractionResults[0].result;

      if (!extracted) {
        showResult({ band: "too_short", p_fake: null });
        return;
      }

      // If client pre-check indicates not_bangla or too_short
      if (extracted.band) {
        showResult({
          band: extracted.band,
          p_fake: null
        });
        return;
      }

      // Send payload to background service worker for network call
      chrome.runtime.sendMessage({
        action: "predict",
        payload: {
          headline: extracted.headline,
          content: extracted.content
        }
      }, (response) => {
        if (chrome.runtime.lastError) {
          showError("error_offline");
          return;
        }

        if (!response || !response.success) {
          const errType = (response && response.errorType) || "error_server";
          showError(errType);
          return;
        }

        showResult(response.data);
      });

    } catch (err) {
      console.error(err);
      showError("error_offline");
    }
  }

  function showState(state) {
    idleState.style.display = state === "idle" ? "block" : "none";
    consentState.style.display = state === "consent" ? "block" : "none";
    loadingState.style.display = state === "loading" ? "block" : "none";
    resultState.style.display = state === "result" ? "block" : "none";
  }

  function showResult(data) {
    showState("result");
    const dict = STRINGS[currentLang] || STRINGS.en;
    const band = data.band;

    // Reset card class
    resultCard.className = `card ${band}`;

    // Get message according to band
    resultMessage.innerText = dict[band] || dict.error_server;

    // Model score supporting detail (NEVER use words true/authentic/safe)
    if (data.p_fake !== null && data.p_fake !== undefined) {
      resultScore.style.display = "block";
      resultScore.innerText = `${dict.model_score_label}: ${Number(data.p_fake).toFixed(2)}`;
    } else {
      resultScore.style.display = "none";
    }

    disclaimerText.innerText = dict.disclaimer;
  }

  function showError(errorType) {
    showState("result");
    const dict = STRINGS[currentLang] || STRINGS.en;
    resultCard.className = "card error";
    resultMessage.innerText = dict[errorType] || dict.error_server;
    resultScore.style.display = "none";
    disclaimerText.innerText = dict.disclaimer;
  }

  function updateTexts() {
    const dict = STRINGS[currentLang] || STRINGS.en;
    appTitle.innerText = dict.app_title;
    langSwitchBtn.innerText = currentLang === "en" ? "বাংলা" : "English";
    analyzeBtn.innerText = dict.analyze_button;
    reanalyzeBtn.innerText = currentLang === "en" ? "Analyze again" : "পুনরায় বিশ্লেষণ";

    consentText.innerText = dict.consent_prompt;
    consentAgreeBtn.innerText = dict.consent_agree;
    consentDeclineBtn.innerText = dict.consent_decline;

    disclaimerText.innerText = dict.disclaimer;
    openOptions.innerText = dict.options_title;
  }

  async function loadFactcheckDomains() {
    try {
      const url = chrome.runtime.getURL("config/factcheck_domains.json");
      const resp = await fetch(url);
      if (resp.ok) {
        return await resp.json();
      }
    } catch (e) {
      console.warn("Could not load factcheck domains", e);
    }
    return ["rumorscanner.com"];
  }
});

