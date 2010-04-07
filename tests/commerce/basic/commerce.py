#!/usr/bin/env python
# -*- coding: UTF-8 -*-

from rollyourown import commerce
from basic import models
from decimal import Decimal


def get_amount_tax(instance): 
    """ A function to test callable-passing. """
    return "10.03"

class CartSummary(commerce.Summary):
    items         = commerce.Items(attribute="items", item_amount_from="model.item_price")
    vouchers      = commerce.Items(attribute="vouchers", item_amount_from="self.get_voucher_amount")
    #coupons       = commerce.Items(attribute="coupons", item_amount_from="model.get_amount")

    my_commission = commerce.Extra()
    tax           = commerce.Extra("GST", amount=get_amount_tax, description="15%", included=True)
    discount      = commerce.Extra(verbose_name="Rabatt", description="Mates Rates", amount="-12.23", included=False)
    delivery      = commerce.Extra(verbose_name="self.delivery_name", description="self.delivery_description", amount="self.delivery_amount", included="model.delivery_included")

    items_total   = commerce.Total('items')
    items_pretax  = commerce.Total('items', '-tax')
    vouchers_total= commerce.Total('vouchers')
    total         = commerce.Total()
    total_prevent_negative = commerce.Total(prevent_negative=True)
    custom_total  = commerce.Total('custom_method')

    def delivery_amount(self): 
        return "10.01"
    def delivery_description(self): 
        return "Interstate"
    def delivery_name(self): 
        return "Lieferung"
    def get_amount_my_commission(self): 
        return Decimal("10.00") + Decimal("00.02")
    def get_voucher_amount(self, instance):
        return (-Decimal(instance.percent * self.items_total) / 100).quantize(Decimal("0.01"))

    def custom_method(self, instance):
        return 42

# Old approach
#    def total_items_amount(self, instance):
#        # This may not be supported yet :-(
#        #return instance.items.all().aggregate(total=Sum(F('product__price')*F('quantity')))
#        return sum([i.price for i in instance.items.all()])


class OrderSummary(commerce.Summary):
    delivery = commerce.Extra()
    total    = commerce.Total()

    def get_amount_delivery(self):
        return "15.00"

