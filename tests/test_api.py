#!/usr/bin/env python3
"""
Test API connectivity and credentials
"""
import os
from dotenv import load_dotenv
import openai

load_dotenv()

def test_openai():
    """Test OpenAI API connectivity"""
    api_key = os.getenv("OPENAI_API_KEY")
    base_url = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
    model_name = os.getenv("MODEL_NAME", "gpt-3.5-turbo")
    
    if not api_key:
        print("❌ OPENAI_API_KEY not found in .env")
        return False
    
    print(f"🔑 API Key: {api_key[:20]}...")
    print(f"🌐 Base URL: {base_url}")
    print(f"🤖 Model: {model_name}")
    
    try:
        client = openai.OpenAI(
            api_key=api_key,
            base_url=base_url
        )
        
        # Simple test request
        response = client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": "Hello, just testing the API"}],
            max_tokens=10
        )
        
        print("✅ OpenAI API test successful!")
        print(f"Response: {response.choices[0].message.content}")
        return True
        
    except Exception as e:
        print(f"❌ OpenAI API test failed: {e}")
        return False


if __name__ == "__main__":
    print("🧪 Testing API Connectivity\n")
    
    openai_works = test_openai()
    
    print("\n📊 Summary:")
    print(f"OpenAI: {'✅ Working' if openai_works else '❌ Failed'}")
    
    if openai_works:
        print("\n💡 You can use: python main.py <url>")
    else:
        print("\n❌ Please check your API configuration in .env")
