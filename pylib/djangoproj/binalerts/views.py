# views.py:
# Views for Bin Alerts. 
#
# Copyright (c) 2010 UK Citizens Online Democracy. All rights reserved.
# Email: francis@mysociety.org; WWW: http://www.mysociety.org/

import os
import re
import datetime

from operator import itemgetter, attrgetter

from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.shortcuts import render_to_response, get_object_or_404
from django.core.urlresolvers import reverse
from django.contrib.admin.views.decorators import staff_member_required

from binalerts.forms import LocationForm, CollectionAlertForm
from binalerts.models import BinCollection, BinCollectionType, Street, CollectionAlert

from emailconfirmation.models import EmailConfirmation

from settings import SECRET_KEY
from settings import BINS_SITENAME
from settings import BINS_DISPLAY_FIRST_DAY
from settings import BINS_DISPLAY_DAYS_SHOWN
from settings import BINS_DISPLAY_SHOW_DATES

# note: hardcoded daynames here must match binalerts.models.DAY_OF_WEEK_CHOICES (e.g. Sunday has index 0 (not Monday))
DISPLAY_DAYS_OF_WEEK =  ['SUN', 'MON', 'TUE', 'WED', 'THURS', 'FRI', 'SAT']

# XXX this array preferred because Monday has index 0, which is what Python expects
DAYS_OF_WEEK_TRUNCATED = ['MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT', 'SUN']

CSS_DAY_IN_PAST = 'past' # used for style in past: should not collide with a collection friendly_id
DAYS_PER_DISPLAY_WEEK = 7 # CSS expects this to be 7: if you change it, change width: XX% in CSS for .mysoc-bin-day

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
    except Street.DoesNotExist:
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
            template_name = get_site_template_name('frontpage.html')
            return render_to_response(template_name, { 
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
    
    class CollectionSummary:
            def __init__(self, bctype, first_date, when_array):
                self.bctype = bctype
                self.first_date = first_date
                self.when_array = when_array # when_array: pretty text saying when ("Tuesday", "tomorrow" as array (for multi days))
            def __repr__(self):
                return repr((self.bctype, self.first_date, self.when_array))
        
    first_dates_dict = {}    # collection types displayed, earliest collections first XXX day names only good for weeklies!
    display_weeks = []
    dd_dates = []           # days to be displayed: dates
    dd_types = []           # days to be displayed: tpyes as string (e.g., DG for Domestic and Garden)
    
    # calculate date of BINS_DISPLAY_FIRST_DAY: if it's a day of the week, then it's the most recent one (past)
    todays_date = datetime.date.today()
    start_date = todays_date
    if BINS_DISPLAY_FIRST_DAY == 'tomorrow':
        start_date = start_date + datetime.timedelta(days=1)
    elif BINS_DISPLAY_FIRST_DAY == 'yesterday':
        start_date = start_date - datetime.timedelta(days=1)
    elif BINS_DISPLAY_FIRST_DAY != 'today':
        try:
            start_day_of_week =  DAYS_OF_WEEK_TRUNCATED.index(BINS_DISPLAY_FIRST_DAY.upper()[:3])
        except ValueError:
            raise ValueError("config error: setting BINS_DISPLAY_FIRST_DAY=\"%s\" seems wrong, expected a day name (e.g., \"Sunday\"), or \"today\", \"tomorrow\" or \"yesterday\"" % BINS_DISPLAY_FIRST_DAY)
        for i in range(7):
            if start_date.weekday() == start_day_of_week:
                break
            start_date = start_date - datetime.timedelta(days=1) # go *back* a day and try again
    
    for day_count in range(BINS_DISPLAY_DAYS_SHOWN):
        collection_date = start_date +  datetime.timedelta(days=day_count)
        bins_day_of_week = (collection_date.weekday() + 1) % 7 # XXX annoying fudge: bins's Monday=0, Python's Monday=1 ?
        dd_dates.append(collection_date)
        dd_types.append('')
        if collection_date < todays_date:
            dd_types[day_count] = CSS_DAY_IN_PAST # currently: don't show (ghost?) collections in the past
        else:
            # ================*** find collection dates in this date range here! ***====================== 
            # note currently this is based *only* on day of week, not dates etc
            for bc in  street.bin_collections.filter(collection_day=bins_day_of_week).order_by('collection_type__friendly_id'):
                if dd_types[day_count].find(bc.collection_type.friendly_id) == -1: # haven't got this type already
                    dd_types[day_count] += bc.collection_type.friendly_id
                this_day = bc.get_collection_day_name()
                if not bc.collection_type.friendly_id in first_dates_dict:
                    first_dates_dict[bc.collection_type.friendly_id] = CollectionSummary(bc.collection_type, collection_date, [this_day])
                elif not this_day in first_dates_dict[bc.collection_type.friendly_id].dates_string:
                        first_dates_dict[bc.collection_type.friendly_id].dates_string.append(this_day)

    # break days down into weeks
    for day_count in range(0, BINS_DISPLAY_DAYS_SHOWN, DAYS_PER_DISPLAY_WEEK):
        display_weeks.append(zip(dd_dates[day_count:day_count+DAYS_PER_DISPLAY_WEEK], dd_types[day_count:day_count+DAYS_PER_DISPLAY_WEEK]))
    
    return render_to_response(get_site_template_name('street.html'), {
        'street': street, 
        'form': form, 
        'show_dates': BINS_DISPLAY_SHOW_DATES,
        'display_weeks': display_weeks,
        'collection_summaries': sorted(first_dates_dict.values(), key=attrgetter('first_date', 'bctype.friendly_id'))
        })

def alert_confirmed(request, id):
    return render_to_response('alert_confirmed.html')

def alert_unsubscribed(request, id):
    alert = get_object_or_404(CollectionAlert, id=id)
    
    return render_to_response('alert_unsubscribed.html', {'alert': alert})

@staff_member_required
def admin_street_report(request):
    num_all_types = 0 # count all streets which have all types of collection
    percent_all_types = "0"
    types = BinCollectionType.objects.all().order_by('friendly_id')
    street_data = []
    for street in Street.objects.all().order_by('name', 'partial_postcode'):
        counts = []
        num_collections = 0
        num_types = 0
        is_multi = False
        for t in types:
            c = street.bin_collections.filter(collection_type=t).count()
            if c > 0:
                num_collections += c
                num_types += 1
                if c > 1:
                    is_multi = True
            counts.append(c)
        street_data.append((street, num_collections, num_types, is_multi, counts))
        if num_types == len(types):
            num_all_types += 1
    if len(street_data) > 0:
        percent_all_types = int(100 * num_all_types/len(street_data))
    return render_to_response('admin_street_report.html', {
        'street_data':street_data, 
        'bin_types':types, 
        'num_all_types':num_all_types,
        'percent_all_types':percent_all_types})

# use a site-name template if it exists
def get_site_template_name(template_name):
    return template_name
    confirmed_template_name = template_name
    if BINS_SITENAME == 'barnet':
        confirmed_template_name = BINS_SITENAME + '/' + template_name
        if not os.path.exists(confirmed_template_name):
            confirmed_template_name = template_name
    return confirmed_template_name