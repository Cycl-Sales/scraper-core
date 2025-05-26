from odoo import models, fields, api


class ResUsers(models.Model):
    _inherit = 'res.users'

    market_location_id = fields.Many2one('market.location', string='Market Location')
    market_size_id = fields.Many2one('market.size', string='Market Size', compute='_compute_market_size', store=True)

    @api.depends('market_location_id')
    def _compute_market_size(self):
        for user in self:
            user.market_size_id = user.market_location_id.market_size_id if user.market_location_id else False
