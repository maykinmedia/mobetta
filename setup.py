import os

from setuptools import find_packages, setup

with open(os.path.join(os.path.dirname(__file__), 'README.md')) as readme:
    README = readme.read()

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name='mobetta',
    version='0.1.5',
    license='BSD',

    # packaging
    install_requires=[
        'Django>=1.8',
        'polib',
        'djangorestframework'
    ],
    include_package_data=True,
    packages=find_packages(exclude=["tests"]),

    # tests
    test_suite='runtests.runtests',
    tests_require=['coverage'],

    # metadata
    description='A Django package for managing translation files',
    long_description=README,
    url='https://github.com/maykinmedia/mobetta',
    author='Maykin Media, Ben Wadsworth',
    author_email='ben@maykinmedia.nl',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Framework :: Django :: 1.8',
        'Framework :: Django :: 1.9',
        'Framework :: Django :: 1.10',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
    ],
)
