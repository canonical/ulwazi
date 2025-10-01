document.addEventListener("DOMContentLoaded", function() {
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
    var chevronUp = label ? label.querySelector('.p-icon--chevron-up') : null;

    function update() {
      if (ul && checkbox) ul.style.display = checkbox.checked ? 'block' : 'none';
    }

    if (!checkbox)  {
        // No checkbox found for nav-item, skipping toggle setup.
        return;
    }

    update();
    checkbox.addEventListener('change', update);

    // Only attach the click handler to the chevron-up icon
    if (chevronUp) {
      chevronUp.addEventListener('click', function(e) {
        checkbox.checked = !checkbox.checked;
        update();
        e.preventDefault();
        e.stopPropagation();
      });
    }
  });
});