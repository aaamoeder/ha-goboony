"""API client for Goboony.

Goboony runs on the Yescapa platform. The website talks to a JSON API with
OAuth bearer tokens; this client uses the same endpoints.
"""
from __future__ import annotations

import logging
import re
import time
from datetime import date, timedelta

import requests

from .const import (
    API_KEY,
    API_URL,
    BASE_URL,
    STATUS_AWAITING_PAYMENT,
    STATUS_CONFIRMED,
    STATUS_REQUEST,
)

_LOGGER = logging.getLogger(__name__)

# Days ahead covered by the availability sensors
AVAILABILITY_WINDOW_DAYS = 365

# Renew the access token this many seconds before it expires
TOKEN_MARGIN = 300

MONTHS = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]
WEEKDAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

# Platform booking state -> status used by the sensors, calendar and card
STATE_STATUS = {
    "VALIDATED": STATUS_REQUEST,
    "ACCEPTED": STATUS_AWAITING_PAYMENT,
    "TO_COME_NOT_PAID": STATUS_AWAITING_PAYMENT,
    "TO_COME": STATUS_CONFIRMED,
    "ONGOING": STATUS_CONFIRMED,
    "FINISHED": STATUS_CONFIRMED,
    "DONE": STATUS_CONFIRMED,
}

# States that are not (or no longer) a booking
IGNORED_STATES = {
    "ACCEPTED_EXP",
    "CANCELLED_BOTH",
    "CANCELLED_GUEST",
    "CANCELLED_OWNER",
    "CANCELLED_STAFF",
}

# Calendar block that holds a booking imported from the old Goboony site
REASON_GOBOONY_BOOKING = "GOBOONY_BOOKING"


class GoboonyApiError(Exception):
    """Base exception for API errors."""


class GoboonyAuthError(GoboonyApiError):
    """Authentication error."""


class GoboonyListingNotFound(GoboonyApiError):
    """The configured listing is not one of the account's campers."""


def _format_check(day: date, time_text: str) -> str:
    """Format a check-in/out moment like 'Sat 3 Oct 2026 – 2:00 PM'."""
    hour, _, minute = time_text.partition(":")
    hour_i = int(hour)
    minute_i = int(minute or 0)
    suffix = "AM" if hour_i < 12 else "PM"
    hour_12 = hour_i % 12 or 12
    return (
        f"{WEEKDAYS[day.weekday()]} {day.day} {MONTHS[day.month - 1][:3]} {day.year}"
        f" – {hour_12}:{minute_i:02d} {suffix}"
    )


def _format_range(start: date, end: date) -> str:
    """Format a date range like 'October 03 - October 11, 2026'."""
    start_text = f"{MONTHS[start.month - 1]} {start.day:02d}"
    if start.year != end.year:
        start_text += f", {start.year}"
    return f"{start_text} - {MONTHS[end.month - 1]} {end.day:02d}, {end.year}"


def _to_float(value) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _days(start: date, end: date) -> list[date]:
    """Return every day from start to end, both included."""
    return [start + timedelta(days=i) for i in range((end - start).days + 1)]


class GoboonyApi:
    """API client for Goboony."""

    def __init__(self, email: str, password: str, listing_id: str) -> None:
        self.email = email
        self.password = password
        self.listing_id = str(listing_id).strip()
        self.product_id: int | None = None
        self._access_token: str | None = None
        self._token_expires = 0.0
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:137.0) Gecko/20100101 Firefox/137.0",
            "X-API-KEY": API_KEY,
            "Accept": "application/json",
            "Accept-Language": "en",
            "Origin": BASE_URL,
            "Referer": f"{BASE_URL}/",
        })

    def close(self) -> None:
        """Close the HTTP session."""
        self.session.close()

    def clear_session(self) -> None:
        """Forget the access token so the next call logs in again."""
        self._access_token = None
        self._token_expires = 0.0
        self.session.headers.pop("Authorization", None)

    def login(self) -> None:
        """Log in with email and password and keep the access token."""
        try:
            resp = self.session.post(
                f"{API_URL}/v4/users/auth/login/",
                json={
                    "username": self.email,
                    "password": self.password,
                    "client_id": API_KEY,
                    "grant_type": "password",
                },
                timeout=30,
            )
        except requests.RequestException as err:
            raise GoboonyApiError(f"Connection error during login: {err}") from err

        if resp.status_code in (400, 401):
            raise GoboonyAuthError("Invalid credentials")
        if resp.status_code != 200:
            raise GoboonyApiError(f"Login failed: HTTP {resp.status_code}")
        try:
            token = resp.json()
            self._access_token = token["access_token"]
            expires_in = int(token.get("expires_in", 3600))
        except (ValueError, KeyError, TypeError) as err:
            raise GoboonyApiError("Unexpected login response") from err

        self._token_expires = time.monotonic() + expires_in - TOKEN_MARGIN
        self.session.headers["Authorization"] = f"Bearer {self._access_token}"
        _LOGGER.debug("Successfully authenticated with Goboony")

    def _ensure_logged_in(self) -> None:
        if not self._access_token or time.monotonic() >= self._token_expires:
            self.login()

    def _get(self, path: str, params: dict | None = None):
        """GET an API path and return the decoded JSON."""
        self._ensure_logged_in()
        url = f"{API_URL}{path}"
        try:
            resp = self.session.get(url, params=params, timeout=30)
            if resp.status_code == 401:
                _LOGGER.debug("Access token rejected, logging in again")
                self.clear_session()
                self.login()
                resp = self.session.get(url, params=params, timeout=30)
        except requests.RequestException as err:
            raise GoboonyApiError(f"Connection error for {path}: {err}") from err

        if resp.status_code == 401:
            raise GoboonyAuthError("Access token rejected")
        if resp.status_code != 200:
            raise GoboonyApiError(f"Failed to load {path}: HTTP {resp.status_code}")
        try:
            return resp.json()
        except ValueError as err:
            raise GoboonyApiError(f"Invalid JSON from {path}") from err

    def _get_products(self) -> list[dict]:
        return self._get("/3/products/me/paginated/").get("results", [])

    def _legacy_product_id(self) -> int | None:
        """Map an old Goboony listing ID to the new camper ID via the site redirect."""
        try:
            resp = self.session.head(
                f"{BASE_URL}/listings/{self.listing_id}", allow_redirects=False, timeout=30
            )
        except requests.RequestException:
            return None
        match = re.search(r"/(?:camper/ysc|campers)/(\d+)", resp.headers.get("Location", ""))
        return int(match.group(1)) if match else None

    def resolve_product(self, products: list[dict] | None = None) -> dict:
        """Return the camper that belongs to the configured listing ID.

        The listing ID may be the new camper ID or the ID of the old Goboony
        site, which the site still redirects to the new camper page.
        """
        if products is None:
            products = self._get_products()
        by_id = {p.get("id"): p for p in products}

        if self.product_id in by_id:
            return by_id[self.product_id]

        candidates = []
        if self.listing_id.isdigit():
            candidates.append(int(self.listing_id))
        legacy = self._legacy_product_id()
        if legacy:
            candidates.append(legacy)
        for candidate in candidates:
            if candidate in by_id:
                self.product_id = candidate
                _LOGGER.debug("Listing %s is camper %s", self.listing_id, candidate)
                return by_id[candidate]

        raise GoboonyListingNotFound(
            f"Listing {self.listing_id} is not one of the campers on this account"
        )

    def validate(self) -> None:
        """Log in and check that the listing belongs to the account."""
        self.login()
        self.resolve_product()

    def get_bookings(self) -> list[dict]:
        """Return the owner's bookings for this camper."""
        bookings = []
        page = 1
        while True:
            data = self._get("/v4/bookings-owner/", {"page": page, "page_size": 50})
            for item in data.get("results", []):
                if item.get("camper", {}).get("id") not in (None, self.product_id):
                    continue
                booking = self._map_booking(item)
                if booking:
                    bookings.append(booking)
            if not data.get("next"):
                break
            page += 1
        return bookings

    def _map_booking(self, item: dict) -> dict | None:
        state = item.get("state", "")
        if state in IGNORED_STATES:
            return None
        status = STATE_STATUS.get(state)
        if status is None:
            _LOGGER.debug("Unknown booking state %s", state)
            status = state.lower()

        try:
            start = date.fromisoformat(item["date_from"][:10])
            end = date.fromisoformat(item["date_to"][:10])
        except (KeyError, TypeError, ValueError):
            return None

        pickup = (item.get("pickup") or {}).get("time") or f"{item.get('hour_from', 14)}:00"
        dropoff = (item.get("dropoff") or {}).get("time") or f"{item.get('hour_to', 12)}:00"
        guest = item.get("guest") or {}
        renter = " ".join(
            part for part in (guest.get("first_name"), guest.get("last_name")) if part
        )
        booking_id = str(item.get("id", ""))

        return {
            "booking_id": booking_id,
            "booking_number": booking_id,
            "status": status,
            "state": state,
            "renter": renter,
            "dates": _format_range(start, end),
            "check_in": _format_check(start, pickup),
            "check_out": _format_check(end, dropoff),
            "num_days": (end - start).days + 1,
            "earnings": _to_float(item.get("total_earnings")),
            "url": f"{BASE_URL}/d/bookings/{booking_id}",
            "start": start.isoformat(),
            "end": end.isoformat(),
            "check_in_time": pickup,
            "check_out_time": dropoff,
        }

    def get_availability(self, bookings: list[dict]) -> dict:
        """Return booked, blocked and available days for the coming year."""
        periods = self._get(f"/3/products/{self.product_id}/calendar/periods/")
        today = date.today()
        window_end = today + timedelta(days=AVAILABILITY_WINDOW_DAYS - 1)

        booked: set[date] = set()
        blocked: set[date] = set()
        blocked_periods = []
        bookings_on_calendar = []
        external_bookings = []
        known = {(b["start"], b["end"]) for b in bookings if b.get("status") == STATUS_CONFIRMED}

        for b in bookings:
            if b.get("status") != STATUS_CONFIRMED:
                continue
            start, end = date.fromisoformat(b["start"]), date.fromisoformat(b["end"])
            booked.update(_days(start, end))
            bookings_on_calendar.append({"start": b["start"], "end": b["end"]})

        for period in periods:
            if period.get("available") or period.get("is_archived"):
                continue
            try:
                start = date.fromisoformat(period["date_from"][:10])
                end = date.fromisoformat(period["date_to"][:10])
            except (KeyError, TypeError, ValueError):
                continue
            days = _days(start, end)
            reason = period.get("non_available_reason")
            if period.get("booking_id") or reason == REASON_GOBOONY_BOOKING:
                booked.update(days)
                span = (start.isoformat(), end.isoformat())
                if span not in known:
                    # A booking that is only on the calendar, such as one from the old Goboony site
                    bookings_on_calendar.append({"start": span[0], "end": span[1]})
                    external_bookings.append({"start": span[0], "end": span[1]})
                continue
            blocked.update(days)
            if end >= today:
                blocked_periods.append({
                    "id": str(period.get("id", "")),
                    "name": (reason or "Blocked").replace("_", " ").capitalize(),
                    "start": start.isoformat(),
                    "end": end.isoformat(),
                })

        window = set(_days(today, window_end))
        booked_in = sorted(booked & window)
        blocked_in = sorted((blocked - booked) & window)
        available_in = sorted(window - booked - blocked)
        blocked_periods.sort(key=lambda p: p["start"])

        return {
            "booked_dates": [d.isoformat() for d in booked_in],
            "blocked_dates": [d.isoformat() for d in blocked_in],
            "available_dates": [d.isoformat() for d in available_in],
            "blocked_periods": blocked_periods,
            "bookings_on_calendar": sorted(bookings_on_calendar, key=lambda p: p["start"]),
            "external_bookings": sorted(external_bookings, key=lambda p: p["start"]),
        }

    def get_rates(self) -> dict:
        """Return the daily rates and mileage pricing of the camper."""
        prices = self._get(f"/3/products/{self.product_id}/calendar/prices/")
        details = self._get(f"/3/products/{self.product_id}/prices-details/")

        active = [p for p in prices if not p.get("is_archived")]
        default = next((p for p in active if p.get("is_default")), None)
        seasons = [p for p in active if not p.get("is_default")]

        def value(p):
            return _to_float(p.get("value")) if p else None

        season_values = [v for v in (value(p) for p in seasons) if v is not None]
        return {
            "base_rate": value(default),
            "peak_rate": max(season_values) if season_values else None,
            "low_rate": min(season_values) if season_values else None,
            "seasons": [
                {"name": p.get("name"), "rate": value(p), "guest_price": _to_float(p.get("guest_price"))}
                for p in active
            ],
            "price_per_extra_km": _to_float(details.get("km_more")),
            "deposit": _to_float(details.get("deposit")),
            "weekly_discount": _to_float(details.get("weekly_factor")),
            "early_booker_discount": _to_float(details.get("early_booker_rate")),
        }

    @staticmethod
    def _map_listing(product: dict) -> dict:
        pictures = sorted(product.get("picture_set") or [], key=lambda p: p.get("index", 0))
        rating = _to_float(product.get("review_average"))
        return {
            "listing_id": str(product.get("id", "")),
            "title": product.get("title"),
            "url": product.get("ad_url"),
            "category": product.get("vehicle_type"),
            "location": product.get("vehicle_location_city"),
            "rating": rating if product.get("review_count") else None,
            "review_count": product.get("review_count"),
            "state": product.get("state"),
            "published": product.get("published"),
            "photo_url": pictures[0].get("base") if pictures else None,
        }

    def get_all_data(self, previous_data: dict | None = None) -> dict:
        """Get all data for the listing.

        If previous_data is provided, failed sections keep their previous
        values instead of returning empty data.
        """
        prev = previous_data or {}
        result = {
            "bookings": prev.get("bookings", []),
            "availability": prev.get("availability", {}),
            "rates": prev.get("rates", {}),
            "listing": prev.get("listing", {}),
        }

        # Login problems and an unknown listing stop the update; they are not partial failures
        product = self.resolve_product()
        result["listing"] = self._map_listing(product)

        try:
            result["bookings"] = self.get_bookings()
            _LOGGER.debug("Found %d bookings", len(result["bookings"]))
        except GoboonyAuthError:
            raise
        except Exception as err:  # noqa: BLE001
            _LOGGER.warning("Failed to get bookings: %s; keeping previous data", err)

        try:
            result["availability"] = self.get_availability(result["bookings"])
        except GoboonyAuthError:
            raise
        except Exception as err:  # noqa: BLE001
            _LOGGER.warning("Failed to get availability: %s; keeping previous data", err)

        try:
            result["rates"] = self.get_rates()
        except GoboonyAuthError:
            raise
        except Exception as err:  # noqa: BLE001
            _LOGGER.warning("Failed to get rates: %s; keeping previous data", err)

        return result
