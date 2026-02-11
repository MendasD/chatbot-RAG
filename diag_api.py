import os
import sys
from dotenv import load_dotenv

# Add src to path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

load_dotenv()

def test_apis():
    print("="*50)
    print("🔍 DIAGNOSTIC DES APIS NOXA")
    print("="*50)

    # 1. Check Env Vars
    hf_token = os.getenv('HF_TOKEN')
    pc_key = os.getenv('PINECONE_API_KEY')
    pc_index = os.getenv('PINECONE_INDEX_NAME', 'rag-test2')
    
    print(f"\n1. Vérification des variables d'environnement:")
    print(f"   - HF_TOKEN: {'✅' if hf_token else '❌ MANQUANT'}")
    print(f"   - PINECONE_API_KEY: {'✅' if pc_key else '❌ MANQUANT'}")
    print(f"   - PINECONE_INDEX: {pc_index}")

    if not all([hf_token, pc_key]):
        print("\n❌ Arrêt: Variables critiques manquantes.")
        return

    # 2. Test Pinecone Connectivity
    print(f"\n2. Test Pinecone (Client & Index):")
    try:
        from pinecone import Pinecone
        pc = Pinecone(api_key=pc_key)
        index = pc.Index(pc_index)
        stats = index.describe_index_stats()
        print(f"   ✅ Connecté. Total vecteurs: {stats['total_vector_count']}")
    except Exception as e:
        print(f"   ❌ ÉCHEC Pinecone: {str(e)}")

    # 3. Test Pinecone Embedding
    print(f"\n3. Test Pinecone Embedding API:")
    try:
        model = "multilingual-e5-large"
        res = pc.inference.embed(
            model=model,
            inputs=["Ceci est un test"],
            parameters={"input_type": "query"}
        )
        print(f"   ✅ OK. Dimension: {len(res[0].values)}")
    except Exception as e:
        print(f"   ❌ ÉCHEC Embedding: {str(e)}")

    # 4. Test Pinecone Rerank
    print(f"\n4. Test Pinecone Rerank API:")
    try:
        res = pc.inference.rerank(
            model="bge-reranker-v2-m3",
            query="test",
            documents=["Ceci est un doc test"],
            top_n=1
        )
        print(f"   ✅ OK. Score: {res.data[0].score}")
    except Exception as e:
        print(f"   ❌ ÉCHEC Rerank: {str(e)}")

    # 5. Test HuggingFace LLM
    print(f"\n5. Test HuggingFace Inference (LLM):")
    try:
        from huggingface_hub import InferenceClient
        client = InferenceClient(api_key=hf_token)
        model = "meta-llama/Llama-3.1-8B-Instruct"
        res = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": "Dit test"}],
            max_tokens=10
        )
        print(f"   ✅ OK. Réponse: {res.choices[0].message.content.strip()}")
    except Exception as e:
        print(f"   ❌ ÉCHEC LLM: {str(e)}")

    print("\n" + "="*50)
    print("FIN DU DIAGNOSTIC")
    print("="*50)

if __name__ == "__main__":
    test_apis()
