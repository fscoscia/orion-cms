/*
 * Orion's interactive components, for the CSP build of Alpine.js.
 *
 * The CSP build does not evaluate expressions, so templates only name the properties
 * and methods defined here (for example x-on:click="toggle"). Load this file before
 * Alpine, both with `defer`.
 */
document.addEventListener("alpine:init", () => {
  /* A disclosure: a button that shows and hides a panel. */
  const disclosure = () => ({
    isOpen: false,

    init() {
      // Panels stay visible without JavaScript; CSS only collapses enhanced ones.
      this.$el.classList.add("is-enhanced");
    },

    get ariaExpanded() {
      return this.isOpen ? "true" : "false";
    },

    get stateClass() {
      return this.isOpen ? "is-open" : "";
    },

    toggle() {
      this.isOpen = !this.isOpen;
    },

    close(event) {
      if (!this.isOpen) {
        return;
      }
      // Escape closes one layer at a time: an open submenu, then the mobile menu.
      if (event) {
        event.stopPropagation();
      }
      this.isOpen = false;
      if (this.$refs.toggle) {
        this.$refs.toggle.focus();
      }
    },

    closeOnOutsideClick(event) {
      if (this.isOpen && !this.$el.contains(event.target)) {
        this.isOpen = false;
      }
    },
  });

  window.Alpine.data("navigation", disclosure);
  window.Alpine.data("submenu", disclosure);
});
