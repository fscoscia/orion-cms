/*
 * Loaded only when Wagtail renders a page as the editor's preview: links and forms
 * must not take the preview away from the page being edited.
 */
(() => {
  document.addEventListener(
    "click",
    (event) => {
      const link = event.target.closest("a[href]");
      if (!link) {
        return;
      }
      const url = new URL(link.href, window.location.href);
      const isSamePageAnchor =
        url.hash && url.pathname === window.location.pathname && url.search === "";
      if (!isSamePageAnchor) {
        event.preventDefault();
      }
    },
    true,
  );
  document.addEventListener("submit", (event) => event.preventDefault(), true);
})();
