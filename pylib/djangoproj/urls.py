# urls.py:
# Mapping from URLs to view functions for Bin Alerts.
#
# Copyright (c) 2010 UK Citizens Online Democracy. All rights reserved.
# Email: francis@mysociety.org; WWW: http://www.mysociety.org/

from django.conf.urls.defaults import *
import django.views.static
import djangoproj.settings
from django.contrib import admin

admin.autodiscover()

import binalerts.views

urlpatterns = patterns('',
     # Bin alerts
     url(r'^$', binalerts.views.frontpage, name='frontpage'),
     url(r'^street/(?P<url_name>.+)$', binalerts.views.show_street, name='show_street'),
     url(r'^confirmed/(\d+)$', binalerts.views.alert_confirmed, name='alert_confirmed'),

     # Admin
     url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
     url(r'^admin/', include(admin.site.urls)),

     # Unsubscribe
     url(r'^unsubscribe/(\d+)/([^/]+)/', 'binalerts.views.unsubscribe_collection_alert'),

     # Email confirmation
     (r'^', include('emailconfirmation.urls')),
     )
     
if djangoproj.settings.SERVE_STATIC_FILES:
     urlpatterns += patterns('',
         (r'^static/(?P<path>.*)$', django.views.static.serve, {'document_root':djangoproj.settings.MEDIA_ROOT}),
     )
