#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
      Title: Populate management command
     Author: Will Hardy (http://willhardy.com.au)
       Date: June 2008
      Usage: python manage.py populate appname
  $Revision: 12 $

Description: 
    Populates models for testing purposes with mildly sensible data.
    Draws upon the field type, limits, constraints and name for deciding data.

    Eg if a field is called "surname" then a surname will be entered.
    The default decisions might be useful for you, but you can control
    the type of data by creating a file called populate.py in the app you want to test.

    Any algorithms used here need not be particularly efficient, this script is only 
    run once in a while. Readability, maintainability and general simplicity is more 
    important.

Improvements:
    * uniqueness
    * populate.py to force data type
    * populate.py to provide data set
    * populate.py to provide function to provide data
    * serialise new objects, creating test_data.json fixture for slow populate


"""

from django.core.exceptions import ImproperlyConfigured
from django.core.management.base import BaseCommand, CommandError
from django.db.models import get_app, get_apps, get_model, get_models

from rollyourown.populate import populate_models

# A handy shortcut for getting the full model name
full_model_name = lambda m: ".".join((m._meta.app_label, m._meta.object_name))

class Command(BaseCommand):
    help = 'Populates the given app with random test data.'
    args = '[appname ...]'

    def handle(self, *app_labels, **options):

        # Get the models we want to export
        models = get_models_to_populate(app_labels)

        populate_models(models)


def get_models_to_populate(app_labels):
    """ Gets a list of models for the given app labels, with some exceptions. 
    """

    # These models are not to be populated, e.g. because they can be generated automatically
    EXCLUDED_MODELS = ('contenttypes.ContentType', )

    models = []

    # If no app labels are given, return all but excluded
    if not app_labels:
        for app in get_apps():
            models.extend([ m for m in get_models(app) if full_model_name(m) not in EXCLUDED_MODELS ])

    # Get all relevant apps
    for app_label in app_labels:
        # If a specific model is mentioned, get only that model, even if it might be excluded
        if "." in app_label:
            app_label, model_name = app_label.split(".", 1)
            model = get_model(app_label, model_name)
            if model is None:
                raise CommandError("Unknown model: %s" % '.'.join((app_label, model_name)))
            models.append(model)
        # Get all models for a given app, except excluded
        else:
            try:
                app = get_app(app_label)
            except ImproperlyConfigured:
                raise CommandError("Unknown application: %s" % app_label)
            models.extend([ m for m in get_models(app) if full_model_name(m) not in EXCLUDED_MODELS ])

    return models


