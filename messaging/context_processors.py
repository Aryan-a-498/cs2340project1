from .models import Message


def unread_messages(request):
    if not request.user.is_authenticated:
        return {}
    return {
        'unread_conversation_count': Message.unread_for(request.user)
        .values('conversation')
        .distinct()
        .count(),
    }
