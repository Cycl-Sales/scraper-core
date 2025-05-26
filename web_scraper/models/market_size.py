from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class MarketSize(models.Model):
    _name = 'market.size'
    _description = 'Market Size'

    name = fields.Char(string='Name', required=True)
    capacity = fields.Integer(string='Capacity', required=True)
    price = fields.Float(string='Price', required=True)
    currency_id = fields.Many2one('res.currency', string='Currency', required=True, default=lambda self: self.env.company.currency_id)
    user_ids = fields.One2many('res.users', 'market_size_id', string='Users')

    @api.constrains('user_ids', 'capacity')
    def _check_capacity(self):
        for rec in self:
            if rec.capacity and len(rec.user_ids) > rec.capacity:
                raise ValidationError(_('Cannot assign more users than the market size capacity.')) 