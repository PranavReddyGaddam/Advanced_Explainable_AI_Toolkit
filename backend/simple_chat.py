#!/usr/bin/env python3
"""
Simple Chat Script for Qwen3 32B Model
Test your OpenRouter API with interactive conversation
"""

import os
import asyncio
import aiohttp
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class SimpleChat:
    def __init__(self):
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        self.model_id = "qwen/qwen3-32b"
        self.base_url = "https://openrouter.ai/api/v1"
        
        if not self.api_key:
            print("❌ OPENROUTER_API_KEY not found in .env file")
            return
        
        print(f"🤖 Chatting with {self.model_id}")
        print("Type 'quit' to exit\n")
    
    async def chat(self, message):
        """Send message to Qwen3 32B and get response"""
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "http://localhost:8000",
                "X-Title": "Qwen3 Chat Test"
            }
            
            payload = {
                "model": self.model_id,
                "messages": [{"role": "user", "content": message}],
                "max_tokens": 1000,
                "temperature": 0.7
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{self.base_url}/chat/completions", 
                                       headers=headers, json=payload) as response:
                    
                    if response.status == 200:
                        result = await response.json()
                        return result["choices"][0]["message"]["content"]
                    else:
                        error = await response.text()
                        return f"❌ Error: {response.status} - {error}"
                        
        except Exception as e:
            return f"❌ Connection failed: {e}"
    
    async def test_connection(self):
        """Test if the model is available"""
        print("🔗 Testing connection to Qwen3 32B...")
        response = await self.chat("Hello! Please respond with just 'Connection successful!'")
        
        if "Connection successful!" in response:
            print("✅ Connection successful!\n")
            return True
        else:
            print(f"❌ Connection failed: {response}\n")
            return False

async def main():
    chat = SimpleChat()
    
    if not chat.api_key:
        return
    
    # Test connection first
    if not await chat.test_connection():
        return
    
    # Start interactive chat
    while True:
        try:
            user_input = input("You: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("👋 Goodbye!")
                break
            
            if not user_input:
                continue
            
            print("🤖 Qwen3 is thinking...")
            response = await chat.chat(user_input)
            print(f"🤖 Qwen3: {response}\n")
            
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    # Install aiohttp if needed
    try:
        import aiohttp
    except ImportError:
        print("📦 Installing aiohttp...")
        os.system("pip install aiohttp")
        import aiohttp
    
    asyncio.run(main())
