from typing import Optional

# small canonicalization mapping; expand as needed
CANONICAL = {
    'end.': 'End Clothing',
    'end clothing': 'End Clothing',
    'endclothing': 'End Clothing',
    'ssense': 'SSENSE',
    'ssense.com': 'SSENSE',
    'farfetch': 'Farfetch',
}


def normalize_retailer(name: Optional[str]) -> str:
    if not name:
        return 'Retailer'
    key = name.strip().lower()
    # remove domain scheme
    key = key.replace('https://', '').replace('http://', '').split('/')[0]
    key = key.replace('www.', '')
    key = key.replace('-', ' ').strip()
    return CANONICAL.get(key, name.strip())
