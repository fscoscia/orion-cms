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

  /*
   * Tabs following the WAI-ARIA tabs pattern. Without JavaScript the tab list stays
   * hidden and every panel shows with its own title. DOM nodes are looked up on each
   * call instead of being stored, because Alpine wraps component data in proxies.
   * Methods use $root: called from a tab's directive, $el is that tab.
   */
  window.Alpine.data("tabs", () => ({
    init() {
      const tabs = this.tabElements();
      this.$root.querySelector('[role="tablist"]').hidden = false;
      tabs.forEach((tab) => {
        const panel = this.panelOf(tab);
        panel.setAttribute("role", "tabpanel");
        panel.setAttribute("aria-labelledby", tab.id);
        panel.tabIndex = 0;
        const title = panel.querySelector(".orion-tabs__panel-title");
        if (title) {
          title.hidden = true;
        }
      });
      this.$root.classList.add("is-enhanced");
      this.show(0, false);
    },

    tabElements() {
      return Array.from(this.$root.querySelectorAll('[role="tab"]'));
    },

    panelOf(tab) {
      return document.getElementById(tab.getAttribute("aria-controls"));
    },

    show(index, moveFocus) {
      this.tabElements().forEach((tab, tabIndex) => {
        const isSelected = tabIndex === index;
        tab.setAttribute("aria-selected", isSelected ? "true" : "false");
        tab.tabIndex = isSelected ? 0 : -1;
        this.panelOf(tab).hidden = !isSelected;
        if (isSelected && moveFocus) {
          tab.focus();
        }
      });
    },

    select(event) {
      this.show(this.tabElements().indexOf(event.currentTarget), false);
    },

    onKeydown(event) {
      const tabs = this.tabElements();
      const current = tabs.indexOf(event.currentTarget);
      const targets = {
        ArrowRight: (current + 1) % tabs.length,
        ArrowLeft: (current - 1 + tabs.length) % tabs.length,
        Home: 0,
        End: tabs.length - 1,
      };
      if (!(event.key in targets)) {
        return;
      }
      event.preventDefault();
      this.show(targets[event.key], true);
    },
  }));

  /*
   * A number that counts up from zero when it scrolls into view. The HTML already
   * holds the final number, which stays as is with reduced motion or without support.
   */
  window.Alpine.data("counter", () => ({
    display: "",

    init() {
      const target = Number.parseInt(this.$el.dataset.target, 10) || 0;
      this.display = String(target);
      const prefersReducedMotion = window.matchMedia(
        "(prefers-reduced-motion: reduce)",
      ).matches;
      if (prefersReducedMotion || !("IntersectionObserver" in window)) {
        return;
      }
      this.display = "0";
      const observer = new IntersectionObserver((entries) => {
        if (entries.some((entry) => entry.isIntersecting)) {
          observer.disconnect();
          this.countUpTo(target);
        }
      });
      observer.observe(this.$el);
    },

    countUpTo(target) {
      const durationMs = 1200;
      const start = performance.now();
      const step = (now) => {
        const progress = Math.min((now - start) / durationMs, 1);
        // Ease out, so the count slows down near the final number.
        const eased = 1 - (1 - progress) ** 3;
        this.display = String(Math.round(target * eased));
        if (progress < 1) {
          window.requestAnimationFrame(step);
        }
      };
      window.requestAnimationFrame(step);
    },
  }));
});
