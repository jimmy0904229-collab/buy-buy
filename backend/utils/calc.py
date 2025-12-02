from typing import Dict

# Fixed conversion rates (assumed for now)
RATES = {
    "GBP": 41.5,
    "JPY": 0.21,
    "USD": 32.5,
    "TWD": 1.0,
}

DEFAULT_SHIPPING_TWD =0
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


def normalize_price_string_to_twd(price_string: str) -> int:
    """Normalize a price string to integer TWD.

    This extracts numeric value and detects currency symbols/keywords. Returns rounded integer TWD.
    """
    if not price_string:
        return 0

    text = str(price_string).strip()

    # NT/TWD explicit
    if 'NT$' in text or 'TWD' in text or text.upper().startswith('NT'):
        m = __import__('re').search(r'([0-9,]+\.?[0-9]*)', text)
        if m:
            try:
                val = float(m.group(1).replace(',', ''))
                return int(round(val))
            except Exception:
                return 0

    # GBP
    if '£' in text or 'GBP' in text.upper():
        m = __import__('re').search(r'£\s*([0-9,]+\.?[0-9]*)', text)
        if not m:
            m = __import__('re').search(r'([0-9,]+\.?[0-9]*)', text)
        if m:
            try:
                val = float(m.group(1).replace(',', ''))
                return int(round(val * RATES['GBP']))
            except Exception:
                return 0

    # JPY
    if '¥' in text or 'JPY' in text.upper():
        m = __import__('re').search(r'[¥\s]*([0-9,]+\.?[0-9]*)', text)
        if m:
            try:
                val = float(m.group(1).replace(',', ''))
                return int(round(val * RATES['JPY']))
            except Exception:
                return 0

    # EUR
    if '€' in text or 'EUR' in text.upper():
        m = __import__('re').search(r'€\s*([0-9,]+\.?[0-9]*)', text)
        if not m:
            m = __import__('re').search(r'([0-9,]+\.?[0-9]*)', text)
        if m:
            try:
                val = float(m.group(1).replace(',', ''))
                return int(round(val * 34.0))
            except Exception:
                return 0

    # USD / $ (but not NT$ which handled above)
    if '$' in text or 'USD' in text.upper():
        m = __import__('re').search(r'\$\s*([0-9,]+\.?[0-9]*)', text)
        if not m:
            m = __import__('re').search(r'([0-9,]+\.?[0-9]*)', text)
        if m:
            try:
                val = float(m.group(1).replace(',', ''))
                return int(round(val * RATES['USD']))
            except Exception:
                return 0

    # fallback: first number as TWD
    m = __import__('re').search(r'([0-9,]+\.?[0-9]*)', text)
    if m:
        try:
            val = float(m.group(1).replace(',', ''))
            return int(round(val))
        except Exception:
            return 0

    return 0
