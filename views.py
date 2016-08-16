from django.shortcuts import render
from django.views.generic import ListView, DetailView
from django.core.paginator import Paginator
from django.forms import formset_factory

from mobetta.util import find_pofiles, app_name_from_filepath
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

    def get_context_data(self, *args, **kwargs):
        ctx = super(FileDetailView, self).get_context_data(*args, **kwargs)

        translations = []

        po = self.object.get_polib_object()

        for entry in po:
            translations.append({
                'original': entry.msgid,
                'translated': entry.msgstr,
                'obsolete': entry.obsolete,
            })

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
                'translation': trans['translated']
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
