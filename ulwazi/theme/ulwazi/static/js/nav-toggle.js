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