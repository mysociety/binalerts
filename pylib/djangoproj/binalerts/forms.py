# forms.py:
# Forms for Bin Alerts.
#
# Copyright (c) 2010 UK Citizens Online Democracy. All rights reserved.
# Email: francis@mysociety.org; WWW: http://www.mysociety.org/

from django import forms

from binalerts.models import BinCollection, CollectionAlert

class LocationForm(forms.Form):
    query = forms.CharField(error_messages = {
        'required': "Enter either all or part of the name of the street. e.g. Abbey",
    })

    def clean_query(self):
        query = self.cleaned_data['query']

        streets = BinCollection.objects.find_by_street_name(query)
        if len(streets) == 0:
            raise forms.ValidationError("No street found with that name. Try typing a smaller part of it. e.g. Nor")

        self.cleaned_data['streets'] = streets

        return query

class CollectionAlertForm(forms.ModelForm): 
    email = forms.EmailField(label='Your email address', error_messages = {
            'required': 'Please enter your email address.',
            'invalid': 'Please enter a valid email address.'
    })

    class Meta:
        model = CollectionAlert
        fields = ('email',)


