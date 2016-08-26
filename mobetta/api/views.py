from rest_framework import viewsets

from mobetta.models import TranslationFile, MessageComment
from mobetta.api.serializers import TranslationFileSerializer, MessageCommentSerializer
from mobetta.api.permissions import CanTranslatePermission


class TranslationFileViewSet(viewsets.ModelViewSet):
    """
    """
    queryset = TranslationFile.objects.all()
    serializer_class = TranslationFileSerializer

    permission_classes = [CanTranslatePermission]


class MessageCommentViewSet(viewsets.ModelViewSet):
    """
    """
    queryset = MessageComment.objects.all()
    serializer_class = MessageCommentSerializer

    permission_classes = [CanTranslatePermission]

    def get_queryset(self):
        queryset = MessageComment.objects.all()
        file_pk = self.request.query_params.get('translation_file', None)

        if file_pk is not None:
            queryset = queryset.filter(translation_file__pk=file_pk)

        msgid = self.request.query_params.get('msgid', None)

        if msgid is not None:
            queryset = queryset.filter(msgid=msgid)

        return queryset


