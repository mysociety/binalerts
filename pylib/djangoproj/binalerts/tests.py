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
import sys
from StringIO import StringIO

from django.test import TestCase
from django.core import mail
from django.http import Http404

from binalerts.models import BinCollectionType, BinCollection, CollectionAlert, Street, DataImport
from emailconfirmation.models import EmailConfirmation

import settings
import binalerts

class BinAlertsTestCase(TestCase):
    fixtures = ['test_data.json']

# Cobranding style
class BarnetStylingTest(BinAlertsTestCase):
    def test_looks_like_barnet_site(self):
        response = self.client.get('/')
        self.assertContains(response, "/barnet/css/basic.css")

# Searching for a street
class StreetSearchTest(BinAlertsTestCase):
    def test_asks_for_street(self):
        response = self.client.get('/')

        self.assertEqual(response.status_code, 200)

        self.assertTemplateUsed(response, 'frontpage.html')
        self.assertContains(response, 'Please enter the name of your&nbsp;street')
        self.assertContains(response, '<input type="text" name="query" id="id_query" />')
        self.assertContains(response, '<input type="submit" value="Go" />')
        self.assertContains(response, 'action="/"')
        self.assertNotContains(response, 'errorlist')

    def test_error_if_nothing_entered(self):
        response = self.client.post('/', { 'query': '' })

        self.assertTemplateUsed(response, 'frontpage.html')
        self.assertContains(response, 'errorlist')

    def test_makes_suggestions_if_no_street_found(self):
        response = self.client.post('/', { 'query': 'Xyz' })

        self.assertContains(response, "No street found with that name. Try typing a smaller part of it")

    def test_offers_list_if_many_streets_found(self):
        response = self.client.post('/', { 'query': 'Abb' })

        self.assertContains(response, "Abbots Road")
        self.assertContains(response, "Abbey View")
        self.assertNotContains(response, "Alyth Gardens")

        self.assertContains(response, '<a href="/street/abbots_road">')

    def test_shows_postcode_in_list_when_two_streets_have_same_name(self):
        response = self.client.post('/', { 'query': 'Ashurst Road' })

        self.assertContains(response, "Ashurst Road (N12)")
        self.assertContains(response, "Ashurst Road (EN4)")

        self.assertContains(response, '<a href="/street/ashurst_road_n12">')
        self.assertContains(response, '<a href="/street/ashurst_road_en4">')

    def test_redirects_if_exactly_one_street_found(self):
        response = self.client.post('/', { 'query': 'Alyth Gardens' })
        self.assertRedirects(response, '/street/alyth_gardens')

# Display info about a street
class StreetPageTest(BinAlertsTestCase):
    def test_show_bin_collection_day_on_street_page(self):
        response = self.client.get('/street/alyth_gardens')
 
        self.assertContains(response, '<title>Bin collection days for Alyth Gardens</title>')
        self.assertContains(response, 'Green Garden')
        self.assertContains(response, '<div class="mysoc-bin-day mysoc-bin-collection-g">') 
        self.assertContains(response, '<div class="mysoc-bin-summary mysoc-bin-summary-g">') 

        self.assertNotContains(response, 'Monday')
        self.assertContains(   response, 'Tuesday')
        self.assertNotContains(response, 'Wednesday')
        self.assertNotContains(response, 'Thursday')
        self.assertNotContains(response, 'Friday')
        self.assertNotContains(response, 'Saturday')
        self.assertNotContains(response, 'Sunday')
        
        self.assertContains(response, 'id="alert_form"') # offers user chance to subscribe to alerts
        
    def test_shows_postcode_when_two_streets_have_same_name(self):
        response = self.client.get('/street/ashurst_road_en4')
        self.assertContains(response, "EN4")

    def test_shows_both_collections_on_street_page(self):
        response = self.client.get('/street/ashurst_road_en4')
        self.assertContains(response, '<strong>Green Garden and Kitchen Waste</strong> collection day is <strong>Tuesday')
        self.assertContains(response, '<strong>Domestic Waste</strong> collection day is <strong>Thursday')
        self.assertContains(response, '<div class="mysoc-bin-day mysoc-bin-collection-g">') 
        self.assertContains(response, '<div class="mysoc-bin-day mysoc-bin-collection-d">') 
        
    def test_shows_message_when_street_has_no_collections(self):
        response = self.client.get('/street/no_collections_road')
        self.assertContains(response, "There is no collection data available for this street")
        self.assertNotContains(response, 'id="alert_form"') # does not offer user chance to subscribe to alerts
        
# Alerts
class AlertsTest(BinAlertsTestCase):
    def test_shows_alert_form(self):
        response = self.client.get('/street/alyth_gardens')

        self.assertContains(response, 'Want a reminder?')
        self.assertContains(response, 'We can email you every week')
        self.assertContains(response, '<input type="text" name="email" id="id_email" />')
        self.assertContains(response, '<input type="submit" value="Subscribe" />')
        self.assertContains(response, 'action=""')

    def test_alert_form_requires_email(self):
        response = self.client.post('/street/alyth_gardens', { 'email': '' })

        self.assertTemplateUsed(response, 'street.html')
        self.assertContains(response, 'errorlist')
        self.assertContains(response, 'Please enter your email address')

    def test_alert_form_requires_valid_email(self):
        response = self.client.post('/street/alyth_gardens', { 'email': 'notanemail' })

        self.assertTemplateUsed(response, 'street.html')
        self.assertContains(response, 'errorlist')
        self.assertContains(response, 'Please enter a valid email address')

    def test_alert_form_accepts_valid_email(self):
        response = self.client.post('/street/alyth_gardens', { 'email': 'francis@mysociety.org' })

        self.assertTemplateUsed(response, 'check_email.html')

    def test_sends_confirmation_email(self):
        self.assertEquals(len(mail.outbox), 0)

        response = self.client.post('/street/alyth_gardens', { 'email': 'francis@mysociety.org' })

        self.assertEquals(len(mail.outbox), 1)
        self.assertEquals(mail.outbox[0].subject, 'Alert confirmation')
        self.assertEquals(mail.outbox[0].from_email, 'Barnet Bin Alerts <%s>' %settings.SERVER_EMAIL)
        assert mail.outbox[0].body.find("The Bin Team") != -1, '"The Bin Team" wasn\'t in the email body; using wrong emailconfirmation template?'

    def test_url_in_confirmation_email_works(self):
        # submit to ask for email confirmation
        response = self.client.post('/street/alyth_gardens', { 'email': 'francis@mysociety.org' })

        # check an email arrives
        self.assertEquals(len(mail.outbox), 1)
        body = mail.outbox[0].body

        # check an alert exists...
        collection_alerts = CollectionAlert.objects.all()
        self.assertEquals(1, len(collection_alerts))
        collection_alert = collection_alerts[0]
        self.assertEquals(collection_alert.email, 'francis@mysociety.org')
        self.assertEquals(collection_alert.street.url_name, 'alyth_gardens')
        # ... and it is not confirmed
        self.assertEquals(collection_alert.is_confirmed(), False)

        # get the URL from the email
        url = re.search("\nhttp://example.com(/C/.*)", body).groups()[0]
        #print "confirmation URL is: ", url

        # follow the URL and make sure..
        response = self.client.get(url)
        # ... user is redirected to the right page
        self.assertRedirects(response, '/confirmed/%d' % collection_alert.id)
        # ... alert is now confirmed
        self.assertEquals(collection_alert.is_confirmed(), True)

    # def test_wrong_token_does_not_confirm_email(self):

    def test_no_alerts_sent_if_not_confirmed_alert(self):
        street = Street.objects.create(name='Alyth Gardens', url_name='alyth_gardens', partial_postcode='XX0') 
        alert = CollectionAlert.objects.create(street=street, email='francis@mysociety.org')
        EmailConfirmation.objects.create(confirmed = False, content_object = alert)
        assert alert.is_confirmed() == False

        for day_of_month in range(3, 12):
            CollectionAlert.objects.send_pending_alerts(now = datetime.datetime(2010, 1, day_of_month, 9, 00, 00))
            self.assertEquals(len(mail.outbox), 0)

    def test_alerts_sent_if_confirmed_alert(self):
        # make an alert for Alyth Gardens
        collection_type = BinCollectionType.objects.get(friendly_id='G')
        street = Street.objects.create(name='Alyth Gardens', url_name='alyth_gardens', partial_postcode='XX0') 
        bin_collection = BinCollection.objects.create(collection_day=2, collection_type=collection_type, street=street)
        collection_type = BinCollectionType.objects.get(friendly_id='D')
        bin_collection2 = BinCollection.objects.create(collection_day=2, collection_type=collection_type, street=street)
        alert = CollectionAlert.objects.create(street=street, email = 'francis@mysociety.org')
        email_confirmation = EmailConfirmation.objects.create(confirmed = True, content_object = alert)

        assert alert.is_confirmed() == True
        
        # In production, the cron job (conf/crontab.ugly) is called at 9am
        # every day. This test simulates as if the cron ran for an arbitary
        # range of dates in January 2010. The date range covers two Mondays, to
        # check the alerts are sent on those days, and not on others.
        for day_of_month in range(3, 12):
            # fake the day/time the alerts are sent for testing purposes
            faked_now = datetime.datetime(2010, 1, day_of_month, 9, 00, 00)
            CollectionAlert.objects.send_pending_alerts(now = faked_now)
            if len(mail.outbox) > 0:
                m = mail.outbox[0]
                # print "Subject:", m.subject
                # print m.body
            # we expect an alert on Monday for Tuesday - both 4th, 11th January 2010 are Mondays
            if day_of_month == 4 or day_of_month == 11: 
                self.assertEquals(len(mail.outbox), 1)
                assert "Green Garden" in m.body
                assert "Domestic" in m.body
                assert "Tuesday" in m.body
                assert "Alyth Gardens" in m.body

                # Check that there is an unsubscribe link in the email
                assert 'http://example.com/D/' in m.body, 'No unsubscribe link in email body'
            else:
                self.assertEquals(len(mail.outbox), 0)
            mail.outbox = []
        # the (only) collection alert should remember when the last email was sent
        assert CollectionAlert.objects.all()[0].last_sent_date == datetime.date(2010, 01, 11)

    def test_unsubscribe_successful(self):
        test_email = 'duncan@mysociety.org'
        
        street = Street.objects.create(name='Alyth Gardens', url_name='alyth_gardens', partial_postcode='XX0') 
        alert = CollectionAlert.objects.create(street=street, email=test_email)
        alert.confirmed.create(confirmed=True)

        unsubscribe_path = alert.confirmed.all()[0].path_for_unsubscribe()
        
        response = self.client.get(unsubscribe_path, follow=True)

        self.assertRedirects(response, '/unsubscribed/%d' %alert.id)

        self.assertTemplateUsed(response, 'alert_unsubscribed.html')
        self.assertContains(response, "Alyth")
        self.assertContains(response, test_email)

        assert not alert.is_confirmed()
        

# Check data loading functions
class LoadDataTest(BinAlertsTestCase):
            
    def test_load_data_from_pdf_xml(self):
        # garden_sample_pdf.xml was converted with "pdftohtml -xml" from this file:
        # http://www.barnet.gov.uk/garden-and-kitchen-waste-collection-streets.pdf

        old_BINS_ALLOW_MULTIPLE_COLLECTIONS_PER_WEEK = settings.BINS_ALLOW_MULTIPLE_COLLECTIONS_PER_WEEK
        settings.BINS_ALLOW_MULTIPLE_COLLECTIONS_PER_WEEK = False
        
        try:
        
            LoadDataTest.old_stdout = sys.stdout
            sys.stdout = StringIO()

            collection_type = BinCollectionType.objects.get(friendly_id='G')
        
            garden_sample_file = os.path.join(os.path.dirname(binalerts.__file__), 'fixtures/sample_garden_from_pdf.xml')
            DataImport.load_from_pdf_xml(garden_sample_file, collection_type=collection_type)

            # first item in sample file
            response = self.client.post('/', { 'query': 'Ibsley Way' })
            self.assertRedirects(response, '/street/ibsley_way_en4')

            # one in the middle
            response = self.client.post('/', { 'query': 'Jade Close' })
            self.assertRedirects(response, '/street/jade_close_nw2')

            # last item in sample file
            response = self.client.post('/', { 'query': 'Juniper Close' })
            self.assertRedirects(response, '/street/juniper_close_en5')

            # check that postcodes are indeed being loaded (and not simply being put into the url_name)
            a_street = Street.objects.get(name="Juniper Close")
            self.assertEquals(a_street.partial_postcode, 'EN5')

            # multiple partial postcodes e.g. EN5/N20 are ignored for now
            response = self.client.post('/', { 'query': 'Barnet Lane' })
            self.assertContains(response, "No street found with that name.")

            # multiple days of week e.g Tuesday/Thursday are ignored for now
            # would be better to test the output (stdout?) from the import task, but this is its consequence
            response = self.client.post('/', { 'query': 'Athenaeum Road' })
            self.assertContains(response, "No street found with that name.")
            
            # they are green/garden waste (the default for xml import)
            response = self.client.get('/street/juniper_close_en5')
            self.assertContains(response, 'Green Garden')

        finally:
            settings.BINS_ALLOW_MULTIPLE_COLLECTIONS_PER_WEEK = old_BINS_ALLOW_MULTIPLE_COLLECTIONS_PER_WEEK

    def test_load_data_from_pdf_xml_with_multiple_days(self):
        old_BINS_ALLOW_MULTIPLE_COLLECTIONS_PER_WEEK = settings.BINS_ALLOW_MULTIPLE_COLLECTIONS_PER_WEEK
        settings.BINS_ALLOW_MULTIPLE_COLLECTIONS_PER_WEEK = True
        try:
            collection_type = BinCollectionType.objects.get(friendly_id='G') 
        
            garden_sample_file = os.path.join(os.path.dirname(binalerts.__file__), 'fixtures/sample_garden_from_pdf.xml')
            DataImport.load_from_pdf_xml(garden_sample_file, collection_type=collection_type)

            # multiple days of week e.g Tuesday/Thursday are handled OK
            response = self.client.get('/street/athenaeum_road_n20')
            #import pdb; pdb.set_trace()
            self.assertContains(response, "Kitchen Waste</strong> collection days are <strong>Tuesday &amp; Thursday")
        finally:
            settings.BINS_ALLOW_MULTIPLE_COLLECTIONS_PER_WEEK = old_BINS_ALLOW_MULTIPLE_COLLECTIONS_PER_WEEK


    def test_load_data_from_csv_without_postcodes(self):
        collection_type = BinCollectionType.objects.get(friendly_id='D') 
        
        # sample_domestic_no_postcodes.csv is the first few lines from a Barnet spreadsheet, exported to CSV 
        domestic_sample_file = os.path.join(os.path.dirname(binalerts.__file__), 'fixtures/sample_domestic_no_postcodes.csv')
        DataImport.load_from_csv_file(open(domestic_sample_file, 'r'), collection_type=collection_type, guess_postcodes=True)

        response = self.client.post('/', { 'query': 'Amber Grove' })
        self.assertContains(response, "No street found with that name. Try typing a smaller part of it")
        
        response = self.client.get('/street/juniper_close')
        self.assertContains(response, "No street found with that name. Try typing a smaller part of it")

    # in this case, xml has postcodes
    # the cvs file doesn't have postcodes, but where streets match, they should snap to the existing ones (guess postcde)
    def test_load_data_from_pdf_then_csv(self):
        Street.objects.all().delete() # not using fixtures here

        collection_type = BinCollectionType.objects.get(friendly_id='G') 
        garden_sample_file = os.path.join(os.path.dirname(binalerts.__file__), 'fixtures/sample_garden_from_pdf.xml')
        DataImport.load_from_pdf_xml(garden_sample_file, collection_type=collection_type)

        collection_type = BinCollectionType.objects.get(friendly_id='D') 
        domestic_sample_file = os.path.join(os.path.dirname(binalerts.__file__), 'fixtures/sample_domestic_no_postcodes.csv')
        DataImport.load_from_csv_file(open(domestic_sample_file, 'r'), collection_type=collection_type, guess_postcodes=True)

        # Should snap to the (only) Juniper Close (with postcode)
        response = self.client.get('/street/juniper_close')
        self.assertRedirects(response, '/street/juniper_close_en5')

        response = self.client.get('/street/juniper_close_en5')
        self.assertContains(response, 'Domestic') # from csv import, because postcode was guessed OK
        self.assertContains(response, 'Garden') # from xml import

        response = self.client.post('/', { 'query': 'Amber Grove' })
        self.assertContains(response, "No street found with that name. Try typing a smaller part of it") # not imported from csv, had no postcode


    def test_load_data_from_csv_then_pdf(self): 
        Street.objects.all().delete() # not using fixtures here
        garden_sample_file = os.path.join(os.path.dirname(binalerts.__file__), 'fixtures/sample_garden_from_pdf.xml')
        DataImport.load_from_pdf_xml(garden_sample_file, collection_type=BinCollectionType.objects.get(friendly_id='G'))
        domestic_sample_file = os.path.join(os.path.dirname(binalerts.__file__), 'fixtures/sample_domestic_no_postcodes.csv')
        DataImport.load_from_csv_file(open(domestic_sample_file, 'r'), collection_type=BinCollectionType.objects.get(friendly_id='D'))

        # Juniper Close in csv doesn't have postcode... should snap to the (only) Juniper Close (with postcode) and
        # not create a record -- instead, redirecting to it
        response = self.client.get('/street/juniper_close')
        self.assertRedirects(response, '/street/juniper_close_en5')

        response = self.client.get('/street/juniper_close_en5')
        self.assertContains(response, 'Garden') # from xml import
        self.assertNotContains(response, 'Domestic') # from the csv import, which had no postcode


    def test_load_data_from_native_csv(self):
        collection_type = BinCollectionType.objects.get(friendly_id='D') 
        # sample_ideal.csv is in the nativce CSV format, rather than a proprietary one
        sample_file = os.path.join(os.path.dirname(binalerts.__file__), 'fixtures/sample_native.csv')
        DataImport.load_from_csv_file(open(sample_file, 'r'), collection_type=collection_type, guess_postcodes=False)

        response = self.client.get('/street/test_road')
        self.assertRedirects(response, '/street/test_road_ab1')

        response = self.client.get('/street/test_road_ab1')
        self.assertContains(response, 'Garden') 
        self.assertContains(response, 'Domestic') 
        self.assertContains(response, 'Friday')
        self.assertNotContains(response, 'Recycl')

# Display info about a street


# Example doctest in case we need it later
__test__ = {"doctest": """
Another way to test that 1 + 1 is equal to 2.

>>> 1 + 1 == 2
True
"""}


