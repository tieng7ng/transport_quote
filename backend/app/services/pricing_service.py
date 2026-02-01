from decimal import Decimal, ROUND_HALF_UP
from typing import Optional, Tuple

class PricingService:
    """
    Service centralisant la logique de calcul de prix et de marges.
    Utilise Decimal pour la précision monétaire.
    """

    @staticmethod
    def _to_decimal(value: float) -> Decimal:
        if value is None:
            return Decimal("0.00")
        return Decimal(str(value))

    @staticmethod
    def calculate_sell_price(cost_price: float, margin_percent: float) -> float:
        """
        Calcule le prix de vente basé sur le prix d'achat et la marge en %.
        Formule : Sell = Cost * (1 + Margin/100)
        """
        cost = PricingService._to_decimal(cost_price)
        margin = PricingService._to_decimal(margin_percent)
        
        sell_price = cost * (Decimal("1.00") + (margin / Decimal("100.00")))
        return float(sell_price.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))

    @staticmethod
    def calculate_margin_percent(cost_price: float, sell_price: float) -> float:
        """
        Calcule le % de marge basé sur prix d'achat et vente.
        Formule : Margin % = ((Sell / Cost) - 1) * 100
        """
        cost = PricingService._to_decimal(cost_price)
        sell = PricingService._to_decimal(sell_price)

        if cost == 0:
            return 100.0 if sell > 0 else 0.0

        margin = ((sell / cost) - Decimal("1.00")) * Decimal("100.00")
        return float(margin.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))

    @staticmethod
    def calculate_margin_amount(cost_price: float, sell_price: float) -> float:
        """
        Calcule le montant de la marge.
        """
        cost = PricingService._to_decimal(cost_price)
        sell = PricingService._to_decimal(sell_price)
        
        margin_amount = sell - cost
        return float(margin_amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))
