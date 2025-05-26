from odoo import models, fields

class USZipCodeReference(models.Model):
    _name = 'us.zipcode.reference'
    _description = 'US ZIP Code Reference'
    _order = 'zip'

    zip = fields.Char(string='ZIP Code', required=True, index=True)
    type = fields.Char(string='Type')
    decommissioned = fields.Boolean(string='Decommissioned')
    primary_city = fields.Char(string='Primary City')
    acceptable_cities = fields.Text(string='Acceptable Cities')
    unacceptable_cities = fields.Text(string='Unacceptable Cities')
    state = fields.Char(string='State')
    county = fields.Char(string='County')
    timezone = fields.Char(string='Timezone')
    area_codes = fields.Char(string='Area Codes')
    world_region = fields.Char(string='World Region')
    country = fields.Char(string='Country')
    latitude = fields.Float(string='Latitude')
    longitude = fields.Float(string='Longitude')
    irs_estimated_population = fields.Integer(string='IRS Estimated Population')
    synced = fields.Boolean(string='Synced', default=False, index=True)
    sync_status = fields.Text(string='Sync Status')

    _sql_constraints = [
        ('zip_unique', 'unique(zip)', 'ZIP Code must be unique!'),
    ]

    def cron_fetch_zipcodes(self, batch_size=10):
        """
        Cron job to fetch a small batch of unsynced ZIP codes from the reference table.
        This is designed to be run frequently by a scheduled action, respecting API rate limits.
        """
        import requests
        Zip = self.env['us.zipcode'].sudo()
        unsynced_zips = self.search([('synced', '=', False)], limit=batch_size)
        for ref in unsynced_zips:
            zip_code = ref.zip
            url = f"http://api.zippopotam.us/us/{zip_code}"
            try:
                resp = requests.get(url, timeout=20)
                if resp.status_code != 200:
                    ref.write({'synced': False, 'sync_status': f'HTTP {resp.status_code}'})
                    continue
                data = resp.json()
                city = data['places'][0]['place name'] if data['places'] else ''
                state = data['places'][0]['state abbreviation'] if data['places'] else ''
                vals = {
                    'zip_code': zip_code,
                    'city': city,
                    'state': state,
                    'county_fips': '',
                    'population': 0,
                }
                existing = Zip.search([('zip_code', '=', zip_code)], limit=1)
                if existing:
                    existing.write(vals)
                else:
                    Zip.create(vals)
                ref.write({'synced': True, 'sync_status': 'OK'})
            except Exception as e:
                ref.write({'synced': False, 'sync_status': str(e)}) 