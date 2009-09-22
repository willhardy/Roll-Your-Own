
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

