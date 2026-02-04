"""
Service RAG pour le chatbot NOXA
Gère la récupération de documents et la génération de réponses
"""
import time
import logging
from typing import List, Dict, Optional
from dataclasses import dataclass, field

from django.conf import settings

# Configuration du logging
logger = logging.getLogger('services.rag')


@dataclass
class RetrievedChunk:
    """Représente un chunk récupéré avec son score de pertinence"""
    publication_id: int
    publication_title: str
    chunk_index: int
    content: str
    page_number: Optional[int]
    relevance_score: float
    metadata: Dict = field(default_factory=dict)


@dataclass
class RAGResponse:
    """Réponse complète du pipeline RAG"""
    answer: str
    sources: List[RetrievedChunk]
    query_embedding_time: float
    retrieval_time: float
    generation_time: float
    total_time: float


class EmbeddingService:
    """Service pour générer les embeddings des requêtes"""

    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self.model_name = model_name
        self._model = None

    @property
    def model(self):
        """Charge le modèle de manière paresseuse"""
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
                self._model = SentenceTransformer(self.model_name)
                logger.info(f"Modèle d'embedding chargé: {self.model_name}")
            except ImportError:
                logger.warning("sentence-transformers non installé, utilisation du mode mock")
                self._model = "mock"
        return self._model

    def embed_query(self, query: str) -> List[float]:
        """
        Génère l'embedding pour une requête

        Args:
            query: Texte de la requête

        Returns:
            Vecteur d'embedding
        """
        if self.model == "mock":
            # Mode mock pour le développement
            import hashlib
            hash_val = int(hashlib.md5(query.encode()).hexdigest(), 16)
            return [(hash_val >> i) % 1000 / 1000 for i in range(384)]

        embedding = self.model.encode(query, convert_to_tensor=False)
        return embedding.tolist()


class VectorStoreService:
    """Service pour interagir avec le vector store (Pinecone/Chroma)"""

    def __init__(self, use_pinecone: bool = True):
        self.use_pinecone = use_pinecone
        self._index = None

    def search(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        topic_filter: Optional[int] = None
    ) -> List[Dict]:
        """
        Recherche les chunks les plus pertinents

        Args:
            query_embedding: Vecteur de la requête
            top_k: Nombre de résultats à retourner
            topic_filter: ID du topic pour filtrer (optionnel)

        Returns:
            Liste de résultats avec scores
        """
        # TODO: Implémenter la connexion à Pinecone/Chroma
        # Pour l'instant, retourne des résultats de test

        logger.info(f"Recherche vectorielle: top_k={top_k}, topic_filter={topic_filter}")

        # Mode développement: recherche dans les chunks de la base Django
        return self._search_django_chunks(query_embedding, top_k, topic_filter)

    def _search_django_chunks(
        self,
        query_embedding: List[float],
        top_k: int,
        topic_filter: Optional[int]
    ) -> List[Dict]:
        """
        Recherche de fallback dans les chunks Django
        Utilise une recherche textuelle simple en attendant le vector store
        """
        from base.models import DocumentChunk, Publication

        # Récupère les chunks disponibles
        chunks_qs = DocumentChunk.objects.select_related('publication')

        if topic_filter:
            chunks_qs = chunks_qs.filter(publication__topic_id=topic_filter)

        chunks = list(chunks_qs[:100])  # Limite pour la démo

        if not chunks:
            return []

        # Scoring simple basé sur la longueur (placeholder)
        # TODO: Remplacer par une vraie recherche vectorielle
        results = []
        for chunk in chunks[:top_k]:
            results.append({
                'id': chunk.pinecone_id,
                'score': 0.8,  # Score fictif
                'metadata': {
                    'publication_id': chunk.publication.id,
                    'publication_title': chunk.publication.theme,
                    'chunk_index': chunk.chunk_index,
                    'page_number': chunk.page_number,
                    'content': chunk.content[:500]  # Extrait
                }
            })

        return results


class LLMService:
    """Service pour la génération de réponses avec un LLM"""

    def __init__(self, model: str = "gpt-3.5-turbo"):
        self.model = model
        self.api_key = getattr(settings, 'OPENAI_API_KEY', None)

    def generate_response(
        self,
        query: str,
        context_chunks: List[RetrievedChunk],
        conversation_history: List[Dict] = None,
        topic_name: str = None
    ) -> str:
        """
        Génère une réponse basée sur le contexte récupéré

        Args:
            query: Question de l'utilisateur
            context_chunks: Chunks de contexte récupérés
            conversation_history: Historique de la conversation
            topic_name: Nom du topic pour contextualiser

        Returns:
            Réponse générée
        """
        # Construit le contexte
        context = self._build_context(context_chunks)

        # Construit le prompt
        system_prompt = self._build_system_prompt(topic_name)
        user_prompt = self._build_user_prompt(query, context, conversation_history)

        # Appel au LLM
        try:
            response = self._call_llm(system_prompt, user_prompt)
        except Exception as e:
            logger.error(f"Erreur LLM: {e}")
            response = self._generate_fallback_response(query, context_chunks)

        return response

    def _build_context(self, chunks: List[RetrievedChunk]) -> str:
        """Construit le contexte à partir des chunks"""
        if not chunks:
            return "Aucun document pertinent trouvé."

        context_parts = []
        for i, chunk in enumerate(chunks, 1):
            source_info = f"[Source {i}: {chunk.publication_title}"
            if chunk.page_number:
                source_info += f", page {chunk.page_number}"
            source_info += "]"

            context_parts.append(f"{source_info}\n{chunk.content}")

        return "\n\n---\n\n".join(context_parts)

    def _build_system_prompt(self, topic_name: str = None) -> str:
        """Construit le prompt système"""
        base_prompt = """Tu es NOXA, un assistant intelligent spécialisé dans l'aide aux étudiants pour leurs travaux académiques.
Tu as accès aux mémoires et rapports académiques de l'école.

Tes missions:
1. Fournir des réponses précises liées aux thématiques de recherche
2. Citer les références pertinentes des mémoires existants
3. Proposer des sources et travaux similaires quand c'est pertinent

Instructions:
- Réponds de manière claire et structurée
- Cite toujours tes sources avec le nom du document et la page si disponible
- Si tu n'as pas assez d'informations, dis-le honnêtement
- Utilise un ton professionnel mais accessible
- Réponds en français"""

        if topic_name:
            base_prompt += f"\n\nContexte: Cette conversation porte sur le thème '{topic_name}'."

        return base_prompt

    def _build_user_prompt(
        self,
        query: str,
        context: str,
        history: List[Dict] = None
    ) -> str:
        """Construit le prompt utilisateur"""
        prompt = f"""Voici les documents pertinents trouvés dans notre base:

{context}

---

Question de l'étudiant: {query}

Réponds à cette question en te basant sur les documents fournis. Cite tes sources."""

        return prompt

    def _call_llm(self, system_prompt: str, user_prompt: str) -> str:
        """Appelle l'API du LLM"""
        if not self.api_key or self.api_key == 'openai-api-key':
            logger.warning("Clé API LLM non configurée")
            return "Désolé, je ne peux pas générer de réponse pour le moment car le service LLM n'est pas configuré."

        try:
            import openai
            client = openai.OpenAI(api_key=self.api_key)
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=1000
            )

            return response.choices[0].message.content

        except Exception as e:
            logger.error(f"Erreur OpenAI: {e}")
            raise

    def _generate_fallback_response(
        self,
        query: str,
        chunks: List[RetrievedChunk]
    ) -> str:
        """Génère une réponse de fallback si le LLM échoue"""
        if not chunks:
            return "Je n'ai pas trouvé de documents pertinents pour répondre à votre question. Pourriez-vous reformuler ou préciser votre recherche?"

        response = f"Concernant votre question sur '{query}', voici les documents pertinents que j'ai trouvés:\n\n"

        for i, chunk in enumerate(chunks[:3], 1):
            response += f"**{i}. {chunk.publication_title}**"
            if chunk.page_number:
                response += f" (page {chunk.page_number})"
            response += f"\n> {chunk.content[:200]}...\n\n"

        response += "\nJe vous recommande de consulter ces documents pour plus de détails."

        return response


class RAGService:
    """
    Service principal RAG qui orchestre le pipeline complet:
    Query -> Embedding -> Retrieval -> Generation -> Response
    
    Utilise maintenant DjangoRAGService qui intègre les modules src/
    """

    def __init__(self):
        # Utilise le nouveau service d'intégration
        from chat.rag_integration import get_django_rag_service
        self.django_rag = get_django_rag_service()
        
        # Garde les anciens services pour compatibilité (mode fallback)
        self.embedding_service = EmbeddingService()
        self.vector_store = VectorStoreService()
        self.llm_service = LLMService()

    def process_query(
        self,
        query: str,
        topic_id: Optional[int] = None,
        topic_name: Optional[str] = None,
        conversation_history: List[Dict] = None,
        top_k: int = 5
    ) -> RAGResponse:
        """
        Traite une requête utilisateur avec le pipeline RAG complet

        Args:
            query: Question de l'utilisateur
            topic_id: ID du topic pour filtrer (optionnel)
            topic_name: Nom du topic pour le contexte
            conversation_history: Historique des messages
            top_k: Nombre de documents à récupérer

        Returns:
            RAGResponse avec la réponse et les métriques
        """
        # Délègue au service d'intégration Django
        return self.django_rag.process_query(
            query=query,
            topic_id=topic_id,
            topic_name=topic_name,
            conversation_history=conversation_history,
            top_k=top_k
        )

    def get_suggested_questions(self, topic_id: Optional[int] = None) -> List[str]:
        """
        Retourne des suggestions de questions basées sur le topic

        Args:
            topic_id: ID du topic (optionnel)

        Returns:
            Liste de questions suggérées
        """
        return self.django_rag.get_suggested_questions(topic_id)


# Instance singleton pour réutilisation
_rag_service = None

def get_rag_service() -> RAGService:
    """Retourne l'instance singleton du service RAG"""
    global _rag_service
    if _rag_service is None:
        _rag_service = RAGService()
    return _rag_service
