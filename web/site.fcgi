#!/usr/bin/python
import sys
import os

sys.path.extend([os.path.abspath(x) for x in ("../pylib", "../commonlib/pylib", "../pylib/djangoproj")])

import mysociety.config
mysociety.config.set_file("../conf/general")

os.environ['DJANGO_SETTINGS_MODULE'] = 'djangoproj.settings'

from django.core.servers.fastcgi import runfastcgi
runfastcgi(method='fork', daemonize='false')
