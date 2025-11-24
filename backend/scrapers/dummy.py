import asyncio
from typing import List, Dict, Any

# Dummy scraper returns mock data quickly so frontend and API can be wired.
async def scrape_dummy(query: str) -> List[Dict[str, Any]]:
    # Simulate some async delay
    await asyncio.sleep(0.1)
    q = query.lower()
    # Mock items across different retailers and currencies
    items = [
        {
            "retailer": "END. Clothing (UK)",
            "image": "https://via.placeholder.com/240x320.png?text=END+Item",
            "original_price": 280.0,
            "currency": "GBP",
            "url": "https://www.endclothing.com/product/1",
        },
        {
            "retailer": "SSENSE",
            "image": "https://via.placeholder.com/240x320.png?text=SSENSE+Item",
            "original_price": 350.0,
            "currency": "USD",
            "url": "https://www.ssense.com/product/1",
        },
        {
            "retailer": "Japanese Retailer",
            "image": "https://via.placeholder.com/240x320.png?text=JP+Item",
            "original_price": 40000.0,
            "currency": "JPY",
            "url": "https://jp.example.com/product/1",
        },
    ]

    # Filter pseudo by query for demo (keeps all for now)
    return items

# Example of real Playwright-based scraper (commented-out)
"""
from playwright.async_api import async_playwright

async def scrape_end_playwright(query: str):
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        page = await browser.new_page()
        # real scraping steps here (search, parse list, etc.)
        await browser.close()
"""
