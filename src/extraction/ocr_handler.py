### **ocr_handler.py**
# - Charge le modèle Chandra une seule fois
# - Traite les images extraites du PDF
# - Traite les pages scannées complètes
# - Génère du markdown/HTML/JSON avec mise en page
# - Parse le résultat pour structurer les données

"""
Gestionnaire OCR avec le modèle Chandra
Traite les images et pages scannées pour extraire le contenu structuré
"""
import torch
from transformers import AutoModel, AutoProcessor
from PIL import Image
from typing import List, Optional, Dict
import re
from pathlib import Path
import os

# Chemin absolu quand on veut tester dans un notebook jupyter
# from src.extraction.document_schemas import ContentBlock, BoundingBox
from document_schemas import ContentBlock, BoundingBox

# Ajout de
os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "max_split_size_mb:128"

class ChandraOCRHandler:
    """Handler pour le modèle Chandra OCR"""
    
    def __init__(self, model_name: str = "datalab-to/chandra", device: str = "cuda", cache_dir: Optional[str] = None):
        """
        Initialise le modèle Chandra
        
        Args:
            model_name: Nom du modèle sur HuggingFace
            device: Device à utiliser (cuda/cpu)
        """
        self.device = device if torch.cuda.is_available() else "cpu"
        print(f"Chargement de Chandra sur {self.device}...")
        
        try:
            print("Début du chargement...")
            self.model = AutoModel.from_pretrained(model_name, 
                                                   cache_dir=cache_dir,  
                                                   dtype=torch.float32,
                                                   low_cpu_mem_usage=True,
                                                   trust_remote_code=True
                                                )
                                                #.to(self.device)
            
            print("Modèle chargé...")
            self.processor = AutoProcessor.from_pretrained(model_name, cache_dir=cache_dir)
            self.model.eval()
            print("Chandra chargé avec succès")
        except Exception as e:
            print(f"Erreur lors du chargement de Chandra: {e}")
            raise
    
    def process_image(
        self, 
        image: Image.Image, 
        page_number: int,
        prompt_type: str = "ocr_layout",
        image_id: Optional[str] = None
    ) -> List[ContentBlock]:
        """
        Traite une image avec Chandra
        
        Args:
            image: Image PIL à traiter
            page_number: Numéro de page
            prompt_type: Type de prompt ("ocr_layout", "ocr", "caption")
            image_id: ID de l'image (optionnel)
            
        Returns:
            Liste de ContentBlocks extraits
        """
        try:
            # Prépare le batch
            from chandra.model.schema import BatchInputItem
            from chandra.model.hf import generate_hf
            from chandra.output import parse_markdown
            
            batch = [
                BatchInputItem(
                    image=image,
                    prompt_type=prompt_type
                )
            ]
            
            # Génère le résultat
            with torch.no_grad():
                result = generate_hf(batch, self.model)[0]
            
            # Parse le markdown
            markdown = parse_markdown(result.raw)
            
            # Convertit en ContentBlocks
            blocks = self._parse_markdown_to_blocks(
                markdown, 
                page_number, 
                image_id
            )
            
            return blocks
            
        except Exception as e:
            print(f"Erreur lors du traitement de l'image: {e}")
            return []
    
    def process_page_image(
        self, 
        page_image: Image.Image, 
        page_number: int
    ) -> List[ContentBlock]:
        """
        Traite une page complète (pour PDFs scannés)
        
        Args:
            page_image: Image de la page complète
            page_number: Numéro de page
            
        Returns:
            Liste de ContentBlocks extraits
        """
        return self.process_image(
            page_image, 
            page_number, 
            prompt_type="ocr_layout"
        )
    
    def process_image_for_description(
        self, 
        image: Image.Image, 
        page_number: int,
        image_id: str
    ) -> ContentBlock:
        """
        Génère une description pour une image
        
        Args:
            image: Image PIL
            page_number: Numéro de page
            image_id: ID de l'image
            
        Returns:
            ContentBlock avec description
        """
        blocks = self.process_image(
            image, 
            page_number, 
            prompt_type="caption",
            image_id=image_id
        )
        
        # Combine tous les textes en description
        description = " ".join([b.content for b in blocks if b.type == "text"])
        
        return ContentBlock(
            type="image",
            content=description,
            page_number=page_number,
            image_id=image_id,
            image_description=description
        )
    
    def _parse_markdown_to_blocks(
        self, 
        markdown: str, 
        page_number: int,
        image_id: Optional[str] = None
    ) -> List[ContentBlock]:
        """
        Parse le markdown généré par Chandra en ContentBlocks
        
        Args:
            markdown: Texte markdown
            page_number: Numéro de page
            image_id: ID image si applicable
            
        Returns:
            Liste de ContentBlocks
        """
        blocks = []
        lines = markdown.split('\n')
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            if not line:
                i += 1
                continue
            
            # Détecte les titres
            if line.startswith('#'):
                level = len(line) - len(line.lstrip('#'))
                title = line.lstrip('#').strip()
                blocks.append(ContentBlock(
                    type="title",
                    content=title,
                    page_number=page_number,
                    level=level
                ))
            
            # Détecte les tableaux (markdown tables)
            elif '|' in line:
                table_lines = [line]
                i += 1
                while i < len(lines) and '|' in lines[i]:
                    table_lines.append(lines[i].strip())
                    i += 1
                
                blocks.append(ContentBlock(
                    type="table",
                    content='\n'.join(table_lines),
                    page_number=page_number
                ))
                continue
            
            # Détecte les listes
            elif re.match(r'^[\*\-\+]\s+', line) or re.match(r'^\d+\.\s+', line):
                list_lines = [line]
                i += 1
                while i < len(lines):
                    next_line = lines[i].strip()
                    if re.match(r'^[\*\-\+]\s+', next_line) or re.match(r'^\d+\.\s+', next_line):
                        list_lines.append(next_line)
                        i += 1
                    else:
                        break
                
                blocks.append(ContentBlock(
                    type="list",
                    content='\n'.join(list_lines),
                    page_number=page_number
                ))
                continue
            
            # Détecte le code
            elif line.startswith('```'):
                code_lines = []
                i += 1
                while i < len(lines) and not lines[i].strip().startswith('```'):
                    code_lines.append(lines[i])
                    i += 1
                
                blocks.append(ContentBlock(
                    type="code",
                    content='\n'.join(code_lines),
                    page_number=page_number
                ))
            
            # Texte normal
            else:
                # Accumule les paragraphes
                paragraph_lines = [line]
                i += 1
                while i < len(lines):
                    next_line = lines[i].strip()
                    if (not next_line or 
                        next_line.startswith('#') or 
                        '|' in next_line or
                        re.match(r'^[\*\-\+]\s+', next_line) or
                        next_line.startswith('```')):
                        break
                    paragraph_lines.append(next_line)
                    i += 1
                
                blocks.append(ContentBlock(
                    type="text",
                    content=' '.join(paragraph_lines),
                    page_number=page_number
                ))
                continue
            
            i += 1
        
        return blocks
    
    def batch_process_images(
        self, 
        images: List[tuple], 
        batch_size: int = 4
    ) -> List[List[ContentBlock]]:
        """
        Traite plusieurs images en batch
        
        Args:
            images: Liste de (image, page_number, image_id)
            batch_size: Taille du batch
            
        Returns:
            Liste de listes de ContentBlocks
        """
        all_blocks = []
        
        for i in range(0, len(images), batch_size):
            batch = images[i:i+batch_size]
            
            for image, page_num, img_id in batch:
                blocks = self.process_image(image, page_num, image_id=img_id)
                all_blocks.append(blocks)
        
        return all_blocks