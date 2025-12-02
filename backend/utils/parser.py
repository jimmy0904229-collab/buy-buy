import re
from typing import Dict, Optional, Tuple

# conversion multipliers (matches main rates)
RATES = {
    'GBP': 41.5,
    'JPY': 0.21,
    'USD': 32.5,
    'TWD': 1.0,
}


def _extract_number(text: str) -> float:
    num_re = re.compile(r'([0-9]{1,3}(?:,[0-9]{3})*(?:\.[0-9]+)?|[0-9]+(?:\.[0-9]+)?)')
    m = num_re.search(text)
    if not m:
        return 0.0
    return float(m.group(1).replace(',', ''))


def parse_currency(price_str: str, serp_result: Optional[Dict] = None) -> Tuple[float, str, bool, int]:
    """Strict deterministic parser.

    Returns: (amount, currency_code, assumed_usd_flag, price_twd_int)
    """
    s = (price_str or '')
    text = s.strip()
    assumed = False

    # 1) TWD / NT / HK$
    if re.search(r'(NT\$|\bNT\b|\bTWD\b|HK\$)', text, flags=re.IGNORECASE):
        amt = _extract_number(text)
        return amt, 'TWD', False, int(round(amt))

    # 2) GBP
    if re.search(r'(£|\bGBP\b)', text, flags=re.IGNORECASE):
        amt = _extract_number(text)
        return amt, 'GBP', False, int(round(amt * RATES['GBP']))

    # 3) EUR
    if re.search(r'(€|\bEUR\b)', text, flags=re.IGNORECASE):
        amt = _extract_number(text)
        return amt, 'EUR', False, int(round(amt * 34.0))

    # 4) JPY
    if re.search(r'(¥|\bJPY\b)', text, flags=re.IGNORECASE):
        amt = _extract_number(text)
        return amt, 'JPY', False, int(round(amt * RATES['JPY']))

    # 5) USD explicit
    if re.search(r'(US\$|\bUSD\b)', text, flags=re.IGNORECASE):
        amt = _extract_number(text)
        return amt, 'USD', False, int(round(amt * RATES['USD']))

    # 6) ambiguous $
    if '$' in text:
        if re.fullmatch(r'\$\s*[0-9,]+(?:\.[0-9]+)?', text):
            amt = _extract_number(text)
            return amt, 'USD', True, int(round(amt * RATES['USD']))

        if serp_result:
            combined = ' '.join([str(v) for v in serp_result.values() if isinstance(v, str)])
            if re.search(r'(NT\$|\bTWD\b|\bNT\b)', combined, flags=re.IGNORECASE):
                amt = _extract_number(text)
                return amt, 'TWD', False, int(round(amt))

        amt = _extract_number(text)
        return amt, 'USD', True, int(round(amt * RATES['USD']))

    # fallback: check serp_result hints
    if serp_result:
        combined = ' '.join([str(v) for v in serp_result.values() if isinstance(v, str)])
        if re.search(r'(NT\$|\bTWD\b|\bNT\b)', combined, flags=re.IGNORECASE):
            amt = _extract_number(text)
            return amt, 'TWD', False, int(round(amt))
        if re.search(r'(US\$|\bUSD\b)', combined, flags=re.IGNORECASE):
            amt = _extract_number(text)
            return amt, 'USD', False, int(round(amt * RATES['USD']))

    # final fallback: assume USD but mark assumed
    amt = _extract_number(text)
    return amt, 'USD', True, int(round(amt * RATES['USD']))


def detect_discount(serp_item: Dict, price_twd: int) -> Tuple[Optional[str], Optional[float], Optional[int]]:
    """Try to detect discount from serp result. Returns (text, pct, strike_twd).

    pct is integer percentage if derivable, strike_twd is original price in TWD if found.
    """
    discount_text = None
    discount_pct = None
    strike_twd = None

    # common keys that may contain list/strike price
    for key in ('strike_price', 'original_price', 'price_before', 'list_price', 'before_price', 'retail_price'):
        val = serp_item.get(key)
        if val:
            try:
                amt, cur, assumed, t = parse_currency(str(val), serp_item)
                strike_twd = t
                break
            except Exception:
                continue

    if strike_twd and strike_twd > price_twd:
        try:
            pct = round((strike_twd - price_twd) / strike_twd * 100)
            discount_pct = pct
            discount_text = f"{pct}% off"
        except Exception:
            pass

    if not discount_text:
        for key in ('discount', 'savings', 'discount_text', 'sale'):
            v = serp_item.get(key)
            if v:
                txt = str(v)
                m = re.search(r'([0-9]{1,3})\s?%|([0-9]{1,3})\s?％', txt)
                if m:
                    pct = int(m.group(1) or m.group(2))
                    discount_pct = pct
                    discount_text = f"{pct}% off"
                else:
                    discount_text = txt
                break

    return discount_text, discount_pct, strike_twd
