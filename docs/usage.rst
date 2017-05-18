=====
Usage
=====

See the index page :ref:`usage` for base-usage instructions. This covers the
Django po/mo files.

ICU message files
=================

The ICU message format is popular in the frontend, and it's quite different
from ``.po`` files. Django does not support them (out of the box).

After :ref:`installing <install-icu>` the ICU message plugin, you can still
manage your translations with mobetta.

Navigate to the translation interface (http://localhost:8000/admin/mobetta/)
and locate the ICU translation files. Create a new translation file, and point
it to the JSON file containing the translations.

Currently, the only supported format is simple key-values, for example
``src/locale/en.json``

.. code-block:: json

    {
        "myapp.unique.identifier": "My app is awesome!",
        "myapp.unique.identifier2": "My app is translated!"
    }

The translations are checked to have a valid `ICU message format`_.

.. _ICU message format: https://formatjs.io/guides/message-syntax/
