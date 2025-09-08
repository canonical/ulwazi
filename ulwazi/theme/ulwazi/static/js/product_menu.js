const initNavigationSliding = () => {
  const ANIMATION_SNAP_DURATION = 100;
  const productNavigation = document.querySelector('.product-menu');
  const secondaryNavigation = document.querySelector('.is-secondary');
  const toggles = document.querySelectorAll('.p-navigation__nav .p-navigation__link[aria-controls]:not(.js-back-button)');
  const searchButtons = document.querySelectorAll('.js-search-button');
  const menuButton = document.querySelector('.js-menu-button');
  const dropdownNavLists = document.querySelectorAll('.js-dropdown-nav-list');
  const topNavList = [...dropdownNavLists].filter((list) => !list.parentNode.closest('.js-dropdown-nav-list'))[0];

  const hasSearch = searchButtons.length > 0;

  const closeAllDropdowns = () => {
    if (hasSearch) {
      closeSearch();
    }
    resetToggles();
    if (productNavigation) {
      productNavigation.classList.remove('has-menu-open');
      productNavigation.querySelectorAll('.p-navigation__item--dropdown-toggle.is-active, .js-dropdown-list.is-active')
        .forEach(el => el.classList.remove('is-active'));
    }
    if (secondaryNavigation) {
      secondaryNavigation.classList.remove('has-menu-open');
    }
    if (menuButton) {
      menuButton.innerHTML = 'Menu';
    }
  };

  const keyPressHandler = (e) => {
    if (e.key === 'Escape') {
      closeAllDropdowns();
    }
  };

  const closeSearch = () => {
    searchButtons.forEach((searchButton) => {
      searchButton.removeAttribute('aria-pressed');
    });

    if (productNavigation) {
      productNavigation.classList.remove('has-search-open');
    }
    document.removeEventListener('keyup', keyPressHandler);
  };

  if (menuButton && productNavigation) {
    menuButton.addEventListener('click', function (e) {
      e.preventDefault();
      closeSearch();
      if (productNavigation.classList.contains('has-menu-open')) {
        // closing product menu
        productNavigation.classList.remove('has-menu-open');
        menuButton.innerHTML = 'Menu';
      } else {
        // opening product menu
        productNavigation.classList.add('has-menu-open');
        menuButton.innerHTML = 'Close menu';
        setFocusable(topNavList);
      }
    });
  }

  const secondaryNavToggle = document.querySelector('.js-secondary-menu-toggle-button');
  if (secondaryNavToggle && secondaryNavigation) {
    secondaryNavToggle.addEventListener('click', (event) => {
      event.preventDefault();
      closeSearch();
      if (secondaryNavigation.classList.contains('has-menu-open')) {
        secondaryNavigation.classList.remove('has-menu-open');
      } else {
        secondaryNavigation.classList.add('has-menu-open');
      }
    });
  }

  const resetToggles = (exception) => {
    toggles.forEach(function (toggle) {
      const target = document.getElementById(toggle.getAttribute('aria-controls'));
      if (!target || target === exception) {
        return;
      }
      collapseDropdown(toggle, target);
    });
  };

  const setActiveDropdown = (dropdownToggleButton, isActive = true) => {
    const dropdownToggleEl = dropdownToggleButton.closest('.js-navigation-dropdown-toggle');
    if (dropdownToggleEl) {
      dropdownToggleEl.classList.toggle('is-active', isActive);

      const parentLevelDropdown = dropdownToggleEl.closest('.js-navigation-sliding-panel');
      if (parentLevelDropdown) {
        parentLevelDropdown.classList.toggle('is-active', isActive);
      }
    }
  };

  const collapseDropdown = (dropdownToggleButton, targetDropdown, animated = false) => {
    const closeHandler = () => {
      targetDropdown.setAttribute('aria-hidden', 'true');
      setActiveDropdown(dropdownToggleButton, false);
    };

    targetDropdown.classList.add('is-collapsed');
    if (animated) {
      setTimeout(closeHandler, ANIMATION_SNAP_DURATION);
    } else {
      closeHandler();
    }
  };

  const expandDropdown = (dropdownToggleButton, targetDropdown, animated = false) => {
    setActiveDropdown(dropdownToggleButton);
    targetDropdown.setAttribute('aria-hidden', 'false');

    if (animated) {
      requestAnimationFrame(() => {
        targetDropdown.classList.remove('is-collapsed');
      });
    } else {
      targetDropdown.classList.remove('is-collapsed');
    }

    setFocusable(targetDropdown);
  };

  // when clicking outside navigation, close all dropdowns
  document.addEventListener('click', function (event) {
    const target = event.target;
    if (target.closest) {
      if (!target.closest('.p-navigation, .p-navigation--sliding, .p-navigation--reduced')) {
        closeAllDropdowns();
      }
    }
  });

  const setListFocusable = (list) => {
    if (list) {
      for (const item of list.children) {
        item.children[0].setAttribute('tabindex', '0');
      }
    }
  };

  const setFocusable = (target) => {
    dropdownNavLists.forEach(function (list) {
      if (list != topNavList) {
        const elements = list.querySelectorAll('ul > li > a, ul > li > button');
        elements.forEach(function (element) {
          element.setAttribute('tabindex', '-1');
        });
      }
    });

    const isList = target.classList.contains('js-dropdown-nav-list');
    if (!isList) {
      target.querySelectorAll('.js-dropdown-nav-list').forEach(function (element) {
        setListFocusable(element);
      });
    } else {
      setListFocusable(target);
    }
  };

  toggles.forEach(function (toggle) {
    toggle.addEventListener('click', function (e) {
      e.preventDefault();
      closeSearch();
      const target = document.getElementById(toggle.getAttribute('aria-controls'));
      if (target) {
        const isNested = !!target.parentNode.closest('.p-navigation__dropdown');
        if (!isNested) {
          resetToggles(target);
        }

        const parentNav = toggle.closest('.product-menu, .is-secondary');
        if (target.getAttribute('aria-hidden') === 'true') {
          expandDropdown(toggle, target, !(parentNav && parentNav.classList.contains('has-menu-open')));
          if (parentNav) {
            parentNav.classList.add('has-menu-open');
          }
        } else {
          collapseDropdown(toggle, target, true);
          if (!isNested && parentNav) {
            parentNav.classList.remove('has-menu-open');
          }
        }
      }
    });
  });

  const goBackOneLevel = (e, backButton) => {
    e.preventDefault();
    const target = backButton.closest('.p-navigation__dropdown');
    target.setAttribute('aria-hidden', 'true');
    setActiveDropdown(backButton, false);
    setFocusable(target.parentNode.parentNode);
  };

  // Handle subsection tabs inside product navigation menu
  if (productNavigation) {
    const tabs = productNavigation.querySelectorAll('.js-navigation-tab');
    if (tabs.length > 0) {
      tabs.forEach((tab) => {
        tab.addEventListener('click', function (e) {
          e.preventDefault();

          // Reset all tabs in product menu
          tabs.forEach((t) => {
            t.classList.remove('is-active');
            t.setAttribute('aria-selected', 'false');
            const contentId = t.getAttribute('aria-controls');
            if (contentId) {
              const content = document.getElementById(contentId);
              if (content) {
                content.setAttribute('hidden', '');
              }
            }
          });

          // Activate clicked tab
          this.classList.add('is-active');
          this.setAttribute('aria-selected', 'true');
          const activeContentId = this.getAttribute('aria-controls');
          if (activeContentId) {
            const activeContent = document.getElementById(activeContentId);
            if (activeContent) {
              activeContent.removeAttribute('hidden');
            }
          }
        });
      });
    }
  }

  dropdownNavLists.forEach(function (dropdown) {
    dropdown.children[1].addEventListener('keydown', function (e) {
      if (e.shiftKey && e.key === 'Tab' && window.getComputedStyle(dropdown.children[0], null).display === 'none') {
        goBackOneLevel(e, dropdown.children[1].children[0]);
        dropdown.parentNode.children[0].focus({
          preventScroll: true,
        });
      }
    });
  });

  document.querySelectorAll('.js-back-button').forEach(function (backButton) {
    backButton.addEventListener('click', function (e) {
      goBackOneLevel(e, backButton);
    });
  });

  if (hasSearch && productNavigation) {
    const toggleSearch = (e) => {
      e.preventDefault();

      if (productNavigation.classList.contains('has-search-open')) {
        closeAllDropdowns();
      } else {
        closeAllDropdowns();
        openSearch(e);
      }
    };

    searchButtons.forEach((searchButton) => {
      searchButton.addEventListener('click', toggleSearch);
    });

    const overlay = document.querySelector('.p-navigation__search-overlay');
    if (overlay) {
      overlay.addEventListener('click', closeAllDropdowns);
    }

    const openSearch = (e) => {
      e.preventDefault();

      let searchInput = productNavigation.querySelector('.p-search-box__input');
      if (!searchInput && secondaryNavigation) {
        searchInput = secondaryNavigation.querySelector('.p-search-box__input');
      }
      const buttons = document.querySelectorAll('.js-search-button');

      buttons.forEach((searchButton) => {
        searchButton.setAttribute('aria-pressed', true);
      });

      productNavigation.classList.add('has-search-open');
      if (searchInput) {
        searchInput.focus();
      }
      document.addEventListener('keyup', keyPressHandler);
    };
  }

  // throttle util (for window resize event)
  var throttle = function (fn, delay) {
    var timer = null;
    return function () {
      var context = this,
        args = arguments;
      clearTimeout(timer);
      timer = setTimeout(function () {
        fn.apply(context, args);
      }, delay);
    };
  };

  // hide side navigation drawer when screen is resized horizontally
  let previousWidth = window.innerWidth;
  window.addEventListener(
    'resize',
    throttle(function () {
      const currentWidth = window.innerWidth;
      if (currentWidth !== previousWidth) {
        closeAllDropdowns();
        previousWidth = currentWidth;
      }
    }, 10),
  );
};

const highlightProductMenuSelectedItems = () => {
  const productMenu = document.querySelector('.product-menu');
  if (!productMenu) return;

  // Find all dropdown toggle buttons inside the product menu
  const toggles = productMenu.querySelectorAll('.js-dropdown-button');

  toggles.forEach((toggle) => {
    toggle.addEventListener('click', (e) => {
      e.preventDefault();

      const parentLi = toggle.closest('.p-navigation__item--dropdown-toggle');
      const targetUl = productMenu.querySelector('#' + toggle.getAttribute('aria-controls'));

      if (!parentLi || !targetUl) return;

      const isOpen = parentLi.classList.contains('is-active');

      // Close all dropdowns first
      toggles.forEach((t) => {
        const li = t.closest('.p-navigation__item--dropdown-toggle');
        const ul = productMenu.querySelector('#' + t.getAttribute('aria-controls'));
        if (li) li.classList.remove('is-active');
        // if (ul) ul.classList.remove('is-active');
      });

      // If it was closed, open it
      if (!isOpen) {
        parentLi.classList.add('is-active');
        // targetUl.classList.add('is-active');
      }
    });
  });
};

highlightProductMenuSelectedItems();

initNavigationSliding();
