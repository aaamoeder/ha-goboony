"""Constanten voor de Goboony-integratie."""

DOMAIN = "goboony"

CONF_EMAIL = "email"
CONF_PASSWORD = "password"
CONF_LISTING_ID = "listing_id"

BASE_URL = "https://www.goboony.com"

# Goboony draait op het platform van Yescapa. De website roept deze API aan met
# een publieke clientsleutel die in elke pagina van www.goboony.com staat.
API_URL = "https://api.jelouemoncampingcar.com"
API_KEY = "1wKbRQSSKtQUYz4UsICsE0d3bh6ghjzNE7pOgP2l"

CONF_SCAN_INTERVAL = "scan_interval"
DEFAULT_SCAN_INTERVAL = 3600  # 1 uur in seconden

# Boekingsstatussen voor de sensoren, de kalender en de kaart
STATUS_CONFIRMED = "confirmed"
STATUS_AWAITING_PAYMENT = "awaiting_payment"
STATUS_REQUEST = "request"
