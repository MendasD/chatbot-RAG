"""
Text Splitter pour découper les documents extraits en chunks
Utilise LangChain pour le chunking récursif intelligent
"""
from langchain_text_splitters import RecursiveCharacterTextSplitter
from typing import List, Dict, Optional, Literal
import json
from pathlib import Path

from ..extraction.document_schemas import ExtractedDocument, ContentBlock


class DocumentChunk:
    """Représente un chunk de document avec ses métadonnées"""
    
    def __init__(
        self,
        chunk_id: str,
        content: str,
        document_id: str,
        document_name: str,
        page_numbers: List[int],
        chunk_index: int,
        total_chunks: int,
        metadata: Dict = None
    ):
        self.chunk_id = chunk_id
        self.content = content
        self.document_id = document_id
        self.document_name = document_name
        self.page_numbers = page_numbers
        self.chunk_index = chunk_index
        self.total_chunks = total_chunks
        self.metadata = metadata or {}
        
        # Métadonnées calculées
        self.char_count = len(content)
        self.word_count = len(content.split())
    
    def to_dict(self) -> Dict:
        """Convertit en dictionnaire"""
        return {
            'chunk_id': self.chunk_id,
            'content': self.content,
            'document_id': self.document_id,
            'document_name': self.document_name,
            'page_numbers': self.page_numbers,
            'chunk_index': self.chunk_index,
            'total_chunks': self.total_chunks,
            'char_count': self.char_count,
            'word_count': self.word_count,
            'metadata': self.metadata
        }
    
    def __repr__(self):
        preview = self.content[:50] + "..." if len(self.content) > 50 else self.content
        return f"Chunk({self.chunk_id}, pages={self.page_numbers}, words={self.word_count}, preview='{preview}')"


class SmartTextSplitter:
    """
    Splitter intelligent qui préserve la structure du document
    Utilise LangChain RecursiveCharacterTextSplitter
    """
    
    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        separators: Optional[List[str]] = None,
        keep_separator: bool = True,
        length_function: callable = len,
        strategy: Literal["recursive", "semantic", "mixed"] = "recursive"
    ):
        """
        Initialise le splitter
        
        Args:
            chunk_size: Taille cible des chunks en caractères
            chunk_overlap: Chevauchement entre chunks
            separators: Séparateurs personnalisés (None = défaut LangChain)
            keep_separator: Garder les séparateurs dans les chunks
            length_function: Fonction pour calculer la longueur
            strategy: Stratégie de découpage
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.strategy = strategy
        
        # Séparateurs par défaut (hiérarchiques)
        if separators is None:
            separators = [
                "\n\n\n",  # Triple saut de ligne (sections)
                "\n\n",    # Double saut de ligne (paragraphes)
                "\n",      # Saut de ligne simple
                ". ",      # Fin de phrase
                "! ",
                "? ",
                "; ",
                ", ",
                " ",       # Espace
                ""         # Caractère par caractère (dernier recours)
            ]
        
        # Initialise le splitter LangChain
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=separators,
            keep_separator=keep_separator,
            length_function=length_function
        )
    
    def split_document(self, doc: ExtractedDocument) -> List[DocumentChunk]:
        """
        Découpe un document extrait en chunks
        
        Args:
            doc: Document extrait
            
        Returns:
            Liste de DocumentChunks
        """
        print(f"\n📄 Chunking de: {doc.filename}")
        print(f"   Pages: {len(doc.pages)}, Stratégie: {self.strategy}")
        
        if self.strategy == "recursive":
            chunks = self._split_recursive(doc)
        elif self.strategy == "semantic":
            chunks = self._split_semantic(doc)
        elif self.strategy == "mixed":
            chunks = self._split_mixed(doc)
        else:
            raise ValueError(f"Stratégie inconnue: {self.strategy}")
        
        print(f"   ✓ {len(chunks)} chunks créés")
        return chunks
    
    def _split_recursive(self, doc: ExtractedDocument) -> List[DocumentChunk]:
        """
        Découpage récursif standard avec LangChain
        Respecte la structure du document (pages, blocs)
        """
        chunks = []
        chunk_counter = 0
        
        # Traite chaque page
        for page in doc.pages:
            # Combine les blocs de texte de la page
            page_blocks = [
                block for block in page.content_blocks
                if block.type in ["text", "title", "list"]
            ]
            
            if not page_blocks:
                continue
            
            # Construit le texte de la page avec contexte
            page_text = self._build_page_text(page_blocks, doc.metadata)
            
            # Découpe avec LangChain
            text_chunks = self.splitter.split_text(page_text)
            
            # Crée les DocumentChunks
            for chunk_text in text_chunks:
                chunk_id = f"{doc.document_id}_chunk_{chunk_counter}"
                
                chunk = DocumentChunk(
                    chunk_id=chunk_id,
                    content=chunk_text,
                    document_id=doc.document_id,
                    document_name=doc.filename,
                    page_numbers=[page.page_number],
                    chunk_index=chunk_counter,
                    total_chunks=0,  # Sera mis à jour après
                    metadata={
                        'extraction_method': page.extraction_method,
                        'has_images': page.has_images,
                        'has_tables': page.has_tables,
                        'document_title': doc.metadata.title,
                        'document_author': doc.metadata.author
                    }
                )
                
                chunks.append(chunk)
                chunk_counter += 1
        
        # Met à jour total_chunks
        for chunk in chunks:
            chunk.total_chunks = len(chunks)
        
        return chunks
    
    def _split_semantic(self, doc: ExtractedDocument) -> List[DocumentChunk]:
        """
        Découpage sémantique basé sur la structure
        Regroupe les blocs par sens (titre + contenu associé)
        """
        chunks = []
        chunk_counter = 0
        
        current_section = []
        current_title = None
        current_pages = set()
        
        for page in doc.pages:
            for block in page.content_blocks:
                # Nouveau titre = nouvelle section
                if block.type == "title":
                    # Finalise la section précédente
                    if current_section:
                        chunk_text = "\n\n".join(current_section)
                        
                        # Découpe si trop long
                        if len(chunk_text) > self.chunk_size * 1.5:
                            sub_chunks = self.splitter.split_text(chunk_text)
                        else:
                            sub_chunks = [chunk_text]
                        
                        for sub_chunk in sub_chunks:
                            chunk = self._create_chunk(
                                sub_chunk,
                                doc,
                                list(current_pages),
                                chunk_counter,
                                {'section_title': current_title}
                            )
                            chunks.append(chunk)
                            chunk_counter += 1
                    
                    # Nouvelle section
                    current_section = [block.content]
                    current_title = block.content
                    current_pages = {page.page_number}
                
                elif block.type in ["text", "list"]:
                    current_section.append(block.content)
                    current_pages.add(page.page_number)
        
        # Finalise la dernière section
        if current_section:
            chunk_text = "\n\n".join(current_section)
            if len(chunk_text) > self.chunk_size * 1.5:
                sub_chunks = self.splitter.split_text(chunk_text)
            else:
                sub_chunks = [chunk_text]
            
            for sub_chunk in sub_chunks:
                chunk = self._create_chunk(
                    sub_chunk,
                    doc,
                    list(current_pages),
                    chunk_counter,
                    {'section_title': current_title}
                )
                chunks.append(chunk)
                chunk_counter += 1
        
        # Met à jour total_chunks
        for chunk in chunks:
            chunk.total_chunks = len(chunks)
        
        return chunks
    
    def _split_mixed(self, doc: ExtractedDocument) -> List[DocumentChunk]:
        """
        Stratégie mixte : sémantique d'abord, puis récursif si nécessaire
        Combine le meilleur des deux approches
        """
        # Commence par découpage sémantique
        semantic_chunks = self._split_semantic(doc)
        
        # Redécoupe les chunks trop longs avec récursif
        final_chunks = []
        chunk_counter = 0
        
        for chunk in semantic_chunks:
            if chunk.char_count > self.chunk_size * 1.5:
                # Redécoupe ce chunk
                sub_texts = self.splitter.split_text(chunk.content)
                
                for sub_text in sub_texts:
                    new_chunk = DocumentChunk(
                        chunk_id=f"{doc.document_id}_chunk_{chunk_counter}",
                        content=sub_text,
                        document_id=doc.document_id,
                        document_name=doc.filename,
                        page_numbers=chunk.page_numbers,
                        chunk_index=chunk_counter,
                        total_chunks=0,
                        metadata=chunk.metadata.copy()
                    )
                    final_chunks.append(new_chunk)
                    chunk_counter += 1
            else:
                # Garde le chunk tel quel
                chunk.chunk_index = chunk_counter
                final_chunks.append(chunk)
                chunk_counter += 1
        
        # Met à jour total_chunks
        for chunk in final_chunks:
            chunk.total_chunks = len(final_chunks)
        
        return final_chunks
    
    def _build_page_text(
        self, 
        blocks: List[ContentBlock], 
        metadata
    ) -> str:
        """
        Construit le texte d'une page avec contexte
        Ajoute des marqueurs pour préserver la structure
        """
        text_parts = []
        
        for block in blocks:
            if block.type == "title":
                # Formate les titres avec des marqueurs
                prefix = "#" * (block.level or 1)
                text_parts.append(f"{prefix} {block.content}")
            
            elif block.type == "list":
                # Préserve le format liste
                text_parts.append(block.content)
            
            else:
                # Texte normal
                text_parts.append(block.content)
        
        return "\n\n".join(text_parts)
    
    def _create_chunk(
        self,
        content: str,
        doc: ExtractedDocument,
        page_numbers: List[int],
        index: int,
        extra_metadata: Dict = None
    ) -> DocumentChunk:
        """Helper pour créer un DocumentChunk"""
        metadata = {
            'document_title': doc.metadata.title,
            'document_author': ", ".join(doc.metadata.author) if doc.metadata.author else None,
        }
        if extra_metadata:
            metadata.update(extra_metadata)
        
        return DocumentChunk(
            chunk_id=f"{doc.document_id}_chunk_{index}",
            content=content,
            document_id=doc.document_id,
            document_name=doc.filename,
            page_numbers=page_numbers,
            chunk_index=index,
            total_chunks=0,
            metadata=metadata
        )
    
    def save_chunks(
        self, 
        chunks: List[DocumentChunk], 
        output_path: str
    ):
        """
        Sauvegarde les chunks en JSON
        
        Args:
            chunks: Liste de chunks
            output_path: Chemin de sortie
        """
        output = {
            'total_chunks': len(chunks),
            'chunks': [chunk.to_dict() for chunk in chunks]
        }
        
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
        
        print(f"💾 Chunks sauvegardés: {output_path}")