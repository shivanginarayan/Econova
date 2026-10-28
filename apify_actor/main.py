"""Private limited-permission Actor for fixed SF public sources."""
import json
import os
import re
from datetime import datetime, timezone
from html.parser import HTMLParser
from urllib.request import Request, urlopen
from urllib.robotparser import RobotFileParser
from urllib.parse import urlsplit

MENU_URL = "https://www.cafeseventy8.com/"
WAGE_URL = "https://www.sf.gov/information/understanding-minimum-wage-ordinance"
USER_AGENT = "EconomyGodModePublicData/1.0"


class Text(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts, self.hidden = [], 0

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style", "noscript"):
            self.hidden += 1
        if tag in ("br", "p", "div", "h1", "h2", "h3") and not self.hidden:
            self.parts.append("\n")

    def handle_endtag(self, tag):
        if tag in ("script", "style", "noscript"):
            self.hidden = max(0, self.hidden - 1)
        if tag in ("p", "div", "h1", "h2", "h3") and not self.hidden:
            self.parts.append("\n")

    def handle_data(self, value):
        if not self.hidden:
            self.parts.append(value)


def parse(html, category, observed_at=None):
    if category not in ("prices", "wages"):
        raise ValueError("Choose prices or wages")
    parser = Text()
    parser.feed(html)
    text = "".join(parser.parts).replace("\xa0", " ")
    observed_at = observed_at or datetime.now(timezone.utc).isoformat()
    if category == "wages":
        match = re.search(r"minimum wage,\s*currently\s*\$(\d+\.\d{2})\s+as of\s+([A-Za-z]+\s+\d{1,2},\s+\d{4})", text, re.I)
        if not match:
            raise ValueError("Current official wage and effective date not found")
        effective = datetime.strptime(match[2], "%B %d, %Y").date()
        if effective > datetime.now(timezone.utc).date():
            raise ValueError("Wage rate is not yet effective")
        return [{"item": "San Francisco general minimum wage", "value": float(match[1]), "unit": "usd_hour",
                 "kind": "statutory_wage_floor_not_average_pay", "effective_date": effective.isoformat(),
                 "source_url": WAGE_URL, "observed_at": observed_at}]
    names = ["HOUSE COFFEE", "CAFÉ AU LAIT", "HOT CHOCOLATE", "MEXICAN HOT CHOCOLATE", "CHAI LATTE",
             "DIRTY CHAI", "MATCHA LATTE", "MIGHTY LEAF TEA", "ESPRESSO", "CAPPUCCINO", "LATTE",
             "MOCHA", "WHITE MOCHA", "AMERICANO", "DEPTH CHARGE"]
    rows = []
    for item in names:
        match = re.search(r"(?:^|\n)\s*" + re.escape(item) + r"\s+(\d+\.\d{2})(?:\s*&\s*(\d+\.\d{2}))?", text, re.I)
        if not match:
            continue
        for index, amount in enumerate(filter(None, match.groups())):
            rows.append({"item": item, "value": float(amount), "unit": "usd_item",
                         "variant": f"listed option {index + 1} (size unspecified)",
                         "venue": "Cafe Seventy8, 78 29th Street, San Francisco",
                         "kind": "listed_menu_price_before_unspecified_tax_or_surcharges",
                         "source_url": MENU_URL, "observed_at": observed_at})
    if len(rows) < 10:
        raise ValueError("Menu structure changed; too few exact prices")
    return rows


def fetch_public(url):
    parts = urlsplit(url)
    robots = RobotFileParser()
    with urlopen(Request(f"{parts.scheme}://{parts.netloc}/robots.txt", headers={"User-Agent": USER_AGENT}), timeout=20) as response:
        robots.parse(response.read(200000).decode("utf-8", errors="replace").splitlines())
    if not robots.can_fetch(USER_AGENT, url):
        raise ValueError("Source robots.txt does not permit collection")
    with urlopen(Request(url, headers={"User-Agent": USER_AGENT}), timeout=35) as response:
        if urlsplit(response.url).hostname not in ("www.cafeseventy8.com", "www.sf.gov", "sf.gov"):
            raise ValueError("Unexpected source redirect")
        return response.read(5000000).decode("utf-8", errors="replace")


def main():
    token = os.environ["APIFY_TOKEN"]
    store, dataset = os.environ["APIFY_DEFAULT_KEY_VALUE_STORE_ID"], os.environ["APIFY_DEFAULT_DATASET_ID"]
    if not all(re.fullmatch(r"[A-Za-z0-9]{1,128}", value) for value in (store, dataset)):
        raise ValueError("Invalid platform storage ID")
    headers = {"Authorization": "Bearer " + token, "Content-Type": "application/json"}
    with urlopen(Request(f"https://api.apify.com/v2/key-value-stores/{store}/records/INPUT", headers=headers), timeout=20) as response:
        category = json.load(response).get("category")
    if category not in ("prices", "wages"):
        raise ValueError("Choose prices or wages; arbitrary source URLs are not accepted")
    rows = parse(fetch_public(MENU_URL if category == "prices" else WAGE_URL), category)
    with urlopen(Request(f"https://api.apify.com/v2/datasets/{dataset}/items", data=json.dumps(rows).encode(), headers=headers, method="POST"), timeout=20) as response:
        response.read()
    print(f"Collected {len(rows)} {category} observations from the configured public source.")


if __name__ == "__main__":
    main()
