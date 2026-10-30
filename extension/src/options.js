/**
 * extension/src/options.js
 * Saves and restores extension options using chrome.storage.local.
 */

document.addEventListener("DOMContentLoaded", () => {
  const backendUrlInput = document.getElementById("backend-url");
  const apiKeyInput = document.getElementById("api-key");
  const languageSelect = document.getElementById("language-select");
  const useMockBackendInput = document.getElementById("use-mock-backend");
  const saveBtn = document.getElementById("save-btn");
  const withdrawConsentBtn = document.getElementById("withdraw-consent-btn");
  const statusMsg = document.getElementById("status-msg");

  // Load saved settings
  chrome.storage.local.get(["backendUrl", "apiKey", "language", "useMockBackend"], (items) => {
    backendUrlInput.value = items.backendUrl || "http://127.0.0.1:8000";
    apiKeyInput.value = items.apiKey || "";
    languageSelect.value = items.language || "en";
    useMockBackendInput.checked = items.useMockBackend || false;
    updateLanguage(items.language || "en");
  });

  // Save settings
  saveBtn.addEventListener("click", () => {
    const backendUrl = backendUrlInput.value.trim() || "http://127.0.0.1:8000";
    const apiKey = apiKeyInput.value.trim();
    const language = languageSelect.value;
    const useMockBackend = useMockBackendInput.checked;

    chrome.storage.local.set({
      backendUrl: backendUrl,
      apiKey: apiKey,
      language: language,
      useMockBackend: useMockBackend
    }, () => {
      showStatus(STRINGS[language].saved_message, "#0d8a2e");
      updateLanguage(language);
    });
  });

  // Withdraw consent
  withdrawConsentBtn.addEventListener("click", () => {
    chrome.storage.local.set({ consentGiven: false }, () => {
      const lang = languageSelect.value;
      showStatus(STRINGS[lang].consent_withdrawn_message, "#c5221f");
    });
  });

  languageSelect.addEventListener("change", (e) => {
    updateLanguage(e.target.value);
  });

  function updateLanguage(lang) {
    const dict = STRINGS[lang] || STRINGS.en;
    document.getElementById("options-title").innerText = dict.options_title;
    document.getElementById("lbl-backend-url").innerText = dict.backend_url_label;
    document.getElementById("lbl-api-key").innerText = dict.api_key_label;
    document.getElementById("save-btn").innerText = dict.save_button;
    document.getElementById("withdraw-consent-btn").innerText = dict.withdraw_consent_button;
  }

  function showStatus(text, color) {
    statusMsg.innerText = text;
    statusMsg.style.color = color;
    statusMsg.style.display = "block";
    setTimeout(() => {
      statusMsg.style.display = "none";
    }, 3000);
  }
});
