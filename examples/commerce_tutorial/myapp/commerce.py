from rollyourown import commerce

from decimal import Decimal

class CartSummaryA(commerce.Summary):
    items    = commerce.Items(attribute="items", item_amount_from="model.get_item_amount")
    delivery = commerce.Extra()
    total    = commerce.Total()

    def get_amount_delivery(self, instance):
        return "10.00"


class CartSummaryB(commerce.Summary):
    items     = commerce.Items(attribute="items", item_amount_from="model.get_item_amount")
    delivery  = commerce.Extra()
    subtotal  = commerce.Total('items')
    total     = commerce.Total()

    def get_amount_delivery(self, instance):
        return (self.subtotal / 10).quantize(Decimal("0.00"))

