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
    currency: str
    price_twd: float = Field(..., description="Price converted to TWD")
    shipping_twd: float
    tax_twd: float
    final_price_twd: float
    landed_cost_estimate: float = Field(..., description="Estimated landed cost in TWD")
    url: Optional[str]
    sizes: Optional[List[str]] = Field(default_factory=list)
    weight: Optional[str] = "N/A"
    is_lowest: bool = False

class SearchResponse(BaseModel):
    query: str
    results: List[Item]
