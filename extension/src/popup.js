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
  const previewState = document.getElementById("preview-state");

  const appTitle = document.getElementById("app-title");
  const langSwitchBtn = document.getElementById("lang-switch-btn");
  const analyzeBtn = document.getElementById("analyze-btn");
  const reanalyzeBtn = document.getElementById("reanalyze-btn");

  const showPreviewCheckbox = document.getElementById("show-preview-checkbox");
  const showPreviewLabel = document.getElementById("show-preview-label");
  const previewHeading = document.getElementById("preview-heading");
  const previewHeadlineLbl = document.getElementById("preview-headline-lbl");
  const previewHeadline = document.getElementById("preview-headline");
  const previewBodyLbl = document.getElementById("preview-body-lbl");
  const previewBody = document.getElementById("preview-body");
  const previewWordCountLbl = document.getElementById("preview-word-count-lbl");
  const previewWordCount = document.getElementById("preview-word-count");
  const previewSendBtn = document.getElementById("preview-send-btn");
  const previewCancelBtn = document.getElementById("preview-cancel-btn");

  const consentText = document.getElementById("consent-text");
  const consentAgreeBtn = document.getElementById("consent-agree-btn");
  const consentDeclineBtn = document.getElementById("consent-decline-btn");

  const resultCard = document.getElementById("result-card");
  const resultMessage = document.getElementById("result-message");
  const resultScore = document.getElementById("result-score");
  const disclaimerText = document.getElementById("disclaimer-text");
  const openOptions = document.getElementById("open-options");

  let pendingExtraction = null;

  // Load language, consent state, and show-preview preference from storage
  chrome.storage.local.get(["language", "consentGiven", "showPreview"], (items) => {
    currentLang = items.language || "en";
    if (showPreviewCheckbox) {
      showPreviewCheckbox.checked = items.showPreview || false;
    }
    updateTexts();

    if (!items.consentGiven) {
      showState("consent");
    } else {
      showState("idle");
    }
  });

  if (showPreviewCheckbox) {
    showPreviewCheckbox.addEventListener("change", (e) => {
      chrome.storage.local.set({ showPreview: e.target.checked });
    });
  }

  // Preview state button listeners
  previewSendBtn.addEventListener("click", () => {
    if (pendingExtraction) {
      sendExtractionToBackend(pendingExtraction);
    }
  });

  previewCancelBtn.addEventListener("click", () => {
    pendingExtraction = null;
    showState("idle");
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

      // C1: Check if "Show what will be sent" is enabled
      const showPreview = showPreviewCheckbox && showPreviewCheckbox.checked;
      if (showPreview) {
        pendingExtraction = extracted;
        showPreviewView(extracted);
        return;
      }

      // Otherwise send directly
      sendExtractionToBackend(extracted);

    } catch (err) {
      console.error(err);
      showError("error_offline");
    }
  }

  function showPreviewView(extracted) {
    showState("preview");
    previewHeadline.innerText = extracted.headline || "(No headline)";
    previewBody.innerText = extracted.content || "(No content)";
    previewWordCount.innerText = extracted.wordCount !== undefined ? extracted.wordCount : extracted.content.split(/\s+/).filter(Boolean).length;
  }

  function sendExtractionToBackend(extracted) {
    showState("loading");
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
  }

  function showState(state) {
    idleState.style.display = state === "idle" ? "block" : "none";
    consentState.style.display = state === "consent" ? "block" : "none";
    loadingState.style.display = state === "loading" ? "block" : "none";
    resultState.style.display = state === "result" ? "block" : "none";
    previewState.style.display = state === "preview" ? "block" : "none";
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

    if (showPreviewLabel) showPreviewLabel.innerText = dict.show_preview_label;
    if (previewHeading) previewHeading.innerText = dict.preview_title;
    if (previewHeadlineLbl) previewHeadlineLbl.innerText = dict.preview_headline_label;
    if (previewBodyLbl) previewBodyLbl.innerText = dict.preview_body_label;
    if (previewWordCountLbl) previewWordCountLbl.innerText = dict.preview_word_count_label;
    if (previewSendBtn) previewSendBtn.innerText = dict.send_analysis_button;
    if (previewCancelBtn) previewCancelBtn.innerText = dict.cancel_button;
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

