#!/usr/bin/env python
# -*- coding: UTF-8 -*-

from rollyourown import shopping
from basic import models
from decimal import Decimal


def get_amount_tax(instance): 
    """ A function to test callable-passing. """
    return "10.03"

class CartPurchase(shopping.ModelPurchase):
    items         = shopping.Items(attribute="items", item_amount_from="model.item_price")
    vouchers      = shopping.Items(attribute="vouchers", item_amount_from="self.get_voucher_amount")
    #coupons       = shopping.Items(attribute="coupons", item_amount_from="model.get_amount")

    my_commission = shopping.Extra()
    tax           = shopping.Extra("GST", amount=get_amount_tax, description="15%", included=True)
    discount      = shopping.Extra(verbose_name="Rabatt", description="Mates Rates", amount="-12.23", included=False)
    delivery      = shopping.Extra(verbose_name="self.delivery_name", description="self.delivery_description", amount="self.delivery_amount", included="model.delivery_included")

    items_total   = shopping.Total('items')
    items_pretax  = shopping.Total('items', '-tax')
    vouchers_total= shopping.Total('vouchers')
    total         = shopping.Total()
    total_prevent_negative = shopping.Total(prevent_negative=True)
    custom_total  = shopping.Total('custom_method')

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


class OrderPurchase(shopping.ModelPurchase):
    delivery = shopping.Extra()
    total    = shopping.Total()

    def get_amount_delivery(self):
        return "15.00"


shopping.register(models.Cart, CartPurchase)
shopping.register(models.Order, OrderPurchase)

