"""
Integration-style tests for binalerts. These tests think of things from the web
frontend point of view. They are designed to make sure the application behaves
as required to the user.
"""

# Various tips on testing forms:
# http://stackoverflow.com/questions/2257958/django-unit-testing-for-form-edit

from django.test import TestCase
from django.test import Client

class FrontPageTest(TestCase):
    def setUp(self):
        self.c = Client()

    def test_asks_for_postcode(self):
        response = self.c.get('/')

        self.assertEqual(response.status_code, 200)

        self.assertEqual(response.template.name, 'binalerts/frontpage.html')
        self.assertContains(response, 'Please enter your postcode')
        self.assertContains(response, '<input type="text" name="postcode" id="id_postcode" />')
        self.assertContains(response, '<input type="submit" value="Go" />')

    def test_error_if_not_postcode(self):
        response = self.c.post('/', { 'postcode': 'notapostcode' })

        self.assertEqual(response.template.name, 'binalerts/frontpage.html')
        self.assertContains(response, 'Sorry')


# Example doctest in case we need it later
__test__ = {"doctest": """
Another way to test that 1 + 1 is equal to 2.

>>> 1 + 1 == 2
True
"""}


