from odoo import models, fields

class GHLLocationUserPermissions(models.Model):
    _name = 'ghl.location.user.permissions'
    _description = 'GHL Location User Permissions'

    campaigns_enabled = fields.Boolean()
    campaigns_read_only = fields.Boolean()
    contacts_enabled = fields.Boolean()
    workflows_enabled = fields.Boolean()
    workflows_read_only = fields.Boolean()
    triggers_enabled = fields.Boolean()
    funnels_enabled = fields.Boolean()
    websites_enabled = fields.Boolean()
    opportunities_enabled = fields.Boolean()
    dashboard_stats_enabled = fields.Boolean()
    bulk_requests_enabled = fields.Boolean()
    appointments_enabled = fields.Boolean()
    reviews_enabled = fields.Boolean()
    online_listings_enabled = fields.Boolean()
    phone_call_enabled = fields.Boolean()
    conversations_enabled = fields.Boolean()
    assigned_data_only = fields.Boolean()
    adwords_reporting_enabled = fields.Boolean()
    membership_enabled = fields.Boolean()
    facebook_ads_reporting_enabled = fields.Boolean()
    attributions_reporting_enabled = fields.Boolean()
    settings_enabled = fields.Boolean()
    tags_enabled = fields.Boolean()
    lead_value_enabled = fields.Boolean()
    marketing_enabled = fields.Boolean()
    agent_reporting_enabled = fields.Boolean()
    bot_service = fields.Boolean()
    social_planner = fields.Boolean()
    blogging_enabled = fields.Boolean()
    invoice_enabled = fields.Boolean()
    affiliate_manager_enabled = fields.Boolean()
    content_ai_enabled = fields.Boolean()
    refunds_enabled = fields.Boolean()
    record_payment_enabled = fields.Boolean()
    cancel_subscription_enabled = fields.Boolean()
    payments_enabled = fields.Boolean()
    communities_enabled = fields.Boolean()
    export_payments_enabled = fields.Boolean()

class GHLLocationUserRoles(models.Model):
    _name = 'ghl.location.user.roles'
    _description = 'GHL Location User Roles'

    type = fields.Char()
    role = fields.Char()
    restrict_sub_account = fields.Boolean()
    location_ids = fields.Many2many('installed.location', string='Locations')

class GHLLocationUserLCPhone(models.Model):
    _name = 'ghl.location.user.lcphone'
    _description = 'GHL Location User LC Phone'

    location_id = fields.Char()

class GHLLocationUser(models.Model):
    _name = 'ghl.location.user'
    _description = 'GHL Location User'

    external_id = fields.Char(string='External ID')
    location_id = fields.Char(string='Location ID', required=True, index=True)
    name = fields.Char()
    first_name = fields.Char()
    last_name = fields.Char()
    email = fields.Char()
    phone = fields.Char()
    extension = fields.Char()
    permissions_id = fields.Many2one('ghl.location.user.permissions', string='Permissions')
    scopes = fields.Char()
    roles_id = fields.Many2one('ghl.location.user.roles', string='Roles')
    deleted = fields.Boolean()
    lc_phone_id = fields.Many2one('ghl.location.user.lcphone', string='LC Phone')
    profile_photo = fields.Char(string='Profile Photo URL')
    membership_contact_id = fields.Char(string='Membership Contact ID')
    freshdesk_contact_id = fields.Char(string='Freshdesk Contact ID')
    totp_enabled = fields.Boolean(string='TOTP Enabled') 