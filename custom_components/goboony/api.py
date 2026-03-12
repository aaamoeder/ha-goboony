"""API client for Goboony."""
from __future__ import annotations

import logging
import re
from datetime import datetime

import requests
from bs4 import BeautifulSoup

from .const import BASE_URL, URL_DASHBOARD_BOOKINGS, URL_SIGN_IN

_LOGGER = logging.getLogger(__name__)


class GoboonyApiError(Exception):
    """Base exception for API errors."""


class GoboonyAuthError(GoboonyApiError):
    """Authentication error."""


class GoboonyApi:
    """API client for Goboony (scraping-based)."""

    def __init__(self, email: str, password: str, listing_id: str) -> None:
        self.email = email
        self.password = password
        self.listing_id = listing_id
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:137.0) Gecko/20100101 Firefox/137.0",
        })

    def close(self) -> None:
        """Close the HTTP session."""
        self.session.close()

    def login(self) -> None:
        """Authenticate with Goboony via Devise."""
        # Get CSRF token
        resp = self.session.get(URL_SIGN_IN, timeout=30)
        if resp.status_code != 200:
            raise GoboonyApiError(f"Failed to load sign-in page: {resp.status_code}")

        soup = BeautifulSoup(resp.text, "html.parser")
        csrf_meta = soup.find("meta", attrs={"name": "csrf-token"})
        if not csrf_meta:
            raise GoboonyApiError("Could not find CSRF token")
        csrf_token = csrf_meta["content"]

        # Submit login form
        resp = self.session.post(
            URL_SIGN_IN,
            data={
                "user[email]": self.email,
                "user[password]": self.password,
                "authenticity_token": csrf_token,
                "commit": "Sign in",
            },
            timeout=30,
            allow_redirects=True,
        )

        # Check if login succeeded (should redirect to dashboard)
        if "sign_in" in resp.url or resp.status_code != 200:
            raise GoboonyAuthError("Invalid credentials")

        _LOGGER.debug("Successfully authenticated with Goboony")

    def _get_page(self, url: str) -> BeautifulSoup:
        """Fetch a page and return parsed HTML."""
        resp = self.session.get(url, timeout=30)
        if resp.status_code == 401 or "sign_in" in resp.url:
            # Re-authenticate
            self.login()
            resp = self.session.get(url, timeout=30)
        if resp.status_code != 200:
            raise GoboonyApiError(f"Failed to load {url}: {resp.status_code}")
        return BeautifulSoup(resp.text, "html.parser")

    def _parse_eur(self, text: str) -> float | None:
        """Parse EUR value from text like 'EUR 392.40' or '€ 392,40'."""
        if not text:
            return None
        text = text.strip()
        # Remove currency symbols/text
        text = re.sub(r"[€EUR\s]", "", text)
        # Detect European format: 1.234,56 (dot as thousands, comma as decimal)
        if re.match(r"^\d{1,3}(\.\d{3})*(,\d+)?$", text):
            text = text.replace(".", "").replace(",", ".")
        else:
            # English format: 1,234.56 (comma as thousands, dot as decimal)
            text = text.replace(",", "")
        try:
            return float(text)
        except (ValueError, TypeError):
            return None

    def _parse_date(self, text: str) -> str | None:
        """Parse date from text like 'Mon 27 Apr 2:00 PM'."""
        if not text:
            return None
        # Try common formats
        text = text.strip()
        for fmt in [
            "%a %d %b %I:%M %p",
            "%a %d %b %Y %I:%M %p",
            "%d %b %Y",
            "%b %d, %Y",
        ]:
            try:
                dt = datetime.strptime(text, fmt)
                if dt.year < 2000:
                    dt = dt.replace(year=datetime.now().year)
                return dt.isoformat()
            except ValueError:
                continue
        return text

    def get_bookings(self) -> list[dict]:
        """Get all bookings from dashboard."""
        soup = self._get_page(URL_DASHBOARD_BOOKINGS)
        bookings = []

        rows = soup.select("tr[data-clickable-destination-value]")
        for row in rows:
            cols = row.find_all("td")
            if len(cols) < 7:
                continue

            href = row.get("data-clickable-destination-value", "")
            booking_id = href.split("/")[-1] if href else ""

            # Extract status
            status_cell = cols[1]
            status_span = status_cell.find("span")
            status = status_span.get_text(strip=True) if status_span else ""

            # Extract booking number
            booking_num = cols[2].get_text(strip=True)

            # Extract renter
            renter = cols[3].get_text(strip=True)

            # Extract dates
            dates = cols[4].get_text(strip=True)

            # Extract earnings (data-value in cents)
            earn_cell = cols[6]
            earn_value = earn_cell.get("data-value")
            earnings = float(earn_value) / 100 if earn_value else None

            bookings.append({
                "booking_id": booking_id,
                "booking_number": booking_num,
                "status": status.lower().replace(" ", "_"),
                "renter": renter,
                "dates": dates,
                "earnings": earnings,
                "url": f"{BASE_URL}{href}" if href else "",
            })

        return bookings

    def get_booking_detail(self, booking_id: str) -> dict:
        """Get detailed booking info."""
        url = f"{BASE_URL}/dashboard/bookings/{booking_id}"
        soup = self._get_page(url)
        detail = {"booking_id": booking_id}

        # Extract dates from table.dates
        dates_table = soup.find("table", class_="dates")
        if dates_table:
            rows = dates_table.find_all("tr")
            for row in rows:
                th = row.find("th")
                td = row.find("td")
                if th and td:
                    label = th.get_text(strip=True).lower()
                    value = td.get_text(strip=True)
                    if "from" in label or "van" in label:
                        detail["check_in"] = value
                    elif "to" in label or "tot" in label:
                        detail["check_out"] = value

        # Extract terms from table.terms
        terms_table = soup.find("table", class_="terms")
        if terms_table:
            rows = terms_table.find_all("tr")
            for row in rows:
                th = row.find("th")
                td = row.find("td")
                if th and td:
                    label = th.get_text(strip=True).lower()
                    value = td.get_text(strip=True)
                    if "days" in label or "dagen" in label:
                        try:
                            detail["num_days"] = int(re.search(r"\d+", value).group())
                        except (AttributeError, ValueError):
                            _LOGGER.debug("Failed to parse num_days from: %s", value)
                    elif "insurance" in label or "verzekering" in label:
                        detail["insurance_per_day"] = value
                    elif "mileage" in label or "kilometer" in label:
                        detail["mileage_limit"] = value
                    elif "extra km" in label:
                        detail["price_per_extra_km"] = value
                    elif "cancellation" in label or "annulering" in label:
                        detail["cancellation_policy"] = value
                    elif "deductible" in label or "eigen risico" in label:
                        detail["deductible"] = value

        # Extract rates from table.rates
        rates_table = soup.find("table", class_="rates")
        if rates_table:
            rows = rates_table.find_all("tr")
            for row in rows:
                th = row.find("th")
                td = row.find("td")
                if th and td:
                    label = th.get_text(strip=True).lower()
                    value = td.get_text(strip=True)
                    if "you earn" in label or "jij verdient" in label:
                        detail["owner_earnings"] = self._parse_eur(value)
                    elif "rental" in label or "huur" in label:
                        detail["rental_fee"] = self._parse_eur(value)

        # Extract total (traveller pays)
        total_table = soup.find("table", class_="total")
        if total_table:
            td = total_table.find("td")
            if td:
                detail["traveller_total"] = self._parse_eur(td.get_text(strip=True))

        # Extract booking state
        state_el = soup.find(attrs={"data-booking-state": True})
        if state_el:
            detail["state"] = state_el.get("data-booking-state")

        return detail

    def get_availability(self) -> dict:
        """Get calendar availability for the listing."""
        url = f"{BASE_URL}/dashboard/listings/{self.listing_id}/availability/edit"
        soup = self._get_page(url)

        result = {
            "booked_dates": [],
            "blocked_dates": [],
            "available_dates": [],
            "blocked_periods": [],
            "bookings_on_calendar": [],
        }

        # Parse calendar cells
        cells = soup.find_all("td", attrs={"data-date": True})
        current_booking_start = None
        current_block_start = None
        current_block_name = None

        for cell in cells:
            date_str = cell.get("data-date", "")
            classes = cell.get("class", [])

            if "has_booking" in classes:
                result["booked_dates"].append(date_str)
                if "start_of_booking" in classes:
                    current_booking_start = date_str
                if "end_of_booking" in classes and current_booking_start:
                    result["bookings_on_calendar"].append({
                        "start": current_booking_start,
                        "end": date_str,
                    })
                    current_booking_start = None
            elif "has_blocked_period" in classes:
                result["blocked_dates"].append(date_str)
            elif "available" in classes:
                result["available_dates"].append(date_str)

        # Extract blocked periods with names
        blocked_links = soup.find_all("a", href=re.compile(r"/blocked_periods/\d+"))
        for link in blocked_links:
            period_id = re.search(r"/blocked_periods/(\d+)", link["href"])
            if period_id:
                result["blocked_periods"].append({
                    "id": period_id.group(1),
                    "name": link.get_text(strip=True),
                    "url": link["href"],
                })

        # Extract pickup/return settings
        pickup_select = soup.find("select", attrs={"name": re.compile(r"pickup_time|check_in_time")})
        if pickup_select:
            selected = pickup_select.find("option", selected=True)
            if selected:
                result["pickup_time"] = selected.get_text(strip=True)

        return_select = soup.find("select", attrs={"name": re.compile(r"return_time|check_out_time")})
        if return_select:
            selected = return_select.find("option", selected=True)
            if selected:
                result["return_time"] = selected.get_text(strip=True)

        return result

    def get_rates(self) -> dict:
        """Get pricing/rates for the listing."""
        url = f"{BASE_URL}/dashboard/listings/{self.listing_id}/rates/edit"
        soup = self._get_page(url)

        rates = {}
        fields = {
            "peak_season_rate": "peak_rate",
            "shoulder_season_early_rate": "shoulder_early_rate",
            "shoulder_season_late_rate": "shoulder_late_rate",
            "base_rate": "base_rate",
            "cleaning_fee": "cleaning_fee",
            "price_per_extra_km": "price_per_extra_km",
            "max_number_of_km": "max_km_per_week",
        }

        for field_name, key in fields.items():
            inp = soup.find("input", attrs={"name": re.compile(field_name)})
            if inp:
                val = inp.get("value", "")
                try:
                    rates[key] = float(val) if val else 0
                except ValueError:
                    rates[key] = val

        # Extract discount checkboxes and values
        discounts = {}
        for inp in soup.find_all("input", attrs={"type": "checkbox", "name": re.compile(r"discount")}):
            name = inp.get("name", "")
            checked = inp.has_attr("checked")
            # Find associated value input
            val_inp = soup.find("input", attrs={"name": name.replace("[active]", "[percentage]")})
            if val_inp:
                try:
                    discounts[name] = {
                        "active": checked,
                        "percentage": float(val_inp.get("value", 0)),
                    }
                except ValueError:
                    pass

        if discounts:
            rates["discounts"] = discounts

        return rates

    def get_listing_info(self) -> dict:
        """Get public listing information."""
        # First load /listings/ID to get the canonical (public) URL
        url = f"{BASE_URL}/listings/{self.listing_id}"
        soup = self._get_page(url)

        info = {"listing_id": self.listing_id}

        # Check for canonical URL and re-fetch if different
        canonical = soup.find("link", rel="canonical")
        if canonical and canonical.get("href") and canonical["href"] != url:
            canonical_url = canonical["href"]
            info["url"] = canonical_url
            soup = self._get_page(canonical_url)

        # Title
        title = soup.find("h1")
        if title:
            info["title"] = title.get_text(strip=True)

        # Category and location from script data
        for script in soup.find_all("script"):
            text = script.string or ""
            if "listing_id" in text:
                match = re.search(r'"listing_category"\s*:\s*"([^"]*)"', text)
                if match:
                    info["category"] = match.group(1)
                match = re.search(r'"listing_location"\s*:\s*"([^"]*)"', text)
                if match:
                    info["location"] = match.group(1)

        # Rating and review count from "X/5 based on Y reviews" text
        rating_text = soup.find(string=re.compile(r"\d+(\.\d+)?/5\s+based\s+on\s+\d+\s+reviews?"))
        if rating_text:
            match = re.search(r"(\d+(?:\.\d+)?)/5\s+based\s+on\s+(\d+)\s+reviews?", rating_text)
            if match:
                info["rating"] = float(match.group(1))
                info["review_count"] = int(match.group(2))

        # Fallback for review count from "X Reviews" text
        if "review_count" not in info:
            review_el = soup.find(string=re.compile(r"\d+\s+[Rr]eviews?"))
            if review_el:
                match = re.search(r"(\d+)", review_el)
                if match:
                    info["review_count"] = int(match.group(1))

        # Times hired
        hired_text = soup.find(string=re.compile(r"(\d+)\s+times?\s+hired"))
        if hired_text:
            match = re.search(r"(\d+)", hired_text)
            if match:
                info["times_hired"] = int(match.group(1))

        # First listing photo
        og_image = soup.find("meta", property="og:image")
        if og_image and og_image.get("content"):
            info["photo_url"] = og_image["content"]
        else:
            img = soup.find("img", class_=re.compile(r"listing|camper|hero|gallery"))
            if img and img.get("src"):
                info["photo_url"] = img["src"]

        return info

    def get_all_data(self) -> dict:
        """Get all data for the listing."""
        self.login()

        result = {
            "bookings": [],
            "availability": {},
            "rates": {},
            "listing": {},
        }

        # Get bookings list
        try:
            result["bookings"] = self.get_bookings()
            _LOGGER.debug("Found %d bookings", len(result["bookings"]))
        except Exception as err:
            _LOGGER.warning("Failed to get bookings: %s", err)

        # Get booking details for all bookings
        for booking in result["bookings"]:
            try:
                detail = self.get_booking_detail(booking["booking_id"])
                booking.update(detail)
            except Exception as err:
                _LOGGER.debug("Failed to get booking detail %s: %s", booking["booking_id"], err)

        # Get availability
        try:
            result["availability"] = self.get_availability()
        except Exception as err:
            _LOGGER.warning("Failed to get availability: %s", err)

        # Get rates
        try:
            result["rates"] = self.get_rates()
        except Exception as err:
            _LOGGER.warning("Failed to get rates: %s", err)

        # Get listing info
        try:
            result["listing"] = self.get_listing_info()
        except Exception as err:
            _LOGGER.debug("Failed to get listing info: %s", err)

        return result
