import re

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse, reverse_lazy
from django.forms import formset_factory
from django.http import HttpResponseRedirect
from django.http.response import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext as _
from django.views.generic import FormView, ListView, RedirectView, TemplateView

from mobetta import formsets, util
from mobetta.access import can_translate, can_translate_language
from mobetta.conf import settings as mobetta_settings
from mobetta.forms import AddTranslatorForm, CommentForm, TranslationForm
from mobetta.models import EditLog, TranslationFile
from mobetta.paginators import MovingRangePaginator


class LanguageListView(TemplateView):

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
        ctx = super(LanguageListView, self).get_context_data(*args, **kwargs)

        ctx.update({
            'languages': self.get_languages()
        })

        return ctx


def download_po_file(request, file_pk):
    translation_file = get_object_or_404(TranslationFile, pk=int(file_pk))

    with open(translation_file.filepath, 'r') as f:
        content = f.read()

    response = HttpResponse(content, content_type='text/plain')
    response['Content-Disposition'] = 'attachment; filename="{}_{}.po"'.format(
        translation_file.name,
        translation_file.language_code
    )

    return response


class FileListView(ListView):

    model = TranslationFile
    context_object_name = 'files'
    template_name = 'mobetta/file_list.html'

    @method_decorator(login_required)
    def dispatch(self, request, lang_code, *args, **kwargs):
        self.language_code = lang_code
        if not can_translate_language(request.user, self.language_code):
            raise PermissionDenied

        return super(FileListView, self).dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return TranslationFile.objects.filter(language_code=self.language_code)

    def get_context_data(self, *args, **kwargs):
        ctx = super(FileListView, self).get_context_data(*args, **kwargs)

        ctx.update({
            'language_name': dict(settings.LANGUAGES)[self.language_code]
        })

        return ctx


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


class FileDetailView(FormView):
    template_name = 'mobetta/file_detail.html'
    form_class = formset_factory(
        TranslationForm,
        formset=formsets.TranslationFormSet,
        extra=0,
    )
    paginator_class = MovingRangePaginator
    paginate_by = 20
    translations_per_page = 20

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        self.translation_file = get_object_or_404(
            TranslationFile,
            pk=self.request.resolver_match.kwargs['pk']
        )

        if not can_translate_language(request.user, self.translation_file.language_code):
            raise PermissionDenied

        return super(FileDetailView, self).dispatch(request, *args, **kwargs)

    def filter_by_search_tag(self, entries, tag):
        regex = re.compile(tag, re.IGNORECASE)

        def entry_matches(entry):
            return (regex.search(entry.msgid) or
                    regex.search(entry.msgstr) or
                    (regex.search(entry.msgctxt) if entry.msgctxt else ''))

        return (entry for entry in entries if entry_matches(entry))

    def filter_by_type(self, pofile, type):
        filters = {
            'translated': 'translated_entries',
            'untranslated': 'untranslated_entries',
            'fuzzy': 'fuzzy_entries',
        }
        return getattr(pofile, filters[type])() if type in filters else pofile

    def form_invalid(self, form):
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

        return self.render_to_response(self.get_context_data(form=form))

    def form_valid(self, form):
        changes = []
        for f in form:
            if f.is_updated():
                changes.append((f, f.get_changes()))

        if any(changes):
            pofile = self.translation_file.get_polib_object()

            applied_changes, rejected_changes = util.update_translations(pofile, changes)

            # Only update the metadata if we've actually made some changes
            if len(applied_changes) > 0:
                if hasattr(self.request.user, 'first_name'):
                    first_name = self.request.user.first_name
                else:
                    first_name = None

                if hasattr(self.request.user, 'last_name'):
                    last_name = self.request.user.last_name
                else:
                    last_name = None

                util.update_metadata(
                    pofile,
                    first_name,
                    last_name,
                    self.request.user.email,
                )

                pofile.save()

                messages.success(self.request, _('Changed %d translations') % len(applied_changes))

                # Update edit logs with the applied_changes
                if mobetta_settings.USE_EDIT_LOGGING:
                    for f, change in applied_changes:
                        EditLog.objects.create(
                            user=self.request.user,
                            file_edited=self.translation_file,
                            msghash=change['md5hash'],
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
                    f.add_error(
                        change['field'],
                        _("This value was edited while you were editing it (new value: %s)") % change['po_value'])
                    messages.error(
                        self.request,
                        _("The %s for \"%s\" was edited while you were editing it") % (change['field'], change['msgid'])
                    )

                return self.form_invalid(form)

        return HttpResponseRedirect(self.get_success_url())

    def get_context_data(self, **kwargs):
        ctx = super(FileDetailView, self).get_context_data(**kwargs)

        translations = self.get_translations()

        # Paginator(translations, self.translations_per_page)
        paginator = self.get_paginator(translations, self.paginate_by)
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
                'occurrences': translation['occurrences'],
                'md5hash': translation['md5hash'],
            }
            for translation in page
        ]

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
        })

        return ctx

    def get_entries(self):
        entries = self.translation_file.get_polib_object()

        type_filter = self.request.GET.get('type')
        if type_filter:
            entries = self.filter_by_type(entries, type_filter)

        search_filter = self.request.GET.get('search_tags')
        if search_filter:
            entries = self.filter_by_search_tag(entries, search_filter)

        return entries

    def get_page(self, paginator):
        try:
            page = paginator.page(self.request.GET.get('page'))
        except:
            page = paginator.page(1)

        return page

    def get_paginator(self, queryset, per_page, orphans=0, allow_empty_first_page=True):
        return self.paginator_class(queryset, per_page, orphans, allow_empty_first_page)

    def get_success_url(self):
        if self.request.GET:
            return "{}?{}".format(
                reverse('mobetta:file_detail', args=(self.translation_file.pk,)),
                self.request.GET.urlencode())
        return reverse('mobetta:file_detail', args=(self.translation_file.pk,))

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
    def dispatch(self, request, file_pk, *args, **kwargs):
        self.translation_file = get_object_or_404(
            TranslationFile,
            pk=file_pk
        )

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
