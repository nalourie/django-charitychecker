from django.db import models

########################
# set up a celery task to autoupdate the app's data
########################

class IRSNonprofitData(models.Model):
    """model representing the data attached to each
    nonprofit published in IRS Pub78.
    """
    # make the nonprofit's EIN their primary key
    ein = models.CharField(
        max_length=9, primary_key=True)
    name = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    country = models.CharField(max_length=100)
    deductability_code = models.CharField(max_length=7)

    def verify_nonprofit(
        ein, name=None, city=None, state=None,
        country=None, deductability_code=None):
        """return true if there is a nonprofit in the
        charitychecker database with information matching
        the information provided to the function as
        arguments, return false otherwise.
        """
        try:
            nonprofit = self.objects.get(ein)
        except(self.DoesNotExist):
            return False
        nonprofit_verified = True
        for attr_name, arg_value in [
            ('name', name), ('city', city),
            ('state', state), ('country', country),
            ('deductability_code', deductability_code)]:
            if arg_value != None:
                nonprofit_verified = (
                    nonprofit_verified and
                    arg_value == getattr(nonprofit, attr_name))
        return nonprofit_verified

    def get_deductability_code(
        ein, name=None, city=None, state=None, country=None):
        """if a nonprofit is found in the charitychecker
        database with information matching the information
        provided as arguments to the function, then return that
        nonprofit's deductability code, otherwise return the
        empty string.
        """
        try:
            nonprofit = self.objects.get(ein)
        except(self.DoesNotExist):
            return ''
        nonprofit_verified = True
        for attr_name, arg_value in [
            ('name', name), ('city', city),
            ('state', state), ('country', country)]:
            if arg_value != None:
                nonprofit_verified = (
                    nonprofit_verified and
                    arg_value == getattr(nonprofit, attr_name))
        if nonprofit_verified:
            return nonprofit.deductability_code
        else:
            return ''
        

            
