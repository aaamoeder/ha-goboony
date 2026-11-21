# Wijzigingen

Alle noemenswaardige wijzigingen aan deze integratie. Versies van voor 2.0.0 staan in de [GitHub-releases](https://github.com/aaamoeder/ha-goboony/releases).

## 2.0.0 (2026-11-21)

### 💥 Brekende wijzigingen
- Goboony is in november 2026 verhuisd naar het platform van Yescapa. De oude loginpagina en het oude eigenaarsdashboard bestaan niet meer, dus 1.x kan niet meer inloggen. De integratie gebruikt nu de JSON-API van de nieuwe website.
- Boekingen van de oude Goboony-site zijn niet meeverhuisd. Het aantal boekingen en de inkomsten beginnen opnieuw bij de boekingen op het nieuwe platform.
- Boekingen hebben nu de status `confirmed`, `awaiting_payment` of `request`. De statussen `accepted`, `inquiry`, `message` en `modified` bestaan niet meer.
- Attributen van de sensor Basistarief: `shoulder_early_rate`, `shoulder_late_rate`, `cleaning_fee` en `max_km_per_week` zijn vervangen door `low_rate`, `seasons`, `deposit`, `weekly_discount` en `early_booker_discount`.
- Sensor Reviews: het attribuut `times_hired` is weg (wordt niet meer gepubliceerd).
- De sensor Totaal boekingen heeft het attribuut `inquiries` niet meer, maar wel `awaiting_payment`.

### ✨ Nieuw
- Een oud Goboony-advertentie-ID wordt automatisch omgezet naar het nieuwe camper-ID, zodat bestaande entiteiten en dashboards blijven werken.
- De kalender toont boekingen die enkel in de Goboony-kalender staan, zoals boekingen van de oude site.
- Attributen bij de sensor Basistarief voor alle seizoensprijzen, de prijs per extra kilometer, de waarborg en de kortingen.

### 🐛 Opgeloste fouten
- Boekingen in de kalender hebben hun echte check-in- en check-out-uur in de tijdzone van Home Assistant (voorheen waren het evenementen van een hele dag).
- Dagen tot volgende boeking en de check-in-aftelling gebruiken de tijdzone van Home Assistant.
- Geblokkeerde periodes staan met hun echte datums in de kalender.

### 🔧 Verbeteringen
- Geen HTML-scraping meer en geen afhankelijkheid van BeautifulSoup.
- Het toegangstoken wordt automatisch vernieuwd voor het verloopt.
- Bij het instellen wordt gecontroleerd of de advertentie bij je account hoort (nieuwe foutmelding "listing not found").

### 🌍 Vertalingen
- Nieuwe foutmelding en uitleg bij het advertentie-ID in het Engels, Nederlands, Duits, Frans en Italiaans.

### 🎨 Uiterlijk
- Boekingskaart: statussen "Confirmed", "Awaiting payment" en "Requests". Kaarten die met de oude filter "Accepted" bewaard zijn, tonen boekingen die op betaling wachten gewoon verder.

### 📝 Documentatie
- README bijgewerkt voor het nieuwe platform, met uitleg over de overstap. Nieuw: een Nederlandse README (`README.nl.md`).
