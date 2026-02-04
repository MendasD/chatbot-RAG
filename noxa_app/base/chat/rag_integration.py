"""
Service d'intégration RAG pour Django
Connecte les modules src/ (LLMHandler, PineconeRetriever) au chatbot Django
"""
import sys
import os
import logging
from typing import List, Dict, Optional
from dataclasses import dataclass

from django.conf import settings

# Ajoute le dossier racine au path pour importer src/
BASE_DIR = settings.BASE_DIR.parent.parent  # Remonte de noxa_app/base/ à la racine
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

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
    metadata: Dict


@dataclass
class RAGResponse:
    """Réponse complète du pipeline RAG"""
    answer: str
    sources: List[RetrievedChunk]
    query_embedding_time: float
    retrieval_time: float
    generation_time: float
    total_time: float


class DjangoRAGService:
    """
    Service RAG intégré pour Django
    Utilise les modules src/ (LLMHandler, PineconeRetriever)
    """
    
    def __init__(self):
        self.llm_handler = None
        self.retriever = None
        
        # Initialise les services
        self._initialize_services()
    
    def _initialize_services(self):
        """Initialise les services LLM et Retriever"""
        # Récupère les configurations
        hf_token = getattr(settings, 'HF_TOKEN', None)
        pinecone_key = getattr(settings, 'PINECONE_API_KEY', None)
        pinecone_index = getattr(settings, 'PINECONE_INDEX_NAME', None)

        # Log détaillé pour Railway
        logger.info("=" * 50)
        logger.info("🔍 DIAGNOSTIC DES CLÉS API (Railway/Production)")
        logger.info(f"  - HF_TOKEN: {'✅ Présent' if hf_token else '❌ MANQUANT'}")
        if hf_token and 'hf_' not in hf_token:
             logger.warning("    ⚠️ HF_TOKEN semble mal formaté (devrait commencer par 'hf_')")
             
        logger.info(f"  - PINECONE_API_KEY: {'✅ Présent' if pinecone_key else '❌ MANQUANT'}")
        if pinecone_key and 'pcsk_' not in pinecone_key:
             logger.warning("    ⚠️ PINECONE_API_KEY semble mal formaté (devrait commencer par 'pcsk_')")
             
        logger.info(f"  - PINECONE_INDEX_NAME: {'✅ Présent (' + pinecone_index + ')' if pinecone_index else '❌ MANQUANT'}")
        logger.info("=" * 50)

        if not hf_token or not pinecone_key:
            missing = []
            if not hf_token: missing.append("HF_TOKEN")
            if not pinecone_key: missing.append("PINECONE_API_KEY")
            logger.error(f"❌ Configuration RAG incomplète. Clés manquantes : {', '.join(missing)}")
            return

        try:
            # Import des modules src/
            from src.generation.llm_handler import LLMHandler
            from src.retrieval.retriever import PineconeRetriever
            
            # Initialise le LLM Handler
            logger.info("Initialisation du LLM Handler...")
            self.llm_handler = LLMHandler(
                model_name=getattr(settings, 'LLM_MODEL', 'meta-llama/Llama-3.1-8B-Instruct'),
                api_key=hf_token,
                temperature=getattr(settings, 'LLM_TEMPERATURE', 0.7),
                max_tokens=getattr(settings, 'LLM_MAX_TOKENS', 1000),
                provider=None
            )
            logger.info("✅ LLM Handler initialisé")
            
            # Initialise le Pinecone Retriever
            logger.info("Initialisation du Pinecone Retriever...")
            self.retriever = PineconeRetriever(
                api_key=pinecone_key,
                index_name=getattr(settings, 'PINECONE_INDEX_NAME', 'noxa-rag'),
                embed_model=getattr(settings, 'PINECONE_EMBED_MODEL', 'multilingual-e5-large'),
                rerank_model=getattr(settings, 'PINECONE_RERANK_MODEL', 'bge-reranker-v2-m3'),
                namespace=getattr(settings, 'PINECONE_NAMESPACE', '__default__')
            )
            logger.info("✅ Pinecone Retriever initialisé")
            
        except Exception as e:
            logger.error(f"❌ Erreur initialisation services RAG: {e}")
            self.llm_handler = None
            self.retriever = None
    
    def process_query(
        self,
        query: str,
        topic_id: Optional[int] = None,
        topic_name: Optional[str] = None,
        conversation_history: List[Dict] = None,
        top_k: int = 5
    ) -> RAGResponse:
        """
        Traite une requête utilisateur avec le pipeline RAG
        """
        import time
        total_start = time.time()
        
        if self.llm_handler and self.retriever:
            return self._process_query_production(
                query, topic_id, topic_name, conversation_history, top_k, total_start
            )
        else:
            # Fallback neutre si les services ne sont pas initialisés
            return RAGResponse(
                answer="Désolé, je ne peux pas traiter votre demande pour le moment car le système RAG n'est pas entièrement configuré (clés API manquantes).",
                sources=[],
                query_embedding_time=0.0,
                retrieval_time=0.0,
                generation_time=0.0,
                total_time=(time.time() - total_start) * 1000
            )
    
    def _process_query_production(
        self,
        query: str,
        topic_id: Optional[int],
        topic_name: Optional[str],
        conversation_history: List[Dict],
        top_k: int,
        total_start: float
    ) -> RAGResponse:
        """Traite la requête en mode production avec LLM et Pinecone"""
        import time
        
        logger.info(f"🔍 Traitement requête PRODUCTION: {query[:100]}...")
        
        # 1. Récupération des documents avec Pinecone
        retrieval_start = time.time()
        try:
            enriched_chunks = self.retriever.retrieve(
                query=query,
                top_k=top_k,
                rerank=True
            )
            retrieval_time = (time.time() - retrieval_start) * 1000
            logger.info(f"✅ {len(enriched_chunks)} chunks récupérés en {retrieval_time:.2f}ms")
        except Exception as e:
            logger.error(f"❌ Erreur récupération: {e}")
            enriched_chunks = []
            retrieval_time = (time.time() - retrieval_start) * 1000
        
        # Convertit les EnrichedChunk en format dict pour le LLM
        retrieved_chunks = []
        for chunk in enriched_chunks:
            chunk_dict = chunk.to_dict()
            retrieved_chunks.append({
                'id': chunk_dict['chunk_id'],
                'score': chunk_dict['rerank_score'] or chunk_dict['score'],
                'text': chunk_dict['text'],
                'metadata': {
                    'document_name': chunk_dict['document_name'],
                    'document_path': chunk_dict['document_name'],
                    'page_numbers': chunk_dict['page_numbers'],
                    'formulas_latex': chunk_dict['formulas_latex'],
                    'image_paths': chunk_dict['image_paths'],
                    'has_formulas': chunk_dict['has_formulas'],
                    'has_images': chunk_dict['has_images']
                }
            })
        
        # 2. Génération de la réponse avec le LLM
        gen_start = time.time()
        try:
            result = self.llm_handler.generate_response(
                question=query,
                retrieved_chunks=retrieved_chunks,
                use_adaptive_template=True,
                include_sources=True,
                conversation_history=conversation_history,
                topic=topic_name
            )
            answer = result['response']
            gen_time = (time.time() - gen_start) * 1000
            logger.info(f"✅ Réponse générée en {gen_time:.2f}ms")
        except Exception as e:
            logger.error(f"❌ Erreur génération: {e}")
            answer = self._generate_fallback_response(query, enriched_chunks)
            gen_time = (time.time() - gen_start) * 1000
        
        # 3. Convertit en format Django (RetrievedChunk)
        sources = []
        for chunk in enriched_chunks[:top_k]:
            chunk_dict = chunk.to_dict()
            sources.append(RetrievedChunk(
                publication_id=0,  # Non utilisé avec Pinecone
                publication_title=chunk_dict['document_name'],
                chunk_index=0,
                content=chunk_dict['text'][:500],
                page_number=chunk_dict['page_numbers'],
                relevance_score=chunk_dict['rerank_score'] or chunk_dict['score'],
                metadata=chunk_dict
            ))
        
        total_time = (time.time() - total_start) * 1000
        
        return RAGResponse(
            answer=answer,
            sources=sources,
            query_embedding_time=0.0,  # Géré par Pinecone
            retrieval_time=retrieval_time,
            generation_time=gen_time,
            total_time=total_time
        )
    
    
    def _generate_fallback_response(self, query: str, chunks: List) -> str:
        """Génère une réponse de fallback si le LLM échoue"""
        if not chunks:
            return "Je n'ai pas trouvé de documents pertinents pour répondre à votre question."
        
        response = f"Concernant votre question : '{query}'\n\n"
        response += f"J'ai trouvé {len(chunks)} documents pertinents :\n\n"
        
        for i, chunk in enumerate(chunks[:3], 1):
            chunk_dict = chunk.to_dict()
            response += f"**{i}. {chunk_dict['document_name']}**"
            if chunk_dict['page_numbers']:
                response += f" (page {chunk_dict['page_numbers']})"
            response += f"\n> {chunk_dict['text'][:200]}...\n\n"
        
        return response
    
    def get_suggested_questions(self, topic_id: Optional[int] = None) -> List[str]:
        """Retourne des suggestions de questions"""
        suggestions = [
            "Quels sont les mémoires disponibles sur ce sujet ?",
            "Peux-tu me résumer les principales conclusions ?",
            "Quelles méthodologies ont été utilisées ?",
            "Y a-t-il des recommandations pour des travaux futurs ?",
            "Quelles sont les références bibliographiques importantes ?"
        ]
        
        if topic_id:
            from base.models import Topic
            try:
                topic = Topic.objects.get(id=topic_id)
                suggestions.insert(0, f"Quels mémoires traitent de {topic.name} ?")
            except Topic.DoesNotExist:
                pass
        
        return suggestions


# Instance singleton
_django_rag_service = None

def get_django_rag_service() -> DjangoRAGService:
    """Retourne l'instance singleton du service RAG Django"""
    global _django_rag_service
    if _django_rag_service is None:
        _django_rag_service = DjangoRAGService()
    return _django_rag_service
