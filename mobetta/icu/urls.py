from __future__ import absolute_import, unicode_literals

from django.conf.urls import url

from .views import ICUFileDetailView, ICUFileDownloadView, ICUFileListView

urlpatterns = [
    url(r'^icu/language/(?P<lang_code>[a-z]{2,3}(-[A-Za-z0-9]{1,8})*)/$',
        ICUFileListView.as_view(), name='icu_file_list'),
    url(r'^icu/file/(?P<pk>\d+)/$', ICUFileDetailView.as_view(), name='icu_file_detail'),
    url(r'^icu/download/(?P<pk>\d+)/$', ICUFileDownloadView.as_view(), name='icu_download'),
]
