.. Mobetta documentation master file, created by
   sphinx-quickstart on Thu May 18 16:05:12 2017.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

=======
Mobetta
=======

.. rubric:: Manage translations in Django projects

.. image:: https://travis-ci.org/maykinmedia/mobetta.svg?branch=master
    :target: https://travis-ci.org/maykinmedia/mobetta

.. image:: https://codecov.io/gh/maykinmedia/mobetta/branch/develop/graph/badge.svg
    :target: https://codecov.io/gh/maykinmedia/mobetta

.. image:: https://img.shields.io/pypi/v/mobetta.svg
    :target: https://pypi.python.org/pypi/mobetta

.. image:: https://lintly.com/gh/maykinmedia/mobetta/badge.svg
    :target: https://lintly.com/gh/maykinmedia/mobetta/

Mobetta is a reusable app to manage translation files in Django projects.

It's inspired on `django-rosetta`_, but takes a more modern approach to problem
and adds extra features, such as:

* comments on translations
* edit history
* support for `ICU message format`_ with json catalogs

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   installation
   usage


.. _quickstart:

Quickstart
==========

Install with pip::

    pip install mobetta

Add it to your installed apps::

    INSTALLED_APPS = [
        ...,
        'mobetta',
        ...,
    ]

Hook up the urls in your root ``urls.py``::

    urlpatterns = [
        url(r'^admin/', include(admin.site.urls)),  # optional
        url(r'^admin/mobetta/', include('mobetta.urls', namespace='mobetta')),
        ...
    ]

Run migrate to create the necessary database tables::

    python manage.py migrate

.. _usage:

Usage
=====

Mobetta discovers your translation files with a management command::

    python manage.py locate_translation_files

Open localhost:8000/admin/mobetta/ to manage your translations.


Notes
=====

How Django loads your translation files
---------------------------------------

See the `django translation docs`_


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`


.. _django-rosetta: https://github.com/mbi/django-rosetta
.. _django translation docs: https://docs.djangoproject.com/en/stable/topics/i18n/translation/#how-django-discovers-translations
.. _ICU message format: https://formatjs.io/guides/message-syntax/
