from playwright.async_api import async_playwright
from typing import List, Dict, Any
import re


async def scrape_end(query: str, max_results: int = 8) -> List[Dict[str, Any]]:
    """Scrape End. Clothing search results for `query` using Playwright.

    Returns list of dicts with keys: retailer, image, original_price, currency, url
    """
    items = []
    search_url = f"https://www.endclothing.com/gb/search?q={query.replace(' ', '+')}"

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        try:
            page = await browser.new_page()
            await page.goto(search_url, timeout=30000)
            # Wait for product tiles - selector may vary; try a few fallbacks
            try:
                await page.wait_for_selector('a[data-test="product-card"]', timeout=5000)
                cards = await page.query_selector_all('a[data-test="product-card"]')
            except Exception:
                # fallback generic link to product
                cards = await page.query_selector_all('a[href*="/product/"]')

            for c in cards[:max_results]:
                try:
                    href = await c.get_attribute('href') or ''
                    url = href if href.startswith('http') else 'https://www.endclothing.com' + href
                    # image
                    img = ''
                    img_el = await c.query_selector('img')
                    if img_el:
                        img = await img_el.get_attribute('src') or ''

                    # price - try to locate price text
                    price_text = ''
                    price_el = await c.query_selector('span[class*=price]')
                    if price_el:
                        price_text = await price_el.inner_text()
                    else:
                        # try any element that looks like a price
                        possible = await c.query_selector_all('span')
                        for p in possible:
                            t = (await p.inner_text()).strip()
                            if re.search(r"\d", t) and ("£" in t or "$" in t or "¥" in t or "JPY" in t or "GBP" in t):
                                price_text = t
                                break

                    # Normalize price and currency
                    price_val = 0.0
                    currency = 'GBP'
                    m = re.search(r"([£€$¥])\s*([0-9,]+\.?[0-9]*)", price_text)
                    if m:
                        symbol = m.group(1)
                        num = m.group(2).replace(',', '')
                        price_val = float(num)
                        if symbol == '£':
                            currency = 'GBP'
                        elif symbol == '$':
                            currency = 'USD'
                        elif symbol == '¥' or symbol == 'JPY':
                            currency = 'JPY'
                    else:
                        # try to parse numbers only
                        m2 = re.search(r"([0-9,]+\.?[0-9]*)", price_text)
                        if m2:
                            price_val = float(m2.group(1).replace(',', ''))

                    items.append({
                        'retailer': 'END. Clothing (UK)',
                        'image': img,
                        'original_price': price_val,
                        'currency': currency,
                        'url': url,
                    })
                except Exception:
                    continue
        finally:
            await browser.close()

    return items
