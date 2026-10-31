/*
 * Location picker for the admin (LocationWidget). Registered as a Stimulus
 * controller, so it also starts on widgets that StreamField adds later. The value
 * lives as JSON ({"lat": ..., "lng": ...}) in the hidden input.
 */
(() => {
  const DECIMALS = 6;
  const MARKER_SVG =
    '<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M12 2a7 7 0 0 0-7 7c0 5.2 6.2 12.2 6.5 12.5a.7.7 0 0 0 1 0C12.8 21.2 19 14.2 19 9a7 7 0 0 0-7-7Zm0 9.5A2.5 2.5 0 1 1 12 6.5a2.5 2.5 0 0 1 0 5Z"/></svg>';

  const round = (number) => Number(number.toFixed(DECIMALS));

  class LocationController extends window.StimulusModule.Controller {
    static targets = ["input", "lat", "lng", "map"];

    static values = {
      centerLat: Number,
      centerLng: Number,
      zoom: Number,
      tilesUrl: String,
      tilesAttribution: String,
      maxZoom: Number,
    };

    connect() {
      this.map = window.L.map(this.mapTarget).setView(
        [this.centerLatValue, this.centerLngValue],
        this.zoomValue,
      );
      window.L.tileLayer(this.tilesUrlValue, {
        attribution: this.tilesAttributionValue,
        maxZoom: this.maxZoomValue,
      }).addTo(this.map);
      this.map.on("click", (event) => this.setLocation(event.latlng));
      // Maps inside collapsed panels need resizing once they become visible.
      this.resizeObserver = new ResizeObserver(() => this.map.invalidateSize());
      this.resizeObserver.observe(this.mapTarget);
      this.onInputChange = () => this.readInput(true);
      this.inputTarget.addEventListener("change", this.onInputChange);
      this.readInput(true);
    }

    disconnect() {
      this.inputTarget.removeEventListener("change", this.onInputChange);
      this.resizeObserver.disconnect();
      this.map.remove();
      this.marker = null;
    }

    readInput(moveView) {
      let location = null;
      try {
        location = JSON.parse(this.inputTarget.value || "null");
      } catch {
        location = null;
      }
      if (location && Number.isFinite(location.lat) && Number.isFinite(location.lng)) {
        this.showLocation(location, moveView);
      }
    }

    setLocation(latlng) {
      const location = { lat: round(latlng.lat), lng: round(latlng.lng) };
      this.inputTarget.value = JSON.stringify(location);
      this.showLocation(location, false);
    }

    showLocation(location, moveView) {
      this.latTarget.value = location.lat;
      this.lngTarget.value = location.lng;
      if (this.marker) {
        this.marker.setLatLng(location);
      } else {
        this.marker = window.L.marker(location, {
          draggable: true,
          icon: window.L.divIcon({
            className: "orion-marker",
            html: MARKER_SVG,
            iconSize: [32, 32],
            iconAnchor: [16, 30],
          }),
        }).addTo(this.map);
        this.marker.on("dragend", () => this.setLocation(this.marker.getLatLng()));
      }
      if (moveView) {
        this.map.setView(location, Math.max(this.map.getZoom(), 15));
      }
    }

    fromCoordinates() {
      const lat = Number.parseFloat(this.latTarget.value);
      const lng = Number.parseFloat(this.lngTarget.value);
      if (Math.abs(lat) <= 90 && Math.abs(lng) <= 180) {
        this.setLocation({ lat, lng });
        this.map.panTo([lat, lng]);
      }
    }

    clear() {
      this.inputTarget.value = "";
      this.latTarget.value = "";
      this.lngTarget.value = "";
      if (this.marker) {
        this.marker.remove();
        this.marker = null;
      }
    }
  }

  window.wagtail.app.register("orion-location", LocationController);
})();
