from rest_framework import serializers

from context.models import Document


class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = ["id", "content", "title", "page"]
        depth = 1
