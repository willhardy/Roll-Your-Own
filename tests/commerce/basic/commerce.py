#!/usr/bin/env python
# -*- coding: UTF-8 -*-

from rollyourown import commerce
from basic import models
from decimal import Decimal
from forms import DeliveryForm


def get_amount_tax(instance): 
    """ A function to test callable-passing. """
    raise_type_error_when_requested(instance)
    return "10.03"


class CartSummary(commerce.Summary):
    items         = commerce.Items(attribute="items", item_amount_from="model.item_price", editable=True)
    vouchers      = commerce.Items(attribute="vouchers", item_amount_from="self.get_voucher_amount", cache_amount_as="VOUCH_AMOUNT_XYZ")
    payments      = commerce.Items()

    my_commission = commerce.Extra()
    tax           = commerce.Extra("GST", amount=get_amount_tax, description="15%", included=True)
    discount      = commerce.Extra(verbose_name="Rabatt", description="Mates Rates", amount="-12.23", included=False, editable="discount_code")
    delivery      = commerce.Extra(verbose_name="self.delivery_name", description="self.delivery_description", amount="self.delivery_amount", included="model.delivery_included", editable=DeliveryForm)

    items_total   = commerce.Total('items')
    items_pretax  = commerce.Total('items', '-tax')
    vouchers_total= commerce.Total('vouchers')
    total         = commerce.Total()
    total_prevent_negative = commerce.Total(prevent_negative=True)
    custom_total  = commerce.Total('custom_method')
    cached_total  = commerce.Total('items', model_cache="cached_total")

    class Meta:
        locale = "en-AU"
        currency = "EUR"
        decimal_html = '<span class="minor">%(minor)s</span>'

    def delivery_amount(self, instance): 
        raise_type_error_when_requested(self)
        return "10.01"
    def delivery_description(self, instance): 
        raise_type_error_when_requested(self)
        return "Interstate"
    def delivery_name(self, instance): 
        raise_type_error_when_requested(self)
        return "Lieferung"
    def get_amount_my_commission(self, instance): 
        raise_type_error_when_requested(self)
        return Decimal("10.00") + Decimal("00.02")
    def get_voucher_amount(self, instance):
        raise_type_error_when_requested(self)
        return (-Decimal(instance.percent * self.items_total) / 100).quantize(Decimal("0.01"))
    def custom_method(self):
        raise_type_error_when_requested(self)
        return 42


class OrderSummary(commerce.Summary):
    items    = commerce.Items(attribute="items", item_amount_from="model.amount")
    delivery = commerce.Extra()
    total    = commerce.Total()

    def get_amount_delivery(self, instance):
        return "15.00"

class SelfMetaSummary(commerce.Summary):
    class Meta:
        locale = "self.get_locale"
        currency = "self.get_currency"
        decimal_html = 'self.get_decimal_html'

    def get_locale(self, instance):
        return 'de-DE'

    def get_currency(self, instance):
        return 'AUD'

    def get_decimal_html(self, instance):
        return u'1234'


class ModelMetaSummary(commerce.Summary):
    class Meta:
        locale = "model.get_locale"
        currency = "model.get_currency"
        decimal_html = 'model.get_decimal_html'


def raise_type_error_when_requested(obj):
    # Raise TypeError on command
    if getattr(obj, 'raise_type_error', False):
        raise TypeError
