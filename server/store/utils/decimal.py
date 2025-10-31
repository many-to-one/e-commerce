from decimal import Decimal

def normalize_products_for_json(products):
    """
    Zamienia obiekty (np. AllegroOrderItem) lub dicty z Decimal
    na JSON-safe dicty (float/int/str).
    """
    normalized = []
    for p in products:
        # jeśli to obiekt modelu, zamień na dict
        if not isinstance(p, dict):
            p = {
                "offer_name": p.offer_name,
                "quantity": int(p.quantity),
                "price_amount": p.price_amount,
                "price_currency": p.price_currency,
                "tax_rate": p.tax_rate,
            }

        normalized.append({
            "offer_name": str(p["offer_name"]),
            "quantity": int(p["quantity"]),
            "price_amount": float(p["price_amount"]) if isinstance(p["price_amount"], Decimal) else p["price_amount"],
            "price_currency": str(p["price_currency"]),
            "tax_rate": float(p.get("tax_rate", 23)),
        })
    return normalized

from decimal import Decimal

def to_decimal_products(products):
    """
    Zamienia JSON-safe dicty (float/int/str) na dicty z Decimal
    do dalszych obliczeń księgowych.
    """
    converted = []
    for p in products:
        converted.append({
            "offer_name": p["offer_name"],
            "quantity": int(p["quantity"]),
            "price_amount": Decimal(str(p["price_amount"])),
            "price_currency": p["price_currency"],
            "tax_rate": Decimal(str(p.get("tax_rate", 23))),
        })
    return converted
