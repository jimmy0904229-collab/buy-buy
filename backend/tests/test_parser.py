import backend.utils.parser as parser


def test_parse_twd():
    amt, cur, assumed, twd = parser.parse_currency('NT$ 1200')
    assert cur == 'TWD'
    assert twd == 1200
    assert assumed is False


def test_parse_usd_symbol_assumed():
    amt, cur, assumed, twd = parser.parse_currency('$100')
    assert cur == 'USD'
    assert assumed is True
    assert twd == int(round(100 * 32.5))


def test_parse_usd_explicit():
    amt, cur, assumed, twd = parser.parse_currency('US$ 50')
    assert cur == 'USD'
    assert assumed is False
    assert twd == int(round(50 * 32.5))


def test_detect_discount_strike():
    serp_item = {'strike_price': '$200', 'price': '$150'}
    price_amt, _, _, price_twd = parser.parse_currency('$150')
    disc_text, pct, strike = parser.detect_discount(serp_item, price_twd)
    assert strike is not None
    assert pct == round((strike - price_twd) / strike * 100)


def test_detect_discount_text():
    serp_item = {'discount': '30% off today!'}
    disc_text, pct, strike = parser.detect_discount(serp_item, 1000)
    assert pct == 30
    assert '30' in disc_text
