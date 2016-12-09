# Mobetta

Mobetta is a reusable app to manage translation files in Django.

It's inspired on django-rosetta and sports extra features such as comments on
translations, improved stability and a couple of bugfixes. More features
are planned.

## Installation

Install with pip:

    pip install mobetta

Next, hook up mobetta by adding it to installed apps:

```python
# settings.py

INSTALLED_APPS = [
    ...
    'mobetta',
    ...
]
```

and add it to your root `urls.py`:

```python
# urls.py

from django.conf.urls import include, url
...

import mobetta.urls

urlpatterns = [
    ...
    url(r'^mobetta/', include(mobetta.urls.urlpatterns, 'mobetta', 'mobetta')),
    ...
]
```

Finally, run `migrate` to create the database tables:

```bash
python manage.py migrate
```

## Usage

Mobetta needs to be aware of your translation files. To discover the files, use
the management command:

    python manage.py locate_translation_files


## Notes ##

### How Django loads translation files ###

See the [django docs](https://docs.djangoproject.com/en/stable/topics/i18n/translation/#how-django-discovers-translations).
