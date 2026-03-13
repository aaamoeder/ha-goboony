<p align="center">
  <img src="https://raw.githubusercontent.com/aaamoeder/ha-goboony/main/images/banner.png" alt="Goboony for Home Assistant" width="800">
</p>

<p align="center">
  <a href="https://github.com/hacs/integration"><img src="https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge" alt="HACS Custom"></a>
  <a href="https://github.com/aaamoeder/ha-goboony/releases"><img src="https://img.shields.io/github/release/aaamoeder/ha-goboony.svg?style=for-the-badge" alt="GitHub Release"></a>
  <a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge" alt="License: MIT"></a>
</p>

<p align="center">
  A custom Home Assistant integration for <a href="https://www.goboony.com">Goboony</a> camper/motorhome rental owners.<br>
  Track your bookings, earnings, availability, rates and reviews directly in your smart home.
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

| Field | Description |
|-------|-------------|
| **Email** | Your Goboony owner account email |
| **Password** | Your Goboony password |
| **Listing ID** | Found in the URL of your listing page (e.g. `goboony.com/listings/12345`) |

> The integration supports **re-authentication** — if your session expires, Home Assistant will prompt you to re-enter your credentials.

### Options

After setup, go to **Settings** > **Devices & Services** > **Goboony** > **Configure** to change:

| Option | Description | Default |
|--------|-------------|---------|
| **Update interval** | How often to fetch data from Goboony (minutes) | 60 |

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

| Option | Description | Default |
|--------|-------------|---------|
| **Bookings entity** | The Goboony total bookings sensor | — |
| **Reviews entity** | The Goboony reviews sensor (optional) | — |

#### Header

| Option | Description | Default |
|--------|-------------|---------|
| **Card title** | Custom title text | `Goboony Bookings` |
| **Show camper icon** | Show/hide the camper icon in the header | `true` |
| **Show total earnings** | Show/hide total earnings in the header | `true` |
| **Show review rating** | Show/hide the star rating badge | `true` |

#### Active rental

| Option | Description | Default |
|--------|-------------|---------|
| **Show active rental banner** | Show/hide the active rental section | `true` |
| **Show progress bar** | Show/hide the rental progress bar | `true` |

#### Bookings

| Option | Description | Default |
|--------|-------------|---------|
| **Show earnings per booking** | Show/hide earnings on each booking | `true` |
| **Show number of days** | Show/hide rental duration | `true` |
| **Show booking number** | Show/hide the booking reference (#12345) | `true` |
| **Show check-out date** | Show/hide the check-out date | `true` |
| **Show relative date** | Show/hide relative date badges (e.g. "in 3d") | `true` |
| **Show gap indicators** | Show/hide gap days and changeover indicators | `true` |
| **Max bookings** | Limit the number of bookings shown (0 = all) | `0` |
| **Compact mode** | Use a compact single-line layout | `false` |

#### Filters

| Option | Description | Default |
|--------|-------------|---------|
| **Show statuses** | Which booking statuses to display (multi-select) | All enabled |

#### Appearance

| Option | Description | Default |
|--------|-------------|---------|
| **Show section headers** | Show/hide section labels (Confirmed, Requests, etc.) | `true` |
| **Show last updated** | Show/hide the "Updated X min ago" footer | `true` |

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
