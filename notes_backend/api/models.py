from django.db import models
from django.contrib.auth import get_user_model


class Note(models.Model):
    """
    Stores a personal note belonging to a user, including title, content,
    timestamps, and archived state.
    """
    title = models.CharField(max_length=200)
    content = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)  # Set on creation
    updated_at = models.DateTimeField(auto_now=True)      # Updated on save
    owner = models.ForeignKey(
        get_user_model(),
        on_delete=models.CASCADE,
        related_name="notes",
        help_text="The owner of the note."
    )
    is_archived = models.BooleanField(default=False)

    class Meta:
        ordering = ['-updated_at']  # Most recently updated first
        indexes = [
            models.Index(fields=["owner", "is_archived"]),
            models.Index(fields=["updated_at"]),
        ]

    def __str__(self) -> str:
        # Helpful representation in admin and logs
        return f"{self.title} (#{self.pk})"
