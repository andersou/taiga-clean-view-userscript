function createLocalStorageAdapter(storageKey, debugKey) {
  function readFlag(key) {
    try {
      return localStorage.getItem(key) === '1';
    } catch (_) {
      return false;
    }
  }

  return {
    loadPrefs: async function () {
      return {
        active: readFlag(storageKey),
        debug: readFlag(debugKey),
      };
    },
    saveState: async function (active) {
      try {
        localStorage.setItem(storageKey, active ? '1' : '0');
      } catch (_) {
        // ignore write errors
      }
    },
    subscribe: function (onChange) {
      function handleStorage(event) {
        if (event.storageArea !== localStorage) return;
        if (event.key === storageKey) {
          onChange({ active: event.newValue === '1' });
        }
        if (event.key === debugKey) {
          onChange({ debug: event.newValue === '1' });
        }
      }

      window.addEventListener('storage', handleStorage);
      return function unsubscribe() {
        window.removeEventListener('storage', handleStorage);
      };
    },
  };
}
