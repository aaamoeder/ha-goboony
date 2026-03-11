"""Constants for the Goboony integration."""

DOMAIN = "goboony"

CONF_EMAIL = "email"
CONF_PASSWORD = "password"
CONF_LISTING_ID = "listing_id"

BASE_URL = "https://www.goboony.com"
URL_SIGN_IN = f"{BASE_URL}/users/sign_in"
URL_DASHBOARD_BOOKINGS = f"{BASE_URL}/dashboard/bookings"

DEFAULT_SCAN_INTERVAL = 3600  # 1 hour in seconds
