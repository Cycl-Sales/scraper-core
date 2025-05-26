from odoo import models, fields, api

class USZipCode(models.Model):
    _name = 'us.zipcode'
    _description = 'US ZIP Code'
    _order = 'zip_code'
    
    zip_code = fields.Char(string='ZIP Code', required=True, index=True)
    city = fields.Char(string='City')
    state = fields.Char(string='State')
    county_fips = fields.Char(string='County FIPS')
    population = fields.Integer(string='Population')
    market_location_id = fields.Many2one('market.location', string='Market Location', required=False, ondelete='restrict', index=True)
    name = fields.Char(string='Name', compute='_compute_name', store=True)

    @api.depends('zip_code', 'state')
    def _compute_name(self):
        for rec in self:
            # Try to use state abbreviation if state is in 'CA - California' format
            abbr = rec.state
            if rec.state and ' - ' in rec.state:
                abbr = rec.state.split(' - ')[0]
            rec.name = f"{rec.zip_code or ''} - {abbr or ''}"

    _sql_constraints = [
        ('zip_code_unique', 'unique(zip_code)', 'ZIP Code must be unique!'),
        ('zip_code_market_location_unique', 'unique(zip_code, market_location_id)', 'Each ZIP can only be linked to one market location!'),
    ] 