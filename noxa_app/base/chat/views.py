"""
Views pour l'application Chat - Interface Chatbot RAG
"""
import json
import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods, require_POST, require_GET
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import Paginator
from django.db.models import Q

from .models import Conversation, ChatMessage, ChatSource, ChatFeedback
from .services import get_rag_service
from base.models import Topic, Publication

logger = logging.getLogger('services.rag')


@login_required
def chat_home(request):
    """
    Page principale du chatbot
    Affiche l'interface de chat et la liste des conversations
    """
    # Récupère les conversations de l'utilisateur
    conversations = Conversation.objects.filter(
        user=request.user,
        is_active=True
    ).order_by('-updated_at')[:20]

    # Récupère les topics pour le filtre
    topics = Topic.objects.all()

    # Questions suggérées
    rag_service = get_rag_service()
    suggested_questions = rag_service.get_suggested_questions()

    context = {
        'conversations': conversations,
        'topics': topics,
        'suggested_questions': suggested_questions,
        'active_conversation': None,
    }

    return render(request, 'chat/chat_interface.html', context)


@login_required
def conversation_view(request, conversation_id):
    """
    Affiche une conversation existante
    """
    conversation = get_object_or_404(
        Conversation,
        id=conversation_id,
        user=request.user
    )

    # Récupère les messages avec leurs sources (renommé pour éviter conflit avec Django messages)
    chat_messages = conversation.messages.prefetch_related('sources__publication').all()

    # Autres conversations pour la sidebar
    conversations = Conversation.objects.filter(
        user=request.user,
        is_active=True
    ).exclude(id=conversation_id).order_by('-updated_at')[:20]

    topics = Topic.objects.all()

    context = {
        'conversations': conversations,
        'active_conversation': conversation,
        'chat_messages': chat_messages,
        'topics': topics,
    }

    return render(request, 'chat/chat_interface.html', context)


@login_required
@require_POST
def create_conversation(request):
    """
    Crée une nouvelle conversation
    API endpoint - retourne JSON
    """
    try:
        data = json.loads(request.body)
        topic_id = data.get('topic_id')
        title = data.get('title', '')

        topic = None
        if topic_id:
            topic = get_object_or_404(Topic, id=topic_id)

        conversation = Conversation.objects.create(
            user=request.user,
            topic=topic,
            title=title
        )

        return JsonResponse({
            'success': True,
            'conversation_id': conversation.id,
            'title': conversation.title,
            'redirect_url': f'/chat/conversation/{conversation.id}/'
        })

    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        logger.error(f"Erreur création conversation: {e}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@require_POST
def send_message(request, conversation_id):
    """
    Envoie un message et obtient une réponse du RAG
    API endpoint - retourne JSON avec streaming possible
    """
    try:
        conversation = get_object_or_404(
            Conversation,
            id=conversation_id,
            user=request.user
        )

        if request.content_type == 'application/json':
            data = json.loads(request.body)
            user_message = data.get('message', '').strip()
        else:
            # Handle multipart/form-data
            user_message = request.POST.get('message', '').strip()

        # Handle multiple files
        uploaded_files = request.FILES.getlist('files')
        # Also check single 'file' for backward compatibility or different client implementation
        if not uploaded_files and request.FILES.get('file'):
            uploaded_files = [request.FILES.get('file')]

        if not user_message and not uploaded_files:
            return JsonResponse({
                'success': False,
                'error': 'Message ou fichier vide'
            }, status=400)

        # Sauvegarde le message utilisateur
        user_msg = ChatMessage.objects.create(
            conversation=conversation,
            role='user',
            content=user_message,
            # Legacy fields - keep for backward compatibility if needed, using first file
            file=uploaded_files[0] if uploaded_files else None,
            file_type=uploaded_files[0].content_type if uploaded_files else None
        )

        # Handle attachments and "Save to Space"
        save_to_space = request.POST.get('save_to_space') == 'true'
        files_saved_count = 0
        from .models import ChatAttachment
        from base.models import Publication

        for f in uploaded_files:
            # Create specific attachment object
            ChatAttachment.objects.create(
                message=user_msg,
                file=f,
                file_size=f.size,
                file_type=f.content_type
            )

            # Optional: Save to personal space (Publications)
            if save_to_space:
                # Basic validation: Publication model expects PDF mostly via validator, 
                # but we can try to save other types if model allows, or restrict here.
                # The model uses validatePdf validator.
                is_pdf = f.name.lower().endswith('.pdf')
                if is_pdf:
                    try:
                        Publication.objects.create(
                            user=request.user,
                            theme=f.name, # Use filename as theme/title
                            file=f,
                            description=f"Uploaded via Chat on {timezone.now().strftime('%Y-%m-%d %H:%M')}"
                        )
                        files_saved_count += 1
                    except Exception as e:
                        print(f"Error saving to space: {e}")


        # Récupère l'historique de la conversation (limité)
        history = list(conversation.messages.order_by('created_at').values(
            'role', 'content'
        )[:10])

        # Appelle le service RAG
        rag_service = get_rag_service()
        response = rag_service.process_query(
            query=user_message,
            topic_id=conversation.topic_id if conversation.topic else None,
            topic_name=conversation.topic.name if conversation.topic else None,
            conversation_history=history,
            top_k=5
        )

        # Sauvegarde la réponse de l'assistant
        assistant_msg = ChatMessage.objects.create(
            conversation=conversation,
            role='assistant',
            content=response.answer,
            query_embedding_time=response.query_embedding_time,
            retrieval_time=response.retrieval_time,
            generation_time=response.generation_time,
            total_time=response.total_time
        )
        

        # Sauvegarde les sources
        sources_data = []
        for source in response.sources:
            try:
                publication = Publication.objects.get(id=source.publication_id)
                chat_source = ChatSource.objects.create(
                    message=assistant_msg,
                    publication=publication,
                    chunk_index=source.chunk_index,
                    relevance_score=source.relevance_score,
                    excerpt=source.content[:500],
                    page_number=source.page_number
                )
                sources_data.append({
                    'publication_id': publication.id,
                    'publication_title': publication.theme,
                    'page_number': source.page_number,
                    'relevance_score': round(source.relevance_score, 2),
                    'excerpt': source.content[:200] + '...' if len(source.content) > 200 else source.content
                })
            except Publication.DoesNotExist:
                continue

        # Met à jour le titre de la conversation si c'est le premier message
        if conversation.messages.count() <= 2:
            # Utilise les premiers mots du message comme titre
            new_title = user_message[:50] + ('...' if len(user_message) > 50 else '')
            conversation.title = new_title
            conversation.save()

        return JsonResponse({
            'success': True,
            'user_message': {
                'id': user_msg.id,
                'content': user_msg.content,
                'created_at': user_msg.created_at.isoformat()
            },
            'assistant_message': {
                'id': assistant_msg.id,
                'content': assistant_msg.content,
                'created_at': assistant_msg.created_at.isoformat(),
                'sources': sources_data,
                'metrics': {
                    'embedding_time': round(response.query_embedding_time, 2),
                    'retrieval_time': round(response.retrieval_time, 2),
                    'generation_time': round(response.generation_time, 2),
                    'total_time': round(response.total_time, 2)
                }
            },
            'conversation_title': conversation.title,
            'files_saved': files_saved_count
        })

    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        logger.error(f"Erreur envoi message: {e}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@require_POST
def delete_conversation(request, conversation_id):
    """
    Supprime (désactive) une conversation
    """
    conversation = get_object_or_404(
        Conversation,
        id=conversation_id,
        user=request.user
    )

    conversation.is_active = False
    conversation.save()

    # Si c'est une requête AJAX, retourner JSON
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True})
    
    # Sinon rediriger vers le chat home
    return redirect('chat:home')


@login_required
@require_POST
def submit_feedback(request, message_id):
    """
    Soumet un feedback sur une réponse du chatbot
    """
    try:
        message = get_object_or_404(
            ChatMessage,
            id=message_id,
            conversation__user=request.user,
            role='assistant'
        )

        data = json.loads(request.body)

        # Feedback rapide (pouce haut/bas)
        if 'is_helpful' in data:
            message.is_helpful = data['is_helpful']
            message.save()

        # Feedback détaillé
        if 'rating' in data or 'issue_type' in data or 'comment' in data:
            feedback, created = ChatFeedback.objects.update_or_create(
                message=message,
                defaults={
                    'user': request.user,
                    'rating': data.get('rating'),
                    'issue_type': data.get('issue_type', ''),
                    'comment': data.get('comment', '')
                }
            )

        return JsonResponse({'success': True})

    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        logger.error(f"Erreur feedback: {e}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@require_GET
def get_suggestions(request):
    """
    Retourne des suggestions de questions
    """
    topic_id = request.GET.get('topic_id')

    rag_service = get_rag_service()
    suggestions = rag_service.get_suggested_questions(
        topic_id=int(topic_id) if topic_id else None
    )

    return JsonResponse({
        'success': True,
        'suggestions': suggestions
    })


@login_required
@require_GET
def search_publications(request):
    """
    Recherche de publications pour référence
    """
    query = request.GET.get('q', '').strip()
    topic_id = request.GET.get('topic_id')

    if not query:
        return JsonResponse({'success': True, 'results': []})

    publications = Publication.objects.filter(
        Q(theme__icontains=query) |
        Q(description__icontains=query) |
        Q(summary__icontains=query)
    )

    if topic_id:
        publications = publications.filter(topic_id=topic_id)

    publications = publications[:10]

    results = [{
        'id': pub.id,
        'title': pub.theme,
        'topic': pub.topic.name if pub.topic else None,
        'authors': [a.username for a in pub.authors.all()[:3]]
    } for pub in publications]

    return JsonResponse({
        'success': True,
        'results': results
    })


@login_required
@require_GET
def conversation_history(request, conversation_id):
    """
    Retourne l'historique des messages d'une conversation
    API pour le chargement paresseux
    """
    conversation = get_object_or_404(
        Conversation,
        id=conversation_id,
        user=request.user
    )

    page = int(request.GET.get('page', 1))
    per_page = int(request.GET.get('per_page', 20))

    messages = conversation.messages.prefetch_related(
        'sources__publication'
    ).order_by('-created_at')

    paginator = Paginator(messages, per_page)
    page_obj = paginator.get_page(page)

    messages_data = []
    for msg in reversed(list(page_obj)):
        msg_data = {
            'id': msg.id,
            'role': msg.role,
            'content': msg.content,
            'created_at': msg.created_at.isoformat(),
            'is_helpful': msg.is_helpful
        }

        if msg.role == 'assistant':
            msg_data['sources'] = [{
                'publication_id': s.publication.id,
                'publication_title': s.publication.theme,
                'page_number': s.page_number,
                'relevance_score': round(s.relevance_score, 2),
                'excerpt': s.excerpt[:200] + '...' if len(s.excerpt) > 200 else s.excerpt
            } for s in msg.sources.all()]

            msg_data['metrics'] = {
                'embedding_time': msg.query_embedding_time,
                'retrieval_time': msg.retrieval_time,
                'generation_time': msg.generation_time,
                'total_time': msg.total_time
            }

        messages_data.append(msg_data)

    return JsonResponse({
        'success': True,
        'messages': messages_data,
        'has_next': page_obj.has_next(),
        'has_previous': page_obj.has_previous(),
        'total_pages': paginator.num_pages,
        'current_page': page
    })
