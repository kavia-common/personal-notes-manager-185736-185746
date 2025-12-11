from django.contrib.auth import get_user_model
from django.db.models import Q
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import api_view, action, permission_classes
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework.permissions import IsAuthenticated, AllowAny

from .models import Note
from .serializers import NoteSerializer, NoteCreateUpdateSerializer


@api_view(['GET'])
@permission_classes([AllowAny])
def health(request):
    """
    PUBLIC_INTERFACE
    Health check endpoint for uptime monitoring.

    Returns:
      200 OK with {"message": "Server is up!"}
    """
    return Response({"message": "Server is up!"})


class IsOwner(permissions.BasePermission):
    """
    Permission to only allow owners of an object to access/modify it.
    """

    def has_object_permission(self, request, view, obj):
        return hasattr(obj, "owner") and obj.owner == request.user


# PUBLIC_INTERFACE
class NotesViewSet(viewsets.ModelViewSet):
    """CRUD endpoints for personal notes. Results are scoped to the authenticated user.

    Query params:
    - search: substring search over title and content
    - archived: 'true' or 'false' to filter by archive state

    Actions:
    - POST /api/notes/{id}/archive/
    - POST /api/notes/{id}/unarchive/
    """
    serializer_class = NoteSerializer
    permission_classes = [IsAuthenticated, IsOwner]

    def get_queryset(self):
        user = self.request.user
        qs = Note.objects.filter(owner=user)
        # filter by archived if provided
        archived = self.request.query_params.get('archived')
        if archived is not None:
            if archived.lower() in ('true', '1', 'yes'):
                qs = qs.filter(is_archived=True)
            elif archived.lower() in ('false', '0', 'no'):
                qs = qs.filter(is_archived=False)
        # simple search
        search = self.request.query_params.get('search')
        if search:
            qs = qs.filter(Q(title__icontains=search) | Q(content__icontains=search))
        return qs

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):
            return NoteCreateUpdateSerializer
        return NoteSerializer

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    def get_object(self):
        # enforce ownership on retrieve/update/delete
        obj = super().get_object()
        self.check_object_permissions(self.request, obj)
        return obj

    @action(detail=True, methods=['post'])
    def archive(self, request, pk=None):
        note = self.get_object()
        note.is_archived = True
        note.save(update_fields=['is_archived', 'updated_at'])
        return Response(NoteSerializer(note).data)

    @action(detail=True, methods=['post'])
    def unarchive(self, request, pk=None):
        note = self.get_object()
        note.is_archived = False
        note.save(update_fields=['is_archived', 'updated_at'])
        return Response(NoteSerializer(note).data)


# PUBLIC_INTERFACE
@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    """
    Register a new user and return an auth token.

    Request body:
    - username: string
    - password: string

    Returns:
    - 201 with {'token': '<token>'} on success
    - 400 with errors otherwise
    """
    username = request.data.get('username')
    password = request.data.get('password')
    if not username or not password:
        return Response({"detail": "username and password are required"}, status=status.HTTP_400_BAD_REQUEST)

    User = get_user_model()
    if User.objects.filter(username=username).exists():
        return Response({"detail": "username already exists"}, status=status.HTTP_400_BAD_REQUEST)

    user = User.objects.create_user(username=username, password=password)
    token, _ = Token.objects.get_or_create(user=user)
    return Response({'token': token.key}, status=status.HTTP_201_CREATED)


# PUBLIC_INTERFACE
@api_view(['POST'])
def token_logout(request):
    """
    Invalidate the current user's auth token (logout for token auth).
    The client should discard the token after this call.

    Returns:
    - 204 No Content on success
    """
    try:
        token = Token.objects.get(user=request.user)
        token.delete()
    except Token.DoesNotExist:
        pass
    return Response(status=status.HTTP_204_NO_CONTENT)
