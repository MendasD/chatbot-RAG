"""
Templates de prompts pour le système RAG
Optimisés pour citation de sources et qualité des réponses
"""
from typing import List, Dict, Optional


class PromptTemplates:
    """Templates de prompts pour différents cas d'usage"""
    
    # Template principal RAG avec sources
    RAG_WITH_SOURCES = """Tu es un assistant expert qui répond aux questions en te basant UNIQUEMENT sur les documents fournis.

RÈGLES IMPORTANTES:
1. Réponds UNIQUEMENT avec les informations présentes dans les documents ci-dessous
2. Si l'information n'est PAS dans les documents, dis clairement "Je ne trouve pas cette information dans les documents fournis"
3. CITE TOUJOURS tes sources en utilisant le format [Source: nom_du_document, page X]
4. Sois précis et factuel
5. Si plusieurs documents disent des choses différentes, mentionne les deux points de vue

DOCUMENTS DE RÉFÉRENCE:
{context}

QUESTION DE L'UTILISATEUR:
{question}

RÉPONSE (avec citations):"""

    # Template pour synthèse multi-documents
    MULTI_DOC_SYNTHESIS = """Tu es un assistant expert en synthèse documentaire.

Ta tâche est de synthétiser les informations des documents suivants pour répondre à la question.

DOCUMENTS:
{context}

QUESTION:
{question}

Fournis une réponse complète qui:
1. Synthétise les informations de TOUS les documents pertinents
2. Cite chaque source utilisée avec [Source: document, page X]
3. Signale les contradictions éventuelles entre documents
4. Reste factuel et objective

RÉPONSE:"""

    # Template pour questions sans contexte (fallback)
    NO_CONTEXT = """Tu es un assistant utile.

L'utilisateur pose la question suivante, mais aucun document pertinent n'a été trouvé dans la base de connaissances.

QUESTION:
{question}

Réponds de manière générale en précisant que tu n'as pas de documents spécifiques sur ce sujet dans la base de connaissances.

RÉPONSE:"""

    # Template pour vérification de pertinence
    RELEVANCE_CHECK = """Les documents suivants sont-ils pertinents pour répondre à la question?

QUESTION: {question}

DOCUMENTS:
{context}

Réponds uniquement par OUI ou NON."""

    @staticmethod
    def format_context(
        retrieved_chunks: List[Dict],
        include_scores: bool = False,
        max_chunks: int = 5
    ) -> str:
        """
        Formate les chunks récupérés en contexte structuré
        
        Args:
            retrieved_chunks: Liste de chunks avec metadata
            include_scores: Inclure les scores de similarité
            max_chunks: Nombre max de chunks à inclure
            
        Returns:
            Contexte formaté
        """
        context_parts = []
        
        for i, chunk in enumerate(retrieved_chunks[:max_chunks], 1):
            # Supporte dict ou EnrichedChunk
            if hasattr(chunk, "to_dict"):
                chunk_dict = chunk.to_dict()
                metadata = getattr(chunk, "metadata", {}) or {}
                text = chunk_dict.get("text", "")
                score_val = chunk_dict.get("score")
            else:
                chunk_dict = chunk
                metadata = chunk.get('metadata', {})
                text = chunk.get('text', chunk.get('content', ''))
                score_val = chunk.get('score')
            
            # Informations de source
            doc_path = metadata.get('document_path') or metadata.get('document_name') or 'Document inconnu'
            pages = metadata.get('page_numbers', 'Page inconnue')
            doc_url = metadata.get('url')
            
            url_str = f" [Lien: {doc_url}]" if doc_url else ""
            
            # Format pages
            if isinstance(pages, list):
                pages_str = f"pages {', '.join(map(str, pages))}"
            elif isinstance(pages, str):
                pages_str = f"page {pages.replace('[', '').replace(']', '')}"
            else:
                pages_str = f"page {pages}"
            
            # Score optionnel
            score_str = ""
            if include_scores and score_val is not None:
                score_str = f" (pertinence: {score_val:.2f})"
            
            # Texte du chunk déjà déterminé

            # Images et formules (si disponibles)
            # Priorité aux objets images riches avec descriptions
            rich_images = metadata.get('images') or []
            image_ids = metadata.get('image_ids', [])
            image_paths = metadata.get('image_paths', [])
            
            # Reconstruction si metadata['images'] est absent (vieux documents)
            if not rich_images and (image_ids or image_paths):
                for i in range(max(len(image_ids), len(image_paths))):
                    rich_images.append({
                        'image_id': image_ids[i] if i < len(image_ids) else None,
                        'image_path': image_paths[i] if i < len(image_paths) else None,
                        'description': ""
                    })

            formulas = metadata.get('formulas_latex') or []
            
            images_str = ""
            if rich_images:
                img_parts = []
                for img in rich_images[:5]:
                    iid = img.get('image_id') or "N/A"
                    idesc = img.get('description') or img.get('image_description') or ""
                    if idesc:
                        img_parts.append(f"{iid} ({idesc})")
                    else:
                        img_parts.append(iid)
                images_str = "\nImages/Figures: " + " | ".join(img_parts)

            formulas_str = ""
            if formulas:
                if isinstance(formulas, list):
                    formulas_str = "\nFormules: " + " | ".join([str(f) for f in formulas[:3]])
                else:
                    formulas_str = f"\nFormules: {formulas}"
            
            # Construction du bloc (Note: on ne donne pas l'URL brute à l'LLM pour éviter qu'il l'affiche)
            context_parts.append(
                f"--- Document {i} ---\n"
                f"Source: {doc_path}, {pages_str}{score_str}\n"
                f"Contenu:\n{text}\n"
                f"{images_str}"
                f"{formulas_str}\n"
            )
        
        return "\n".join(context_parts)
    
    @staticmethod
    def build_rag_prompt(
        question: str,
        retrieved_chunks: List[Dict],
        template: str = None,
        **kwargs
    ) -> str:
        """
        Construit le prompt RAG complet
        
        Args:
            question: Question de l'utilisateur
            retrieved_chunks: Chunks récupérés
            template: Template personnalisé (optionnel)
            **kwargs: Arguments additionnels pour le template
            
        Returns:
            Prompt complet
        """
        if template is None:
            template = PromptTemplates.RAG_WITH_SOURCES
        
        # Formate le contexte
        context = PromptTemplates.format_context(
            retrieved_chunks,
            include_scores=kwargs.get('include_scores', False),
            max_chunks=kwargs.get('max_chunks', 5)
        )
        
        # Construit le prompt
        prompt = template.format(
            context=context,
            question=question,
            **kwargs
        )
        
        return prompt
    
    @staticmethod
    def build_chat_messages(
        question: str,
        retrieved_chunks: List[Dict],
        system_prompt: Optional[str] = None,
        conversation_history: Optional[List[Dict]] = None,
        topic: Optional[str] = None,
        template: Optional[str] = None
    ) -> List[Dict]:
        """
        Construit les messages pour chat API (format OpenAI)
        
        Args:
            question: Question actuelle
            retrieved_chunks: Chunks récupérés
            system_prompt: Prompt système personnalisé
            conversation_history: Historique de conversation
            
        Returns:
            Liste de messages au format chat
        """
        messages = []
        
        # System prompt
        if system_prompt is None:
            context = PromptTemplates.format_context(retrieved_chunks)
            context_noxa = f"Tu es Noxa AI, l'IA intégrée dans Noxa. Noxa est une application permettant d'aider les étudiants et chercheurs dans la rédaction de leurs documents académiques et scientifiques."
            topic_line = f"Tu es spécialisé en {topic}." if topic else "Tu es un assistant expert."
            system_prompt = f"""{topic_line} {context_noxa} Ton objectif est de fournir une réponse DÉTAILLÉE, SYNTHÉTIQUE et COMPLÈTE en te basant UNIQUEMENT sur les documents fournis.
            
RÈGLES DE RÉPONSE :
1) Fournis une réponse rédigée, structurée et riche en informations. Évite les réponses trop courtes ou les simples listes d'extraits.
2) **CITE TOUJOURS** tes sources au coeur de tes phrases en utilisant le format [Source: Nom_Document, page X].
3) **NE JAMAIS** afficher d'URL brute (http...) dans ta réponse. Le système se charge de générer les liens à partir de tes citations.
4) Si les documents contiennent des informations complémentaires ou contradictoires, mentionne-les pour donner la vision la plus large possible.
5) Toute équation doit être entourée par $$ ... $$ (LaTeX).
6) À la fin de ta réponse, ajoute ces blocs techniques (NE PAS LES TRADUIRE) :
   SOURCES_USED: [nom1.pdf, nom2.pdf]
   IMAGES_USED: [id1, id2]
   FOLLOW_UP_QUESTIONS: [Question 1?; Question 2?; Question 3?]

**ATTENTION :** Les mots SOURCES_USED, IMAGES_USED et FOLLOW_UP_QUESTIONS doivent rester en ANGLAIS.

DOCUMENTS DE RÉFÉRENCE :
{context}
"""
        
        messages.append({
            "role": "system",
            "content": system_prompt
        })
        
        # Historique de conversation
        if conversation_history:
            messages.extend(conversation_history)
        
        # Question actuelle
        messages.append({
            "role": "user",
            "content": question
        })
        
        return messages
    
    @staticmethod
    def extract_sources_from_response(response: str) -> List[str]:
        """
        Extrait les sources citées d'une réponse
        
        Args:
            response: Réponse du LLM
            
        Returns:
            Liste des sources citées
        """
        import re
        
        # Pattern pour [Source: ...]
        pattern = r'\[Source:\s*([^\]]+)\]'
        sources = re.findall(pattern, response)
        
        return list(set(sources))  # Déduplique
    
    @staticmethod
    def extract_metadata_blocks(response: str) -> Dict:
        """
        Extrait et retire les blocs de métadonnées de la réponse.
        Gère les formats : TAG: [item1, item2] ou TAG: item1, item2
        """
        import re
        
        metadata = {
            'sources_used': [],
            'images_used': [],
            'equations_used': [],
            'follow_up_questions': []
        }
        
        clean_response = response
        
        try:
            # 1. Extraction simple ligne par ligne pour plus de stabilité
            lines = clean_response.split('\n')
            final_lines = []
            
            tag_patterns = {
                'sources_used': re.compile(r'^(?:SOURCES_USED|SOURCES_UTILISEES|SOURCES_UTILISEE|SOURCE_USED)\s*:\s*(.*)', re.I),
                'images_used': re.compile(r'^(?:IMAGES_USED|IMAGES_UTILISEES|IMAGES_UTILISEE|IMAGE_USED)\s*:\s*(.*)', re.I),
                'equations_used': re.compile(r'^(?:EQUATIONS_USED|FORMULES_UTILISEES|EQUATION_USED)\s*:\s*(.*)', re.I),
                'follow_up_questions': re.compile(r'^(?:FOLLOW_UP_QUESTIONS|FOLLOW_UP_QUESTION|QUESTIONS_SUGGEREES|SUITE_DE_QUESTION|SUITE_DE_QUESTIONS)\s*:\s*(.*)', re.I)
            }

            for line in lines:
                matched = False
                for key, pattern in tag_patterns.items():
                    match = pattern.match(line.strip())
                    if match:
                        content = match.group(1).strip()
                        # Nettoie les crochets si présents
                        content = content.strip('[] ')
                        # Split les items
                        items = [item.strip() for item in re.split(r'[;,\n]', content) if item.strip()]
                        # Nettoyage supplémentaire des guillemets
                        items = [item.strip('"\' ') for item in items]
                        metadata[key].extend(items)
                        matched = True
                        break
                
                if not matched:
                    # Garde la ligne si ce n'est pas un bloc de métadonnées
                    # On vérifie seulement les tags les plus fréquents pour éviter de tout supprimer
                    if not any(tag in line.upper() for tag in ['SOURCES_USED:', 'IMAGES_USED:', 'FOLLOW_UP_QUESTIONS:']):
                        final_lines.append(line)
            
            clean_response = '\n'.join(final_lines).strip()
            
            # 2. Nettoyage final des phrases de transition
            phrases_a_supprimer = [
                r'^(?i)Voici la réponse.*?:',
                r'^(?i)MÉTADONNÉES.*',
                r'^(?i)BLOC DE FONCTIONS.*'
            ]
            for p in phrases_a_supprimer:
                clean_response = re.sub(p, '', clean_response, flags=re.M).strip()
                
        except Exception as e:
            print(f"⚠️ Erreur lors de l'extraction des métadonnées: {e}")
            # En cas d'erreur, on garde la réponse brute
            clean_response = response

        return {
            'clean_response': clean_response,
            'metadata': metadata
        }
    
    @staticmethod
    def format_response_with_sources(
        response: str,
        retrieved_chunks: List[Dict]
    ) -> Dict:
        """
        Formate la réponse avec métadonnées des sources
        
        Args:
            response: Réponse du LLM
            retrieved_chunks: Chunks utilisés
            
        Returns:
            Dict avec réponse et sources détaillées
        """
        # Parse et nettoie la réponse
        parsed_result = PromptTemplates.extract_metadata_blocks(response)
        clean_response = parsed_result['clean_response']
        metadata = parsed_result['metadata']
        
        # Extrait les sources citées (soit du texte, soit du bloc metadata si présent)
        cited_sources = PromptTemplates.extract_sources_from_response(clean_response)
        if metadata['sources_used']:
            cited_sources.extend(metadata['sources_used'])
        cited_sources = list(set(cited_sources))
        
        # Collecte les infos des sources
        sources_info = []
        for chunk in retrieved_chunks:
            if hasattr(chunk, "to_dict"):
                chunk_dict = chunk.to_dict()
                metadata_chunk = getattr(chunk, "metadata", {}) or {}
                chunk_id = chunk_dict.get("chunk_id", "")
                score_val = chunk_dict.get("score", 0.0)
            else:
                chunk_dict = chunk
                metadata_chunk = chunk.get('metadata', {})
                chunk_id = chunk.get('id', '')
                score_val = chunk.get('score', 0.0)
            
            doc_name = metadata_chunk.get('document_name', '')
            pages = metadata_chunk.get('page_numbers', '')
            
            source_info = {
                'document': doc_name,
                'pages': pages,
                'chunk_id': chunk_id,
                'score': score_val
            }
            
            if source_info not in sources_info:
                sources_info.append(source_info)
        
        return {
            'response': clean_response,  # Texte nettoyé sans métadonnées
            'cited_sources': cited_sources,
            'all_sources': sources_info,
            'num_sources_used': len(retrieved_chunks),
            'extracted_metadata': metadata  # Métadonnées structurées
        }


# Templates prédéfinis pour différents types de questions

QUESTION_TYPE_TEMPLATES = {
    'factual': """Réponds à cette question factuelle en te basant sur les documents:

DOCUMENTS:
{context}

QUESTION: {question}

Réponse courte et précise avec source:""",
    
    'explanation': """Explique le concept suivant en te basant sur les documents:

DOCUMENTS:
{context}

QUESTION: {question}

Explication détaillée avec exemples et sources:""",
    
    'comparison': """Compare les éléments mentionnés en te basant sur les documents:

DOCUMENTS:
{context}

QUESTION: {question}

Comparaison structurée avec sources pour chaque point:""",
    
    'summary': """Fais une synthèse en te basant sur les documents:

DOCUMENTS:
{context}

QUESTION: {question}

Synthèse concise avec points clés et sources:"""
}


def get_template_for_question_type(question: str) -> str:
    """
    Sélectionne le template approprié selon le type de question
    
    Args:
        question: Question de l'utilisateur
        
    Returns:
        Template approprié
    """
    question_lower = question.lower()
    
    if any(word in question_lower for word in ['comparer', 'différence', 'versus', 'vs']):
        return QUESTION_TYPE_TEMPLATES['comparison']
    
    elif any(word in question_lower for word in ['expliquer', 'comment', 'pourquoi', "c'est quoi"]):
        return QUESTION_TYPE_TEMPLATES['explanation']
    
    elif any(word in question_lower for word in ['résumer', 'synthèse', 'résumé', 'principaux points']):
        return QUESTION_TYPE_TEMPLATES['summary']
    
    elif any(word in question_lower for word in ['qui', 'quoi', 'où', 'quand', 'combien']):
        return QUESTION_TYPE_TEMPLATES['factual']
    
    else:
        return PromptTemplates.RAG_WITH_SOURCES
