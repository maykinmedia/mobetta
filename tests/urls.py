from django.conf.urls import include, url
from django.contrib import admin

urlpatterns = [
    url(r'^admin/', include(admin.site.urls)),
    url(r'^api/', include('tests.api.urls', namespace='api')),  # See #46
    url(r'^mobetta/', include('mobetta.urls')),
]
