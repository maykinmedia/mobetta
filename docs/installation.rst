============
Installation
============

The :ref:`quickstart` section covers the basic installation without any extra
plugins.

.. _install-icu:

ICU message files
=================

ICU message files support is optional, and can be installed in one go with::

    pip install mobetta[icu]

Since this is set-up as a Django app as well, you'll need to add it to
``INSTALLED_APPS``::

    INSTALLED_APPS = [
        ...,
        'mobetta',
        'mobetta.icu',
        ...,
    ]

Migrate your database to finalize the installation::

    python manage.py migrate


Contributor
===========

You can install the library with all the dev-dependencies with::

    pip install -e .[icu,test,docs]
