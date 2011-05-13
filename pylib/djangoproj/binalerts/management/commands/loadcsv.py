import os

from django.core.management.base import BaseCommand
from django.core.management.base import CommandError
from django.db import transaction

from binalerts import models

import binalerts

class Command(BaseCommand):
    def handle(self, *args, **options):
        if len(args) != 1:
            raise CommandError("Only argument is name of .xml file in fixtures directory to load, e.g. garden_sample_pdf.xml")

        #transaction.enter_transaction_management()
        #transaction.managed(True)
        
        file_to_load = os.path.join(os.path.dirname(binalerts.__file__), 'fixtures/', args[0])
        csv_file = open(file_to_load, 'r')
        models.DataImport.load_from_csv_file(csv_file)
