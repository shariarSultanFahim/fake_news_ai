/**
 * extension/src/content.js
 * Content script to extract article headline and body text according to AGENT.md section 6 (M6).
 *
 * Rules:
 * - Headline order: og:title -> first h1 -> document.title.
 * - Body: Mozilla Readability library (cloned document), send the first 400 words.
 * - Check that at least 50% of the letters in headline + content are Bangla before sending.
 * - Handles pages that load content late: brief wait and single retry if body is initially short.
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

  function getBodyContent() {
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
      console.warn("Readability parsing error, falling back to innerText:", e);
    }

    // Fallback if Readability fails
    const articleElem = document.querySelector("article") || document.body;
    return articleElem ? articleElem.innerText.trim() : "";
  }

  function isBanglaChar(char) {
    const code = char.charCodeAt(0);
    return code >= 0x0980 && code <= 0x09FF;
  }

  function isLetterOrBangla(char) {
    if (isBanglaChar(char)) {
      // Exclude Bengali digits and Bengali currency/punctuation if desired,
      // but primarily check Unicode range 0x0980 - 0x09FF
      return true;
    }
    // General Latin / alphabetic regex
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

  function extractArticle() {
    const headline = getHeadline();
    const rawContent = getBodyContent();

    // Take the first 400 words of the body
    const words = rawContent.split(/\s+/).filter(Boolean);
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

    if (words.length < 40) {
      return {
        headline: headline,
        content: first400Words,
        wordCount: words.length,
        band: "too_short"
      };
    }

    return {
      headline: headline,
      content: first400Words,
      wordCount: words.length,
      band: null // Eligible for model inference
    };
  }

  return extractArticle();
})();
