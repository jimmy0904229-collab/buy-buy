import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from typing import List

from .schemas import SearchRequest, SearchResponse, Item
from .scrapers.dummy import scrape_dummy
from .utils.calc import calculate_landed_cost

app = FastAPI(title="HypePrice Tracker API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Optionally mount frontend static files if present at runtime
frontend_dir = os.path.join(os.path.dirname(__file__), "..", "frontend_dist")
frontend_dir = os.path.abspath(frontend_dir)
if os.path.exists(frontend_dir):
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")


@app.post("/api/search", response_model=SearchResponse)
async def search(req: SearchRequest):
    if not req.q:
        raise HTTPException(status_code=400, detail="Query parameter `q` is required")

    # Use dummy scraper for now (returns list of dicts)
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
