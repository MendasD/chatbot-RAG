/**
 * Chat Interface JavaScript
 * Gère la logique du chatbot RAG
 */

class ChatInterface {
    constructor() {
        this.currentConversationId = null;
        this.isLoading = false;
        this.messageCount = 0;
        this.init();
    }

    init() {
        this.cacheElements();
        this.attachEventListeners();
        this.loadConversation();
    }

    cacheElements() {
        // Sidebar
        this.newChatBtn = document.querySelector('.new-chat-btn');
        this.conversationsList = document.querySelector('.conversations-list');

        // Header
        this.chatHeaderTitle = document.querySelector('.chat-header-title');

        // Messages
        this.chatMessages = document.querySelector('.chat-messages');

        // Input
        this.chatInput = document.querySelector('.chat-input');
        this.sendBtn = document.querySelector('.send-btn');
        this.inputWrapper = document.querySelector('.input-field-wrapper');
    }

    attachEventListeners() {
        this.newChatBtn?.addEventListener('click', () => this.createNewConversation());
        this.sendBtn?.addEventListener('click', () => this.sendMessage());
        this.chatInput?.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });

        // Delegation pour les conversations
        this.conversationsList?.addEventListener('click', (e) => {
            const deleteBtn = e.target.closest('.conversation-delete-btn');
            const item = e.target.closest('.conversation-item');

            if (deleteBtn) {
                e.stopPropagation();
                const id = deleteBtn.dataset.conversationId;
                this.deleteConversation(id);
            } else if (item) {
                const id = item.dataset.conversationId;
                this.loadConversation(id);
            }
        });

        // Delegation pour les feedbacks
        this.chatMessages?.addEventListener('click', (e) => {
            const feedbackBtn = e.target.closest('.feedback-btn');
            if (feedbackBtn) {
                const messageId = feedbackBtn.dataset.messageId;
                const type = feedbackBtn.dataset.type;
                this.submitFeedback(messageId, type, feedbackBtn);
            }
        });

        // Auto-resize textarea
        this.chatInput?.addEventListener('input', () => this.autoResizeInput());
    }

    autoResizeInput() {
        if (!this.chatInput) return;
        this.chatInput.style.height = 'auto';
        this.chatInput.style.height = Math.min(this.chatInput.scrollHeight, 120) + 'px';
    }

    async createNewConversation() {
        try {
            const topicId = document.querySelector('[data-topic-id]')?.dataset.topicId;
            
            const response = await fetch('/chat/api/conversation/create/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCsrfToken()
                },
                body: JSON.stringify({
                    topic_id: topicId || null,
                    title: ''
                })
            });

            if (!response.ok) {
                throw new Error('Erreur lors de la création de la conversation');
            }

            const data = await response.json();
            
            if (data.success) {
                this.loadConversation(data.conversation_id);
                window.history.pushState(null, '', `/chat/conversation/${data.conversation_id}/`);
            }
        } catch (error) {
            console.error('Erreur:', error);
            this.showError('Impossible de créer une conversation');
        }
    }

    async loadConversation(conversationId = null) {
        try {
            // Si pas d'ID, cherche celui de la page
            if (!conversationId) {
                const urlMatch = window.location.pathname.match(/\/chat\/conversation\/(\d+)\//);
                if (urlMatch) {
                    conversationId = urlMatch[1];
                }
            }

            if (conversationId) {
                this.currentConversationId = conversationId;
                await this.loadMessageHistory(conversationId);
                this.updateConversationUI(conversationId);
                this.chatInput?.focus();
            } else {
                this.showEmptyState();
            }
        } catch (error) {
            console.error('Erreur:', error);
            this.showError('Impossible de charger la conversation');
        }
    }

    async loadMessageHistory(conversationId, page = 1) {
        try {
            const response = await fetch(`/chat/api/conversation/${conversationId}/history/?page=${page}`, {
                headers: {
                    'Accept': 'application/json'
                }
            });

            if (!response.ok) {
                throw new Error('Erreur lors du chargement de l\'historique');
            }

            const data = await response.json();
            
            if (data.success) {
                this.displayMessages(data.messages);
            }
        } catch (error) {
            console.error('Erreur:', error);
        }
    }

    displayMessages(messages) {
        this.chatMessages.innerHTML = '';
        
        if (messages.length === 0) {
            this.showEmptyState();
            return;
        }

        messages.forEach(msg => {
            const msgEl = this.createMessageElement(msg);
            this.chatMessages.appendChild(msgEl);
        });

        this.scrollToBottom();
    }

    createMessageElement(message) {
        const msgDiv = document.createElement('div');
        msgDiv.className = `message ${message.role}`;
        msgDiv.dataset.messageId = message.id;

        const avatar = document.createElement('div');
        avatar.className = 'message-avatar';
        avatar.textContent = message.role === 'user' ? 'V' : 'A';

        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';

        const textDiv = document.createElement('div');
        textDiv.className = 'message-text';
        textDiv.innerHTML = this.sanitizeHtml(message.content);
        contentDiv.appendChild(textDiv);

        if (message.sources && message.sources.length > 0) {
            contentDiv.appendChild(this.createSourcesElement(message.sources));
        }

        if (message.metrics) {
            contentDiv.appendChild(this.createMetricsElement(message.metrics));
        }

        const timestampDiv = document.createElement('div');
        timestampDiv.className = 'message-timestamp';
        timestampDiv.textContent = new Date(message.created_at).toLocaleTimeString();
        contentDiv.appendChild(timestampDiv);

        if (message.role === 'assistant') {
            contentDiv.appendChild(this.createFeedbackElement(message.id, message.is_helpful));
        }

        msgDiv.appendChild(avatar);
        msgDiv.appendChild(contentDiv);

        return msgDiv;
    }

    createSourcesElement(sources) {
        const sourcesDiv = document.createElement('div');
        sourcesDiv.className = 'message-sources';

        const title = document.createElement('div');
        title.className = 'sources-title';
        title.textContent = '📚 Sources utilisées';
        sourcesDiv.appendChild(title);

        sources.forEach(source => {
            const sourceItem = document.createElement('div');
            sourceItem.className = 'source-item';

            sourceItem.innerHTML = `
                <div class="source-title">
                    ${this.sanitizeHtml(source.publication_title)}
                    <span class="source-score">${(source.relevance_score * 100).toFixed(0)}%</span>
                </div>
                <div class="source-info">
                    ${source.page_number ? `📄 Page ${source.page_number} • ` : ''}
                    <em>"${this.sanitizeHtml(source.excerpt.substring(0, 100))}..."</em>
                </div>
            `;
            sourcesDiv.appendChild(sourceItem);
        });

        return sourcesDiv;
    }

    createMetricsElement(metrics) {
        const metricsDiv = document.createElement('div');
        metricsDiv.className = 'message-metrics';

        const total = (metrics.embedding_time + metrics.retrieval_time + metrics.generation_time).toFixed(2);
        
        metricsDiv.innerHTML = `
            <span class="metric-item">
                <span class="metric-label">⚡ Total:</span> ${total}ms
            </span>
            <span class="metric-item">
                <span class="metric-label">🔍 Recherche:</span> ${metrics.retrieval_time?.toFixed(2) || 0}ms
            </span>
            <span class="metric-item">
                <span class="metric-label">🤖 Génération:</span> ${metrics.generation_time?.toFixed(2) || 0}ms
            </span>
        `;

        return metricsDiv;
    }

    createFeedbackElement(messageId, isHelpful = null) {
        const feedbackDiv = document.createElement('div');
        feedbackDiv.className = 'message-feedback';

        const likeBtn = document.createElement('button');
        likeBtn.className = `feedback-btn ${isHelpful === true ? 'active' : ''}`;
        likeBtn.textContent = '👍 Utile';
        likeBtn.dataset.messageId = messageId;
        likeBtn.dataset.type = 'helpful';

        const dislikeBtn = document.createElement('button');
        dislikeBtn.className = `feedback-btn ${isHelpful === false ? 'active' : ''}`;
        dislikeBtn.textContent = '👎 Pas utile';
        dislikeBtn.dataset.messageId = messageId;
        dislikeBtn.dataset.type = 'not_helpful';

        feedbackDiv.appendChild(likeBtn);
        feedbackDiv.appendChild(dislikeBtn);

        return feedbackDiv;
    }

    async sendMessage() {
        const message = this.chatInput.value.trim();

        if (!message || !this.currentConversationId || this.isLoading) {
            return;
        }

        this.isLoading = true;
        this.sendBtn.disabled = true;

        try {
            // Ajoute le message utilisateur
            const userMsgEl = this.createMessageElement({
                id: 0,
                role: 'user',
                content: message,
                created_at: new Date().toISOString()
            });
            this.chatMessages.appendChild(userMsgEl);

            // Clear input
            this.chatInput.value = '';
            this.chatInput.style.height = 'auto';

            // Ajoute indicateur de chargement
            const loadingMsg = this.createLoadingMessage();
            this.chatMessages.appendChild(loadingMsg);
            this.scrollToBottom();

            // Envoie la requête
            const response = await fetch(
                `/chat/api/conversation/${this.currentConversationId}/send/`,
                {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': this.getCsrfToken()
                    },
                    body: JSON.stringify({ message })
                }
            );

            if (!response.ok) {
                throw new Error('Erreur lors de l\'envoi du message');
            }

            const data = await response.json();

            if (data.success) {
                // Supprime le loading message
                loadingMsg.remove();

                // Ajoute la réponse
                const assistantMsgEl = this.createMessageElement({
                    id: data.assistant_message.id,
                    role: 'assistant',
                    content: data.assistant_message.content,
                    sources: data.assistant_message.sources,
                    metrics: data.assistant_message.metrics,
                    created_at: data.assistant_message.created_at,
                    is_helpful: null
                });
                this.chatMessages.appendChild(assistantMsgEl);

                // Met à jour le titre
                if (data.conversation_title) {
                    this.chatHeaderTitle.textContent = data.conversation_title;
                }
            } else {
                throw new Error(data.error || 'Erreur inconnue');
            }
        } catch (error) {
            console.error('Erreur:', error);
            this.showError('Impossible d\'envoyer le message: ' + error.message);
            loadingMsg?.remove();
        } finally {
            this.isLoading = false;
            this.sendBtn.disabled = false;
            this.scrollToBottom();
            this.chatInput?.focus();
        }
    }

    createLoadingMessage() {
        const msgDiv = document.createElement('div');
        msgDiv.className = 'message assistant';

        const avatar = document.createElement('div');
        avatar.className = 'message-avatar';
        avatar.textContent = 'A';

        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';

        const textDiv = document.createElement('div');
        textDiv.className = 'message-text';
        textDiv.innerHTML = `
            <div class="loading-indicator">
                <div class="loading-dot"></div>
                <div class="loading-dot"></div>
                <div class="loading-dot"></div>
            </div>
        `;
        contentDiv.appendChild(textDiv);

        msgDiv.appendChild(avatar);
        msgDiv.appendChild(contentDiv);

        return msgDiv;
    }

    async submitFeedback(messageId, type, btn) {
        try {
            const isHelpful = type === 'helpful';

            const response = await fetch(`/chat/api/message/${messageId}/feedback/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCsrfToken()
                },
                body: JSON.stringify({ is_helpful: isHelpful })
            });

            if (response.ok) {
                // Update button UI
                const feedbackBtns = btn.parentElement.querySelectorAll('.feedback-btn');
                feedbackBtns.forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
            }
        } catch (error) {
            console.error('Erreur feedback:', error);
        }
    }

    async deleteConversation(conversationId) {
        if (!confirm('Êtes-vous sûr de vouloir supprimer cette conversation?')) {
            return;
        }

        try {
            const response = await fetch(`/chat/api/conversation/${conversationId}/delete/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': this.getCsrfToken()
                }
            });

            if (response.ok) {
                // Recharge la liste
                location.reload();
            }
        } catch (error) {
            console.error('Erreur:', error);
            this.showError('Impossible de supprimer la conversation');
        }
    }

    updateConversationUI(conversationId) {
        // Met à jour l'affichage de la conversation active
        document.querySelectorAll('.conversation-item').forEach(item => {
            item.classList.remove('active');
            if (item.dataset.conversationId === String(conversationId)) {
                item.classList.add('active');
            }
        });
    }

    showEmptyState() {
        this.chatMessages.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">💬</div>
                <div class="empty-state-title">Nouvelle conversation</div>
                <p class="empty-state-description">
                    Posez une question et je vous aiderai en utilisant les mémoires et documents académiques disponibles.
                </p>
                <div class="suggestions" id="suggestions"></div>
            </div>
        `;
        this.loadSuggestions();
    }

    async loadSuggestions() {
        try {
            const topicId = document.querySelector('[data-topic-id]')?.dataset.topicId;
            const params = topicId ? `?topic_id=${topicId}` : '';
            
            const response = await fetch(`/chat/api/suggestions/${params}`);
            const data = await response.json();

            if (data.success) {
                const suggestionsDiv = document.getElementById('suggestions');
                data.suggestions.forEach(suggestion => {
                    const card = document.createElement('div');
                    card.className = 'suggestion-card';
                    card.textContent = suggestion;
                    card.addEventListener('click', () => {
                        this.chatInput.value = suggestion;
                        this.autoResizeInput();
                        this.chatInput.focus();
                    });
                    suggestionsDiv.appendChild(card);
                });
            }
        } catch (error) {
            console.error('Erreur suggestions:', error);
        }
    }

    showError(message) {
        const msgDiv = document.createElement('div');
        msgDiv.className = 'message assistant';
        msgDiv.innerHTML = `
            <div class="message-avatar">⚠️</div>
            <div class="message-content">
                <div class="message-text" style="background-color: #fee; color: #c00;">
                    ${this.sanitizeHtml(message)}
                </div>
            </div>
        `;
        this.chatMessages.appendChild(msgDiv);
        this.scrollToBottom();
    }

    scrollToBottom() {
        if (this.chatMessages) {
            this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
        }
    }

    getCsrfToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]')?.value ||
               document.querySelector('meta[name="csrf-token"]')?.content || '';
    }

    sanitizeHtml(html) {
        const div = document.createElement('div');
        div.textContent = html;
        return div.innerHTML;
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    window.chatInterface = new ChatInterface();
});
