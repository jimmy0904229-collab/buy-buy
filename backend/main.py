import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from typing import List

from .schemas import SearchRequest, SearchResponse, Item
from .scrapers.dummy import scrape_dummy
# try to import the real End scraper; if not available, we'll fall back to dummy
try:
    from .scrapers.end_playwright import scrape_end
except Exception:
    scrape_end = None
from .utils.calc import calculate_landed_cost

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

    # simple log for Render to show the incoming search in service logs
    try:
        print("Search triggered for:", req.q)
    except Exception:
        pass

    async def get_mock_data(query: str):
        # Build realistic mock items based on query keywords
        q = (query or "").lower()
        default_image = "https://placehold.co/400x400?text=Product+Image"
        mock = []
        # small library of brand-specific models
        brand_models = {
            'barbour': [
                ('Barbour Bedale', 329.0, 'GBP'),
                ('Barbour Ashby', 289.0, 'GBP'),
                ('Barbour Beaufort', 349.0, 'GBP'),
            ],
            'carhartt': [
                ('Carhartt Detroit Jacket', 149.0, 'USD'),
                ('Carhartt Duck Active Jacket', 179.0, 'USD'),
            ],
            'ralph': [
                ('Ralph Lauren Polo Jacket', 299.0, 'USD'),
                ('Ralph Lauren Stadium Jacket', 349.0, 'USD'),
            ],
        }

        entries = []
        for k, models in brand_models.items():
            if k in q:
                entries = models
                break

        if not entries:
            # generic product variants
            entries = [
                (f"{query} Classic", 120.0, 'USD'),
                (f"{query} Premium", 199.0, 'USD'),
                (f"{query} Limited", 249.0, 'USD'),
                (f"{query} Reissue", 179.0, 'USD'),
            ]

        # expand to 6-8 items with small price variations and sizes
        i = 0
        while len(mock) < 6 and i < len(entries) * 3:
            base = entries[i % len(entries)]
            name = base[0]
            price = round(base[1] * (1 + (i % 3) * 0.05), 2)
            currency = base[2]
            mock.append({
                'retailer': f"Mock Retailer {i+1}",
                'image': default_image,
                'image_url': default_image,
                'original_price': price,
                'currency': currency,
                'url': f"https://example.com/{name.replace(' ', '-').lower()}",
                'sizes': ['S', 'M', 'L'] if 'women' not in q else ['XS','S','M'],
                'weight': f"{1.0 + (i%3)*0.2}kg",
            })
            i += 1

        return mock

    raw_items = []
    # Try real scraper first but don't crash
    if scrape_end is not None:
        try:
            raw_items = await scrape_end(req.q)
        except Exception:
            raw_items = []

    # Attempt to enrich scraped items (extract image_url and sizes if present)
    enriched = []
    for r in raw_items:
        try:
            image_url = r.get('image') or r.get('image_url') or None
            sizes = r.get('sizes') or r.get('available_sizes') or []
            weight = r.get('weight') or 'N/A'
            enriched.append({
                'retailer': r.get('retailer', 'unknown'),
                'image': image_url,
                'image_url': image_url,
                'original_price': r.get('original_price', 0.0),
                'currency': r.get('currency', 'USD'),
                'url': r.get('url'),
                'sizes': sizes,
                'weight': weight,
            })
        except Exception:
            continue

    if not enriched:
        # fallback to dummy scraper function which may provide basic items
        try:
            fallback = await scrape_dummy(req.q)
        except Exception:
            fallback = []

        if fallback:
            for r in fallback:
                enriched.append({
                    'retailer': r.get('retailer', 'unknown'),
                    'image': r.get('image'),
                    'image_url': r.get('image'),
                    'original_price': r.get('original_price', 0.0),
                    'currency': r.get('currency', 'USD'),
                    'url': r.get('url'),
                    'sizes': r.get('sizes') or ['S','M','L'],
                    'weight': r.get('weight') or 'N/A',
                })

    # If still empty, create smart mock data
    if not enriched:
        enriched = await get_mock_data(req.q)

    results: List[Item] = []
    for r in enriched:
        try:
            calc = calculate_landed_cost(r.get("original_price", 0.0), r.get("currency", "USD"))
            item = Item(
                retailer=r.get("retailer", "unknown"),
                image=r.get("image"),
                image_url=r.get("image_url") or r.get("image"),
                original_price=r.get("original_price", 0.0),
                currency=r.get("currency", "USD"),
                price_twd=calc["price_twd"],
                shipping_twd=calc.get("shipping_twd", 0.0),
                tax_twd=calc.get("tax_twd", 0.0),
                final_price_twd=calc["final_price_twd"],
                url=r.get("url"),
                sizes=r.get("sizes") or [],
                weight=r.get("weight") or "N/A",
            )
            results.append(item)
        except Exception:
            continue

    # Mark lowest
    if results:
        lowest = min(results, key=lambda x: x.final_price_twd)
        for it in results:
            it.is_lowest = (it is lowest)

    return SearchResponse(query=req.q, results=results)


# Optionally mount frontend static files if present at runtime (mount last so API routes are preferred)
frontend_dir = os.path.join(os.path.dirname(__file__), "..", "frontend_dist")
frontend_dir = os.path.abspath(frontend_dir)
if os.path.exists(frontend_dir):
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")
