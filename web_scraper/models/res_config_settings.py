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