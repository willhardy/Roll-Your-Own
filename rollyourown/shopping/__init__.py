
"""
    This is the main entry point to the shopping framework, applications only
    need to import this module. All publically available functionality should be
    accessible here (except maybe abstract models and utils).

    eg 

    >>> from rollyourown import shopping
    >>> class MyCartPurchase(shopping.ModelPurchase):
    ...     pass
    >>> from myapp.models import MyCart
    >>> shopping.register(MyCart, MyCartPurchase)

"""

__all__ = ( 
            'ModelPurchase', 'Extra', 'Items', 'Total',
            'register', 'get_model', 'get', 
            'inlineformset_factory', 
          )

from registration import registry
from purchase import ModelPurchase, Extra, Items, Total
from forms import inlineformset_factory

SHOPPING_MODEL_SESSION_KEY = 'ROLLYOUROWN_SHOPPING_%s_PK'
SHOPPING_MODEL_SESSION_KEY_OLD = 'ROLLYOUROWN_SHOPPING_%s_PK_OLD'

def register(model, model_purchase):
    registry.register(model, model_purchase)

def get_model(model):
    return registry.get_model(model)

def get(model, request, create=True):
    """ Gets an instance of the given model for this session. 
        For example: cart = get(Cart, request)
    """
    try:
        pk = request.session[SHOPPING_MODEL_SESSION_KEY % model.__name__]
    except KeyError:
        if create:
            instance = model()
            instance.save()
            pk = instance.pk
            request.session[SHOPPING_MODEL_SESSION_KEY % model.__name__] = pk
        else:
            return None

    return get_model(model)._default_manager.get(pk=pk)


def get_previous_from_session(model, request):
    old_order_ids = request.session.get(SHOPPING_MODEL_SESSION_KEY_OLD % model.__name__, set())
    current_order_id = request.session.get(SHOPPING_MODEL_SESSION_KEY % model.__name__, None)
    if current_order_id is not None:
        old_order_ids.add(current_order_id)
    return get_model(model)._default_manager.filter(id__in=old_order_ids)


def clear_current(model, request):
    try:
        order_id = request.session.pop(SHOPPING_MODEL_SESSION_KEY % model.__name__)

        # Add order ID to the list of previous orders
        old_orders = request.session.get(SHOPPING_MODEL_SESSION_KEY_OLD % model.__name__, set())
        old_orders.add(order_id)
        request.session[SHOPPING_MODEL_SESSION_KEY_OLD % model.__name__] = old_orders
    except KeyError:
        pass
