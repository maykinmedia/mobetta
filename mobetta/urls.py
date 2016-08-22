from django.conf.urls import url

from .views import (
    FileDetailView,
    FileListView,
    LanguageListView,
    EditHistoryView,
)


urlpatterns = [
    url(r'^$', LanguageListView.as_view(), name='language_list'),
    url(r'^language/(?P<lang_code>\w{2})/$', FileListView.as_view(), name='file_list'),
    url(r'^file/(?P<pk>\d+)/$', FileDetailView.as_view(), name='file_detail'),
    url(r'^edit_log/(?P<file_pk>\d+)/$', EditHistoryView.as_view(), name='edit_history'),
]
