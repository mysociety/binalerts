from django.http import HttpResponse
from django.shortcuts import render_to_response

from binalerts.forms import LocationForm

def frontpage(request):
    if request.method == 'POST': # If the form has been submitted...
        form = LocationForm(request.POST) # A form bound to the POST data
        if form.is_valid(): # All validation rules pass
            # Process the data in form.cleaned_data
            # ...
            return HttpResponseRedirect('/thanks/') # Redirect after POST
    else:
        form = LocationForm() # An unbound form

    return render_to_response('binalerts/frontpage.html', { 'form': form })


