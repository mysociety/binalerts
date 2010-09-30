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

class FrontPageTest(TestCase):
    def setUp(self):
        self.c = Client()

    def test_asks_for_street(self):
        response = self.c.get('/')

        self.assertEqual(response.status_code, 200)

        self.assertEqual(response.template.name, 'binalerts/frontpage.html')
        self.assertContains(response, 'Please type the name of your street')
        self.assertContains(response, '<input type="text" name="query" id="id_query" />')
        self.assertContains(response, '<input type="submit" value="Go" />')
        self.assertNotContains(response, 'errorlist')

    def test_error_if_nothing_entered(self):
        response = self.c.post('/', { 'query': '' })

        self.assertEqual(response.template.name, 'binalerts/frontpage.html')
        self.assertContains(response, 'errorlist')


# Example doctest in case we need it later
__test__ = {"doctest": """
Another way to test that 1 + 1 is equal to 2.

>>> 1 + 1 == 2
True
"""}


