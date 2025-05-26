from odoo import models, fields
from odoo.exceptions import UserError
import base64
import io
import csv

class UploadZipcodeReferenceWizard(models.TransientModel):
    _name = 'upload.zipcode.reference.wizard'
    _description = 'Upload ZIP Code Reference CSV Wizard'

    csv_file = fields.Binary(string='ZIP Code Reference CSV', required=True)
    csv_filename = fields.Char(string='CSV Filename')
    result_message = fields.Text(string='Result', readonly=True)

    def action_upload_zipcode_reference(self):
        if not self.csv_file:
            raise UserError('Please upload a ZIP code reference CSV file.')
        csv_data = base64.b64decode(self.csv_file)
        csvfile = io.StringIO(csv_data.decode('utf-8'))
        reader = csv.DictReader(csvfile)
        Ref = self.env['us.zipcode.reference'].sudo()
        imported, updated = 0, 0
        for row in reader:
            zip_code = row.get('zip')
            if not zip_code:
                continue
            vals = {
                'zip': zip_code,
                'type': row.get('type', ''),
                'decommissioned': row.get('decommissioned', '0') in ('1', 'True', 'true'),
                'primary_city': row.get('primary_city', ''),
                'acceptable_cities': row.get('acceptable_cities', ''),
                'unacceptable_cities': row.get('unacceptable_cities', ''),
                'state': row.get('state', ''),
                'county': row.get('county', ''),
                'timezone': row.get('timezone', ''),
                'area_codes': row.get('area_codes', ''),
                'world_region': row.get('world_region', ''),
                'country': row.get('country', ''),
                'latitude': float(row.get('latitude', 0) or 0),
                'longitude': float(row.get('longitude', 0) or 0),
                'irs_estimated_population': int(row.get('irs_estimated_population', 0) or 0),
            }
            existing = Ref.search([('zip', '=', zip_code)], limit=1)
            if existing:
                existing.write(vals)
                updated += 1
            else:
                Ref.create(vals)
                imported += 1
        self.result_message = f"Imported: {imported}, Updated: {updated} ZIP code reference records."
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'upload.zipcode.reference.wizard',
            'view_mode': 'form',
            'target': 'new',
            'res_id': self.id,
        } 