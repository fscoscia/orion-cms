/*
 * Orion's interactive components, for the CSP build of Alpine.js.
 *
 * The CSP build does not evaluate expressions, so templates only name the properties
 * and methods defined here (for example x-on:click="toggle"). Load this file before
 * Alpine, both with `defer`.
 */
const MARKER_SVG =
  '<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M12 2a7 7 0 0 0-7 7c0 5.2 6.2 12.2 6.5 12.5a.7.7 0 0 0 1 0C12.8 21.2 19 14.2 19 9a7 7 0 0 0-7-7Zm0 9.5A2.5 2.5 0 1 1 12 6.5a2.5 2.5 0 0 1 0 5Z"/></svg>';

let leafletPromise = null;

/* Add Leaflet's stylesheet and script once, from the site itself. */
function loadLeaflet(cssUrl, jsUrl) {
  if (!leafletPromise) {
    const load = (element) =>
      new Promise((resolve, reject) => {
        element.onload = resolve;
        element.onerror = reject;
        document.head.append(element);
      });
    const stylesheet = document.createElement("link");
    stylesheet.rel = "stylesheet";
    stylesheet.href = cssUrl;
    const script = document.createElement("script");
    script.src = jsUrl;
    // The map is laid out only once both its styles and its code are in.
    leafletPromise = Promise.all([load(stylesheet), load(script)]);
  }
  return leafletPromise;
}

/*
 * Blocks marked data-reveal (ORION_BLOCK_REVEAL) appear as they enter the screen. CSS
 * hides them only when scripts run, so this must never leave one hidden: without an
 * observer they all show, and if the observer does not answer in a few seconds (for
 * example a tab in the background) they show too.
 */
(() => {
  const items = Array.from(document.querySelectorAll("[data-reveal]"));
  if (items.length === 0) {
    return;
  }
  const show = (item) => item.classList.add("is-revealed");
  if (!("IntersectionObserver" in window)) {
    items.forEach(show);
    return;
  }
  let hasAnswered = false;
  const observer = new IntersectionObserver(
    (entries) => {
      hasAnswered = true;
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          show(entry.target);
          observer.unobserve(entry.target);
        }
      });
    },
    { rootMargin: "0px 0px -10% 0px" },
  );
  items.forEach((item) => observer.observe(item));
  window.setTimeout(() => {
    if (!hasAnswered) {
      observer.disconnect();
      items.forEach(show);
    }
  }, 3000);
})();

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
  /*
   * A map that loads on request: Leaflet and the tiles (from an external provider)
   * are only fetched when the visitor presses "Show map". Points come from a JSON
   * script element, which the browser does not run.
   */
  window.Alpine.data("map", () => ({
    init() {
      // Without JavaScript the button stays hidden and the link remains.
      this.$refs.showButton.hidden = false;
    },

    async show() {
      const root = this.$root;
      await loadLeaflet(root.dataset.leafletCss, root.dataset.leafletJs);
      const points = JSON.parse(
        root.querySelector('script[type="application/json"]').textContent,
      );
      const canvas = this.$refs.canvas;
      canvas.hidden = false;
      this.$refs.showButton.hidden = true;
      const L = window.L;
      const map = L.map(canvas);
      L.tileLayer(root.dataset.tilesUrl, {
        attribution: root.dataset.tilesAttribution,
        maxZoom: Number(root.dataset.maxZoom) || 19,
      }).addTo(map);
      const icon = L.divIcon({
        className: "orion-map__marker",
        html: MARKER_SVG,
        iconSize: [32, 32],
        iconAnchor: [16, 30],
        popupAnchor: [0, -28],
      });
      const markers = points.map((point) => {
        const marker = L.marker([point.lat, point.lng], { icon, title: point.name });
        const popup = document.createElement("div");
        if (point.name) {
          const name = document.createElement("strong");
          name.textContent = point.name;
          popup.append(name);
        }
        if (point.description) {
          const description = document.createElement("p");
          description.textContent = point.description;
          popup.append(description);
        }
        if (popup.childNodes.length) {
          marker.bindPopup(popup);
        }
        return marker.addTo(map);
      });
      if (markers.length === 1) {
        map.setView(markers[0].getLatLng(), Number(root.dataset.zoom) || 16);
      } else {
        map.fitBounds(L.featureGroup(markers).getBounds(), { padding: [32, 32] });
      }
      canvas.focus();
    },
  }));

  /*
   * A video over its cover. It stops when it leaves the screen, which also covers a
   * slide moving away; an ambient video plays while on screen, unless the visitor
   * prefers reduced motion or paused it.
   */
  window.Alpine.data("video", () => ({
    isPausedByVisitor: false,

    init() {
      const isAmbient = "ambient" in this.$root.dataset;
      if (!isAmbient) {
        this.$refs.player.hidden = true;
        this.$refs.start.hidden = false;
      }
      if (!("IntersectionObserver" in window)) {
        return;
      }
      const prefersReducedMotion = window.matchMedia(
        "(prefers-reduced-motion: reduce)",
      ).matches;
      const canAutoplay = isAmbient && !prefersReducedMotion;
      if (canAutoplay) {
        this.$refs.toggle.hidden = false;
      }
      const observer = new IntersectionObserver(
        (entries) => {
          const isOnScreen = entries[entries.length - 1].isIntersecting;
          if (!isOnScreen) {
            this.$refs.player.pause();
          } else if (canAutoplay && !this.isPausedByVisitor) {
            this.play();
          }
        },
        { threshold: 0.25 },
      );
      observer.observe(this.$root);
    },

    play() {
      // The browser may refuse; the cover stays in place.
      this.$refs.player.play().catch(() => {});
    },

    /* The cover's play button gives way to the video and its native controls. */
    start() {
      this.$refs.start.hidden = true;
      this.$refs.player.hidden = false;
      this.$refs.player.focus();
      this.play();
    },

    toggle() {
      this.isPausedByVisitor = !this.isPausedByVisitor;
      this.$refs.toggle.setAttribute(
        "aria-pressed",
        this.isPausedByVisitor ? "true" : "false",
      );
      if (this.isPausedByVisitor) {
        this.$refs.player.pause();
      } else {
        this.play();
      }
    },
  }));

  /*
   * Controls over a track that scrolls natively, so touch gestures work by themselves
   * and without JavaScript the slides can still be scrolled. The arrows use
   * aria-disabled, not disabled, so that the keyboard focus stays on them at the ends.
   */
  window.Alpine.data("carousel", () => ({
    init() {
      this.$refs.controls.hidden = false;
      this.$root.classList.add("is-enhanced");
      this.update();
    },

    slides() {
      return Array.from(this.$refs.track.children);
    },

    /* Scroll position of a slide, measured from the first one. */
    positionOf(slide) {
      return slide.offsetLeft - this.slides()[0].offsetLeft;
    },

    /* The slide closest to the start of the track. */
    nearestIndex() {
      const { scrollLeft } = this.$refs.track;
      const distances = this.slides().map((slide) =>
        Math.abs(this.positionOf(slide) - scrollLeft),
      );
      return distances.indexOf(Math.min(...distances));
    },

    isAtEnd() {
      const track = this.$refs.track;
      return track.scrollLeft + track.clientWidth >= track.scrollWidth - 1;
    },

    update() {
      const last = this.slides().length - 1;
      const isAtEnd = this.isAtEnd();
      const current = isAtEnd ? last : this.nearestIndex();
      this.$refs.previous.setAttribute(
        "aria-disabled",
        current === 0 ? "true" : "false",
      );
      this.$refs.next.setAttribute("aria-disabled", isAtEnd ? "true" : "false");
      Array.from(this.$refs.dots.children).forEach((dot, index) => {
        if (index === current) {
          dot.setAttribute("aria-current", "true");
        } else {
          dot.removeAttribute("aria-current");
        }
      });
      this.$refs.status.textContent = this.$root.dataset.status
        .replace("{current}", current + 1)
        .replace("{total}", last + 1);
    },

    goTo(index) {
      const slides = this.slides();
      const slide = slides[Math.max(0, Math.min(index, slides.length - 1))];
      const prefersReducedMotion = window.matchMedia(
        "(prefers-reduced-motion: reduce)",
      ).matches;
      this.$refs.track.scrollTo({
        left: this.positionOf(slide),
        behavior: prefersReducedMotion ? "auto" : "smooth",
      });
    },

    previous() {
      this.goTo(this.nearestIndex() - 1);
    },

    next() {
      this.goTo(this.nearestIndex() + 1);
    },

    goToDot(event) {
      this.goTo(Number(event.currentTarget.dataset.index));
    },

    onKeydown(event) {
      // A video with controls uses the arrows to seek.
      if (event.target.closest("video")) {
        return;
      }
      if (event.key === "ArrowRight") {
        event.preventDefault();
        this.next();
      } else if (event.key === "ArrowLeft") {
        event.preventDefault();
        this.previous();
      }
    },
  }));

  /*
   * The time left until a deadline. Pages are cached, so the browser works it out from
   * the deadline written in the page. Without JavaScript the written date is all there
   * is, and the clock stays hidden.
   */
  window.Alpine.data("countdown", () => ({
    days: "0",
    hours: "00",
    minutes: "00",
    seconds: "00",
    timer: null,

    init() {
      const deadline = Date.parse(this.$root.dataset.deadline);
      if (Number.isNaN(deadline)) {
        return;
      }
      this.$refs.clock.hidden = false;
      this.tick(deadline);
      if (Date.now() < deadline) {
        this.timer = window.setInterval(() => this.tick(deadline), 1000);
      }
    },

    destroy() {
      window.clearInterval(this.timer);
    },

    tick(deadline) {
      const pad = (number) => String(number).padStart(2, "0");
      const remaining = Math.max(0, deadline - Date.now());
      const total = Math.floor(remaining / 1000);
      this.days = String(Math.floor(total / 86400));
      this.hours = pad(Math.floor((total % 86400) / 3600));
      this.minutes = pad(Math.floor((total % 3600) / 60));
      this.seconds = pad(total % 60);
      if (remaining === 0) {
        window.clearInterval(this.timer);
        // The editor's message replaces the zeros, when there is one.
        if (this.$refs.closed) {
          this.$refs.clock.hidden = true;
          this.$refs.closed.hidden = false;
        }
      }
    },
  }));

  /*
   * A marquee that is still until this runs: it starts the movement, which CSS only
   * plays when the visitor has not asked for reduced motion, and shows the pause
   * button. The pointer over the marquee pauses it too (see orion.css).
   */
  window.Alpine.data("marquee", () => ({
    isPaused: false,

    init() {
      this.$root.classList.add("is-moving");
      const prefersReducedMotion = window.matchMedia(
        "(prefers-reduced-motion: reduce)",
      ).matches;
      if (!prefersReducedMotion) {
        this.$refs.toggle.hidden = false;
      }
    },

    get stateClass() {
      return this.isPaused ? "is-paused" : "";
    },

    get pressed() {
      return this.isPaused ? "true" : "false";
    },

    get label() {
      const { labelPause, labelPlay } = this.$root.dataset;
      return this.isPaused ? labelPlay : labelPause;
    },

    toggle() {
      this.isPaused = !this.isPaused;
    },
  }));

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
