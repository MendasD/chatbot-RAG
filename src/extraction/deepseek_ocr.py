from doctr.io import DocumentFile
from doctr.models import ocr_predictor

# Charger le modèle OCR + layout (CPU)
model = ocr_predictor(
    det_arch="db_resnet50",
    reco_arch="crnn_vgg16_bn",
    pretrained=True
)

# Charger une image
doc = DocumentFile.from_images("data/images/comparaison_clusters.png")

# OCR
result = model(doc)

# Extraire le texte
for page in result.pages:
    for block in page.blocks:
        for line in block.lines:
            text = " ".join(word.value for word in line.words)
            print(text)
