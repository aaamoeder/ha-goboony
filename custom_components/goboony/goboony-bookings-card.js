class GoboonyBookingsCardEditor extends HTMLElement {
  set hass(hass) {
    this._hass = hass;
    if (!this._rendered) this._render();
  }

  setConfig(config) {
    this._config = { ...config };
    if (this._rendered) this._render();
  }

  _render() {
    this._rendered = true;
    const cfg = this._config || {};

    this.innerHTML = `
      <style>
        .editor-row {
          display: flex;
          flex-direction: column;
          gap: 4px;
          margin-bottom: 16px;
        }
        .editor-row label {
          font-weight: 500;
          font-size: 0.9em;
          color: var(--primary-text-color);
        }
        .editor-row select, .editor-row input {
          padding: 8px 12px;
          border: 1px solid var(--divider-color, #ccc);
          border-radius: 8px;
          font-size: 0.95em;
          background: var(--card-background-color, #fff);
          color: var(--primary-text-color);
          font-family: inherit;
        }
        .editor-row .hint {
          font-size: 0.8em;
          color: var(--secondary-text-color);
        }
        .editor-toggle {
          display: flex;
          align-items: center;
          gap: 10px;
          margin-bottom: 12px;
        }
        .editor-toggle label {
          font-size: 0.9em;
          color: var(--primary-text-color);
        }
      </style>

      <div class="editor-row">
        <label>Entity</label>
        <select id="entity">
          ${this._entityOptions(cfg.entity)}
        </select>
        <span class="hint">Kies de Goboony totaal boekingen sensor</span>
      </div>

      <div class="editor-row">
        <label>Titel</label>
        <input id="title" type="text" value="${cfg.title || "Goboony Boekingen"}" placeholder="Goboony Boekingen" />
      </div>

      <div class="editor-row">
        <label>Standaard filter</label>
        <select id="default_filter">
          <option value="all" ${cfg.default_filter === "all" || !cfg.default_filter ? "selected" : ""}>Alles</option>
          <option value="confirmed" ${cfg.default_filter === "confirmed" ? "selected" : ""}>Bevestigd</option>
          <option value="request" ${cfg.default_filter === "request" ? "selected" : ""}>Aanvragen</option>
          <option value="message" ${cfg.default_filter === "message" ? "selected" : ""}>Berichten</option>
        </select>
      </div>

      <div class="editor-toggle">
        <input type="checkbox" id="show_earnings" ${cfg.show_earnings !== false ? "checked" : ""} />
        <label for="show_earnings">Inkomsten tonen</label>
      </div>

      <div class="editor-toggle">
        <input type="checkbox" id="show_days" ${cfg.show_days !== false ? "checked" : ""} />
        <label for="show_days">Aantal dagen tonen</label>
      </div>

      <div class="editor-toggle">
        <input type="checkbox" id="show_filters" ${cfg.show_filters !== false ? "checked" : ""} />
        <label for="show_filters">Filterknoppen tonen</label>
      </div>
    `;

    this.querySelector("#entity").addEventListener("change", (e) => this._update("entity", e.target.value));
    this.querySelector("#title").addEventListener("input", (e) => this._update("title", e.target.value));
    this.querySelector("#default_filter").addEventListener("change", (e) => this._update("default_filter", e.target.value));
    this.querySelector("#show_earnings").addEventListener("change", (e) => this._update("show_earnings", e.target.checked));
    this.querySelector("#show_days").addEventListener("change", (e) => this._update("show_days", e.target.checked));
    this.querySelector("#show_filters").addEventListener("change", (e) => this._update("show_filters", e.target.checked));
  }

  _entityOptions(selected) {
    if (!this._hass) return `<option value="${selected || ""}">${selected || ""}</option>`;
    const entities = Object.keys(this._hass.states)
      .filter(e => e.startsWith("sensor.goboony"))
      .sort();
    // Also include the current selection if not in list
    if (selected && !entities.includes(selected)) {
      entities.unshift(selected);
    }
    return entities.map(e =>
      `<option value="${e}" ${e === selected ? "selected" : ""}>${this._hass.states[e]?.attributes?.friendly_name || e}</option>`
    ).join("");
  }

  _update(key, value) {
    this._config = { ...this._config, [key]: value };
    const event = new CustomEvent("config-changed", { detail: { config: this._config } });
    this.dispatchEvent(event);
  }
}

customElements.define("goboony-bookings-card-editor", GoboonyBookingsCardEditor);


class GoboonyBookingsCard extends HTMLElement {
  constructor() {
    super();
    this._activeFilter = null;
  }

  static getConfigElement() {
    return document.createElement("goboony-bookings-card-editor");
  }

  set hass(hass) {
    this._hass = hass;
    this._render();
  }

  setConfig(config) {
    this._config = config;
    this._entityId = config.entity || "sensor.goboony_totaal_boekingen";
    if (this._activeFilter === null) {
      this._activeFilter = config.default_filter || "all";
    }
  }

  getCardSize() {
    return 4;
  }

  static getStubConfig() {
    return {
      entity: "sensor.goboony_totaal_boekingen",
      title: "Goboony Boekingen",
      default_filter: "all",
      show_earnings: true,
      show_days: true,
      show_filters: true,
    };
  }

  _statusInfo(status) {
    const map = {
      confirmed: { label: "Bevestigd", icon: "✓", color: "#4CAF50", bg: "#E8F5E9" },
      request_accepted: { label: "Geaccepteerd", icon: "✓", color: "#4CAF50", bg: "#E8F5E9" },
      request: { label: "Aanvraag", icon: "⏳", color: "#FF9800", bg: "#FFF3E0" },
      inquiry: { label: "Vraag", icon: "💬", color: "#2196F3", bg: "#E3F2FD" },
      message: { label: "Bericht", icon: "💬", color: "#2196F3", bg: "#E3F2FD" },
      dates_changed_by_admin: { label: "Gewijzigd", icon: "✎", color: "#9C27B0", bg: "#F3E5F5" },
    };
    return map[status] || { label: status, icon: "?", color: "#757575", bg: "#F5F5F5" };
  }

  _setFilter(filter) {
    this._activeFilter = filter;
    this._render();
  }

  _render() {
    if (!this._hass || !this._config) return;

    const state = this._hass.states[this._entityId];
    if (!state) {
      this.innerHTML = `<ha-card header="Goboony Boekingen"><div class="card-content">Entity niet gevonden: ${this._entityId}</div></ha-card>`;
      return;
    }

    const bookings = state.attributes.bookings || [];
    const confirmed = bookings.filter(b => b.status === "confirmed" || b.status === "request_accepted");
    const totalEarnings = confirmed.reduce((sum, b) => sum + (b.earnings || 0), 0);

    // Count per status for filter badges
    const counts = { all: bookings.length };
    for (const b of bookings) {
      const key = this._filterKey(b.status);
      counts[key] = (counts[key] || 0) + 1;
    }

    // Filter bookings
    const filtered = this._activeFilter === "all"
      ? [...bookings]
      : bookings.filter(b => this._filterKey(b.status) === this._activeFilter);

    // Sort by start date (earliest first)
    filtered.sort((a, b) => {
      const da = this._extractStartDate(a);
      const db = this._extractStartDate(b);
      if (!da && !db) return 0;
      if (!da) return 1;
      if (!db) return -1;
      return da - db;
    });

    // Build filter buttons
    const filters = [
      { key: "all", label: "Alles", color: "#757575", bg: "#F5F5F5" },
      { key: "confirmed", label: "Bevestigd", color: "#4CAF50", bg: "#E8F5E9" },
      { key: "request", label: "Aanvraag", color: "#FF9800", bg: "#FFF3E0" },
      { key: "message", label: "Berichten", color: "#2196F3", bg: "#E3F2FD" },
    ];

    let filterHtml = "";
    for (const f of filters) {
      if (f.key !== "all" && !counts[f.key]) continue;
      const active = this._activeFilter === f.key;
      filterHtml += `
        <button class="filter-btn ${active ? "active" : ""}" data-filter="${f.key}"
          style="--f-color:${f.color};--f-bg:${f.bg}">
          ${f.label}
          <span class="filter-count">${counts[f.key] || 0}</span>
        </button>
      `;
    }

    // Build booking rows
    let bookingRows = "";
    if (filtered.length === 0) {
      bookingRows = `<div class="empty">Geen boekingen met deze status</div>`;
    } else {
      for (const b of filtered) {
        const si = this._statusInfo(b.status);
        const dates = b.check_in ? `${b.check_in}` : b.dates || "—";
        const datesTo = b.check_out || "";
        const earnings = b.earnings != null ? `€${b.earnings.toFixed(2)}` : "—";
        const days = b.num_days ? `${b.num_days} dagen` : "";

        bookingRows += `
          <div class="booking">
            <div class="booking-header">
              <span class="status-badge" style="background:${si.bg};color:${si.color}">
                <span class="status-icon">${si.icon}</span> ${si.label}
              </span>
              ${this._config.show_earnings !== false ? `<span class="earnings" ${b.earnings != null ? "" : 'style="opacity:0.4"'}>${earnings}</span>` : ""}
            </div>
            <div class="booking-body">
              <div class="renter">
                <svg class="icon" viewBox="0 0 24 24"><path fill="currentColor" d="M12,4A4,4 0 0,1 16,8A4,4 0 0,1 12,12A4,4 0 0,1 8,8A4,4 0 0,1 12,4M12,14C16.42,14 20,15.79 20,18V20H4V18C4,15.79 7.58,14 12,14Z"/></svg>
                <span>${b.renter || "Onbekend"}</span>
              </div>
              <div class="dates">
                <svg class="icon" viewBox="0 0 24 24"><path fill="currentColor" d="M19,19H5V8H19M16,1V3H8V1H6V3H5C3.89,3 3,3.89 3,5V19A2,2 0 0,2 5,21H19A2,2 0 0,0 21,19V5C21,3.89 20.1,3 19,3H18V1M17,12H12V17H17V12Z"/></svg>
                <div class="date-range">
                  <span>${dates}</span>
                  ${datesTo ? `<span class="date-arrow">→</span><span>${datesTo}</span>` : ""}
                </div>
              </div>
              ${days && this._config.show_days !== false ? `<div class="days"><svg class="icon" viewBox="0 0 24 24"><path fill="currentColor" d="M12,20A8,8 0 0,0 20,12A8,8 0 0,0 12,4A8,8 0 0,0 4,12A8,8 0 0,0 12,20M12,2A10,10 0 0,1 22,12A10,10 0 0,1 12,22C6.47,22 2,17.5 2,12A10,10 0 0,1 12,2M12.5,7V12.25L17,14.92L16.25,16.15L11,13V7H12.5Z"/></svg><span>${days}</span></div>` : ""}
            </div>
          </div>
        `;
      }
    }

    this.innerHTML = `
      <ha-card>
        <div class="card-header-custom">
          <div class="header-left">
            <svg class="header-icon" viewBox="0 0 24 24"><path fill="currentColor" d="M5,11L6.5,6.5H17.5L19,11M17.5,16A1.5,1.5 0 0,1 16,14.5A1.5,1.5 0 0,1 17.5,13A1.5,1.5 0 0,1 19,14.5A1.5,1.5 0 0,1 17.5,16M6.5,16A1.5,1.5 0 0,1 5,14.5A1.5,1.5 0 0,1 6.5,13A1.5,1.5 0 0,1 8,14.5A1.5,1.5 0 0,1 6.5,16M18.92,6C18.72,5.42 18.16,5 17.5,5H6.5C5.84,5 5.28,5.42 5.08,6L3,12V20A1,1 0 0,0 4,21H5A1,1 0 0,0 6,20V19H18V20A1,1 0 0,0 19,21H20A1,1 0 0,0 21,20V12L18.92,6Z"/></svg>
            <span>${this._config.title || "Goboony Boekingen"}</span>
          </div>
          <div class="header-stats">
            <span class="stat">${confirmed.length} bevestigd</span>
            <span class="stat total">€${totalEarnings.toFixed(2)}</span>
          </div>
        </div>
        ${this._config.show_filters !== false ? `<div class="filter-bar">${filterHtml}</div>` : ""}
        <div class="card-content-custom">
          ${bookingRows}
        </div>
      </ha-card>
      <style>
        ha-card {
          overflow: hidden;
        }
        .card-header-custom {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 16px 16px 12px;
        }
        .header-left {
          display: flex;
          align-items: center;
          gap: 10px;
          font-size: 1.1em;
          font-weight: 500;
          color: var(--primary-text-color);
        }
        .header-icon {
          width: 28px;
          height: 28px;
          color: var(--primary-color, #03a9f4);
        }
        .header-stats {
          display: flex;
          gap: 12px;
          align-items: center;
        }
        .stat {
          font-size: 0.85em;
          color: var(--secondary-text-color);
          background: var(--secondary-background-color, #f5f5f5);
          padding: 4px 10px;
          border-radius: 12px;
        }
        .stat.total {
          font-weight: 600;
          color: #4CAF50;
          background: #E8F5E9;
        }
        .filter-bar {
          display: flex;
          gap: 8px;
          padding: 0 16px 12px;
          flex-wrap: wrap;
          border-bottom: 1px solid var(--divider-color, #e0e0e0);
        }
        .filter-btn {
          display: inline-flex;
          align-items: center;
          gap: 6px;
          padding: 6px 14px;
          border: 2px solid transparent;
          border-radius: 20px;
          background: var(--secondary-background-color, #f5f5f5);
          color: var(--secondary-text-color);
          font-size: 0.85em;
          font-weight: 500;
          cursor: pointer;
          transition: all 0.2s;
          font-family: inherit;
        }
        .filter-btn:hover {
          border-color: var(--f-color);
          background: var(--f-bg);
          color: var(--f-color);
        }
        .filter-btn.active {
          background: var(--f-bg);
          color: var(--f-color);
          border-color: var(--f-color);
          font-weight: 600;
        }
        .filter-count {
          background: rgba(0,0,0,0.08);
          padding: 1px 7px;
          border-radius: 10px;
          font-size: 0.9em;
          min-width: 18px;
          text-align: center;
        }
        .filter-btn.active .filter-count {
          background: rgba(0,0,0,0.1);
        }
        .card-content-custom {
          padding: 12px 16px 16px;
        }
        .booking {
          background: var(--card-background-color, #fff);
          border: 1px solid var(--divider-color, #e8e8e8);
          border-radius: 12px;
          padding: 14px;
          margin-bottom: 10px;
          transition: box-shadow 0.2s;
        }
        .booking:last-child {
          margin-bottom: 0;
        }
        .booking:hover {
          box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        }
        .booking-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 10px;
        }
        .status-badge {
          display: inline-flex;
          align-items: center;
          gap: 4px;
          padding: 4px 12px;
          border-radius: 20px;
          font-size: 0.82em;
          font-weight: 600;
          letter-spacing: 0.02em;
        }
        .status-icon {
          font-size: 0.9em;
        }
        .earnings {
          font-size: 1.15em;
          font-weight: 700;
          color: var(--primary-text-color);
        }
        .booking-body {
          display: flex;
          flex-direction: column;
          gap: 6px;
        }
        .renter, .dates, .days {
          display: flex;
          align-items: center;
          gap: 8px;
          color: var(--secondary-text-color);
          font-size: 0.92em;
        }
        .renter span {
          font-weight: 500;
          color: var(--primary-text-color);
          font-size: 1.02em;
        }
        .icon {
          width: 18px;
          height: 18px;
          flex-shrink: 0;
          color: var(--secondary-text-color);
          opacity: 0.7;
        }
        .date-range {
          display: flex;
          align-items: center;
          gap: 6px;
          flex-wrap: wrap;
        }
        .date-arrow {
          color: var(--primary-color, #03a9f4);
          font-weight: 600;
        }
        .empty {
          text-align: center;
          padding: 32px 16px;
          color: var(--secondary-text-color);
          font-style: italic;
        }
      </style>
    `;

    // Attach filter button click handlers
    this.querySelectorAll(".filter-btn").forEach(btn => {
      btn.addEventListener("click", () => {
        this._setFilter(btn.dataset.filter);
      });
    });
  }

  _extractStartDate(booking) {
    // Try check_in first (e.g. "Mon 27 Apr 2:00 PM")
    const ci = booking.check_in;
    if (ci) {
      const m = ci.match(/(\d{1,2})\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s*(\d{4})?/i);
      if (m) {
        const months = {jan:0,feb:1,mar:2,apr:3,may:4,jun:5,jul:6,aug:7,sep:8,oct:9,nov:10,dec:11};
        const year = m[3] ? parseInt(m[3]) : new Date().getFullYear();
        return new Date(year, months[m[2].toLowerCase()], parseInt(m[1]));
      }
    }
    // Try dates string (e.g. "Apr 27 - May 1, 2026")
    const ds = booking.dates;
    if (ds) {
      const m = ds.match(/(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{1,2})/i);
      if (m) {
        const months = {jan:0,feb:1,mar:2,apr:3,may:4,jun:5,jul:6,aug:7,sep:8,oct:9,nov:10,dec:11};
        const ym = ds.match(/(\d{4})/);
        const year = ym ? parseInt(ym[1]) : new Date().getFullYear();
        return new Date(year, months[m[1].toLowerCase()], parseInt(m[2]));
      }
    }
    return null;
  }

  _filterKey(status) {
    if (status === "confirmed" || status === "request_accepted" || status === "dates_changed_by_admin") return "confirmed";
    if (status === "request") return "request";
    return "message";
  }
}

customElements.define("goboony-bookings-card", GoboonyBookingsCard);

window.customCards = window.customCards || [];
window.customCards.push({
  type: "goboony-bookings-card",
  name: "Goboony Boekingen",
  description: "Toont aankomende Goboony boekingen met status, datums en inkomsten",
  preview: true,
});
