# Mobetta #

Full README still to come...

## Notes ##

### How Django loads translation files ###

Loading non-lazy translations is done when the server is started. The relevant code is in `utils/translation/trans_real.py`.

* First Django loads its own translations (from `django/conf/locale/`)
* Then it loads translations for `INSTALLED_APPS`, in the reverse order in which they are specified in settings.py.
* Then, if we've specified LOCALE_DIRS in settings.py, we load the files from those directories.

After a locale directory is loaded, it is merged into a 'main' translation object. Therefore if the same string is specified in two of our apps, the translation specified in the app closest to the top of `INSTALLED_APPS` is used, no matter what app is requesting the translation.