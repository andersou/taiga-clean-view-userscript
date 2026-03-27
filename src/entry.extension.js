(function () {
  'use strict';

  const STORAGE_KEY = 'taiga-clean-view';
  const DEBUG_KEY = 'taiga-clean-view-debug';

  const app = createTaigaCleanViewApp({
    environmentName: 'Extension content script',
    markerAttribute: 'data-taiga-clean-view-extension',
    loadedAtProperty: '__taigaCleanViewExtensionAt',
    storage: createChromeStorageAdapter(STORAGE_KEY, DEBUG_KEY),
  });

  app.start();
})();
