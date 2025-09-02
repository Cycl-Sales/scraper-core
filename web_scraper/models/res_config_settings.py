from odoo import models, fields, api

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    rapidapi_host = fields.Char(
        string='RapidAPI Host',
        config_parameter='web_scraper.rapidapi_host',
        help='The x-rapidapi-host value for API requests'
    )
    rapidapi_key = fields.Char(
        string='RapidAPI Key',
        config_parameter='web_scraper.rapidapi_key',
        help='The x-rapidapi-key value for API authentication'
    )
    openai_api_key = fields.Char(
        string='OpenAI API Key',
        config_parameter='web_scraper.openai_api_key',
        help='The OpenAI API key for vision analysis.'
    )

    # GHL Installed Locations Sync Status Fields
    ghl_locations_sync_status = fields.Char(string="GHL Locations Sync Status")
    ghl_locations_sync_started = fields.Datetime(string="GHL Locations Sync Started")
    ghl_locations_sync_completed = fields.Datetime(string="GHL Locations Sync Completed")
    ghl_locations_sync_result = fields.Char(string="GHL Locations Sync Result")
    ghl_locations_sync_error = fields.Text(string="GHL Locations Sync Error")
    ghl_locations_sync_app_id = fields.Char(string="GHL Locations Sync App ID")

    # GHL Contacts Sync Status Fields
    ghl_contacts_sync_status = fields.Char(string="GHL Contacts Sync Status")
    ghl_contacts_sync_started = fields.Datetime(string="GHL Contacts Sync Started")
    ghl_contacts_sync_completed = fields.Datetime(string="GHL Contacts Sync Completed")
    ghl_contacts_sync_result = fields.Char(string="GHL Contacts Sync Result")
    ghl_contacts_sync_error = fields.Text(string="GHL Contacts Sync Error")
    ghl_contacts_sync_location_id = fields.Char(string="GHL Contacts Sync Location ID")

    # GHL API Pagination Settings
    ghl_api_max_pages = fields.Integer(
        string="GHL API Max Pages",
        default=50,
        help="Maximum number of pages to fetch from GHL API (None for unlimited). Set to 0 for unlimited."
    )
    ghl_api_delay_between_requests = fields.Float(
        string="GHL API Delay Between Requests (seconds)",
        default=0.1,
        help="Delay between API requests to avoid rate limiting"
    )

    # GHL API Search Settings
    ghl_enable_api_search = fields.Boolean(
        string="Enable GHL API Search",
        default=True,
        help="Enable searching GoHighLevel API when local results are insufficient"
    )
    ghl_search_threshold = fields.Integer(
        string="GHL Search Threshold",
        default=10,
        help="Minimum number of local results required before skipping GHL API search"
    )
    ghl_search_limit = fields.Integer(
        string="GHL Search Limit",
        default=50,
        help="Maximum number of contacts to fetch from GHL API search"
    )
    ghl_api_timeout = fields.Integer(
        string="GHL API Timeout (seconds)",
        default=10,
        help="Timeout for GHL API requests in seconds"
    )
    final_contact_limit = fields.Integer(
        string="Final Contact Limit",
        default=50,
        help="Maximum number of contacts to return in search results"
    )
    local_search_limit = fields.Integer(
        string="Local Search Limit",
        default=50,
        help="Maximum number of contacts to return from local database search"
    )
    cross_location_limit = fields.Integer(
        string="Cross Location Search Limit",
        default=50,
        help="Maximum number of contacts to return when searching across all locations"
    )
    ghl_auto_create_contacts = fields.Boolean(
        string="Auto-create Contacts from GHL API",
        default=True,
        help="Automatically create new contact records when found via GHL API search"
    ) 