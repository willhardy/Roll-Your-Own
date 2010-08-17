# -*- coding: UTF-8 -*-
from django import forms

class DeliveryForm(forms.Form):
    address = forms.CharField()
    pickup  = forms.BooleanField(required=False)
    state   = forms.ChoiceField(required=False, choices=(("One", "One"),("Two","Two")))

    def __init__(self, *args, **kwargs):
        self.instance = kwargs.pop('instance', None)
        super(DeliveryForm, self).__init__(*args, **kwargs)

    def save(self, commit=True):
        self.instance.address = self.cleaned_data['address']
        self.instance.save()
