"""
utilities and general functionality necessary
for the operation of the django-charitychecker module.
"""

import urllib2
import io
import zipfile
from .models import IRSNonprofitData
import re
import os


# Keep these global variables up-to-date

# the url of the IRS publication 78, assumed to
# be a zip folder containing a text file of
# publication 78, in the format:
#    EIN|name|city|state abbreviation|country|deductability code
IRS_NONPROFIT_DATA_URL=(
    "http://apps.irs.gov/"
    "pub/epostcard/data-download-pub78.zip")

# the name that the irs gives to the text file
# version of publication 78 contained in their
# zip file download
TXT_FILE_NAME="data-download-pub78.txt"

# variable to configure where you want publication
# 78 and its update log to be stored on disk
DATA_LOCATION=os.path.join(
    os.path.dirname(__file__), "data")

# dynamically generated path to the irs publication
# 78 file, do not edit/change this variable.
_irs_data_path = os.path.join(
    DATA_LOCATION, TXT_FILE_NAME)

def ignore_blank_space(f):
    """given a text file, return a generator which skips
    blank lines and strips whitespace off the end of each
    line (so no pesky \n characters!).
    """
    for line in f:
        output_line = line.rstrip()
        if output_line:
            yield output_line


def _normalize_data(f):
    """given the IRS Publication 78, normalize the quirks
    out of the data by wrapping it in this generator. The
    data format for FORGN nonprofits is heinously inconsistent
    and poorly defined, so we just filter then out.
    """
    for nonprofit_string in ignore_blank_space(f):
        if not re.match(
            # if it is not a foreign nonprofit, return it.
            r'.*FORGN(?:,[A-Z]{2,5})*$',
            nonprofit_string):
            yield nonprofit_string


class IRSNonprofitDataContextManager(object):
    """a context manager for the nonprofit data
    (EINs and other identifying information)
    contained in IRS Publication 78.

    Returns publication 78 as generator for the lines
    of nonprofit data. It strips blank lines and \n
    characters from the lines in the downloaded Pub78
    file. It also skips all FORGN nonprofits. The
    context manager downloads and unzips a new copy of
    the data every time, to catch new updates.
    """

    def _download_irs_nonprofit_data(self):
        """internal method downloading the irs
        publication 78 data, unzipping it, and
        writing the txt file to disk.
        """
        # with statements are not supported on
        # some of these filetypes, so need to
        # use try finally clauses.
        try:
            # download IRS data
            irs_url_data = urllib2.urlopen(
                IRS_NONPROFIT_DATA_URL)
            try:
                # convert IRS data to proper format
                irs_zip_data = io.BytesIO(
                    irs_url_data.read())
                try:
                    # extract zipfile from IRS data
                    z = zipfile.ZipFile(irs_zip_data)
                    z.extract(member=TXT_FILE_NAME,
                              path=DATA_LOCATION)
                finally:
                    z.close()
            finally:
                irs_zip_data.close()
        finally:
            irs_url_data.close()
    
    def __enter__(self):
        # always get fresh copy of publication 78
        # before using it. This context manager
        # should only be used by functions/methods
        # meant to run asynchronously like _make_dbm.
        self._download_irs_nonprofit_data()
        self.pub78 = open(_irs_data_path, 'r')
        
        return _normalize_data(self.pub78)

    def __exit__(self, exc_type, exc_value, traceback):
        self.pub78.close()


def update_charitychecker_data():
    """download a fresh copy of IRS Pub78, process
    the data and update it into the database.
    """
    with IRSNonprofitDataContextManager() as irs_data:
        for nonprofit_string in irs_data:
            string_data = nonprofit_string.split('|')
            nonprofit_data = {
                'ein': string_data[0],
                'name': string_data[1],
                'city': string_data[2],
                'state': string_data[3],
                'country': string_data[4],
                'deductability_code': string_data[5]}
            try:
                nonprofit = IRSNonprofitData.objects.get(
                    pk=nonprofit_data['ein'])
            except(IRSNonprofitData.DoesNotExist):
                nonprofit = None
            if nonprofit:
                # since there is a nonprofit, run the following code
                # if any of the fields have been changed.
                if reduce(
                    # fold over nonprofit_data as (key, value) pairs,
                    # checking if nonprofit.key != value, and accumulating
                    # these checks into a final boolean, True if there has
                    # been a change to the nonprofit's data.
                    lambda x, y: (getattr(nonprofit, x[0]) != x[1]) or y,
                    nonprofit.items(),
                    False):
                    # update each field on the model instance
                    for attr, value in nonprofit_data.items():
                        setattr(nonprofit, attr, value)
                    # push updates to the database
                    nonprofit.save()
            else:
                # since there's no nonprofit instance in the database with
                # the EIN in consideration, create one.
                IRSNonprofitData(**nonprofit_data).save()

