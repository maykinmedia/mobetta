from django.conf.urls import url

from .views import FileDetailView, FileListView, LanguageListView


urlpatterns = [
    url(r'^$', LanguageListView.as_view(), name='language_list'),
    url(r'^language/(?P<lang_code>\w{2})/$', FileListView.as_view(), name='file_list'),
    url(r'^file/(?P<pk>\d+)/$', FileDetailView.as_view(), name='file_detail'),
]
