django-charitychecker
=====================

A django app for verifying U.S. nonprofits by their EIN number. For a
general python module with similar functionality, check out
`charitycheck <https://github.com/nalourie/charitycheck>`__.

Visit the
`github <https://github.com/nalourie/django-charitychecker>`__.

Installation:
=============

From pip:

::

    pip install django-charitychecker

In your settings.py:

.. code:: python

    INSTALLED_APPS = (
        ...
        charitychecker
        ...
        )

Note that if you want django-charitychecker to work properly, you'll
need to periodically fetch data from the IRS to update your local
database.

Useage:
=======

django-charitychecker only checks U.S. based nonprofits, this means that
it will not verify foreign nonprofits registered with the IRS (there are
a few, but the data entry format for these organizations is inconsistent
and so can't be machine parsed easily).

django-charitychecker makes the following functions and models public:

Public Objects and Methods
--------------------------

Models
~~~~~~

``charitychecker.IRSNonprofitData``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

a model representing a nonprofit with the following fields:

Attributes
''''''''''

-  ``IRSNonprofitData.ein``: a string representing the nonprofit's EIN
   number.

-  ``IRSNonprofitData.name``: a string representing the name of the
   Nonprofit as published in IRS Publication 78.

-  ``IRSNonprofitData.city``: a string representing the city in which
   the nonprofit is incorporated.

-  ``IRSNonprofitData.state``: a string representing the state in which
   the nonprofit is incorporated.

-  ``IRSNonprofitData.country``: a string representing the country in
   which the nonprofit is incorporated.

-  ``IRSNonprofitData.deductability_code``: the tax deductability code
   of the nonprofit organization. See the
   `charitycheck <https://github.com/nalourie/charitycheck>`__ README
   for more information on deductability codes.

Of course, you can retrieve a nonprofit's info using their EIN by
``IRSNonprofitData.objects.get(ein="some ein string")``.

Methods
'''''''

-  ``IRSNonprofitData.verify_nonprofit(ein, name=None, city=None, state=None, country=None, deductability_code=None)``:
   return true if there is a nonprofit in the charitychecker database
   with information matching the information provided to the function as
   arguments, return false otherwise.

-  ``IRSNonprofitData.get_deductability_code(ein, name=None, city=None, state=None, country=None)``:
   if a nonprofit is found in the charitychecker database with
   information matching the information provided as arguments to the
   function, then return that nonprofit's deductability code, otherwise
   return the empty string.

Utilities
~~~~~~~~~

``ignore_blank_space``
^^^^^^^^^^^^^^^^^^^^^^

A function which takes an iterator (it's meant for file like objects but
should take any iterator returning strings), and returns that iterator
skipping all blank lines and stripping all white space from the end of
any line.

``open_zip_from_url``
^^^^^^^^^^^^^^^^^^^^^

A context manager taking two arguments, ``zip_url`` and ``file_name``.
The context manager downloads the file from ``zip_url``, attempts to
unzip and then return the file at the path ``file_name`` from the
downloaded zip archive. It does all of this in memory without writing to
disk.

``irs_nonprofit_data_context_manager``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

A context manager for dealing with the IRS Publication 78 data. It
automatically downloads, unzips, and opens the file from the IRS
website, closing the resources when finished. It skips any ``FORGN``
registered nonprofits, and returns all of the nonprofit data strings as
a generator. Use is as you would any context manager:

::

    with IRSNonprofitDataContextManager() as irs_data:
        # code using irs_data as a file object
        .... 

The Publication 78 file is a series of lines of the form
``ein|name|city|state|country|deductability_code``.

``update_database_from_file``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

A function that takes ``file_manager``, ``convert_line``, ``pk_field``,
and ``model`` arguments, then uses a file to update in bulk your
application's database. Specifically, it takes:

-  ``file_manager``: a context manager which returns a generator
   yielding strings. Conceptually, we think of this iterator as a file
   like object, but any generator should work.
-  ``convert_line``: a function whose input is a line yielded by
   ``file_manager`` and that outputs a dictionary mapping keys which are
   field names of ``model`` and values which will be used to instantiate
   those field names.
-  ``pk_field``: The name field which is defined to be the primary key
   on ``model``. This field should not be an ``AutoField`` for the
   following reasons: 1.) bulk updating commands in Django do not call
   the save method on the model, and thus do not set ``AutoField``
   primary keys, 2.) if you are updating your database from some
   third-party source data, you want to be able to identify each line in
   the third-party data uniquely, thus some primary-key like
   value/unique identifier should already exist in your source data.
   Using an ``AutoField`` instead would mean that the function would
   have no way of distinguishing new data and old data that's been
   updated.
-  ``model``: the model you want to update.

Note! This function will delete any data that is in your database and
not present in the source file provided by ``file_manager``.

``update_charitychecker_data``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

A function that, when called, downloads a fresh copy of the IRS
Publication 78 data, unzips it, and uses it to update the charitychecker
database. It accepts no arguments.

Management Commands
~~~~~~~~~~~~~~~~~~~

``update_charitychecker_data``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

A command that downloads a new copy of the IRS Publication 78 data,
unzips it, and uses the data to update the charitychecker database.

This command takes no arguments, and only the default django command
options. Run it by typing into the command prompt:

``python manage.py update_charitychecker_data``

Of course, you can only run the command after charitychecker is
installed into your project's ``settings.py`` file's ``INSTALLED_APPS``,
and you've run ``python manage.py syncdb``. This command could take a
long time to finish, because it checks that your entire nonprofit
database (800,000+ rows) is up to date.

Testing
=======

Test the app as you would any other Django app. In a project with
charitychecker installed run:

::

    python manage.py test charitychecker

Note that since the test suite tests downloading and unzipping the data
from the IRS, the test suite can take a minute or so, if you want to
speed up the tests simply skip the tests using
``irs_nonprofit_data_context_manager`` and the test suite should run
much faster.

Contributing
============

Pull requests are welcome. Also check out
`charitycheck <https://github.com/nalourie/charitycheck>`__ for a
general python equivalent of this package if you are interested in
contributing.

Suggestions for contributing:

-  python 3 support
-  incorporate this module into a larger family of modules/packages
   dealing with nonprofit data (but of course, following the UNIX
   philosophy is really important here. Do one thing and do it well!)
-  writing tests for the ``open_zip_from_url`` and
   ``update_database_from_file`` functions which currently are only
   tested indirectly by the tests on
   ``irs_nonprofit_data_context_manager`` and
   ``update_charitychecker_data``, which are both wrappers for these
   more general functions.
-  add tests for the newly added string methods on the IRSNonprofitData
   model.

Authors
=======

Authored by Nicholas A. Lourie. You can contact him at
developer.nick@kozbox.com.
