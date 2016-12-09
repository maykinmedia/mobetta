from django.conf.urls import include, url

from rest_framework import routers

from mobetta.api import views

router = routers.DefaultRouter()
router.register(r'files', views.TranslationFileViewSet)
router.register(r'comments', views.MessageCommentViewSet)


urlpatterns = [
    url(r'^', include(router.urls)),
    url(r'^auth/', include('rest_framework.urls', namespace='rest_framework')),
    url(r'^suggestion/', views.TranslationSuggestionsView.as_view(), name='translation_suggestion'),
]
