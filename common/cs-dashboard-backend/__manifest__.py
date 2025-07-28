# -*- coding: utf-8 -*-
{
    'name': "Cycl Sales Dashboard Backend",

    'summary': "Backend API and data management for Cycl Sales dashboard",

    'description': """
Cycl Sales Dashboard Backend Module
===================================

This module provides the backend infrastructure for the Cycl Sales dashboard,
including API endpoints, data models, and business logic for managing sales
analytics, customer data, and dashboard functionality.

Features:
- Sales analytics and reporting
- Customer data management
- Dashboard API endpoints
- Data processing and aggregation
- GoHighLevel contact integration
    """,

    'author': "Cycl Sales",
    'website': "https://cyclsales.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Sales',
    'version': '1.0',

    # any module necessary for this one to work correctly
    'depends': ['base', 'web_scraper'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'data/oauth_config_data.xml',
        'data/automation_template_real_estate_investor.xml',
        'data/automation_template_business_acquisition.xml',
        'data/automation_template_real_estate_agent.xml',
        'data/automation_template_coaching_programs.xml',
        'data/automation_template_cleaning_companies.xml',
        'data/automation_template_universal_business.xml',
        'data/automation_template_custom_business.xml',
        'views/views.xml',
        'views/templates.xml',
        'views/automation_template_views.xml',
    ],
}

