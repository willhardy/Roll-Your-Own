# -*- coding: UTF-8 -*-

"""
    Summary class.

    This class allows an ecommerce system to be summarised. It is defined using
    a declarative syntax, and automates several aspects of ecommerce systems:

        * calculation of totals
        * currency formatting
        * callable handling

    The organisation of this system is designed to be extremely flexible
    and promote good software design. See unit tests and online
    documentation for usage.

    $Revision$

"""

from decimal import Decimal
from django.db.models.base import ModelBase, Model
from django.db.models.fields import FieldDoesNotExist
from rollyourown.commerce.utils import FormattedDecimal
from django.utils.datastructures import SortedDict


class NotSet(object):
    " Singleton class to flag when a value hasn't been set "
    def __str__(self): return "NotSet"
    def __repr__(self): return self.__str__()
NotSet = NotSet()

class SummaryValidationError(Exception):
    " An error raised when validating the summary definition at compile time. "


#
# Extra objects
#
# These describe single amounts that can be added or subtracted from a total,
# such as delivery costs, adjustments or discounts. As their value can be set
# to be calculated dynamically from the model instance, they need to be bound
# at run time, to ensure they have access to the model in question. A
# descriptor is used to perform this task.
#

class ExtraDescriptor(object):
    " Descriptor to handle the lazy access and binding of Extra() objects "

    def __init__(self, extra):
        self.extra = extra

    def __get__(self, obj, type=None):
        if obj is None:
            raise AttributeError('Can only be accessed via an instance.')

        # Bind and add the Extra object
        if self.extra.name not in obj.__dict__:
            obj.__dict__[self.extra.name] = BoundExtra(obj, self.extra)
        return obj.__dict__[self.extra.name]

    def __set__(self, obj, value):
        pass


class BoundExtra(object):
    """ An Extra object, bound to a model instance and therefore able to
        calculate the relevant amount.
        The referenced method, function or value in Extra() can be
        resolved when called.

        TODO: It may be worthwhile caching the resolved values, if
              we're prepared to assume that the model instance will
              no longer change.
              This should be simply a case of moving resolve_value()
              to the __init__ method.

       TODO: Might want to do import time validation, so that a more
             usable error message is shown when the amount is not set
    """
    def __init__(self, summary_instance, extra):
        self._extra        = extra
        self._summary_instance = summary_instance
        self._instance     = summary_instance.instance

        # Get values or functions to be resolved at run time
        self._verbose_name = self.get_referenced_method('verbose_name')
        self._amount       = self.get_referenced_method('amount')
        self._description  = self.get_referenced_method('description')
        self._included     = self.get_referenced_method('included')

    # Resolve values of any callable attributes when accessed.
    verbose_name = property(lambda s:s.resolve_value(s._verbose_name))
    description  = property(lambda s:s.resolve_value(s._description))
    included     = property(lambda s:bool(s.resolve_value(s._included)))

    @property
    def amount(self):
        return FormattedDecimal(self.resolve_value(self._amount),
                            summary_instance=self._summary_instance)

    def resolve_value(self, value):
        """ Generic accessor returning a value, calling it if possible.
            Methods on a model instance are called with no arguments, 
            all other callables are called with the model instance as
            the only argument.
        """
        if callable(value):
            # Is this callable a method on a django Model instance?
            if isinstance(getattr(value, 'im_self', None), Model):
                return value()
            else:
                return value(self._instance)
        else:
            return value

    def __unicode__(self):
        if self.description:
            return u"%s (%s)" % (self.verbose_name, self.description)
        else:
            return self.verbose_name

    def get_referenced_method(self, attribute):
        """ This allows instance objects to be referenced by string. If the
            value of an attribute is a string eg "model.my_funky_method", and
            this method exists on the model instance, then the method is used.

            TODO: This is only used in the BoundExtra module
        """
        value = getattr(self._extra, attribute)
        purch_inst = self._summary_instance
        mod_inst = self._instance
        if isinstance(value, basestring):
            if value.startswith("self.") and hasattr(purch_inst, value[5:]):
                return getattr(purch_inst, value[5:])
            elif value.startswith("model.") and hasattr(mod_inst, value[6:]):
                return getattr(mod_inst, value[6:])

        return value

class CommerceElement(object):
    """ Parent class for summary elements.
    """
    creation_counter = 0

    def __init__(self):
        # Set and increment the creation counter, to keep track of ordering
        self.creation_counter = CommerceElement.creation_counter
        CommerceElement.creation_counter += 1


class Extra(CommerceElement):
    """ Describes an extra cost or discount, providing access to related
        information. Currently it stores a verbose_name (ie "tax"), description
        (ie "10% VAT") and amount ("10.23"). These attributes can of course
        point to functions, which provide the relevant inforamtion.

        NB the first argument is verbose_name, just like Django DB fields
    """

    def __init__(self, verbose_name=NotSet, amount=NotSet, 
                            included=False, description=NotSet):
        self.name = None
        self.verbose_name = verbose_name
        self.amount = amount
        self.description = description
        self.included = included
        #display = None # For the future
        #currency = None # For the future

        super(Extra, self).__init__()

    def __unicode__(self):
        return self.verbose_name

    def __str__(self):
        return self.__unicode__().encode("ascii", "ignore")

    def __repr__(self):
        return self.__str__()

    def contribute_to_class(self, cls, name):
        self.name = name

        # Fill in values that are not set
        if self.verbose_name is NotSet:
            self.verbose_name = " ".join(name.split("_")).capitalize()
        if self.description is NotSet:
            self.description = None
        if self.amount is NotSet:
            self.amount = "self.get_amount_%s" % name

        setattr(cls, name, ExtraDescriptor(self))


#
# Total objects
#
# These describe a total that is to be calculated by the system, by summing
# the amounts derived from Items or Extras. Like Extras, these need to be
# bound to a model instance at run time, and a descriptor is again used to
# do this.
# When accessed, the descriptor returns the calculated value directly as a
# formatted Decimal.
#

class TotalDescriptor(object):
    def __init__(self, total):
        self.total = total

    def __get__(self, obj, type=None):
        if obj is None:
            raise AttributeError('Can only be accessed via an instance.')
        return self.total.get_total(obj)

    def __set__(self, obj, value):
        pass


class Total(CommerceElement):
    """ Describes a set of items to be included.
    """

    def __init__(self, *args, **kwargs):
        self.attributes = args
        self.prevent_negative = kwargs.pop('prevent_negative', False)
        self.model_cache = kwargs.pop('model_cache', None)
        self.name = None

        if kwargs:
            raise SummaryValidationError("Unknown keyword argument for Total: %s" % kwargs.keys()[0])

        super(Total, self).__init__()

    def contribute_to_class(self, cls, name):
        self.name = name
        setattr(cls, name, TotalDescriptor(self))

    def get_total(self, summary_instance):
        items = {}
        extras = {}
        custom = {}
        negatives = set()

        # If attributes are given, use 
        if self.attributes:
            for name in self.attributes:
                # Flag any negative amounts
                if name.startswith("-"):
                    name = name[1:]
                    negatives.add(name)

                value = getattr(summary_instance, name)

                # Handle items
                if name in summary_instance._meta.items:
                    items[name] = value

                # Handle extras
                elif name in summary_instance._meta.extras:
                    extras[name] = value

                # Handle custom methods and attributes
                else:
                    custom[name] = value

        # If no attributes are given, use all items, and all extras
        else:
            items = dict([(name,getattr(summary_instance, name))
                                    for name in summary_instance._meta.items])
            extras = dict([(name,getattr(summary_instance, name))
                                    for name in summary_instance._meta.extras])

        total = Decimal(0)

        # Sum all the items
        for name, queryset in items.items():
            item_total = sum([getattr(i, summary_instance._meta.items[name].cache_amount_as) or Decimal('0') for i in queryset])
            total += item_total

        # Sum all the extras
        for name,value in extras.items():
            if name not in negatives and not value.included:
                total += value.amount or Decimal(0)
            elif name in negatives and value.included:
                total -= value.amount or Decimal(0)

        # Sum any custom amounts
        for name,value in custom.items():
            if callable(value):
                # Is this callable a method on a django Model instance?
                if isinstance(getattr(value, 'im_self', None), Summary):
                    return value()
                else:
                    return value(summary_instance)
            if name in negatives:
                value = -value
            total += value or Decimal(0)
    
        if bool(self.prevent_negative) and total < 0:
            total = Decimal(0)

        # Save the cached value to the database
        if self.model_cache is not None:
            summary_instance.save_total(name=self.name, field_name=self.model_cache, total=total)

        return FormattedDecimal(total, summary_instance=summary_instance)


#
# Item objects
#
# These reference a group of objects, whose sum is to be included in a total.
# The objects are retrieved from the database once, and processing is done
# in Python, as there generally wont be many items.
# A descriptor is again used to populate and cache the list of items at runtime.
#

class Items(CommerceElement):
    """ Describes a set of items to be included.
    """

    def __init__(self, attribute=NotSet, item_amount_from=NotSet, cache_amount_as="AMOUNT"):
        self.attribute = attribute
        self.item_amount_from = item_amount_from
        self.cache_amount_as = cache_amount_as
        self.name = None

        # Validate values
        if (self.item_amount_from is not NotSet 
                and not self.item_amount_from.startswith("self.") 
                and not self.item_amount_from.startswith("model.")):
            msg = "Items() parameter 'item_amount_from' must start with either 'self.' or 'model.' (got %s)" % self.item_amount_from
            raise SummaryValidationError(msg)

        super(Items, self).__init__()


    def contribute_to_class(self, cls, name):
        self.name = name
        if self.attribute is NotSet:
            self.attribute = name
        if self.item_amount_from is NotSet:
            self.item_amount_from = 'self.get_%s_amount' % name

        setattr(cls, name, ItemsDescriptor(self))


class ItemsDescriptor(object):

    def __init__(self, items):
        self.items = items

    def __get__(self, obj, type=None):
        if obj is None:
            raise AttributeError('Can only be accessed via an instance.')

        if self.items.name in obj._cache:
            return obj._cache[self.items.name]

        model_instance = obj.instance

        # If this is a ManyToMany field with a "through=" model, use that
        # instead of the final model
        try:
            field = model_instance._meta.get_field(self.items.attribute)
            # NB: Different versions of django have a different name for
            # the through_model
            if field.rel.through is not None \
                            and hasattr(field.rel.through, '_meta'):
                # Keep moving if this through field was automatically created
                if field.rel.through._meta.auto_created:
                    raise AttributeError
                through_model = field.rel.through
            else:
                through_model = field.rel.through_model
            for f in through_model._meta.fields:
                if hasattr(f,'rel') and f.rel \
                            and f.rel.to == field.related.model:
                    query = {f.name: model_instance}
                    queryset = through_model._default_manager.filter(**query)
                    break
        # Otherwise, just use django to get the queryset
        except (FieldDoesNotExist, AttributeError):
            manager = getattr(model_instance, self.items.attribute)
            queryset = manager.all().select_related()

        # Calculate the amounts now, they will most likely be required later (eg in totals)
        for i in queryset:
            amount = self.get_item_unit_total(self.items.item_amount_from, i, obj)
            setattr(i, self.items.cache_amount_as, FormattedDecimal(amount, summary_instance=obj))

        obj._cache[self.items.name] = queryset
        return queryset

    def get_item_unit_total(self, value, rel_instance, summary_instance):

        if isinstance(value, basestring):
            if value.startswith("self.") \
                            and hasattr(summary_instance, value[5:]):
                return getattr(summary_instance, value[5:])(rel_instance)
            elif value.startswith("model.") \
                            and hasattr(rel_instance, value[6:]):
                value = getattr(rel_instance, value[6:])
                if callable(value):
                    return value()
                else:
                    return value
        elif iscallable(value):
            return value(rel_instance)

class SummaryOptions(object):
    def __init__(self, meta_options):
        self.locale = getattr(meta_options, 'locale', None)
        self.currency = getattr(meta_options, 'currency', None)
        self.decimal_html = getattr(meta_options, 'decimal_html', None)

        self.items = SortedDict()
        self.extras = SortedDict()
        self.totals = SortedDict()

        if self.locale and self.locale.startswith("self."):
            self.locale = attrs[locale[5:]]

        if self.currency and self.currency.startswith("self."):
            self.currency = attrs[self.currency[5:]]

        if self.decimal_html and self.decimal_html.startswith("self."):
            self.decimal_html = attrs[self.decimal_html[5:]]

    def add_element(self, key, value):
        """ Adds an element to one of the lists. """
        if isinstance(value, Items):
            self.items[key] = value
        elif isinstance(value, Extra):
            self.extras[key] = value
        elif isinstance(value, Total):
            self.totals[key] = value


class SummaryBase(type):

    def add_to_class(cls, name, value):
        if hasattr(value, 'contribute_to_class'):
            value.contribute_to_class(cls, name)
        else:
            setattr(cls, name, value)

    def __new__(cls, name, bases, attrs):
        new_class = super(SummaryBase, cls).__new__(cls, name, bases, attrs)
        _meta = SummaryOptions(attrs.pop('Meta', {}))

        elements = [(name, attrs.pop(name)) for name, obj in attrs.items() if isinstance(obj, CommerceElement)]
        elements.sort(lambda x, y: cmp(x[1].creation_counter, y[1].creation_counter))

        for key, value in elements:
            _meta.add_element(key, value)
            new_class.add_to_class(key, value)

        new_class.add_to_class('_meta', _meta)

        # Add the remaining attributes
        for key, value in attrs.items():
            new_class.add_to_class(key, value)

        return new_class


class Summary(object):
    __metaclass__ = SummaryBase

    def __init__(self, instance, locale=None):
        self.instance = instance
        self._cache = {}
        if locale:
            self._meta.locale = locale

        # Call any callables now that we have the instance we need
        if callable(self._meta.locale):
            self._meta.locale = self._meta.locale(instance)
        if callable(self._meta.currency):
            self._meta.currency = self._meta.currency(instance)
        if callable(self._meta.decimal_html):
            self._meta.decimal_html = self._meta.decimal_html(instance)

    def save_total(self, name, field_name, total):
        """ Save calculated total to model instance. 
            By default, the model instance isn't automatically saved, 
            but this can be cusomised..
        """
        setattr(self.instance, field_name, total)

    def __unicode__(self):
        """ Produce a text description of the summary.
        """

        # Collect the elements
        item_output = []
        for items in self._meta.items.keys():
            item_output.extend([(unicode(i), getattr(i, self._meta.items[items].cache_amount_as)) for i in getattr(self, items)])
        extra_output = [(unicode(getattr(self, e)), getattr(self, e).amount) for e in self._meta.extras]
        total_output = [(" ".join(t.split("_")).capitalize(), getattr(self, t)) for t in self._meta.totals]

        # Setup formatting (assumes 2 decimal_places)
        entry_length = max(map(len, [unicode(n) for n,v in (item_output+extra_output+total_output)]))
        max_digits   = max(map(len, ["%.2f"%v for n,v in (item_output+extra_output+total_output)]))
        item_format_string = u'%%-%ds  %%%d.%df' % (entry_length, max_digits, 2)
        total_format_string = u'%%%ds  %%%d.%df' % (entry_length, max_digits, 2)

        # Produce the output
        output = []
        output.extend(item_format_string % i for i in item_output)
        output.append(u"")
        output.extend(item_format_string % i for i in extra_output)
        output.append(u"")
        output.extend(total_format_string % i for i in total_output)
        output.append(u"")

        return "\n".join(output)

    def __str__(self):
        return self.__unicode__().encode("ascii", "ignore")
