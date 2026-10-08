document.addEventListener("DOMContentLoaded", function() {
  // Side navigation drawer on small screens (Vanilla side navigation pattern).
  var drawer = document.getElementById('drawer');
  var drawerToggles = document.querySelectorAll('.js-drawer-toggle[aria-controls="drawer"]');

  if (drawer && drawerToggles.length) {
    var drawerPanel = drawer.querySelector('.p-side-navigation__drawer');
    var opener = document.querySelector('button.has-icon.js-drawer-toggle[aria-controls="drawer"]');
    var desktop = window.matchMedia('(min-width: 1036px)');
    var reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');

    function focusableItems() {
      return Array.from(drawerPanel.querySelectorAll('a[href], button:not([disabled]), input:not([disabled]), [tabindex]:not([tabindex="-1"])'))
        .filter(function(item) { return item.getClientRects().length > 0; });
    }

    function toggleDrawer(show) {
      if (!show && drawerPanel.contains(document.activeElement) && opener) {
        opener.focus();
      }
      drawer.classList.toggle('is-drawer-expanded', show);
      drawer.classList.toggle('is-drawer-collapsed', !show);
      drawerToggles.forEach(function(toggle) {
        toggle.setAttribute('aria-expanded', String(show));
      });
      if (!show && reducedMotion.matches) {
        drawer.classList.add('is-drawer-hidden');
      }
    }

    // Keep the closed drawer out of reach of the keyboard and screen readers.
    drawer.classList.add('is-drawer-hidden');
    drawerPanel.addEventListener('animationend', function() {
      if (!drawer.classList.contains('is-drawer-expanded')) {
        drawer.classList.add('is-drawer-hidden');
      }
    });

    drawerToggles.forEach(function(toggle) {
      toggle.addEventListener('click', function() {
        var show = !drawer.classList.contains('is-drawer-expanded');
        drawer.classList.remove('is-drawer-hidden');
        toggleDrawer(show);
        if (show) {
          var items = focusableItems();
          if (items.length) items[0].focus();
        }
      });
    });

    document.addEventListener('keydown', function(e) {
      if (e.key === 'Escape' && drawer.classList.contains('is-drawer-expanded')) {
        toggleDrawer(false);
      } else if (e.key === 'Tab' && drawer.classList.contains('is-drawer-expanded')) {
        var items = focusableItems();
        if (!items.length) return;
        if (e.shiftKey && (document.activeElement === items[0] || !drawerPanel.contains(document.activeElement))) {
          e.preventDefault();
          items[items.length - 1].focus();
        } else if (!e.shiftKey && (document.activeElement === items[items.length - 1] || !drawerPanel.contains(document.activeElement))) {
          e.preventDefault();
          items[0].focus();
        }
      }
    });

    desktop.addEventListener('change', function(e) {
      if (e.matches && drawer.classList.contains('is-drawer-expanded')) {
        toggleDrawer(false);
        drawer.classList.add('is-drawer-hidden');
      }
    });
  }

  document.querySelectorAll('.nav-item').forEach(function(navItem) {
    var label = navItem.querySelector('label');
    var checkbox = null;
    if (label && label.htmlFor) {
      checkbox = navItem.querySelector('#' + label.htmlFor);
    } else {
      checkbox = navItem.querySelector('.toctree-checkbox');
    }
    var ul = navItem.nextElementSibling;
    var li = navItem.closest('li');

    function update() {
      if (ul && checkbox) {
        ul.style.display = checkbox.checked ? 'block' : 'none';
        ul.querySelectorAll(':scope > li').forEach(function(childLi) {
          if (checkbox.checked) {
            childLi.classList.remove('hidden');
          } else {
            childLi.classList.add('hidden');
          }
        });
      }
    }

    if (!checkbox) return;

    update();
    checkbox.addEventListener('change', update);

    label.addEventListener('click', function(e) {
      checkbox.checked = !checkbox.checked;
      update();
      e.preventDefault();
      e.stopPropagation();
    });
  });
});