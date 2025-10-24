from backend.app.core.normalizers.transactions import compute_amount, normalize_ptr_record


def test_compute_amount():
    assert compute_amount(10, 5) == 50
    assert compute_amount(None, 5) is None


def test_normalize_ptr_record():
    record = normalize_ptr_record(
        {
            "tx_date": "01/05/2024",
            "action": "Sale (Partial)",
            "ticker": "ABC",
            "amount": "$15,001 - $50,000",
            "security": "ABC Corp",
        }
    )
    assert record.action == "sell"
    assert record.amount == 50000.0
    assert record.ticker == "ABC"
