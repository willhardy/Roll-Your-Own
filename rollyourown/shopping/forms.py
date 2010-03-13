# -*- coding: UTF-8 -*-

from django import forms
from registration import registry
from django.db import models

def inlineformset_factory(parent_model, attribute, show_initial=True, form=forms.ModelForm,
            fields=None, exclude=None, can_order=False, can_delete=True, extra=0, max_num=0):
    """ Return a formset for the given (Cart) instance and field.
        TRIAL: This API is in a trial stage and may change in the future.
        FIXME: The shopping API can't be introspected without an instance, the
               shopping API can't be created on an instance which has not been
               saved.
    """
    model_attribute = registry.get_model(parent_model)()._shopping
    model_attribute = model_attribute._items[attribute].attribute
    field = parent_model._meta.get_field(model_attribute)

    if isinstance(field, models.ManyToManyField):
        # If a ManyToManyField is given look for a through model
        if field.rel.through is not None:
            model = field.rel.through   #this was through_model in early django versions
        # Otherwise, we have to do things manually
        else:
            return m2m_formset_factory(field.name, show_initial=show_initial, form=form,
                            fields=fields, exclude=exclude, can_order=can_order,
                            can_delete=can_delete, extra=extra, max_num=max_num)
    else:
        model = field.rel.to
    FormSet = forms.models.inlineformset_factory(parent_model, model, form=form, fields=fields, exclude=exclude,
                        can_order=can_order, can_delete=can_delete, extra=extra, max_num=max_num)
    return FormSet


def m2m_formset_factory(field_name, show_initial=True, form=forms.ModelForm, fields=None, exclude=None,
                          can_order=False, can_delete=True, extra=0, max_num=0):

    M2MFormSet = forms.formsets.formset_factory(form=form, can_order=can_order, can_delete=can_delete, extra=extra, max_num=max_num)

    class M2MInlineFormSet(M2MFormSet):
        # TODO: Change the parameters to match (parent) formset
        def __init__(self, data=None, instance=None):
            self.instance = instance
            if show_initial:
                initial = [{field_name: i} for i in getattr(self.instance, field_name).all()]
                super(M2MInlineFormSet, self).__init__(data, initial=initial)
            else:
                super(M2MInlineFormSet, self).__init__(data)

        def save(self, commit=True):
            for form in self.forms:
                if form.is_valid() and field_name in form.cleaned_data:
                    getattr(self.instance, field_name).add(form.cleaned_data[field_name])
                    form.save()

    return M2MInlineFormSet
