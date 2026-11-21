# Changelog

All notable changes to this integration. Versions before 2.0.0 are described in the [GitHub releases](https://github.com/aaamoeder/ha-goboony/releases).

## 2.0.0 (2026-11-21)

### 💥 Breaking changes
- Goboony moved to the Yescapa platform in November 2026. The old login page and owner dashboard are gone, so 1.x can no longer log in. The integration now uses the JSON API of the new website.
- Bookings from the old Goboony site were not moved to the new platform. Booking counts and earnings start again from the bookings on the new platform.
- Booking statuses are now `confirmed`, `awaiting_payment` and `request`. The statuses `accepted`, `inquiry`, `message` and `modified` no longer exist.
- Base rate sensor attributes: `shoulder_early_rate`, `shoulder_late_rate`, `cleaning_fee` and `max_km_per_week` are replaced by `low_rate`, `seasons`, `deposit`, `weekly_discount` and `early_booker_discount`.
- Reviews sensor: the `times_hired` attribute is removed (no longer published).
- The total bookings sensor no longer has the `inquiries` attribute; it has `awaiting_payment` instead.

### ✨ New features
- An old Goboony listing ID is mapped to the new camper ID automatically, so existing entities and dashboards keep working.
- The calendar shows bookings that are only on the Goboony calendar, such as bookings made on the old site.
- Base rate sensor attributes for all season prices, mileage price, deposit and discounts.

### 🐛 Bug fixes
- Calendar bookings have their real check-in and check-out time in the Home Assistant time zone (they were all-day events before).
- Days until next booking and check-in countdown use the Home Assistant time zone.
- Blocked periods in the calendar have their real dates.

### 🔧 Improvements
- No more HTML scraping and no BeautifulSoup dependency.
- The access token is renewed automatically before it expires.
- Setup checks that the listing belongs to your account (new error "listing not found").

### 🌍 Translations
- New error message and listing ID help text in English, Dutch, German, French and Italian.

### 🎨 UI/UX
- Bookings card: statuses Confirmed, Awaiting payment and Requests. Cards saved with the old "Accepted" filter keep showing bookings that await payment.

### 📝 Documentation
- README updated for the new platform, with upgrade notes.
