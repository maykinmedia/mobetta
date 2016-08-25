from rest_framework import serializers

from mobetta.models import TranslationFile, MessageComment


class TranslationFileSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = TranslationFile
        fields = ('name', 'filepath', 'language_code')


class MessageCommentSerializer(serializers.HyperlinkedModelSerializer):
    translation_file = serializers.PrimaryKeyRelatedField(many=False, queryset=TranslationFile.objects.all())
    comment_count = serializers.SerializerMethodField()

    class Meta:
        model = MessageComment
        fields = ('msgid', 'translation_file', 'body', 'created', 'comment_count')

    def create(self, validated_data):
        current_user = self.context['request'].user
        return MessageComment.objects.create(user=current_user, **validated_data)

    def get_comment_count(self, instance):
        return MessageComment.objects.filter(
            msgid=instance.msgid,
            translation_file=instance.translation_file,
        ).count()
