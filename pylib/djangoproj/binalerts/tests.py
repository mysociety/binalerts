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

from django.test import TestCase
from django.test import Client

class BinAlertsTestCase(TestCase):
    fixtures = ['barnet_sample.json']

    def setUp(self):
        self.c = Client()

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



# Example doctest in case we need it later
__test__ = {"doctest": """
Another way to test that 1 + 1 is equal to 2.

>>> 1 + 1 == 2
True
"""}


