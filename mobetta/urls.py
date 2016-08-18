from django.conf.urls import url

from .views import FileListView, FileDetailView


urlpatterns = [
    url(r'^$', FileListView.as_view(), name='file_list'),
    url(r'^file/(?P<pk>\d+)/$', FileDetailView.as_view(), name='file_detail'),
]