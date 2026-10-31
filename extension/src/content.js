/**
 * extension/src/content.js
 * Content script to extract article headline and body text according to AGENT.md section 6 (M6) and C2.
 *
 * Extraction Order (C2):
 * 1. Headline order: og:title -> first h1 -> document.title.
 * 2. Body extraction:
 *    a) Mozilla Readability first.
 *    b) If Readability fails or produces < 40 words, try the largest text block among:
 *       - article
 *       - [itemprop=articleBody]
 *       - main
 *    c) If initial attempt produces < 40 words (late loading content), wait briefly (~800ms) and retry once.
 * 3. If all fail (< 40 words or empty), return extraction_failed: true and log the reason.
 * 4. Send first 400 words. Check that at least 50% of the letters in headline + content are Bangla.
 */

(function () {
  function getHeadline() {
    // 1. og:title
    const ogTitle = document.querySelector('meta[property="og:title"]');
    if (ogTitle && ogTitle.content && ogTitle.content.trim()) {
      return ogTitle.content.trim();
    }

    // 2. First h1
    const h1 = document.querySelector("h1");
    if (h1 && h1.innerText && h1.innerText.trim()) {
      return h1.innerText.trim();
    }

    // 3. document.title
    if (document.title && document.title.trim()) {
      return document.title.trim();
    }

    return "";
  }

  function getWordCount(text) {
    if (!text) return 0;
    return text.trim().split(/\s+/).filter(Boolean).length;
  }

  function extractWithReadability() {
    try {
      if (typeof Readability !== "undefined") {
        const documentClone = document.cloneNode(true);
        const reader = new Readability(documentClone);
        const article = reader.parse();
        if (article && article.textContent && article.textContent.trim()) {
          return article.textContent.trim();
        }
      }
    } catch (e) {
      console.warn("[BanglaFakeNews] Readability exception:", e);
    }
    return "";
  }

  function extractFromSelectors() {
    // Try the largest text block among article, [itemprop=articleBody], main
    const candidateSelectors = ["article", "[itemprop='articleBody']", "main"];
    let bestText = "";
    let maxWords = 0;

    for (const sel of candidateSelectors) {
      const elements = document.querySelectorAll(sel);
      for (const el of elements) {
        const text = (el.innerText || "").trim();
        const words = getWordCount(text);
        if (words > maxWords) {
          maxWords = words;
          bestText = text;
        }
      }
    }

    return bestText;
  }

  function attemptExtraction() {
    let bodyText = extractWithReadability();
    let methodUsed = "readability";

    // If Readability fails or gives under 40 words, try largest block among selectors
    if (getWordCount(bodyText) < 40) {
      const selectorText = extractFromSelectors();
      if (getWordCount(selectorText) > getWordCount(bodyText)) {
        bodyText = selectorText;
        methodUsed = "selectors";
      }
    }

    return { bodyText, methodUsed };
  }

  function isBanglaChar(char) {
    const code = char.charCodeAt(0);
    return code >= 0x0980 && code <= 0x09FF;
  }

  function isLetterOrBangla(char) {
    if (isBanglaChar(char)) {
      return true;
    }
    return /\p{L}/u.test(char);
  }

  function checkBanglaRatio(text) {
    let totalLetters = 0;
    let banglaLetters = 0;

    for (const char of text) {
      if (isLetterOrBangla(char)) {
        totalLetters++;
        if (isBanglaChar(char)) {
          banglaLetters++;
        }
      }
    }

    if (totalLetters === 0) return 0;
    return banglaLetters / totalLetters;
  }

  function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  async function runExtractionPipeline() {
    const headline = getHeadline();

    // 1. First extraction attempt
    let { bodyText, methodUsed } = attemptExtraction();
    let wordCount = getWordCount(bodyText);

    // 2. If < 40 words, page may load content late; wait briefly and retry once
    if (wordCount < 40) {
      await sleep(800);
      const secondAttempt = attemptExtraction();
      if (getWordCount(secondAttempt.bodyText) > wordCount) {
        bodyText = secondAttempt.bodyText;
        methodUsed = `${secondAttempt.methodUsed}_retry`;
        wordCount = getWordCount(bodyText);
      }
    }

    // 3. If still under 40 words or empty, report extraction failure
    // Note: Privacy rule: Log only the failure reason (no article text)
    if (wordCount < 40) {
      console.warn(`[BanglaFakeNews] Article extraction failed. Reason: no article text found or text under 40 words (words found: ${wordCount}, method: ${methodUsed})`);
      return {
        headline: headline,
        content: bodyText,
        wordCount: wordCount,
        band: "extraction_failed",
        failureReason: `no article text (words: ${wordCount})`
      };
    }

    // 4. Take the first 400 words
    const words = bodyText.split(/\s+/).filter(Boolean);
    const first400Words = words.slice(0, 400).join(" ");

    // Check Bangla ratio on headline + first 400 words
    const combined = `${headline} ${first400Words}`.trim();
    const ratio = checkBanglaRatio(combined);

    if (ratio < 0.50) {
      return {
        headline: headline,
        content: first400Words,
        wordCount: words.length,
        band: "not_bangla"
      };
    }

    return {
      headline: headline,
      content: first400Words,
      wordCount: words.length,
      band: null // Eligible for model inference
    };
  }

  return runExtractionPipeline();
})();
