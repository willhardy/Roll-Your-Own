# -*- coding: UTF-8 -*-


# TODO:
#       prevent negative amounts in totals, if desired.
#       I imagine this could be just a prevent_negative=True attribute to the total, 
#       that if set turns negative values into zero.

from django.db.models.base import ModelBase, Model
from decimal import Decimal
from django.core.exceptions import FieldError
import logging


class NotSet(object):
    """ Singleton class to flag when a value hasn't been set (if None is a valid value).  """
    def __str__(self): return "NotSet"
    def __repr__(self): return self.__str__()
NotSet = NotSet()


class ExtraDescriptor(object):
    def __init__(self, extra):
        self.extra = extra

    def __get__(self, obj, type=None):
        if obj is None:
            raise AttributeError('Can only be accessed via an instance.')

        if self.extra.name not in obj.__dict__:
            model_instance = obj._model_instance
            obj.__dict__[self.extra.name] = BoundExtra(model_instance, self.extra)
        return obj.__dict__[self.extra.name]

    def __set__(self, obj, value):
        pass


class BoundExtra(object):
    def __init__(self, instance, extra):
        self._extra        = extra
        self._instance     = instance
        purchase_instance  = instance._shopping
        self._verbose_name = get_referenced_method(self._extra.verbose_name, self._instance, purchase_instance)
        self._amount       = get_referenced_method(self._extra.amount, self._instance, purchase_instance)
        self._description  = get_referenced_method(self._extra.description, self._instance, purchase_instance)
        self._included     = get_referenced_method(self._extra.included, self._instance, purchase_instance)

    verbose_name = property(lambda s:s.resolve_value(s._verbose_name))
    amount       = property(lambda s:Decimal(s.resolve_value(s._amount))) # Might want to validate for a more usable error message when amount is not set
    description  = property(lambda s:s.resolve_value(s._description))
    included     = property(lambda s:s.resolve_value(s._included))

    def resolve_value(self, value):
        """ Generic accessor returning a value, calling it if possible. 
        """
        if callable(value):
            try:
                return value(self._instance)
            except TypeError, e: 
                return value()
        else:
            return value


class Extra(object):
    """ Describes an extra cost or discount, providing access to related information. 
        Currently it stores a verbose_name (ie "tax"), description (ie "10% VAT") and amount ("10.23").
        These attributes can of course point to functions, which provide the relevant inforamtion.
    """

    def __init__(self, verbose_name=NotSet, amount=NotSet, description=NotSet, included=False):
        self.name = None
        self.verbose_name = verbose_name
        self.amount = amount
        self.description = description
        self.included = included
        #display = None # For the future
        #currency = None # For the future

    def __unicode__(self):
        return self.verbose_name

    def __str__(self):
        return str(self.__unicode__())

    def __repr__(self):
        return self.__str__()

    def contribute_to_class(self, cls, name):
        self.name = name

        # Fill in values that are not set
        if self.verbose_name is NotSet:
            self.verbose_name = " ".join(name.lower().split("_"))
        if self.description is NotSet:
            self.description = None
        if self.amount is NotSet:
            self.amount = "self.get_amount_%s" % name

        setattr(cls, name, ExtraDescriptor(self))


def get_referenced_method(value, model_instance, purchase_instance):
    """ This allows instance objects to be referenced by string.
        If the value of an attribute is a string eg "model.my_funky_method", 
        and this method exists on the model instance, then the method is used.
    """
    if isinstance(value, basestring):
        if value.startswith("self.") and hasattr(purchase_instance, value[5:]):
            return getattr(purchase_instance, value[5:])
        elif value.startswith("model.") and hasattr(model_instance, value[6:]):
            return getattr(model_instance, value[6:])
        
    return value


class TotalDescriptor(object):
    def __init__(self, total):
        self.total = total

    def __get__(self, obj, type=None):
        if obj is None:
            raise AttributeError('Can only be accessed via an instance.')
        model_instance = obj._model_instance
        return self.total.get_total(model_instance)

    def __set__(self, obj, value):
        pass


class Total(object):
    """ Describes a set of items to be included.
    """
    def __init__(self, *args, **kwargs):
        self.attributes = args
        self.prevent_negative = kwargs.get('prevent_negative', False)
        self.name = None

    def contribute_to_class(self, cls, name):
        self.name = name
        setattr(cls, name, TotalDescriptor(self))

    def get_total(self, instance):
        purchase_instance = instance._shopping

        if self.attributes:
            items = dict([(name,getattr(purchase_instance, name)) for name in purchase_instance._items if name in self.attributes])
            extras = dict([(name,getattr(purchase_instance, name)) for name in purchase_instance._extras if name in self.attributes])
            removed_extras = dict([(name,getattr(purchase_instance, name)) for name in purchase_instance._extras if '-%s'%name in self.attributes])
        else:
            items = dict([(name,getattr(purchase_instance, name)) for name in purchase_instance._items])
            extras = dict([(name,getattr(purchase_instance, name)) for name in purchase_instance._extras])
            removed_extras = {}

        total = Decimal(0)

        # Sum all the items
        for name, queryset in items.items():
            item_total = sum([i.AMOUNT or Decimal('0') for i in queryset])
            logging.debug("Adding %s (%s) to the total" % (name, item_total))
            total += item_total

        # Sum all the extras
        for name in purchase_instance._extras:
            value = getattr(purchase_instance, name)
            # Add the amount of any extras that are not already included in the total
            if name in extras and value.included is False:
                logging.debug("Adding %s (%s) to the total" % (name, value.amount))
                total += value.amount or Decimal(0)
            elif name in removed_extras and value.included is True:
                logging.debug("Removing %s (%s) from the total" % (name, value.amount))
                total -= value.amount or Decimal(0)
            # The following automatic removal has now been replaced with explicit removal
            ## Remove the amount of any extras that are already included in the total
            #elif name not in extras and value.included is True:
            #    logging.debug("Removing %s (%s) from the total" % (name, value.amount))
            #    total -= value.amount or Decimal(0)

        if self.prevent_negative and total < 0:
            total = Decimal(0)

        return total


class Items(object):
    """ Describes a set of items to be included.
    """
    def __init__(self, attribute=NotSet, item_amount_from=NotSet):
        self.attribute = attribute
        self.item_amount_from = item_amount_from
        self.name = None

    def contribute_to_class(self, cls, name):
        self.name = name
        setattr(cls, name, ItemsDescriptor(self))


class ItemsDescriptor(object):

    def __init__(self, items):
        self.items = items

    def __get__(self, obj, type=None):
        if obj is None:
            raise AttributeError('Can only be accessed via an instance.')

        if self.items.name in obj._cache:
            return obj._cache[self.items.name]

        model_instance = obj._model_instance

        # If this is a ManyToMany field with a "through=" model, use that instead of the final model
        field = model_instance._meta.get_field(self.items.attribute)
        if field.rel.through is not None:
            for f in field.rel.through_model._meta.fields:
                if hasattr(f,'rel') and f.rel and f.rel.to == field.related.model:
                    queryset = field.rel.through_model._default_manager.filter(**{f.name: model_instance})
                    break
        # Otherwise, just use django to get the queryset
        else:
            queryset = getattr(model_instance, self.items.attribute).all().select_related()

        for i in queryset:
            purchase_instance = model_instance._shopping
            amount = self.resolve_value(self.get_item_unit_total(self.items.item_amount_from, i, model_instance), model_instance)
            i.AMOUNT = amount

        obj._cache[self.items.name] = queryset
        return queryset

    def get_item_unit_total(self, value, rel_instance, model_instance):
        purchase_instance = model_instance._shopping

        if isinstance(value, basestring):
            if value.startswith("self.") and hasattr(purchase_instance, value[5:]):
                return getattr(purchase_instance, value[5:])(rel_instance)
            elif value.startswith("model.") and hasattr(rel_instance, value[6:]):
                val = getattr(rel_instance, value[6:])
                try:
                    return val(purchase_instance)
                except TypeError:
                    try:
                        return val()
                    except TypeError:
                        return val
        
        return value

    def resolve_value(self, value, model_instance):
        if callable(value):
            try:
                return value(model_instance)
            except TypeError, e: 
                return value()
        else:
            return value


class ModelPurchaseBase(type):

    def add_to_class(cls, name, value):
        if hasattr(value, 'contribute_to_class'):
            value.contribute_to_class(cls, name)
        else:
            setattr(cls, name, value)

    def __new__(cls, name, bases, attrs):
        new_class = super(ModelPurchaseBase, cls).__new__(cls, name, bases, attrs)

        # This will setup and store the extras that will be needed, from which
        # BoundExtra objects can be created at instantiation.
        extras = {}
        items = {}
        totals = {}

        for key, value in attrs.items():
            if isinstance(value, Items):
                items[key] = value
            elif isinstance(value, Extra):
                extras[key] = value
            elif isinstance(value, Total):
                totals[key] = value
            
            attrs.pop(key)
            new_class.add_to_class(key, value)

        new_class.add_to_class('_extras', extras)
        new_class.add_to_class('_items', items)
        new_class.add_to_class('_totals', totals)
        return new_class


class ModelPurchase(object):
    __metaclass__ = ModelPurchaseBase
    _model_instance = None

    def __init__(self, model_instance):
        self._model_instance = model_instance
        self._cache = {}



