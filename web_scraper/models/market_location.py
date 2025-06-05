from odoo import models, fields, api


class MarketLocation(models.Model):
    _name = 'market.location'
    _description = 'Market Location'

    city_address = fields.Char(string='City/Address', required=True)
    market_size_id = fields.Many2one('market.size', string='Market Size', required=True)
    postal_code = fields.Char(string='Postal Code')
    user_ids = fields.Many2many('res.users', 'market_location_user_rel', 'market_location_id', 'user_id',
                                string='Users')
    zipcode_ids = fields.One2many('us.zipcode', 'market_location_id', string='ZIP Codes')
    population = fields.Integer(string='Population', compute='_compute_population', store=True)
    name = fields.Char(string='Name', compute='_compute_name', store=True)
    ghl_location_ids = fields.One2many('ghl.location', 'market_location_id', string='GHL Locations')

    @api.depends('city_address', 'market_size_id')
    def _compute_name(self):
        for rec in self:
            # Try to use state abbreviation if state is in 'CA - California' format

            rec.name = f"{rec.city_address or ''} - {rec.market_size_id.name or ''}"

    @api.depends('zipcode_ids.population')
    def _compute_population(self):
        for rec in self:
            rec.population = sum(rec.zipcode_ids.mapped('population'))
