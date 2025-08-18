#!/usr/bin/env python3
"""
Script to check and create AI service records if needed.
Run this script to ensure there's a valid AI service for usage logging.
"""

import os
import sys

# Add Odoo path
odoo_path = '/opt/odoo/odoo18'
sys.path.insert(0, odoo_path)

# Set up Odoo environment
os.environ['ODOO_RC'] = '/opt/odoo/odoo18/conf/cyclsales.conf'

import odoo
from odoo import api, SUPERUSER_ID

def check_ai_service():
    """Check and create AI service if needed"""
    
    print("Checking AI Service Configuration")
    print("=" * 40)
    
    # Initialize Odoo
    odoo.cli.server.main()
    
    # Get registry
    registry = odoo.registry('cyclsales')
    
    with registry.cursor() as cr:
        env = api.Environment(cr, SUPERUSER_ID, {})
        
        # Check if AI service exists
        ai_service = env['cyclsales.vision.ai'].search([('is_active', '=', True)], limit=1)
        
        if ai_service:
            print(f"✓ Found AI service: {ai_service.name} (ID: {ai_service.id})")
            print(f"  - Model type: {ai_service.model_type}")
            print(f"  - Base URL: {ai_service.base_url}")
            print(f"  - Max tokens: {ai_service.max_tokens}")
            print(f"  - Temperature: {ai_service.temperature}")
            print(f"  - Cost per 1K tokens: {ai_service.cost_per_1k_tokens}")
            print(f"  - Is active: {ai_service.is_active}")
        else:
            print("✗ No active AI service found. Creating one...")
            
            # Create default AI service
            ai_service = env['cyclsales.vision.ai'].create({
                'name': 'Default OpenAI GPT-4 Service',
                'model_type': 'gpt-4o',
                'base_url': 'https://api.openai.com/v1',
                'max_tokens': 500,
                'temperature': 0.3,
                'cost_per_1k_tokens': 0.03,
                'is_active': True
            })
            
            print(f"✓ Created AI service: {ai_service.name} (ID: {ai_service.id})")
        
        # Check usage log model
        usage_log_count = env['cyclsales.vision.ai.usage.log'].search_count([])
        print(f"\nUsage Log Records: {usage_log_count}")
        
        # Check installed locations
        location_count = env['installed.location'].search_count([])
        print(f"Installed Locations: {location_count}")
        
        if location_count > 0:
            locations = env['installed.location'].search([], limit=5)
            print("Sample locations:")
            for loc in locations:
                print(f"  - {loc.name} (ID: {loc.id})")
        
        cr.commit()
        
        print("\n" + "=" * 40)
        print("AI Service Check Complete")
        
        if ai_service:
            print("✓ AI service is properly configured")
            print("✓ Usage logging should work now")
        else:
            print("✗ Failed to create AI service")

if __name__ == "__main__":
    check_ai_service()
