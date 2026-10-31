/*
 * Orion's additions to the page editor. Runs before DOMContentLoaded, when Wagtail
 * reads which side panel to restore, so the first edit can open the preview.
 */
(() => {
  const WIDE_SCREEN = 1200;
  const NARROW_SCREEN = 800;
  const OPEN_KEY = "wagtail:side-panel-open";
  const WIDTH_KEY = "wagtail:side-panel-width";
  const DEVICE_KEY = "wagtail:preview-panel-device";
  const labels = document.currentScript.dataset;

  try {
    const openPanel = localStorage.getItem(OPEN_KEY);
    if (openPanel === null && window.innerWidth >= WIDE_SCREEN) {
      // First edit on a wide screen: preview at half the window. Wagtail remembers
      // the editor's later choices under the same keys.
      localStorage.setItem(OPEN_KEY, "preview");
      localStorage.setItem(WIDTH_KEY, String(Math.round(window.innerWidth / 2)));
    } else if (window.innerWidth < NARROW_SCREEN) {
      // On phones the panel covers the form, so editing starts on the form, and the
      // preview uses the phone size: a desktop page scaled down is unreadable.
      if (openPanel === "preview") {
        localStorage.setItem(OPEN_KEY, "");
      }
      localStorage.setItem(DEVICE_KEY, "mobile");
    }
  } catch {
    // Storage may be unavailable (private mode): Wagtail's defaults apply.
  }

  const addLabel = (button, text, className) => {
    if (!button || !text || button.querySelector(`.${className}`)) {
      return;
    }
    const label = document.createElement("span");
    label.className = className;
    label.textContent = text;
    button.append(label);
  };

  document.addEventListener("DOMContentLoaded", () => {
    addLabel(
      document.querySelector('[data-side-panel-toggle="preview"]'),
      labels.previewLabel,
      "orion-preview-label",
    );
    addLabel(
      document.querySelector("[data-form-side-close-button]"),
      labels.editLabel,
      "orion-edit-label",
    );
  });
})();
