from odoo import models, fields, api
from odoo.exceptions import UserError
import requests
import csv
from io import StringIO
import base64

class FetchUSZipcodeWizard(models.TransientModel):
    _name = 'fetch.us.zipcode.wizard'
    _description = 'Fetch US ZIP Code Data Wizard'

    result_message = fields.Text(string='Result', readonly=True)
    offset = fields.Integer(string='Batch Offset', default=0)
    batch_size = fields.Integer(string='Batch Size', default=100)
    single_zip = fields.Char(string='Fetch Single ZIP Code')
    failed_details = fields.Text(string='Failed ZIPs Details', readonly=True)
    csv_file = fields.Binary(string='CSV File')

    def action_fetch_zipcodes(self):
        Ref = self.env['us.zipcode.reference'].sudo()
        Zip = self.env['us.zipcode'].sudo()
        # Get unsynced ZIPs
        unsynced_zips = Ref.search([('synced', '=', False)], offset=self.offset, limit=self.batch_size)
        imported, updated, failed = 0, 0, 0
        failed_details = []
        for ref in unsynced_zips:
            zip_code = ref.zip
            url = f"http://api.zippopotam.us/us/{zip_code}"
            try:
                resp = requests.get(url, timeout=20)
                if resp.status_code != 200:
                    failed += 1
                    ref.write({'synced': False, 'sync_status': f'HTTP {resp.status_code}'})
                    failed_details.append(f"{zip_code}: HTTP {resp.status_code}")
                    continue
                print(data)
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
                    updated += 1
                else:
                    Zip.create(vals)
                    imported += 1
                ref.write({'synced': True, 'sync_status': 'OK'})
            except Exception as e:
                failed += 1
                ref.write({'synced': False, 'sync_status': str(e)})
                failed_details.append(f"{zip_code}: {str(e)}")
        msg = f"Processed {len(unsynced_zips)} unsynced ZIPs. Imported: {imported}, Updated: {updated}, Failed: {failed}."
        if unsynced_zips:
            msg += f"\nTo continue, increment the offset and run again."
        else:
            msg += "\nNo more unsynced ZIPs."
        self.result_message = msg
        self.failed_details = '\n'.join(failed_details)
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'fetch.us.zipcode.wizard',
            'view_mode': 'form',
            'target': 'new',
            'res_id': self.id,
        }

    def action_fetch_single_zip(self):
        if not self.single_zip and not self.csv_file:
            raise UserError('Please enter a ZIP code or upload a CSV file to fetch.')

        zip_codes = []
        if self.single_zip:
            zip_codes.extend(self.single_zip.split(','))  # Split by comma for multiple ZIPs
        elif self.csv_file:
            file_content = StringIO(base64.b64decode(self.csv_file).decode('utf-8'))
            csv_reader = csv.reader(file_content)
            for row in csv_reader:
                if row:  # Ensure the row is not empty
                    zip_codes.append(row[0].strip())

        imported, updated, failed = 0, 0, 0
        failed_details = []
        Zip = self.env['us.zipcode'].sudo()
        Ref = self.env['us.zipcode.reference'].sudo()

        for zip_code in zip_codes:
            zip_code = zip_code.strip()  # Ensure no leading/trailing spaces
            ref = Ref.search([('zip', '=', zip_code)], limit=1)
            try:
                url = f"http://api.zippopotam.us/us/{zip_code}"
                resp = requests.get(url, timeout=20)
                if resp.status_code != 200:
                    failed += 1
                    if ref:
                        ref.write({'synced': False, 'sync_status': f'HTTP {resp.status_code}'})
                    failed_details.append(f"{zip_code}: HTTP {resp.status_code}")
                else:
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
                        updated += 1
                    else:
                        Zip.create(vals)
                        imported += 1
                    if ref:
                        ref.write({'synced': True, 'sync_status': 'OK'})
            except Exception as e:
                failed += 1
                if ref:
                    ref.write({'synced': False, 'sync_status': str(e)})
                failed_details.append(f"{zip_code}: {str(e)}")

        msg = f"Processed ZIPs. Imported: {imported}, Updated: {updated}, Failed: {failed}."
        self.result_message = msg
        self.failed_details = '\n'.join(failed_details)
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'fetch.us.zipcode.wizard',
            'view_mode': 'form',
            'target': 'new',
            'res_id': self.id,
        }

    def action_increment_offset(self):
        self.offset += 100
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'fetch.us.zipcode.wizard',
            'view_mode': 'form',
            'target': 'new',
            'res_id': self.id,
        } 