#!/usr/bin/env python3
"""
Comprehensive API Test Suite for XAI Backend
Tests all endpoints and validates response formats match frontend expectations
"""

import requests
import json
import sys
from typing import Dict, Any, List
from datetime import datetime

# API Configuration
BASE_URL = "http://localhost:8000"
HEADERS = {"Content-Type": "application/json"}

def test_health_endpoint():
    """Test /api/health endpoint"""
    print("\n=== Testing /api/health ===")
    try:
        response = requests.get(f"{BASE_URL}/api/health")
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "status" in data, "Missing 'status' field"
        assert "timestamp" in data, "Missing 'timestamp' field"
        assert "version" in data, "Missing 'version' field"
        assert data["status"] == "healthy", f"Expected healthy status, got {data['status']}"
        
        print("✅ Health endpoint test passed")
        return data
        
    except Exception as e:
        print(f"❌ Health endpoint test failed: {e}")
        return None

def test_models_endpoint():
    """Test /api/models endpoint"""
    print("\n=== Testing /api/models ===")
    try:
        response = requests.get(f"{BASE_URL}/api/models")
        
        print(f"Status Code: {response.status_code}")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        print(f"Number of models: {len(data)}")
        print(f"Response: {json.dumps(data, indent=2)}")
        
        assert isinstance(data, list), "Expected list of models"
        assert len(data) > 0, "Expected at least one model"
        
        # Validate each model structure
        for i, model in enumerate(data):
            assert "name" in model, f"Model {i} missing 'name' field"
            assert "provider" in model, f"Model {i} missing 'provider' field"
            assert "capabilities" in model, f"Model {i} missing 'capabilities' field"
            assert "description" in model, f"Model {i} missing 'description' field"
            
            # Validate capabilities
            caps = model["capabilities"]
            assert "logprobs" in caps, f"Model {i} capabilities missing 'logprobs'"
            assert "attention_weights" in caps, f"Model {i} capabilities missing 'attention_weights'"
            assert "hidden_states" in caps, f"Model {i} capabilities missing 'hidden_states'"
            assert "gradients" in caps, f"Model {i} capabilities missing 'gradients'"
            
            assert isinstance(caps["logprobs"], bool), f"Model {i} logprobs should be boolean"
            assert isinstance(caps["attention_weights"], bool), f"Model {i} attention_weights should be boolean"
        
        print("✅ Models endpoint test passed")
        return data
        
    except Exception as e:
        print(f"❌ Models endpoint test failed: {e}")
        return None

def test_methods_endpoint():
    """Test /api/methods endpoint"""
    print("\n=== Testing /api/methods ===")
    try:
        response = requests.get(f"{BASE_URL}/api/methods")
        
        print(f"Status Code: {response.status_code}")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        print(f"Number of methods: {len(data)}")
        print(f"Response: {json.dumps(data, indent=2)}")
        
        assert isinstance(data, list), "Expected list of methods"
        assert len(data) > 0, "Expected at least one method"
        
        # Validate each method structure
        for i, method in enumerate(data):
            assert "name" in method, f"Method {i} missing 'name' field"
            assert "description" in method, f"Method {i} missing 'description' field"
            assert "requires_internals" in method, f"Method {i} missing 'requires_internals' field"
            assert "fallback_available" in method, f"Method {i} missing 'fallback_available' field"
            assert "supported_models" in method, f"Method {i} missing 'supported_models' field"
            
            assert isinstance(method["requires_internals"], bool), f"Method {i} requires_internals should be boolean"
            assert isinstance(method["fallback_available"], bool), f"Method {i} fallback_available should be boolean"
            assert isinstance(method["supported_models"], list), f"Method {i} supported_models should be list"
        
        print("✅ Methods endpoint test passed")
        return data
        
    except Exception as e:
        print(f"❌ Methods endpoint test failed: {e}")
        return None

def test_explain_endpoint():
    """Test /api/explain endpoint"""
    print("\n=== Testing /api/explain ===")
    
    test_request = {
        "model": "cerebras/llama3.3-70b",
        "method": "lime",
        "input_text": "Explain the difference between supervised and unsupervised learning.",
        "method_params": {}
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/explain",
            headers=HEADERS,
            json=test_request
        )
        
        print(f"Status Code: {response.status_code}")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        print(f"Response: {json.dumps(data, indent=2)}")
        
        # Validate response structure (matches frontend ExplanationResponse type)
        assert "success" in data, "Missing 'success' field"
        assert "explanation" in data, "Missing 'explanation' field"
        assert "error" in data, "Missing 'error' field"
        assert "execution_time" in data, "Missing 'execution_time' field"
        
        assert isinstance(data["success"], bool), "success should be boolean"
        assert isinstance(data["execution_time"], (int, float)), "execution_time should be number"
        
        if data["success"]:
            explanation = data["explanation"]
            assert explanation is not None, "success=True but explanation is null"
            
            # Validate explanation structure (matches frontend Explanation type)
            assert "model" in explanation, "Missing 'model' in explanation"
            assert "method" in explanation, "Missing 'method' in explanation"
            assert "input_text" in explanation, "Missing 'input_text' in explanation"
            assert "output_text" in explanation, "Missing 'output_text' in explanation"
            assert "tokens" in explanation, "Missing 'tokens' in explanation"
            assert "scores" in explanation, "Missing 'scores' in explanation"
            assert "graphs" in explanation, "Missing 'graphs' in explanation"
            assert "narrative" in explanation, "Missing 'narrative' in explanation"
            assert "metadata" in explanation, "Missing 'metadata' in explanation"
            
            # Validate tokens and scores
            assert isinstance(explanation["tokens"], list), "tokens should be list"
            assert isinstance(explanation["scores"], list), "scores should be list"
            assert len(explanation["tokens"]) == len(explanation["scores"]), "tokens and scores length should match"
            
            # Validate all tokens are strings and scores are numbers
            for i, token in enumerate(explanation["tokens"]):
                assert isinstance(token, str), f"Token {i} should be string"
            
            for i, score in enumerate(explanation["scores"]):
                assert isinstance(score, (int, float)), f"Score {i} should be number"
                assert 0 <= score <= 1, f"Score {i} should be between 0 and 1"
            
            # Validate graphs structure
            graphs = explanation["graphs"]
            assert graphs is not None, "graphs should not be null"
            assert "attention_flow" in graphs, "Missing 'attention_flow' in graphs"
            
            attention_flow = graphs["attention_flow"]
            assert "nodes" in attention_flow, "Missing 'nodes' in attention_flow"
            assert "edges" in attention_flow, "Missing 'edges' in attention_flow"
            
            # Validate narrative
            assert isinstance(explanation["narrative"], str), "narrative should be string"
            assert len(explanation["narrative"]) > 0, "narrative should not be empty"
            
            # Validate metadata
            metadata = explanation["metadata"]
            assert metadata is not None, "metadata should not be null"
            assert "execution_time" in metadata, "Missing 'execution_time' in metadata"
            assert "num_samples" in metadata, "Missing 'num_samples' in metadata"
            assert "method_params" in metadata, "Missing 'method_params' in metadata"
            assert "model_capabilities" in metadata, "Missing 'model_capabilities' in metadata"
        
        print("✅ Explain endpoint test passed")
        return data
        
    except Exception as e:
        print(f"❌ Explain endpoint test failed: {e}")
        return None

def test_validate_endpoint():
    """Test /api/validate endpoint"""
    print("\n=== Testing /api/validate ===")
    
    # Test valid request
    valid_request = {
        "model": "cerebras/llama3.3-70b",
        "method": "lime",
        "input_text": "Test input",
        "method_params": {}
    }
    
    # Test invalid request
    invalid_request = {
        "model": "",
        "method": "invalid_method",
        "input_text": "",
        "method_params": {}
    }
    
    try:
        # Test valid request
        response = requests.post(
            f"{BASE_URL}/api/validate",
            headers=HEADERS,
            json=valid_request
        )
        
        print(f"Valid request - Status Code: {response.status_code}")
        print(f"Valid request - Response: {json.dumps(response.json(), indent=2)}")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "valid" in data, "Missing 'valid' field"
        assert "errors" in data, "Missing 'errors' field"
        assert isinstance(data["valid"], bool), "valid should be boolean"
        assert isinstance(data["errors"], list), "errors should be list"
        
        # Test invalid request (Pydantic validation should return 422)
        response = requests.post(
            f"{BASE_URL}/api/validate",
            headers=HEADERS,
            json=invalid_request
        )
        
        print(f"Invalid request - Status Code: {response.status_code}")
        print(f"Invalid request - Response: {json.dumps(response.json(), indent=2)}")
        
        # Pydantic validation returns 422 for invalid methods
        assert response.status_code == 422, f"Expected 422 for invalid method, got {response.status_code}"
        
        data = response.json()
        assert "detail" in data, "Invalid request should return validation errors in detail field"
        
        print("✅ Validate endpoint test passed")
        return True
        
    except Exception as e:
        print(f"❌ Validate endpoint test failed: {e}")
        return False

def save_test_results(results: Dict[str, Any]):
    """Save test results to file for analysis"""
    timestamp = datetime.now().isoformat().replace(":", "-")
    filename = f"test_results_{timestamp}.json"
    
    try:
        with open(filename, "w") as f:
            json.dump(results, f, indent=2, default=str)
        print(f"\n📁 Test results saved to: {filename}")
    except Exception as e:
        print(f"❌ Failed to save test results: {e}")

def main():
    """Run all API tests"""
    print("🚀 Starting XAI Backend API Test Suite")
    print(f"Testing API at: {BASE_URL}")
    
    results = {
        "timestamp": datetime.now().isoformat(),
        "base_url": BASE_URL,
        "tests": {}
    }
    
    # Run all tests
    results["tests"]["health"] = test_health_endpoint()
    results["tests"]["models"] = test_models_endpoint()
    results["tests"]["methods"] = test_methods_endpoint()
    results["tests"]["explain"] = test_explain_endpoint()
    results["tests"]["validate"] = test_validate_endpoint()
    
    # Save results
    save_test_results(results)
    
    # Summary
    passed_tests = sum(1 for test in results["tests"].values() if test is not None and test is not False)
    total_tests = len(results["tests"])
    
    print(f"\n📊 Test Summary: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("🎉 All tests passed! Backend API is working correctly.")
        return 0
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
