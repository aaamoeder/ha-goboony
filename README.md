# Goboony for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)
[![GitHub Release](https://img.shields.io/github/release/aaamoeder/ha-goboony.svg)](https://github.com/aaamoeder/ha-goboony/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A Home Assistant custom integration for [Goboony](https://www.goboony.com) camper/motorhome rental platform owners. Track your bookings, earnings, availability and rates directly in Home Assistant.

## Features

- **Bookings overview** - Total, confirmed, pending and inquiry counts
- **Next booking** - See your upcoming booking details and days countdown
- **Earnings tracking** - Total confirmed earnings
- **Rate monitoring** - Base and peak season rates with all rate details
- **Calendar availability** - Booked, blocked and available day counts
- **Blocked periods** - Named blocked periods (personal events, etc.)
- **Calendar entity** - Native HA calendar with all bookings and blocked periods
- **Custom Lovelace card** - Beautiful bookings overview card with status filters

## Installation

### HACS (Recommended)

1. Open HACS in your Home Assistant instance
2. Click the three dots in the top right corner
3. Select "Custom repositories"
4. Add `https://github.com/aaamoeder/ha-goboony` with category "Integration"
5. Click "Install"
6. Restart Home Assistant

### Manual

1. Copy the `custom_components/goboony` folder to your `config/custom_components/` directory
2. Restart Home Assistant

## Setup

1. Go to **Settings** > **Devices & Services** > **Add Integration**
2. Search for "Goboony"
3. Enter your Goboony owner account credentials:
   - **Email** - Your Goboony login email
   - **Password** - Your Goboony password
   - **Listing ID** - Your listing ID (found in the URL of your listing page, e.g. `goboony.com/listings/12345`)

## Sensors

| Sensor | Description | Unit |
|--------|-------------|------|
| Total bookings | Number of all bookings | count |
| Confirmed bookings | Number of confirmed bookings | count |
| Next booking | Dates of the next confirmed booking | - |
| Days until next booking | Countdown to next booking | days |
| Total earnings | Sum of confirmed booking earnings | EUR |
| Base rate | Low season daily rate | EUR |
| Peak rate | High season daily rate | EUR |
| Booked days | Days with confirmed bookings on calendar | days |
| Blocked days | Owner-blocked days on calendar | days |
| Available days | Available days on calendar | days |
| Blocked periods | Number of blocked periods | count |

## Custom Lovelace Card

The integration includes a custom bookings card that is automatically registered when the integration loads. No manual file copying or resource registration needed.

Add the card to your dashboard:

```yaml
type: custom:goboony-bookings-card
entity: sensor.goboony_LISTINGID_total_bookings
```

The card supports a visual editor with options for:
- Entity selection
- Custom title
- Default filter (All / Confirmed / Requests / Messages)
- Show/hide earnings, days count, and filter buttons

## How it works

This integration scrapes the Goboony owner dashboard. Goboony does not provide a public API - their mobile app also uses server-rendered HTML (Turbo Native). Data is refreshed every hour.

## Disclaimer

This integration is not affiliated with or endorsed by Goboony. It relies on web scraping, which means it may break if Goboony changes their website structure. Use at your own risk.

## License

MIT License - see [LICENSE](LICENSE) for details.
