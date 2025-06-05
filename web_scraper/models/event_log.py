from odoo import models, fields

class WebScraperEventLog(models.Model):
    _name = 'web.scraper.event.log'
    _description = 'Web Scraper Event Log'
    _order = 'timestamp desc'

    name = fields.Char(string='Event Name')
    event_type = fields.Char(string='Event Type')
    payload = fields.Text(string='Payload')
    location_id = fields.Char(string='Location ID')
    company_id = fields.Char(string='Company ID')
    user_id = fields.Char(string='User ID')
    timestamp = fields.Datetime(string='Timestamp') 