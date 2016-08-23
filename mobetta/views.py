import re

from django.shortcuts import render
from django.views.generic import FormView, ListView, TemplateView
from django.core.paginator import Paginator
from django.core.urlresolvers import reverse
from django.forms import formset_factory
from django.contrib import messages
from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext as _
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.contrib.auth.decorators import user_passes_test
from django.conf import settings
from django.http import HttpResponseRedirect

from mobetta import util
from mobetta import formsets
from mobetta.models import TranslationFile, EditLog
from mobetta.forms import TranslationForm
from mobetta.access import can_translate
from mobetta.conf import settings as mobetta_settings


class LanguageListView(TemplateView):

    template_name = 'mobetta/language_list.html'

    def get_languages(self):
        language_codes = TranslationFile.objects.all().values_list('language_code', flat=True)
        language_tuples = [
            (code, name, TranslationFile.objects.filter(language_code=code).count())
            for code, name in settings.LANGUAGES if code in language_codes
        ]
        return language_tuples

    def get_context_data(self, *args, **kwargs):
        ctx = super(LanguageListView, self).get_context_data(*args, **kwargs)

        ctx.update({
            'languages': self.get_languages()
        })

        return ctx


class FileListView(ListView):

    model = TranslationFile
    context_object_name = 'files'
    template_name = 'mobetta/file_list.html'

    @method_decorator(user_passes_test(lambda user: can_translate(user), settings.LOGIN_URL))
    def dispatch(self, request, lang_code, *args, **kwargs):
        self.language_code = lang_code
        return super(FileListView, self).dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return TranslationFile.objects.filter(language_code=self.language_code)

    def get_context_data(self, *args, **kwargs):
        ctx = super(FileListView, self).get_context_data(*args, **kwargs)

        ctx.update({
            'language_name': dict(settings.LANGUAGES)[self.language_code]
        })

        return ctx


class FileDetailView(FormView):
    template_name = 'mobetta/file_detail.html'
    form_class = formset_factory(
        TranslationForm,
        formset=formsets.TranslationFormSet,
        extra=0,
    )
    translations_per_page = 20

    @method_decorator(never_cache)
    @method_decorator(user_passes_test(lambda user: can_translate(user), settings.LOGIN_URL))
    def dispatch(self, request, *args, **kwargs):
        self.file = get_object_or_404(
            TranslationFile,
            pk=self.request.resolver_match.kwargs['pk']
        )
        return super(FileDetailView, self).dispatch(request, *args, **kwargs)

    def filter_by_search_tag(self, entries, tag):
        regex = re.compile(tag)

        return (
            entry for entry in entries
            if regex.search(entry.msgid) or regex.search(entry.msgstr)
        )

    def filter_by_type(self, pofile, type):
        filters = {
            'translated': 'translated_entries',
            'untranslated': 'untranslated_entries',
            'fuzzy': 'fuzzy_entries',
        }
        return getattr(pofile, filters[type])() if type in filters else pofile

    def form_invalid(self, form):
        # Populate the old_<fieldname> values with the file's current translation/context
        pofile = self.file.get_polib_object()

        form_msgids = [
            f.cleaned_data['msgid']
            for f in form
        ]

        file_translations = {
            poentry.msgid: {
                'translation': poentry.msgstr,
                'context': poentry.msgctxt,
            }

            for poentry in [
                e for e in pofile if e.msgid in form_msgids
            ]
        }

        for f in form:
            form_data = f.cleaned_data
            form_data.update({
                'old_translation': file_translations[form_data['msgid']]['translation'],
                'old_context': file_translations[form_data['msgid']]['context'],
            })
            new_form_data = {
                '{}-{}'.format(f.prefix, k) : form_data[k]
                for k in form_data.keys()
            }
            f.data = new_form_data

        return self.render_to_response(self.get_context_data(form=form))

    def form_valid(self, form):
        changes = []
        for f in form:
            if f.is_updated():
                changes.append((f, f.get_changes()))

        if any(changes):
            pofile = self.file.get_polib_object()

            applied_changes, rejected_changes = util.update_translations(pofile, changes)

            # Only update the metadata if we've actually made some changes
            if len(applied_changes) > 0:
                util.update_metadata(
                    pofile,
                    self.request.user.first_name,
                    self.request.user.last_name,
                    self.request.user.email,
                )

                pofile.save()

                messages.success(self.request, _('Changed %d translations') % len(applied_changes))

                # Update edit logs with the applied_changes
                if mobetta_settings.USE_EDIT_LOGGING:
                    for f, change in applied_changes:
                        EditLog.objects.create(
                            user=self.request.user,
                            file_edited=self.file,
                            msgid=change['msgid'],
                            fieldname=change['field'],
                            old_value=change['from'],
                            new_value=change['to'],
                        )

            # Add messages/errors about rejected changes
            if len(rejected_changes) > 0:
                for f, change in rejected_changes:
                    # Add an error message to the field as well as a message
                    # in the top of the view.
                    f.add_error(change['field'], _("This value was edited while you were editing it (new value: %s)") % (change['po_value']))
                    messages.error(self.request, _("The %s for \"%s\" was edited while you were editing it") % (change['field'], change['msgid']))

                return self.form_invalid(form)

        return HttpResponseRedirect(self.get_success_url())

    def get_context_data(self, **kwargs):
        ctx = super(FileDetailView, self).get_context_data(**kwargs)

        translations = self.get_translations()

        paginator = Paginator(translations, self.translations_per_page)
        page = self.get_page(paginator)

        ctx['formset'] = ctx.pop('form')
        ctx['formset'].initial = [
            {
                'msgid': translation['original'],
                'translation': translation['translated'],
                'old_translation': translation['translated'],
                'fuzzy': translation['fuzzy'],
                'old_fuzzy': translation['fuzzy'],
                'context': translation['context'],
                'old_context': translation['context'],
                'occurrences': translation['occurrences']
            }
            for translation in page
        ]

        # Keep track of the query parameters for the url of the pages.
        page_query_params = self.request.GET.copy()
        if 'page' in page_query_params:
            page_query_params.pop('page')

        # Keep track of the query parameters for the url of the filters.
        filter_query_params = page_query_params.copy()
        if 'type' in filter_query_params:
            filter_query_params.pop('type')

        # Keep track of the search tags
        search_tags = ''
        query_params = self.request.GET.copy()
        if 'search_tags' in query_params:
            search_tags = ' '.join(query_params.copy().pop('search_tags'))

        ctx.update({
            'page': page,
            'file': self.file,
            'search_tags': search_tags,
            'page_query_params': page_query_params.urlencode(),
            'filter_query_params': filter_query_params.urlencode(),
        })

        return ctx

    def get_entries(self):
        entries = self.file.get_polib_object()

        type_filter = self.request.GET.get('type')
        if type_filter:
            entries = self.filter_by_type(entries, type_filter)

        search_filter = self.request.GET.get('search_tags')
        if search_filter:
            entries = self.filter_by_search_tag(entries, search_filter)

        return entries

    def get_page(self, paginator):
        page = self.request.GET.get('page')
        try:
            entries = paginator.page(page)
        except:
            entries = paginator.page(1)

        return entries

    def get_success_url(self):
        return reverse('file_detail', args=(self.file.pk,))

    def get_translations(self):
        entries = self.get_entries()

        translations = [
            {
                'original': entry.msgid,
                'translated': entry.msgstr,
                'obsolete': entry.obsolete,
                'fuzzy': util.message_is_fuzzy(entry),
                'context': entry.msgctxt,
                'occurrences': util.get_occurrences(entry)
            }
            for entry in entries
        ]

        return translations


class EditHistoryView(ListView):

    model = EditLog
    context_object_name = 'edits'
    template_name = 'mobetta/edit_history.html'

    @method_decorator(never_cache)
    @method_decorator(user_passes_test(lambda user: can_translate(user), settings.LOGIN_URL))
    def dispatch(self, request, file_pk, *args, **kwargs):
        self.translation_file = get_object_or_404(
            TranslationFile,
            pk=file_pk
        )

        return super(EditHistoryView, self).dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return self.translation_file.edit_logs.all()

    def get_context_data(self, *args, **kwargs):
        ctx = super(EditHistoryView, self).get_context_data(*args, **kwargs)

        ctx.update({
            'translation_file': self.translation_file
        })

        return ctx
