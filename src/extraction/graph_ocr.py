# PLUS UTILISE
from huggingface_hub import hf_hub_download
import re
from PIL import Image
from transformers import NougatProcessor, VisionEncoderDecoderModel
from accelerate import Accelerator
import torch
import os

if __name__ == "__main__":
    # Forcer le téléchargement du modèle dans le disque E
    os.environ["HF_HOME"] = "E:/hf_cache"
    os.environ["TRANSFORMERS_CACHE"] = "E:/hf_cache/transformers"
    os.environ["HF_HUB_CACHE"] = "E:/hf_cache/hub"

    processor = NougatProcessor.from_pretrained("facebook/nougat-base", cache_dir="E:/hf_cache/transformers")
    model = VisionEncoderDecoderModel.from_pretrained("facebook/nougat-base")

    device = Accelerator().device
    model.to(device)
    # prepare PDF image for the model
    #filepath = hf_hub_download(repo_id="hf-internal-testing/fixtures_docvqa", filename="nougat_paper.png", repo_type="dataset")
    filepath = "data/images/comparaison_clusters.png"
    image = Image.open(filepath)
    pixel_values = processor(image, return_tensors="pt").pixel_values

    # generate transcription (here we only generate 30 tokens)
    outputs = model.generate(
        pixel_values.to(device),
        min_length=1,
        max_new_tokens=30,
        bad_words_ids=[[processor.tokenizer.unk_token_id]],
    )

    sequence = processor.batch_decode(outputs, skip_special_tokens=True)[0]
    sequence = processor.post_process_generation(sequence, fix_markdown=False)
    # note: we're using repr here such for the sake of printing the \n characters, feel free to just print the sequence
    print(repr(sequence))
    print(sequence)
    '\n\n# Nougat: Neural Optical Understanding for Academic Documents\n\n Lukas Blecher\n\nCorrespondence to: lblecher@'