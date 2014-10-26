from django.core.management.base import BaseCommand, CommandError
from ...utilities import update_charitychecker_data

class Command(BaseCommand):
    help = ("Downloads new data and makes sure"
            "charitychecker's database is up-to-date.")

    def handle(self, *args, **kwargs):
        """download data and update the charitychecker
        database."""
        self.stdout.write(
            "beginning to download data and update database\n"
            "This could take several minutes.")
        update_charitychecker_data()
        self.stdout.write(
            "finished updating the charitychecker database.")
