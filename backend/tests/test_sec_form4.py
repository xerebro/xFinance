from backend.app.core.parsers.sec_form4 import parse_form4_xml


def test_parse_form4_xml_basic():
    xml = """
    <ownershipDocument>
      <issuer>
        <issuerCik>0000320193</issuerCik>
        <issuerTradingSymbol>AAPL</issuerTradingSymbol>
      </issuer>
      <reportingOwner>
        <reportingOwnerId>
          <rptOwnerName>Tim Cook</rptOwnerName>
        </reportingOwnerId>
        <reportingOwnerRelationship>
          <isDirector>0</isDirector>
          <isOfficer>1</isOfficer>
          <officerTitle>CEO</officerTitle>
        </reportingOwnerRelationship>
      </reportingOwner>
      <nonDerivativeTable>
        <nonDerivativeTransaction>
          <securityTitle><value>Common Stock</value></securityTitle>
          <transactionCoding><transactionCode>P</transactionCode></transactionCoding>
          <transactionDate><value>2024-01-10</value></transactionDate>
          <transactionAmounts>
            <transactionShares><value>100</value></transactionShares>
            <transactionPricePerShare><value>150</value></transactionPricePerShare>
          </transactionAmounts>
        </nonDerivativeTransaction>
      </nonDerivativeTable>
    </ownershipDocument>
    """

    txns = parse_form4_xml(xml)
    assert len(txns) == 1
    txn = txns[0]
    assert txn.issuer_cik == "0000320193"
    assert txn.issuer_ticker == "AAPL"
    assert txn.tx_code == "P"
    assert txn.shares == 100.0
    assert txn.price == 150.0
