# forms.py:
# Forms for Bin Alerts.
#
# Copyright (c) 2010 UK Citizens Online Democracy. All rights reserved.
# Email: francis@mysociety.org; WWW: http://www.mysociety.org/

from django import forms
from django.contrib.localflavor.uk.forms import UKPostcodeField

# Due to a bug in UKPostcodeField, can't override error message. This is 
# fixed in: http://code.djangoproject.com/ticket/12017
# So remove this extra class when we have a recent enough Django.
class MyUKPostcodeField(UKPostcodeField):
    default_error_messages = {
        'invalid': 'Sorry, we need your complete UK postcode to work out when your bins are emptied.'
    }

class LocationForm(forms.Form):
    postcode = MyUKPostcodeField(error_messages = {
        'required': 'Please enter your postcode',
        # 'invalid': 'Sorry, we need your complete UK postcode to work out when your bins are emptied.'
    })



