from rest_framework import serializers

from mobetta.models import MessageComment, TranslationFile


class TranslationFileSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = TranslationFile
        fields = ('name', 'filepath', 'language_code')


class MessageCommentSerializer(serializers.HyperlinkedModelSerializer):
    translation_file = serializers.PrimaryKeyRelatedField(many=False, queryset=TranslationFile.objects.all())
    comment_count = serializers.SerializerMethodField()
    user_name = serializers.SerializerMethodField()

    class Meta:
        model = MessageComment
        fields = ('msghash', 'translation_file', 'body', 'created', 'comment_count', 'user_name')

    def create(self, validated_data):
        current_user = self.context['request'].user
        return MessageComment.objects.create(user=current_user, **validated_data)

    def get_comment_count(self, instance):
        return MessageComment.objects.filter(
            msghash=instance.msghash,
            translation_file=instance.translation_file,
        ).count()

    def get_user_name(self, instance):
        return str(instance.user)
