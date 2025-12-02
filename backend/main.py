import os
import requests
import re
import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from typing import List

from .schemas import SearchRequest, SearchResponse, Item
from .scrapers.dummy import scrape_dummy
from .utils.calc import calculate_landed_cost, convert_to_twd
from .utils import parser, cache, retailer

# logging
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO').upper()
logging.basicConfig(level=LOG_LEVEL, format='%(asctime)s %(levelname)s %(name)s: %(message)s')
logger = logging.getLogger('hypeprice')

# SerpApi configuration (read from env; do not crash at import — handle at runtime)
SERPAPI_KEY = os.getenv('SERPAPI_KEY')
if not SERPAPI_KEY:
    logger.warning('Environment variable SERPAPI_KEY is not set. /api/search will return 503 until configured.')
SERPAPI_URL = "https://serpapi.com/search"



def call_serpapi(query: str, gl: str = 'tw', hl: str = 'zh-tw'):
    params = {
        'engine': 'google_shopping',
        'q': query,
        'gl': gl,
        'hl': hl,
    }
    # attach api key at call time to allow runtime swapping and safer import
    if not SERPAPI_KEY:
        logger.error('call_serpapi invoked but SERPAPI_KEY is not configured')
        return {}
    params['api_key'] = SERPAPI_KEY
    try:
        resp = requests.get(SERPAPI_URL, params=params, timeout=15)
        resp.raise_for_status()
        return resp.json()
    except Exception:
        logger.exception('SerpApi request failed')
        return {}


# Cached wrapper to reduce SerpApi calls
call_serpapi_cached = cache.ttl_cache(ttl=120)(call_serpapi)


app = FastAPI(title="HypePrice Tracker API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {"status": "ok", "serpapi_configured": bool(SERPAPI_KEY)}


@app.post("/api/search", response_model=SearchResponse)
async def search(req: SearchRequest):
    if not req.q:
        raise HTTPException(status_code=400, detail="Query parameter `q` is required")

    try:
        logger.info("Search triggered for: %s", req.q)
    except Exception:
        logger.exception("Failed logging search trigger")

    # If SERPAPI_KEY isn't configured, return a clear 503 so the deploy/runtime can start
    if not SERPAPI_KEY:
        raise HTTPException(status_code=503, detail="SERPAPI_KEY not configured. Set the SERPAPI_KEY environment variable.")

    # Query multiple regions (foreign-first) to surface international listings/discounts.
    requested_regions = req.regions if getattr(req, 'regions', None) else None
    # default foreign markets (exclude TW by default so we surface non-local prices)
    default_regions = ['us', 'gb', 'jp']
    regions = requested_regions if requested_regions else default_regions

    items = []
    placeholder = "https://placehold.co/400x400?text=Product+Image"

    # collect by unique key (prefer link when available)
    seen = {}
    for region in regions:
        data = call_serpapi_cached(req.q, gl=region)
        shopping = data.get('shopping_results') or []
        for s in shopping:
            try:
                title = s.get('title') or s.get('product_title') or s.get('name') or ''
                price_text = s.get('price') or s.get('extracted_price') or s.get('price_string') or ''
                thumbnail = s.get('thumbnail') or s.get('thumbnail_image') or s.get('image') or ''
                source_raw = s.get('source') or s.get('merchant') or s.get('store') or s.get('displayed_at') or 'Retailer'
                source = retailer.normalize_retailer(source_raw)
                link = s.get('link') or s.get('product_link') or ''

                # preserve original string
                original_price_string = str(price_text) if price_text is not None else ''

                parsed_amount, parsed_currency, assumed_usd, price_twd = parser.parse_currency(original_price_string, s)
                if assumed_usd and original_price_string:
                    original_price_string = f"{original_price_string} (Assumed USD)"

                shipping = 800
                tax = int(round((price_twd + shipping) * 0.17))
                final_price = int(round(price_twd + shipping + tax))

                discount_text, discount_pct, strike_twd = parser.detect_discount(s, price_twd)

                key = link or f"{title}||{source}||{region}"
                # dedupe: if we already have this link, keep the cheaper one
                existing = seen.get(key)
                candidate = dict(
                    retailer=source,
                    image=thumbnail or None,
                    image_url=thumbnail or None,
                    original_price=parsed_amount,
                    original_price_string=original_price_string,
                    currency=parsed_currency,
                    discount_text=discount_text,
                    discount_pct=discount_pct,
                    price_twd=price_twd,
                    shipping_twd=shipping,
                    tax_twd=tax,
                    final_price_twd=final_price,
                    landed_cost_estimate=final_price,
                    url=link or None,
                    sizes=[],
                    weight='N/A',
                    region=region,
                )
                if existing:
                    # keep the one with lower final_price_twd
                    if candidate['final_price_twd'] < existing['final_price_twd']:
                        seen[key] = candidate
                else:
                    seen[key] = candidate
            except Exception:
                continue

    # include any seen items
    for v in seen.values():
        items.append(Item(
            retailer=v['retailer'],
            image=v['image'],
            image_url=v['image_url'],
            original_price=v['original_price'],
            original_price_string=v['original_price_string'],
            currency=v['currency'],
            discount_text=v.get('discount_text'),
            discount_pct=v.get('discount_pct'),
            price_twd=v['price_twd'],
            shipping_twd=v['shipping_twd'],
            tax_twd=v['tax_twd'],
            final_price_twd=v['final_price_twd'],
            landed_cost_estimate=v['landed_cost_estimate'],
            url=v['url'],
            sizes=v.get('sizes') or [],
            weight=v.get('weight') or 'N/A',
        ))
    # Fallback to mock/dummy if nothing
    if not items:
        # try dummy scraper
        try:
            fallback = await scrape_dummy(req.q)
        except Exception:
            fallback = []

        if fallback:
            for r in fallback:
                original_price_string = r.get('original_price_string') or str(r.get('original_price', ''))
                parsed_amount, parsed_currency, assumed_usd, price_twd = parser.parse_currency(original_price_string, r)
                if assumed_usd and original_price_string:
                    original_price_string = f"{original_price_string} (Assumed USD)"
                shipping = 800
                tax = int(round((price_twd + shipping) * 0.17))
                final_price = int(round(price_twd + shipping + tax))

                items.append(Item(
                    retailer=r.get('retailer', 'unknown'),
                    image=r.get('image'),
                    image_url=r.get('image'),
                    original_price=float(r.get('original_price', 0.0)),
                    original_price_string=original_price_string,
                    currency=r.get('currency', 'USD'),
                    discount_text=None,
                    discount_pct=None,
                    price_twd=price_twd,
                    shipping_twd=shipping,
                    tax_twd=tax,
                    final_price_twd=final_price,
                    landed_cost_estimate=final_price,
                    url=r.get('url'),
                    sizes=r.get('sizes') or [],
                    weight=r.get('weight') or 'N/A',
                ))
        else:
            # smart mock
            async def get_mock_data(query: str):
                q = (query or '').lower()
                default_image = placeholder
                mock = []
                brand_models = {
                    'barbour': [
                        ('Barbour Bedale', 329.0, 'GBP'),
                        ('Barbour Ashby', 289.0, 'GBP'),
                        ('Barbour Beaufort', 349.0, 'GBP'),
                    ],
                }
                entries = []
                for k, models in brand_models.items():
                    if k in q:
                        entries = models
                        break
                if not entries:
                    entries = [
                        (f"{query} Classic", 120.0, 'USD'),
                        (f"{query} Premium", 199.0, 'USD'),
                        (f"{query} Limited", 249.0, 'USD'),
                    ]
                i = 0
                while len(mock) < 6 and i < len(entries) * 3:
                    base = entries[i % len(entries)]
                    name = base[0]
                    price = round(base[1] * (1 + (i % 3) * 0.05), 2)
                    currency = base[2]
                    # normalize mock price and produce integer TWD
                    original_price_string = f"{price} {currency}"
                    parsed_amount, parsed_currency, assumed_usd, price_twd = parser.parse_currency(original_price_string)
                    if assumed_usd and original_price_string:
                        original_price_string = f"{original_price_string} (Assumed USD)"
                    shipping = 800
                    tax = int(round((price_twd + shipping) * 0.17))
                    final_price = int(round(price_twd + shipping + tax))
                    mock.append(Item(
                        retailer=f"Mock Retailer {i+1}",
                        image=default_image,
                        image_url=default_image,
                        original_price=price,
                        original_price_string=original_price_string,
                        currency=currency,
                        discount_text=None,
                        discount_pct=None,
                        price_twd=price_twd,
                        shipping_twd=shipping,
                        tax_twd=tax,
                        final_price_twd=final_price,
                        landed_cost_estimate=final_price,
                        url=f"https://example.com/{name.replace(' ', '-').lower()}",
                        sizes=['S','M','L'],
                        weight=f"{1.0 + (i%3)*0.2}kg",
                    ))
                    i += 1
                return mock

            items = await get_mock_data(req.q)

    # mark lowest
    if items:
        lowest = min(items, key=lambda x: x.final_price_twd)
        for it in items:
            it.is_lowest = (it is lowest)

    return SearchResponse(query=req.q, results=items)


# mount frontend at the end
frontend_dir = os.path.join(os.path.dirname(__file__), '..', 'frontend_dist')
frontend_dir = os.path.abspath(frontend_dir)
if os.path.exists(frontend_dir):
    app.mount('/', StaticFiles(directory=frontend_dir, html=True), name='frontend')
