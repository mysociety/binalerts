# views.py:
# Views for Bin Alerts. 
#
# Copyright (c) 2010 UK Citizens Online Democracy. All rights reserved.
# Email: francis@mysociety.org; WWW: http://www.mysociety.org/


from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response
from django.core.urlresolvers import reverse

from binalerts.forms import LocationForm, CollectionAlertForm
from binalerts.models import BinCollection, Street

from emailconfirmation.models import EmailConfirmation

# note: hardcoded daynames here must match binalerts.models.DAY_OF_WEEK_CHOICES (e.g. Sunday has index 0 (not Monday))
DISPLAY_DAYS_OF_WEEK =  ['SUN', 'MON', 'TUE', 'WED', 'THURS', 'FRI', 'SAT']

def frontpage(request):
    streets = None

    if request.method == 'POST': 
        form = LocationForm(request.POST) 
        if form.is_valid(): 
            query = form.cleaned_data['query']
            streets = form.cleaned_data['streets']

            if len(streets) == 1:
                return HttpResponseRedirect(reverse('show_street', kwargs = { 'url_name' : streets[0].url_name })) 
            elif len(streets) > 1:
                pass
            else:
                raise BaseException("internal error: this should have made the form invalid")
    else:
        form = LocationForm() # An unbound form

    return render_to_response('frontpage.html', { 'form': form, 'streets': streets })

def show_street(request, url_name):
    street = Street.objects.get(url_name=url_name)
    form = CollectionAlertForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            alert = form.save(commit=False)
            alert.street = street
            alert.save()
            EmailConfirmation.objects.confirm(request, alert, 'alert_confirmed')
            return render_to_response('check_email.html')    
    return render_to_response('street.html', { 'street': street, 'bin_collections': street.bin_collections.all(), 'form': form, 'daynames': DISPLAY_DAYS_OF_WEEK })

def alert_confirmed(request, id):
    return render_to_response('alert_confirmed.html', { })

