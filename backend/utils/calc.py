from typing import Dict

# Fixed conversion rates (assumed for now)
RATES = {
    "GBP": 41.5,
    "JPY": 0.21,
    "USD": 32.5,
    "TWD": 1.0,
}

DEFAULT_SHIPPING_TWD = 800.0
IMPORT_TAX_RATE = 0.17  # 17%


def convert_to_twd(amount: float, currency: str) -> float:
    rate = RATES.get(currency.upper(), None)
    if rate is None:
        # fallback: treat as USD
        rate = RATES["USD"]
    return round(amount * rate, 2)


def calculate_landed_cost(original_price: float, currency: str, shipping_twd: float = None) -> Dict:
    """Return a dict with converted price, shipping, tax and final landed price in TWD."""
    price_twd = convert_to_twd(original_price, currency)
    shipping = DEFAULT_SHIPPING_TWD if shipping_twd is None else float(shipping_twd)
    taxable = price_twd + shipping
    tax = round(taxable * IMPORT_TAX_RATE, 2)
    final = round(price_twd + shipping + tax, 2)
    return {
        "price_twd": price_twd,
        "shipping_twd": shipping,
        "tax_twd": tax,
        "final_price_twd": final,
    }
