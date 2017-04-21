from __future__ import absolute_import, unicode_literals

import re

from django.contrib import messages
from django.forms import formset_factory
from django.utils.translation import ugettext_lazy as _

from .. import formsets
from ..views import FileDetailView, FileListView
from .forms import TranslationForm
from .models import EditLog, ICUTranslationFile
from .utils import update_translations


class ICUFileListView(FileListView):
    model = ICUTranslationFile
    template_name = 'mobetta/icu/file_list.html'


class ICUFileDetailView(FileDetailView):
    model = ICUTranslationFile
    template_name = 'mobetta/icu/file_detail.html'
    form_class = formset_factory(
        TranslationForm,
        formset=formsets.TranslationFormSet,
        extra=0,
    )

    edit_log_model = EditLog
    success_url_pattern = 'mobetta:icu_file_detail'

    def filter_by_type(self, icu_file, type):
        filters = {
            'translated': 'translated_entries',
            'untranslated': 'untranslated_entries',
        }
        if type not in filters:
            return icu_file
        return getattr(icu_file, filters[type])

    def filter_by_search_tag(self, entries, tag):  # TODO: check/test against invalid regexes
        regex = re.compile(tag, re.IGNORECASE)

        def entry_matches(entry):
            return (regex.search(entry.msgid) or
                    regex.search(entry.msgstr) or
                    (regex.search(entry.msgctxt) if entry.msgctxt else ''))

        return (entry for entry in entries if entry_matches(entry))

    def get_entries(self):
        entries = self.translation_file.get_icufile_object()

        type_filter = self.request.GET.get('type')
        if type_filter:
            entries = self.filter_by_type(entries, type_filter)

        search_filter = self.request.GET.get('search_tags')
        if search_filter:
            entries = self.filter_by_search_tag(entries, search_filter)

        return entries

    def get_formset_initial(self, page):
        return [translation for translation in page]

    def get_translations(self):
        entries = self.get_entries()
        return [{
            'msgid': msgid,
            'md5hash': msgid,  # unique anyway
            'translation': translation,
            'old_translation': translation,
        } for msgid, translation in entries]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'fuzzy_filter': False
        })
        return context

    def save_changes(self, changes):
        icu_file = self.translation_file.get_icufile_object()
        applied_changes, rejected_changes = update_translations(icu_file, changes)
        if len(applied_changes) > 0:
            icu_file.save()
            messages.success(self.request, _('Changed %d translations') % len(applied_changes))
            self.log_edits(applied_changes)
        return rejected_changes

    def populate_old_data(self, form):
        # Populate the old_<fieldname> values with the file's current translation/context
        icu_file = self.translation_file.get_icufile_object()
        for f in form:
            form_data = f.cleaned_data
            form_data['old_translation'] = icu_file.contents[form_data['md5hash']]
            new_form_data = {
                '{}-{}'.format(f.prefix, k): form_data[k]
                for k in form_data.keys()
            }
            f.data = new_form_data
        return form

    def handle_rejected_changes(self, changes):
        for f, change in changes:
            # Add an error message to the field as well as a message
            # in the top of the view.
            error_msg = _("This value was edited while you were editing it (new value: %s)") % change['current_value']
            f.add_error('translation', error_msg)
            messages.error(
                self.request,
                _("The translation for \"%s\" was edited while you were editing it") % change['msgid']
            )
