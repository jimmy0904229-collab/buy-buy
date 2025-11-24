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

    raw_items = []
    # Prefer End scraper if available
    if scrape_end is not None:
        try:
            raw_items = await scrape_end(req.q)
        except Exception:
            raw_items = []

    # Fallback to dummy if real scraper returned nothing
    if not raw_items:
        raw_items = await scrape_dummy(req.q)

    results: List[Item] = []
    for r in raw_items:
        calc = calculate_landed_cost(r["original_price"], r.get("currency", "USD"))
        item = Item(
            retailer=r.get("retailer", "unknown"),
            image=r.get("image"),
            original_price=r.get("original_price", 0.0),
            currency=r.get("currency", "USD"),
            price_twd=calc["price_twd"],
            shipping_twd=calc["shipping_twd"],
            tax_twd=calc["tax_twd"],
            final_price_twd=calc["final_price_twd"],
            url=r.get("url"),
        )
        results.append(item)

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
