"""
Mini boutique — calcul du panier.
Version corrigée.
"""

import decimal
from decimal import Decimal


def calculate_order_total(prices: list[float], discount: float = 0.0) -> float:
    """Calcule le total d'une commande (avec remise [0..1])."""
    if discount < 0 or discount > 1:
        raise ValueError("discount doit être compris entre 0 et 1")
    subtotal = Decimal('0.0')
    for price in prices:
        subtotal = subtotal + Decimal(str(price))   # CORRIGÉ
    return float(subtotal * (Decimal('1') - Decimal(str(discount))))
