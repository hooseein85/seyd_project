from groq import Groq

def get_active_models():
    # کلید API شما
    client = Groq(api_key="")
    
    try:
        print("🔄 Fetching available models from Groq...")
        models = client.models.list()
        
        print("\n✅ Active Models you have access to:")
        print("-" * 40)
        for m in models.data:
            print(f"👉 {m.id}")
        print("-" * 40)
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    get_active_models()