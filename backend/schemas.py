from pydantic import BaseModel, Field
from typing import List, Optional

class SearchRequest(BaseModel):
    q: str
    currency: Optional[str] = "USD"

class Item(BaseModel):
    retailer: str
    image: Optional[str]
    original_price: float
    currency: str
    price_twd: float = Field(..., description="Price converted to TWD")
    shipping_twd: float
    tax_twd: float
    final_price_twd: float
    url: Optional[str]
    is_lowest: bool = False

class SearchResponse(BaseModel):
    query: str
    results: List[Item]
