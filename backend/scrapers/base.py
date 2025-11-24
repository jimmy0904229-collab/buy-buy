from abc import ABC, abstractmethod
from typing import List, Dict, Any

class BaseScraper(ABC):
    """Abstract base scraper. Concrete scrapers should implement `scrape`.

    The `scrape` method should return a list of dicts with at least:
    - retailer, image, price, currency, url
    """

    @abstractmethod
    async def scrape(self, query: str) -> List[Dict[str, Any]]:
        raise NotImplementedError()
