# views.py:
# Views for Bin Alerts. 
#
# Copyright (c) 2010 UK Citizens Online Democracy. All rights reserved.
# Email: francis@mysociety.org; WWW: http://www.mysociety.org/

import re

from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.shortcuts import render_to_response, get_object_or_404
from django.core.urlresolvers import reverse
from django.core.exceptions import ObjectDoesNotExist

from binalerts.forms import LocationForm, CollectionAlertForm
from binalerts.models import BinCollection, Street, CollectionAlert

from emailconfirmation.models import EmailConfirmation

from settings import SECRET_KEY

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
    try:
        street = Street.objects.get(url_name=url_name)
    except ObjectDoesNotExist:
        # Policy for failing to find a street:
        #   break the name down, strip off a trailing postcode (if there is one) and search for
        #   the new name: redirect if there's a single hit, otherwise show the front page
        #   populated with the matches (if any) that were found.
        #   Note this automatically corrects "wrong" postcodes (where the street name is 
        #   unambiguous, which is *probably* what you want).
        lost_street_name_parts = url_name.split('_')
        if len(lost_street_name_parts) > 1 and re.search("^\w\w?\d+$", lost_street_name_parts[-1]):
            lost_street_name_parts = lost_street_name_parts[:-1] # drop the postcode
        lost_street_name = " ".join(lost_street_name_parts)
        streets =  Street.objects.find_by_name(lost_street_name)
        if len(streets)==1:
            return HttpResponseRedirect('/street/' + streets[0].url_name) # careful of looping here
        else:
            return render_to_response('frontpage.html', { 
                'form': LocationForm({'query':lost_street_name}), 
                'streets': Street.objects.find_by_name(lost_street_name)  })
        
    form = CollectionAlertForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            alert = form.save(commit=False)
            alert.street = street
            alert.save()
            EmailConfirmation.objects.confirm(alert)
            return render_to_response('check_email.html')

    # prepare the data to keep things as simple as possible in the template
    
    collection_days = {}         # collect all unique days on which a collection is taking place
    collection_days_by_type = {} # collect all unique types of collection 'g' => [2,5]  (normally, just one day)
    collection_types = {}        # collect unique instances of bin_collection
    collection_types_as_strings = ['' for x in DISPLAY_DAYS_OF_WEEK] # friendly_ids, concatted and sorted, for each day
    
    for bc in street.bin_collections.all().order_by('collection_type__friendly_id', 'collection_day'):
        collection_days[bc.collection_day] = True
        collection_types[bc.collection_type.friendly_id] = bc.collection_type
        day_name = bc.get_collection_day_name()
        try:
            if not (day_name in collection_days_by_type[bc.collection_type.friendly_id]):
                collection_days_by_type[bc.collection_type.friendly_id].append(day_name)
        except KeyError:
            collection_days_by_type[bc.collection_type.friendly_id] = [day_name]
        if collection_types_as_strings[bc.collection_day].find(bc.collection_type.friendly_id) == -1: # haven't got this type already
            collection_types_as_strings[bc.collection_day] += bc.collection_type.friendly_id

    day_by_day_collections = zip(DISPLAY_DAYS_OF_WEEK, collection_types_as_strings)
    collection_types_with_days = [(collection_types[x], collection_days_by_type[x]) for x in sorted(collection_types.keys())]
    return render_to_response('street.html', {
        'street': street, 
        'form': form,  
        'day_by_day_collections': day_by_day_collections, 
        'collection_days': sorted(collection_days.keys()), 
        'collection_types_with_days': collection_types_with_days,
        'daynames': DISPLAY_DAYS_OF_WEEK })

def alert_confirmed(request, id):
    return render_to_response('alert_confirmed.html', {})

def alert_unsubscribed(request, id):
    alert = get_object_or_404(CollectionAlert, id=id)
    
    return render_to_response('alert_unsubscribed.html', {'alert': alert})
