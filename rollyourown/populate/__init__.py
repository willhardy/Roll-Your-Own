
from rollyourown.populate.data import DEFAULT_GENERATOR_FUNCTIONS

from rollyourown.populate.registration import registry, Populator

def register(*args, **kwargs):
    registry.register(*args, **kwargs)


def populate_models(models):
    """ Populates all given models. """

    # Record all the populators we've created
    populators = {}

    for model in models:
        if model in registry:
            populators[model] = registry[model]
        else:
            populators[model] = Populator(model)

        populators[model].populate()

    for model, populator in populators.items():
        populator.populate_many_to_many()


# Version information
__version__ = filter(str.isdigit, "$Revision: 16 $")
__authors__ = ["Will Hardy <rollyourown@willhardy.com.au>"]
