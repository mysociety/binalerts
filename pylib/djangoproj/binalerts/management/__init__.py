# __init__.py:
# Management bits for binalerts 
#
# 1) Commands to load in pdf and csv data from Barnet.
# 2) Set the site to the right name and domain using signals.
#
# Copyright (c) 2011 UK Citizens Online Democracy. All rights reserved.
# Email: duncan@mysociety.org; WWW: http://www.mysociety.org/

from south import signals
from django.contrib.sites.models import Site

import settings

def update_default_site(app, **kwargs):
    """Set the default site from settings.py.

    If your project uses the binalerts app, then it's going to want the domain
    and name in sites set to be whatever is in your settings. On migrations
    seems a good time to do this (We can't do it with a fixture, since it
    won't be the same in all cases, and I don't want the fixture to be an
    ugly file...)

    This function just grabs hold of the first site and changes it, so not very
    subtle!

    """
    if app != 'binalerts':
        return

    domain = settings.DOMAIN_NAME
    name = settings.BINS_SITENAME
    
    s = Site.objects.all()[0]
    s.domain = domain
    s.name = name
    s.save()
    Site.objects.clear_cache()

signals.post_migrate.connect(update_default_site)
