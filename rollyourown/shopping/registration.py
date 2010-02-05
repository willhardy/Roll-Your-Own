# -*- coding: UTF-8 -*-


from django.db.models import get_apps
import logging

logging.warning("Registration approach to ModelPurchase API is deprecated. It will be removed before 1.0.")

# This is the name of the shopping module n an app, eg 'shopping' for shopping.py
SHOPPING_MODULE_NAME = "shopping"

class AlreadyRegistered(Exception): pass
class NotRegistered(Exception): pass 

class ShoppingCache(object):
    def __init__(self):
        self.models = {}
        self.discovered = False

    def register(self, model, purchase_class):
        """ Register the given model with the given purchase class definition. """
        if model in self.models:
            raise AlreadyRegistered("The model %s is already registered." % model)
        self.models[model] = purchase_proxy_factory(model, purchase_class)

    def discover(self):
        if self.discovered: 
            return

        for app in get_apps():
            # Try to import shopping module in this app
            app_name = app.__name__.split(".")[:-1]
            module_name = ".".join(app_name + [SHOPPING_MODULE_NAME])
    
            try:
                # Simply importing the module will register the models
                shopping_module = __import__(module_name, '', '', [''])
                logging.debug("Registering shopping module: %s" % module_name)
            except ImportError:
                pass

        self.discovered = True

    def get_model(self, model):
        self.discover()
        try:
            return self.models[model]
        except (KeyError, TypeError):
            raise NotRegistered('%s not in registry (%s)' % (model.__name__, self.models))

def purchase_proxy_factory(model, purchase_class):
    """ Simply creates a proxy model based on the given model, adding the
        functionality specified by the purchase_class. 
    """

    class Meta:
        proxy = True

    def init(self, *args, **kwargs):
        model.__init__(self, *args, **kwargs)
        self._shopping = purchase_class(instance=self)

    attrs = {'Meta': Meta, '__init__': init, '__module__': model.__module__ }
    name = 'Shopping%s' % model.__name__
    new_class = type(name, (model,), attrs)

    return new_class

registry = ShoppingCache()
