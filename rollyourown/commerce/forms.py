#!/usr/bin/env python
# -*- coding: UTF-8 -*-

from django import forms
from django.forms.models import inlineformset_factory, modelformset_factory, formset_factory, ModelForm
from django.forms.formsets import BaseFormSet

from django.utils.html import conditional_escape
from django.utils.encoding import force_unicode
from django.forms.forms import DeclarativeFieldsMetaclass, BoundField
from django.utils.safestring import mark_safe
from django.forms.models import _get_foreign_key

class SummaryFormBase(object):
    """ A collection of formsets and form fields. 
    """
    elements = None
    form_elements = None
    SummaryModelForm = None
    _max_form_columns = 1

    def __init__(self, *args, **kwargs):
        self.instance = kwargs.pop('instance', None)
        self.model_instance = self.instance.instance
        if self.instance is None:
            raise TypeError("%s requires an 'instance' argument" % self.__class__)

        self._summary_form = self.SummaryModelForm(instance=self.model_instance, *args, **kwargs)

        self._formsets = {}
        self._forms = {}
        prefix = kwargs.pop('prefix', '')
        if prefix:
            prefix = '%s-' % prefix
        for key, element in self.__class__.form_elements.items():
            if isinstance(element, DeclarativeFieldsMetaclass):
                _prefix = '%s%s' % (prefix, key)
                self._forms[key] = element(instance=self.model_instance, prefix=_prefix, *args, **kwargs)
            elif type(element) is type and issubclass(element, BaseFormSet):
                _prefix = '%s%s' % (prefix, key)
                # XXX This formset should use the queryset from the summary, not from the instance
                # meaning that I may need to write my own inline formset that takes a summary argument and
                # uses the correct queryset to populate the initial data. Check where/when Django finds the
                # relevant queryset.
                queryset = getattr(self.instance, key)
                self._formsets[key] = element(prefix=_prefix, queryset=queryset, *args, **kwargs)

    def save(self, commit=True):
        self._summary_form.save(commit)
        for form in self._forms.values():
            form.save(commit)
        for formset in self._formsets.values():
            formset.save(commit)

    def is_valid(self):
        return (self._summary_form.is_valid() 
                    and all([f.is_valid() for f in self._forms.values()]) 
                    and all([f.is_valid() for f in self._formsets.values()]))

    def is_bound(self):
        return self._args or self._kwargs.get('data', False) or self._kwargs.get('files', False)

    def non_form_errors(self):
        # TODO
        pass

    @property
    def errors(self):
        # TODO: key conflicts?
        errors = self._summary_form.errors
        for f in self._forms.values():
            errors.update(f.errors)
        for fs in self._formsets.values():
            for f in fs.forms:
                errors.update(f.errors)
        return errors

    def table_data(self):
        """ Provides the data without the table tags, allowing for customised display. """
        # Collect all the rows. Each row is a 3-tuple with name, form (if any) and total
        rows = []
        max_columns = 1
        for name in self.elements:
            if name in self._forms:
                form_element = self._forms[name]
                max_columns = max((len(form_element.base_fields), max_columns))
            elif name in self._formsets:
                form_element = self._formsets[name]
                max_columns = max((len(form_element.form.base_fields), max_columns))
            elif name in self.form_elements:
                form_element = self._summary_form[self.form_elements[name]]
            else:
                form_element = None
            rows.append((name, form_element, getattr(self.instance, name)))
            self._max_form_columns = max_columns
        return rows

    def item_as_table_rows(self, name, formset, element, cache_amount_as):
        output = []
        if name in self._formsets:
            output.append(self._formset_labels_as_columns(formset))
            for f in formset.forms:
                # XXX use table cells instead of as_ul (ie tabular inline)
                output.append(u'<tr><th>%s</th>%s<td>%s</td></tr>' % (f.instance, self._form_as_table_columns(f), getattr(f.instance, cache_amount_as)))
        else:
            for i in getattr(self.instance, name):
                output.append(u'<tr><th>%s</th><td colspan="%d"></td><td>%s</td></tr>' % (i, self._max_form_columns, getattr(i, cache_amount_as)))
        return output

    def _formset_labels_as_columns(self, formset):
        cols = []
        cols.append(unicode(formset.management_form))
        cols.extend(f.label for f in formset.form.base_fields.values())
        return u"".join(u"<th>%s</th>"%c for c in cols)

    def _form_labels_as_columns(self, form):
        cols = ["&nbsp;"]
        cols.extend(BoundField(form, f, n).label_tag() for n,f in form.fields.items())
        return u"".join(u"<th>%s</th>"%c for c in cols)

    def _form_as_table_columns(self, form):
        cols = []
        num_visible_cols = 0
        for name, field in form.fields.items():
            bf = BoundField(form, field, name)
            if field.widget.is_hidden:
                cols.append(u'%s' % bf)
            else:
                cols.append(u'<td>%s</td>' % bf)
                num_visible_cols += 1
        if num_visible_cols < self._max_form_columns:
            cols.append(u'<td colspan="%d">&nbsp;</td>' % (self._max_form_columns - num_visible_cols ))
        return "".join(cols)
        
    def extra_as_table_row(self, name, form, element):
        if name in self._forms:
            output = []
            output.append(u'<tr>%s</tr>'%self._form_labels_as_columns(self._forms[name]))
            output.append(u'<tr><th>%s</th>%s<td>%s</td></tr>' % (name, self._form_as_table_columns(self._forms[name]), element.amount))
            return u"".join(output)
        elif name in self.form_elements:
            field = form
            form_cell = u'%s%s%s' % (field.errors, field, field.help_text)
            # XXX: Dear Django, why is there no ':' in the label tag?
            return u'<tr><th>%s</th><td colspan="%d">%s %s</td><td>%s</td></tr>' % (name, self._max_form_columns, field.label_tag(), field, element.amount)
        else:
            return u'<tr><th>%s</th><td colspan="%d"></td><td>%s</td></tr>' % (name, self._max_form_columns, element.amount)

    def as_table(self):
        """ Produce a tabular version of the data and forms.
        """
        output = []

        # Collect all the rows. Each row is a 3-tuple with name, form (if any) and total
        data = self.table_data()
        for name, form, element in self.table_data():
            if hasattr(element, '__iter__'):
                output.extend(self.item_as_table_rows(name, form, element, self.instance._meta.items[name].cache_amount_as))
            elif hasattr(element, 'amount'):
                output.append(self.extra_as_table_row(name, form, element))
            else:
                output.append(u'<tr><th colspan="%d">%s</th><td>%s</td></tr>' % (self._max_form_columns+1, name, element))

        # XXX TMP AUTO TEST CODE
        f = open("/home/kogan/tmp/deletemenow.html", 'w')
        f.write('<table>')
        f.write(mark_safe("\n".join(output)))
        f.write('</table>')
        f.close()

        return mark_safe("\n".join(output))

    def as_ul(self):
        pass

    def as_p(self):
        pass

    def __get__(self, key):
        """ Allow elements to be accessed directly, by name (in eg templates). """
        try:
            return self._forms[key]
        except KeyError:
            return self._formsets[key]
        element = self.form_elements[key]
        if isinstance(element, basestring):
            return self._summary_form[element]
        else:
            raise KeyError

    def field_html_output(self, name, normal_row, error_row, row_ender, help_text_html, errors_on_separate_row):
        html_class_attr = ''
        bf = field = self._summary_form[name]
        bf_errors = self._summary_form.error_class([conditional_escape(error) for error in bf.errors]) # Escape and cache in local variable.
        if bf.is_hidden:
            if bf_errors:
                top_errors.extend([u'(Hidden field %s) %s' % (name, force_unicode(e)) for e in bf_errors])
            hidden_fields.append(unicode(bf))
        else:
            # Create a 'class="..."' atribute if the row should have any
            # CSS classes applied.
            css_classes = bf.css_classes()
            if css_classes:
                html_class_attr = ' class="%s"' % css_classes
    
            if errors_on_separate_row and bf_errors:
                output.append(error_row % force_unicode(bf_errors))
    
            if bf.label:
                label = conditional_escape(force_unicode(bf.label))
                # Only add the suffix if the label does not end in
                # punctuation.
                if self._summary_form.label_suffix:
                    if label[-1] not in ':?.!':
                        label += self._summary_form.label_suffix
                label = bf.label_tag(label) or ''
            else:
                label = ''
    
            if field.help_text:
                help_text = help_text_html % force_unicode(field.help_text)
            else:
                help_text = u''
    
            return normal_row % {
                'errors': force_unicode(bf_errors),
                'label': force_unicode(label),
                'field': unicode(bf),
                'help_text': help_text,
                'html_class_attr': html_class_attr
            }


def generate_summary_form(summary):
    """ Creates a Form class for processing summaries. """
    # A dict of forms, formsets and strings which point to fields in the summary form
    form_elements = {}
    attrs = {'form_elements': form_elements, 'elements': summary._meta.elements.keys()}
    summary_form_fields = {}

    for name, element in summary._meta.elements.items():
        if name in summary._meta.items:
            items = summary._meta.items[name].bound_items(summary)
            if element.editable is True and items.rel_model is not None:
                subform = subform_factory(summary, items, included_fields=None)
                form_elements[name] = modelformset_factory(items.rel_model, form=subform, extra=0, formset=SummaryFormSet)
            elif type(element.editable) is type and issubclass(element.editable, forms.BaseForm):
                form_elements[name] = modelformset_factory(items.rel_model, form=element.editable, extra=0, formset=SummaryFormSet)
            elif hasattr(element.editable, '__iter__') and items.rel_model is not None:
                subform = subform_factory(summary, items, included_fields=element.editable)
                form_elements[name] = modelformset_factory(items.rel_model, form=subform, extra=0, formset=SummaryFormSet)
        elif name in summary._meta.extras:
            if element.editable is True:
                summary_form_fields[name] = name
                form_elements[name] = name
            elif isinstance(element.editable, basestring):
                summary_form_fields[element.editable] = element.editable
                form_elements[name] = element.editable
            elif type(element.editable) is DeclarativeFieldsMetaclass and issubclass(element.editable, forms.BaseForm):
                form_elements[name] = element.editable

    # Create the global summary form class
    class Meta:
        model = summary.instance
        fields = summary_form_fields.keys()
    summary_form_fields['Meta'] = Meta
    attrs['SummaryModelForm'] = type('SummaryModelForm', (forms.ModelForm,), {'Meta': Meta})

    return type('SummaryForm', (SummaryFormBase,), attrs)


from django.utils.html import escape
from django.utils.safestring import mark_safe
from django.forms.util import flatatt

class ReadOnlyWidget(forms.Widget):
    def render(self, name, value, attrs):
        final_attrs = self.build_attrs(attrs, name=name)
        if hasattr(self, 'initial'):
            value = self.initial
            return mark_safe("<span %s>%s</span>" % (flatatt(final_attrs), escape(value) or ''))

    def _has_changed(self, initial, data):
        return False

class ReadOnlyField(forms.Field):
    widget = ReadOnlyWidget
    def __init__(self, widget=None, label=None, initial=None, help_text=None):
        super(type(self), self).__init__(self, label=label, initial=initial,
            help_text=help_text, widget=widget)
        self.widget.initial = initial

    def clean(self, value):
        return self.widget.initial 

from django.forms.models import BaseModelFormSet

class SummaryFormSet(BaseModelFormSet):
    def get_queryset(self):
        # This is the same as the BaseModelFormSet version, except
        # that no further queries are made (for eg ordering).
        if not hasattr(self, '_queryset'):
            if self.queryset is not None:
                qs = self.queryset
            else:
                qs = self.model._default_manager.get_query_set()

            # In this spot, django ensures the queryset it receives
            # is ordered. We're avoiding this for now, as we don't
            # want the queryset to be regenerated.

            # Removed queryset limiting here. As per discussion re: #13023
            # on django-dev, max_num should not prevent existing
            # related objects/inlines from being displayed.
            self._queryset = qs
        return self._queryset


def subform_factory(summary, items, included_fields=None):
    # TODO: fk_name may be necessary
    excludes = []
    try:
        fk = _get_foreign_key(summary.instance.__class__, items.rel_model, fk_name=None)
        excludes.append(fk.name)
    except Exception:
        pass
    # The following feature has been removed, in favour of explicit field selection
    # If this is an intermediate model, exclude the other foreign key field
    #if items.end_model is not None:
    #    efk = _get_foreign_key(items.end_model, items.rel_model, fk_name=None)
    #    excludes.append(efk.name)
    class Meta:
        model = items.rel_model
        exclude = excludes
        fields = included_fields
    return type('%sModelForm'%items.rel_model.__name__, (ModelForm,), {'Meta': Meta})
