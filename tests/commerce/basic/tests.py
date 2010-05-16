"""
This file demonstrates two different styles of tests (one doctest and one
unittest). These will both pass when you run "manage.py test".

Replace these with more appropriate tests for your application.
"""

from django.test import TestCase
from models import Cart, Order, Product, CartItem, Voucher
from commerce import CartSummary, OrderSummary
from decimal import Decimal
from django.db.models import Sum

class TestExtras(TestCase):
    def setUp(self):
        cart = Cart.objects.create()
        order = Order.objects.create()

        self.cart = Cart.objects.get(pk=cart.pk)
        self.order = Order.objects.get(pk=order.pk)

        self.cart_summary = CartSummary(instance=cart)
        self.order_summary = OrderSummary(instance=order)

    def test_extras_creation(self):
        """ Tests that the extras in the summary are created properly """
        assert hasattr(self.cart_summary, "my_commission"), "my_commission attribute missing from instance_summary"
        assert hasattr(self.cart_summary, "tax"), "tax attribute missing from instance_summary"
        assert hasattr(self.cart_summary, "discount"), "discount attribute missing from instance_summary"
        assert hasattr(self.cart_summary, "delivery"), "delivery attribute missing from instance_summary"
        assert hasattr(self.order_summary, "delivery"), "delivery attribute missing from instance_summary"


    def test_name_explicit(self):
        """ Tests that the name attribute can be explicitly set."""
        self.assertEqual(self.cart_summary.discount.verbose_name, u"Rabatt")
        self.assertEqual(self.cart_summary.tax.verbose_name, u"GST")

    def test_name_default(self):
        """ Tests that the name attribute is set to a sensible default."""
        self.assertEqual(self.cart_summary.my_commission.verbose_name, u"My commission")

    def test_name_callable(self):
        """ Tests that the name attribute can be set by a callable."""
        self.assertEqual(self.cart_summary.delivery.verbose_name, u"Lieferung")

    def test_description_explicit(self):
        """ Tests that the name attribute can be explicitly set."""
        self.assertEqual(self.cart_summary.discount.description, u"Mates Rates")
        self.assertEqual(self.cart_summary.tax.description, u"15%")

    def test_description_default(self):
        """ Tests that the description attribute is set to a sensible default."""
        self.assertEqual(self.cart_summary.my_commission.description, None)

    def test_description_callable(self):
        """ Tests that the description attribute can be set by a callable."""
        self.assertEqual(self.cart_summary.delivery.description, u"Interstate")

    def test_amount_explicit(self):
        """ Tests that the name attribute can be explicitly set."""
        self.assertEqual(self.cart_summary.discount.amount, Decimal("-12.23"))

    def test_amount_default(self):
        """ Tests that the description attribute is set to a sensible default."""
        self.assertEqual(self.cart_summary.my_commission.amount, Decimal("10.02"))
        self.assertEqual(self.cart_summary.tax.amount, Decimal("10.03"))

    def test_amount_callable(self):
        """ Tests that the description attribute can be set by a callable."""
        self.assertEqual(self.cart_summary.delivery.amount, Decimal("10.01"))

    def test_included_explicit(self):
        """ Tests that the included attribute can be explicitly set."""
        self.assertEqual(self.cart_summary.discount.included, False)
        self.assertEqual(self.cart_summary.tax.included, True)

    def test_included_default(self):
        """ Tests that the included attribute is set to a sensible default."""
        self.assertEqual(self.cart_summary.my_commission.included, False)

    def test_included_callable(self):
        """ Tests that the included attribute can be set by a callable."""
        self.assertEqual(self.cart_summary.delivery.included, False)

class TestItems(TestCase):

    def setUp(self):
        cart = Cart.objects.create()

        self.product_1 = Product.objects.create(price=Decimal("0.01"))
        self.product_2 = Product.objects.create(price=Decimal("11.22"))
        self.item_1    = CartItem.objects.create(cart=cart, product=self.product_1)
        self.item_2    = CartItem.objects.create(cart=cart, product=self.product_2)

        self.cart = Cart.objects.get(pk=cart.pk)

        self.cart_summary = CartSummary(instance=cart)

    def test_items_creation(self):
        assert hasattr(self.cart_summary, "items"), "items attribute missing from instance_summary"

    def test_items_simple(self):
        self.assertEqual(len(self.cart_summary.items), 2)
        self.assertEqual(self.cart_summary.items[0].pk, self.item_1.pk)
        self.assertEqual(self.cart_summary.items[1].pk, self.item_2.pk)

    def test_items_total(self):
        self.assertEqual(self.cart_summary.items_total, Decimal("11.23"))

    def test_items_amount(self):
        voucher = Voucher.objects.create(percent=10)
        self.cart.vouchers.add(voucher)
        self.assertEqual(self.cart_summary.vouchers_total, Decimal("-1.12"))

class TestTotals(TestCase):

    def setUp(self):
        self.cart = Cart.objects.create()

        self.product_1 = Product.objects.create(price=Decimal("0.01"))
        self.product_2 = Product.objects.create(price=Decimal("11.22"))
        self.item_1    = CartItem.objects.create(cart=self.cart, product=self.product_1, quantity=7)
        self.item_2    = CartItem.objects.create(cart=self.cart, product=self.product_2)

        self.cart_summary = CartSummary(instance=self.cart)

    def test_total_creation(self):
        """ Tests that self_summary is created properly """
        assert hasattr(self.cart_summary, "items_total"), "items_total attribute missing from instance_summary"
        assert hasattr(self.cart_summary, "items_pretax"), "items_pretax attribute missing from instance_summary"
        assert hasattr(self.cart_summary, "total"), "total attribute missing from instance_summary"

    def test_pretax(self):
        # product_1 + product_2 - tax
        # 0.07      + 11.22     - 10.03
        self.assertEqual(self.cart_summary.items_pretax, Decimal("1.26"))

    def test_total(self):
        # product_1 + product_2 + discount + delivery + commission
        # 0.07      + 11.22     + -12.23   + 10.01    + 10.02
        self.assertEqual(self.cart_summary.total, Decimal("19.09"))

    def test_prevent_negative(self):
        voucher = Voucher.objects.create(percent=200)
        self.cart.vouchers.add(voucher)
        self.assertEqual(self.cart_summary.total_prevent_negative, Decimal(0))

    def test_custom_total(self):
        """ Tests a total calculated using a custom method. """
        self.assertEqual(self.cart_summary.custom_total, 42)

    def test_custom_method(self):
        """ Tests that access to custom methods/properties/attribtues is enabled. """
        self.assertEqual(self.cart_summary.custom_method(self.cart_summary.instance), 42)

    def test_model_cache(self):
        """ Checks that summary total is saved to the model instance. """
        cached_total = self.cart_summary.cached_total
        self.assertEqual(self.cart.cached_total, cached_total)

    def test_model_cache_aggregation(self):
        """ Checks that aggregation works with cached summary totals. """
        # Add another model instance and test aggregation
        cart2 = Cart.objects.create()
        item_1    = CartItem.objects.create(cart=cart2, product=self.product_1)
        cart_summary2 = CartSummary(instance=cart2)

        cached_total = self.cart_summary.cached_total + cart_summary2.cached_total
        self.cart.save()
        cart2.save()

        self.assertEqual(cached_total, Cart.objects.all().aggregate(cached_sum=Sum('cached_total'))['cached_sum'])


class TestGeneral(TestCase):

    def setUp(self):
        self.cart = Cart.objects.create()

        self.product_1 = Product.objects.create(price=Decimal("0.01"), name="Product One")
        self.product_2 = Product.objects.create(price=Decimal("10011.22"), name="Product Two")
        self.item_1    = CartItem.objects.create(cart=self.cart, product=self.product_1, quantity=7)
        self.item_2    = CartItem.objects.create(cart=self.cart, product=self.product_2)

        self.cart_summary = CartSummary(instance=self.cart)

    def test_unicode(self):
        """ Tests the standard unicode output of a summary.  """
        self.assertEqual(unicode(self.cart_summary), u"""
7x Product One              0.07
1x Product Two          10011.22

Lieferung (Interstate)     10.01
Rabatt (Mates Rates)      -12.23
My commission              10.02
GST (15%)                  10.03

        Vouchers total      0.00
                 Total  10019.09
          Custom total     42.00
           Items total  10011.29
          Cached total  10011.29
Total prevent negative  10019.09
          Items pretax  10001.26
""".lstrip())
