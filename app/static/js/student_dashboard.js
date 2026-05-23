
(function () {
  'use strict';

  function shouldReloadOnBack(event) {
    try {
      if (event && event.persisted) return true;
      if (window.performance && typeof window.performance.getEntriesByType === 'function') {
        var nav = window.performance.getEntriesByType('navigation');
        if (nav && nav.length) {
          return nav[0].type === 'back_forward';
        }
      }
      if (window.performance && window.performance.navigation) {
        return window.performance.navigation.type === 2;
      }
    } catch (e) {
      return false;
    }

    return false;
  }
  window.addEventListener('pageshow', function (event) {
    if (shouldReloadOnBack(event)) {
      fetch('/api/auth/status', { cache: 'no-store', credentials: 'same-origin' })
        .then(function (res) { return res.json(); })
        .then(function (data) {
          if (!data || !data.authenticated) {
            window.location.href = '/';
          }
        })
        .catch(function () {
          window.location.href = '/';
        });
    }
  }, false);
  document.addEventListener('visibilitychange', function () {
    if (document.visibilityState === 'visible') {
      try {
        fetch('/api/auth/status', { cache: 'no-store', credentials: 'same-origin' })
          .then(function (res) { return res.json(); })
          .then(function (data) {
            if (!data || !data.authenticated) {
              window.location.href = '/';
            }
          })
          .catch(function () {
            window.location.href = '/';
          });
      } catch (e) {
      }
    }
  });

})();
