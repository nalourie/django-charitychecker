"""
unit/integration tests for the django-charitychecker package.
"""

# because this test suite also tests the downloading and database
# building functionality, it can take a very long time. If someone
# wants to switch some of these tests to mocks, it'd be much
# appreciated.
               
import re
import datetime
from StringIO import StringIO
from itertools import izip
import os
from django.test import TestCase
from .models import IRSNonprofitData
from .utilities import (ignore_blank_space, _normalize_data,
                        IRSNonprofitDataContextManager,
                        update_charitychecker_data,
                        _irs_data_path)


class TestIRSNonprofitDataContextManager(TestCase):
    """test suite for the IRSNonprofitDataContextManager class."""
    
    # Some of these tests will have side effects,
    # i.e., downloading a file to disk. Tests with side
    # effects have been marked with a comment. These tests
    # should not be run while the module is in use.
    def test__download_irs_nonprofit_data(self):
        # get fresh copy of irs and check for exceptions
        # in writing permissions, internet connections,
        # etc...
        IRSNonprofitDataContextManager(
            )._download_irs_nonprofit_data()

    def test_context_manager_updates_data(self):
        """check that opening the context manager
        updates the local irs pub78 data.
        """
        with open(_irs_data_path, 'a+') as irs_data:
            irs_data.write("TESTSTRING_FOR_CHARITYCHECK")
            found_test_phrase = False
            irs_data.seek(-27, 2)
            for line in irs_data:
                if "TESTSTRING_FOR_CHARITYCHECK" in line:
                    found_test_phrase = True
            # check that the test fails before we use
            # the context manager.
            self.assertTrue(found_test_phrase)
        with IRSNonprofitDataContextManager() as new_irs_data:
            # see if we've overwritten the old file
            found_test_phrase = False
            for line in new_irs_data:
                if "TESTSTRING_FOR_CHARITYCHECK" in line:
                    found_test_phrase = True
            # assert that the test phrase has been overwritten
            self.assertFalse(found_test_phrase)

    def test_file_format(self):
        """check that the file downloaded from the IRS
        is in the format we expect.
        """
        with IRSNonprofitDataContextManager() as irs_data:
            in_expected_format = True
            for line in irs_data:
                m = re.match(
                    # a regex to match the following:
                    #     ein|name|city|state|country|deductability_code
                    r'^\d{9}\|.+\|.+\|[A-Z]{2}\|.+\|[A-Z]{2,5}(?:,[A-Z]{2,5})*$',
                    line)
                in_expected_format = in_expected_format and bool(m)
            self.assertTrue(in_expected_format)


class TestUpdateCharitycheckerData(TestCase):
    """test suite for the update_charitychecker_data function."""
        
    def test_update_charitychecker_data_populates_db(self):
        """test that when the update_charitychecker_data
        function is called on an empty database, it populates
        the tables.
        """
        # populate the database
        print "before charity checker"
        update_charitychecker_data()
        print "after"
        # check that all the information matches the
        # information in IRS Publication 78
        does_information_match = True
        with IRSNonprofitDataContextManager() as irs_data:
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
        before_filename = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "test-data-with-FORGNS.txt")
        after_filename = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "test-data-without-FORGNS.txt")
        with open(before_filename) as before:
            with open(after_filename) as after:
                for before_line, after_line in izip(
                    _normalize_data(before),
                    ignore_blank_space(after)):
                    files_are_same = files_are_same and (
                        before_line == after_line)
                self.assertTrue(files_are_same)


class TestIRSNonprofitData(TestCase):
    """test suite for the IRSNonprofitData model."""
    
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

