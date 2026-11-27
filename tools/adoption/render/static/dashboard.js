// Progressive enhancement for the adoption dashboard: filtering, sorting,
// expandable details and the colour theme. The page is complete without it.
(function () {
  "use strict";

  var STORAGE_KEY = "ulwazi-theme"; // shared with the Ulwazi theme
  var table = document.getElementById("projects");
  if (!table) {
    return;
  }
  var tbody = table.tBodies[0];
  var rows = Array.prototype.slice.call(tbody.querySelectorAll("tr.adopt-row"));
  var evidence = {};
  tbody.querySelectorAll("tr.adopt-evidence").forEach(function (row) {
    evidence[row.getAttribute("data-for")] = row;
  });

  var controls = {
    q: document.getElementById("filter-q"),
    scope: document.getElementById("filter-scope"),
    stack: document.getElementById("filter-stack"),
    ulwazi: document.getElementById("filter-ulwazi"),
  };
  var resetButton = document.getElementById("filter-reset");
  var counter = document.getElementById("result-count");
  var emptyState = document.getElementById("empty-state");
  var tiles = Array.prototype.slice.call(document.querySelectorAll(".adopt-tile"));
  var segments = Array.prototype.slice.call(document.querySelectorAll(".adopt-seg"));
  var headers = Array.prototype.slice.call(table.querySelectorAll("thead th[data-key]"));

  var TILE_PRESETS = {
    all: { scope: "", stack: "", ulwazi: "", latest: false },
    stack: { scope: "in", stack: "", ulwazi: "", latest: false },
    latest: { scope: "in", stack: "", ulwazi: "", latest: true },
    out: { scope: "out", stack: "", ulwazi: "", latest: false },
  };

  var state = { q: "", scope: "", stack: "", ulwazi: "", latest: false, sort: "name", dir: "asc" };

  // -- state <-> URL ---------------------------------------------------------

  function readUrl() {
    var params = new URLSearchParams(window.location.search);
    ["q", "scope", "stack", "ulwazi", "sort", "dir"].forEach(function (key) {
      if (params.has(key)) {
        state[key] = params.get(key);
      }
    });
    state.latest = params.get("latest") === "1";
  }

  function writeUrl() {
    var params = new URLSearchParams();
    ["q", "scope", "stack", "ulwazi"].forEach(function (key) {
      if (state[key]) {
        params.set(key, state[key]);
      }
    });
    if (state.latest) {
      params.set("latest", "1");
    }
    if (state.sort !== "name" || state.dir !== "asc") {
      params.set("sort", state.sort);
      params.set("dir", state.dir);
    }
    var query = params.toString();
    window.history.replaceState(null, "", query ? "?" + query : window.location.pathname);
  }

  // -- filtering -------------------------------------------------------------

  function matches(row) {
    var data = row.dataset;
    if (state.q && data.search.indexOf(state.q.toLowerCase()) === -1) {
      return false;
    }
    if (state.scope && data.scope !== state.scope) {
      return false;
    }
    if (state.stack && data.stack !== state.stack) {
      return false;
    }
    if (state.ulwazi && data.ulwazi !== state.ulwazi) {
      return false;
    }
    return !state.latest || data.latest === "1";
  }

  function isFiltered() {
    return Boolean(state.q || state.scope || state.stack || state.ulwazi || state.latest);
  }

  function pressedTile() {
    return Object.keys(TILE_PRESETS).filter(function (name) {
      var preset = TILE_PRESETS[name];
      return (
        !state.q &&
        state.scope === preset.scope &&
        state.stack === preset.stack &&
        state.ulwazi === preset.ulwazi &&
        state.latest === preset.latest
      );
    })[0];
  }

  function apply() {
    var shown = 0;
    rows.forEach(function (row) {
      var visible = matches(row);
      row.hidden = !visible;
      var detail = evidence[row.id];
      if (detail && !visible) {
        detail.classList.remove("is-open");
        row.querySelector(".adopt-expand").setAttribute("aria-expanded", "false");
      }
      if (detail) {
        detail.hidden = !visible;
      }
      if (visible) {
        shown += 1;
      }
    });
    counter.textContent =
      shown === rows.length
        ? rows.length + " projects"
        : "Showing " + shown + " of " + rows.length + " projects";
    emptyState.hidden = shown !== 0;
    resetButton.hidden = !isFiltered();

    var active = pressedTile();
    tiles.forEach(function (tile) {
      tile.setAttribute("aria-pressed", String(tile.dataset.preset === active));
    });
    segments.forEach(function (segment) {
      segment.setAttribute("aria-pressed", String(state.stack === segment.dataset.stack));
    });
    controls.q.value = state.q;
    controls.scope.value = state.scope;
    controls.stack.value = state.stack;
    controls.ulwazi.value = state.ulwazi;
    writeUrl();
  }

  // -- sorting ---------------------------------------------------------------

  var SORT_FIELDS = {
    name: { attribute: "name", numeric: false },
    repo: { attribute: "repo", numeric: false },
    stack: { attribute: "stackSort", numeric: false },
    ulwazi: { attribute: "ulwaziSort", numeric: false },
    built: { attribute: "built", numeric: true },
  };

  function sortRows() {
    var field = SORT_FIELDS[state.sort] || SORT_FIELDS.name;
    var factor = state.dir === "desc" ? -1 : 1;
    rows.sort(function (a, b) {
      var left = a.dataset[field.attribute];
      var right = b.dataset[field.attribute];
      // Rows without a value always go last, whatever the direction.
      if (!left && left !== "0" && right) {
        return 1;
      }
      if (!right && right !== "0" && left) {
        return -1;
      }
      if (field.numeric) {
        return (Number(left) - Number(right)) * factor;
      }
      return left < right ? -factor : left > right ? factor : a.dataset.name < b.dataset.name ? -1 : 1;
    });
    rows.forEach(function (row) {
      tbody.appendChild(row);
      if (evidence[row.id]) {
        tbody.appendChild(evidence[row.id]);
      }
    });
    headers.forEach(function (header) {
      var active = header.dataset.key === state.sort;
      if (active) {
        header.setAttribute("aria-sort", state.dir === "desc" ? "descending" : "ascending");
      } else {
        header.removeAttribute("aria-sort");
      }
    });
  }

  // -- events ----------------------------------------------------------------

  function setPreset(name) {
    var preset = TILE_PRESETS[name];
    state.q = "";
    state.scope = preset.scope;
    state.stack = preset.stack;
    state.ulwazi = preset.ulwazi;
    state.latest = preset.latest;
    apply();
  }

  controls.q.addEventListener("input", function () {
    state.q = controls.q.value.trim();
    apply();
  });
  ["scope", "stack", "ulwazi"].forEach(function (key) {
    controls[key].addEventListener("change", function () {
      state[key] = controls[key].value;
      state.latest = false;
      apply();
    });
  });
  resetButton.addEventListener("click", function () {
    setPreset("all");
  });
  tiles.forEach(function (tile) {
    tile.addEventListener("click", function () {
      setPreset(tile.dataset.preset);
    });
  });
  segments.forEach(function (segment) {
    segment.addEventListener("click", function () {
      var same = state.stack === segment.dataset.stack;
      setPreset("all");
      state.scope = "in";
      state.stack = same ? "" : segment.dataset.stack;
      apply();
    });
  });
  headers.forEach(function (header) {
    header.querySelector("button").addEventListener("click", function () {
      var key = header.dataset.key;
      state.dir = state.sort === key && state.dir === "asc" ? "desc" : "asc";
      state.sort = key;
      sortRows();
      apply();
    });
  });
  tbody.addEventListener("click", function (event) {
    var button = event.target.closest(".adopt-expand");
    if (!button) {
      return;
    }
    var open = button.getAttribute("aria-expanded") !== "true";
    button.setAttribute("aria-expanded", String(open));
    document.getElementById(button.getAttribute("aria-controls")).classList.toggle("is-open", open);
  });

  // -- theme -----------------------------------------------------------------

  var toggle = document.getElementById("theme-toggle");
  function setTheme(theme) {
    var root = document.documentElement;
    root.classList.remove("is-light", "is-dark");
    root.classList.add(theme);
    toggle.setAttribute("aria-pressed", String(theme === "is-dark"));
    toggle.querySelector(".adopt-theme__label").textContent =
      theme === "is-dark" ? "Light mode" : "Dark mode";
  }
  var saved = localStorage.getItem(STORAGE_KEY);
  setTheme(saved === "is-dark" || saved === "is-light" ? saved : "is-light");
  toggle.addEventListener("click", function () {
    var next = document.documentElement.classList.contains("is-dark") ? "is-light" : "is-dark";
    localStorage.setItem(STORAGE_KEY, next);
    setTheme(next);
  });

  readUrl();
  sortRows();
  apply();
})();
