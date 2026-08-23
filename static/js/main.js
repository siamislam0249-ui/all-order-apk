// Tiffin Desk - small progressive-enhancement helpers (no framework needed).

document.addEventListener("DOMContentLoaded", function () {
  // Auto-fade flash messages after a few seconds.
  document.querySelectorAll(".flash").forEach(function (el, i) {
    setTimeout(function () {
      el.style.transition = "opacity .4s ease";
      el.style.opacity = "0";
      setTimeout(function () { el.remove(); }, 400);
    }, 4500 + i * 200);
  });

  // Close any open inline "Edit" panel when clicking outside it,
  // and make sure only one edit panel is open at a time.
  const editPanels = document.querySelectorAll(".edit-panel");
  editPanels.forEach(function (panel) {
    panel.addEventListener("toggle", function () {
      if (panel.open) {
        editPanels.forEach(function (other) {
          if (other !== panel) other.open = false;
        });
      }
    });
  });

  document.addEventListener("click", function (e) {
    editPanels.forEach(function (panel) {
      if (panel.open && !panel.contains(e.target)) {
        panel.open = false;
      }
    });
  });
});
