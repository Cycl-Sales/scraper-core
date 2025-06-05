# -*- coding: utf-8 -*-
{
    'name': 'Web Scraper',
    'version': '18.0.1.0',
    'category': 'Tools',
    'summary': 'Web Scraper for Zillow',
    'description': """
        Web Scraper for Zillow
    """,
    'author': 'CyclSales',
    'website': 'https://www.cyclsales.com',
    'depends': ['base', 'web'],
    'data': [
        'security/ir.model.access.csv',
        'views/zillow_property_views.xml',
        'views/res_users_view.xml',
        'views/market_size_location_views.xml',
        'views/fetch_us_zipcode_wizard_views.xml',
        'views/upload_zipcode_reference_wizard_views.xml',
        'views/res_config_settings_views.xml',
        'views/views.xml',
        'views/templates.xml',
        'views/ghl_templates.xml',
        'views/ghl_location_views.xml',
        'data/ghl_cron.xml',
    ],
    # 'assets': {
    #     'web.assets_backend': [
    #         'web_scraper/static/src/js/zillow_property.js',
    #         'web_scraper/static/src/css/zillow_property.css',
    #     ],
    # },
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
