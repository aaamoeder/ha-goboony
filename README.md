<p align="center">
  <img src="images/banner.png" alt="Goboony for Home Assistant" width="800">
</p>

<p align="center">
  <a href="https://github.com/hacs/integration"><img src="https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge" alt="HACS Custom"></a>
  <a href="https://github.com/aaamoeder/ha-goboony/releases"><img src="https://img.shields.io/github/release/aaamoeder/ha-goboony.svg?style=for-the-badge" alt="GitHub Release"></a>
  <a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge" alt="License: MIT"></a>
</p>

<p align="center">
  A custom Home Assistant integration for <a href="https://www.goboony.com">Goboony</a> camper/motorhome rental owners.<br>
  Track your bookings, earnings, availability and rates directly in your smart home.
</p>

---

## Features

| Feature | Description |
|---------|-------------|
| **Bookings overview** | Total, confirmed, pending and inquiry counts |
| **Next booking** | Upcoming booking details with countdown |
| **Earnings tracking** | Total confirmed earnings |
| **Rate monitoring** | Base and peak season rates |
| **Calendar availability** | Booked, blocked and available day counts |
| **Blocked periods** | Named blocked periods (holidays, maintenance, etc.) |
| **Calendar entity** | Native HA calendar with all bookings and blocked periods |
| **Custom card** | Beautiful bookings card with multi-status filtering |

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

## Sensors

| Sensor | Description | Unit |
|--------|-------------|------|
| Total bookings | Number of all bookings | — |
| Confirmed bookings | Number of confirmed bookings | — |
| Next booking | Dates of the next confirmed booking | — |
| Days until next booking | Countdown to next booking | days |
| Total earnings | Sum of confirmed booking earnings | EUR |
| Base rate | Low season daily rate | EUR |
| Peak rate | High season daily rate | EUR |
| Booked days | Days with confirmed bookings | days |
| Blocked days | Owner-blocked days | days |
| Available days | Available days on calendar | days |
| Blocked periods | Number of blocked periods | — |

## Custom Lovelace card

The integration includes a custom bookings card that is **automatically registered** — no manual resource setup needed.

### Adding the card

1. Edit your dashboard
2. Click **Add Card**
3. Search for **Goboony Bookings**
4. Configure via the visual editor

### Card options

| Option | Description | Default |
|--------|-------------|---------|
| **Entity** | The Goboony total bookings sensor | — |
| **Title** | Card header title | `Goboony Bookings` |
| **Show statuses** | Which booking statuses to display (multi-select) | All enabled |
| **Show earnings** | Show earnings per booking | `true` |
| **Show number of days** | Show rental duration | `true` |

### YAML example

```yaml
type: custom:goboony-bookings-card
entity: sensor.goboony_68972_total_bookings
title: My Camper Bookings
show_statuses:
  - confirmed
  - accepted
  - request
show_earnings: true
show_days: true
```

## Calendar

The integration creates a native Home Assistant **calendar entity** showing:
- Confirmed bookings with renter name and dates
- Owner-blocked periods

This works with all calendar cards and automations in Home Assistant.

## How it works

Goboony does not provide a public API. Their mobile app uses server-rendered HTML via [Turbo Native](https://turbo.hotwired.dev/handbook/native). This integration scrapes the owner dashboard to retrieve your data.

- **Polling interval**: every 60 minutes
- **Authentication**: standard email/password login

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

## Disclaimer

This integration is **not affiliated with or endorsed by Goboony**. It relies on web scraping, which means it may break if Goboony changes their website. Use at your own risk.

## License

[MIT License](LICENSE) — see LICENSE file for details.
