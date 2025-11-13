#!/usr/bin/env python3
"""
API Testing & Usage Examples for Ingredient Matcher
Run this file to test the FastAPI service.
"""

import requests
import json
import time
from typing import List, Dict

# Configuration
BASE_URL = "http://localhost:8000"
EXAMPLES = [
    "TOMATOES 1kg pack",
    "onion red 500g",
    "gralic peeled 100 g",
    "milk full cream 1 L",
    "extra virgin olive oil 500ml",
    "jeera seeds 50 g",
    "white sugar 2kg",
    "plain flour 1kg",
    "butter unslt 250 g",
    "rice long grain 5 kg",
    # Edge cases
    "unknown ingredient xyz",
    "1kg pack",  # Only size info
    "",  # Empty (will error)
]


def test_health() -> bool:
    """Test /health endpoint."""
    print("\n[TEST] Health Check")
    print("-" * 60)
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_root() -> bool:
    """Test / endpoint."""
    print("\n[TEST] Root Endpoint")
    print("-" * 60)
    try:
        response = requests.get(f"{BASE_URL}/")
        print(f"Status: {response.status_code}")
        data = response.json()
        print(f"Service: {data.get('service')}")
        print(f"Version: {data.get('version')}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_match_endpoint(raw_names: List[str]) -> Dict[str, bool]:
    """Test /match endpoint with multiple examples."""
    print("\n[TEST] Match Endpoint")
    print("-" * 60)
    
    results = {}
    
    for raw_name in raw_names:
        try:
            payload = {"raw_name": raw_name}
            response = requests.post(
                f"{BASE_URL}/match",
                json=payload,
                timeout=5
            )
            
            status_code = response.status_code
            
            # Print result
            if status_code == 200:
                data = response.json()
                ingredient_id = data.get("ingredient_id")
                confidence = data.get("confidence")
                
                # Determine status
                if confidence >= 0.8:
                    status_icon = "✓"
                elif confidence >= 0.6:
                    status_icon = "~"
                else:
                    status_icon = "✗"
                
                print(f"{status_icon} '{raw_name[:40]:<40}' → ID:{ingredient_id} (conf:{confidence:.4f})")
                results[raw_name] = True
                
            elif status_code == 400:
                print(f"✗ '{raw_name[:40]:<40}' → 400 Bad Request (empty/missing)")
                results[raw_name] = True  # Expected error
                
            elif status_code == 422:
                print(f"✗ '{raw_name[:40]:<40}' → 422 Validation Error")
                results[raw_name] = True  # Expected validation error
                
            else:
                print(f"✗ '{raw_name[:40]:<40}' → {status_code} {response.reason}")
                results[raw_name] = False
                
        except requests.exceptions.ConnectionError:
            print(f"❌ Connection error. Is the server running on {BASE_URL}?")
            return {"connection_error": False}
        except Exception as e:
            print(f"❌ Error for '{raw_name}': {e}")
            results[raw_name] = False
    
    return results


def test_batch_matching(raw_names: List[str]) -> Dict:
    """Test batch matching (sequential /match calls)."""
    print("\n[TEST] Batch Matching")
    print("-" * 60)
    
    matches = []
    
    for raw_name in raw_names:
        try:
            response = requests.post(
                f"{BASE_URL}/match",
                json={"raw_name": raw_name},
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                matches.append({
                    "raw_name": raw_name,
                    "ingredient_id": data.get("ingredient_id"),
                    "confidence": data.get("confidence")
                })
        except Exception as e:
            print(f"Error matching '{raw_name}': {e}")
    
    print(f"Successfully matched {len(matches)}/{len(raw_names)} items\n")
    
    # Print summary
    if matches:
        confidences = [m["confidence"] for m in matches]
        print(f"Confidence stats:")
        print(f"  Min: {min(confidences):.4f}")
        print(f"  Max: {max(confidences):.4f}")
        print(f"  Avg: {sum(confidences)/len(confidences):.4f}")
        
        high_conf = len([m for m in matches if m["confidence"] >= 0.6])
        print(f"\nHigh-confidence matches (≥0.6): {high_conf}/{len(matches)}")
    
    return {"total_matched": len(matches), "total": len(raw_names), "matches": matches}


def test_error_handling() -> bool:
    """Test error handling."""
    print("\n[TEST] Error Handling")
    print("-" * 60)
    
    all_passed = True
    
    # Test 1: Missing field
    print("1. Missing 'raw_name' field:")
    try:
        response = requests.post(f"{BASE_URL}/match", json={})
        print(f"   Status: {response.status_code}")
        assert response.status_code == 422, "Expected 422 Unprocessable Entity"
        print("   ✓ Correctly returned 422 Validation Error")
    except Exception as e:
        print(f"   ✗ Error: {e}")
        all_passed = False
    
    # Test 2: Empty string
    print("\n2. Empty 'raw_name':")
    try:
        response = requests.post(f"{BASE_URL}/match", json={"raw_name": ""})
        print(f"   Status: {response.status_code}")
        assert response.status_code == 400, "Expected 400 Bad Request"
        print("   ✓ Correctly returned 400 Bad Request")
    except Exception as e:
        print(f"   ✗ Error: {e}")
        all_passed = False
    
    # Test 3: Whitespace only
    print("\n3. Whitespace-only 'raw_name':")
    try:
        response = requests.post(f"{BASE_URL}/match", json={"raw_name": "   "})
        print(f"   Status: {response.status_code}")
        assert response.status_code == 400, "Expected 400 Bad Request"
        print("   ✓ Correctly returned 400 Bad Request")
    except Exception as e:
        print(f"   ✗ Error: {e}")
        all_passed = False
    
    # Test 4: Very long string
    print("\n4. Very long 'raw_name':")
    try:
        long_name = "a" * 10000
        response = requests.post(f"{BASE_URL}/match", json={"raw_name": long_name})
        print(f"   Status: {response.status_code}")
        if response.status_code in [200, 400]:
            print(f"   ✓ Handled long input gracefully (status: {response.status_code})")
        else:
            print(f"   ✗ Unexpected status: {response.status_code}")
            all_passed = False
    except Exception as e:
        print(f"   ✗ Error: {e}")
        all_passed = False
    
    return all_passed


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("INGREDIENT MATCHER - API TEST SUITE")
    print("=" * 60)
    print(f"\nTesting endpoint: {BASE_URL}")
    
    # Check if server is running
    print("\n⏳ Connecting to server...")
    time.sleep(0.5)
    
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=2)
    except requests.exceptions.ConnectionError:
        print(f"\n❌ Cannot connect to {BASE_URL}")
        print("Please start the server first:")
        print("  python app.py")
        print("\nOr with Docker:")
        print("  docker build -t ingredient-matcher:latest .")
        print("  docker run -p 8000:8000 ingredient-matcher:latest")
        return
    
    print("✓ Connected!\n")
    
    # Run tests
    results = {}
    
    results["health"] = test_health()
    results["root"] = test_root()
    
    # Test match endpoint with examples
    test_examples = [ex for ex in EXAMPLES if ex]  # Skip empty string for now
    match_results = test_match_endpoint(test_examples)
    results["match"] = all(match_results.values())
    
    # Test batch
    batch_results = test_batch_matching([ex for ex in EXAMPLES[:10] if ex])
    results["batch"] = batch_results["total_matched"] > 0
    
    # Test error handling
    results["error_handling"] = test_error_handling()
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    for test_name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{test_name:<20} {status}")
    
    total_passed = sum(results.values())
    total_tests = len(results)
    
    print(f"\nTotal: {total_passed}/{total_tests} tests passed")
    
    if total_passed == total_tests:
        print("\n🎉 All tests passed! API is ready for use.")
    else:
        print("\n⚠️  Some tests failed. Check configuration and try again.")
    
    print("\n" + "=" * 60 + "\n")


# Quick API usage examples (as docstring)
"""
QUICK API USAGE EXAMPLES
========================

### Using curl

# Match single item
curl -X POST http://localhost:8000/match \
  -H "Content-Type: application/json" \
  -d '{"raw_name": "tomato 1kg"}'

# Response
{
  "ingredient_id": 1,
  "confidence": 0.98
}

# Health check
curl http://localhost:8000/health

# Service info
curl http://localhost:8000/


### Using Python requests

import requests

# Single match
response = requests.post(
    "http://localhost:8000/match",
    json={"raw_name": "onion red 500g"}
)
print(response.json())
# Output: {'ingredient_id': 2, 'confidence': 0.92}

# Batch matching
supplier_items = [
    "TOMATOES 1kg pack",
    "onion red 500g",
    "gralic peeled 100 g",
]

for item in supplier_items:
    response = requests.post(
        "http://localhost:8000/match",
        json={"raw_name": item}
    )
    data = response.json()
    print(f"{item} → {data['ingredient_id']} (confidence: {data['confidence']})")


### Using httpx (async)

import httpx

async def test_api():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/match",
            json={"raw_name": "butter unslt 250g"}
        )
        print(response.json())

# Run: asyncio.run(test_api())
"""


if __name__ == "__main__":
    main()
