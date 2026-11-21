"""Constants for the Goboony integration."""

DOMAIN = "goboony"

CONF_EMAIL = "email"
CONF_PASSWORD = "password"
CONF_LISTING_ID = "listing_id"

BASE_URL = "https://www.goboony.com"

# Goboony runs on the Yescapa platform. The website calls this API with a
# public client key that is embedded in every page of www.goboony.com.
API_URL = "https://api.jelouemoncampingcar.com"
API_KEY = "1wKbRQSSKtQUYz4UsICsE0d3bh6ghjzNE7pOgP2l"

CONF_SCAN_INTERVAL = "scan_interval"
DEFAULT_SCAN_INTERVAL = 3600  # 1 hour in seconds

# Booking statuses used by the sensors, calendar and card
STATUS_CONFIRMED = "confirmed"
STATUS_AWAITING_PAYMENT = "awaiting_payment"
STATUS_REQUEST = "request"
