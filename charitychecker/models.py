from django.db import models


class IRSNonprofitData(models.Model):
    """model representing the data attached to each
    nonprofit published in IRS Pub78.
    """
    # make the nonprofit's EIN their primary key
    ein = models.CharField(
        max_length=9, primary_key=True, editable=False)
    name = models.CharField(
        max_length=100, editable=False)
    city = models.CharField(
        max_length=50, editable=False)
    state = models.CharField(
        max_length=2, editable=False)
    country = models.CharField(
        max_length=50, editable=False)
    deductability_code = models.CharField(
        max_length=5, editable=False)

    class Meta:
        verbose_name = "IRS nonprofit datum"
        verbose_name_plural = "IRS nonprofit data"
        
    # string/printing methods
    
    def __unicode__(self):
        return unicode("{name}, EIN: {ein}".format(
            name=self.name, ein=self.ein))

    def __repr__(self):
        return str("<Nonprofit with EIN={ein}>".format(
                ein=self.ein))

    def __str__(self):
        return str(unicode(self))

    @classmethod
    def verify_nonprofit(
        cls, ein, name=None, city=None, state=None,
        country=None, deductability_code=None):
        """return true if there is a nonprofit in the
        charitychecker database with information matching
        the information provided to the function as
        arguments, return false otherwise.
        """
        try:
            nonprofit = cls.objects.get(pk=ein)
        except(cls.DoesNotExist):
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

    @classmethod
    def get_deductability_code(
        cls, ein, name=None, city=None, state=None,
        country=None):
        """if a nonprofit is found in the charitychecker
        database with information matching the information
        provided as arguments to the function, then return that
        nonprofit's deductability code, otherwise return the
        empty string.
        """
        try:
            nonprofit = cls.objects.get(pk=ein)
        except(cls.DoesNotExist):
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

