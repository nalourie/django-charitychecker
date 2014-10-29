from distutils.core import setup

setup(
    name='django-charitychecker',
    version='1.1',
    author='Nicholas A. Lourie',
    author_email='developer.nick@kozbox.com',
    install_requires="django >= 1.6",
    packages=['charitychecker',
              'charitychecker.management',
              'charitychecker.management.commands'],
    license='MIT License',
    description=('a small django app to verify information'
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
    
