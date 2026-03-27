function createChromeStorageAdapter(storageKey, debugKey) {
  return {
    loadPrefs: async function () {
      const data = await chrome.storage.local.get([storageKey, debugKey]);
      return {
        active: data[storageKey] === '1',
        debug: data[debugKey] === '1',
      };
    },
    saveState: async function (active) {
      try {
        await chrome.storage.local.set({ [storageKey]: active ? '1' : '0' });
      } catch (_) {
        // ignore write errors
      }
    },
    subscribe: function (onChange) {
      function handleChanges(changes, area) {
        if (area !== 'local') return;
        if (changes[storageKey]) {
          onChange({ active: changes[storageKey].newValue === '1' });
        }
        if (changes[debugKey]) {
          onChange({ debug: changes[debugKey].newValue === '1' });
        }
      }

      chrome.storage.onChanged.addListener(handleChanges);
      return function unsubscribe() {
        chrome.storage.onChanged.removeListener(handleChanges);
      };
    },
  };
}
