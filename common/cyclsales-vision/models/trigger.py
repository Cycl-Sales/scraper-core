from odoo import models, fields, api, _
import json

class CyclSalesVisionTrigger(models.Model):
    _name = 'cyclsales.vision.trigger'
    _description = 'CyclSales Vision GHL Workflow Trigger'
    _order = 'create_date desc'

    external_id = fields.Char('External ID', required=True, index=True)
    key = fields.Char('Trigger Key')
    filters = fields.Text('Filters (JSON)')
    event_type = fields.Char('Event Type')
    target_url = fields.Char('Target URL')
    location_id = fields.Many2one('installed.location', string='Location')
    workflow_id = fields.Char('Workflow ID')
    company_id = fields.Char('Company ID')
    meta_key = fields.Char('Meta Key')
    meta_version = fields.Char('Meta Version')

    _sql_constraints = [
        ('external_id_uniq', 'unique(external_id)', 'Trigger external ID must be unique!'),
    ]

    @api.model
    def create_or_update_from_webhook(cls, payload):
        trigger_data = payload.get('triggerData', {})
        meta = payload.get('meta', {})
        extras = payload.get('extras', {})
        external_id = trigger_data.get('id')
        vals = {
            'external_id': external_id,
            'key': trigger_data.get('key'),
            'filters': json.dumps(trigger_data.get('filters', [])),
            'event_type': trigger_data.get('eventType'),
            'target_url': trigger_data.get('targetUrl'),
            'workflow_id': extras.get('workflowId'),
            'company_id': extras.get('companyId'),
            'meta_key': meta.get('key'),
            'meta_version': meta.get('version'),
        }
        # Link to installed.location if possible
        location_id_val = extras.get('locationId')
        if location_id_val:
            location = cls.env['installed.location'].search([('location_id', '=', location_id_val)], limit=1)
            if location:
                vals['location_id'] = location.id
        trigger = cls.sudo().search([('external_id', '=', external_id)], limit=1)
        if trigger:
            trigger.write(vals)
        else:
            trigger = cls.sudo().create(vals)
        return trigger 