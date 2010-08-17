from django.db import models
from datetime import datetime
from decimal import Decimal

class Product(models.Model):
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)

class Cart(models.Model):
    items        = models.ManyToManyField(Product, through="CartItem")
    payments        = models.ManyToManyField('Payment')
    vouchers     = models.ManyToManyField('Voucher')
    date_created = models.DateTimeField(default=datetime.now)
    cached_total = models.DecimalField(max_digits=10, decimal_places=2, editable=False, blank=True, null=True)
    discount_code = models.CharField(max_length=16, default="", blank=True)
    address       = models.TextField(default="", blank=True)

    def delivery_included(self): 
        return False

    def get_locale(self):
        return 'fr-FR'

    def get_currency(self):
        return 'USD'

    def get_decimal_html(self):
        return u'5678'

class CartItem(models.Model):
    product  = models.ForeignKey(Product)
    cart     = models.ForeignKey(Cart)
    quantity = models.PositiveSmallIntegerField(default=1)

    def item_price(self):
        return self.product.price * self.quantity

    def __unicode__(self):
        if self.product_id:
            return u"%dx %s" % (self.quantity, self.product.name)
        else:
            return u"%dx ?" % (self.quantity, )

class Order(models.Model):
    items         = models.ManyToManyField(Product, through="OrderItem")
    vouchers      = models.ManyToManyField('Voucher')
    date_created  = models.DateTimeField(default=datetime.now)

class OrderItem(models.Model):
    product = models.ForeignKey(Product)
    order   = models.ForeignKey(Order)
    quantity = models.PositiveSmallIntegerField(default=1)

    amount = property(lambda self: self.quantity * self.product.price)

class Voucher(models.Model):
    percent = models.DecimalField(max_digits=5, decimal_places=2)

class Payment(models.Model):
    pass
