from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Exists, OuterRef, Subquery
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_http_methods, require_POST

from accounts.models import User
from jobs.models import JobPosting
from .forms import MessageForm
from .models import Conversation, Message


def _display_name(user):
    return user.get_full_name() or user.username


def _conversation_list(user):
    latest_message = Message.objects.filter(
        conversation=OuterRef('pk')
    ).order_by('-created_at', '-id')
    conversations = Conversation.for_user(user).select_related(
        'recruiter', 'job_seeker', 'job'
    ).annotate(
        last_message_body=Subquery(latest_message.values('body')[:1]),
        has_unread=Exists(Message.unread_for(user).filter(conversation=OuterRef('pk'))),
    )
    for conversation in conversations:
        conversation.other_user = conversation.other_participant(user)
        conversation.other_name = _display_name(conversation.other_user)
    return conversations


def _message_data(message, user):
    return {
        'id': message.id,
        'body': message.body,
        'is_mine': message.sender_id == user.id,
        'sent_at': timezone.localtime(message.created_at).strftime('%b %-d, %-I:%M %p'),
    }


@login_required
def inbox(request):
    return render(request, 'messaging/inbox.html', {
        'title': 'Messages',
        'conversations': _conversation_list(request.user),
    })


@login_required
@require_http_methods(['GET', 'POST'])
def conversation_detail(request, conversation_id):
    conversation = get_object_or_404(
        Conversation.for_user(request.user).select_related(
            'recruiter', 'job_seeker', 'job'
        ),
        id=conversation_id,
    )

    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid():
            message = form.save(commit=False)
            message.conversation = conversation
            message.sender = request.user
            message.save()
            conversation.updated_at = message.created_at
            conversation.save(update_fields=['updated_at'])
            return redirect('messaging.conversation', conversation_id=conversation.id)
    else:
        form = MessageForm()

    conversation.mark_read(request.user)
    other_user = conversation.other_participant(request.user)
    return render(request, 'messaging/inbox.html', {
        'title': f'Messages with {_display_name(other_user)}',
        'conversations': _conversation_list(request.user),
        'active_conversation': conversation,
        'other_user': other_user,
        'other_name': _display_name(other_user),
        'thread_messages': conversation.messages.select_related('sender'),
        'form': form,
    })


@login_required
def conversation_updates(request, conversation_id):
    conversation = get_object_or_404(
        Conversation.for_user(request.user),
        id=conversation_id,
    )
    try:
        after_id = int(request.GET.get('after', 0))
    except ValueError:
        after_id = 0

    new_messages = conversation.messages.filter(id__gt=after_id)
    if new_messages:
        conversation.mark_read(request.user)
    return JsonResponse({
        'messages': [
            _message_data(message, request.user) for message in new_messages
        ],
    })


@login_required
@require_POST
def start_conversation(request, user_id):
    if request.user.role != User.Role.RECRUITER:
        return HttpResponseForbidden('Only recruiters can start conversations.')
    job_seeker = get_object_or_404(User, id=user_id, role=User.Role.JOB_SEEKER)

    job = None
    if request.POST.get('job'):
        job = get_object_or_404(
            JobPosting,
            id=request.POST['job'],
            posted_by=request.user,
        )

    conversation, created = Conversation.objects.get_or_create(
        recruiter=request.user,
        job_seeker=job_seeker,
        defaults={'job': job},
    )
    if created:
        messages.success(
            request,
            f'Say hello to {_display_name(job_seeker)} — they will see your message in their inbox.',
        )
    return redirect('messaging.conversation', conversation_id=conversation.id)
