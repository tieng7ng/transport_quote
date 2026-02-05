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

    @staticmethod
    def calculate_transport_price(
        pricing_type: str,
        unit_price: float,
        weight: float,
        origin_country: str = "FR",
        fuel_surcharge_percent: float = 0.0,
        handling_fee_per_100kg: float = 0.0
    ) -> float:
        """
        Calcule le prix final de transport incluant les règles spécifiques (arrondi, fuel, handling).
        """
        price = Decimal("0.00")
        unit_price_dec = PricingService._to_decimal(unit_price)
        weight_dec = PricingService._to_decimal(weight)
        
        # 1. Calcul Base
        if pricing_type == "LUMPSUM":
            price = unit_price_dec
        elif pricing_type == "PER_100KG":
            # Arrondi au 100kg supérieur : ceil(weight / 100) * 100
            rounded_weight = (weight_dec / Decimal("100")).to_integral_value(rounding=ROUND_HALF_UP)
            
            # Si le rounding a arrondi vers le bas (ex 2.4 -> 2), on ajuste car on veut ceil
            # Mais ROUND_HALF_UP sur 2.4 -> 2. 
            import math
            ceil_100 = math.ceil(float(weight) / 100.0)
            
            # Prix = (Poids arrondi / 100) * Prix unitaire
            # Ex: 250kg -> 300kg => 3 * Prix
            price = Decimal(ceil_100) * unit_price_dec
            
        else:
            # Fallback simple
            price = unit_price_dec

        # 2. Handling (Italie ou paramétré)
        # Handling s'applique sur le poids réel ou taxable ? D'après doc: "1,00 € / 100 kg weight" 
        # On suppose poids réel/taxable de l'input
        if handling_fee_per_100kg > 0:
            qty_100 = Decimal(math.ceil(float(weight) / 100.0))
            handling_cost = qty_100 * PricingService._to_decimal(handling_fee_per_100kg)
            price += handling_cost
            
        # 3. Fuel Surcharge
        if fuel_surcharge_percent > 0:
            surcharge = price * (PricingService._to_decimal(fuel_surcharge_percent) / Decimal("100.00"))
            price += surcharge
            
        return float(price.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))
