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
    def test_frontpage_asks_for_postcode(self):
        c = Client()
        response = c.get('/')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Please enter your postcode')
        self.assertContains(response, '<input type="text" name="postcode" id="id_postcode" />')
        self.assertContains(response, '<input type="submit" value="Go" />')
        self.assertEqual(response.template.name, 'binalerts/frontpage.html')



# Example doctest in case we need it later
__test__ = {"doctest": """
Another way to test that 1 + 1 is equal to 2.

>>> 1 + 1 == 2
True
"""}


