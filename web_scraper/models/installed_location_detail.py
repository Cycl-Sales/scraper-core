from odoo import models, fields

class LocationBusiness(models.Model):
    _name = 'location.business'
    _description = 'Business Info for Location'

    name = fields.Char(string='Business Name')
    address = fields.Char(string='Business Address')
    city = fields.Char(string='Business City')
    state = fields.Char(string='Business State')
    country = fields.Char(string='Business Country')
    postal_code = fields.Char(string='Business Postal Code')
    website = fields.Char(string='Business Website')
    timezone = fields.Char(string='Business Timezone')
    logo_url = fields.Char(string='Business Logo URL')

class LocationSocial(models.Model):
    _name = 'location.social'
    _description = 'Social Info for Location'

    facebook_url = fields.Char(string='Facebook URL')
    google_plus = fields.Char(string='Google Plus')
    linked_in = fields.Char(string='LinkedIn')
    foursquare = fields.Char(string='Foursquare')
    twitter = fields.Char(string='Twitter')
    yelp = fields.Char(string='Yelp')
    instagram = fields.Char(string='Instagram')
    youtube = fields.Char(string='YouTube')
    pinterest = fields.Char(string='Pinterest')
    blog_rss = fields.Char(string='Blog RSS')
    google_places_id = fields.Char(string='Google Places ID')

class LocationSettings(models.Model):
    _name = 'location.settings'
    _description = 'Settings Info for Location'

    allow_duplicate_contact = fields.Boolean(string='Allow Duplicate Contact')
    allow_duplicate_opportunity = fields.Boolean(string='Allow Duplicate Opportunity')
    allow_facebook_name_merge = fields.Boolean(string='Allow Facebook Name Merge')
    disable_contact_timezone = fields.Boolean(string='Disable Contact Timezone')

class LocationReseller(models.Model):
    _name = 'location.reseller'
    _description = 'Reseller Info for Location'
    # Add fields as needed (empty for now)

class InstalledLocationDetail(models.Model):
    _name = 'installed.location.detail'
    _description = 'Detailed Information for Installed Location'

    location_id = fields.Many2one('installed.location', string='Installed Location', required=True, ondelete='cascade')
    company_id = fields.Char(string='Company ID')
    name = fields.Char(string='Name')
    domain = fields.Char(string='Domain')
    address = fields.Char(string='Address')
    city = fields.Char(string='City')
    state = fields.Char(string='State')
    logo_url = fields.Char(string='Logo URL')
    country = fields.Char(string='Country')
    postal_code = fields.Char(string='Postal Code')
    website = fields.Char(string='Website')
    timezone = fields.Char(string='Timezone')
    first_name = fields.Char(string='First Name')
    last_name = fields.Char(string='Last Name')
    email = fields.Char(string='Email')
    phone = fields.Char(string='Phone')
    business_id = fields.Many2one('location.business', string='Business Info')
    social_id = fields.Many2one('location.social', string='Social Info')
    settings_id = fields.Many2one('location.settings', string='Settings Info')
    reseller_id = fields.Many2one('location.reseller', string='Reseller Info') 