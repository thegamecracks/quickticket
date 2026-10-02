from enum import StrEnum
from typing import Any

from pydantic import BaseModel
from sqlalchemy import JSON, Dialect, TypeDecorator
from sqlalchemy.dialects.postgresql import JSONB

__all__ = (
    "Currency",
    "Money",
    "MoneySerializer",
)


class Currency(StrEnum):
    """An enumeration of supported Stripe currencies.

    https://docs.stripe.com/currencies#presentment-currencies
    Last updated: 2026-10-01

    """

    USD = "USD"
    AED = "AED"
    AFN = "AFN"  # not supported by American Express
    ALL = "ALL"
    AMD = "AMD"
    ANG = "ANG"
    AOA = "AOA"  # not supported by American Express
    ARS = "ARS"  # not supported by American Express
    AUD = "AUD"
    AWG = "AWG"
    AZN = "AZN"
    BAM = "BAM"
    BBD = "BBD"
    BDT = "BDT"
    BIF = "BIF"
    BMD = "BMD"
    BND = "BND"
    BOB = "BOB"  # not supported by American Express
    BRL = "BRL"  # not supported by American Express
    BSD = "BSD"
    BWP = "BWP"
    BYN = "BYN"
    BZD = "BZD"
    CAD = "CAD"
    CDF = "CDF"
    CHF = "CHF"
    CLP = "CLP"  # not supported by American Express
    CNY = "CNY"
    COP = "COP"  # not supported by American Express
    CRC = "CRC"  # not supported by American Express
    CVE = "CVE"  # not supported by American Express
    CZK = "CZK"
    DJF = "DJF"  # not supported by American Express
    DKK = "DKK"
    DOP = "DOP"
    DZD = "DZD"
    EGP = "EGP"
    ETB = "ETB"
    EUR = "EUR"
    FJD = "FJD"
    FKP = "FKP"  # not supported by American Express
    GBP = "GBP"
    GEL = "GEL"
    GIP = "GIP"
    GMD = "GMD"
    GNF = "GNF"  # not supported by American Express
    GTQ = "GTQ"  # not supported by American Express
    GYD = "GYD"
    HKD = "HKD"
    HNL = "HNL"  # not supported by American Express
    HTG = "HTG"
    HUF = "HUF"
    IDR = "IDR"
    ILS = "ILS"
    INR = "INR"
    ISK = "ISK"
    JMD = "JMD"
    JPY = "JPY"
    KES = "KES"
    KGS = "KGS"
    KHR = "KHR"
    KMF = "KMF"
    KRW = "KRW"
    KYD = "KYD"
    KZT = "KZT"
    LAK = "LAK"  # not supported by American Express
    LBP = "LBP"
    LKR = "LKR"
    LRD = "LRD"
    LSL = "LSL"
    MAD = "MAD"
    MDL = "MDL"
    MGA = "MGA"
    MKD = "MKD"
    MMK = "MMK"
    MNT = "MNT"
    MOP = "MOP"
    MUR = "MUR"  # not supported by American Express
    MVR = "MVR"
    MWK = "MWK"
    MXN = "MXN"
    MYR = "MYR"
    MZN = "MZN"
    NAD = "NAD"
    NGN = "NGN"
    NIO = "NIO"  # not supported by American Express
    NOK = "NOK"
    NPR = "NPR"
    NZD = "NZD"
    PAB = "PAB"  # not supported by American Express
    PEN = "PEN"  # not supported by American Express
    PGK = "PGK"
    PHP = "PHP"
    PKR = "PKR"
    PLN = "PLN"
    PYG = "PYG"  # not supported by American Express
    QAR = "QAR"
    RON = "RON"
    RSD = "RSD"
    RUB = "RUB"
    RWF = "RWF"
    SAR = "SAR"
    SBD = "SBD"
    SCR = "SCR"
    SEK = "SEK"
    SGD = "SGD"
    SHP = "SHP"  # not supported by American Express
    SLE = "SLE"
    SOS = "SOS"
    SRD = "SRD"  # not supported by American Express
    STD = "STD"  # not supported by American Express
    SZL = "SZL"
    THB = "THB"
    TJS = "TJS"
    TOP = "TOP"
    TRY = "TRY"
    TTD = "TTD"
    TWD = "TWD"
    TZS = "TZS"
    UAH = "UAH"
    UGX = "UGX"
    UYU = "UYU"  # not supported by American Express
    UZS = "UZS"
    VND = "VND"
    VUV = "VUV"
    WST = "WST"
    XAF = "XAF"
    XCD = "XCD"
    XCG = "XCG"
    XOF = "XOF"  # not supported by American Express
    XPF = "XPF"  # not supported by American Express
    YER = "YER"
    ZAR = "ZAR"
    ZMW = "ZMW"


class Money(BaseModel):
    amount: int
    currency: Currency


class MoneySerializer(TypeDecorator):
    """De/serialize the Money class to and from the database."""

    impl = JSON
    cache_ok = True

    def load_dialect_impl(self, dialect: Dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(JSONB(none_as_null=True))
        else:
            return dialect.type_descriptor(JSON(none_as_null=True))

    def process_bind_param(self, value: Money | None, dialect: Dialect):
        if value is not None:
            return value.model_dump()

    def process_result_value(self, value: Any | None, dialect: Dialect):
        if value is not None:
            return Money.model_validate(value)
