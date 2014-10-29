"""
utilities and general functionality necessary
for the operation of the django-charitychecker module.
"""

import re
import os
import urllib2
import io
import zipfile
from contextlib import contextmanager
from django.db import transaction
from .models import IRSNonprofitData

# Global Variables
#
# make sure these global variables are up-to-date

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

# End Global Variables


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


@contextmanager
def open_zip_from_url(zip_url, file_name):
    """a context manager for opening a file from a zip
    archive stored at some url location. Will download,
    unzip, and return the file from the archive.
    """
    try:
        # download zip data
        zip_data = urllib2.urlopen(zip_url)
        try:
            # convert zip data to proper format
            zip_data_buffer = io.BytesIO(zip_data.read())
            try:
                # create a ZipFile instance from data
                zip_file = zipfile.ZipFile(zip_data_buffer)
                try:
                    # open the desired file from zip archive
                    return_file = zip_file.open(file_name)
                    yield return_file
                finally:
                    return_file.close()
            finally:
                zip_file.close()
        finally:
            zip_data_buffer.close()
    finally:
        zip_data.close()


@contextmanager
def irs_nonprofit_data_context_manager():
    """context manager for the nonprofit data
    contained in IRS Publication 78.

    Returns IRS Publication 78 data as a generator
    for the lines of nonprofit data. It strips
    blank lines and \n characters from the lines
    in IRS Publication 78 file. It also skips all
    FORGN nonprofits. The context manager downloads
    and unzips a new copy of the data every time so
    as to be up-to-date.
    """
    with open_zip_from_url(
        zip_url=IRS_NONPROFIT_DATA_URL,
        file_name=TXT_FILE_NAME) as zipped_file:
        yield _normalize_data(zipped_file)


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
    with file_manager() as file_data:
        with transaction.atomic():
            db_data_map = {row.pk: row for row in model.objects.all()}
            to_create = []
            progress = 0
            for line in file_data:
                data = convert_line(line)
                row = db_data_map.pop(data[pk_field], None)
                if row:
                    if reduce(
                        lambda acc, (attr_name, attr_value):
                            (getattr(row, attr_name) != attr_value) or acc,
                        data.items(),
                        False):
                        for attr, value in data.items():
                            setattr(row, attr, value)
                        row.save()
                else:
                    to_create.append(model(**data))
            model.objects.bulk_create(to_create)
            model.objects.filter(pk__in=db_data_map).delete()


def update_charitychecker_data(
    # use default value for file manager, allowing mocks to
    # be passed in for testing.
    file_manager=irs_nonprofit_data_context_manager):
    """update the charitychecker database with data from
    IRS Publication 78, downloading a fresh copy of the
    data from the IRS website.
    """
    update_database_from_file(
        file_manager=file_manager,
        convert_line=(
            lambda ln: dict(zip(
                ('ein', 'name', 'city', 'state', 'country', 'deductability_code'),
                ln.split('|')))),
        pk_field='ein',
        model=IRSNonprofitData)

