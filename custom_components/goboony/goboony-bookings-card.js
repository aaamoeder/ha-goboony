class GoboonyBookingsCardEditor extends HTMLElement {
  set hass(hass) {
    this._hass = hass;
    if (this._form) this._form.hass = hass;
  }

  setConfig(config) {
    this._config = { ...config };
    this._render();
  }

  get _schema() {
    return [
      {
        name: "entity",
        required: true,
        selector: { entity: { domain: "sensor" } },
      },
      {
        name: "title",
        selector: { text: {} },
      },
      {
        name: "show_statuses",
        selector: {
          select: {
            multiple: true,
            custom_value: false,
            mode: "list",
            options: [
              { value: "confirmed", label: "Confirmed" },
              { value: "accepted", label: "Accepted" },
              { value: "request", label: "Requests" },
              { value: "inquiry", label: "Inquiries" },
              { value: "message", label: "Messages" },
              { value: "modified", label: "Modified" },
            ],
          },
        },
      },
      {
        name: "show_earnings",
        default: true,
        selector: { boolean: {} },
      },
      {
        name: "show_days",
        default: true,
        selector: { boolean: {} },
      },
    ];
  }

  _computeLabel(schema) {
    const labels = {
      entity: "Entity",
      title: "Title",
      show_statuses: "Show statuses",
      show_earnings: "Show earnings",
      show_days: "Show number of days",
    };
    return labels[schema.name] || schema.name;
  }

  _render() {
    if (!this._form) {
      this._form = document.createElement("ha-form");
      this._form.computeLabel = (s) => this._computeLabel(s);
      this._form.addEventListener("value-changed", (ev) => {
        const newConfig = ev.detail.value;
        this._config = newConfig;
        const event = new CustomEvent("config-changed", {
          detail: { config: newConfig },
        });
        this.dispatchEvent(event);
      });
      this.appendChild(this._form);
    }

    // Ensure defaults for ha-form data
    const data = {
      show_statuses: ["confirmed", "accepted", "request", "inquiry", "message", "modified"],
      show_earnings: true,
      show_days: true,
      ...this._config,
    };

    this._form.hass = this._hass;
    this._form.data = data;
    this._form.schema = this._schema;
  }
}

customElements.define("goboony-bookings-card-editor", GoboonyBookingsCardEditor);


class GoboonyBookingsCard extends HTMLElement {
  static getConfigElement() {
    return document.createElement("goboony-bookings-card-editor");
  }

  set hass(hass) {
    this._hass = hass;
    this._render();
  }

  setConfig(config) {
    this._config = config;
    this._entityId = config.entity || "sensor.goboony_total_bookings";
  }

  getCardSize() {
    return 4;
  }

  static getStubConfig() {
    return {
      entity: "sensor.goboony_total_bookings",
      title: "Goboony Bookings",
      show_statuses: ["confirmed", "accepted", "request", "inquiry", "message", "modified"],
      show_earnings: true,
      show_days: true,
    };
  }

  _statusInfo(status) {
    const map = {
      confirmed: { label: "Confirmed", icon: "✓", color: "#4CAF50", bg: "#E8F5E9" },
      request_accepted: { label: "Accepted", icon: "✓", color: "#4CAF50", bg: "#E8F5E9" },
      request: { label: "Request", icon: "⏳", color: "#FF9800", bg: "#FFF3E0" },
      inquiry: { label: "Inquiry", icon: "💬", color: "#2196F3", bg: "#E3F2FD" },
      message: { label: "Message", icon: "💬", color: "#2196F3", bg: "#E3F2FD" },
      dates_changed_by_admin: { label: "Modified", icon: "✎", color: "#9C27B0", bg: "#F3E5F5" },
    };
    return map[status] || { label: status, icon: "?", color: "#757575", bg: "#F5F5F5" };
  }

  _render() {
    if (!this._hass || !this._config) return;

    const state = this._hass.states[this._entityId];
    if (!state) {
      this.innerHTML = `<ha-card header="Goboony Bookings"><div class="card-content">Entity not found: ${this._entityId}</div></ha-card>`;
      return;
    }

    const bookings = state.attributes.bookings || [];
    const confirmed = bookings.filter(b => b.status === "confirmed" || b.status === "request_accepted");
    const totalEarnings = confirmed.reduce((sum, b) => sum + (b.earnings || 0), 0);

    // Filter bookings based on enabled statuses
    const showStatuses = this._config.show_statuses || ["confirmed", "accepted", "request", "inquiry", "message", "modified"];
    const filtered = bookings.filter(b => this._statusEnabled(b.status, showStatuses));

    // Sort by start date (earliest first)
    filtered.sort((a, b) => {
      const da = this._extractStartDate(a);
      const db = this._extractStartDate(b);
      if (!da && !db) return 0;
      if (!da) return 1;
      if (!db) return -1;
      return da - db;
    });

    // Build booking rows
    let bookingRows = "";
    if (filtered.length === 0) {
      bookingRows = `<div class="empty">No bookings found</div>`;
    } else {
      for (const b of filtered) {
        const si = this._statusInfo(b.status);
        const dates = b.check_in ? `${b.check_in}` : b.dates || "\u2014";
        const datesTo = b.check_out || "";
        const earnings = b.earnings != null ? `\u20ac${b.earnings.toFixed(2)}` : "\u2014";
        const days = b.num_days ? `${b.num_days}d` : "";

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
                <span>${b.renter || "Unknown"}</span>
              </div>
              <div class="dates">
                <svg class="icon" viewBox="0 0 24 24"><path fill="currentColor" d="M19,19H5V8H19M16,1V3H8V1H6V3H5C3.89,3 3,3.89 3,5V19A2,2 0 0,2 5,21H19A2,2 0 0,0 21,19V5C21,3.89 20.1,3 19,3H18V1M17,12H12V17H17V12Z"/></svg>
                <div class="date-range">
                  <span>${dates}</span>
                  ${datesTo ? `<span class="date-arrow">\u2192</span><span>${datesTo}</span>` : ""}
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
            <span>${this._config.title || "Goboony Bookings"}</span>
          </div>
          <div class="header-stats">
            <span class="stat">${confirmed.length} confirmed</span>
            <span class="stat total">\u20ac${totalEarnings.toFixed(2)}</span>
          </div>
        </div>
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
  }

  _extractStartDate(booking) {
    const ci = booking.check_in;
    if (ci) {
      const m = ci.match(/(\d{1,2})\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s*(\d{4})?/i);
      if (m) {
        const months = {jan:0,feb:1,mar:2,apr:3,may:4,jun:5,jul:6,aug:7,sep:8,oct:9,nov:10,dec:11};
        const year = m[3] ? parseInt(m[3]) : new Date().getFullYear();
        return new Date(year, months[m[2].toLowerCase()], parseInt(m[1]));
      }
    }
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

  _statusEnabled(status, showStatuses) {
    const map = {
      confirmed: "confirmed",
      request_accepted: "accepted",
      request: "request",
      inquiry: "inquiry",
      message: "message",
      dates_changed_by_admin: "modified",
    };
    const key = map[status] || "message";
    return showStatuses.includes(key);
  }
}

customElements.define("goboony-bookings-card", GoboonyBookingsCard);

window.customCards = window.customCards || [];
window.customCards.push({
  type: "goboony-bookings-card",
  name: "Goboony Bookings",
  description: "Shows upcoming Goboony bookings with status, dates and earnings",
  preview: true,
});
