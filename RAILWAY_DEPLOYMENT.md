# Guide de Déploiement Railway - Configuration Finale

## ✅ Ce qui a été fait

1. **Code pushé sur GitHub** avec toutes les modifications
2. **Variables d'environnement à configurer dans Railway**

## 🔧 Configuration Railway - Étape par Étape

### 1. Accéder aux Variables d'Environnement

1. Allez sur [railway.app](https://railway.app)
2. Sélectionnez votre projet
3. Cliquez sur l'onglet **"Variables"**

### 2. Ajouter les Variables Requises

Ajoutez ces **3 variables** exactement comme indiqué :

#### Variable 1 : HF_TOKEN
```
Nom: HF_TOKEN
Valeur: <votre-token-huggingface>
```

#### Variable 2 : PINECONE_API_KEY
```
Nom: PINECONE_API_KEY
Valeur: <votre-cle-pinecone>
```

#### Variable 3 : PINECONE_INDEX_NAME
```
Nom: PINECONE_INDEX_NAME
Valeur: <votre-nom-index-pinecone>
```

### 3. Redéployer l'Application

Après avoir ajouté les variables :
1. Railway redéploiera **automatiquement**
2. Ou cliquez sur **"Deploy"** manuellement

### 4. Vérifier les Logs

Une fois déployé, vérifiez les logs Railway. Vous devriez voir :

```
======================================================================
🔧 Vérification de la configuration RAG
======================================================================
HF_TOKEN: ✅ Configuré
PINECONE_API_KEY: ✅ Configuré
======================================================================
🚀 Mode PRODUCTION - LLM et Pinecone configurés
Initialisation du LLM Handler...
🤖 Initialisation LLM Handler...
   Modèle: meta-llama/Llama-3.1-8B-Instruct
✅ LLM prêt
✅ LLM Handler initialisé
Initialisation du Pinecone Retriever...
✅ Retriever initialisé:
   Index: llama-text-embed-v2-index
✅ Pinecone Retriever initialisé
```

## ⚠️ Si le Mode Démo Persiste

Si vous voyez toujours le message de mode démo, vérifiez :

### Checklist de Dépannage

- [ ] Les 3 variables sont bien ajoutées dans Railway (pas dans `.env` local)
- [ ] Les noms des variables sont **exactement** : `HF_TOKEN`, `PINECONE_API_KEY`, `PINECONE_INDEX_NAME`
- [ ] Les valeurs ne contiennent pas d'espaces avant/après
- [ ] L'application a été redéployée après l'ajout des variables
- [ ] Les logs montrent "🚀 Mode PRODUCTION" et non "⚠️ Mode DEMO"

### Vérification dans les Logs

Cherchez dans les logs Railway :

**✅ Bon signe** :
```
🔧 Vérification de la configuration RAG
HF_TOKEN: ✅ Configuré
PINECONE_API_KEY: ✅ Configuré
🚀 Mode PRODUCTION
```

**❌ Problème** :
```
HF_TOKEN: ❌ Non configuré ou invalide
   Valeur détectée comme placeholder: your-huggingface-token...
⚠️ Mode DEMO
```

## 🧪 Test Final

Une fois en mode production :

1. **Accédez au chatbot** sur Railway
2. **Posez une question** : "Qu'est-ce que l'intelligence artificielle ?"
3. **Vérifiez la réponse** :
   - ❌ Si vous voyez "**Mode Démonstration Activé**" → Variables non configurées
   - ✅ Si vous recevez une réponse intelligente avec sources → Succès !

## 📞 Support

Si le problème persiste après avoir suivi toutes les étapes :

1. **Copiez les logs Railway** (section avec "🔧 Vérification de la configuration RAG")
2. **Vérifiez que les variables sont bien visibles** dans l'onglet Variables de Railway
3. **Essayez de supprimer et recréer** les variables si nécessaire

---

**Note** : Le fichier `.env` local n'est **pas utilisé** par Railway. Seules les variables d'environnement configurées dans Railway comptent pour le déploiement.
