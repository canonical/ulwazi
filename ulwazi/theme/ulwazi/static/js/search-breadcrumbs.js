/**
 * Adds breadcrumb navigation to Sphinx search results
 * This extends the default searchtools.js functionality
 */

(function() {
  'use strict';

  /**
   * Generate breadcrumb HTML from navigation path
   * @param {string} docName - The document name (e.g., "content/myst-cheat-sheet")
   * @param {string} title - The page title
   * @returns {HTMLElement|null} - The breadcrumb element or null
   */
  function createBreadcrumb(docName, title) {
    const breadcrumbNav = document.createElement('nav');
    breadcrumbNav.className = 'search-result-breadcrumb';
    breadcrumbNav.setAttribute('aria-label', 'Result location');

    const breadcrumbList = document.createElement('ol');
    breadcrumbList.className = 'search-breadcrumb-list';

    // Always add home link first
    const homeLi = document.createElement('li');
    homeLi.className = 'search-breadcrumb-item';
    const homeLink = document.createElement('a');
    homeLink.href = '../index.html';
    homeLink.textContent = 'Home';
    homeLi.appendChild(homeLink);
    breadcrumbList.appendChild(homeLi);

    // Check if we have a breadcrumb map from the navigation structure
    if (window.SEARCH_BREADCRUMB_MAP && window.SEARCH_BREADCRUMB_MAP[docName]) {
      const navPath = window.SEARCH_BREADCRUMB_MAP[docName];
      
      // Add each item from the navigation path
      navPath.forEach((item, index) => {
        const li = document.createElement('li');
        li.className = 'search-breadcrumb-item';
        
        const link = document.createElement('a');
        link.href = '../' + item.link;
        link.textContent = item.title;
        li.appendChild(link);
        
        breadcrumbList.appendChild(li);
      });
    } else {
      // Fallback: use file system path if navigation map not available
      const parts = docName.split('/');
      if (parts.length > 1) {
        // Add parent sections from file path
        for (let i = 0; i < parts.length - 1; i++) {
          const part = parts[i];
          const li = document.createElement('li');
          li.className = 'search-breadcrumb-item';
          
          const link = document.createElement('a');
          const partPath = parts.slice(0, i + 1).join('/');
          link.href = '../' + partPath + '/index.html';
          link.textContent = part.charAt(0).toUpperCase() + part.slice(1).replace(/-/g, ' ');
          li.appendChild(link);
          
          breadcrumbList.appendChild(li);
        }
      }
    }

    breadcrumbNav.appendChild(breadcrumbList);
    return breadcrumbNav;
  }

  /**
   * Override the _displayItem function to include breadcrumbs
   */
  function initSearchBreadcrumbs() {
    // Wait for _displayItem to be defined
    if (typeof window._displayItem === 'undefined') {
      // Check if Search.performSearch exists instead
      if (typeof Search !== 'undefined' && typeof Search.performSearch !== 'undefined') {
        // Sphinx search is loaded, but _displayItem isn't exposed globally
        // We need to override it differently
        overrideSearchDisplay();
      } else {
        setTimeout(initSearchBreadcrumbs, 100);
      }
      return;
    }

    // Store the original function
    const original_displayItem = window._displayItem;

    window._displayItem = function(item, searchTerms, highlightTerms) {
      const docBuilder = DOCUMENTATION_OPTIONS.BUILDER;
      const docFileSuffix = DOCUMENTATION_OPTIONS.FILE_SUFFIX;
      const docLinkSuffix = DOCUMENTATION_OPTIONS.LINK_SUFFIX;
      const showSearchSummary = DOCUMENTATION_OPTIONS.SHOW_SEARCH_SUMMARY;
      const contentRoot = document.documentElement.dataset.content_root;

      const [docName, title, anchor, descr, score, _filename] = item;

      let listItem = document.createElement("li");
      let requestUrl;
      let linkUrl;
      
      if (docBuilder === "dirhtml") {
        let dirname = docName + "/";
        if (dirname.match(/\/index\/$/))
          dirname = dirname.substring(0, dirname.length - 6);
        else if (dirname === "index/") dirname = "";
        requestUrl = contentRoot + dirname;
        linkUrl = requestUrl;
      } else {
        requestUrl = contentRoot + docName + docFileSuffix;
        linkUrl = docName + docLinkSuffix;
      }
      
      // Create breadcrumb (above the title)
      const breadcrumb = createBreadcrumb(docName, title);
      if (breadcrumb) {
        listItem.appendChild(breadcrumb);
      }
      
      // Create the main link
      let linkEl = listItem.appendChild(document.createElement("a"));
      linkEl.href = linkUrl + anchor;
      linkEl.dataset.score = score;
      linkEl.innerHTML = title;
      if (anchor) {
        // If there's an anchor, add the heading reference
        const headingText = anchor.replace('#', '');
        if (headingText) {
          const headingSpan = document.createElement("span");
          headingSpan.className = "search-result-heading";
          headingSpan.textContent = " › " + decodeURIComponent(headingText).replace(/-/g, ' ');
          linkEl.appendChild(headingSpan);
        }
      }
      
      // Add description if present
      if (descr) {
        listItem.appendChild(document.createElement("span")).innerHTML =
          " (" + descr + ")";
        if (typeof SPHINX_HIGHLIGHT_ENABLED !== 'undefined' && SPHINX_HIGHLIGHT_ENABLED)
          highlightTerms.forEach((term) => _highlightText(listItem, term, "highlighted"));
      }
      else if (showSearchSummary)
        fetch(requestUrl)
          .then((responseData) => responseData.text())
          .then((data) => {
            if (data)
              listItem.appendChild(
                Search.makeSearchSummary(data, searchTerms, anchor)
              );
            if (typeof SPHINX_HIGHLIGHT_ENABLED !== 'undefined' && SPHINX_HIGHLIGHT_ENABLED)
              highlightTerms.forEach((term) => _highlightText(listItem, term, "highlighted"));
          });
      
      Search.output.appendChild(listItem);
    };
  }

  /**
   * Alternative method to override search display by monkeypatching Search object
   */
  function overrideSearchDisplay() {
    if (typeof Search === 'undefined' || typeof Search.performSearch === 'undefined') {
      setTimeout(overrideSearchDisplay, 100);
      return;
    }

    // Store original performSearch
    const originalPerformSearch = Search.performSearch;
    
    // Override performSearch to inject our custom display logic
    Search.performSearch = function(query) {
      // Call original
      originalPerformSearch.call(this, query);
      
      // After search completes, modify the results
      // Use multiple checks with increasing delays to catch all results
      const addBreadcrumbsToResults = () => {
        const results = document.querySelectorAll('#search-results ul.search > li');
        results.forEach(listItem => {
          // Check if breadcrumb already added
          if (listItem.querySelector('.search-result-breadcrumb')) {
            return;
          }
          
          const link = listItem.querySelector('a');
          if (!link) return;
          
          const href = link.getAttribute('href');
          if (!href) return;
          
          // Extract docname from href
          let docName = href.split('#')[0];
          docName = docName.replace(/^\.\.\//, '').replace(/\/$/, '');
          
          const title = link.textContent.trim();
          
          // Create and insert breadcrumb
          const breadcrumb = createBreadcrumb(docName, title);
          if (breadcrumb) {
            listItem.insertBefore(breadcrumb, link);
          }
        });
      };
      
      // Try multiple times to catch all results as they're rendered
      setTimeout(addBreadcrumbsToResults, 10);
      setTimeout(addBreadcrumbsToResults, 100);
      setTimeout(addBreadcrumbsToResults, 300);
    };
  }

  // Initialize when DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initSearchBreadcrumbs);
  } else {
    initSearchBreadcrumbs();
  }
})();
