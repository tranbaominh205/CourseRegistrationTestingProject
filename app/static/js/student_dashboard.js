// student_dashboard.js
// Ensure that when the user navigates back to this page (via browser Back button)
// the page is reloaded so the server can enforce authentication (login_required).
// This prevents the browser's bfcache/back-forward cache from showing a stale,
// authenticated view after the user logged out.

(function () {
  'use strict';

  function shouldReloadOnBack(event) {
    try {
      // If the page was restored from the bfcache, event.persisted is true
      if (event && event.persisted) return true;

      // Check Navigation Timing Level 2
      if (window.performance && typeof window.performance.getEntriesByType === 'function') {
        var nav = window.performance.getEntriesByType('navigation');
        if (nav && nav.length) {
          return nav[0].type === 'back_forward';
        }
      }

      // Fallback to deprecated API for older browsers
      if (window.performance && window.performance.navigation) {
        return window.performance.navigation.type === 2; // TYPE_BACK_FORWARD
      }
    } catch (e) {
      // Ignore errors and do not force reload
      return false;
    }

    return false;
  }

  // pageshow fires when the page is shown, including when restored from bfcache.
  // Instead of forcing a full reload, call the small status endpoint to verify
  // the session is still authenticated. If not, redirect to home/login.
  window.addEventListener('pageshow', function (event) {
    if (shouldReloadOnBack(event)) {
      fetch('/api/auth/status', { cache: 'no-store', credentials: 'same-origin' })
        .then(function (res) { return res.json(); })
        .then(function (data) {
          if (!data || !data.authenticated) {
            // Not authenticated anymore -> go to public index
            window.location.href = '/';
          }
        })
        .catch(function () {
          // On error, be conservative and redirect to index
          window.location.href = '/';
        });
    }
  }, false);

  // Also check on visibilitychange; if the page becomes visible again (user returned)
  // verify authentication status.
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
        // ignore
      }
    }
  });

})();


// No additional UI handling needed for logout (we use a POST form). JS only
// enforces re-checking authentication on back/restore.
