# -*- coding: UTF-8 -*-

"""
    A collection of abstract models to speed up and standardise development. 
    They are not required to use the shopping framework.
"""

from datetime import datetime
from django.db import models
from rollyourown.shopping import purchase
from rollyourown.shopping.utils import FriendlyID

friendly_id = FriendlyID()

class ActiveObjectManager(models.Manager):
    " Provides easy access to active objects. "
    def active(self):
        return self.get_query_set().filter(is_active=True)

class ProductManager(ActiveObjectManager):
    " Provides access to a number of common features "
    def popular(self):
        " Returns query set of the most popular items. "
        raise NotImplemented

    def featured(self):
        " Returns Query Set of Featured Products "
        raise NotImplemented

class Product(models.Model):
    # Basic product information
    name        = models.CharField(max_length=150, help_text="Full product name, but keep this one simple")
    slug        = models.SlugField(unique=True, help_text="Used to form the URL for this product")
    sku         = models.SlugField(unique=True, help_text="A unique code to identify this product")
    
    # Shop information
    available_from  = models.DateField(blank=True, null=True, help_text='Enter the earlist date the product will dispatch (optional)')
    active          = models.BooleanField(default=True, help_text="Uncheck this box to remove product from site display")

    # Highlighting
    featured    = models.BooleanField(default=False, help_text="Will highlight this product as featured thoughout the website")
    rank        = models.PositiveIntegerField('order rank', default=5, help_text="Determines where the product will be displayed in the listings. 1 means at top")
    
    # HTML Meta data
    meta_page_title = models.CharField(max_length=150, default="", blank=True, help_text="SEO Browser title for this product")
    meta_keywords = models.CharField(max_length=150, default="", blank=True, help_text="Keywords for search engine optimisation")
    meta_description = models.TextField(default="", blank=True, help_text="Product description for search engine optimisation")

    created_on = models.DateTimeField(default=datetime.now, blank=True, editable=False)
    updated_on = models.DateTimeField(blank=True, editable=False)

    objects = ProductManager()

    def save(self, *args, **kwargs):
        self.meta_page_title = self.meta_page_title or self.name
        self.updated_on = datetime.now()
        super(Product, self).save(*args, **kwargs)

    class Meta:
        abstract = True
        ordering = ['rank', 'name', 'sku']
    
    def __unicode__(self):
        return self.name or self.sku

class ProductCategory(models.Model):
    " A simple way to categories products. "
    title = models.CharField(max_length=100, help_text="The title of the category is displayed in link menus.")
    slug = models.SlugField('key', unique=True, help_text="A unique key to identify this category. Ideally human readable.")

    is_active = models.BooleanField('is active', default=True, help_text="Uncheck this to deactivate this category from showing in the site")

    rank = models.PositiveIntegerField('rank', default=5, help_text="Set Where you want this category to appear in the list of categories. <strong>1 means at the top</strong>")

    objects = ActiveObjectManager()

    class Meta:
        abstract = True
        verbose_name_plural = "product categories"
        ordering = ('rank','title')

    def __unicode__(self):
        return self.title


class Item(models.Model):
    # product = models.ForeignKey(Product)
    # cart    = models.ForeignKey(Cart, related_name="items")
    unit_price = models.DecimalField(decimal_places=2, max_digits=12, blank=True)
    quantity   = models.PositiveSmallIntegerField(default=1)

    def save(self, *args, **kwargs):
        if self.unit_price is None:
            self.unit_price = self.product.price
        super(Item, self).save(*args, **kwargs)

    class Meta:
        abstract = True

    def amount(self):
        return self.unit_price * self.quantity

    def __unicode__(self):
        return u'%d x %s' % (self.quantity, self.unit_price)



class Purchase(models.Model):
    " An abstract purchase, you need to link your own items as demonstrated below. "
    # items = models.ManyToManyField(Item)
    date_created = models.DateTimeField(default=datetime.now)

    class Meta:
        abstract = True


class Order(Purchase):
    invoice_number = models.CharField(max_length=16, default="", blank=True)

    def save(self, *args, **kwargs):
        if not self.invoice_number:
            if not self.id:
                super(Order, self).save(*args, **kwargs)
            self.invoice_number = friendly_id.encode(self.id)
        super(Order, self).save(*args, **kwargs)

    class Meta:
        abstract = True


class ProductPhoto(models.Model):
    " A Photo of a Product "

    UPLOAD_TO = lambda i,f: 'products/%s%s' % (i.slug, os.path.splitext(f)[1])

    image = models.ImageField('image', upload_to=UPLOAD_TO, help_text="Filebrowser. The Product Image")
    title = models.CharField('title', max_length=100, help_text="The Image Title will be displayed as alt text")
    slug = models.SlugField('catalogue code', help_text="Unique catalogue code to identify this image.")
    rank = models.PositiveIntegerField('rank', default=5, help_text="A Rank of 1 will displayed at the top.")

    class Meta:
        abstract = True
        ordering = ['rank', 'title']

    def __unicode__(self):
        return self.title

    def get_absolute_url(self):
        return self.get_image_url()
