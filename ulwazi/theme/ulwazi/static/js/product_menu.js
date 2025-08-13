/**
 * Self-contained script to manage a multi-level, sliding top navigation menu,
 * based on the class structure from Canonical's p-navigation component.
 *
 * This script handles three main interactions:
 * 1. Toggling the main menu on smaller screens.
 * 2. Opening nested sub-menu dropdowns.
 * 3. Closing sub-menus with a "back" button.
 */
document.addEventListener('DOMContentLoaded', function() {
  const nav = document.getElementById('navigation');
  if (!nav) {
    console.error('Navigation script: Could not find navigation element with id="navigation".');
    return;
  }

  // 1. Main menu toggle for mobile/small screens
  const menuButton = nav.querySelector('.js-menu-button');
  const mainNavContainer = nav.querySelector('.js-show-nav');

  if (menuButton && mainNavContainer) {
    menuButton.addEventListener('click', function() {
      // Toggles a class on the main nav container to show/hide it.
      // The CSS should handle the transition (e.g., display: block/none).
      mainNavContainer.classList.toggle('is-visible');
      const isVisible = mainNavContainer.classList.contains('is-visible');
      this.setAttribute('aria-expanded', isVisible);
    });
  } else {
    console.warn('Navigation script: Main menu button or container not found.');
  }

  // 2. Handlers for opening sub-menus
  const dropdownButtons = nav.querySelectorAll('.js-dropdown-button');
  dropdownButtons.forEach(button => {
    button.addEventListener('click', function(event) {
      event.preventDefault();
      const targetId = this.getAttribute('aria-controls');
      const targetDropdown = document.getElementById(targetId);

      if (targetDropdown) {
        // Show the target dropdown
        targetDropdown.classList.remove('is-collapsed');
        targetDropdown.setAttribute('aria-hidden', 'false');

        // Add a class to the main navigation to indicate a dropdown is open.
        // This is used to apply the sliding animation effect.
        nav.classList.add('is-drawer-open');
      } else {
        console.warn(`Navigation script: Could not find dropdown with id "${targetId}".`);
      }
    });
  });

  // 3. Handlers for the "back" buttons to close sub-menus
  const backButtons = nav.querySelectorAll('.js-back-button');
  backButtons.forEach(button => {
    button.addEventListener('click', function(event) {
      event.preventDefault();
      // Find the closest parent dropdown that this back button is inside of.
      const parentDropdown = this.closest('.p-navigation__dropdown, .p-navigation__dropdown-content--sliding');

      if (parentDropdown) {
        // Hide the current dropdown
        parentDropdown.classList.add('is-collapsed');
        parentDropdown.setAttribute('aria-hidden', 'true');
        
        // Check if any other drawers are still open. If not, remove the class.
        // This logic assumes nested drawers. A simpler approach is to check if the closed drawer was the last one.
        const stillOpenDrawers = nav.querySelectorAll('.p-navigation__dropdown:not(.is-collapsed), .p-navigation__dropdown-content--sliding:not(.is-collapsed)');
        if (stillOpenDrawers.length === 0) {
           nav.classList.remove('is-drawer-open');
        }

      } else {
        console.warn('Navigation script: Could not find parent dropdown for back button.', this);
      }
    });
  });
});
