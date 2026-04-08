function initSearchResetButtons(selector) {
  var resetButtons = [].slice.call(document.querySelectorAll(selector));

  resetButtons.forEach(function(button) {
    button.addEventListener('click', function() {
      var input = button.parentNode.querySelector('input');

      input.focus();
    });
  });
}

/**
 * Customize Sphinx search results after they are rendered.
 *
 * Sphinx's searchtools.js dynamically creates an <h2> heading and a status
 * <p> inside #search-results. We use a MutationObserver to wait for Sphinx
 * to finish (the heading changes from "Searching" to "Search Results"),
 * then patch the DOM:
 *  - Promote the heading from <h2> to <h1> with Vanilla Framework class.
 *  - Replace Sphinx's status text with "Showing N results for "query"".
 *
 * If Sphinx changes its markup and any expected element is missing, the
 * observer silently disconnects after a timeout to avoid running forever.
 */
function patchSearchResults() {
  var container = document.getElementById('search-results');
  if (!container) return;

  var TIMEOUT_MS = 30000;
  var patched = false;

  var observer = new MutationObserver(function() {
    var h2 = container.querySelector('h2');
    // Wait until Sphinx replaces "Searching" with final heading text
    if (!h2 || h2.textContent.trim() === 'Searching') return;

    // Promote heading to h1 with Vanilla Framework styling, sentence case
    var h1 = document.createElement('h1');
    h1.className = 'p-heading--1';
    h1.textContent = 'Search results';
    h2.replaceWith(h1);

    // Replace status with "Showing N results for "query""
    var status = container.querySelector('p.search-summary');
    if (status) {
      var query = new URLSearchParams(window.location.search).get('q');
      var match = status.textContent.match(/found (\d+)/);
      var count = match ? match[1] : '0';
      status.textContent = 'Showing ' + count + ' result' +
        (count === '1' ? '' : 's') + ' for \u201c' + (query || '') + '\u201d';
    }

    patched = true;
    observer.disconnect();
  });

  observer.observe(container, { childList: true, subtree: true, characterData: true });

  // Safety: disconnect if Sphinx never produces expected output
  setTimeout(function() {
    if (!patched) observer.disconnect();
  }, TIMEOUT_MS);
}

document.addEventListener('DOMContentLoaded', function() {
  initSearchResetButtons('.p-search-box__reset');
  patchSearchResults();
});