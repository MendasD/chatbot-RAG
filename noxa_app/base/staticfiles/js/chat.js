/**
 * NOXA Chat - JavaScript pour l'interface chatbot
 */

class NoxaChat {
    constructor(config) {
        this.config = config;
        this.conversationId = config.conversationId;
        this.isLoading = false;

        this.init();
    }

    init() {
        // Éléments DOM
        this.elements = {
            messageInput: document.getElementById('messageInput'),
            sendBtn: document.getElementById('sendBtn'),
            chatForm: document.getElementById('chatForm'),
            messagesContainer: document.getElementById('messagesContainer'),
            charCount: document.getElementById('charCount'),
            typingIndicator: document.getElementById('typingIndicator'),
            conversationTitle: document.getElementById('conversationTitle'),
            newChatBtn: document.getElementById('newChatBtn'),
            newChatModal: document.getElementById('newChatModal'),
            closeModal: document.getElementById('closeModal'),
            cancelNewChat: document.getElementById('cancelNewChat'),
            confirmNewChat: document.getElementById('confirmNewChat'),
            newChatTopic: document.getElementById('newChatTopic'),
            conversationsList: document.getElementById('conversationsList'),
            chatWelcome: document.getElementById('chatWelcome'),
        };

        this.bindEvents();
        this.hideWelcomeIfMessages();
        this.scrollToBottom();
    }

    hideWelcomeIfMessages() {
        // Masquer le welcome s'il y a des messages
        if (this.elements.chatWelcome && this.elements.messagesContainer) {
            const hasMessages = this.elements.messagesContainer.querySelectorAll('.message').length > 0;
            if (hasMessages) {
                this.elements.chatWelcome.style.display = 'none !important';
            }
        }
    }

    bindEvents() {
        // Formulaire de message
        if (this.elements.chatForm) {
            this.elements.chatForm.addEventListener('submit', (e) => this.handleSubmit(e));
        }

        // Textarea auto-resize et compteur
        if (this.elements.messageInput) {
            this.elements.messageInput.addEventListener('input', () => this.handleInput());
            this.elements.messageInput.addEventListener('keydown', (e) => this.handleKeydown(e));
        }

        // Bouton nouvelle conversation
        if (this.elements.newChatBtn) {
            this.elements.newChatBtn.addEventListener('click', () => this.openNewChatModal());
        }

        // Modal
        if (this.elements.closeModal) {
            this.elements.closeModal.addEventListener('click', () => this.closeNewChatModal());
        }
        if (this.elements.cancelNewChat) {
            this.elements.cancelNewChat.addEventListener('click', () => this.closeNewChatModal());
        }
        if (this.elements.confirmNewChat) {
            this.elements.confirmNewChat.addEventListener('click', () => this.createConversation());
        }

        // Suggestions de questions
        document.querySelectorAll('.suggestion-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const question = btn.dataset.question;
                if (this.elements.messageInput) {
                    this.elements.messageInput.value = question;
                    this.handleInput();
                    this.elements.messageInput.focus();
                }
            });
        });

        // Toggle sources
        document.querySelectorAll('.sources-toggle').forEach(btn => {
            btn.addEventListener('click', (e) => this.toggleSources(e));
        });

        // Feedback buttons
        document.querySelectorAll('.feedback-btn').forEach(btn => {
            btn.addEventListener('click', (e) => this.handleFeedback(e));
        });

        // Delete conversation buttons
        document.querySelectorAll('.delete-conv-btn').forEach(btn => {
            btn.addEventListener('click', (e) => this.handleDeleteConversation(e));
        });

        // Fermer modal en cliquant en dehors
        if (this.elements.newChatModal) {
            this.elements.newChatModal.addEventListener('click', (e) => {
                if (e.target === this.elements.newChatModal) {
                    this.closeNewChatModal();
                }
            });
        }
    }

    handleInput() {
        const input = this.elements.messageInput;
        const charCount = this.elements.charCount;
        const sendBtn = this.elements.sendBtn;

        // Compteur de caractères
        const count = input.value.length;
        charCount.textContent = `${count} / 2000`;

        // Activer/désactiver le bouton d'envoi
        sendBtn.disabled = count === 0 || count > 2000 || this.isLoading;

        // Auto-resize du textarea
        input.style.height = 'auto';
        input.style.height = Math.min(input.scrollHeight, 200) + 'px';
    }

    handleKeydown(e) {
        // Envoyer avec Enter (sans Shift)
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            if (!this.elements.sendBtn.disabled) {
                this.handleSubmit(e);
            }
        }
    }

    async handleSubmit(e) {
        e.preventDefault();

        const message = this.elements.messageInput.value.trim();
        if (!message || this.isLoading) return;

        // Si pas de conversation active, en créer une d'abord
        if (!this.conversationId) {
            await this.createConversation();
            if (!this.conversationId) return;
        }

        this.isLoading = true;
        this.elements.sendBtn.disabled = true;
        this.elements.typingIndicator.style.display = 'flex';

        // Ajouter le message utilisateur à l'UI
        this.addMessageToUI('user', message);
        this.elements.messageInput.value = '';
        this.handleInput();

        try {
            const response = await this.sendMessage(message);

            if (response.success) {
                // Ajouter la réponse de l'assistant
                this.addAssistantMessageToUI(response.assistant_message);

                // Mettre à jour le titre si c'est le premier message
                if (response.conversation_title && this.elements.conversationTitle) {
                    this.elements.conversationTitle.textContent = response.conversation_title;
                }
            } else {
                this.showError(response.error || 'Erreur lors de l\'envoi du message');
            }
        } catch (error) {
            this.showError('Erreur de connexion. Veuillez réessayer.');
        } finally {
            this.isLoading = false;
            this.elements.sendBtn.disabled = false;
            this.elements.typingIndicator.style.display = 'none';
        }
    }

    async sendMessage(message) {
        const url = this.config.urls.sendMessage;

        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': this.config.csrfToken
            },
            body: JSON.stringify({ message })
        });

        return await response.json();
    }

    addMessageToUI(role, content) {
        // Masquer l'écran de bienvenue
        if (this.elements.chatWelcome) {
            this.elements.chatWelcome.style.display = 'none';
        }

        // Créer ou afficher le container de messages
        if (!this.elements.messagesContainer) {
            // Créer le container si inexistant
            const main = document.querySelector('.chat-main');
            const inputContainer = document.querySelector('.chat-input-container');

            const container = document.createElement('div');
            container.className = 'messages-container';
            container.id = 'messagesContainer';

            main.insertBefore(container, inputContainer);
            this.elements.messagesContainer = container;
        }

        const messageDiv = document.createElement('div');
        messageDiv.className = `message message-${role}`;

        const initial = role === 'user' ?
            document.querySelector('.avatar-user')?.textContent || 'U' :
            'N';

        messageDiv.innerHTML = `
            <div class="message-avatar">
                <div class="avatar-${role}">${initial}</div>
            </div>
            <div class="message-content">
                <div class="message-text">${this.formatMessage(content)}</div>
            </div>
        `;

        messageDiv.classList.add('new-message');
        this.elements.messagesContainer.appendChild(messageDiv);
        this.scrollToBottom();
    }

    addAssistantMessageToUI(messageData) {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message message-assistant';
        messageDiv.dataset.id = messageData.id;

        let sourcesHTML = '';
        if (messageData.sources && messageData.sources.length > 0) {
            const sourceItems = messageData.sources.map(s => `
                <a href="/publication/${s.publication_id}/" class="source-item" target="_blank">
                    <strong>${this.escapeHtml(s.publication_title)}</strong>
                    ${s.page_number ? `<span class="source-page">Page ${s.page_number}</span>` : ''}
                    <span class="source-score">${Math.round(s.relevance_score * 100)}%</span>
                </a>
            `).join('');

            sourcesHTML = `
                <div class="message-sources">
                    <button class="sources-toggle">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                            <polyline points="14 2 14 8 20 8"></polyline>
                        </svg>
                        ${messageData.sources.length} source${messageData.sources.length > 1 ? 's' : ''}
                    </button>
                    <div class="sources-list" style="display: none;">
                        ${sourceItems}
                    </div>
                </div>
            `;
        }

        messageDiv.innerHTML = `
            <div class="message-avatar">
                <div class="avatar-assistant">N</div>
            </div>
            <div class="message-content">
                <div class="message-text">${this.formatMessage(messageData.content)}</div>
                ${sourcesHTML}
                <div class="message-feedback">
                    <button class="feedback-btn" data-type="helpful" data-id="${messageData.id}" title="Utile">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M14 9V5a3 3 0 0 0-3-3l-4 9v11h11.28a2 2 0 0 0 2-1.7l1.38-9a2 2 0 0 0-2-2.3zM7 22H4a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2h3"></path>
                        </svg>
                    </button>
                    <button class="feedback-btn" data-type="not-helpful" data-id="${messageData.id}" title="Pas utile">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M10 15v4a3 3 0 0 0 3 3l4-9V2H5.72a2 2 0 0 0-2 1.7l-1.38 9a2 2 0 0 0 2 2.3zm7-13h2.67A2.31 2.31 0 0 1 22 4v7a2.31 2.31 0 0 1-2.33 2H17"></path>
                        </svg>
                    </button>
                </div>
            </div>
        `;

        messageDiv.classList.add('new-message');
        this.elements.messagesContainer.appendChild(messageDiv);

        // Bind events pour le nouveau message
        messageDiv.querySelectorAll('.sources-toggle').forEach(btn => {
            btn.addEventListener('click', (e) => this.toggleSources(e));
        });
        messageDiv.querySelectorAll('.feedback-btn').forEach(btn => {
            btn.addEventListener('click', (e) => this.handleFeedback(e));
        });

        this.scrollToBottom();
    }

    formatMessage(content) {
        // Convertir les sauts de ligne en <p> et <br>
        return content
            .split('\n\n')
            .map(para => `<p>${para.replace(/\n/g, '<br>')}</p>`)
            .join('');
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    scrollToBottom() {
        if (this.elements.messagesContainer) {
            this.elements.messagesContainer.scrollTop = this.elements.messagesContainer.scrollHeight;
        }
    }

    toggleSources(e) {
        const btn = e.currentTarget;
        const sourcesList = btn.nextElementSibling;

        if (sourcesList) {
            const isHidden = sourcesList.style.display === 'none';
            sourcesList.style.display = isHidden ? 'flex' : 'none';
        }
    }

    async handleFeedback(e) {
        const btn = e.currentTarget;
        const messageId = btn.dataset.id;
        const type = btn.dataset.type;
        const isHelpful = type === 'helpful';

        // Toggle active state
        const parent = btn.parentElement;
        parent.querySelectorAll('.feedback-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');

        try {
            const url = this.config.urls.submitFeedback.replace('{id}', messageId);
            await fetch(url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.config.csrfToken
                },
                body: JSON.stringify({ is_helpful: isHelpful })
            });
        } catch (error) {
        }
    }

    async handleDeleteConversation(e) {
        e.preventDefault();
        e.stopPropagation();

        const btn = e.currentTarget;
        const convId = btn.dataset.id;

        if (!confirm('Supprimer cette conversation ?')) return;

        try {
            const url = this.config.urls.deleteConversation.replace('{id}', convId);
            const response = await fetch(url, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': this.config.csrfToken,
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });

            if (response.ok) {
                // Supprimer de l'UI avec animation
                const convItem = btn.closest('.conversation-item');
                if (convItem) {
                    convItem.style.animation = 'slideOutLeft 0.4s ease-out forwards';
                    setTimeout(() => convItem.remove(), 400);
                }

                // Afficher message toast
                this.showToast('Conversation supprimée avec succès', 'success');

                // Rediriger si c'est la conversation active
                if (this.conversationId === parseInt(convId)) {
                    setTimeout(() => {
                        window.location.href = '/chat/';
                    }, 800);
                }
            }
        } catch (error) {
            this.showToast('Erreur lors de la suppression', 'error');
        }
    }

    showToast(message, type = 'info') {
        const toastContainer = document.querySelector('.toast-messages') || this.createToastContainer();
        const toast = document.createElement('div');
        toast.className = `toast-message toast-${type}`;
        toast.innerHTML = `
            <span>${message}</span>
            <button type="button" class="close-btn" aria-label="Close">&times;</button>
        `;
        toastContainer.appendChild(toast);
        
        // Auto-remove après 3 secondes
        setTimeout(() => {
            toast.style.animation = 'slideOutUp 0.3s ease-out forwards';
            setTimeout(() => toast.remove(), 300);
        }, 3000);

        // Close button
        toast.querySelector('.close-btn').addEventListener('click', () => {
            toast.style.animation = 'slideOutUp 0.3s ease-out forwards';
            setTimeout(() => toast.remove(), 300);
        });
    }

    createToastContainer() {
        const container = document.createElement('div');
        container.className = 'toast-messages';
        document.body.appendChild(container);
        return container;
    }

    openNewChatModal() {
        if (this.elements.newChatModal) {
            this.elements.newChatModal.style.display = 'flex';
        }
    }

    closeNewChatModal() {
        if (this.elements.newChatModal) {
            this.elements.newChatModal.style.display = 'none';
        }
    }

    async createConversation() {
        const topicId = this.elements.newChatTopic?.value || null;

        try {
            const response = await fetch(this.config.urls.createConversation, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.config.csrfToken
                },
                body: JSON.stringify({
                    topic_id: topicId ? parseInt(topicId) : null
                })
            });

            const data = await response.json();

            if (data.success) {
                this.closeNewChatModal();

                // Mettre à jour l'ID de conversation
                this.conversationId = data.conversation_id;

                // Mettre à jour l'URL de sendMessage
                this.config.urls.sendMessage = `/chat/api/conversation/${data.conversation_id}/send/`;

                // Rediriger vers la nouvelle conversation
                window.location.href = data.redirect_url;
            } else {
                this.showError(data.error || 'Erreur lors de la création');
            }
        } catch (error) {
            this.showError('Erreur de connexion');
        }
    }

    showError(message) {
        // Créer une notification d'erreur temporaire
        const notification = document.createElement('div');
        notification.className = 'chat-notification error';
        notification.textContent = message;
        notification.style.cssText = `
            position: fixed;
            bottom: 100px;
            left: 50%;
            transform: translateX(-50%);
            background-color: #ef4444;
            color: white;
            padding: 12px 24px;
            border-radius: 8px;
            z-index: 1000;
            animation: fadeIn 0.3s ease;
        `;

        document.body.appendChild(notification);

        setTimeout(() => {
            notification.style.animation = 'fadeOut 0.3s ease';
            setTimeout(() => notification.remove(), 300);
        }, 3000);
    }
}

// Initialisation
document.addEventListener('DOMContentLoaded', () => {
    if (typeof CONFIG !== 'undefined') {
        window.noxaChat = new NoxaChat(CONFIG);
    }
});

// Animations CSS
const style = document.createElement('style');
style.textContent = `
    @keyframes fadeIn {
        from { opacity: 0; transform: translateX(-50%) translateY(10px); }
        to { opacity: 1; transform: translateX(-50%) translateY(0); }
    }
    @keyframes fadeOut {
        from { opacity: 1; transform: translateX(-50%) translateY(0); }
        to { opacity: 0; transform: translateX(-50%) translateY(10px); }
    }
`;
document.head.appendChild(style);
