from rest_framework import serializers

from mobetta.models import TranslationFile, MessageComment


class TranslationFileSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = TranslationFile
        fields = ('name', 'filepath', 'language_code')


class MessageCommentSerializer(serializers.HyperlinkedModelSerializer):
    translation_file = serializers.HyperlinkedIdentityField(view_name="api:translationfile-detail")

    class Meta:
        model = MessageComment
        fields = ('msgid', 'translation_file', 'body', 'created')
