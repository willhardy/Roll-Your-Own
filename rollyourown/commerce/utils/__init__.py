from rollyourown.commerce.utils.friendly_id import FriendlyID
from rollyourown.commerce.utils.formatting import FormattedDecimal

__all__ = ('FriendlyID', 'FormattedDecimal', 'json_summary')

from django.utils import simplejson
from django.core.serializers.json import DjangoJSONEncoder

def json_summary(summary, fields=None):
    """ serialize the given summary to JSON. """

    data = {}
    for items in summary._meta.items.keys():
        if fields and items in fields:
            data[items] = dict((i.pk, getattr(i, summary._meta.items[items].cache_amount_as)) for i in getattr(summary, items))
    for extra in summary._meta.extras:
        if fields and extra in fields:
            data[extra] = getattr(summary, extra).amount
    for total in summary._meta.totals:
        if fields and total in fields:
            data[total] = getattr(summary, total)

    return simplejson.dumps(data, cls=DjangoJSONEncoder)

