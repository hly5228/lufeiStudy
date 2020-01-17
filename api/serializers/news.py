from rest_framework import serializers
from api import models


class NewsSerializer(serializers.ModelSerializer):
    article_type = serializers.CharField(source='get_article_type_display')
    status = serializers.CharField(source='get_status_display')
    position = serializers.CharField(source='get_position_display')
    source = serializers.CharField(source='source.name')

    class Meta:
        model = models.Article
        fields = '__all__'


class CommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Comment
        fields = '__all__'

