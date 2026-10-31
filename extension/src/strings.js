/**
 * extension/src/strings.js
 * User-facing wording in English and Bangla as specified in AGENT.md section 5.
 * Note: Bangla strings are flagged as "needs human review" per docs/DECISIONS.md.
 */

const STRINGS = {
  en: {
    app_title: "Bangla Fake News Detector",
    analyze_button: "Analyze this page",
    analyzing: "Analyzing article...",
    options_title: "Settings",
    backend_url_label: "Backend Server URL",
    api_key_label: "API Key (Optional)",
    save_button: "Save Settings",
    saved_message: "Settings saved successfully.",
    withdraw_consent_button: "Withdraw Consent",
    consent_withdrawn_message: "Consent has been withdrawn.",
    language_label: "Language / ভাষা",

    // Bands & Results
    strong: "Strong resemblance to content previously found to be false or misleading.",
    some: "Some resemblance to false or misleading content.",
    none: "No strong fake-news signals found. This does not mean the article is true.",
    too_short: "Not enough text to analyze.",
    not_bangla: "This page does not appear to be in Bangla.",
    factcheck: "This looks like a fact-check article. This tool does not score fact-checks.",

    // Errors
    error_offline: "Could not reach the analysis server.",
    error_server: "The analysis server returned an error. Try again later.",

    // Disclaimer & Consent
    disclaimer: "Automated estimate from a machine-learning model. It is not a fact-check. Verify with trusted sources.",
    consent_prompt: "To analyze an article, this extension sends its headline and the first part of its text to the project's server. The text is not stored. Do you agree?",
    consent_agree: "I Agree",
    consent_decline: "Decline",

    // Supporting Details
    model_score_label: "Model score",
    details_label: "Details",

    // C1: Show what will be sent (Needs human review)
    show_preview_label: "Show what will be sent",
    preview_title: "Content to be analyzed",
    preview_headline_label: "Headline:",
    preview_body_label: "Body content (first 400 words):",
    preview_word_count_label: "Word count:",
    send_analysis_button: "Send for analysis",
    cancel_button: "Cancel"
  },

  bn: {
    app_title: "বাংলা ফেক নিউজ ডিটেক্টর",
    analyze_button: "এই পৃষ্ঠা বিশ্লেষণ করুন",
    analyzing: "প্রতিবেদন বিশ্লেষণ করা হচ্ছে...",
    options_title: "সেটিংস",
    backend_url_label: "ব্যাকএন্ড সার্ভার ইউআরএল",
    api_key_label: "এপিআই কি (ঐচ্ছিক)",
    save_button: "সেটিংস সংরক্ষণ করুন",
    saved_message: "সেটিংস সফলভাবে সংরক্ষিত হয়েছে।",
    withdraw_consent_button: "সম্মতি প্রত্যাহার করুন",
    consent_withdrawn_message: "সম্মতি প্রত্যাহার করা হয়েছে।",
    language_label: "ভাষা / Language",

    // Bands & Results (Needs human review)
    strong: "পূর্বে অসত্য বা বিভ্রান্তিকর প্রমাণিত তথ্যের সাথে জোরালো সাদৃশ্য রয়েছে।",
    some: "অসত্য বা বিভ্রান্তিকর তথ্যের সাথে কিছুটা সাদৃশ্য রয়েছে।",
    none: "কোনো জোরালো ভুয়া সংবাদের লক্ষণ পাওয়া যায়নি। তবে এর মানে এই নয় যে প্রতিবেদনটি নিশ্চিতভাবে সত্য।",
    too_short: "বিশ্লেষণ করার জন্য পর্যাপ্ত তথ্য বা লেখা নেই।",
    not_bangla: "এই পৃষ্ঠাটি বাংলায় রচিত বলে প্রতীয়মান হচ্ছে না।",
    factcheck: "এটি একটি ফ্যাক্ট-চেক (তথ্য যাচাই) প্রতিবেদন বলে মনে হচ্ছে। এই টুলটি ফ্যাক্ট-চেক প্রতিবেদন বিশ্লেষণ করে না।",

    // Errors (Needs human review)
    error_offline: "বিশ্লেষণ সার্ভারের সাথে সংযোগ স্থাপন করা সম্ভব হয়নি।",
    error_server: "বিশ্লেষণ সার্ভারে ত্রুটি দেখা দিয়েছে। কিছুক্ষণ পর আবার চেষ্টা করুন।",

    // Disclaimer & Consent (Needs human review)
    disclaimer: "এটি একটি মেশিন-লার্নিং মডেলের স্বয়ংক্রিয় আনুমানিক ধারণা। এটি চূড়ান্ত কোনো তথ্য যাচাই (ফ্যাক্ট-চেক) নয়। নির্ভরযোগ্য সূত্রের মাধ্যমে নিজে যাচাই করুন।",
    consent_prompt: "একটি প্রতিবেদন বিশ্লেষণ করতে, এই এক্সটেনশনটি এর শিরোনাম এবং সংবাদের শুরুর অংশটুকু আমাদের সার্ভারে পাঠায়। কোনো তথ্য বা লেখা সার্ভারে সংরক্ষণ করা হয় না। আপনি কি সম্মত?",
    consent_agree: "আমি সম্মত",
    consent_decline: "সম্মতি নেই",

    // Supporting Details
    model_score_label: "মডেল স্কোর",
    details_label: "বিস্তারিত",

    // C1: Show what will be sent (Needs human review)
    show_preview_label: "যা পাঠানো হবে তা দেখুন",
    preview_title: "বিশ্লেষণের জন্য নির্ধারিত বিষয়বস্তু",
    preview_headline_label: "শিরোনাম:",
    preview_body_label: "মূল বক্তব্য (প্রথম ৪০০ শব্দ):",
    preview_word_count_label: "শব্দ সংখ্যা:",
    send_analysis_button: "বিশ্লেষণের জন্য পাঠান",
    cancel_button: "বাতিল"
  }
};

// Export for module or browser environments
if (typeof module !== "undefined" && module.exports) {
  module.exports = STRINGS;
}

