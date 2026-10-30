/**
 * extension/src/background.js
 * Background service worker handling HTTP communication with the backend.
 * Uses chrome.storage.local for settings and consent.
 */

const DEFAULT_BACKEND_URL = "http://127.0.0.1:8000";

// Message listener for popup/content requests
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === "predict") {
    handlePredict(request.payload)
      .then(response => sendResponse({ success: true, data: response }))
      .catch(error => sendResponse({ success: false, error: error.message, errorType: error.errorType || "error_server" }));
    return true; // Keep message port open for async response
  }

  if (request.action === "getSettings") {
    chrome.storage.local.get(["backendUrl", "apiKey", "consentGiven", "language", "useMockBackend"], (items) => {
      sendResponse({
        backendUrl: items.backendUrl || DEFAULT_BACKEND_URL,
        apiKey: items.apiKey || "",
        consentGiven: items.consentGiven || false,
        language: items.language || "en",
        useMockBackend: items.useMockBackend || false
      });
    });
    return true;
  }
});

async function handlePredict(payload) {
  const settings = await chrome.storage.local.get(["backendUrl", "apiKey", "useMockBackend"]);
  const backendUrl = (settings.backendUrl || DEFAULT_BACKEND_URL).replace(/\/$/, "");
  const apiKey = settings.apiKey || "";
  const useMock = settings.useMockBackend || false;

  // Mock backend mode for offline/UI testing (e.g. M7 checks)
  if (useMock) {
    if (payload.headline && payload.headline.includes("FORCE_OFFLINE")) {
      const err = new Error("Could not reach the analysis server.");
      err.errorType = "error_offline";
      throw err;
    }
    if (payload.headline && payload.headline.includes("FORCE_ERROR")) {
      const err = new Error("Server error.");
      err.errorType = "error_server";
      throw err;
    }
    // Return sample mock strong/some/none
    return {
      band: payload.mockBand || "some",
      p_fake: 0.55,
      threshold: 0.40,
      model_version: "v1-mock",
      word_count: 120,
      truncated: false,
      latency_ms: 45
    };
  }

  const endpoint = `${backendUrl}/predict`;
  const headers = {
    "Content-Type": "application/json"
  };
  if (apiKey) {
    headers["X-API-Key"] = apiKey;
  }

  try {
    const response = await fetch(endpoint, {
      method: "POST",
      headers: headers,
      body: JSON.stringify({
        headline: payload.headline || "",
        content: payload.content || ""
      })
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      const err = new Error(errorData.detail || `Server returned ${response.status}`);
      err.errorType = "error_server";
      err.status = response.status;
      throw err;
    }

    const data = await response.json();
    return data;
  } catch (err) {
    if (err.errorType) {
      throw err;
    }
    // Network failure / offline
    const networkErr = new Error("Could not reach the analysis server.");
    networkErr.errorType = "error_offline";
    throw networkErr;
  }
}
