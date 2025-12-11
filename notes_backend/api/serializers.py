from rest_framework import serializers
from .models import Note

# PUBLIC_INTERFACE
class NoteSerializer(serializers.ModelSerializer):
    """Serializer for reading Note instances including id and timestamps."""
    owner = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Note
        fields = [
            "id",
            "title",
            "content",
            "created_at",
            "updated_at",
            "owner",
            "is_archived",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "owner"]


# PUBLIC_INTERFACE
class NoteCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating Note instances (owner set in view)."""

    class Meta:
        model = Note
        fields = ["title", "content", "is_archived"]
