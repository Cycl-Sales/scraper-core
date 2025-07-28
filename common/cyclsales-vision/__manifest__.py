# -*- coding: utf-8 -*-
{
    'name': "Cycl Sales Vision AI Integration",
    'summary': "AI-powered call summary and GHL integration for Cycl Sales",
    'description': """
Cycl Sales Vision AI Integration
===============================

This module provides API endpoints for integrating Go High Level (GHL) with Odoo, enabling AI-powered phone call summarization and workflow automation. It receives call-completed webhooks, processes call data, and can generate summaries using AI (OpenAI integration ready).

Features:
- Receives GHL call-completed webhooks
- API endpoint for GHL workflow custom actions
- AI-powered call summary (stubbed, ready for OpenAI)
- Robust error handling and logging
- Odoo 18-compliant structure
    """,
    'author': "Cycl Sales",
    'website': "https://cyclsales.com",
    'category': 'Tools',
    'version': '1.0',
    'depends': ['base', 'web_scraper', 'cs-dashboard-backend'],
    'data': [
        'security/ir.model.access.csv',
        'data/ai_service_data.xml',
        'views/views.xml',
        'views/templates.xml',
        'views/trigger_views.xml',
        'views/ai_views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}

