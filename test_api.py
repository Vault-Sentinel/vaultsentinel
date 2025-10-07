#!/usr/bin/env python3
"""
Test script to demonstrate VaultSentinel API endpoints.
"""

import requests
import json
import time

def test_api_endpoints():
    """Test VaultSentinel API endpoints."""
    base_url = "http://localhost:8000"
    
    print("🔍 Testing VaultSentinel API Endpoints")
    print("=" * 50)
    
    # Test health endpoint
    print("1. Testing /healthz endpoint...")
    try:
        response = requests.get(f"{base_url}/healthz")
        if response.status_code == 200:
            health_data = response.json()
            print(f"   ✅ Health check passed: {health_data.get('status', 'unknown')}")
            print(f"   📊 Agent status: {health_data.get('agent_status', {}).get('status', 'unknown')}")
        else:
            print(f"   ❌ Health check failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test findings endpoint
    print("\n2. Testing /findings endpoint...")
    try:
        response = requests.get(f"{base_url}/findings")
        if response.status_code == 200:
            findings_data = response.json()
            findings = findings_data.get('findings', [])
            print(f"   ✅ Found {len(findings)} findings")
            for finding in findings[:3]:  # Show first 3
                print(f"   🔐 {finding.get('kind', 'unknown')}: {finding.get('preview_masked', 'N/A')}")
        else:
            print(f"   ❌ Findings request failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test metrics endpoint
    print("\n3. Testing /metrics endpoint...")
    try:
        response = requests.get(f"{base_url}/metrics")
        if response.status_code == 200:
            metrics_data = response.json()
            print(f"   ✅ Metrics retrieved")
            print(f"   📊 Total findings: {metrics_data.get('total_findings', 0)}")
            print(f"   📈 Counts by status: {metrics_data.get('counts_by_status', {})}")
            print(f"   🔍 Counts by kind: {metrics_data.get('counts_by_kind', {})}")
        else:
            print(f"   ❌ Metrics request failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print(f"\n🌐 Dashboard available at: {base_url}")
    print(f"📊 API Documentation at: {base_url}/docs")

if __name__ == "__main__":
    # Wait a moment for the server to start
    print("⏳ Waiting for server to start...")
    time.sleep(3)
    test_api_endpoints()
