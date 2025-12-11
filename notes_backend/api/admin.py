from django.contrib import admin
from .models import Note


@admin.register(Note)
class NoteAdmin(admin.ModelAdmin):
    list_display = ("title", "owner", "updated_at", "is_archived")
    search_fields = ("title", "content")
    list_filter = ("is_archived",)
