#!/usr/bin/env python3
"""
Simple test script for the /api/explain endpoint
Tests the backend API directly without frontend complexity
"""

import requests
import json
import time

def test_explain_api():
    """Test the /api/explain endpoint with a simple request"""
    
    base_url = "http://localhost:8000"
    
    print("🧪 Testing XAI Backend API")
    print("=" * 40)
    
    # Test 1: Check if backend is running
    print("1. Testing backend connection...")
    try:
        response = requests.get(f"{base_url}/api/models", timeout=5)
        if response.status_code == 200:
            models = response.json()
            print(f"✅ Backend is running! Found {len(models)} models")
            for model in models:
                print(f"   - {model['name']} ({model['provider']})")
        else:
            print(f"❌ Backend connection failed: {response.status_code}")
            return
    except requests.exceptions.RequestException as e:
        print(f"❌ Backend connection failed: {e}")
        return
    
    # Test 2: Test explanation generation
    print("\n2. Testing explanation generation...")
    
    test_request = {
        "model": "qwen/qwen3-32b",
        "method": "lime", 
        "input_text": "The quick brown fox jumps over the lazy dog.",
        "parameters": {}
    }
    
    print(f"   Model: {test_request['model']}")
    print(f"   Method: {test_request['method']}")
    print(f"   Text: {test_request['input_text']}")
    print("   Sending request...")
    
    start_time = time.time()
    
    try:
        response = requests.post(
            f"{base_url}/api/explain",
            json=test_request,
            timeout=30  # 30 second timeout
        )
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"   Response time: {duration:.2f} seconds")
        print(f"   Status code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Explanation generation successful!")
            
            # Display key results
            explanation = result.get("explanation", {})
            
            print(f"\n📊 Results:")
            print(f"   Model: {explanation.get('model', 'N/A')}")
            print(f"   Method: {explanation.get('method', 'N/A')}")
            print(f"   Input text: {explanation.get('input_text', 'N/A')}")
            print(f"   Output text: {explanation.get('output_text', 'N/A')[:100]}...")
            print(f"   Number of tokens: {len(explanation.get('tokens', []))}")
            print(f"   Number of scores: {len(explanation.get('scores', []))}")
            
            # Show first few tokens and scores
            tokens = explanation.get('tokens', [])
            scores = explanation.get('scores', [])
            
            if tokens and scores:
                print(f"\n🎯 Token Importance (first 5):")
                for i, (token, score) in enumerate(zip(tokens[:5], scores[:5])):
                    print(f"   {i+1}. '{token}' -> {score:.4f}")
            
            # Show narrative
            narrative = explanation.get('narrative', '')
            if narrative:
                print(f"\n📝 Analysis: {narrative[:200]}...")
            
            # Show metadata
            metadata = explanation.get('metadata', {})
            if metadata:
                print(f"\n📋 Metadata:")
                for key, value in metadata.items():
                    print(f"   {key}: {value}")
                    
        else:
            print(f"❌ Explanation generation failed!")
            print(f"   Error: {response.text}")
            
    except requests.exceptions.Timeout:
        print("❌ Request timed out after 30 seconds")
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
    
    # Test 3: Test with different methods
    print("\n3. Testing different XAI methods...")
    
    methods = ["lime", "shap", "contrast_cat"]
    
    for method in methods:
        print(f"\n   Testing {method}...")
        
        test_request["method"] = method
        
        try:
            start_time = time.time()
            response = requests.post(
                f"{base_url}/api/explain",
                json=test_request,
                timeout=15
            )
            end_time = time.time()
            
            if response.status_code == 200:
                result = response.json()
                explanation = result.get("explanation", {})
                duration = end_time - start_time
                print(f"   ✅ {method} successful! ({duration:.2f}s)")
                print(f"      Tokens: {len(explanation.get('tokens', []))}")
            else:
                print(f"   ❌ {method} failed: {response.status_code}")
                
        except requests.exceptions.Timeout:
            print(f"   ❌ {method} timed out")
        except Exception as e:
            print(f"   ❌ {method} error: {e}")

if __name__ == "__main__":
    test_explain_api()
