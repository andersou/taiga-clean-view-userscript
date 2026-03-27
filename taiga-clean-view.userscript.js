// ==UserScript==
// @name         Taiga Taskboard – Clean view
// @namespace    http://tampermonkey.net/
// @version      1.0.4
// @description  Toggle compact taskboard: hide large summary, zero header padding and key margins.
// @author       Anderson Souza
// @match        https://tree.taiga.io/project/*/taskboard/*
// @match        https://*.taiga.io/project/*/taskboard/*
// @icon         https://www.google.com/s2/favicons?sz=64&domain=taiga.io
// @grant        none
// @run-at       document-idle
// @noframes
// ==/UserScript==

(function () {
  'use strict';

  const STORAGE_KEY = 'taiga-clean-view';
  const ROOT_CLASS = 'taiga-clean-view-active';
  const BUTTON_ATTR = 'data-taiga-clean-view-toggle';
  const STYLE_ID = 'taiga-clean-view-styles';
  const LOG_PREFIX = '[Taiga Clean View]';
  const DEBUG_KEY = 'taiga-clean-view-debug';
  const ICON_ENABLE_CLEAN = '🧹';
  const ICON_RESTORE_VIEW = '↺';
  let missingHeaderLogCount = 0;

  function isDebugEnabled() {
    try {
      return localStorage.getItem(DEBUG_KEY) === '1';
    } catch (_) {
      return false;
    }
  }

  function log(...args) {
    if (!isDebugEnabled()) return;
    console.log(LOG_PREFIX, ...args);
  }

  function warn(...args) {
    console.warn(LOG_PREFIX, ...args);
  }

  function error(...args) {
    console.error(LOG_PREFIX, ...args);
  }

  function injectStyles() {
    if (document.getElementById(STYLE_ID)) {
      log('Styles already injected');
      return;
    }
    const style = document.createElement('style');
    style.id = STYLE_ID;
    style.textContent = `
.${ROOT_CLASS} .taskboard-inner > div.summary.large-summary,
.${ROOT_CLASS} .taskboard-inner .summary.large-summary,
.${ROOT_CLASS} .summary.large-summary { display: none !important; }
.${ROOT_CLASS} .taskboard-header { padding: 0 !important; }
.${ROOT_CLASS} .graphics-container { margin: 0 !important; }
.${ROOT_CLASS} .taskboard-actions { margin: 0 !important; }
`;
    document.documentElement.appendChild(style);
    log('Styles injected');
  }

  function loadState() {
    try {
      return localStorage.getItem(STORAGE_KEY) === '1';
    } catch {
      return false;
    }
  }

  function saveState(active) {
    try {
      localStorage.setItem(STORAGE_KEY, active ? '1' : '0');
    } catch (_) { }
  }

  function applyRootState(active) {
    document.documentElement.classList.toggle(ROOT_CLASS, active);
    const btn = document.querySelector(`[${BUTTON_ATTR}]`);
    if (btn) {
      btn.setAttribute('aria-pressed', active ? 'true' : 'false');
      updateToggleButtonUI(btn, active);
    }
    log('Applied root state', { active, hasButton: !!btn });
  }

  function updateToggleButtonUI(btn, active) {
    const isCleanEnabled = active;
    btn.textContent = isCleanEnabled ? ICON_RESTORE_VIEW : ICON_ENABLE_CLEAN;
    btn.setAttribute(
      'aria-label',
      isCleanEnabled ? 'Restaurar visual original do taskboard' : 'Ativar visual limpo do taskboard'
    );
    btn.title = isCleanEnabled ? 'Restore view' : 'Clean view';
  }

  function findTitleAnchor(header) {
    return (
      header.querySelector('h1') ||
      header.querySelector('h2') ||
      header.querySelector('.title') ||
      header.querySelector('[class*="title"]') ||
      header.querySelector('a[href*="/taskboard/"]')
    );
  }

  function ensureToggleButton() {
    const header = document.querySelector('.taskboard-header');
    if (!header) {
      missingHeaderLogCount += 1;
      if (missingHeaderLogCount <= 3 || missingHeaderLogCount % 20 === 0) {
        warn('Taskboard header not found yet', {
          url: location.href,
          attempt: missingHeaderLogCount,
        });
      }
      return;
    }

    if (header.querySelector(`[${BUTTON_ATTR}]`)) {
      log('Toggle button already exists');
      return;
    }

    const active = loadState();
    applyRootState(active);

    const btn = document.createElement('button');
    btn.type = 'button';
    btn.setAttribute(BUTTON_ATTR, '');
    btn.setAttribute('aria-pressed', active ? 'true' : 'false');
    btn.style.cssText =
      'margin-left:0.45em;padding:0 0.15em;font:inherit;font-size:1.05em;line-height:1;cursor:pointer;vertical-align:middle;background:transparent;border:0;';
    updateToggleButtonUI(btn, active);

    const anchor = findTitleAnchor(header);
    if (anchor && (anchor.matches('h1') || anchor.matches('h2'))) {
      anchor.appendChild(btn);
      log('Toggle button appended inside title heading');
    } else if (anchor) {
      anchor.insertAdjacentElement('afterend', btn);
      log('Toggle button inserted after title anchor');
    } else {
      if (getComputedStyle(header).display !== 'flex') {
        header.style.display = 'flex';
        header.style.alignItems = 'center';
      }
      btn.style.marginLeft = 'auto';
      header.appendChild(btn);
      warn('Title anchor not found, appended button to header');
    }

    btn.addEventListener('click', () => {
      const next = !document.documentElement.classList.contains(ROOT_CLASS);
      log('Toggle clicked', { previous: !next, next });
      applyRootState(next);
      saveState(next);
    });

    log('Toggle button created', { active });
  }

  function isTaskboardRoute() {
    return /\/taskboard(\/|$)/.test(location.pathname);
  }

  function init() {
    document.documentElement.setAttribute('data-taiga-clean-view-script', '1');
    window.__taigaCleanViewLoadedAt = new Date().toISOString();
    warn('Userscript init', {
      href: location.href,
      path: location.pathname,
      readyState: document.readyState,
      debug: isDebugEnabled(),
    });

    log('Init started', {
      href: location.href,
      readyState: document.readyState,
      debug: isDebugEnabled(),
    });

    if (!isTaskboardRoute()) {
      warn('URL does not look like taskboard route', location.pathname);
    }

    try {
      injectStyles();
      applyRootState(loadState());
    } catch (err) {
      error('Failed during initial setup', err);
    }

    let debounceId;
    const scheduleEnsure = () => {
      clearTimeout(debounceId);
      debounceId = window.setTimeout(ensureToggleButton, 50);
    };

    ensureToggleButton();

    if (document.body) {
      const obs = new MutationObserver(scheduleEnsure);
      obs.observe(document.body, { childList: true, subtree: true });
      log('MutationObserver attached');
    } else {
      warn('document.body not available during init');
    }

    window.addEventListener('popstate', scheduleEnsure);
    log('popstate listener attached');
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
  warn('Userscript file evaluated');
})();
