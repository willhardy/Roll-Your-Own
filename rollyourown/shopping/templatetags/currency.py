# -*- coding: UTF-8 -*-
from decimal import Decimal
from django import template
import locale
locale.setlocale(locale.LC_ALL, 'en_AU')
register = template.Library()
 
@register.filter()
def currency(value):
    #string = locale.currency(value, grouping=True)
    #return template.mark_safe(string)
    return template.mark_safe(money_format(value, curr="$", neg='(', trailneg=")"))

@register.filter()
def html_currency(value):
    #string = locale.currency(value, grouping=True)
    #return template.mark_safe(string)
    return template.mark_safe(money_format(value, curr="$", html=True, neg='(', trailneg=")"))

@register.filter()
def short_currency(value):
    output = template.mark_safe(money_format(value, places=2, curr="$", neg='(', trailneg=")"))
    if output.endswith(".00"):
        return output[:-3]
    else:
        return output

def money_format(value, places=2, curr='', sep=',', dp='.',
             pos='', neg='-', trailneg='', html=False):
    """Convert Decimal to a money formatted string.

    places:  required number of places after the decimal point
    curr:    optional currency symbol before the sign (may be blank)
    sep:     optional grouping separator (comma, period, space, or blank)
    dp:      decimal point indicator (comma or period)
             only specify as blank when places is zero
    pos:     optional sign for positive numbers: '+', space or blank
    neg:     optional sign for negative numbers: '-', '(', space or blank
    trailneg:optional trailing minus indicator:  '-', ')', space or blank
    html:    formats for html goodness

    >>> d = Decimal('-1234567.8901')
    >>> money_format(d, curr='$')
    '-$1,234,567.89'
    >>> money_format(d, places=0, sep='.', dp='', neg='', trailneg='-')
    '1.234.568-'
    >>> money_format(d, curr='$', neg='(', trailneg=')')
    '($1,234,567.89)'
    >>> money_format(Decimal(123456789), sep=' ')
    '123 456 789.00'
    >>> money_format(Decimal('-0.02'), neg='<', trailneg='>')
    '<0.02>'
    >>> money_format(Decimal("123.45"), curr="$" html=True)
    <span class="money"><span class="currency">$</span>123<span class="cents">.45</span></span>

    """
    if value is None or isinstance(value, basestring):
        return value
    value = Decimal(value)
    q = Decimal(10) ** -places      # 2 places --> '0.01'
    sign, digits, exp = value.quantize(q).as_tuple()
    result = []
    digits = map(str, digits)
    build, next = result.append, digits.pop
    if html:
        build('</span>')
    if html:
        curr = '<span class="currency">%s</span>' % curr
        neg = neg.replace("-", "&#8722;")
        trailneg = trailneg.replace("-", "&#8722;")
    if sign:
        build(trailneg)
    if html:
        build('</span>')
    for i in range(places):
        build(next() if digits else '0')
    build(dp)
    if html:
        build('<span class="cents">')
    if not digits:
        build('0')
    i = 0
    while digits:
        build(next())
        i += 1
        if i == 3 and digits:
            i = 0
            build(sep)
    build(curr)
    build(neg if sign else pos)
    if html:
        build('<span class="money">')
    return ''.join(reversed(result))


