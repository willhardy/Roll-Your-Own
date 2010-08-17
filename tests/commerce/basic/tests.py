"""
This file demonstrates two different styles of tests (one doctest and one
unittest). These will both pass when you run "manage.py test".

Replace these with more appropriate tests for your application.
"""

from django.test import TestCase
from models import Cart, Order, Product, CartItem, Voucher
from commerce import CartSummary, OrderSummary, SelfMetaSummary, ModelMetaSummary
from decimal import Decimal
from django.db.models import Sum
from django.utils.datastructures import SortedDict


class Extras(TestCase):
    def setUp(self):
        self.cart = Cart.objects.create()
        self.order = Order.objects.create()

        self.cart_summary = CartSummary(instance=self.cart)
        self.order_summary = OrderSummary(instance=self.order)

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

    def test_editable(self):
        """ Tests that a form is provided. """
        form = self.cart_summary.form()
        data = {'items-TOTAL_FORMS': 0,
                'items-INITIAL_FORMS': 0,
                'items-MAX_NUM_FORMS': '',
                'delivery-address': '123 Main St',
                'discount_code': 'CDE',
                }

        form = self.cart_summary.form(data)
        assert form.is_valid(), str(form.errors)
        form.save()
        self.assertEqual(self.cart.discount_code, 'CDE')
        self.assertEqual(self.cart.address, '123 Main St')

    def test_editable_errors(self):
        form = self.cart_summary.form()
        data = {'items-TOTAL_FORMS': 0,
                'items-INITIAL_FORMS': 0,
                'items-MAX_NUM_FORMS': '',
                # 'delivery-address' missing
                'discount_code': 'CDE',
                }

        form = self.cart_summary.form(data)
        assert form.errors, "No error raised for form"

class Items(TestCase):

    def setUp(self):
        self.cart = Cart.objects.create()

        self.product_1 = Product.objects.create(price=Decimal("0.01"), name="ABC")
        self.product_2 = Product.objects.create(price=Decimal("11.22"), name="CDE")
        self.item_1    = CartItem.objects.create(cart=self.cart, product=self.product_1)
        self.item_2    = CartItem.objects.create(cart=self.cart, product=self.product_2)

        self.cart_summary = CartSummary(self.cart)

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

    def test_cache_item_as(self):
        voucher = Voucher.objects.create(percent=10)
        self.cart.vouchers.add(voucher)
        total_one = self.cart_summary.vouchers_total
        self.assertEqual(self.cart_summary.vouchers[0].VOUCH_AMOUNT_XYZ, Decimal("-1.12"))

        # Change the total, and check that the old one was cached
        total_one = self.cart_summary.vouchers_total
        Voucher.objects.all().update(percent=50)
        total_two = self.cart_summary.vouchers_total
        self.assertEqual(total_one, total_two)

    def test_editable_table(self):
        form = self.cart_summary.form()
        self.assertEqual(form.as_table(), "")

    def test_editable_table_data(self):
        form = self.cart_summary.form()
        data = form.table_data()
        assert data
        self.assertEqual(len(data), len(self.cart_summary._meta.elements))
        self.assertEqual(len(data[0]), 3)
        element_names = self.cart_summary._meta.elements.keys()
        self.assertEqual([i[0] for i in data], element_names)
        self.assertEqual([i[2] for i in data], [getattr(self.cart_summary, n) for n in element_names])
        

class Totals(TestCase):

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
        self.assertEqual(self.cart_summary.custom_method(), 42)

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


class GeneralTests(TestCase):

    def setUp(self):
        self.cart = Cart.objects.create()
        self.order = Order.objects.create()

        self.product_1 = Product.objects.create(price=Decimal("0.01"), name="Product One")
        self.product_2 = Product.objects.create(price=Decimal("10011.22"), name="Product Two")
        self.item_1    = CartItem.objects.create(cart=self.cart, product=self.product_1, quantity=7)
        self.item_2    = CartItem.objects.create(cart=self.cart, product=self.product_2)

        self.cart_summary = CartSummary(instance=self.cart)
        self.order_summary = OrderSummary(instance=self.cart)
        self.self_meta_summary = SelfMetaSummary(instance=self.cart)
        self.model_meta_summary = ModelMetaSummary(instance=self.cart)

    def test_unicode(self):
        """ Tests the standard unicode output of a summary.  """
        self.assertEqual(unicode(self.cart_summary), u"""
7x Product One              0.07
1x Product Two          10011.22

My commission              10.02
GST (15%)                  10.03
Rabatt (Mates Rates)      -12.23
Lieferung (Interstate)     10.01

           Items total  10011.29
          Items pretax  10001.26
        Vouchers total      0.00
                 Total  10019.09
Total prevent negative  10019.09
          Custom total     42.00
          Cached total  10011.29
""".lstrip())

    def test_meta(self):
        """ Checks that a meta attribute is created. """
        assert hasattr(self.cart_summary, '_meta'), 'No _meta attribute created when specified'
        assert hasattr(self.order_summary, '_meta'), 'No _meta attribute created automatically'
        assert hasattr(self.self_meta_summary, '_meta'), 'No _meta attribute created when specified'
        assert hasattr(self.model_meta_summary, '_meta'), 'No _meta attribute created when specified'

    def test_meta_locale(self):
        """ Checks that the locale is made available. """
        self.assertEqual(self.cart_summary._meta.locale, "en-AU")
        self.assertEqual(self.order_summary._meta.locale, None)
        self.assertEqual(self.self_meta_summary._meta.locale, "de-DE")
        self.assertEqual(self.model_meta_summary._meta.locale, "fr-FR")

    def test_meta_currency(self):
        """ Checks that the currency is made available. """
        self.assertEqual(self.cart_summary._meta.currency, "EUR")
        self.assertEqual(self.order_summary._meta.currency, None)
        self.assertEqual(self.self_meta_summary._meta.currency, "AUD")
        self.assertEqual(self.model_meta_summary._meta.currency, "USD")

    def test_meta_decimal_html(self):
        """ Checks that the decimal html format is made available. """
        self.assertEqual(self.cart_summary._meta.decimal_html, 
                         '<span class="minor">%(minor)s</span>')
        self.assertEqual(self.order_summary._meta.decimal_html, None)
        self.assertEqual(self.self_meta_summary._meta.decimal_html, u'1234')
        self.assertEqual(self.model_meta_summary._meta.decimal_html, u'5678')

    def test_meta_items(self):
        """ Checks that the items are correctly provided, including ordering. """
        self.assertEqual(self.cart_summary._meta.items.keys(), 
                        ['items', 'vouchers', 'payments'])
        self.assertEqual(self.order_summary._meta.items.keys(), ['items'])

    def test_meta_extras(self):
        """ Checks that the extras are correctly provided, including ordering. """
        self.assertEqual(self.cart_summary._meta.extras.keys(), 
                        ['my_commission', 'tax', 'discount', 'delivery'])
        self.assertEqual(self.order_summary._meta.extras.keys(), 
                        ['delivery'])

    def test_meta_totals(self):
        """ Checks that the totals are correctly provided, including ordering. """
        self.assertEqual(self.cart_summary._meta.totals.keys(), 
                        ['items_total', 'items_pretax', 'vouchers_total', 'total', 
                        'total_prevent_negative', 'custom_total', 'cached_total'])
        self.assertEqual(self.order_summary._meta.totals.keys(), 
                        ['total'])

    def test_meta_elements(self):
        """ Checks that an elements attribute is creating with the correct ordering. """
        self.assertEqual(self.cart_summary._meta.elements.keys(), 
                        ['items', 'vouchers', 'payments',
                        'my_commission', 'tax', 'discount', 'delivery',
                        'items_total', 'items_pretax', 'vouchers_total', 'total', 
                        'total_prevent_negative', 'custom_total', 'cached_total'])
        self.assertEqual(self.order_summary._meta.elements.keys(), 
                        ['items', 'delivery', 'total'])

    def test_non_model(self):
        class FakeModel(object):
            pass
        class FakeItem(object):
            quantity = 1
            amount = 4
            def __unicode__(self):
                return "Fake Product"
        fake_model = FakeModel()
        fake_model.items = [FakeItem(), FakeItem()]
        fake_model.vouchers = []
        summary = OrderSummary(fake_model)
        self.assertEqual(unicode(summary), u"""
Fake Product   4.00
Fake Product   4.00

Delivery      15.00

       Total  23.00
""".lstrip())
        


class RegressionTests(TestCase):
    def setUp(self):
        self.cart = Cart.objects.create()

        self.product_1 = Product.objects.create(price=Decimal("0.01"))
        self.product_2 = Product.objects.create(price=Decimal("11.22"))
        self.item_1    = CartItem.objects.create(cart=self.cart, product=self.product_1)
        self.item_2    = CartItem.objects.create(cart=self.cart, product=self.product_2)

        self.cart_summary = CartSummary(instance=self.cart)

    def issue01_test_type_error(self):
        """ Issue #1: TypeErrors in functions should not be caught. """
        self.cart.raise_type_error = True
        cart_summary = CartSummary(instance=self.cart)
        self.assertRaises(TypeError, lambda: cart_summary.tax.amount)

        cart_summary = CartSummary(instance=self.cart)
        self.cart_summary.raise_type_error = True
        self.assertRaises(TypeError, lambda: self.cart_summary.delivery.amount)

        cart_summary = CartSummary(instance=self.cart)
        self.cart_summary.raise_type_error = True
        self.assertRaises(TypeError, lambda: self.cart_summary.my_commission.amount)

        cart_summary = CartSummary(instance=self.cart)
        self.cart_summary.raise_type_error = True
        self.assertRaises(TypeError, lambda: self.cart_summary.custom_total)

