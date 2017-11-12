import os

from setuptools import find_packages, setup

basedir = os.path.normpath(os.path.abspath(os.path.dirname(__file__)))


with open(os.path.join(basedir, 'docs', 'index.rst')) as readme:
    README = readme.read()

# allow setup.py to be run from any path
os.chdir(basedir)

try:
    from django import VERSION as DJANGO_VERSION
except ImportError:  # nothing we can do...
    limit_drf = False
else:
    limit_drf = DJANGO_VERSION < (1, 9)


DRF_DEP = 'djangorestframework<3.7' if limit_drf else 'djangorestframework'


setup(
    name='mobetta',
    version='0.2.9',
    license='BSD',

    # packaging
    install_requires=[
        'Django>=1.8',
        'polib',
        DRF_DEP,
    ],
    include_package_data=True,
    packages=find_packages(exclude=["tests"]),
    extras_require={
        'icu': ['PyICU'],
        'test': [
            'django_webtest',
            'factory_boy',
            'mock',
            'pytest',
            'pytest-cov',
            'pytest-django',
            'pytest-pep8',
            'pytest-pylint',
            'pytest-pythonpath',
            'pytest-runner',
        ],
        'docs': [
            'Sphinx',
            'sphinx-autobuild',
            'sphinx_rtd_theme'
        ]
    },

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
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Framework :: Django :: 1.8',
        'Framework :: Django :: 1.9',
        'Framework :: Django :: 1.10',
        'Framework :: Django :: 1.11',
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
