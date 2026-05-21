// class_list.js
// Lightweight client-side helpers for the class list page.

(function () {
  'use strict';

  var STORAGE_KEY = 'student_class_list_scroll_state';

  function getTableContainers() {
    return Array.prototype.slice.call(document.querySelectorAll('.table-container'));
  }

  function saveScrollState() {
    try {
      var containers = getTableContainers();
      var state = {
        windowX: window.scrollX || window.pageXOffset || 0,
        windowY: window.scrollY || window.pageYOffset || 0,
        containers: containers.map(function (container, index) {
          return {
            index: index,
            scrollTop: container.scrollTop || 0,
            scrollLeft: container.scrollLeft || 0
          };
        })
      };

      sessionStorage.setItem(STORAGE_KEY, JSON.stringify(state));
    } catch (error) {
      // Ignore storage errors (private mode, disabled storage, etc.)
    }
  }

  function restoreScrollState() {
    try {
      var raw = sessionStorage.getItem(STORAGE_KEY);
      if (!raw) {
        return;
      }

      var state = JSON.parse(raw);
      var containers = getTableContainers();

      if (state && typeof state.windowY === 'number') {
        window.scrollTo(state.windowX || 0, state.windowY || 0);
      }

      if (state && Array.isArray(state.containers)) {
        state.containers.forEach(function (saved) {
          var container = containers[saved.index];
          if (!container) {
            return;
          }

          container.scrollTop = saved.scrollTop || 0;
          container.scrollLeft = saved.scrollLeft || 0;
        });
      }

      sessionStorage.removeItem(STORAGE_KEY);
    } catch (error) {
      // Ignore malformed storage data and fall back to normal page behavior.
    }
  }

  function isStudentActionForm(form) {
    if (!form || typeof form.matches !== 'function') {
      return false;
    }

    return form.matches('form[action*="/student/classes/"]') ||
      form.matches('form[action*="/student/enrollments/"]') ||
      form.id === 'confirm-form';
  }

  document.addEventListener('submit', function (event) {
    if (isStudentActionForm(event.target)) {
      saveScrollState();
    }
  }, true);

  window.addEventListener('beforeunload', saveScrollState);

  document.addEventListener('DOMContentLoaded', function () {
    if ('scrollRestoration' in history) {
      history.scrollRestoration = 'manual';
    }

    restoreScrollState();
  });

  window.addEventListener('pageshow', function (event) {
    if (event.persisted) {
      restoreScrollState();
    }
  });
})();

