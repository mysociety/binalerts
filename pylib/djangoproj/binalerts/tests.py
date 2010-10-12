# urls.py:
# Integration-style tests for Bin Alerts. 
#
# These tests think of things from the web frontend point of view. They are
# designed to make sure the application behaves as required to the user.
#
# Copyright (c) 2010 UK Citizens Online Democracy. All rights reserved.
# Email: francis@mysociety.org; WWW: http://www.mysociety.org/

# Various tips on testing forms:
# http://stackoverflow.com/questions/2257958/django-unit-testing-for-form-edit

import os
import re
import datetime

import mysociety

from django.test import TestCase
from django.test import Client
from django.core import mail

from binalerts.models import BinCollection, CollectionAlert

import binalerts

class BinAlertsTestCase(TestCase):
    fixtures = ['barnet_sample.json']

    def setUp(self):
        self.c = Client(HTTP_HOST='testserver')

# Cobranding style
class BarnetStylingTest(BinAlertsTestCase):
    def test_looks_like_barnet_site(self):
        response = self.c.get('/')
        self.assertContains(response, "/barnet/css/basic.css")

# Searching for a street
class StreetSearchTest(BinAlertsTestCase):
    def test_asks_for_street(self):
        response = self.c.get('/')

        self.assertEqual(response.status_code, 200)

        self.assertTemplateUsed(response, 'frontpage.html')
        self.assertContains(response, 'Please type the name of your street')
        self.assertContains(response, '<input type="text" name="query" id="id_query" />')
        self.assertContains(response, '<input type="submit" value="Go" />')
        self.assertContains(response, 'action="/"')
        self.assertNotContains(response, 'errorlist')

    def test_error_if_nothing_entered(self):
        response = self.c.post('/', { 'query': '' })

        self.assertTemplateUsed(response, 'frontpage.html')
        self.assertContains(response, 'errorlist')

    def test_makes_suggestions_if_no_street_found(self):
        response = self.c.post('/', { 'query': 'Xyz' })

        self.assertContains(response, "No street found with that name. Try typing a smaller part of it")

    def test_offers_list_if_many_streets_found(self):
        response = self.c.post('/', { 'query': 'Abb' })

        self.assertContains(response, "Abbots Road")
        self.assertContains(response, "Abbey View")
        self.assertNotContains(response, "Alyth Gardens")

        self.assertContains(response, '<a href="/street/abbots_road">')

    def test_shows_postcode_in_list_when_two_streets_have_same_name(self):
        response = self.c.post('/', { 'query': 'Ashurst Road' })

        self.assertContains(response, "Ashurst Road (N12)")
        self.assertContains(response, "Ashurst Road (EN4)")

        self.assertContains(response, '<a href="/street/ashurst_road_n12">')
        self.assertContains(response, '<a href="/street/ashurst_road_en4">')

    def test_redirects_if_exactly_one_street_found(self):
        response = self.c.post('/', { 'query': 'Alyth Gardens' })
        self.assertRedirects(response, '/street/alyth_gardens')

# Display info about a street
class StreetPageTest(BinAlertsTestCase):
    def test_show_bin_collection_day_on_street_page(self):
        response = self.c.get('/street/alyth_gardens')
 
        self.assertContains(response, 'Green Garden')
        self.assertContains(response, 'Tuesday')
 
    def test_shows_postcode_when_two_streets_have_same_name(self):
        response = self.c.get('/street/ashurst_road_en4')
        self.assertContains(response, "EN4")

# Alerts
class AlertsTest(BinAlertsTestCase):
    def test_shows_alert_form(self):
        response = self.c.get('/street/alyth_gardens')

        self.assertContains(response, 'Email me every week the day before my bins are collected')
        self.assertContains(response, '<input type="text" name="email" id="id_email" />')
        self.assertContains(response, '<input type="submit" value="Subscribe" />')
        self.assertContains(response, 'action=""')

    def test_alert_form_requires_email(self):
        response = self.c.post('/street/alyth_gardens', { 'email': '' })

        self.assertTemplateUsed(response, 'street.html')
        self.assertContains(response, 'errorlist')
        self.assertContains(response, 'Please enter your email address')

    def test_alert_form_requires_valid_email(self):
        response = self.c.post('/street/alyth_gardens', { 'email': 'notanemail' })

        self.assertTemplateUsed(response, 'street.html')
        self.assertContains(response, 'errorlist')
        self.assertContains(response, 'Please enter a valid email address')

    def test_alert_form_accepts_valid_email(self):
        response = self.c.post('/street/alyth_gardens', { 'email': 'francis@mysociety.org' })

        self.assertTemplateUsed(response, 'check_email.html')

    def test_sends_confirmation_email(self):
        self.assertEquals(len(mail.outbox), 0)

        response = self.c.post('/street/alyth_gardens', { 'email': 'francis@mysociety.org' })

        self.assertEquals(len(mail.outbox), 1)
        self.assertEquals(mail.outbox[0].subject, 'Alert confirmation')
        self.assertEquals(mail.outbox[0].from_email, 'Barnet Bin Alerts <%s>' % mysociety.config.get('BUGS_EMAIL'))

    def test_url_in_confirmation_email_works(self):
        # submit to ask for email confirmation
        response = self.c.post('/street/alyth_gardens', { 'email': 'francis@mysociety.org' })

        # check an email arrives
        self.assertEquals(len(mail.outbox), 1)
        body = mail.outbox[0].body

        # check an alert exists...
        collection_alerts = CollectionAlert.objects.all()
        self.assertEquals(1, len(collection_alerts))
        collection_alert = collection_alerts[0]
        self.assertEquals(collection_alert.email, 'francis@mysociety.org')
        self.assertEquals(collection_alert.street_url_name, 'alyth_gardens')
        # ... and it is not confirmed
        self.assertEquals(collection_alert.is_confirmed(), False)

        # get the URL from the email
        url = re.search("\nhttp://testserver(/C/.*)", body).groups()[0]
        #print "confirmation URL is: ", url

        # follow the URL and make sure..
        response = self.c.get(url)
        # ... user is redirected to the right page
        self.assertRedirects(response, '/confirmed/%d' % collection_alert.id)
        # ... alert is now confirmed
        self.assertEquals(collection_alert.is_confirmed(), True)

    # def test_wrong_token_does_not_confirm_email(self):

    def test_alert_is_sent_on_right_day(self):
        # Monday 4th January, no alert
        CollectionAlert.objects.send_pending_alerts(now = datetime.datetime(2010, 1, 4, 9, 00, 00))
        self.assertEquals(len(mail.outbox), 0)

        # Tuesday 5th January, alert
        # CollectionAlert.objects.send_pending_alerts(now = datetime.datetime(2010, 1, 5, 9, 00, 00))
        # self.assertEquals(len(mail.outbox), 1)
        # body = mail.outbox[0].body

        # Wednesday 6th January, no alert
        CollectionAlert.objects.send_pending_alerts(now = datetime.datetime(2010, 1, 6, 9, 00, 00))
        self.assertEquals(len(mail.outbox), 0)

        # Monday 11th January, no alert
        CollectionAlert.objects.send_pending_alerts(now = datetime.datetime(2010, 1, 11, 9, 00, 00))
        self.assertEquals(len(mail.outbox), 0)

        # Tuesday 12th January, alert
        # CollectionAlert.objects.send_pending_alerts(now = datetime.datetime(2010, 1, 12, 9, 00, 00))
        # self.assertEquals(len(mail.outbox), 1)
        # body = mail.outbox[0].body

    # def test_alert_is_sent_only_for_confirmed(self):

# Check data loading functions
class LoadDataTest(BinAlertsTestCase):
    def test_load_data_from_pdf_xml(self):
        # garden_sample_pdf.xml was converted with "pdftohtml -xml" from this file:
        # http://www.barnet.gov.uk/garden-and-kitchen-waste-collection-streets.pdf
        garden_sample_file = os.path.join(os.path.dirname(binalerts.__file__), 'fixtures/garden_sample_pdf.xml')
        BinCollection.objects.load_from_pdf_xml(garden_sample_file)

        # first item in sample file
        response = self.c.post('/', { 'query': 'Ibsley Way' })
        self.assertRedirects(response, '/street/ibsley_way_en4')

        # one in the middle
        response = self.c.post('/', { 'query': 'Jade Close' })
        self.assertRedirects(response, '/street/jade_close_nw2')

        # last item in sample file
        response = self.c.post('/', { 'query': 'Juniper Close' })
        self.assertRedirects(response, '/street/juniper_close_en5')


# Display info about a street


# Example doctest in case we need it later
__test__ = {"doctest": """
Another way to test that 1 + 1 is equal to 2.

>>> 1 + 1 == 2
True
"""}


