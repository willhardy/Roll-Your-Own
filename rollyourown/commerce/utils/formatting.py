#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
    The FormattedDecimal class allows locale aware formatting of currency
    amounts as decimals. This is intended to be used internally to format
    total values and extra values automatically when printed.
"""


from django.conf import settings
from decimal import Decimal
from django.utils.safestring import mark_safe
from django.utils import numberformat
from django.utils.encoding import smart_str

# babel has more comprehensive localisation, if it's available, we'll use that.
try:
    import babel.numbers
except ImportError:
    babel = None


DEFAULT_DECIMAL_HTML = ('<span class="money">'
                        '<span class="currency">%(curr_sym)s</span>%(major)s'
                        '<span class="cents">%(decimal_sym)s%(minor)s</span>'
                        '</span>')

class FormattedDecimal(Decimal):
    """ A formatted decimal according to the given locale and currency. """

    def __new__(cls, value=0, context=None, summary_instance=None):
        """ Create a new immutable Decimal object, adding our custom
            attributes.
        """
        obj = Decimal.__new__(cls, value, context)
        obj.initialise_context(summary_instance)
        return obj

    def initialise_context(self, summary_instance):
        self.locale = summary_instance._meta.locale or settings.LANGUAGE_CODE
        self.currency = summary_instance._meta.currency
        self.HTML = summary_instance._meta.decimal_html or DEFAULT_DECIMAL_HTML
        if babel:
            self.locale = babel.core.Locale.parse(self.locale, sep="-")

    @property
    def html(self):
        """ Provides a marked up version of the figure which can be easily
            styled. eg 123.45 will be marked up as:
            <span class="money">
              <span class="currency">$</span>123<span class="cents">.45</span>
            </span>
        """
        return mark_safe(self.HTML % self.elements)

    @property
    def elements(self):
        """ Returns a dict of the various elements for localised display.
            eg en_AU:
                   value        "1,234.56"
                   curr_sym     "$"
                   decimal_sym  "."
                   major        "1,234"
                   minor        "56"

            Additional items may be present if available.
        """

        # If babel is available, use its comprehensive locale skills
        if babel:
            value = self
            curr_sym = self.locale.currency_symbols.get(self.currency,
                                                            self.currency)
            decimal_sym = self.locale.number_symbols.get('decimal', ".")
            value = babel.numbers.format_decimal(value, "#,##0.00",
                                                        locale=self.locale)

        # If no babel, use Django's built-in locale data
        else:
            value = "%.02f" % self
            curr_sym = self.currency
            decimal_sym = get_format('DECIMAL_SEPARATOR', self.locale)
            group_sym = get_format('THOUSAND_SEPARATOR', self.locale)
            num_group = get_format('NUMBER_GROUPING', self.locale)
            value = numberformat.format(value, decimal_sym, None,
                                                    num_group, group_sym)

        major, minor = value.rsplit(decimal_sym, 1)
        return locals().copy()

    @property
    def raw(self):
        """ Return the decimal unformatted, as the Decimal class would have it.
        """
        return super(FormattedDecimal, self).__unicode__()

    def __unicode__(self):
        """ Return a formatted version of the Decimal, using the preset locale
            and currency.
        """
        if babel and self.currency:
            return babel.numbers.format_currency(self, self.currency,
                                                    locale=self.locale)
        else:
            return self.elements['value']


#
#    DJANGO REPRODUCTIONS
#    The following two functions are an edited copy of the Django locale
#    handling functions, which hardcodes system locale.
#    These can be replaced if/when Django makes its version more flexible.
#

from django.conf import settings
from django.utils.translation import get_language, to_locale, check_for_language
from django.utils.importlib import import_module

def get_format_modules(reverse=False, locale=None):
    """
    Returns an iterator over the format modules found in the project and Django.
    """
    modules = []
    if not locale or not check_for_language(get_language()) \
                                        or not settings.USE_L10N:
        return modules
    if not locale:
        locale = get_language()

    locale = to_locale(locale)

    if settings.FORMAT_MODULE_PATH:
        format_locations = [settings.FORMAT_MODULE_PATH + '.%s']
    else:
        format_locations = []
    format_locations.append('django.conf.locale.%s')
    for location in format_locations:
        for l in (locale, locale.split('_')[0]):
            try:
                mod = import_module('.formats', location % l)
            except ImportError:
                pass
            else:
                # Don't return duplicates
                if mod not in modules:
                    modules.append(mod)
    if reverse:
        modules.reverse()
    return modules

def get_format(format_type, locale=None):
    """
    For a specific format type, returns the format for the current
    language (locale), defaults to the format in the settings.
    format_type is the name of the format, e.g. 'DATE_FORMAT'
    """

    format_type = smart_str(format_type)
    if settings.USE_L10N:
        for module in get_format_modules(locale=locale):
            try:
                return getattr(module, format_type)
            except AttributeError:
                pass
    return getattr(settings, format_type)
