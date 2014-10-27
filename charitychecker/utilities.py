"""
utilities and general functionality necessary
for the operation of the django-charitychecker module.
"""

import urllib2
import io
import zipfile
from contextlib import contextmanager
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


class OpenZipFromURL(object):
    """a context manager for opening a file from a zip
    archive stored at some url location. Will download,
    unzip, and return the file from the archive.
    """

    def __init__(self, zip_url, file_name, *args, **kwargs):
        super(OpenZipFromURL, self).__init__(*args, **kwargs)
        self.zip_url = zip_url
        self.file_name = file_name

    def __enter__(self):
        try:
            # download zip data
            zip_data = urllib2.urlopen(self.zip_url)
            try:
                # convert zip data to proper format
                zip_data_buffer = io.BytesIO(zip_data.read())
                try:
                    # create a ZipFile instance from data
                    zip_file = zipfile.ZipFile(zip_data_buffer)
                    try:
                        # open the desired file from zip archive
                        self.return_file = zip_file.open(self.file_name)
                    except Exception as e:
                        # if return file throws an exception,
                        # make sure it gets closed.
                        self.return_file.close()
                        raise e
                finally:
                    zip_file.close()
            finally:
                zip_data_buffer.close()
        finally:
            zip_data.close()
        # we know have return_file and all the other intermediary
        # files are closed, freeing up the memory
    return self.return_file

    def __exit__(self):
        # make sure that zip file is closed.
        self.return_file.close()


# 2.) change update_charitychecker_data to a general update_database_from_file
# function that takes a context manager and a model, and then updates the
# database.
# 3.) create a mock context manager or some such, then use it to benchmark
# my new database updating command as I optimize it.
# 4.) optimize the database update, and then fix this module, release a
# new version.
class IRSNonprofitDataContextManager(OpenZipFromURL):
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

    def __init__(self):
        super(IRSNonprofitDataContextManager, self).__init__(
            zip_url=IRS_NONPROFIT_DATA_URL
            file_name=TXT_FILE_NAME)
        
    def __enter__(self):
        # always get fresh copy of publication 78
        # before using it. This context manager
        # should only be used by functions/methods
        # meant to run asynchronously like _make_dbm.
        return _normalize_data(
            super(IRSNonprofitDataContextManager, self).__enter__())

    def __exit__(self):
        super(IRSNonprofitDataContextManager, self).__exit__()


def update_database_from_file(file_manager, convert_line,
                              pk_field, model):
    """update the database in bulk using data from a file.
    Inputs:
        file_manager: a context manager that yields an
            iterable where each line contains the data used
            to update.

        convert_line: a function converting each line returned
            by the iterator into a dictionary mapping fields to
            values.

        pk_field: the name of the field which is the primary key
            of the data stored in the database.

        model: the model to be updated.
    """
    pass
            

def update_charitychecker_data():
    update_database_from_file(
        file_manager=IRSNonprofitDataContextManager,
        convert_line=(
            lambda ln: return dict(zip(
                ('ein', 'name', 'city', 'state', 'country', 'deductability_code'),
                ln.split('|')))),
        pk_field='ein',
        model=IRSNonprofitData)

##def update_charitychecker_data():
##    """download a fresh copy of IRS Pub78, process
##    the data and update it into the database.
##    """
##    with IRSNonprofitDataContextManager() as irs_data:
##        for nonprofit_string in irs_data:
##            string_data = nonprofit_string.split('|')
##            nonprofit_data = {
##                'ein': string_data[0],
##                'name': string_data[1],
##                'city': string_data[2],
##                'state': string_data[3],
##                'country': string_data[4],
##                'deductability_code': string_data[5]}
##            try:
##                nonprofit = IRSNonprofitData.objects.get(
##                    pk=nonprofit_data['ein'])
##            except(IRSNonprofitData.DoesNotExist):
##                nonprofit = None
##            if nonprofit:
##                # since there is a nonprofit, run the following code
##                # if any of the fields have been changed.
##                if reduce(
##                    # fold over nonprofit_data as (key, value) pairs,
##                    # checking if nonprofit.key != value, and accumulating
##                    # these checks into a final boolean, True if there has
##                    # been a change to the nonprofit's data.
##                    lambda x, y: (getattr(nonprofit, x[0]) != x[1]) or y,
##                    nonprofit.items(),
##                    False):
##                    # update each field on the model instance
##                    for attr, value in nonprofit_data.items():
##                        setattr(nonprofit, attr, value)
##                    # push updates to the database
##                    nonprofit.save()
##            else:
##                # since there's no nonprofit instance in the database with
##                # the EIN in consideration, create one.
##                IRSNonprofitData(**nonprofit_data).save()
##
