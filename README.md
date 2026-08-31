# Stinson

Daily aggregator of Stinson classified listings (Model 108 "Voyager"/
"Station Wagon", the prewar Model 10/10A Voyager, the SR "Reliant"
series, and the military L-5 "Sentinel") from
[Barnstormers.com](https://www.barnstormers.com), published as a static
page (`docs/index.html`) meant to be embedded via `<iframe>` on
taildraggers.com.

Controller.com was evaluated (in the companion [Aeronca](https://github.com/taildraggers/aeronca)
repo) and dropped: its search results are only reachable through an internal
client-side widget (not a plain URL), which a headless browser can't drive
reliably for an unattended daily job.

Note: in the companion [Aviat](https://github.com/taildraggers/aviat),
[CubCrafters](https://github.com/taildraggers/cub-crafters),
[de Havilland](https://github.com/taildraggers/de-Havilland),
[Maule](https://github.com/taildraggers/maule),
[Van's RV](https://github.com/taildraggers/vans),
[RANS](https://github.com/taildraggers/rans),
[Luscombe](https://github.com/taildraggers/luscombe),
[Just Aircraft](https://github.com/taildraggers/just-aircraft),
[Kitfox](https://github.com/taildraggers/kitfox),
[Bellanca](https://github.com/taildraggers/bellanca),
[Stearman](https://github.com/taildraggers/stearman),
[Waco](https://github.com/taildraggers/waco),
[Pitts](https://github.com/taildraggers/pitts),
[Taylorcraft](https://github.com/taildraggers/taylorcraft),
[Swift](https://github.com/taildraggers/swift),
[Beechcraft](https://github.com/taildraggers/beech),
[Air Tractor](https://github.com/taildraggers/airtractor), and
[Fairchild](https://github.com/taildraggers/fairchild) repos, Barnstormers'
single-manufacturer category pages turned out to include unrelated
listings mixed in with no distinguishing HTML markup. This repo is built
with the same fix from day one: `scraper/barnstormers.py` filters by
title against a small allowlist (see `TARGET_MODEL_PHRASES` in
`scraper/barnstormers.py`) before publishing.

Stinson's model lineup spans several distinct families across decades:
the postwar **Model 108** "Voyager"/"Station Wagon" (`108`, `108-1`,
`108-2`, `108-3`), the prewar **Model 10/10A** Voyager, the **SR**
"Reliant" series (`SR-5` through `SR-10`, later ones nicknamed
"Gullwing"), and the military **L-5** "Sentinel" (`L-5`, `L-5B`, `L-5C`,
`L-5E`, `L-5G`). Every one of the marketing names - "Reliant", "Voyager",
"Sentinel", "Station Wagon", "Gullwing" - is an ordinary English word or
phrase with real collision risk (a Plymouth Reliant, a Winnebago/Plymouth
Voyager, a police sentinel, etc.), so unlike Waco's or RANS's coined model
names, every match here - names and numeric codes alike - requires the
title to also say "Stinson" explicitly (the same lesson learned the hard
way in the companion Piper repo, where a bare "Cub" mislabeled non-Piper
homebuilts as genuine Pipers). A bare "Stinson" mention with no specific
model stated is still published, the same bare-brand-fallback policy used
in the companion Stearman/Waco/Pitts/Taylorcraft/Swift/Beechcraft/Air
Tractor/Fairchild repos. Titles that read as parts, accessories,
services, or raffles are still dropped regardless. Every surviving
listing's title is rewritten to a canonical **`YEAR STINSON MODEL`** form
when the ad states a model year and a specific model (e.g. `1946 Stinson
108`), `YEAR Stinson` when only the model is missing, `STINSON MODEL`
when only the year is missing, or plain **`Stinson`** when neither is
stated.

**Gear note:** the Stinson 108 Voyager is a fixed conventional tailwheel
design by default, like every other Stinson model here - but unlike most
of the companion repos (Pitts, Waco, Swift, Air Tractor, Fairchild), it
does have a documented *rare* aftermarket tricycle-gear conversion:
Chambers Aircraft Co. converted some Voyagers to tricycle gear in the
1960s. This never became common the way Volpar's Beech 18 conversions did
(323+ aircraft, still turning up regularly in the used market - see the
companion [Beechcraft](https://github.com/taildraggers/beech) repo's
categorical "Volpar" exclusion), so rather than add a categorical
exclusion keyed on "Chambers" - itself a common surname/word with its own
collision risk, for a conversion this rare - the standard text-based
tricycle/nosewheel safety net used in every companion repo is relied on
instead to catch any surviving tricycle-gear Voyager by its own ad text.

## How it works

- `scraper/barnstormers.py` searches Barnstormers.com's Stinson category
  for listings, follows pagination, then keeps only the ones whose URL
  slug matches the Stinson allowlist (Barnstormers builds each listing's
  URL slug directly from the ad's own title, so this runs before any
  detail page is fetched). For the matches, it visits each listing's
  detail page to pull out the price, location, and posted date (falling
  back to regex heuristics over the visible text since the site doesn't
  expose structured data). The title is derived from the listing URL's
  own SEO slug, since every detail page shares one generic `<title>`/
  `<h1>`; the final parsed title is checked against the allowlist again
  as a safety net. Pagination is built directly from Barnstormers' known
  `?seocategory=<url-encoded-path>&page=<n>` URL pattern rather than
  discovered by following a "Next" link, since this category's pager
  renders as page-number buttons with no "Next" text or `rel="next"`
  attribute to find (a lesson learned the hard way in the companion Van's
  RV and Aviat repos, where the link-following approach silently stopped
  after page 1).
- `main.py` runs the scraper, de-duplicates results, sorts them
  newest-posted-first, and renders them into `docs/index.html` titled
  **"Other Stinson Ads on the Web"**, with one row per listing: Title
  (linked to the original ad), Price, Location, Date Posted, and Site
  Posted On. Below phone width, each row collapses into a card (title +
  price on one line, location/date/site on a smaller line below) instead
  of a horizontally-scrolling table. Below the table, a "Search More
  Stinson Listings" section links out to Trade-A-Plane, Controller, and
  ASO - sites that block automated scraping, but are still worth sending
  visitors to directly via a pre-filled search. Links use
  `rel="noopener noreferrer"` and the page sets a `no-referrer` meta
  policy, so none of these sites see that the click came from
  taildraggers.com.
- `.github/workflows/daily-scrape.yml` runs the whole thing once a day (13:00 UTC),
  commits the regenerated `docs/index.html` if it changed, and can also be triggered
  manually from the Actions tab (`workflow_dispatch`).

## One-time setup: enable GitHub Pages

This repo publishes `docs/index.html` as a plain static file — GitHub Pages just needs
to be pointed at it once:

1. Go to **Settings → Pages** in this repository.
2. Under **Build and deployment → Source**, choose **Deploy from a branch**.
3. Branch: `main`, folder: `/docs`. Save.
4. GitHub will publish the page at `https://taildraggers.github.io/stinson/`
   (may take a minute or two the first time).

Also check **Settings → Actions → General**:
- **Actions permissions**: "Allow all actions and reusable workflows".
- **Workflow permissions**: "Read and write permissions" (needed so the daily
  job can commit the regenerated page back to the repo).

## Embedding on taildraggers.com

```html
<iframe
  src="https://taildraggers.github.io/stinson/"
  title="Other Stinson Ads on the Web"
  style="width: 100%; height: 800px; border: 0;"
  loading="lazy">
</iframe>
```

The page also posts its rendered height to the parent window on load/resize
(`{ type: "taildraggers:resize", height }`) so it can be auto-sized instead
of using a fixed guessed height - add a matching `message` listener on the
embedding page to pick this up.

## Running locally

```bash
pip install -r requirements.txt
playwright install --with-deps chromium
python main.py
```

This writes/overwrites `docs/index.html`.

## Notes

- If Barnstormers changes its markup or is briefly unreachable, the run logs will
  show a `[warn]`/`[error]` line pointing at what broke rather than failing silently.
- The scraper identifies itself with a browser-like `User-Agent` and adds a short
  delay between requests to be polite to the site.
- Only one Barnstormers category is currently configured
  (`category-16568-Antique-Classic--Stinson.html`). If listings turn out
  to be split across additional categories, add more URLs to
  `CATEGORY_URLS` in `scraper/barnstormers.py`.
- The SR "Reliant" letter-suffix list (`SR-9B`, `SR-9C`, `SR-9D`, etc.)
  isn't exhaustive of every Reliant variant ever built. Missing a code
  isn't fatal since the bare-"Reliant"/"Stinson" fallback still publishes
  the listing (just without a specific sub-model in the title) - but if a
  particular code turns up often enough, add it to
  `scraper/barnstormers.py`.
