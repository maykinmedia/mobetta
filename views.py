import re

from django.shortcuts import render
from django.views.generic import ListView, DetailView
from django.core.paginator import Paginator
from django.forms import formset_factory

from mobetta.util import find_pofiles, app_name_from_filepath, message_is_fuzzy
from mobetta.models import TranslationFile
from mobetta.forms import TranslationForm


class FileListView(ListView):

    model = TranslationFile
    context_object_name = 'files'
    template_name = 'mobetta/file_list.html'

    def get_queryset(self):
        return TranslationFile.objects.all()


class FileDetailView(DetailView):

    model = TranslationFile
    context_object_name = 'file'
    template_name = 'mobetta/file_detail.html'
    translations_per_page = 20

    def allow_entry(self, entry):
        if 'query' in self.request.GET:
            regex = re.compile(self.request.GET['query'])
            if regex.search(entry.msgid) is None and \
                regex.search(entry.msgstr) is None:

                return False

        return True

    def get_translations(self):
        translations = []

        po = self.object.get_polib_object()

        translations = [
            {
                'original': entry.msgid,
                'translated': entry.msgstr,
                'obsolete': entry.obsolete,
                'fuzzy': message_is_fuzzy(entry),
            }
            for entry in po
            if self.allow_entry(entry)
        ]

        return translations

    def get_context_data(self, *args, **kwargs):
        ctx = super(FileDetailView, self).get_context_data(*args, **kwargs)

        translations = self.get_translations()
        paginator = Paginator(translations, self.translations_per_page)

        if 'page' in self.request.GET and int(self.request.GET.get('page')) <= paginator.num_pages and int(self.request.GET.get('page')) > 0:
            page = int(self.request.GET.get('page'))
        else:
            page = 1

        needs_pagination = paginator.num_pages > 1
        if needs_pagination:
            page_range = range(1, 1 + paginator.num_pages)

        TranslationFormSet = formset_factory(TranslationForm)
        formset = TranslationFormSet(initial=[
            {
                'msgid': trans['original'],
                'translation': trans['translated'],
                'fuzzy': trans['fuzzy'],
            } for trans in paginator.page(page).object_list
        ])

        ctx.update({
            'formset': formset,
            'paginator': paginator,
            'needs_pagination': needs_pagination,
            'page_range': needs_pagination and page_range,
            'page': page,
        })

        return ctx
