(function () {
  'use strict';

  const STORAGE_KEY = 'taiga-clean-view';
  const DEBUG_KEY = 'taiga-clean-view-debug';

  const app = createTaigaCleanViewApp({
    environmentName: 'Userscript',
    markerAttribute: 'data-taiga-clean-view-script',
    loadedAtProperty: '__taigaCleanViewLoadedAt',
    storage: createLocalStorageAdapter(STORAGE_KEY, DEBUG_KEY),
  });

  app.start();
})();
