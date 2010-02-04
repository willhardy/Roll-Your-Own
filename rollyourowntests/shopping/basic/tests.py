"""
This file demonstrates two different styles of tests (one doctest and one
unittest). These will both pass when you run "manage.py test".

Replace these with more appropriate tests for your application.
"""

from django.test import TestCase
from rollyourowntests.shopping.basic.models import Cart, Order, Product, CartItem, Voucher
from rollyourowntests.shopping.basic.shopping import CartPurchase, OrderPurchase
from decimal import Decimal

class TestExtras(TestCase):
    def setUp(self):
        cart = Cart.objects.create()
        order = Order.objects.create()

        self.cart = Cart.objects.get(pk=cart.pk)
        self.order = Order.objects.get(pk=order.pk)

        self.cart_purchase = CartPurchase(instance=cart)
        self.order_purchase = OrderPurchase(instance=order)

    def test_extras_creation(self):
        """ Tests that self_purchase is created properly """
        assert hasattr(self.cart_purchase, "my_commission"), "my_commission attribute missing from instance_purchase"
        assert hasattr(self.cart_purchase, "tax"), "tax attribute missing from instance_purchase"
        assert hasattr(self.cart_purchase, "discount"), "discount attribute missing from instance_purchase"
        assert hasattr(self.cart_purchase, "delivery"), "delivery attribute missing from instance_purchase"
        assert hasattr(self.order_purchase, "delivery"), "delivery attribute missing from instance_purchase"


    def test_name_explicit(self):
        """ Tests that the name attribute can be explicitly set."""
        self.assertEqual(self.cart_purchase.discount.verbose_name, u"Rabatt")
        self.assertEqual(self.cart_purchase.tax.verbose_name, u"GST")

    def test_name_default(self):
        """ Tests that the name attribute is set to a sensible default."""
        self.assertEqual(self.cart_purchase.my_commission.verbose_name, u"my commission")

    def test_name_callable(self):
        """ Tests that the name attribute can be set by a callable."""
        #self.assertEqual(self.cart_purchase.delivery.verbose_name(self.cart), u"Lieferung")
        self.assertEqual(self.cart_purchase.delivery.verbose_name, u"Lieferung")

    def test_description_explicit(self):
        """ Tests that the name attribute can be explicitly set."""
        self.assertEqual(self.cart_purchase.discount.description, u"Mates Rates")
        self.assertEqual(self.cart_purchase.tax.description, u"15%")

    def test_description_default(self):
        """ Tests that the description attribute is set to a sensible default."""
        self.assertEqual(self.cart_purchase.my_commission.description, None)

    def test_description_callable(self):
        """ Tests that the description attribute can be set by a callable."""
        #self.assertEqual(self.cart_purchase.delivery.description(self.cart), u"Interstate")
        self.assertEqual(self.cart_purchase.delivery.description, u"Interstate")

    def test_amount_explicit(self):
        """ Tests that the name attribute can be explicitly set."""
        self.assertEqual(self.cart_purchase.discount.amount, Decimal("-12.23"))

    def test_amount_default(self):
        """ Tests that the description attribute is set to a sensible default."""
        #self.assertEqual(self.cart_purchase.my_commission.amount(self.cart), Decimal("10.02"))
        self.assertEqual(self.cart_purchase.my_commission.amount, Decimal("10.02"))
        #self.assertEqual(self.cart_purchase.tax.amount(self.cart), Decimal("10.03"))
        self.assertEqual(self.cart_purchase.tax.amount, Decimal("10.03"))

    def test_amount_callable(self):
        """ Tests that the description attribute can be set by a callable."""
        #self.assertEqual(self.cart_purchase.delivery.amount(self.cart), Decimal("10.01"))
        self.assertEqual(self.cart_purchase.delivery.amount, Decimal("10.01"))

    def test_included_explicit(self):
        """ Tests that the included attribute can be explicitly set."""
        self.assertEqual(self.cart_purchase.discount.included, False)
        self.assertEqual(self.cart_purchase.tax.included, True)

    def test_included_default(self):
        """ Tests that the included attribute is set to a sensible default."""
        self.assertEqual(self.cart_purchase.my_commission.included, False)

    def test_included_callable(self):
        """ Tests that the included attribute can be set by a callable."""
        self.assertEqual(self.cart_purchase.delivery.included, False)

class TestItems(TestCase):

    def setUp(self):
        cart = Cart.objects.create()

        self.product_1 = Product.objects.create(price=Decimal("0.01"))
        self.product_2 = Product.objects.create(price=Decimal("11.22"))
        self.item_1    = CartItem.objects.create(cart=cart, product=self.product_1)
        self.item_2    = CartItem.objects.create(cart=cart, product=self.product_2)

        self.cart = Cart.objects.get(pk=cart.pk)

        self.cart_purchase = CartPurchase(instance=cart)

    def test_items_creation(self):
        assert hasattr(self.cart_purchase, "items"), "items attribute missing from instance_purchase"

    def test_items_simple(self):
        self.assertEqual(len(self.cart_purchase.items), 2)
        self.assertEqual(self.cart_purchase.items[0].pk, self.item_1.pk)
        self.assertEqual(self.cart_purchase.items[1].pk, self.item_2.pk)

    def test_items_total(self):
        self.assertEqual(self.cart_purchase.items_total, Decimal("11.23"))

    def test_items_amount(self):
        voucher = Voucher.objects.create(percent=10)
        self.cart.vouchers.add(voucher)
        self.assertEqual(self.cart_purchase.vouchers_total, Decimal("-1.12"))

class TestTotals(TestCase):

    def setUp(self):
        cart = Cart.objects.create()

        self.product_1 = Product.objects.create(price=Decimal("0.01"))
        self.product_2 = Product.objects.create(price=Decimal("11.22"))
        self.item_1    = CartItem.objects.create(cart=cart, product=self.product_1, quantity=7)
        self.item_2    = CartItem.objects.create(cart=cart, product=self.product_2)

        self.cart = Cart.objects.get(pk=cart.pk)

        self.cart_purchase = CartPurchase(instance=cart)

    def test_total_creation(self):
        """ Tests that self_purchase is created properly """
        assert hasattr(self.cart_purchase, "items_total"), "items_total attribute missing from instance_purchase"
        assert hasattr(self.cart_purchase, "items_pretax"), "items_pretax attribute missing from instance_purchase"
        assert hasattr(self.cart_purchase, "total"), "total attribute missing from instance_purchase"

    def test_pretax(self):
        # product_1 + product_2 - tax
        # 0.07      + 11.22     - 10.03
        self.assertEqual(self.cart_purchase.items_pretax, Decimal("1.26"))

    def test_total(self):
        # product_1 + product_2 + discount + delivery + commission
        # 0.07      + 11.22     + -12.23   + 10.01    + 10.02
        self.assertEqual(self.cart_purchase.total, Decimal("19.09"))

    def test_prevent_negative(self):
        voucher = Voucher.objects.create(percent=200)
        self.cart.vouchers.add(voucher)
        self.assertEqual(self.cart_purchase.total_prevent_negative, Decimal(0))

