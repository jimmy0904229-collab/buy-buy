from backend.utils.calc import convert_to_twd, calculate_landed_cost


def test_convert():
    assert convert_to_twd(1, 'GBP') == 41.5
    assert convert_to_twd(1000, 'JPY') == 210.0
    assert convert_to_twd(10, 'USD') == 325.0


def test_calculate_landed_default_shipping():
    res = calculate_landed_cost(100, 'USD')
    # 100 USD -> 3250 TWD, shipping 800, taxable 4050 -> tax 688.5, final 3250+800+688.5 = 4738.5
    assert res['price_twd'] == 3250.0
    assert res['shipping_twd'] == 800.0
    assert round(res['tax_twd'], 2) == round((3250.0 + 800.0) * 0.17, 2)
    assert round(res['final_price_twd'], 2) == round(3250.0 + 800.0 + res['tax_twd'], 2)
