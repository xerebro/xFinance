from backend.app.core.parsers.ptr_house import parse_ptr_house_html


def test_parse_ptr_house_html_extracts_rows():
    html = """
    <table>
      <tr>
        <th>Date</th><th>Owner</th><th>Security</th><th>Type</th><th>Amount</th>
      </tr>
      <tr>
        <td>01/15/2024</td>
        <td>John Doe</td>
        <td>Company Inc. (XYZ)</td>
        <td>Purchase</td>
        <td>$1,001 - $15,000</td>
      </tr>
    </table>
    """
    rows = parse_ptr_house_html(html)
    assert len(rows) == 1
    row = rows[0]
    assert row["ticker"] == "XYZ"
    assert row["amount_lo"] == 1001.0
    assert row["amount_hi"] == 15000.0
