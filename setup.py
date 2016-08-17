import os
from setuptools import find_packages, setup

with open(os.path.join(os.path.dirname(__file__), 'README.rst')) as readme:
    README = readme.read()

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name='mobetta',
    version='0.0.1',
    license='MIT',

    # packaging
    install_requires=['Django>=1.8','polib'],
    include_package_data=True,
    packages=find_packages(),

    # tests
    test_suite='runtests.runtests',
    tests_require=['coverage'],

    # metadata
    description='A Django package for managing translation files',
    long_description=README,
    url='https://www.example.com/',
    author='Maykin Media, Ben Wadsworth',
    author_email='ben@maykinmedia.nl',
    classifiers=[
        'Environment :: Web Environment',
        'Framework :: Django',
        'Framework :: Django :: X.Y',  # replace "X.Y" as appropriate
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',  # example license
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
    ],
)
