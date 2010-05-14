from django.db import models
from datetime import datetime
from decimal import Decimal

class Product(models.Model):
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)

class Cart(models.Model):
    items        = models.ManyToManyField(Product, through="CartItem")
    vouchers     = models.ManyToManyField('Voucher')
    date_created = models.DateTimeField(default=datetime.now)
    cached_total = models.DecimalField(max_digits=10, decimal_places=2, editable=False, blank=True, null=True)

    def delivery_included(self): 
        return False

class CartItem(models.Model):
    product  = models.ForeignKey(Product)
    cart     = models.ForeignKey(Cart)
    quantity = models.PositiveSmallIntegerField(default=1)

    def item_price(self, instance):
        return self.product.price * self.quantity

class Order(models.Model):
    items        = models.ManyToManyField(Product, through="OrderItem")
    vouchers     = models.ManyToManyField('Voucher')
    date_created = models.DateTimeField(default=datetime.now)

class OrderItem(models.Model):
    product = models.ForeignKey(Product)
    order   = models.ForeignKey(Order)
    quantity = models.PositiveSmallIntegerField(default=1)

class Voucher(models.Model):
    percent = models.DecimalField(max_digits=5, decimal_places=2)
