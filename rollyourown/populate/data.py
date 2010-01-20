# -*- coding: UTF-8 -*-

""" Data generating functions for automatically populating.
    This module contains a few intelligent default data generators.
"""

import os, string, random
from decimal import Decimal
from datetime import date, datetime, timedelta
from django.template.defaultfilters import slugify, linebreaks
from django.contrib.webdesign import lorem_ipsum

# FUNCTIONS

def generate_chars(field, instance, counter):
    """ Generates a 2-4 word title. """
    if 'phone' in field.name or 'mobile' in field.name or 'fax' in field.name:
        return generate_phone(field, instance, counter)
    if 'address' in field.name:
        return generate_address(field, instance, counter).splitlines()[0]
    max_length = int(field.max_length)
    if max_length < 15:
        length = random.randint(1, max_length)
        if 'number' in field.name or 'postcode' in field.name or 'zip' in field.name:
            return "".join([random.choice(string.digits) for i in range(length)])
        else:
            length = random.randint(1, max_length)
            return "".join([random.choice(string.ascii_letters) for i in range(length)])
    elif max_length < 25:
        return lorem_ipsum.words(1, common=False).title()[:max_length]
    elif max_length < 70:
        return lorem_ipsum.words(2, common=False).title()[:max_length]
    else:
        return lorem_ipsum.words(3, common=False).title()[:max_length]

def generate_text(field, instance, counter):
    """ Generates a number of paragraphs of text. """
    if 'address' in field.name:
        return generate_address(field, instance, counter)
    return generate_html(field, instance, counter)

def generate_phone(field, instance, counter):
    prefix = '(03)'
    digits = min((8, field.max_length-2-len(prefix)))
    value = str(random.randint(10**8, 10**9-1))
    return ' '.join((prefix, value[:digits/2], value[digits/2:]))

def generate_address(field, instance, counter):
    # TODO: Replace this with a corpus of entertainingly varied 
    # (and possibly localised) addresses.
    country = "Australia"
    lorem = lorem_ipsum.words(3, common=False).title().split()
    lines = []
    lines.append('%d %s %s' % (random.randint(0,999), lorem[0], random.choice(("St", "Rd", "Crt", "Ave"))))
    lines.append('%s, %s %d' % (lorem[1], lorem[2], random.randint(1000, 9999)))
    lines.append(country)
    return '\n'.join(lines)

def generate_plaintext(field, instance, counter):
    """ Generates several paragraphs of plain text. """
    plaintext = "\n\n".join(lorem_ipsum.paragraphs(3, common=False))
    return plaintext

def generate_html(field, instance, counter):
    """ Generates several paragraphs of plain text. """
    paragraphs = lorem_ipsum.paragraphs(3, common=False)
    text = "\n\n".join([ htmlify(p) for p in paragraphs ])
    html = linebreaks(text)
    return html

def htmlify(text):
    words = text.split()
    num_words = len(words)
    # Randomly make some text strong or italic
    strong = random.randint(0,num_words-1)
    words[strong] = "<strong>%s</strong>" % words[strong]
    em = random.randint(0,num_words-1)
    words[em] = "<em>%s</em>" % words[em]
    link = random.randint(0,num_words-3)
    words[link:link+2] = ['<a href="#">%s</a>' % " ".join(words[link:link+2])]
    return " ".join(words)

def generate_slug(field, instance, counter):
    return slugify(lorem_ipsum.words(3, common=False))

def generate_integer(field, instance, counter):
    small = True
    positive = True
    max = small and 255 or 100000
    min = not positive and -max or 0
    return random.randint(min, max)

def generate_boolean(field, instance, counter):
    # bias in favor of True for active flags
    if field.name == 'is_active' or field.name == 'active':
        return random.choice((True, True, True, False))
    else:
        return random.choice((True, False))

def generate_date(field, instance, counter):
    min_date = date.today() - timedelta(days=365*5)
    max_date = date.today() + timedelta(days=365*5)
    return min_date + timedelta(days=random.randint(0, (max_date - min_date).days))

def generate_datetime(field, instance, counter):
    min_date = max_date = None
    # TODO: Automatically detect all past-only fields, being fields ending with 'ed'
    if field.name.endswith('created') or field.name.endswith('added') or field.name.endswith('paid'):
        max_date = datetime.now()
    min_date = min_date or datetime.now() - timedelta(days=365*5)
    max_date = max_date or datetime.now() + timedelta(days=365*5)

    return min_date + timedelta(days=random.randint(0, (max_date - min_date).days), seconds=random.randint(0,60*60*24))

def generate_decimal(field, instance, counter):
    max_places = field.decimal_places
    digits = random.randint(1, field.max_digits)
    value = str(random.randint(10**digits))
    value = ".".join((value[:-max_places], value[-max_places:]))
    return Decimal(value)

def generate_email(field, instance, counter):
    # TODO: hmmmm
    #domains = ("gmail.com", "hotmail.com")
    domains = ("willhardy.com.au",)
    names = ("will",)
    return '@'.join((random.choice(names), random.choice(domains)))

def generate_file(field, instance, counter):
    return generate_image(field, instance, counter)

def generate_filepath(field, instance, counter):
    pass

def generate_float(field, instance, counter):
    return random.random()

def generate_image(field, instance, counter):
    from django.core.files.base import ContentFile 
    directory = os.path.join(os.path.dirname(__file__), 'data_files')
    if 'logo' in field.name:
        directory = os.path.join(directory, 'logos')
    filename_choices = [f for f in os.listdir(directory) if not f.startswith(".")]
    filename = random.choice([f for f in filename_choices if (not f.startswith(".") and "." in f)])
    return (filename, ContentFile(open(os.path.join(directory, filename), "r").read()))

def add_image_to_instance(field, instance, value):
    getattr(instance, field.name).save(save=False, *value)
generate_image.add_to_instance = add_image_to_instance

def generate_ipaddress(field, instance, counter):
    number = random.randint(0, 2**32-1)
    return '.'.join([str((number>>(i*8)) % 256) for i in range(4)])

def generate_url(field, instance, counter):
    # hmmmm
    domains = ('http://willhardy.com.au',)
    return random.choice(domains)

def generate_reference(field, instance, counter):
    return field.rel.to._default_manager.all().order_by("?")[0]

def generate_point(field, instance, counter):
    from django.contrib.gis.geos import Point
    x_around = 144.940
    y_around = -37.814

    x = x_around is not None and (x_around + (random.random() - 0.5)) or (random_random() - 0.5) * 360
    y = y_around is not None and (y_around + (random.random() - 0.5)) or (random_randint() - 0.5) * 180
    return Point(x, y)

DEFAULT_GENERATOR_FUNCTIONS = {
    'CharField':  generate_chars,
    'BooleanField': generate_boolean,
    # CommaSeparatedIntegerField
    'DateField': generate_date,
    'DateTimeField': generate_datetime,
    'DecimalField': generate_decimal,
    'EmailField': generate_email,
    'FileField': generate_file,
    #'FilePathField': generate_filepath,
    'FloatField': generate_float,
    'ImageField': generate_image,
    'IntegerField': generate_integer,
    'IPAddressField': generate_ipaddress,
    'NullBooleanField': generate_boolean,
    'PositiveIntegerField':  generate_integer,
    'PositiveSmallIntegerField': generate_integer,
    'SlugField':  generate_slug,
    'SmallIntegerField': generate_integer,
    'TextField':  generate_text,
    'ForeignKey':  generate_reference,
    #'TimeField': generate_time,
    'URLField': generate_url,
    #'XMLField': generate_xml,
    'PointField': generate_point,
    #'LineStringField': generate_,
    #'PolygonField': generate_,
    #'MultiPointField': generate_,
    #'MultiLineStringField': generate_,
    #'MultiPolygonField': generate_,
    #'GeometryCollectionField': generate_,
    }
