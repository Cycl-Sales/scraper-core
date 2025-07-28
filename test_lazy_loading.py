#!/usr/bin/env python3
"""
Test script for lazy loading implementation
"""

import requests
import json

def test_lazy_loading():
    """Test the lazy loading implementation"""
    
    base_url = "http://localhost:8069"
    
    print("Testing Lazy Loading Implementation")
    print("=" * 50)
    
    # Test 1: Check if initial sync only loads limited contacts
    print("\n1. Testing initial contact sync (should only load 300 contacts max)...")
    
    # This would be triggered by the normal sync process
    # We can't directly test this via API, but we can verify the behavior
    
    # Test 2: Test load more contacts endpoint
    print("\n2. Testing load more contacts endpoint...")
    
    # You'll need to replace these with actual values from your system
    test_data = {
        'location_id': 's1R5gJRdM3U3G74s2JoC',  # Replace with actual location ID
        'page': 2,
        'page_size': 100
    }
    
    try:
        response = requests.post(
            f"{base_url}/api/load-more-contacts",
            json=test_data,
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Response: {json.dumps(result, indent=2)}")
            
            if result.get('success'):
                print(f"✓ Load more contacts endpoint working")
                print(f"  - Contacts loaded: {len(result.get('contacts', []))}")
                print(f"  - Page: {result.get('page')}")
                print(f"  - Has more: {result.get('has_more')}")
                print(f"  - Total contacts: {result.get('total_contacts')}")
            else:
                print(f"✗ API Error: {result.get('error')}")
        else:
            print(f"✗ HTTP Error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"✗ Exception: {str(e)}")
    
    # Test 3: Test contact details endpoint
    print("\n3. Testing contact details endpoint...")
    
    test_data = {
        'contact_id': 1  # Replace with actual contact ID
    }
    
    try:
        response = requests.post(
            f"{base_url}/api/contact-details",
            json=test_data,
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Response: {json.dumps(result, indent=2)}")
            
            if result.get('success'):
                contact = result.get('contact', {})
                print(f"✓ Contact details endpoint working")
                print(f"  - Contact: {contact.get('firstName', '')} {contact.get('lastName', '')}")
                print(f"  - Details fetched: {contact.get('details_fetched', False)}")
                print(f"  - Tasks: {len(contact.get('tasks', []))}")
                print(f"  - Conversations: {len(contact.get('conversations', []))}")
                print(f"  - Opportunities: {len(contact.get('opportunities', []))}")
            else:
                print(f"✗ API Error: {result.get('error')}")
        else:
            print(f"✗ HTTP Error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"✗ Exception: {str(e)}")
    
    print("\n" + "=" * 50)
    print("Lazy Loading Test Complete")
    print("\nExpected Behavior:")
    print("1. Initial sync should only load ~300 contacts (3 pages)")
    print("2. Load more contacts should fetch additional contacts from database")
    print("3. Contact details should be fetched on-demand when viewing a contact")

if __name__ == "__main__":
    test_lazy_loading() 