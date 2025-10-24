"""Parser for Form 13F XML infoTable documents."""

from __future__ import annotations

from lxml import etree
from pydantic import BaseModel


class InfoTable(BaseModel):
    nameOfIssuer: str
    cusip: str
    value: int
    sshPrnamt: int
    sshPrnamtType: str


def parse_13f_xml(xml_text: str) -> list[InfoTable]:
    root = etree.fromstring(xml_text.encode())
    out: list[InfoTable] = []
    for it in root.findall(".//infoTable"):
        out.append(
            InfoTable(
                nameOfIssuer=it.findtext("nameOfIssuer"),
                cusip=it.findtext("cusip"),
                value=int((it.findtext("value") or "0").replace(",", "")),
                sshPrnamt=int(it.findtext("shrsOrPrnAmt/sshPrnamt") or 0),
                sshPrnamtType=it.findtext("shrsOrPrnAmt/sshPrnamtType") or "SH",
            )
        )
    return out


__all__ = ["parse_13f_xml", "InfoTable"]
