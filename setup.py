from setuptools import setup

setup(
    name='django-charitychecker',
    version='1.3',
    author='Nicholas A. Lourie',
    author_email='developer.nick@kozbox.com',
    install_requires="",
    packages=['charitychecker',
              'charitychecker.management',
              'charitychecker.management.commands',
              'charitychecker.test_data'],
    data_files=[
        ('charitychecker/test_data',
         ['charitychecker/test_data/mock-irs-data-after.txt',
          'charitychecker/test_data/mock-irs-data-before.txt',
          'charitychecker/test_data/test-data-with-FORGNS.txt',
          'charitychecker/test_data/test-data-without-FORGNS.txt']),
    ],
    license='MIT License',
    description=('a small django app to verify information '
                 'about nonprofits using their EINs'),
    long_description=open('README.rst').read(),
    include_package_data=True,
    keywords="nonprofit nonprofits EIN IRS django",
    url="https://github.com/nalourie/django-charitychecker",
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Environment :: Web Environment',
        'Framework :: Django',
    ],
)
    
