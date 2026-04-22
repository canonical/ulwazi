document.addEventListener("DOMContentLoaded", () => {
  const STORAGE_KEY = "ulwazi-theme";
  const body = document.body;
  const toggleButton = document.querySelector(".theme-toggle");

  const applyTheme = (themeClass) => { //themeClass can be "is-light", "is-dark"
    body.classList.remove("is-light", "is-dark");
    if (themeClass) {
      body.classList.add(themeClass);
    }
    if (toggleButton) {
      toggleButton.setAttribute("aria-pressed", themeClass === "is-dark" ? "true" : "false"); //For accessibility
    }
  };

  const savedTheme = localStorage.getItem(STORAGE_KEY);
  if (savedTheme === "is-light" || savedTheme === "is-dark") {
    applyTheme(savedTheme);
  } else if (window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches) {
    applyTheme("is-dark");
  } else {
    applyTheme("is-light");
  }

  if (!toggleButton) {
    return;
  }

  toggleButton.addEventListener("click", () => {
    const isDark = body.classList.contains("is-dark");
    const nextTheme = isDark ? "is-light" : "is-dark";
    applyTheme(nextTheme);
    localStorage.setItem(STORAGE_KEY, nextTheme);
  });
});