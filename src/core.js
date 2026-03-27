function createTaigaCleanViewApp(options) {
  const storage = options.storage;
  const environmentName = options.environmentName || 'unknown';
  const markerAttribute = options.markerAttribute || 'data-taiga-clean-view';
  const loadedAtProperty = options.loadedAtProperty || '__taigaCleanViewLoadedAt';

  const ROOT_CLASS = 'taiga-clean-view-active';
  const BUTTON_ATTR = 'data-taiga-clean-view-toggle';
  const STYLE_ID = 'taiga-clean-view-styles';
  const LOG_PREFIX = '[Taiga Clean View]';
  const ICON_ENABLE_CLEAN = '🧹';
  const ICON_RESTORE_VIEW = '↺';

  let missingHeaderLogCount = 0;
  let debugEnabled = false;
  let cachedActive = false;

  function log() {
    if (!debugEnabled) return;
    const args = Array.from(arguments);
    console.log.apply(console, [LOG_PREFIX].concat(args));
  }

  function warn() {
    const args = Array.from(arguments);
    console.warn.apply(console, [LOG_PREFIX].concat(args));
  }

  function error() {
    const args = Array.from(arguments);
    console.error.apply(console, [LOG_PREFIX].concat(args));
  }

  function injectStyles() {
    if (document.getElementById(STYLE_ID)) {
      log('Styles already injected');
      return;
    }
    const style = document.createElement('style');
    style.id = STYLE_ID;
    style.textContent =
      '.' + ROOT_CLASS + ' .taskboard-inner > div.summary.large-summary,\n' +
      '.' + ROOT_CLASS + ' .taskboard-inner .summary.large-summary,\n' +
      '.' + ROOT_CLASS + ' .summary.large-summary { display: none !important; }\n' +
      '.' + ROOT_CLASS + ' .taskboard-header { padding: 0 !important; }\n' +
      '.' + ROOT_CLASS + ' .graphics-container { margin: 0 !important; }\n' +
      '.' + ROOT_CLASS + ' .taskboard-actions { margin: 0 !important; }';
    document.documentElement.appendChild(style);
    log('Styles injected');
  }

  function updateToggleButtonUI(btn, active) {
    const isCleanEnabled = active;
    btn.textContent = isCleanEnabled ? ICON_RESTORE_VIEW : ICON_ENABLE_CLEAN;
    btn.setAttribute(
      'aria-label',
      isCleanEnabled
        ? 'Restaurar visual original do taskboard'
        : 'Ativar visual limpo do taskboard'
    );
    btn.title = isCleanEnabled ? 'Restore view' : 'Clean view';
  }

  function applyRootState(active) {
    document.documentElement.classList.toggle(ROOT_CLASS, active);
    const btn = document.querySelector('[' + BUTTON_ATTR + ']');
    if (btn) {
      btn.setAttribute('aria-pressed', active ? 'true' : 'false');
      updateToggleButtonUI(btn, active);
    }
    log('Applied root state', { active: active, hasButton: !!btn });
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

    if (header.querySelector('[' + BUTTON_ATTR + ']')) {
      log('Toggle button already exists');
      return;
    }

    applyRootState(cachedActive);

    const btn = document.createElement('button');
    btn.type = 'button';
    btn.setAttribute(BUTTON_ATTR, '');
    btn.setAttribute('aria-pressed', cachedActive ? 'true' : 'false');
    btn.style.cssText =
      'margin-left:0.45em;padding:0 0.15em;font:inherit;font-size:1.05em;line-height:1;cursor:pointer;vertical-align:middle;background:transparent;border:0;';
    updateToggleButtonUI(btn, cachedActive);

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

    btn.addEventListener('click', function () {
      const next = !document.documentElement.classList.contains(ROOT_CLASS);
      log('Toggle clicked', { previous: !next, next: next });
      cachedActive = next;
      applyRootState(next);
      void storage.saveState(next);
    });

    log('Toggle button created', { active: cachedActive });
  }

  function isTaskboardRoute() {
    return /\/taskboard(\/|$)/.test(location.pathname);
  }

  function onPrefsChange(change) {
    if (typeof change.debug === 'boolean') {
      debugEnabled = change.debug;
    }
    if (typeof change.active === 'boolean') {
      cachedActive = change.active;
      applyRootState(cachedActive);
    }
  }

  async function init() {
    const prefs = await storage.loadPrefs();
    cachedActive = !!prefs.active;
    debugEnabled = !!prefs.debug;

    document.documentElement.setAttribute(markerAttribute, '1');
    window[loadedAtProperty] = new Date().toISOString();

    warn(environmentName + ' init', {
      href: location.href,
      path: location.pathname,
      readyState: document.readyState,
      debug: debugEnabled,
    });

    if (!isTaskboardRoute()) {
      warn('URL does not look like taskboard route', location.pathname);
    }

    try {
      injectStyles();
      applyRootState(cachedActive);
    } catch (err) {
      error('Failed during initial setup', err);
    }

    let debounceId;
    const scheduleEnsure = function () {
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

    if (typeof storage.subscribe === 'function') {
      storage.subscribe(onPrefsChange);
    }

    window.addEventListener('popstate', scheduleEnsure);
    log('popstate listener attached');
  }

  function start() {
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', function () {
        void init();
      });
    } else {
      void init();
    }
  }

  return { start: start };
}
