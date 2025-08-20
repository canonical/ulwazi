document.addEventListener('DOMContentLoaded', () => {
  const nav = document.getElementById('navigation');
  if (!nav) return;

  const menuButton = nav.querySelector('.js-menu-button'); // main menu toggle
  const dropdownButtons = nav.querySelectorAll('.js-dropdown-button'); // all dropdown links

  // Toggle main menu
  if (menuButton) {
    menuButton.addEventListener('click', e => {
      e.stopPropagation();
      const isOpen = nav.classList.toggle('is-drawer-open');
      menuButton.setAttribute('aria-expanded', isOpen);
    });
  }

  // Toggle dropdowns
  dropdownButtons.forEach(btn => {
    btn.addEventListener('click', e => {
      e.preventDefault();
      e.stopPropagation();

      const dropdownId = btn.getAttribute('aria-controls');
      const dropdown = document.getElementById(dropdownId);
      if (!dropdown) return;

      // Toggle aria-hidden
      const isHidden = dropdown.getAttribute('aria-hidden') === 'true';
      dropdown.setAttribute('aria-hidden', !isHidden ? 'true' : 'false');

      // Toggle collapsed class
      dropdown.classList.toggle('is-collapsed', isHidden ? false : true);
    });
  });

  // Click outside closes menu and all dropdowns
  document.addEventListener('click', e => {
    if (!nav.contains(e.target)) {
      nav.classList.remove('is-drawer-open');
      if (menuButton) menuButton.setAttribute('aria-expanded', 'false');

      const allDropdowns = nav.querySelectorAll('.p-navigation__dropdown');
      allDropdowns.forEach(d => {
        d.setAttribute('aria-hidden', 'true');
        d.classList.add('is-collapsed');
      });
    }
  });

  // Escape closes everything
  document.addEventListener('keydown', e => {
    if (e.key === 'Escape') {
      nav.classList.remove('is-drawer-open');
      if (menuButton) menuButton.setAttribute('aria-expanded', 'false');

      const allDropdowns = nav.querySelectorAll('.p-navigation__dropdown');
      allDropdowns.forEach(d => {
        d.setAttribute('aria-hidden', 'true');
        d.classList.add('is-collapsed');
      });
    }
  });
});
