<p align="center">
  <img src="https://raw.githubusercontent.com/aaamoeder/ha-goboony/main/images/banner.png" alt="Goboony for Home Assistant" width="800">
</p>

<p align="center">
  <a href="https://github.com/hacs/integration"><img src="https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge" alt="HACS Custom"></a>
  <a href="https://github.com/aaamoeder/ha-goboony/releases"><img src="https://img.shields.io/github/release/aaamoeder/ha-goboony.svg?style=for-the-badge" alt="GitHub Release"></a>
  <a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge" alt="License: MIT"></a>
</p>

<p align="center">
  An all-in-one Home Assistant package for <a href="https://www.goboony.com">Goboony</a> camper/motorhome rental owners.<br>
  Includes a <strong>custom integration</strong> (sensors, calendar, binary sensors, diagnostics) and a <strong>custom Lovelace card</strong> with visual editor.<br>
  Track your bookings, earnings, availability, rates and reviews directly in your smart home.
</p>

---

<p align="center">
  <em>If this project helped you, please consider buying me a coffee</em> ☕
</p>

<p align="center">
  <a href="https://buymeacoffee.com/aaamoeder">
    <img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" alt="Buy Me A Coffee" width="217">
  </a>
</p>

---

## Features

| Feature | Description |
|---------|-------------|
| **Bookings overview** | Total, confirmed, accepted, pending and inquiry counts |
| **Next booking** | Upcoming booking details with countdown |
| **Check-in countdown** | Hours until next check-in |
| **Earnings tracking** | Total confirmed + accepted earnings |
| **Rate monitoring** | Base and peak season rates |
| **Calendar availability** | Booked, blocked and available day counts |
| **Occupancy rate** | Percentage of booked vs available days |
| **Blocked periods** | Named blocked periods (holidays, maintenance, etc.) |
| **Reviews & rating** | Listing rating and review count |
| **Currently rented** | Binary sensor: ON when camper is rented out |
| **Pending requests** | Binary sensor: ON when there are open booking requests |
| **Upcoming booking** | Binary sensor: ON when a future booking exists |
| **Turnaround** | Binary sensor: ON between check-out and next check-in |
| **Manual refresh** | Button entity to trigger an immediate data update |
| **Listing photo** | Image entity showing your listing's main photo |
| **Calendar entity** | Native HA calendar with all bookings and blocked periods |
| **Custom card** | Fully configurable bookings card with visual editor |
| **Diagnostics** | Download debug data from the integration page |

## Installation

### HACS (Recommended)

1. Open **HACS** in your Home Assistant instance
2. Click the **three dots** menu (top right) and select **Custom repositories**
3. Add this repository URL:
   ```
   https://github.com/aaamoeder/ha-goboony
   ```
4. Set the category to **Integration** and click **Add**
5. Find **Goboony** in the HACS store and click **Install**
6. **Restart** Home Assistant

### Manual installation

1. Download the [latest release](https://github.com/aaamoeder/ha-goboony/releases/latest)
2. Copy the `custom_components/goboony` folder to your `config/custom_components/` directory
3. Restart Home Assistant

## Configuration

1. Go to **Settings** > **Devices & Services** > **Add Integration**
2. Search for **Goboony**
3. Enter your credentials:

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `email` | string | yes | Your Goboony owner account email |
| `password` | string | yes | Your Goboony password |
| `listing_id` | string | yes | Found in the URL of your listing page (e.g. `goboony.com/listings/12345`) |

> The integration supports **re-authentication** — if your session expires, Home Assistant will prompt you to re-enter your credentials.

### Options

After setup, go to **Settings** > **Devices & Services** > **Goboony** > **Configure** to change:

| Name | Type | Required | Default | Since | Description |
|------|------|----------|---------|-------|-------------|
| `scan_interval` | number | no | `60` | v1.0.0 | How often to fetch data from Goboony (minutes, range: 15–1440) |

## Entities

### Sensors

| Sensor | Description | Unit | Category |
|--------|-------------|------|----------|
| Total bookings | Number of all bookings | — | — |
| Confirmed bookings | Number of confirmed + accepted bookings | — | — |
| Next booking | Dates of the next confirmed booking | — | — |
| Days until next booking | Countdown to next booking | days | — |
| Check-in countdown | Hours until next check-in | hours | — |
| Total earnings | Sum of confirmed + accepted booking earnings | EUR | — |
| Occupancy rate | Booked days as percentage of total | % | — |
| Reviews | Listing rating (e.g. 5.0) with review count | — | — |
| Base rate | Low season daily rate | EUR | Diagnostic |
| Peak rate | High season daily rate | EUR | Diagnostic |
| Booked days | Days with confirmed bookings | days | — |
| Blocked days | Owner-blocked days | days | — |
| Available days | Available days on calendar | days | — |
| Blocked periods | Number of blocked periods | — | Diagnostic |

### Binary sensors

| Sensor | Description |
|--------|-------------|
| Currently rented | ON when the camper is currently rented out |
| Pending requests | ON when there are open booking requests or inquiries |
| Upcoming booking | ON when there is a future confirmed booking |
| Turnaround | ON between a check-out and the next check-in |

### Other entities

| Entity | Type | Description |
|--------|------|-------------|
| Refresh data | Button | Trigger an immediate data refresh |
| Listing photo | Image | Main photo from your Goboony listing |
| Bookings calendar | Calendar | All bookings and blocked periods |

## Custom Lovelace card

The integration includes a custom bookings card that is **automatically registered** — no manual resource setup needed.

<p align="center">
  <img src="https://raw.githubusercontent.com/aaamoeder/ha-goboony/main/images/card-light.png" alt="Bookings card — light mode" width="400">
  &nbsp;&nbsp;
  <img src="https://raw.githubusercontent.com/aaamoeder/ha-goboony/main/images/card-dark.png" alt="Bookings card — dark mode" width="400">
</p>

### Adding the card

1. Edit your dashboard
2. Click **Add Card**
3. Search for **Goboony Bookings**
4. Configure via the visual editor

### Card features

- Active rental banner with progress bar and countdown
- Gap indicators between bookings showing days between rentals
- Changeover day detection (when check-out = next check-in)
- Clickable bookings linking to Goboony detail page
- Relative date badges ("in 3d", "tomorrow", etc.)
- Review rating display in header
- Multi-status filtering (confirmed, accepted, requests, inquiries, messages, modified)
- Earnings per booking and total earnings in header
- Compact mode for a denser layout
- Fully themed using HA CSS variables — works with all themes (light, dark, custom)
- Visual editor with collapsible sections (Mushroom card style)

### Card options

The visual editor is organized in collapsible sections:

#### Entity

| Name | Type | Required | Default | Since | Description |
|------|------|----------|---------|-------|-------------|
| `entity` | string | yes | — | v1.0.0 | The Goboony total bookings sensor entity |
| `review_entity` | string | no | — | v1.5.0 | The Goboony reviews sensor entity |

#### Header

| Name | Type | Required | Default | Since | Description |
|------|------|----------|---------|-------|-------------|
| `title` | string | no | `Goboony Bookings` | v1.0.0 | Custom title text |
| `show_header_icon` | boolean | no | `true` | v1.7.0 | Show/hide the camper icon in the header |
| `show_total_earnings` | boolean | no | `true` | v1.7.0 | Show/hide total earnings in the header |
| `show_review` | boolean | no | `true` | v1.7.0 | Show/hide the star rating badge |

#### Active rental

| Name | Type | Required | Default | Since | Description |
|------|------|----------|---------|-------|-------------|
| `show_active_rental` | boolean | no | `true` | v1.7.0 | Show/hide the active rental section |
| `show_progress_bar` | boolean | no | `true` | v1.7.0 | Show/hide the rental progress bar |

#### Bookings

| Name | Type | Required | Default | Since | Description |
|------|------|----------|---------|-------|-------------|
| `show_earnings` | boolean | no | `true` | v1.7.0 | Show/hide earnings on each booking |
| `show_days` | boolean | no | `true` | v1.7.0 | Show/hide rental duration |
| `show_booking_number` | boolean | no | `true` | v1.7.0 | Show/hide the booking reference (#12345) |
| `show_checkout_date` | boolean | no | `true` | v1.7.0 | Show/hide the check-out date |
| `show_relative_date` | boolean | no | `true` | v1.7.0 | Show/hide relative date badges (e.g. "in 3d") |
| `show_gap_indicators` | boolean | no | `true` | v1.7.0 | Show/hide gap days and changeover indicators |
| `max_bookings` | number | no | `0` | v1.7.0 | Limit the number of bookings shown (0 = all) |
| `compact_mode` | boolean | no | `false` | v1.7.0 | Use a compact single-line layout |

#### Filters

| Name | Type | Required | Default | Since | Description |
|------|------|----------|---------|-------|-------------|
| `show_statuses` | list | no | all | v1.6.0 | Which booking statuses to display (confirmed, accepted, request, inquiry, message, modified) |

#### Appearance

| Name | Type | Required | Default | Since | Description |
|------|------|----------|---------|-------|-------------|
| `show_section_labels` | boolean | no | `true` | v1.7.0 | Show/hide section labels (Confirmed, Requests, etc.) |
| `show_last_updated` | boolean | no | `true` | v1.7.0 | Show/hide the "Updated X min ago" footer |

### YAML example

```yaml
type: custom:goboony-bookings-card
entity: sensor.goboony_68972_total_bookings
review_entity: sensor.goboony_68972_reviews
title: My Camper Bookings
show_statuses:
  - confirmed
  - accepted
  - request
show_header_icon: true
show_total_earnings: true
show_review: true
show_active_rental: true
show_progress_bar: true
show_earnings: true
show_days: true
show_booking_number: true
show_checkout_date: true
show_relative_date: true
show_gap_indicators: true
show_section_labels: true
show_last_updated: true
max_bookings: 0
compact_mode: false
```

## Calendar

The integration creates a native Home Assistant **calendar entity** showing:
- Confirmed and accepted bookings with renter name and dates
- Owner-blocked periods

This works with all calendar cards and automations in Home Assistant.

## Diagnostics

Go to **Settings** > **Devices & Services** > **Goboony** > **three dots** > **Download diagnostics** to get a debug data file. Credentials are automatically redacted.

## How it works

Goboony does not provide a public API. Their mobile app uses server-rendered HTML via [Turbo Native](https://turbo.hotwired.dev/handbook/native). This integration scrapes the owner dashboard to retrieve your data.

- **Polling interval**: configurable, default 60 minutes (range: 15–1440 minutes)
- **Resilient fetching**: on failure, retries every 2 minutes while keeping previous data (up to 3 consecutive failures)
- **Authentication**: lazy login — only authenticates when session cookies expire
- **Data sources**: dashboard bookings, booking details, availability calendar, rates, public listing page

## Supported languages

The integration UI is translated into all Goboony market languages:

| Language | Status |
|----------|--------|
| English | Fully translated |
| Nederlands | Fully translated |
| Deutsch | Fully translated |
| Fran&ccedil;ais | Fully translated |
| Italiano | Fully translated |

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Integration not loading | Clear browser cache and restart HA |
| Authentication failed | Check credentials, re-authenticate via **Settings > Integrations** |
| No bookings shown | Verify your listing ID is correct |
| Card not appearing | Make sure the integration is loaded, then search for "Goboony Bookings" when adding a card |
| Accepted bookings not showing | Make sure "Accepted" is checked in card settings, and clear browser cache |
| Sensors showing "unknown" | Wait for the first data fetch (up to 60 min) or press the Refresh button |

## Disclaimer

This integration is **not affiliated with or endorsed by Goboony**. It relies on web scraping, which means it may break if Goboony changes their website. Use at your own risk.

## License

[MIT License](LICENSE) — see LICENSE file for details.
