#!/usr/bin/env python3
"""
Test script specifically for BERT-based methods (INSEQ, GAF)
"""

import requests
import json

def test_bert_methods():
    """Test INSEQ and GAF methods with BERT model"""
    
    base_url = "http://localhost:8000"
    
    print("🧪 Testing BERT-based Methods (INSEQ, GAF)")
    print("=" * 50)
    
    # Test INSEQ method
    print("\n1. Testing INSEQ with BERT...")
    
    test_request = {
        "model": "huggingface/bert-base",
        "method": "inseq", 
        "input_text": "The quick brown fox jumps over the lazy dog.",
        "parameters": {}
    }
    
    try:
        response = requests.post(f"{base_url}/api/explain", json=test_request, timeout=10)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            explanation = result.get("explanation", {})
            print(f"   ✅ INSEQ successful!")
            print(f"   Tokens: {len(explanation.get('tokens', []))}")
            print(f"   Scores: {len(explanation.get('scores', []))}")
            print(f"   Output: {explanation.get('output_text', 'N/A')[:100]}...")
        else:
            print(f"   ❌ INSEQ failed: {response.text}")
            
    except Exception as e:
        print(f"   ❌ INSEQ error: {e}")
    
    # Test GAF method
    print("\n2. Testing GAF with BERT...")
    
    test_request["method"] = "gaf"
    
    try:
        response = requests.post(f"{base_url}/api/explain", json=test_request, timeout=10)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            explanation = result.get("explanation", {})
            print(f"   ✅ GAF successful!")
            print(f"   Tokens: {len(explanation.get('tokens', []))}")
            print(f"   Scores: {len(explanation.get('scores', []))}")
            print(f"   Output: {explanation.get('output_text', 'N/A')[:100]}...")
        else:
            print(f"   ❌ GAF failed: {response.text}")
            
    except Exception as e:
        print(f"   ❌ GAF error: {e}")

if __name__ == "__main__":
    test_bert_methods()
