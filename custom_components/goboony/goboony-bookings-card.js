class GoboonyBookingsCardEditor extends HTMLElement {
  static get _sections() {
    return {
      entity: {
        label: "Entity",
        icon: "mdi:database",
        expanded: true,
        schema: [
          { name: "entity", required: true, selector: { entity: { domain: "sensor" } } },
          { name: "review_entity", selector: { entity: { domain: "sensor" } } },
        ],
        labels: {
          entity: "Bookings entity",
          review_entity: "Reviews entity (optional)",
        },
      },
      header: {
        label: "Header",
        icon: "mdi:page-layout-header",
        schema: [
          { name: "title", selector: { text: {} } },
          { name: "show_header_icon", default: true, selector: { boolean: {} } },
          { name: "show_total_earnings", default: true, selector: { boolean: {} } },
          { name: "show_review", default: true, selector: { boolean: {} } },
        ],
        labels: {
          title: "Card title",
          show_header_icon: "Show camper icon",
          show_total_earnings: "Show total earnings",
          show_review: "Show review rating",
        },
      },
      active_rental: {
        label: "Active rental",
        icon: "mdi:car-key",
        schema: [
          { name: "show_active_rental", default: true, selector: { boolean: {} } },
          { name: "show_progress_bar", default: true, selector: { boolean: {} } },
        ],
        labels: {
          show_active_rental: "Show active rental banner",
          show_progress_bar: "Show progress bar",
        },
      },
      bookings: {
        label: "Bookings",
        icon: "mdi:book-multiple",
        schema: [
          { name: "show_earnings", default: true, selector: { boolean: {} } },
          { name: "show_days", default: true, selector: { boolean: {} } },
          { name: "show_booking_number", default: true, selector: { boolean: {} } },
          { name: "show_checkout_date", default: true, selector: { boolean: {} } },
          { name: "show_relative_date", default: true, selector: { boolean: {} } },
          { name: "show_gap_indicators", default: true, selector: { boolean: {} } },
          { name: "max_bookings", default: 0, selector: { number: { min: 0, max: 50, step: 1, mode: "box" } } },
          { name: "compact_mode", default: false, selector: { boolean: {} } },
        ],
        labels: {
          show_earnings: "Show earnings per booking",
          show_days: "Show number of days",
          show_booking_number: "Show booking number",
          show_checkout_date: "Show check-out date",
          show_relative_date: "Show relative date (e.g. 'in 3d')",
          show_gap_indicators: "Show gap days between bookings",
          max_bookings: "Max bookings to show (0 = all)",
          compact_mode: "Compact mode",
        },
      },
      filters: {
        label: "Filters",
        icon: "mdi:filter-variant",
        schema: [
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
        ],
        labels: {
          show_statuses: "Show statuses",
        },
      },
      appearance: {
        label: "Appearance",
        icon: "mdi:palette",
        schema: [
          { name: "show_section_labels", default: true, selector: { boolean: {} } },
          { name: "show_last_updated", default: true, selector: { boolean: {} } },
        ],
        labels: {
          show_section_labels: "Show section headers (Confirmed, Requests, ...)",
          show_last_updated: "Show last updated timestamp",
        },
      },
    };
  }

  set hass(hass) {
    this._hass = hass;
    if (this._forms) {
      for (const f of Object.values(this._forms)) f.hass = hass;
    }
  }

  setConfig(config) {
    this._config = { ...config };
    this._render();
  }

  _fireConfigChanged() {
    this.dispatchEvent(new CustomEvent("config-changed", {
      detail: { config: { ...this._config } },
    }));
  }

  _getDefaults() {
    return {
      show_statuses: ["confirmed", "accepted", "request", "inquiry", "message", "modified"],
      show_header_icon: true,
      show_total_earnings: true,
      show_review: true,
      show_active_rental: true,
      show_progress_bar: true,
      show_earnings: true,
      show_days: true,
      show_booking_number: true,
      show_checkout_date: true,
      show_relative_date: true,
      show_gap_indicators: true,
      show_section_labels: true,
      show_last_updated: true,
      max_bookings: 0,
      compact_mode: false,
    };
  }

  _render() {
    if (this._built) {
      this._updateForms();
      return;
    }
    this._built = true;
    this._forms = {};

    this.innerHTML = "";

    const style = document.createElement("style");
    style.textContent = `
      .editor-container { display: flex; flex-direction: column; gap: 8px; }
      ha-expansion-panel { --expansion-panel-summary-padding: 0 16px; }
      .panel-content { padding: 0 16px 16px; }
      .panel-header { display: flex; align-items: center; gap: 8px; }
      .panel-header ha-icon { color: var(--secondary-text-color); --mdc-icon-size: 20px; }
      .panel-header span { font-size: 14px; font-weight: 500; }
    `;
    this.appendChild(style);

    const container = document.createElement("div");
    container.className = "editor-container";
    this.appendChild(container);

    const sections = GoboonyBookingsCardEditor._sections;
    for (const [key, section] of Object.entries(sections)) {
      const panel = document.createElement("ha-expansion-panel");
      panel.outlined = true;
      if (section.expanded) panel.expanded = true;

      const header = document.createElement("div");
      header.slot = "header";
      header.className = "panel-header";
      header.innerHTML = `<ha-icon icon="${section.icon}"></ha-icon><span>${section.label}</span>`;
      panel.appendChild(header);

      const content = document.createElement("div");
      content.className = "panel-content";

      const form = document.createElement("ha-form");
      form.hass = this._hass;
      form.computeLabel = (s) => section.labels[s.name] || s.name;
      form.schema = section.schema;
      form.addEventListener("value-changed", (ev) => {
        const changed = ev.detail.value;
        for (const [k, v] of Object.entries(changed)) {
          this._config[k] = v;
        }
        this._fireConfigChanged();
        this._updateForms();
      });

      this._forms[key] = form;
      content.appendChild(form);
      panel.appendChild(content);
      container.appendChild(panel);
    }

    this._updateForms();
  }

  _updateForms() {
    const data = { ...this._getDefaults(), ...this._config };
    const sections = GoboonyBookingsCardEditor._sections;
    for (const [key, section] of Object.entries(sections)) {
      const form = this._forms[key];
      if (!form) continue;
      const sectionData = {};
      for (const field of section.schema) {
        sectionData[field.name] = data[field.name];
      }
      form.data = sectionData;
    }
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
      show_header_icon: true,
      show_total_earnings: true,
      show_review: true,
      show_active_rental: true,
      show_progress_bar: true,
      show_earnings: true,
      show_days: true,
      show_booking_number: true,
      show_checkout_date: true,
      show_relative_date: true,
      show_gap_indicators: true,
      show_section_labels: true,
      show_last_updated: true,
      max_bookings: 0,
      compact_mode: false,
    };
  }

  _esc(str) {
    if (str == null) return "";
    const d = document.createElement("div");
    d.textContent = String(str);
    return d.innerHTML;
  }

  _escUrl(url) {
    if (!url) return "";
    try {
      const u = new URL(url);
      if (u.protocol === "https:" || u.protocol === "http:") return u.href;
    } catch { /* invalid URL */ }
    return "";
  }

  _statusInfo(status) {
    const map = {
      confirmed: { label: "Confirmed", color: "var(--success-color, #4CAF50)" },
      accepted: { label: "Accepted", color: "var(--info-color, #2196F3)" },
      request_accepted: { label: "Accepted", color: "var(--info-color, #2196F3)" },
      request: { label: "Request", color: "var(--warning-color, #FF9800)" },
      inquiry: { label: "Inquiry", color: "var(--warning-color, #FF9800)" },
      message: { label: "Message", color: "var(--secondary-text-color)" },
      dates_changed_by_admin: { label: "Modified", color: "var(--secondary-text-color)" },
    };
    return map[status] || { label: status, color: "var(--secondary-text-color)" };
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

  _extractEndDate(booking) {
    const co = booking.check_out;
    if (co) {
      const m = co.match(/(\d{1,2})\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s*(\d{4})?/i);
      if (m) {
        const months = {jan:0,feb:1,mar:2,apr:3,may:4,jun:5,jul:6,aug:7,sep:8,oct:9,nov:10,dec:11};
        const year = m[3] ? parseInt(m[3]) : new Date().getFullYear();
        return new Date(year, months[m[2].toLowerCase()], parseInt(m[1]));
      }
    }
    return null;
  }

  _relativeDate(startDate) {
    if (!startDate) return "";
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const start = new Date(startDate);
    start.setHours(0, 0, 0, 0);
    const diff = Math.round((start - today) / 86400000);
    if (diff === 0) return "today";
    if (diff === 1) return "tomorrow";
    if (diff === -1) return "yesterday";
    if (diff > 1) return `in ${diff}d`;
    return `${Math.abs(diff)}d ago`;
  }

  _statusEnabled(status, showStatuses) {
    const map = {
      confirmed: "confirmed",
      accepted: "accepted",
      request_accepted: "accepted",
      request: "request",
      inquiry: "inquiry",
      message: "message",
      dates_changed_by_admin: "modified",
    };
    const key = map[status] || "message";
    return showStatuses.includes(key);
  }

  _findActiveRental(bookings) {
    const now = new Date();
    for (const b of bookings) {
      if (b.status !== "confirmed" && b.status !== "accepted" && b.status !== "request_accepted") continue;
      const startDate = this._extractStartDate(b);
      let endDate = null;
      if (b.check_out) {
        const m = b.check_out.match(/(\d{1,2})\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s*(\d{4})?/i);
        if (m) {
          const months = {jan:0,feb:1,mar:2,apr:3,may:4,jun:5,jul:6,aug:7,sep:8,oct:9,nov:10,dec:11};
          const year = m[3] ? parseInt(m[3]) : new Date().getFullYear();
          endDate = new Date(year, months[m[2].toLowerCase()], parseInt(m[1]));
        }
      }
      if (startDate && endDate) {
        const startDay = new Date(startDate.getFullYear(), startDate.getMonth(), startDate.getDate());
        const endDay = new Date(endDate.getFullYear(), endDate.getMonth(), endDate.getDate());
        const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
        if (today >= startDay && today <= endDay) {
          const totalDays = Math.max(1, Math.round((endDay - startDay) / 86400000));
          const elapsedDays = Math.round((today - startDay) / 86400000);
          const remainingDays = Math.round((endDay - today) / 86400000);
          const progress = Math.min(100, Math.round((elapsedDays / totalDays) * 100));
          return { booking: b, totalDays, elapsedDays, remainingDays, progress };
        }
      }
    }
    return null;
  }

  _lastUpdated() {
    const state = this._hass.states[this._entityId];
    if (!state || !state.last_updated) return "";
    const updated = new Date(state.last_updated);
    const now = new Date();
    const diffMin = Math.round((now - updated) / 60000);
    if (diffMin < 1) return "just now";
    if (diffMin === 1) return "1 min ago";
    if (diffMin < 60) return `${diffMin} min ago`;
    const diffHr = Math.round(diffMin / 60);
    if (diffHr === 1) return "1 hour ago";
    return `${diffHr} hours ago`;
  }

  _render() {
    if (!this._hass || !this._config) return;

    const state = this._hass.states[this._entityId];
    if (!state) {
      this.innerHTML = `<ha-card header="Goboony Bookings"><div class="card-content">Entity not found: ${this._esc(this._entityId)}</div></ha-card>`;
      return;
    }

    const bookings = state.attributes.bookings || [];
    const confirmed = bookings.filter(b => b.status === "confirmed" || b.status === "accepted" || b.status === "request_accepted");
    const totalEarnings = confirmed.reduce((sum, b) => sum + (b.earnings || 0), 0);
    const compact = this._config.compact_mode === true;

    // Review entity data
    let reviewHtml = "";
    if (this._config.show_review !== false && this._config.review_entity) {
      const reviewState = this._hass.states[this._config.review_entity];
      if (reviewState) {
        const rating = reviewState.state;
        const reviewCount = reviewState.attributes.review_count;
        if (rating && rating !== "unknown" && rating !== "unavailable") {
          const countStr = reviewCount != null ? ` (${this._esc(reviewCount)})` : "";
          reviewHtml = `<span class="header-rating">\u2605 ${this._esc(rating)}${countStr}</span>`;
        }
      }
    }

    // Active rental detection
    const activeRental = this._findActiveRental(bookings);
    let activeRentalHtml = "";
    if (activeRental && this._config.show_active_rental !== false) {
      const ab = activeRental.booking;
      const dates = this._esc(ab.check_in || ab.dates || "\u2014");
      const datesTo = this._esc(ab.check_out || "");
      const showProgress = this._config.show_progress_bar !== false;
      activeRentalHtml = `
        <div class="active-rental">
          <div class="active-rental-label">
            <svg class="active-rental-icon" viewBox="0 0 24 24"><path fill="currentColor" d="M5,11L6.5,6.5H17.5L19,11M17.5,16A1.5,1.5 0 0,1 16,14.5A1.5,1.5 0 0,1 17.5,13A1.5,1.5 0 0,1 19,14.5A1.5,1.5 0 0,1 17.5,16M6.5,16A1.5,1.5 0 0,1 5,14.5A1.5,1.5 0 0,1 6.5,13A1.5,1.5 0 0,1 8,14.5A1.5,1.5 0 0,1 6.5,16M18.92,6C18.72,5.42 18.16,5 17.5,5H6.5C5.84,5 5.28,5.42 5.08,6L3,12V20A1,1 0 0,0 4,21H5A1,1 0 0,0 6,20V19H18V20A1,1 0 0,0 19,21H20A1,1 0 0,0 21,20V12L18.92,6Z"/></svg>
            Active rental
          </div>
          <div class="active-rental-renter">
            <svg class="active-rental-person-icon" viewBox="0 0 24 24"><path fill="currentColor" d="M12,4A4,4 0 0,1 16,8A4,4 0 0,1 12,12A4,4 0 0,1 8,8A4,4 0 0,1 12,4M12,14C16.42,14 20,15.79 20,18V20H4V18C4,15.79 7.58,14 12,14Z"/></svg>
            ${this._esc(ab.renter) || "Unknown"}
          </div>
          <div class="active-rental-dates">
            ${dates}${datesTo ? ` \u2192 ${datesTo}` : ""}
          </div>
          <div class="active-rental-countdown">${activeRental.remainingDays} day${activeRental.remainingDays !== 1 ? "s" : ""} remaining</div>
          ${showProgress ? `
            <div class="active-rental-progress-track">
              <div class="active-rental-progress-bar" style="width:${activeRental.progress}%"></div>
            </div>
            <div class="active-rental-progress-label">${activeRental.progress}% complete</div>
          ` : ""}
        </div>
      `;
    }

    // Filter bookings — exclude active rental from list
    const activeBookingId = activeRental ? (activeRental.booking.booking_number || activeRental.booking.booking_id || activeRental.booking.id) : null;
    const showStatuses = this._config.show_statuses || ["confirmed", "accepted", "request", "inquiry", "message", "modified"];
    const filtered = bookings.filter(b => {
      if (!this._statusEnabled(b.status, showStatuses)) return false;
      if (activeBookingId) {
        const bid = b.booking_number || b.booking_id || b.id;
        if (bid && bid === activeBookingId) return false;
      }
      return true;
    });

    // Group by status, sort by date within
    const statusOrder = ["confirmed", "accepted", "request_accepted", "request", "inquiry", "message", "dates_changed_by_admin"];
    filtered.sort((a, b) => {
      const oa = statusOrder.indexOf(a.status); const ob = statusOrder.indexOf(b.status);
      const sa = oa >= 0 ? oa : 99; const sb = ob >= 0 ? ob : 99;
      if (sa !== sb) return sa - sb;
      const da = this._extractStartDate(a); const db = this._extractStartDate(b);
      if (!da && !db) return 0; if (!da) return 1; if (!db) return -1;
      return da - db;
    });

    const sectionLabels = {
      confirmed: "Confirmed", accepted: "Accepted", request_accepted: "Accepted",
      request: "Requests", inquiry: "Inquiries", message: "Messages",
      dates_changed_by_admin: "Modified",
    };

    // Apply max_bookings limit
    const maxBookings = parseInt(this._config.max_bookings) || 0;
    const limited = maxBookings > 0 ? filtered.slice(0, maxBookings) : filtered;
    const showSectionLabels = this._config.show_section_labels !== false;
    const showGapIndicators = this._config.show_gap_indicators !== false;
    const showRelativeDate = this._config.show_relative_date !== false;
    const showCheckoutDate = this._config.show_checkout_date !== false;
    const showBookingNumber = this._config.show_booking_number !== false;

    // Build booking rows
    let bookingRows = "";
    if (limited.length === 0) {
      bookingRows = `<div class="empty">No bookings found</div>`;
    } else {
      let lastSection = "";
      let prevConfirmedEnd = null;
      // If there's an active rental, use its end date as the starting point for gap calculation
      if (activeRental) {
        prevConfirmedEnd = this._extractEndDate(activeRental.booking);
      }
      for (let fi = 0; fi < limited.length; fi++) {
        const b = limited[fi];
        const section = sectionLabels[b.status] || b.status;
        if (section !== lastSection) {
          if (showSectionLabels) {
            if (lastSection !== "") bookingRows += `<div class="section-divider"></div>`;
            bookingRows += `<div class="section-label">${this._esc(section)}</div>`;
          }
          lastSection = section;
          if (section !== "Confirmed" && section !== "Accepted") prevConfirmedEnd = null;
        }

        // Gap indicator between confirmed bookings
        const isConfirmed = b.status === "confirmed" || b.status === "accepted" || b.status === "request_accepted";
        if (showGapIndicators && isConfirmed && prevConfirmedEnd) {
          const thisStart = this._extractStartDate(b);
          if (thisStart && prevConfirmedEnd) {
            const prevEnd = new Date(prevConfirmedEnd.getFullYear(), prevConfirmedEnd.getMonth(), prevConfirmedEnd.getDate());
            const curStart = new Date(thisStart.getFullYear(), thisStart.getMonth(), thisStart.getDate());
            const gapDays = Math.round((curStart - prevEnd) / 86400000);
            if (gapDays === 0) {
              bookingRows += `<div class="gap-indicator changeover"><svg viewBox="0 0 24 24" class="gap-icon"><path fill="currentColor" d="M7.41,8.58L12,13.17L16.59,8.58L18,10L12,16L6,10L7.41,8.58Z"/></svg> Changeover day</div>`;
            } else if (gapDays > 0) {
              bookingRows += `<div class="gap-indicator"><svg viewBox="0 0 24 24" class="gap-icon"><path fill="currentColor" d="M7.41,8.58L12,13.17L16.59,8.58L18,10L12,16L6,10L7.41,8.58Z"/></svg> ${gapDays} day${gapDays !== 1 ? "s" : ""} gap</div>`;
            }
          }
        }
        if (isConfirmed) {
          prevConfirmedEnd = this._extractEndDate(b);
        }
        const si = this._statusInfo(b.status);
        const dates = this._esc(b.check_in || b.dates || "\u2014");
        const datesTo = this._esc(b.check_out || "");
        const earnings = b.earnings != null ? `\u20ac${b.earnings.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}` : "\u2014";
        const days = b.num_days ? `${parseInt(b.num_days)}d` : "";
        const safeUrl = this._escUrl(b.url);
        const hasUrl = safeUrl.length > 0;
        const startDate = this._extractStartDate(b);
        const relative = showRelativeDate ? this._relativeDate(startDate) : "";
        const renter = this._esc(b.renter) || "Unknown";
        const bookingNum = this._esc(b.booking_number || b.id || "");

        if (compact) {
          bookingRows += `
            <${hasUrl ? `a href="${safeUrl}" target="_blank" rel="noopener noreferrer" class="booking-link"` : `div class="booking-link-none"`}>
              <div class="booking-compact" style="border-left-color:${si.color}">
                <span class="compact-renter">${renter}</span>
                <span class="compact-dates">${dates}${relative ? ` <span class="relative">${relative}</span>` : ""}</span>
                ${days && this._config.show_days !== false ? `<span class="compact-days">${days}</span>` : ""}
                ${this._config.show_earnings !== false ? `<span class="compact-earnings">${earnings}</span>` : ""}
              </div>
            </${hasUrl ? "a" : "div"}>
          `;
        } else {
          bookingRows += `
            <${hasUrl ? `a href="${safeUrl}" target="_blank" rel="noopener noreferrer" class="booking-link"` : `div class="booking-link-none"`}>
              <div class="booking" style="border-left-color:${si.color}">
                <div class="booking-header">
                  <div class="renter-block">
                    <span class="renter-name">${renter}</span>
                    ${showBookingNumber && bookingNum ? `<span class="booking-num">#${bookingNum}</span>` : ""}
                  </div>
                  ${this._config.show_earnings !== false ? `<span class="earnings" ${b.earnings != null ? "" : 'style="opacity:0.35"'}>${earnings}</span>` : ""}
                </div>
                <div class="booking-body">
                  <div class="dates">
                    <svg class="icon" viewBox="0 0 24 24"><path fill="currentColor" d="M19,19H5V8H19M16,1V3H8V1H6V3H5C3.89,3 3,3.89 3,5V19A2,2 0 0,2 5,21H19A2,2 0 0,0 21,19V5C21,3.89 20.1,3 19,3H18V1M17,12H12V17H17V12Z"/></svg>
                    <div class="date-range">
                      <span>${dates}</span>
                      ${showCheckoutDate && datesTo ? `<span class="date-arrow">\u2192</span><span>${datesTo}</span>` : ""}
                      ${relative ? `<span class="relative">${relative}</span>` : ""}
                    </div>
                  </div>
                  ${days && this._config.show_days !== false ? `<div class="days-row"><svg class="icon" viewBox="0 0 24 24"><path fill="currentColor" d="M12,20A8,8 0 0,0 20,12A8,8 0 0,0 12,4A8,8 0 0,0 4,12A8,8 0 0,0 12,20M12,2A10,10 0 0,1 22,12A10,10 0 0,1 12,22C6.47,22 2,17.5 2,12A10,10 0 0,1 12,2M12.5,7V12.25L17,14.92L16.25,16.15L11,13V7H12.5Z"/></svg><span>${days}</span></div>` : ""}
                </div>
              </div>
            </${hasUrl ? "a" : "div"}>
          `;
        }
      }
      if (maxBookings > 0 && filtered.length > maxBookings) {
        bookingRows += `<div class="truncated">${filtered.length - maxBookings} more booking${filtered.length - maxBookings !== 1 ? "s" : ""}...</div>`;
      }
    }

    const lastUpdated = this._lastUpdated();

    const showTotalEarnings = this._config.show_total_earnings !== false;
    const showLastUpdated = this._config.show_last_updated !== false;
    const cardTitle = this._esc(this._config.title) || "Goboony Bookings";

    this.innerHTML = `
      <ha-card>
        <div class="card-header-custom">
          <div class="header-left">
            ${this._config.show_header_icon !== false ? `<svg class="header-icon" viewBox="0 0 24 24"><path fill="currentColor" d="M5,11L6.5,6.5H17.5L19,11M17.5,16A1.5,1.5 0 0,1 16,14.5A1.5,1.5 0 0,1 17.5,13A1.5,1.5 0 0,1 19,14.5A1.5,1.5 0 0,1 17.5,16M6.5,16A1.5,1.5 0 0,1 5,14.5A1.5,1.5 0 0,1 6.5,13A1.5,1.5 0 0,1 8,14.5A1.5,1.5 0 0,1 6.5,16M18.92,6C18.72,5.42 18.16,5 17.5,5H6.5C5.84,5 5.28,5.42 5.08,6L3,12V20A1,1 0 0,0 4,21H5A1,1 0 0,0 6,20V19H18V20A1,1 0 0,0 19,21H20A1,1 0 0,0 21,20V12L18.92,6Z"/></svg>` : ""}
            <span class="header-title">${cardTitle}</span>
            ${reviewHtml}
          </div>
          ${showTotalEarnings ? `
            <div class="header-earnings">
              <span class="earnings-label">Total</span>
              <span class="earnings-value">\u20ac${totalEarnings.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}</span>
            </div>
          ` : ""}
        </div>
        <div class="card-content-custom">
          ${activeRentalHtml}
          ${bookingRows}
        </div>
        ${showLastUpdated && lastUpdated ? `<div class="card-footer">Updated ${lastUpdated}</div>` : ""}
      </ha-card>
      <style>
        ha-card {
          overflow: hidden;
          font-size: var(--ha-card-body-font-size, 14px);
        }

        /* Header */
        .card-header-custom {
          display: flex; justify-content: space-between; align-items: center;
          padding: 16px 16px 12px; flex-wrap: wrap; gap: 8px;
        }
        .header-left {
          display: flex; align-items: center; gap: 8px;
          color: var(--primary-text-color);
        }
        .header-title {
          font-size: var(--ha-card-header-font-size, 18px);
          font-weight: 500;
          line-height: 1.2;
        }
        .header-icon {
          width: 24px; height: 24px;
          color: var(--primary-color);
        }
        .header-rating {
          font-size: 0.85em; font-weight: 600;
          color: var(--warning-color, #FF9800);
          background: color-mix(in srgb, var(--warning-color, #FF9800) 12%, transparent);
          padding: 2px 8px; border-radius: 8px; white-space: nowrap;
        }
        .header-earnings {
          display: flex; align-items: center; gap: 8px;
        }
        .earnings-label {
          font-size: 0.85em; color: var(--secondary-text-color);
        }
        .earnings-value {
          font-size: 1.1em; font-weight: 700;
          color: var(--success-color, #4CAF50);
        }

        /* Content */
        .card-content-custom { padding: 0 16px 8px; }

        /* Active rental — subtle theme tint */
        .active-rental {
          background: color-mix(in srgb, var(--primary-color) 8%, var(--card-background-color, #fff));
          border: 1px solid color-mix(in srgb, var(--primary-color) 20%, transparent);
          border-radius: 12px; padding: 16px; margin-bottom: 16px;
          color: var(--primary-text-color);
        }
        .active-rental-label {
          display: flex; align-items: center; gap: 8px;
          font-size: 0.85em; font-weight: 700; text-transform: uppercase;
          letter-spacing: 0.06em; color: var(--primary-color);
          margin-bottom: 8px;
        }
        .active-rental-icon { width: 18px; height: 18px; color: var(--primary-color); }
        .active-rental-renter {
          display: flex; align-items: center; gap: 8px;
          font-size: 1.1em; font-weight: 600; margin-bottom: 4px;
          color: var(--primary-text-color);
        }
        .active-rental-person-icon {
          width: 20px; height: 20px;
          color: var(--secondary-text-color);
        }
        .active-rental-dates {
          font-size: 1em; color: var(--secondary-text-color);
          margin-bottom: 8px;
        }
        .active-rental-countdown {
          font-size: 1em; font-weight: 600;
          color: var(--primary-text-color); margin-bottom: 8px;
        }
        .active-rental-progress-track {
          background: color-mix(in srgb, var(--primary-color) 15%, transparent);
          border-radius: 4px; height: 6px; overflow: hidden; margin-bottom: 4px;
        }
        .active-rental-progress-bar {
          background: var(--primary-color); height: 100%;
          border-radius: 4px; transition: width 0.4s ease;
        }
        .active-rental-progress-label {
          font-size: 0.85em; color: var(--secondary-text-color);
          text-align: right;
        }

        /* Booking links */
        a.booking-link, div.booking-link-none {
          display: block; text-decoration: none; color: inherit;
        }
        a.booking-link:hover .booking, a.booking-link:hover .booking-compact {
          background: color-mix(in srgb, var(--primary-color) 5%, var(--card-background-color, #fff));
        }
        a.booking-link .booking, a.booking-link .booking-compact { cursor: pointer; }

        /* Normal booking row */
        .booking {
          border-left: 3px solid var(--divider-color, #e0e0e0);
          border-bottom: 1px solid var(--divider-color, #e0e0e0);
          padding: 12px 16px;
          transition: background 0.2s;
        }
        .booking:last-child { border-bottom: none; }
        .booking-header {
          display: flex; justify-content: space-between; align-items: flex-start;
          margin-bottom: 6px;
        }
        .renter-block { display: flex; flex-direction: column; gap: 2px; }
        .renter-name {
          font-weight: 500; color: var(--primary-text-color); font-size: 1em;
        }
        .booking-num {
          font-size: 0.85em; color: var(--secondary-text-color);
        }
        .earnings {
          font-size: 1em; font-weight: 600; color: var(--primary-text-color);
        }
        .booking-body { display: flex; flex-direction: column; gap: 4px; }
        .dates, .days-row {
          display: flex; align-items: center; gap: 8px;
          color: var(--secondary-text-color); font-size: 0.92em;
        }
        .icon {
          width: 16px; height: 16px; flex-shrink: 0;
          color: var(--secondary-text-color);
        }
        .date-range { display: flex; align-items: center; gap: 6px; flex-wrap: wrap; }
        .date-arrow { color: var(--secondary-text-color); font-weight: 500; }
        .relative {
          font-size: 0.85em; font-weight: 600;
          color: var(--primary-color);
          background: color-mix(in srgb, var(--primary-color) 8%, transparent);
          padding: 2px 8px; border-radius: 8px; white-space: nowrap;
        }

        /* Compact mode */
        .booking-compact {
          display: flex; align-items: center; gap: 12px;
          padding: 10px 16px;
          border-left: 3px solid var(--divider-color, #e0e0e0);
          border-bottom: 1px solid var(--divider-color, #e0e0e0);
          transition: background 0.2s;
        }
        .booking-compact:last-child { border-bottom: none; }
        .compact-renter {
          font-weight: 500; color: var(--primary-text-color);
          min-width: 80px; flex-shrink: 0;
        }
        .compact-dates {
          color: var(--secondary-text-color); flex: 1;
          white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
          font-size: 0.92em;
        }
        .compact-days {
          color: var(--secondary-text-color); flex-shrink: 0;
          font-size: 0.92em;
        }
        .compact-earnings {
          font-weight: 600; color: var(--primary-text-color); flex-shrink: 0;
        }

        /* Section dividers */
        .section-divider {
          height: 1px; background: var(--divider-color, #e0e0e0);
          margin: 12px 0 4px;
        }
        .section-label {
          font-size: 0.85em; font-weight: 500; text-transform: uppercase;
          letter-spacing: 0.06em; color: var(--secondary-text-color);
          padding: 4px 0 8px;
        }

        /* Footer */
        .card-footer {
          padding: 8px 16px 12px; text-align: right;
          font-size: 0.85em; color: var(--secondary-text-color);
          opacity: 0.5;
        }

        /* Gap indicator */
        .gap-indicator {
          display: flex; align-items: center; justify-content: center;
          gap: 6px; padding: 4px 16px;
          font-size: 0.85em; color: var(--secondary-text-color);
          border-left: 3px solid transparent;
        }
        .gap-indicator.changeover {
          color: var(--warning-color, #FF9800);
          font-weight: 500;
        }
        .gap-icon {
          width: 14px; height: 14px;
          color: inherit; opacity: 0.6;
        }

        /* Empty & truncated state */
        .empty {
          text-align: center; padding: 24px 16px;
          color: var(--secondary-text-color);
        }
        .truncated {
          text-align: center; padding: 8px 16px;
          font-size: 0.85em; color: var(--secondary-text-color);
          font-style: italic;
        }
      </style>
    `;
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
