from django.http import HttpResponse
from django.shortcuts import render_to_response

def frontpage(request):
    return render_to_response('binalerts/frontpage.html', {})


