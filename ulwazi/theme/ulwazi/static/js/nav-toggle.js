document.addEventListener("DOMContentLoaded", function() {
  // Side navigation drawer on small screens (Vanilla side navigation pattern).
  var drawer = document.getElementById('drawer');
  var drawerToggles = document.querySelectorAll('.js-drawer-toggle[aria-controls="drawer"]');

  if (drawer && drawerToggles.length) {
    var drawerPanel = drawer.querySelector('.p-side-navigation__drawer');

    function toggleDrawer(show) {
      drawer.classList.toggle('is-drawer-expanded', show);
      drawer.classList.toggle('is-drawer-collapsed', !show);
      drawerToggles.forEach(function(toggle) {
        toggle.setAttribute('aria-expanded', String(show));
      });
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
        drawer.classList.remove('is-drawer-hidden');
        toggleDrawer(!drawer.classList.contains('is-drawer-expanded'));
      });
    });

    document.addEventListener('keydown', function(e) {
      if (e.key === 'Escape' && drawer.classList.contains('is-drawer-expanded')) {
        toggleDrawer(false);
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