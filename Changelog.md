# Changelog

## 0.3.0

* Dropped support for Django < 1.11
* Added support for Django 2.0.x

## 0.2.9

* Fixed form CharField strip argument, fixing an incorrect validation error
  saying the translation was edited by someone else when it wasn't (issue #10)

## 0.2.7

* Changed CharField to TextField in log models, msgids can have arbitrary lengths

## 0.2.6

* Fixed bug in url patterns causing download views to be broken.

## 0.2.5

* Fixed .po file discovery when using country codes in locales, e.g. nl-NL,
  nl_NL

## 0.2.4

* Fixed packaging/imports to use mobetta without extensions

## 0.2.3

### icu

* better solution dealing with max_length issue below

## 0.2.2

### icu

* hash msgid to stay under `CharField.max_length`

## 0.2.1

### icu

* fix packaging: icu templates were not included

## version 0.1.4

- Added a compile all files button
- It now remembers the page it was editing instead of going back to the first page of translations.
- Fixed a bug involving start or end \n where it thought there was a change.
