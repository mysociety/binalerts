# urls.py:
# Mapping from URLs to view functions for Bin Alerts.
#
# Copyright (c) 2011 UK Citizens Online Democracy. All rights reserved.
# Email: duncan@mysociety.org; WWW: http://www.mysociety.org/

from django.conf.urls.defaults import *
import django.views.static
import djangoproj.settings
from django.contrib import admin

admin.autodiscover()

import binalerts.views
import binalerts.models

urlpatterns = patterns('',
     # Bin alerts
     url(r'^$', binalerts.views.frontpage, name='frontpage'),
     url(r'^street/(?P<url_name>.+)$', 
         binalerts.views.show_street, name='show_street'),
     url(r'^confirmed/(\d+)$', 
         binalerts.views.alert_confirmed, name='alert_confirmed'),
     url(r'^unsubscribed/(\d+)$', 
         binalerts.views.alert_unsubscribed, name='alert_unsubscribed'),

     # Admin
     url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
     url(r'^admin/', include(admin.site.urls)),

     # Email confirmation
     (r'^', include('emailconfirmation.urls'), {'model_type': binalerts.models.CollectionAlert}),
     )
     
if djangoproj.settings.SERVE_STATIC_FILES:
     urlpatterns += patterns('',
         (r'^static/(?P<path>.*)$', django.views.static.serve, 
          {'document_root':djangoproj.settings.MEDIA_ROOT}),
     )
