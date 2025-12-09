#!/usr/bin/env python3
"""
Debug single method to see detailed error
"""

import requests
import json

def test_single_method():
    """Test one method to see detailed error"""
    
    base_url = "http://localhost:8000"
    
    print("🔍 Debugging Single Method...")
    
    test_request = {
        "model": "qwen/qwen3-32b",
        "method": "lime", 
        "input_text": "The quick brown fox jumps over the lazy dog.",
        "parameters": {}
    }
    
    try:
        response = requests.post(f"{base_url}/api/explain", json=test_request, timeout=30)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Success!")
            print(f"Graph nodes: {len(result['explanation']['graphs']['attention_flow']['nodes'])}")
            print(f"Graph edges: {len(result['explanation']['graphs']['attention_flow']['edges'])}")
        else:
            print(f"❌ Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")

if __name__ == "__main__":
    test_single_method()
