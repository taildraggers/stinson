"""Scraper for Stinson listings on barnstormers.com.

Barnstormers' single-manufacturer category pages (the same pattern seen in
the companion Aviat, CubCrafters, de Havilland, Maule, Van's RV, RANS,
Luscombe, Just Aircraft, Kitfox, Bellanca, Stearman, Waco, Pitts,
Taylorcraft, Swift, Beechcraft, Air Tractor, and Fairchild repos) can mix
in off-brand or off-topic listings with no distinguishing HTML markup from
the genuine ones. So results are filtered by title against a small
allowlist of Stinson-specific terms before being published.

Stinson's model lineup spans several distinct families across decades: the
postwar Model 108 "Voyager"/"Station Wagon" (108, 108-1, 108-2, 108-3),
the prewar Model 10/10A Voyager, the SR "Reliant" series (SR-5 through
SR-10, later ones nicknamed "Gullwing"), and the military L-5 "Sentinel"
(L-5, L-5B, L-5C, L-5E, L-5G). Every one of the marketing names -
"Reliant", "Voyager", "Sentinel", "Station Wagon", "Gullwing" - is an
ordinary English word/phrase with real collision risk (a Plymouth
Reliant, a Winnebago/Plymouth Voyager, a police sentinel, etc.), so unlike
Waco's or RANS's coined model names, every match here - names and numeric
codes alike - requires the title to also say "Stinson" explicitly, the
same lesson learned the hard way in the companion Piper repo, where a
bare "Cub" mislabeled non-Piper homebuilts as genuine Pipers. A bare
"Stinson" mention with no specific model stated is still published, the
same bare-brand-fallback policy used in the companion Stearman/Waco/
Pitts/Taylorcraft/Swift/Beechcraft/Air Tractor/Fairchild repos.

Titles that read as parts, accessories, services, or raffles are still
dropped regardless. Surviving titles are rewritten to a canonical "YEAR
STINSON MODEL" form when the ad states a model year and a specific model,
"YEAR Stinson" when only the model is missing, "STINSON MODEL" when only
the year is missing, or plain "Stinson" when neither is stated.

Gear note: the Stinson 108 Voyager is a fixed conventional tailwheel
design by default, like every other Stinson model here - but unlike most
of the companion repos (Pitts, Waco, Swift, Air Tractor, Fairchild), it
does have a documented rare aftermarket tricycle-gear conversion: Chambers
Aircraft Co. converted some Voyagers to tricycle gear in the 1960s. This
never became common the way Volpar's Beech 18 conversions did (323+
aircraft, still turning up regularly in the used market - see the
companion Beechcraft repo's categorical "Volpar" exclusion), so rather
than add a categorical exclusion keyed on "Chambers" - itself a common
surname/word with its own collision risk, for a conversion this rare - the
standard text-based tricycle/nosewheel safety net is relied on instead to
catch any surviving tricycle-gear Voyager by its own ad text.
"""
from __future__ import annotations

import re
from urllib.parse import quote, unquote, urljoin, urlparse

from bs4 import BeautifulSoup

from .common import (
    Listing,
    extract_date,
    extract_location,
    extract_price,
    fetch,
    format_aircraft_title,
)

SITE_NAME = "Barnstormers.com"
BASE = "https://www.barnstormers.com"
MAKE = "Stinson"

# Category page for Stinson listings on Barnstormers.
CATEGORY_URLS = [
    f"{BASE}/category-16568-Antique-Classic--Stinson.html",
]

MAX_PAGES = 10
LISTING_LINK_RE = re.compile(r"^/classified-(\d+)-(.+)\.html$")
GENERIC_SITE_TITLE_SNIPPET = "barnstormers.com find aircraft"


def _compact(text: str) -> str:
    return re.sub(r"[\s-]", "", text.lower())


# "Stinson" is the only coarse-gate phrase used - the model codes and
# marketing names below carry too much substring-collision risk to use
# safely as a coarse filter on their own.
TARGET_MODEL_PHRASES = ["stinson"]


def _matches_target_models(title: str) -> bool:
    compact = _compact(title)
    return any(phrase in compact for phrase in TARGET_MODEL_PHRASES)


_BRAND_RE = re.compile(r"\bstinson\b", re.IGNORECASE)

_L5_RE = re.compile(r"\bl-?5-?([a-z])?\b", re.IGNORECASE)
# Model 108: bare "108" or with a dash-number sub-model (108-1, 108-2,
# 108-3). Only a hyphen (not a space) is allowed before the sub-model
# digit, matching the lesson learned live in the companion Fairchild repo
# (a space there let unrelated following words false-match as a suffix).
_MODEL108_RE = re.compile(r"\b108-?([1-5])?\b", re.IGNORECASE)
# SR "Reliant" series: SR, SR-5 through SR-10, with an optional 0-2 letter
# engine/variant suffix directly attached (SR-9B, SR-9C, SR-9D are all
# well-documented, not obscure). The digit and letter suffix are captured
# as a single combined group so a directly-attached trailing letter (no
# space) doesn't break the word-boundary check the way it would if split
# across two separately-anchored groups.
_SR_RE = re.compile(r"\bsr-?((?:5|6|7|8|9|10)[a-z]{0,2})?\b", re.IGNORECASE)
# Prewar Model 10/10A Voyager.
_MODEL10_RE = re.compile(r"\b10-?(a)?\b", re.IGNORECASE)

_MARKETING_NAME_RULES = [
    (re.compile(r"\bstation\s*wagon\b", re.IGNORECASE), "Station Wagon"),
    (re.compile(r"\bgullwing\b", re.IGNORECASE), "Gullwing Reliant"),
    (re.compile(r"\breliant\b", re.IGNORECASE), "Reliant"),
    (re.compile(r"\bvoyager\b", re.IGNORECASE), "Voyager"),
    (re.compile(r"\bsentinel\b", re.IGNORECASE), "Sentinel"),
]


def _extract_model(title: str) -> tuple[str, str] | None:
    if not _BRAND_RE.search(title):
        return None

    match = _L5_RE.search(title)
    if match:
        suffix = match.group(1)
        return MAKE, f"L-5{suffix.upper()}" if suffix else "L-5"

    match = _MODEL108_RE.search(title)
    if match:
        suffix = match.group(1)
        return MAKE, f"108-{suffix}" if suffix else "108"

    match = _SR_RE.search(title)
    if match:
        suffix = match.group(1)
        return MAKE, f"SR-{suffix.upper()}" if suffix else "SR"

    match = _MODEL10_RE.search(title)
    if match:
        suffix = match.group(1)
        return MAKE, f"10{suffix.upper()}" if suffix else "10"

    for pattern, canonical in _MARKETING_NAME_RULES:
        if pattern.search(title):
            return MAKE, canonical

    return MAKE, ""


# Ads whose title or body text explicitly calls out tricycle/nosewheel gear
# are dropped, regardless of which model they are - see module docstring.
_NON_TAILWHEEL_KEYWORDS = (
    "tricycle gear",
    "tricycle landing gear",
    "trike gear",
    "tri-gear",
    "tri gear",
    "nosewheel",
    "nose wheel",
    "nose-wheel",
)


def _is_non_tailwheel(text: str) -> bool:
    lowered = text.lower()
    return any(keyword in lowered for keyword in _NON_TAILWHEEL_KEYWORDS)


def _page_url(category_url: str, page: int) -> str:
    """Build a category page's URL directly.

    Barnstormers' category pager renders as page-number buttons with no
    "Next" text or rel="next" attribute for a link-following heuristic to
    find (confirmed on the companion Van's RV, Aviat, and several other
    repos, where that approach silently stopped after page 1) - so each
    page's URL is built from the known
    ?seocategory=<url-encoded-path>&page=<n> pattern instead.
    """
    if page <= 1:
        return category_url
    path = urlparse(category_url).path
    return f"{category_url}?seocategory={quote(path, safe='')}&page={page}"


def _title_from_url(url: str) -> str:
    """Listing pages share a generic <title>/<h1>, but the URL slug is the ad's own title."""
    slug = url.rstrip("/").rsplit("/", 1)[-1]
    match = LISTING_LINK_RE.match("/" + slug)
    if not match:
        return unquote(slug)
    return unquote(match.group(2)).replace("-", " ").strip()


def _find_listing_links(html: str) -> set[str]:
    soup = BeautifulSoup(html, "lxml")
    links = set()
    for a in soup.find_all("a", href=True):
        href = a["href"].split("?")[0]
        if LISTING_LINK_RE.match(href):
            links.add(urljoin(BASE, href))
    return links


def _debug_dump_hrefs(html: str, limit: int = 25) -> None:
    soup = BeautifulSoup(html, "lxml")
    hrefs = [a["href"] for a in soup.find_all("a", href=True)]
    interesting = [h for h in hrefs if "classified" in h.lower() or "stinson" in h.lower()]
    sample = interesting[:limit] or hrefs[:limit]
    print(f"  [debug] {len(hrefs)} total <a href> on page; sample: {sample}")


def _parse_detail_page(url: str, html: str) -> Listing | None:
    soup = BeautifulSoup(html, "lxml")

    title_tag = soup.find("h1") or soup.find("title")
    title = title_tag.get_text(strip=True) if title_tag else None
    if title:
        title = re.sub(r"\s*[\|\-]\s*Barnstormers.*$", "", title, flags=re.IGNORECASE).strip()
    if not title or GENERIC_SITE_TITLE_SNIPPET in title.lower():
        title = _title_from_url(url)
    if not title:
        return None

    if not _matches_target_models(title):
        return None

    text = soup.get_text(" ", strip=True)

    if _is_non_tailwheel(title) or _is_non_tailwheel(text):
        return None

    formatted_title = format_aircraft_title(title, text, _extract_model)
    if not formatted_title:
        return None
    # A bare-"Stinson" match (no specific model code) leaves a trailing
    # space from format_aircraft_title's "{make} {model}" join, since
    # _extract_model returns an empty model string in that case.
    title = formatted_title.rstrip()

    price = extract_price(text)
    location = extract_location(text)
    date_posted = extract_date(text)

    return Listing(
        title=title,
        price=price,
        location=location,
        date_posted=date_posted,
        site=SITE_NAME,
        url=url,
    )


def scrape() -> list[Listing]:
    print(f"[{SITE_NAME}] starting scrape")
    all_links: set[str] = set()

    for category_url in CATEGORY_URLS:
        seen_this_category: set[str] = set()
        for page in range(1, MAX_PAGES + 1):
            url = _page_url(category_url, page)
            html = fetch(url)
            if not html:
                break
            links = _find_listing_links(html)
            new_links = links - seen_this_category
            print(f"  [{category_url}] page {page}: {len(links)} links ({len(new_links)} new)")
            if page == 1 and not links:
                _debug_dump_hrefs(html)
            seen_this_category |= links
            if not new_links:
                break
        all_links |= seen_this_category

    print(f"[{SITE_NAME}] {len(all_links)} unique listing URLs found")

    candidate_links = {url for url in all_links if _matches_target_models(_title_from_url(url))}
    print(f"[{SITE_NAME}] {len(candidate_links)} match Stinson product names")

    listings: list[Listing] = []
    for url in sorted(candidate_links):
        html = fetch(url)
        if not html:
            continue
        listing = _parse_detail_page(url, html)
        if listing:
            listings.append(listing)

    print(f"[{SITE_NAME}] parsed {len(listings)} listings")
    return listings
