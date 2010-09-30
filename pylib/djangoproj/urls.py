# urls.py:
# Mapping from URLs to view functions for Bin Alerts.
#
# Copyright (c) 2010 UK Citizens Online Democracy. All rights reserved.
# Email: francis@mysociety.org; WWW: http://www.mysociety.org/

from django.conf.urls.defaults import *
from django.contrib import admin

admin.autodiscover()

import binalerts.views

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
     # Bin alerts
     (r'^$', binalerts.views.frontpage),

     # Admin
     (r'^admin/doc/', include('django.contrib.admindocs.urls')),
     (r'^admin/', include(admin.site.urls)),
)
