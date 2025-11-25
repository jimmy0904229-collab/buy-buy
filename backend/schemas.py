from pydantic import BaseModel, Field
from typing import List, Optional

class SearchRequest(BaseModel):
    q: str
    currency: Optional[str] = "USD"

class Item(BaseModel):
    retailer: str
    image: Optional[str]
    image_url: Optional[str]
    original_price: float
    original_price_string: Optional[str] = None
    currency: str
    price_twd: int = Field(..., description="Price converted to TWD as integer")
    shipping_twd: int
    tax_twd: int
    final_price_twd: int
    landed_cost_estimate: int = Field(..., description="Estimated landed cost in TWD")
    url: Optional[str]
    sizes: Optional[List[str]] = Field(default_factory=list)
    weight: Optional[str] = "N/A"
    is_lowest: bool = False

class SearchResponse(BaseModel):
    query: str
    results: List[Item]
