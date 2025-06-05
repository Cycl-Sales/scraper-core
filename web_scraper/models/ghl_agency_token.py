from odoo import models, fields

class GHLAgencyToken(models.Model):
    _name = 'ghl.agency.token'
    _description = 'GHL Agency OAuth Token'

    company_id = fields.Char(string='Company ID', required=True, index=True)
    access_token = fields.Char(string='Access Token', required=True)
    refresh_token = fields.Char(string='Refresh Token', required=True)
    token_expiry = fields.Datetime(string='Token Expiry', required=True)
    create_date = fields.Datetime(string='Created On', readonly=True) 