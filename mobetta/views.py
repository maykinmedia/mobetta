import re

from django.shortcuts import render
from django.views.generic import FormView, ListView
from django.core.paginator import Paginator
from django.core.urlresolvers import reverse
from django.forms import formset_factory
from django.contrib import messages
from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext as _
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import user_passes_test
from django.conf import settings

from mobetta.util import (
    find_pofiles,
    app_name_from_filepath,
    message_is_fuzzy,
    update_translations,
    update_metadata,
)
from mobetta.models import TranslationFile
from mobetta.forms import TranslationForm
from mobetta.access import can_translate
from mobetta import formsets


class FileListView(ListView):

    model = TranslationFile
    context_object_name = 'files'
    template_name = 'mobetta/file_list.html'

    @method_decorator(user_passes_test(lambda user: can_translate(user), settings.LOGIN_URL))
    def dispatch(self, *args, **kwargs):
        return super(FileListView, self).dispatch(*args, **kwargs)

    def get_queryset(self):
        return TranslationFile.objects.all()


class FileDetailView(FormView):
    template_name = 'mobetta/file_detail.html'
    form_class = formset_factory(
        TranslationForm,
        formset=formsets.TranslationFormSet,
        extra=0,
    )
    translations_per_page = 20

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
        return self.render_to_response(self.get_context_data(form=form))

    def form_valid(self, form):
        updates = [{
            'msgid': f.cleaned_data['msgid'],
            'msgstr': f.cleaned_data['translation'],
            'fuzzy': f.cleaned_data['fuzzy'],
            'context': f.cleaned_data['context'],
        } for f in form if f.is_updated()]

        if any(updates):
            pofile = self.file.get_polib_object()
            update_translations(pofile, updates)

            update_metadata(
                pofile,
                self.request.user.first_name,
                self.request.user.last_name,
                self.request.user.email,
            )

            pofile.save()

        messages.success(self.request, _('Changed %d translations') % len(updates))

        return self.render_to_response(self.get_context_data(form=form))

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
            }
            for translation in page
        ]

        ctx.update({
            'page': page,
            'file': self.file
        })

        return ctx

    def get_entries(self):
        entries = self.file.get_polib_object()

        type_filter = self.request.GET.get('type')
        if type_filter:
            entries = self.filter_by_type(entries, type_filter)

        search_filter = self.request.GET.get('query')
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
                'fuzzy': message_is_fuzzy(entry),
                'context': entry.msgctxt,
            }
            for entry in entries
        ]

        return translations
