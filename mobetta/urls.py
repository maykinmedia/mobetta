from django.apps import apps
from django.conf.urls import include, url

from .views import (
    AddTranslatorView, CompilePoFilesView, EditHistoryView, FileDetailView,
    FileDownloadView, FileListView, FindPoFilesView, LanguageListView
)

app_name = 'mobetta'
urlpatterns = [
    url(r'^$', LanguageListView.as_view(), name='language_list'),
    url(r'^find/$', FindPoFilesView.as_view(), name='find_po_files'),
    url(r'^compile/$', CompilePoFilesView.as_view(), name='compile_po_files'),
    url(r'^add_translator/$', AddTranslatorView.as_view(), name='add_translator'),
    url(r'^edit_log/(?P<pk>\d+)/$', EditHistoryView.as_view(), name='edit_history'),
    url(r'^download/(?P<pk>\d+)/$', FileDownloadView.as_view(), name='download'),
    url(r'^file/(?P<pk>\d+)/$', FileDetailView.as_view(), name='file_detail'),
    url(r'^language/(?P<lang_code>[a-z]{2,3}(-[A-Za-z0-9]{1,8})*)/$', FileListView.as_view(), name='file_list'),
    url(r'^api/', include('mobetta.api.urls', namespace='api')),
]


if apps.is_installed('mobetta.icu'):
    urlpatterns += [
        url(r'^icu/', include('mobetta.icu.urls')),
    ]
