### **pdf_extractor.py**
# - Coordonne l'extraction complète
# - Utilise PyMuPDF pour extraction de base
# - Détecte si le PDF est scanné ou a une mise en page complexe
# - Délègue à ocr_handler.py si nécessaire
# - Extrait les métadonnées
# - Assemble le document final



"""
Extracteur principal de PDF
Coordonne l'extraction avec PyMuPDF et Chandra OCR
"""
import fitz  # PyMuPDF
from PIL import Image
import io
import time
from pathlib import Path
from typing import List, Optional, Tuple
import json

from src.extraction.document_schemas import (
    ExtractedDocument, 
    PageContent, 
    ContentBlock, 
    BoundingBox,
    DocumentMetadata,
    TOCEntry,
    ExtractionStats
)
from src.extraction.ocr_handler import ChandraOCRHandler
from src.extraction.preprocessor import TextPreprocessor


class PDFExtractor:
    """Extracteur principal pour documents PDF"""
    
    def __init__(self, config: dict = None):
        """
        Initialise l'extracteur
        
        Args:
            config: Configuration d'extraction
        """
        self.config = config or {}
        
        # Initialise les composants
        self.ocr_handler = None
        self.preprocessor = TextPreprocessor(
            self.config.get('preprocessing', {})
        )
        
        # Configuration
        self.extract_images = self.config.get('pymupdf', {}).get('extract_images', True)
        self.use_ocr_for_images = self.config.get('chandra', {}).get('use_for_images', True)
        self.use_ocr_for_scanned = self.config.get('chandra', {}).get('use_for_scanned', True)
        self.output_dir = Path(self.config.get('output_dir', 'data/extracted'))
        self.temp_dir = Path(self.config.get('temp_dir', 'data/temp'))
        
        # Crée les répertoires
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.temp_dir.mkdir(parents=True, exist_ok=True)
    
    def _init_ocr_handler(self):
        """Initialise le handler OCR (lazy loading)"""
        if self.ocr_handler is None:
            chandra_config = self.config.get('chandra', {})
            self.ocr_handler = ChandraOCRHandler(
                model_name=chandra_config.get('model_name', 'datalab-to/chandra'),
                device=chandra_config.get('device', 'cuda')
            )
    
    def extract_pdf(self, pdf_path: str) -> ExtractedDocument:
        """
        Extrait le contenu complet d'un PDF
        
        Args:
            pdf_path: Chemin vers le fichier PDF
            
        Returns:
            ExtractedDocument avec tout le contenu structuré
        """
        start_time = time.time()
        
        print(f"\n📄 Extraction de: {pdf_path}")
        
        # Crée le document
        doc = ExtractedDocument.create_new(pdf_path)
        
        # Ouvre le PDF
        try:
            pdf_doc = fitz.open(pdf_path)
        except Exception as e:
            print(f"❌ Erreur ouverture PDF: {e}")
            doc.stats.errors.append(f"Erreur ouverture: {str(e)}")
            return doc
        
        # Extrait les métadonnées
        doc.metadata = self._extract_metadata(pdf_doc)
        
        # Extrait la table des matières
        doc.table_of_contents = self._extract_toc(pdf_doc)
        
        # Détecte si le PDF est scanné
        is_scanned = self._is_scanned_pdf(pdf_doc)
        if is_scanned:
            print("📸 PDF scanné détecté - utilisation de Chandra")
            if self.use_ocr_for_scanned:
                self._init_ocr_handler()
        
        # Traite chaque page
        print(f"📖 Traitement de {len(pdf_doc)} pages...")
        
        for page_num in range(len(pdf_doc)):
            try:
                page_content = self._extract_page(
                    pdf_doc, 
                    page_num, 
                    is_scanned
                )
                doc.pages.append(page_content)
                
                # Compte les éléments
                doc.stats.total_text_blocks += len([
                    b for b in page_content.content_blocks 
                    if b.type in ["text", "title"]
                ])
                doc.stats.total_images += len([
                    b for b in page_content.content_blocks 
                    if b.type == "image"
                ])
                doc.stats.total_tables += len([
                    b for b in page_content.content_blocks 
                    if b.type == "table"
                ])
                
                if page_content.extraction_method == "chandra":
                    doc.stats.pages_with_ocr += 1
                
                print(f"  ✓ Page {page_num + 1}/{len(pdf_doc)}")
                
            except Exception as e:
                print(f"  ❌ Erreur page {page_num + 1}: {e}")
                doc.stats.errors.append(f"Page {page_num + 1}: {str(e)}")
        
        pdf_doc.close()
        
        # Statistiques finales
        doc.stats.total_pages = len(doc.pages)
        doc.stats.processing_time_seconds = time.time() - start_time
        
        print(f"\n✅ Extraction terminée en {doc.stats.processing_time_seconds:.2f}s")
        print(f"   - Pages: {doc.stats.total_pages}")
        print(f"   - Blocs texte: {doc.stats.total_text_blocks}")
        print(f"   - Images: {doc.stats.total_images}")
        print(f"   - Tableaux: {doc.stats.total_tables}")
        print(f"   - Pages OCR: {doc.stats.pages_with_ocr}")
        
        return doc
    
    def _extract_metadata(self, pdf_doc) -> DocumentMetadata:
        """Extrait les métadonnées du PDF"""
        metadata = pdf_doc.metadata
        
        return DocumentMetadata(
            title=metadata.get('title'),
            author=metadata.get('author'),
            subject=metadata.get('subject'),
            keywords=metadata.get('keywords', '').split(',') if metadata.get('keywords') else [],
            creation_date=metadata.get('creationDate'),
            modification_date=metadata.get('modDate'),
            num_pages=len(pdf_doc),
            producer=metadata.get('producer'),
            language=None  # PyMuPDF ne fournit pas cette info
        )
    
    def _extract_toc(self, pdf_doc) -> List[TOCEntry]:
        """Extrait la table des matières"""
        toc = []
        try:
            toc_data = pdf_doc.get_toc()
            for entry in toc_data:
                level, title, page = entry
                toc.append(TOCEntry(
                    title=title,
                    level=level,
                    page=page
                ))
        except:
            pass
        
        return toc
    
    def _is_scanned_pdf(self, pdf_doc, sample_pages: int = 3) -> bool:
        """
        Détecte si le PDF est scanné
        
        Args:
            pdf_doc: Document PyMuPDF
            sample_pages: Nombre de pages à échantillonner
            
        Returns:
            True si le PDF semble scanné
        """
        # Vérifie les premières pages
        pages_to_check = min(sample_pages, len(pdf_doc))
        text_found = 0
        
        for page_num in range(pages_to_check):
            page = pdf_doc[page_num]
            text = page.get_text().strip()
            if len(text) > 100:  # Au moins 100 caractères de texte
                text_found += 1
        
        # Si moins de la moitié des pages ont du texte, c'est probablement scanné
        return text_found < (pages_to_check / 2)
    
    def _extract_page(
        self, 
        pdf_doc, 
        page_num: int, 
        is_scanned: bool
    ) -> PageContent:
        """
        Extrait le contenu d'une page
        
        Args:
            pdf_doc: Document PyMuPDF
            page_num: Numéro de page
            is_scanned: Si le PDF est scanné
            
        Returns:
            PageContent avec tout le contenu
        """
        page = pdf_doc[page_num]
        blocks = []
        extraction_method = "pymupdf"
        
        # Si scanné et OCR activé, traite la page complète avec Chandra
        if is_scanned and self.use_ocr_for_scanned and self.ocr_handler:
            blocks = self._extract_with_ocr(page, page_num)
            extraction_method = "chandra"
        else:
            # Extraction normale avec PyMuPDF
            blocks = self._extract_with_pymupdf(page, page_num)
        
        # Prétraitement
        blocks = self.preprocessor.preprocess_blocks(blocks)
        
        # Texte brut de la page
        page_text = page.get_text()
        
        return PageContent(
            page_number=page_num + 1,
            content_blocks=blocks,
            page_text=page_text,
            has_images=any(b.type == "image" for b in blocks),
            has_tables=any(b.type == "table" for b in blocks),
            extraction_method=extraction_method
        )
    
    def _extract_with_pymupdf(self, page, page_num: int) -> List[ContentBlock]:
        """Extrait le contenu avec PyMuPDF"""
        blocks = []
        
        # Extrait les blocs de texte avec positions
        text_blocks = page.get_text("dict")["blocks"]
        
        for block_idx, block in enumerate(text_blocks):
            if block["type"] == 0:  # Bloc texte
                bbox = BoundingBox(
                    x0=block["bbox"][0],
                    y0=block["bbox"][1],
                    x1=block["bbox"][2],
                    y1=block["bbox"][3],
                    page=page_num + 1
                )
                
                # Extrait le texte
                text_content = ""
                for line in block.get("lines", []):
                    for span in line.get("spans", []):
                        text_content += span.get("text", "") + " "
                
                text_content = text_content.strip()
                
                if text_content:
                    # Détecte si c'est un titre (taille de police plus grande)
                    is_title = self._is_likely_title(block)
                    
                    blocks.append(ContentBlock(
                        type="title" if is_title else "text",
                        content=text_content,
                        page_number=page_num + 1,
                        bbox=bbox,
                        level=1 if is_title else None
                    ))
            
            elif block["type"] == 1:  # Image
                if self.extract_images:
                    image_block = self._extract_image(
                        page, 
                        block, 
                        page_num,
                        block_idx
                    )
                    if image_block:
                        blocks.append(image_block)
        
        # Extrait les tableaux
        tables = page.find_tables()
        for table_idx, table in enumerate(tables.tables):
            table_text = self._extract_table_text(table)
            blocks.append(ContentBlock(
                type="table",
                content=table_text,
                page_number=page_num + 1
            ))
        
        return blocks
    
    def _extract_with_ocr(self, page, page_num: int) -> List[ContentBlock]:
        """Extrait le contenu avec Chandra OCR"""
        # Convertit la page en image
        pix = page.get_pixmap(dpi=300)
        img_data = pix.tobytes("png")
        image = Image.open(io.BytesIO(img_data))
        
        # Traite avec Chandra
        blocks = self.ocr_handler.process_page_image(image, page_num + 1)
        
        return blocks
    
    def _extract_image(
        self, 
        page, 
        image_block: dict, 
        page_num: int,
        img_idx: int
    ) -> Optional[ContentBlock]:
        """Extrait et traite une image"""
        try:
            bbox = BoundingBox(
                x0=image_block["bbox"][0],
                y0=image_block["bbox"][1],
                x1=image_block["bbox"][2],
                y1=image_block["bbox"][3],
                page=page_num + 1
            )
            
            # Extrait l'image
            xref = image_block["image"]
            base_image = page.parent.extract_image(xref)
            image_data = base_image["image"]
            
            # Convertit en PIL Image
            image = Image.open(io.BytesIO(image_data))
            
            # Sauvegarde l'image temporairement
            image_id = f"img_{page_num}_{img_idx}"
            image_path = self.temp_dir / f"{image_id}.png"
            image.save(image_path)
            
            # Génère une description avec Chandra si activé
            description = ""
            if self.use_ocr_for_images and self.ocr_handler:
                desc_block = self.ocr_handler.process_image_for_description(
                    image, 
                    page_num + 1, 
                    image_id
                )
                description = desc_block.image_description or ""
            
            return ContentBlock(
                type="image",
                content=description,
                page_number=page_num + 1,
                bbox=bbox,
                image_id=image_id,
                image_description=description,
                image_path=str(image_path)
            )
            
        except Exception as e:
            print(f"    ⚠️  Erreur extraction image: {e}")
            return None
    
    def _is_likely_title(self, block: dict) -> bool:
        """Détecte si un bloc est probablement un titre"""
        if not block.get("lines"):
            return False
        
        # Vérifie la taille de police
        first_line = block["lines"][0]
        if first_line.get("spans"):
            font_size = first_line["spans"][0].get("size", 0)
            # Considère comme titre si police > 14pt
            return font_size > 14
        
        return False
    
    def _extract_table_text(self, table) -> str:
        """Extrait le texte d'un tableau"""
        try:
            rows = table.extract()
            table_text = []
            
            for row in rows:
                row_text = " | ".join([str(cell) if cell else "" for cell in row])
                table_text.append(row_text)
            
            return "\n".join(table_text)
        except:
            return ""
    
    def save_document(self, doc: ExtractedDocument) -> str:
        """
        Sauvegarde le document extrait en JSON
        
        Args:
            doc: Document à sauvegarder
            
        Returns:
            Chemin du fichier sauvegardé
        """
        output_file = self.output_dir / f"{doc.document_id}.json"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(doc.to_dict(), f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 Document sauvegardé: {output_file}")
        return str(output_file)