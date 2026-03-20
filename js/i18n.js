/* ════════════════════════════════════════════════════
   i18n.js — Internationalization logic
   Depends on: locales/translations.js (TRANSLATIONS global)

   Usage in HTML:
     data-i18n="section.key"       → sets textContent
     data-i18n-html="section.key"  → sets innerHTML (for text with tags)
════════════════════════════════════════════════════ */

(function () {

  /* ── Persisted language (defaults to Spanish) ─────── */
  var currentLang = localStorage.getItem('bb_lang') || 'es';

  /* ── Resolve a dot-notation key from TRANSLATIONS ─── */
  function t(key) {
    var parts = key.split('.');
    var val   = TRANSLATIONS[currentLang];
    for (var i = 0; i < parts.length; i++) {
      if (val == null) return key;
      val = val[parts[i]];
    }
    return (val != null) ? val : key;
  }

  /* ── Update the lang toggle button visuals ─────────── */
  function updateToggle() {
    var esEl = document.getElementById('lang-es');
    var enEl = document.getElementById('lang-en');
    if (esEl) esEl.style.color = currentLang === 'es' ? '#60a5fa' : 'rgba(255,255,255,0.32)';
    if (enEl) enEl.style.color = currentLang === 'en' ? '#60a5fa' : 'rgba(255,255,255,0.32)';
  }

  /* ── Apply all translations to the DOM ─────────────── */
  function applyTranslations() {
    /* html[lang] attribute */
    document.documentElement.lang = currentLang;

    /* <title> */
    document.title = t('meta.title');

    /* Plain text — data-i18n="key" */
    document.querySelectorAll('[data-i18n]').forEach(function (el) {
      el.textContent = t(el.getAttribute('data-i18n'));
    });

    /* HTML content — data-i18n-html="key" (preserves inner tags) */
    document.querySelectorAll('[data-i18n-html]').forEach(function (el) {
      el.innerHTML = t(el.getAttribute('data-i18n-html'));
    });

    /* Placeholder text — data-i18n-placeholder="key" */
    document.querySelectorAll('[data-i18n-placeholder]').forEach(function (el) {
      el.setAttribute('placeholder', t(el.getAttribute('data-i18n-placeholder')));
    });

    /* aria-label — data-i18n-aria="key" */
    document.querySelectorAll('[data-i18n-aria]').forEach(function (el) {
      el.setAttribute('aria-label', t(el.getAttribute('data-i18n-aria')));
    });

    updateToggle();

    /* Notify other scripts that the language changed */
    window.dispatchEvent(new CustomEvent('langchange', { detail: { lang: currentLang } }));
  }

  /* ── Toggle between es / en ─────────────────────────── */
  function toggleLang() {
    currentLang = (currentLang === 'es') ? 'en' : 'es';
    localStorage.setItem('bb_lang', currentLang);
    applyTranslations();
  }

  /* ── Expose translation function globally ───────────── */
  window.bb_t = t;

  /* ── Init on DOM ready ──────────────────────────────── */
  document.addEventListener('DOMContentLoaded', function () {
    var btn = document.getElementById('lang-btn');
    if (btn) btn.addEventListener('click', toggleLang);
    applyTranslations();
  });

})();
