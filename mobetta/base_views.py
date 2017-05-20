"""
Defines the base view classes for various actions.

Plugins can use these to implement the plugin-specific behaviour.
"""
from __future__ import absolute_import, unicode_literals

import re

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.utils.decorators import method_decorator
from django.views.generic import FormView, ListView, View
from django.views.generic.detail import SingleObjectMixin

from .access import can_translate_language
from .conf import settings as mobetta_settings
from .forms import CommentForm
from .paginators import MovingRangePaginator


class BaseFileListView(ListView):
    context_object_name = 'files'
    model = None  # must be specified
    template_name = None  # must be specified

    @method_decorator(login_required)
    def dispatch(self, request, lang_code, *args, **kwargs):
        self.language_code = lang_code
        if not can_translate_language(request.user, self.language_code):
            raise PermissionDenied

        return super(BaseFileListView, self).dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return self.model.objects.filter(language_code=self.language_code)

    def get_context_data(self, *args, **kwargs):
        context = super(BaseFileListView, self).get_context_data(*args, **kwargs)
        context['language_name'] = dict(settings.LANGUAGES)[self.language_code]
        return context


class BaseFileDetailView(FormView):
    model = None  # must be set
    template_name = None  # must be set in subclass
    form_class = None  # must be specified in subclass
    paginator_class = MovingRangePaginator
    paginate_by = 20
    translations_per_page = 20

    edit_log_model = None  # must be set in subclass
    success_url_pattern = None  # must be set in subclass

    # callback to test if an entry matches
    entry_matches = None  # must be set in subclass

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        self.translation_file = get_object_or_404(self.model, pk=kwargs['pk'])

        if not can_translate_language(request.user, self.translation_file.language_code):
            raise PermissionDenied

        return super(BaseFileDetailView, self).dispatch(request, *args, **kwargs)

    def filter_by_search_tag(self, entries, tag):
        try:
            regex = re.compile(tag, re.IGNORECASE)
        except re.error:  # invalid regex supplied TODO: better feedback
            return ()
        return (entry for entry in entries if self.entry_matches(regex, entry))

    def form_invalid(self, form):
        form = self.populate_old_data(form)
        return self.render_to_response(self.get_context_data(form=form))

    def log_edits(self, changes):
        if mobetta_settings.USE_EDIT_LOGGING:
            for f, change in changes:
                self.edit_log_model.objects.create(
                    user=self.request.user,
                    file_edited=self.translation_file,
                    msghash=change['md5hash'],
                    msgid=change['msgid'],
                    fieldname=change['field'],
                    old_value=change['from'],
                    new_value=change['to'],
                )

    def form_valid(self, form):
        changes = []
        for f in form:
            if f.is_updated():
                changes.append((f, f.get_changes()))

        if any(changes):
            rejected_changes = self.save_changes(changes)

            # Add messages/errors about rejected changes
            if len(rejected_changes) > 0:
                self.handle_rejected_changes(rejected_changes)
                return self.form_invalid(form)

        return redirect(self.get_success_url())

    def get_context_data(self, **kwargs):
        ctx = super(BaseFileDetailView, self).get_context_data(**kwargs)

        translations = self.get_translations()

        # Paginator(translations, self.translations_per_page)
        paginator = self.get_paginator(translations, self.paginate_by)
        page = self.get_page(paginator)

        ctx['formset'] = ctx.pop('form')
        ctx['formset'].initial = self.get_formset_initial(page)

        if mobetta_settings.USE_MS_TRANSLATE:
            ctx['show_suggestions'] = True

        # Keep track of the query parameters for the url of the pages.
        pagination_query_params = self.request.GET.copy()
        if 'page' in pagination_query_params:
            pagination_query_params.pop('page')

        # Keep track of the query parameters for the url of the filters.
        filter_query_params = pagination_query_params.copy()
        if 'type' in filter_query_params:
            filter_query_params.pop('type')

        # Keep track of the search tags
        search_tags = ''
        query_params = self.request.GET.copy()
        if 'search_tags' in query_params:
            search_tags = ' '.join(query_params.copy().pop('search_tags'))

        # Prepopulate comment form with the current translation file
        comment_form = CommentForm(initial={
            'translation_file': self.translation_file,
        })

        ctx.update({
            'file': self.translation_file,
            'filter_query_params': filter_query_params.urlencode(),
            'is_paginated': paginator.num_pages > 1,
            'object_list': page.object_list,
            'page_obj': page,
            'pagination_query_params': pagination_query_params.urlencode(),
            'paginator': paginator,
            'search_tags': search_tags,
            'comment_form': comment_form,
            'fuzzy_filter': True,
        })

        return ctx

    def get_page(self, paginator):
        try:
            page = paginator.page(self.request.GET.get('page'))
        except Exception:  # TODO: no pokemon exception catching allowed
            page = paginator.page(1)

        return page

    def get_paginator(self, queryset, per_page, orphans=0, allow_empty_first_page=True):
        return self.paginator_class(queryset, per_page, orphans, allow_empty_first_page)

    def get_success_url(self):
        url = reverse(self.success_url_pattern, args=(self.translation_file.pk,))
        if self.request.GET:
            return "{}?{}".format(url, self.request.GET.urlencode())
        return url

    def get_translations(self):
        raise NotImplementedError

    def filter_by_type(self, pofile, type):
        raise NotImplementedError

    def populate_old_data(self, form):
        raise NotImplementedError

    def get_formset_initial(self, page):
        raise NotImplementedError

    def get_entries(self):
        raise NotImplementedError

    def handle_rejected_changes(self, changes):
        raise NotImplementedError

    def save_changes(self, changes):
        raise NotImplementedError


class BaseFileDownloadView(SingleObjectMixin, View):
    model = None  # must be set by the subclass

    def dispatch(self, request, *args, **kwargs):
        """
        Check that the user is allowed to download this translation.
        """
        language_code = self.get_object().language_code
        if not can_translate_language(request.user, language_code):
            raise PermissionDenied
        return super(BaseFileDownloadView, self).dispatch(request, *args, **kwargs)

    def get_attachment_file_name(self, translation_file):
        raise NotImplementedError

    def get(self, request, *args, **kwargs):
        translation_file = self.get_object()
        with open(translation_file.filepath, 'r') as f:
            content = f.read()
        response = HttpResponse(content, content_type='application/json')
        filename = self.get_attachment_file_name(translation_file)
        response['Content-Disposition'] = 'attachment; filename="{}"'.format(filename)
        return response
