from django.core.management.base import BaseCommand, CommandError
from ...utilities import update_charitychecker_data

class Command(BaseCommand):
    help = ("Downloads new data and makes sure"
            "charitychecker's database is up-to-date.")

    def handle(self, *args, **kwargs):
        """download data and update the charitychecker
        database."""
        import time
        self.stdout.write(
            "beginning to download data and update database\n"
            "This could take several minutes.")
        time1 = time.time()
        update_charitychecker_data()
        time2 = time.time()
        self.stdout.write(
            "took %0.3f ms" % ((time2 - time1)*1000))
        self.stdout.write(
            "finished updating the charitychecker database.")
