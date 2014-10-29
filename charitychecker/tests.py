"""
unit/integration tests for the django-charitychecker package.
"""
               
import re
import datetime
from StringIO import StringIO
from itertools import izip
import os
from contextlib import contextmanager
from django.test import TestCase
from .models import IRSNonprofitData
from .utilities import (ignore_blank_space, _normalize_data,
                        open_zip_from_url,
                        irs_nonprofit_data_context_manager,
                        update_database_from_file,
                        update_charitychecker_data)

# Global Variables/Mocks

WITH_FORGNS_LOCATION = os.path.join(
    # irs data for testing removal of FORGN
    # registered nonprofits
    os.path.dirname(__file__),
    "test_data/test-data-with-FORGNS.txt")

WITHOUT_FORGNS_LOCATION = os.path.join(
    # irs data for testing removal of FORGN
    # registered nonprofits
    os.path.dirname(__file__),
    "test_data/test-data-without-FORGNS.txt")

MOCK_DATA_LOCATION_BEFORE = os.path.join(
    # mock irs data for intializing the database
    os.path.dirname(__file__), "test_data/mock-irs-data-before.txt")

MOCK_DATA_LOCATION_AFTER = os.path.join(
    # mock irs data for an update afterwards
    os.path.dirname(__file__), "test_data/mock-irs-data-after.txt")

@contextmanager
def irs_mock_data_before():
    """context manager providing mock irs publication
    78 data for initializing the database.
    """
    with open(MOCK_DATA_LOCATION_BEFORE) as mock_data:
        yield mock_data

@contextmanager
def irs_mock_data_after():
    """context manager providing mock irs publication
    78 data for testing update functionality.
    """
    with open(MOCK_DATA_LOCATION_AFTER) as mock_data:
        yield mock_data

# End Global Variables


# Tests for utilities.py

class TestIgnoreBlankSpace(TestCase):
    """test suite for the ignore_blank_space function."""

    def test_is_stable_on_files_without_extra_whitespace(self):
        """run ignore_blank_space on a file with no excess
        whitespace.
        """
        chars = ["a", "b", "c", "d"]
        f = StringIO("\n".join(chars))
        for i, line in enumerate(
            ignore_blank_space(f)):
            self.assertEquals(chars[i], line)

    def test_removes_trailing_whitespace_from_lines(self):
        """run ignore_blank_space on a file with trailing
        whitespace on some lines.
        """
        lines = ["a   ", "   b   ", "c\t", "d", "e \t "]
        answers = ["a", "   b", "c", "d", "e"]
        f = StringIO("\n".join(lines))
        for i, line in enumerate(
            ignore_blank_space(f)):
            self.assertEquals(answers[i], line)

    def test_removes_blank_lines(self):
        """run ignore_blank_space on a file with blank lines
        throughout it.
        """
        f = StringIO("\n\nsome text\n\nmore text\n\n")
        answers = ["some text", "more text"]
        for i, line in enumerate(
            ignore_blank_space(f)):
            self.assertEqual(answers[i], line)


class TestNormalizeData(TestCase):
    """test suite for the normalize_data function."""

    def test_removes_foreign_entities_and_no_one_else(self):
        """run normalize data on a file and check it against
        that file but where I've (semi) manually removed the
        FORGN entities.
        """
        files_are_same = True
        with open(WITH_FORGNS_LOCATION) as before:
            with open(WITHOUT_FORGNS_LOCATION) as after:
                for before_line, after_line in izip(
                    _normalize_data(before),
                    ignore_blank_space(after)):
                    files_are_same = files_are_same and (
                        before_line == after_line)
                self.assertTrue(files_are_same)


class TestOpenZipFromURL(TestCase):
    """test suite for the open_zip_from_url context manager."""
    pass


class TestIRSNonprofitDataContextManager(TestCase):
    """test suite for the IRSNonprofitDataContextManager class."""
    
    def test_download_irs_nonprofit_data(self):
        """download the irs nonprofit data as a sanity check to
        see if exceptions get thrown for internet connections,
        404, etc...
        """
        with irs_nonprofit_data_context_manager() as irs_data:
            pass

    def test_file_format(self):
        """check that the file downloaded from the IRS
        is in the format we expect.
        """
        with irs_nonprofit_data_context_manager() as irs_data:
            in_expected_format = True
            for line in irs_data:
                m = re.match(
                    # a regex to match the following:
                    #     ein|name|city|state|country|deductability_code
                    r'^\d{9}\|.+\|.+\|[A-Z]{2}\|.+\|[A-Z]{2,5}(?:,[A-Z]{2,5})*$',
                    line)
                in_expected_format = in_expected_format and bool(m)
            self.assertTrue(in_expected_format)


class TestUpdateDatabaseFromFile(TestCase):
    """test suite for the update_database_from_file function."""
    pass


class TestUpdateCharitycheckerData(TestCase):
    """test suite for the update_charitychecker_data function."""
        
    def test_update_charitychecker_data_populates_db(self):
        """test that when the update_charitychecker_data
        function is called on an empty database, it populates
        the tables.
        """
        # populate the database
        update_charitychecker_data(
            file_manager=irs_mock_data_before)
        # check that all the information matches the
        # information in IRS Publication 78
        does_information_match = True
        with irs_mock_data_before() as irs_data:
            for line in irs_data:
                nonprofit_data = line.split('|')
                nonprofit = IRSNonprofitData.objects.get(
                    pk=nonprofit_data[0])
                does_information_match = does_information_match and (
                    nonprofit.name == nonprofit_data[1] and
                    nonprofit.city == nonprofit_data[2] and
                    nonprofit.state == nonprofit_data[3] and
                    nonprofit.country == nonprofit_data[4] and
                    nonprofit.deductability_code == nonprofit_data[5])
        self.assertTrue(does_information_match)

    def test_update_charitychecker_data_updates_db(self):
        """test that when the update_charitychecker_data
        function is called on a nonempty database that it
        deletes, updates, and creates the proper nonprofits.
        """
        update_charitychecker_data(
            file_manager=irs_mock_data_before)
        self.assertTrue(
            # check that nonprofit to be deleted is in data
            IRSNonprofitData.objects.get(pk='010407276'))
        with self.assertRaises(IRSNonprofitData.DoesNotExist):
            # check that the nonprofit is not yet in the database
            # 900410317|Blank Family Foundation|Long Lake|MN|United States|PF
            IRSNonprofitData.objects.get(pk='900410317')
        self.assertEquals(
            # 010400845|Bauneg Beg Lake Association Inc.|N Berwick|ME|United States|PC
            IRSNonprofitData.objects.get(pk='010400845').city,
            'N Berwick')
        # update database
        update_charitychecker_data(
            file_manager=irs_mock_data_after)
        # check that the nonprofit was deleted
        ## deleted nonprofit's data:
        # 010407276|Sunrise Opportunities|Machias|ME|United States|PC
        with self.assertRaises(IRSNonprofitData.DoesNotExist):
            # check that the nonprofit was deleted
            IRSNonprofitData.objects.get(pk='010407276')
        # check that the nonprofit was created
        self.assertTrue(
            # check that the nonprofit was created
            IRSNonprofitData.objects.get(pk='900410317'))
        # check that the nonprofit was updated
        self.assertEquals(
            # 010400845|Bauneg Beg Lake Association Inc.|Calais|ME|United States|PC
            IRSNonprofitData.objects.get(pk='010400845').city,
            'Calais')


# Test models.py

class TestIRSNonprofitData(TestCase):
    """test suite for the IRSNonprofitData model."""

    def setUp(self):
        # add Red Cross to the database.
        IRSNonprofitData(
            ein='530196605', name='American National Red Cross',
            city='Charlotte', state='NC', country='United States',
            deductability_code='PC').save()
    
    # testing the verify_nonprofit method
    def test_verify_nonprofit_all_arguments_when_true(self):
        self.assertTrue(IRSNonprofitData.verify_nonprofit(
            ein='530196605', name='American National Red Cross',
            city='Charlotte', state='NC', country='United States',
            deductability_code='PC'))

    def test_verify_nonprofit_some_arguments_when_true_1(self):
        self.assertTrue(IRSNonprofitData.verify_nonprofit(
            ein='530196605', name='American National Red Cross',
            city='Charlotte', state='NC', country='United States',
            deductability_code=None))

    def test_verify_nonprofit_some_arguments_when_true_2(self):
        self.assertTrue(IRSNonprofitData.verify_nonprofit(
            ein='530196605', name='American National Red Cross',
            city='Charlotte', state='NC', country=None,
            deductability_code=None))

    def test_verify_nonprofit_some_arguments_when_true_3(self):
        self.assertTrue(IRSNonprofitData.verify_nonprofit(
            ein='530196605', name='American National Red Cross',
            city='Charlotte'))

    def test_verify_nonprofit_some_arguments_when_true_4(self):
        self.assertTrue(IRSNonprofitData.verify_nonprofit(
            ein='530196605', name='American National Red Cross'))

    def test_verify_nonprofit_some_arguments_when_true_5(self):
        self.assertTrue(IRSNonprofitData.verify_nonprofit(
            ein='530196605', state='NC', country='United States',
            deductability_code='PC'))

    def test_verify_nonprofit_some_arguments_when_true_6(self):
        self.assertTrue(IRSNonprofitData.verify_nonprofit(
            ein='530196605', name=None,
            city='Charlotte', state='NC', country='United States',
            deductability_code='PC'))

    def test_verify_nonprofit_some_arguments_when_true_7(self):
        self.assertTrue(IRSNonprofitData.verify_nonprofit(
            ein='530196605', name='American National Red Cross',
            city=None, state=None, country='United States',
            deductability_code=None))

    def test_verify_nonprofit_just_ein_when_true(self):
        self.assertTrue(IRSNonprofitData.verify_nonprofit(
            ein='530196605'))

    def test_verify_nonprofit_some_arguments_when_false(self):
        self.assertFalse(IRSNonprofitData.verify_nonprofit(
            ein='530196605', name='American National Red Cross',
            city='Boston')) # city is a false argument

    def test_verify_nonprofit_bad_ein(self):
        self.assertFalse(IRSNonprofitData.verify_nonprofit(ein='4'))

    # testing the get_deductability_code method
    def test_get_deductability_code_all_arguments_true(self):
        self.assertEqual(
            IRSNonprofitData.get_deductability_code(
                ein='530196605', name='American National Red Cross',
                city='Charlotte', state='NC', country='United States'),
            'PC')

    def test_get_deductability_code_some_arguments_when_true_1(self):
        self.assertEqual(
            IRSNonprofitData.get_deductability_code(
                ein='530196605', name='American National Red Cross',
                city=None, state='NC', country='United States'),
            'PC')

    def test_get_deductability_code_some_arguments_when_true_2(self):
        self.assertEqual(
            IRSNonprofitData.get_deductability_code(
                ein='530196605', name='American National Red Cross',
                city='Charlotte', state='NC', country=None),
            'PC')

    def test_get_deductability_code_some_arguments_when_true_3(self):
        self.assertEqual(
            IRSNonprofitData.get_deductability_code(
                ein='530196605', name='American National Red Cross',
                city='Charlotte'),
            'PC')

    def test_get_deductability_code_some_arguments_when_true_4(self):
        self.assertEqual(
            IRSNonprofitData.get_deductability_code(
                ein='530196605', name='American National Red Cross'),
            'PC')

    def test_get_deductability_code_some_arguments_when_true_5(self):
        self.assertEqual(
            IRSNonprofitData.get_deductability_code(
                ein='530196605', state='NC', country='United States'),
            'PC')

    def test_get_deductability_code_some_arguments_when_true_6(self):
        self.assertEqual(
            IRSNonprofitData.get_deductability_code(
                ein='530196605', name=None,
                city='Charlotte', state='NC', country='United States'),
            'PC')

    def test_get_deductability_code_some_arguments_when_true_7(self):
        self.assertEqual(
            IRSNonprofitData.get_deductability_code(
                ein='530196605', name='American National Red Cross',
                city=None, state=None, country='United States'),
            'PC')

    def test_get_deductability_code_just_ein_when_true(self):
        self.assertEqual(
            IRSNonprofitData.get_deductability_code(
                ein='530196605'),
            'PC')

    def test_get_deductability_code_some_arguments_when_false(self):
        self.assertEqual(
            IRSNonprofitData.get_deductability_code(
                ein='530196605', name='American National Red Cross',
                city='Boston'), # city is a false argument
            '') 

    def test_get_deductability_code_bad_ein(self):
        self.assertEqual(
            IRSNonprofitData.get_deductability_code(
                ein='6'),
            '')

