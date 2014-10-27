django-charitychecker
=====================

A django app for verifying U.S. nonprofits by their EIN number. For a general python module with similar functionality, check out [charitycheck](https://github.com/nalourie/charitycheck). 

Visit the [github](https://github.com/nalourie/django-charitychecker). 

# Installation:

From pip:

```
pip install django-charitychecker
```

In your settings.py:

```python
INSTALLED_APPS = (
    ...
    charitychecker
    ...
    )
```

Note that if you want django-charitychecker to work properly, you'll need to periodically fetch data from the IRS to update your local database. 

# Useage:

django-charitychecker only checks U.S. based nonprofits, this means that it will not verify foreign nonprofits registered with the IRS (there are a few, but the data entry format for these organizations is inconsistent and so can't be machine parsed easily).

django-charitychecker makes the following functions and models public:

## Public Objects and Methods

### Models

#### ```charitychecker.IRSNonprofitData``` 

a model representing a nonprofit with the following fields:

##### Attributes

- ```IRSNonprofitData.ein```: a string representing the nonprofit's EIN number.

- ```IRSNonprofitData.name```: a string representing the name of the Nonprofit as published in IRS Publication 78.

- ```IRSNonprofitData.city```: a string representing the city in which the nonprofit is incorporated.

- ```IRSNonprofitData.state```: a string representing the state in which the nonprofit is incorporated.

- ```IRSNonprofitData.country```: a string representing the country in which the nonprofit is incorporated.

- ```IRSNonprofitData.deductability_code```: the tax deductability code of the nonprofit organization. See the [charitycheck](https://github.com/nalourie/charitycheck) README for more information on deductability codes.

Of course, you can retrieve a nonprofit's info using their EIN by ```IRSNonprofitData.objects.get(ein="some ein string")```.

##### Methods

- ```IRSNonprofitData.verify_nonprofit(ein, name=None, city=None, state=None, country=None, deductability_code=None)```: return true if there is a nonprofit in the charitychecker database with information matching the information provided to the function as arguments, return false otherwise.

- ```IRSNonprofitData.get_deductability_code(ein, name=None, city=None, state=None, country=None)```: if a nonprofit is found in the charitychecker database with information matching the information provided as arguments to the function, then return that nonprofit's deductability code, otherwise return the empty string.

### Utilities

#### ```IRSNonprofitDataContextManager```

A context manager for dealing with the IRS Publication 78 data. It automatically downloads, unzips, and opens the file from the IRS website, closing the resources when finished. It skips any ```FORGN``` registered nonprofits, and returns all of the nonprofit data strings as a generator. Use is as you would any context manager:

```
with IRSNonprofitDataContextManager() as irs_data:
    # code using irs_data as a file object
    .... 
```

The Publication 78 file is a series of lines of the form ```ein|name|city|state|country|deductability_code```.

#### ```update_charitychecker_data```

A function that, when called, downloads a fresh copy of the IRS Publication 78 data, unzips it, and uses it to update the charitychecker database. It accepts no arguments.

### Management Commands

#### ```update_charitychecker_data```

A command that downloads a new copy of the IRS Publication 78 data, unzips it, and uses the data to update the charitychecker database.

This command takes no arguments, and only the default django command options. Run it by typing into the command prompt:

```python manage.py update_charitychecker_data```

Of course, you can only run the command after charitychecker is installed into your project's ```settings.py``` file's ```INSTALLED_APPS```, and you've run ```python manage.py syncdb```. This command could take a long time to finish, because it checks that your entire nonprofit database (800,000+ rows) is up to date.

# Contributing 

Pull requests are welcome. Also check out [charitycheck](https://github.com/nalourie/charitycheck) for a general python equivalent of this package if you are interested in contributing.

Suggestions for contributions are adding python 3 support, incorporating this module into a large family of modules/packages dealing with nonprofit data (but of course, following the UNIX philosophy is really important here. Do one thing and do it well!), and most importantly, refactoring the utilities module to allow you to put in mocks for the IRSNonprofitDataContextManager's downloading url, and the url that update_charitychecker_data passes to IRSNonprofitDataContextManager, as currently the test suite takes about 25 minutes. Another important contribution would be some optimization of the database interactions in updating and creating the nonprofit database, as an in-memory database can take hours to update.

# Authors

Authored by Nicholas A. Lourie. You can contact him at developer.nick@kozbox.com.