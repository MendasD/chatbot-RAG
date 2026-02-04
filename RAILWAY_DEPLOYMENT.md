# Railway Deployment Configuration

## Environment Variables

Add these variables in Railway dashboard:

### Required for Production Mode
```
HF_TOKEN=your-huggingface-token-here
PINECONE_API_KEY=your-pinecone-api-key-here
PINECONE_INDEX_NAME=your-index-name
```

### Optional (with defaults)
```
PINECONE_EMBED_MODEL=multilingual-e5-large
PINECONE_RERANK_MODEL=bge-reranker-v2-m3
PINECONE_NAMESPACE=__default__
LLM_MODEL=meta-llama/Llama-3.1-8B-Instruct
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=1000
```

### Django Settings (already configured)
```
DEBUG=False
SECRET_KEY=<your-secret-key>
ALLOWED_HOSTS=.railway.app
DATABASE_URL=<automatically-set-by-railway>
```

## Deployment Steps

1. Push to GitHub:
   ```bash
   git add .
   git commit -m "feat: Connect chatbot to LLM with HuggingFace and Pinecone"
   git push origin main
   ```

2. Railway will automatically:
   - Detect the Dockerfile
   - Build the image
   - Install dependencies from requirements.txt
   - Run migrations
   - Start the application

3. Configure environment variables in Railway dashboard

4. Redeploy if needed

## Notes

- The application works in DEMO mode without API keys
- Production mode activates automatically when HF_TOKEN and PINECONE_API_KEY are set
- Check logs for mode confirmation: "🚀 Mode PRODUCTION" or "⚠️ Mode DEMO"
