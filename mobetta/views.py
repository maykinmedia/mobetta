from __future__ import absolute_import, unicode_literals

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.exceptions import PermissionDenied
from django.core.management import call_command
from django.core.urlresolvers import reverse_lazy
from django.forms import formset_factory
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext as _
from django.views.generic import FormView, ListView, RedirectView, TemplateView

from mobetta import formsets, util
from mobetta.access import can_translate, can_translate_language
from mobetta.forms import AddTranslatorForm, TranslationForm
from mobetta.models import EditLog, TranslationFile
from mobetta.paginators import MovingRangePaginator

from .base_views import (
    BaseFileDetailView, BaseFileDownloadView, BaseFileListView
)
from .ext import ICULanguageListMixin


class LanguageListView(ICULanguageListMixin, TemplateView):

    template_name = 'mobetta/language_list.html'

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super(LanguageListView, self).dispatch(request, *args, **kwargs)

    def get_languages(self):
        language_codes = TranslationFile.objects.all().values_list('language_code', flat=True)
        language_tuples = [
            (code, name, TranslationFile.objects.filter(language_code=code).count())
            for code, name in settings.LANGUAGES
            if code in language_codes and can_translate_language(self.request.user, code)
        ]
        return language_tuples

    def get_context_data(self, *args, **kwargs):
        kwargs['languages'] = self.get_languages()
        return super(LanguageListView, self).get_context_data(*args, **kwargs)


class FileDownloadView(BaseFileDownloadView):
    model = TranslationFile

    def get_attachment_file_name(self, translation_file):
        return '{}_{}.po'.format(
            translation_file.name,
            translation_file.language_code
        )


class FileListView(BaseFileListView):
    model = TranslationFile
    template_name = 'mobetta/file_list.html'


class CompilePoFilesView(RedirectView):
    url = reverse_lazy('mobetta:language_list')
    permanent = False

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super(CompilePoFilesView, self).dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        translation_files = TranslationFile.objects.all()
        for translation_file in translation_files:
            translation_file.save_mofile()

        messages.success(request, _('Compiled the translations. Checkout the new files.'))
        return super(CompilePoFilesView, self).get(request, *args, **kwargs)


class FindPoFilesView(RedirectView):
    url = reverse_lazy('mobetta:language_list')
    permanent = False

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super(FindPoFilesView, self).dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        call_command('locate_translation_files')
        return super(FindPoFilesView, self).get(request, *args, **kwargs)


def _entry_matches(regex, entry):
    return (regex.search(entry.msgid) or
            regex.search(entry.msgstr) or
            (regex.search(entry.msgctxt) if entry.msgctxt else ''))


class FileDetailView(BaseFileDetailView):
    model = TranslationFile
    template_name = 'mobetta/file_detail.html'
    form_class = formset_factory(
        TranslationForm,
        formset=formsets.TranslationFormSet,
        extra=0,
    )
    paginator_class = MovingRangePaginator
    paginate_by = 20
    translations_per_page = 20

    edit_log_model = EditLog
    success_url_pattern = 'mobetta:file_detail'

    # callback to test if an entry matches
    entry_matches = staticmethod(_entry_matches)

    def filter_by_type(self, pofile, type):
        filters = {
            'translated': 'translated_entries',
            'untranslated': 'untranslated_entries',
            'fuzzy': 'fuzzy_entries',
        }
        return getattr(pofile, filters[type])() if type in filters else pofile

    def populate_old_data(self, form):
        # Populate the old_<fieldname> values with the file's current translation/context
        pofile = self.translation_file.get_polib_object()

        form_hashes = [
            f.cleaned_data['md5hash']
            for f in form
        ]

        file_translations = {
            util.get_message_hash(poentry): {
                'translation': poentry.msgstr,
            }

            for poentry in [
                e for e in pofile if util.get_message_hash(e) in form_hashes
            ]
        }

        for f in form:
            form_data = f.cleaned_data
            form_data.update({
                'old_translation': file_translations[form_data['md5hash']]['translation'],
            })
            new_form_data = {
                '{}-{}'.format(f.prefix, k): form_data[k]
                for k in form_data.keys()
            }
            f.data = new_form_data
        return form

    def save_changes(self, changes):
        pofile = self.translation_file.get_polib_object()

        applied_changes, rejected_changes = util.update_translations(pofile, changes)

        # Only update the metadata if we've actually made some changes
        if len(applied_changes) > 0:
            first_name = getattr(self.request.user, 'first_name', None)
            last_name = getattr(self.request.user, 'last_name', None)
            util.update_metadata(pofile, first_name, last_name, self.request.user.email)

            pofile.save()

            messages.success(self.request, _('Changed %d translations') % len(applied_changes))

            # Update edit logs with the applied_changes
            self.log_edits(applied_changes)

        return rejected_changes

    def handle_rejected_changes(self, changes):
        for f, change in changes:
            # Add an error message to the field as well as a message
            # in the top of the view.
            f.add_error(
                change['field'],
                _("This value was edited while you were editing it (new value: %s)") % change['po_value'])
            messages.error(
                self.request,
                _("The %s for \"%s\" was edited while you were editing it") % (change['field'], change['msgid'])
            )

    def get_formset_initial(self, page):
        return [{
            'msgid': translation['original'],
            'translation': translation['translated'],
            'old_translation': translation['translated'],
            'fuzzy': translation['fuzzy'],
            'old_fuzzy': translation['fuzzy'],
            'context': translation['context'],
            'occurrences': translation['occurrences'],
            'md5hash': translation['md5hash'],
        } for translation in page]

    def get_entries(self):
        entries = self.translation_file.get_polib_object()

        type_filter = self.request.GET.get('type')
        if type_filter:
            entries = self.filter_by_type(entries, type_filter)

        search_filter = self.request.GET.get('search_tags')
        if search_filter:
            entries = self.filter_by_search_tag(entries, search_filter)

        return entries

    def get_translations(self):
        entries = self.get_entries()

        translations = [
            {
                'original': entry.msgid,
                'translated': entry.msgstr,
                'obsolete': entry.obsolete,
                'fuzzy': util.message_is_fuzzy(entry),
                'context': entry.msgctxt,
                'occurrences': util.get_occurrences(entry),
                'md5hash': util.get_message_hash(entry),
            }
            for entry in entries
        ]

        return translations


class EditHistoryView(ListView):

    model = EditLog
    context_object_name = 'edits'
    template_name = 'mobetta/edit_history.html'
    paginator_class = MovingRangePaginator
    paginate_by = 20

    @method_decorator(login_required)
    def dispatch(self, request, pk, *args, **kwargs):
        self.translation_file = get_object_or_404(TranslationFile, pk=pk)

        if not can_translate_language(request.user, self.translation_file.language_code):
            raise PermissionDenied

        return super(EditHistoryView, self).dispatch(request, *args, **kwargs)

    def get_queryset(self):
        logs = self.translation_file.edit_logs.all()

        order_fields = {
            'time': 'created',
            'user': 'user',
            'msgid': 'msgid',
            'msghash': 'msghash',
            'fieldname': 'fieldname',
            'old_value': 'old_value',
            'new_value': 'new_value',
        }

        field = self.request.GET.get('order_by')

        if field is None:
            return logs.all()

        __, order, field = field.rpartition('-')

        if field in order_fields:
            return logs.order_by(order + order_fields[field])

        return logs.all()

    def get_context_data(self, *args, **kwargs):
        ctx = super(EditHistoryView, self).get_context_data(*args, **kwargs)

        # Keep track of the query parameters for the url of the pages.
        pagination_query_params = self.request.GET.copy()
        if 'page' in pagination_query_params:
            pagination_query_params.pop('page')

        ctx.update({
            'translation_file': self.translation_file,
            'pagination_query_params': pagination_query_params.urlencode(),
        })

        return ctx


class AddTranslatorView(FormView):

    form_class = AddTranslatorForm
    template_name = 'mobetta/add_translator.html'
    success_url = reverse_lazy('mobetta:language_list')

    @method_decorator(user_passes_test(lambda user: can_translate(user), settings.LOGIN_URL))
    def dispatch(self, request, *args, **kwargs):
        return super(AddTranslatorView, self).dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.save()

        messages.success(
            self.request,
            _("{user} successfully added as a translator for {language}").format(
                user=str(form.cleaned_data.get('user')),
                language=dict(settings.LANGUAGES)[form.cleaned_data.get('language')]
            )
        )
        return super(AddTranslatorView, self).form_valid(form)
