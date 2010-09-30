# views.py:
# Views for Bin Alerts. 
#
# Copyright (c) 2010 UK Citizens Online Democracy. All rights reserved.
# Email: francis@mysociety.org; WWW: http://www.mysociety.org/


from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response
from django.core.urlresolvers import reverse

from binalerts.forms import LocationForm
from binalerts.models import BinCollection

def frontpage(request):
    if request.method == 'POST': 
        form = LocationForm(request.POST) 
        if form.is_valid(): 
            query = form.cleaned_data['query']
            streets = BinCollection.objects.find_by_street_name(query)

            if len(streets) == 1:
                return HttpResponseRedirect(reverse('show_street', kwargs = { 'url_name' : streets[0].street_url_name })) 
            else:
                raise BaseException("incomplete")
    else:
        form = LocationForm() # An unbound form

    return render_to_response('binalerts/frontpage.html', { 'form': form })

def show_street(request, url_name):
    return render_to_response('binalerts/street.html', { })


