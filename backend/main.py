import os
import requests
import re
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from typing import List

from .schemas import SearchRequest, SearchResponse, Item
from .scrapers.dummy import scrape_dummy
from .utils.calc import calculate_landed_cost, convert_to_twd

# SerpApi configuration (placeholder key)
SERPAPI_KEY = "6313cd4d2dd307a65fb95b1ae33f759cc0558415e5f36c9698568bd7fabe267f"
SERPAPI_URL = "https://serpapi.com/search"


def parse_price_and_currency(price_text: str):
    """Return (amount: float, currency: str) inferred from price_text."""
    if not price_text:
        return 0.0, 'USD'

    text = price_text.strip()
    # common patterns
    # NT$ or TWD
    if 'NT$' in text or 'TWD' in text or 'NT' in text:
        m = re.search(r'([0-9,]+\.?[0-9]*)', text)
        if m:
            return float(m.group(1).replace(',', '')), 'TWD'
    # GBP
    m = re.search(r'£\s*([0-9,]+\.?[0-9]*)', text)
    if m:
        return float(m.group(1).replace(',', '')), 'GBP'
    # JPY
    m = re.search(r'¥\s*([0-9,]+\.?[0-9]*)', text)
    if m:
        return float(m.group(1).replace(',', '')), 'JPY'
    # USD (dollar symbol ambiguous)
    m = re.search(r'\$\s*([0-9,]+\.?[0-9]*)', text)
    if m:
        return float(m.group(1).replace(',', '')), 'USD'

    # fallback: extract first number and assume USD
    m = re.search(r'([0-9,]+\.?[0-9]*)', text)
    if m:
        return float(m.group(1).replace(',', '')), 'USD'

    return 0.0, 'USD'


def call_serpapi(query: str, gl: str = 'tw', hl: str = 'zh-tw'):
    params = {
        'engine': 'google_shopping',
        'q': query,
        'gl': gl,
        'hl': hl,
        'api_key': SERPAPI_KEY,
    }
    try:
        resp = requests.get(SERPAPI_URL, params=params, timeout=15)
        resp.raise_for_status()
        return resp.json()
    except Exception:
        return {}


app = FastAPI(title="HypePrice Tracker API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/api/search", response_model=SearchResponse)
async def search(req: SearchRequest):
    if not req.q:
        raise HTTPException(status_code=400, detail="Query parameter `q` is required")

    try:
        print("Search triggered for:", req.q)
    except Exception:
        pass

    # Call SerpApi
    data = call_serpapi(req.q)
    shopping = data.get('shopping_results') or []

    items = []
    placeholder = "https://placehold.co/400x400?text=Product+Image"

    if shopping:
        for s in shopping:
            try:
                title = s.get('title') or s.get('product_title') or s.get('name') or ''
                price_text = s.get('price') or s.get('extracted_price') or s.get('price_string') or ''
                thumbnail = s.get('thumbnail') or s.get('thumbnail_image') or s.get('image') or ''
                source = s.get('source') or s.get('merchant') or s.get('store') or s.get('displayed_at') or 'Retailer'
                link = s.get('link') or s.get('product_link') or s.get('link') or ''

                amount, currency = parse_price_and_currency(str(price_text))

                # compute landed cost using existing helper
                calc = calculate_landed_cost(amount, currency)

                item = Item(
                    retailer=source,
                    image=thumbnail or None,
                    image_url=thumbnail or None,
                    original_price=amount,
                    currency=currency,
                    price_twd=calc['price_twd'],
                    shipping_twd=calc['shipping_twd'],
                    tax_twd=calc['tax_twd'],
                    final_price_twd=calc['final_price_twd'],
                    landed_cost_estimate=calc['final_price_twd'],
                    url=link,
                    sizes=[],
                    weight='N/A',
                )
                items.append(item)
            except Exception:
                continue

    # Fallback to mock/dummy if nothing
    if not items:
        # try dummy scraper
        try:
            fallback = await scrape_dummy(req.q)
        except Exception:
            fallback = []

        if fallback:
            for r in fallback:
                calc = calculate_landed_cost(r.get('original_price', 0.0), r.get('currency', 'USD'))
                items.append(Item(
                    retailer=r.get('retailer', 'unknown'),
                    image=r.get('image'),
                    image_url=r.get('image'),
                    original_price=r.get('original_price', 0.0),
                    currency=r.get('currency', 'USD'),
                    price_twd=calc['price_twd'],
                    shipping_twd=calc['shipping_twd'],
                    tax_twd=calc['tax_twd'],
                    final_price_twd=calc['final_price_twd'],
                    landed_cost_estimate=calc['final_price_twd'],
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
                    calc = calculate_landed_cost(price, currency)
                    mock.append(Item(
                        retailer=f"Mock Retailer {i+1}",
                        image=default_image,
                        image_url=default_image,
                        original_price=price,
                        currency=currency,
                        price_twd=calc['price_twd'],
                        shipping_twd=calc['shipping_twd'],
                        tax_twd=calc['tax_twd'],
                        final_price_twd=calc['final_price_twd'],
                        landed_cost_estimate=calc['final_price_twd'],
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
