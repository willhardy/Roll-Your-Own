# -*- coding: UTF-8 -*-

from django.db.models import get_apps
from datetime import datetime
import logging
from django.db import transaction

# This is the name of the populate module n an app, eg 'populate' for populate.py
POPULATE_MODULE_NAME = "populate"

class AlreadyRegistered(Exception): pass
class NotRegistered(Exception): pass 

class PopulateCache(object):
    def __init__(self):
        self.models = {}
        self.discovered = False

    def register(self, *args, **kwargs):
        """ Register the given model with the given details. """
        # TODO: change to exception handling
        if 'model' in kwargs:
            model = kwargs.pop('model')
        elif args:
            args = list(args)
            model = args.pop(0)
        else:
            raise TypeError("register() requires the argument 'model'")

        if model in self.models:
            raise AlreadyRegistered("The model %s is already registered." % model)

        self.models[model] = Populator(model, *args, **kwargs)

    def discover(self):
        if self.discovered: 
            return

        for app in get_apps():
            # Try to import populate module in this app
            app_name = app.__name__.split(".")[:-1]
            module_name = ".".join(app_name + [POPULATE_MODULE_NAME])
    
            try:
                # Simply importing the module will register the models
                populate_module = __import__(module_name, '', '', [''])
                logging.debug("Registering populate module: %s" % module_name)
            except ImportError:
                pass

        self.discovered = True

    def __getitem__(self, key):
        self.discover()
        return self.models[key]

    def __setitem__(self, key, value):
        args = [value]
        self.register(key, *args)

    def __delitem__(self, key):
        del self.models[key]

    def __len__(self):
        return len(self.models)

    def __iter__(self):
        return self.models.__iter__

    def __contains__(self, item):
        self.discover()
        return item in self.models

    def get_model(self, model):
        self.discover()
        try:
            return self.models[model]
        except (KeyError, TypeError):
            raise NotRegistered('%s not in registry (%s)' % (model.__name__, self.models))

from rollyourown.populate import DEFAULT_GENERATOR_FUNCTIONS
import random
import logging

class Populator(object):
    def __init__(self, model, instances=10, clear_existing=False, data_functions=None, max_many_to_many_connections=5):
        self.model = model
        self.number_instances = instances
        self.clear_existing = clear_existing
        self.data_functions = data_functions
        self.instances = []
        self.max_many_to_many_connections = max_many_to_many_connections

    def populate(self):
        if not self.instances:
            # Delete all existing objects, only if it was asked for and we have testing mode
            if self.clear_existing:
                self.model._default_manager.all().delete()

            for i in range(self.number_instances):
                instance = self.populate_instance(i)
                self.instances.append(instance)
            print "Created %d instances of %s.%s" % (len(self.instances), self.model._meta.app_label, self.model._meta.object_name)
        logging.debug("Populator.populate() called twice on instance.")

    def populate_instance(self, counter=None):
        instance = self.model()

        for field in self.model._meta.fields:
            # If choices are given, use those exclusively
            if field.choices:
                setattr(instance, field.name, random.choice(field.choices)[0])
            # If this field accepts a blank value, leave it blank sometimes (not so often though)
            elif blankable(field):
                pass
            else:
                generator_function = DEFAULT_GENERATOR_FUNCTIONS.get(field.__class__.__name__, None)
                if not generator_function:
                    generator_function = DEFAULT_GENERATOR_FUNCTIONS.get(field.get_internal_type(), None)
                if generator_function:
                    value = generator_function(field, instance, counter)
                    if hasattr(generator_function, 'add_to_instance'):
                        generator_function.add_to_instance(field, instance, value)
                    else:
                        setattr(instance, field.name, value)
    
        transaction.enter_transaction_management()
        transaction.managed(True)
        try:
            instance.save()
        except:
            transaction.rollback()
            #logging.debug(repr(instance.__dict__))
            #raise
        else:
            transaction.commit()
    
        return instance

    def populate_many_to_many(self):
        # Many to Many fields are special, they need to be added after saving
        # TODO: ManyToMany with through= attributes may need some help here

        for instance in self.instances:
            for field in self.model._meta.many_to_many:
                rel_to_instances = list(field.rel.to._default_manager.all().order_by('?')[:self.max_many_to_many_connections])
                for i in range(random.randint(0,len(rel_to_instances))):
                    getattr(instance, field.name).add(rel_to_instances[i])


def blankable(field):
    """ If a given can be made blank. """
    return (not field.editable and not field.default == datetime.now) or (
        # Blank values need to be valid
        field.blank 
        # Lets only do this once in a while
        and random.choice((True, False, False, False)) 
        # Lets not have half the data being the same
        and not field.default == datetime.now 
        )
        
registry = PopulateCache()
