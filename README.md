# NOXA - Plateforme RAG Intelligente pour Publications Académiques

![Python](https://img.shields.io/badge/Python-3.11-blue)
![Django](https://img.shields.io/badge/Django-5.2-green)
![License](https://img.shields.io/badge/License-MIT-yellow)

NOXA est une plateforme web intelligente permettant de gérer, partager et interroger des publications académiques grâce à un système de Retrieval-Augmented Generation (RAG). Les utilisateurs peuvent uploader des documents PDF, les indexer automatiquement, et interagir avec un chatbot IA pour obtenir des réponses précises basées sur le contenu de ces documents.

> 🎓 **Projet Académique** - Développé dans le cadre du cours de Natural Language Processing (NLP)

**🌐 Application en ligne** : [https://noxa-production.up.railway.app](https://noxa-production.up.railway.app)

## 🌟 Fonctionnalités Principales

### 📚 Gestion de Publications
- **Upload de documents PDF** avec métadonnées enrichies
- **Extraction automatique** de titre, auteur, contenu et images
- **Stockage cloud** : PDFs sur AWS S3, images sur Cloudinary
- **Organisation par thèmes et topics** 
- **Système de tags** pour catégorisation fine
- **Collections personnalisées** pour regrouper des publications
- **Profils utilisateurs** avec suivi des publications et followers

### 🤖 Chatbot RAG Intelligent
- **Recherche sémantique** dans la base de documents
- **Réponses contextuelles** générées par LLM (Llama 3.1)
- **Citations précises** avec références aux documents sources
- **Conversation contextuelle** avec historique
- **Filtrage par sources** pour cibler des documents spécifiques

### 🔍 Recherche Avancée
- **Recherche full-text** dans publications et profils
- **Filtres multiples** : thèmes, topics, tags, auteurs
- **Résultats pertinents** classés par score de similarité
- **Prévisualisation** des documents directement dans le navigateur

### 👥 Fonctionnalités Sociales
- **Système de followers/following**
- **Collections publiques/privées**
- **Partage de publications**
- **Notifications** d'activités

## 🛠️ Technologies Utilisées

### Backend
- **Django 5.2** - Framework web Python
- **SQLite** - Base de données (développement)
- **PostgreSQL** - Base de données (production)

### Intelligence Artificielle
- **Pinecone** - Base de données vectorielle pour embeddings
- **Hugging Face Inference API** - Génération de texte avec Llama 3.1
- **multilingual-e5-large** - Modèle d'embeddings multilingue
- **bge-reranker-v2-m3** - Reranking des résultats de recherche

### Stockage Cloud
- **AWS S3** - Stockage des documents PDF uploadés
- **Cloudinary** - Stockage des images extraites des documents PDF

### Traitement de Documents
- **PyMuPDF (fitz)** - Extraction de texte et métadonnées PDF
- **LangChain** - Framework pour applications RAG
- **RecursiveCharacterTextSplitter** - Chunking intelligent des documents

### Frontend
- **HTML/CSS/JavaScript** - Interface utilisateur
- **Bootstrap** - Framework CSS responsive
- **Jazzmin** - Interface d'administration Django améliorée

### Déploiement
- **Railway** - Plateforme de déploiement cloud
- **WhiteNoise** - Serving de fichiers statiques
- **Gunicorn** - Serveur WSGI Python

## 📋 Prérequis

- Python 3.11+
- pip (gestionnaire de packages Python)
- Compte AWS (pour S3 - stockage des PDFs)
- Compte Cloudinary (pour stockage des images extraites)
- Compte Pinecone (gratuit disponible, mais limité)
- Compte Hugging Face (pour accès API)
- Compte Railway (pour déploiement)

## 🚀 Installation

### 1. Cloner le repository

```bash
git clone https://github.com/MendasD/chatbot-RAG.git
cd noxa
```

### 2. Créer un environnement virtuel

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux/Mac
source .venv/bin/activate
```

### 3. Installer les dépendances

```bash
pip install -r requirements.txt
```

### 4. Configuration des variables d'environnement

Créez un fichier `.env` à la racine du projet :

```env
# Django
SECRET_KEY=votre_secret_key_django
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost

# AWS S3
AWS_ACCESS_KEY_ID=votre_aws_access_key
AWS_SECRET_ACCESS_KEY=votre_aws_secret_key
AWS_STORAGE_BUCKET_NAME=votre_bucket_name
AWS_S3_REGION_NAME=eu-north-1

# Pinecone
PINECONE_API_KEY=votre_pinecone_api_key
PINECONE_INDEX_NAME=votre-index-name-pinecone
PINECONE_NAMESPACE=__default__
PINECONE_EMBED_MODEL=multilingual-e5-large
PINECONE_RERANK_MODEL=bge-reranker-v2-m3

# Hugging Face
HF_TOKEN=votre_hugging_face_token

# LLM Configuration
LLM_MODEL=meta-llama/Llama-3.1-8B-Instruct
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=1024

# Cloudinary (pour images extraites des PDFs)
CLOUDINARY_CLOUD_NAME=votre_cloud_name
CLOUDINARY_API_KEY=votre_api_key
CLOUDINARY_API_SECRET=votre_api_secret
```

### 5. Migrations de base de données

```bash
cd noxa_app/base
python manage.py makemigrations
python manage.py migrate
```

### 6. Créer un superutilisateur

```bash
python manage.py createsuperuser
```

### 7. Collecter les fichiers statiques

```bash
python manage.py collectstatic --noinput
```

### 8. Lancer le serveur de développement

```bash
python manage.py runserver
```

L'application sera accessible sur `http://127.0.0.1:8000/`

## 📁 Structure du Projet

```
PROJET_CHATBOT/
├── data/                       # Contient les fichiers générésaprès extraction, et chunking
├── config/                     # Contient certains fichiers de configuration
├── noxa_app/
│   ├── base/                    # Application principale
│   │   ├── templates/           # Les fichiers templates de cette application
│   │   └── templatetags/        # Les fichiers python pour la gestion des tags
│   │   ├── cloud_service.py     # Gestion opération avec le stockage cloud (AWS et Cloudinary)
│   │   ├── cloudinary_config.py    # Configuration du compte cloudinary
│   │   ├── models.py   
│   │   ├── urls.py 
│   │   ├── forms.py  
│   │   └── views.py       
│   │   
│   ├── chat/                           # Application chatbot
│   │   ├── migrations/   
│   │   ├── templates/   
│   │   ├── models.py                   # Modèles Conversation/Message
│   │   ├── views.py                    # Logique chatbot
│   │   ├── urls.py                     # Routes chat
│   │   └── document_processing.py      # Connexion avec la logique du système RAG
│   │
│   ├── noxa/                   # Configuration projet Django
│   │   ├── settings.py         # Paramètres Django
│   │   ├── urls.py             # URLs principales
│   │   └── wsgi.py             # Configuration WSGI
│   │
│   ├── static/                 # Fichiers statiques
│   │   ├── css/
│   │   ├── js/
│   │   └── images/
│   │
│   ├── staticfiles/                
│   │   ├── css/
│   │   ├── js/
│   │   └── images/
│   │
│   ├── Templates/              # Templates HTML
|   |
│   ├── utils/                
│   │   └── decorateurs.py
│   │
│   └── manage.py               # CLI Django
|
├── src/
│   ├── extraction/ 
|   |   ├── document_schemas.py     # Définit le schémas à respecter lors de l'extraction des documents
|   |   ├── pdf_extractor.py        # Extracteur principal des documents
|   |   ├── ocr_handler.py          # Extraction du contenu d'une image
|   |   ├── math_ocr_handler.py     # Extraction des contenus mathématiques
|   |   └── preprocessor.py         # Nettoyage après extraction
|   |
│   ├── chunking/ 
|   |   ├── text_splitter.py           # Création des chunks
|   |   └── chunk_optimizer.py         # Optimisation des chunks
|   |
│   ├── vectorstore/ 
|   |   ├── pinecone_handler.py         # Gestion du flux avec pinecone
|   |
│   ├── retrieval/ 
|   |   ├── retriever.py                # Recherche vectorielle + reranking
|   |   └── test_retriever.py           # Test du retriever
|   |
│   └── generation/ 
|   |   ├── llm_handler.py              # Configuration du llm
|   |   ├── prompt_template.py          # Formats des prompts pour le llm
|   |   └── test_generation.py         
|
├── tests/                      # Contient certains fichiers de test
├── .env                        # Variables d'environnement
├── requirements.txt            # Dépendances Python
├── .gitignore 
├── dockerignore                   
├── docker-compose.yml
├── Dockerfile      
└── README.md                   
```

## 🏗️ Architecture du Système

### Flux de Traitement des Documents

```
┌─────────────────┐
│  Upload PDF     │
│  par utilisateur│
└────────┬────────┘
         │
         ▼
┌─────────────────────────────┐
│  1. Sauvegarde AWS S3       │◄─── Stockage permanent du PDF
│     (fichier complet)       │
└────────┬────────────────────┘
         │
         ▼
┌─────────────────────────────┐
│  2. Extraction PyMuPDF      │
│     • Texte                 │
│     • Métadonnées           │
│     • Images                │
└────────┬────────────────────┘
         │
         ├─────────────────────┐
         │                     │
         ▼                     ▼
┌──────────────────┐  ┌────────────────────┐
│ 3a. Images       │  │ 3b. Texte          │
│ → Cloudinary     │  │ → Chunking         │
└──────────────────┘  └────────┬───────────┘
                               │
                               ▼
                      ┌────────────────────┐
                      │ 4. Embeddings      │
                      │ (multilingual-e5)  │
                      └────────┬───────────┘
                               │
                               ▼
                      ┌────────────────────┐
                      │ 5. Indexation      │
                      │    Pinecone        │
                      └────────────────────┘
```

### Flux de Recherche RAG

```
┌─────────────────┐
│  Question       │
│  utilisateur    │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────┐
│  1. Embedding de la question│
│     (multilingual-e5)       │
└────────┬────────────────────┘
         │
         ▼
┌─────────────────────────────┐
│  2. Recherche vectorielle   │
│     dans Pinecone           │
│     (top 50 résultats)      │
└────────┬────────────────────┘
         │
         ▼
┌─────────────────────────────┐
│  3. Reranking               │
│     (bge-reranker-v2-m3)    │
│     (top 10 pertinents)     │
└────────┬────────────────────┘
         │
         ▼
┌─────────────────────────────┐
│  4. Génération réponse      │
│     LLM (Llama 3.1)         │
│     + Citations sources     │
└────────┬────────────────────┘
         │
         ▼
┌─────────────────────────────┐
│  Réponse avec sources       │
│  affichée à l'utilisateur   │
└─────────────────────────────┘
```

## 🎯 Utilisation

### Créer une Publication

1. Connectez-vous à votre compte
2. Cliquez sur "Créer une publication"
3. Remplissez les informations :
   - Thème de recherche
   - Topic
   - Description et résumé
   - Tags (séparés par des virgules)
   - Auteurs additionnels (usernames séparés par des virgules)
4. Uploadez votre fichier PDF
5. Cliquez sur "Publier"

Le document sera automatiquement :
- **Uploadé sur AWS S3** (stockage du fichier PDF complet)
- **Analysé** pour extraire texte, métadonnées et images
- **Images sauvegardées sur Cloudinary** (si présentes dans le PDF)
- **Découpé en chunks** intelligents pour optimiser la recherche
- **Indexé dans Pinecone** pour la recherche vectorielle sémantique

> ⏱️ **Note** : Le traitement d'un document peut prendre quelques secondes à quelques minutes selon sa taille. Vous serez redirigé vers la page de la publication une fois l'upload terminé.

### Utiliser le Chatbot

1. Accédez à la page Chat
2. (Optionnel) Sélectionnez un topic spécifiques dans le panneau latéral
3. Posez votre question dans le champ de texte
4. Le chatbot :
   - Recherche les passages pertinents dans les documents
   - Génère une réponse contextualisée
   - Cite les sources utilisées avec liens vers les documents

### Rechercher des Publications

1. Utilisez la barre de recherche
2. Appliquez des filtres :
   - Par thème
   - Par topic
   - Par tags
   - Par auteur
3. Consultez les résultats et prévisualisez les PDF

## 🔧 Configuration Avancée

### Optimisation Pinecone

Modifiez les paramètres dans `src/vectorstore/pinecone_handler.py` :

```python
# Nombre de résultats à récupérer
TOP_K = 50

# Nombre de résultats après reranking
RERANK_TOP_K = 10

# Seuil de score de similarité
MIN_SIMILARITY_SCORE = 0.3
```

### Configuration du Chunking

Ajustez les paramètres de découpage dans `src/text_splitter.py` :

```python
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,        # Taille max d'un chunk
    chunk_overlap=200,      # Chevauchement entre chunks
    length_function=len,
    separators=["\n\n", "\n", ". ", " ", ""]
)
```

### Personnalisation du LLM

Modifiez les variables d'environnement :

```env
LLM_MODEL=meta-llama/Llama-3.1-70B-Instruct  # Modèle plus puissant
LLM_TEMPERATURE=0.3  # Plus déterministe (0.0-1.0)
LLM_MAX_TOKENS=2048  # Réponses plus longues
```

## 🚢 Déploiement sur Railway

### 1. Préparer le projet

Assurez-vous d'avoir :
- `requirements.txt` à jour
- `.gitignore` incluant `.env` et `db.sqlite3`
- `Dockerfile` et `docker-compose.yml` configurés

### 2. Créer un projet Railway

```bash
# Installer Railway CLI
npm i -g @railway/cli

# Login
railway login

# Initialiser le projet
railway init

# Déployer
railway up
```

### 3. Configurer les variables d'environnement

Dans le dashboard Railway, ajoutez toutes les variables du fichier `.env`.

### 4. Ajouter les services

- **PostgreSQL** : Base de données production (optionnel, SQLite fonctionne aussi)

### 5. Commandes post-déploiement

```bash
railway run python manage.py migrate
railway run python manage.py createsuperuser
railway run python manage.py collectstatic --noinput
```

## 🔒 Sécurité

### Bonnes Pratiques

- ✅ Ne jamais commiter `.env` ou secrets dans Git
- ✅ Utiliser `DEBUG=False` en production
- ✅ Configurer `ALLOWED_HOSTS` correctement
- ✅ Utiliser HTTPS en production (Railway le fournit)
- ✅ Valider et sanitiser toutes les entrées utilisateur
- ✅ Limiter la taille des fichiers uploadés
- ✅ Configurer CORS si nécessaire

### Configuration HTTPS

```python
# settings.py (production)
SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
```

## 📊 Monitoring et Logs

### Consulter les logs

```bash
# Logs Railway
railway logs

# Logs Django (développement)
tail -f rag.log
```

### Métriques importantes

- Temps de réponse du chatbot
- Taux d'erreur Pinecone
- Utilisation AWS S3
- Temps de traitement PDF

## 🧪 Tests

```bash
# Lancer les tests
python manage.py test

# Tests avec coverage
pip install coverage
coverage run --source='.' manage.py test
coverage report
```

## 🐛 Dépannage

### Erreur "I/O operation on closed file"

**Solution** : Lire le contenu du fichier avant upload S3.

```python
file_content = file.read()
# vous utiliser file_content pour S3 et RAG
```

### Erreur Pinecone "Invalid type for field 'attachment_id'"

**Solution** : Retirer les valeurs `None` des métadonnées.

```python
if value is None:
    continue  # Ne pas ajouter ce champ
```

### PDF non accessible sur Railway

**Solution** : Utiliser S3 ou un service de stockage externe, pas le système de fichiers local.

### Timeout lors du traitement RAG

**Cause** : Les documents volumineux peuvent prendre du temps à traiter.

**Solutions** :
1. **Court terme** : Augmenter le timeout dans les settings
2. **Long terme** : Implémenter un système de tâches asynchrones (Celery + Redis) pour traiter les PDFs en arrière-plan sans bloquer l'utilisateur

## 🤝 Contribution

Les contributions sont les bienvenues ! 

1. Fork le projet
2. Créez une branche (`git checkout -b feature/AmazingFeature`)
3. Committez vos changements (`git commit -m 'Add some AmazingFeature'`)
4. Push vers la branche (`git push origin feature/AmazingFeature`)
5. Ouvrez une Pull Request

### Guidelines

- Suivre PEP 8 pour le code Python
- Ajouter des docstrings aux fonctions
- Écrire des tests pour les nouvelles fonctionnalités
- Mettre à jour la documentation

## 📝 Roadmap

### Améliorations Futures Potentielles

- [ ] **Celery + Redis** pour traitement asynchrone des PDFs
- [ ] **PostgreSQL** full-text search pour recherche hybride
- [ ] **API REST** pour accès programmatique
- [ ] **Export de conversations** en PDF/Markdown
- [ ] **Support multi-langues** (i18n)
- [ ] **Annotations** sur documents PDF
- [ ] **Statistiques** d'utilisation et analytics
- [ ] **Notifications** par email
- [ ] **OAuth** authentication (Google, GitHub)
- [ ] **Mode sombre** pour l'interface

> Ces fonctionnalités sont des suggestions d'amélioration et ne sont pas actuellement implémentées dans le projet.

## 📄 Licence

Ce projet est sous licence MIT. Voir le fichier `LICENSE` pour plus de détails.

## 👨‍💻 Équipe de Développement

Ce projet a été développé dans le cadre du cours de **Natural Language Processing (NLP)** par :

- **MEKONTCHOU NZONDE David Christ** - [GitHub](https://github.com/MendasD)
- **Abdou BA** - [GitHub](https://github.com/ba2664890)
- **Papa Magatte DIOP** - [GitHub](https://github.com/papamagattediop)
- **Fatou Soumaya WADE** - [GitHub](https://github.com/SAKINA005)

### 🎓 Contexte Académique

**Institution** : Ecole nationale de la Statistique et de l'Analyse économique Pierre Ndiaye
**Cours** : Natural Language Processing (NLP)  
**Année Académique** : 2025-2026  
**Encadrant** : Mme Mously DIAW

## 🙏 Remerciements

- [Django](https://www.djangoproject.com/) - Framework web
- [Pinecone](https://www.pinecone.io/) - Base vectorielle
- [Hugging Face](https://huggingface.co/) - Modèles IA
- [Railway](https://railway.app/) - Plateforme de déploiement
- [LangChain](https://www.langchain.com/) - Framework RAG

## 📞 Support et Contact

Pour toute question concernant le projet :
- Ouvrir une [issue](https://github.com/MendasD/chatbot-RAG/issues) sur GitHub

> **Note** : Ce projet est développé dans un cadre académique. Le support est fourni dans la mesure du possible par l'équipe de développement.

---

**NOXA** - Rendre la connaissance académique accessible et interrogeable par IA 🚀
