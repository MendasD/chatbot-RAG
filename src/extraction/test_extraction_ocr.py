from src.extraction.ocr_handler1 import ChandraOCRHandler
from PIL import Image
import os

if __name__ == "__main__":
    # Forcer le téléchargement du modèle dans le disque E
    os.environ["HF_HOME"] = "E:/hf_cache"
    os.environ["TRANSFORMERS_CACHE"] = "E:/hf_cache/transformers"
    os.environ["HF_HUB_CACHE"] = "E:/hf_cache/hub"

    ocr_handler = ChandraOCRHandler(cache_dir="E:/hf_cache/transformers") # Forcer encore le chemin
    print("Modèle chargé")

    # Chargement d'une image exemple
    example_image = Image.open("../../data/images/comparaison_clusters.png")

    # Traitement de l'image
    blocks = ocr_handler.process_image(example_image, 1)

    for block in blocks:
        print(f"Type: {block.type}, Content: {block.content[:50]}...")  # Affiche le type et les premiers 50 caractères du contenu

    
    