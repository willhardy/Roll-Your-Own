__test__ = {"doctest": """

Add some data

>>> from myapp.models import Cart, Product, CartItem
>>> guitar = Product.objects.create(name="Guitar", price="329.42")
>>> saxophone = Product.objects.create(name="Saxophone", price="672.23")
>>> triangle = Product.objects.create(name="Triangle", price="4.48")
>>> my_cart = Cart.objects.create()
>>> CartItem.objects.create(product=guitar, cart=my_cart)
<CartItem: 1x Guitar>
>>> CartItem.objects.create(product=triangle, cart=my_cart)
<CartItem: 1x Triangle>
>>> CartItem.objects.create(product=saxophone, cart=my_cart, quantity=3)
<CartItem: 3x Saxophone>

>>> from myapp.commerce import CartSummaryA
>>> cart_summary = CartSummaryA(my_cart)
>>> cart_summary.total
Decimal('2360.59')
>>> print cart_summary
1x Guitar      329.42
1x Triangle      4.48
3x Saxophone  2016.69
<BLANKLINE>
Delivery        10.00
<BLANKLINE>
       Total  2360.59
<BLANKLINE>


>>> from myapp.commerce import CartSummaryB
>>> cart_summary = CartSummaryB(my_cart)
>>> cart_summary.subtotal
Decimal('2350.59')
>>> cart_summary.total
Decimal('2585.65')
>>> cart_summary.delivery.amount
Decimal('235.06')
>>> print cart_summary
1x Guitar      329.42
1x Triangle      4.48
3x Saxophone  2016.69
<BLANKLINE>
Delivery       235.06
<BLANKLINE>
       Total  2585.65
    Subtotal  2350.59
<BLANKLINE>

"""}
