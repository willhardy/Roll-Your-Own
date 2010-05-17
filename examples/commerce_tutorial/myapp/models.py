from django.db import models

class Product(models.Model):
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)

class Cart(models.Model):
    items        = models.ManyToManyField(Product, through="CartItem")

class CartItem(models.Model):
    product  = models.ForeignKey(Product)
    cart     = models.ForeignKey(Cart)
    quantity = models.PositiveIntegerField(default=1)

    def get_item_amount(self, instance):
        return self.product.price * self.quantity

    def __unicode__(self):
        return "%dx %s" % (self.quantity, self.product.name)
