from odoo import http
from odoo.http import request
import json

class ZillowPropertyController(http.Controller):
    
    @http.route('/api/zillow/properties', type='http', auth='public', methods=['GET'], csrf=False)
    def get_zillow_properties(self, **kwargs):
        try:
            # Get all Zillow property records
            properties = request.env['zillow.property.detail'].sudo().search_read([], 
                fields=['name', 'street', 'city', 'state', 'zip_code', 'price', 'bedrooms', 
                       'bathrooms', 'square_feet', 'property_type', 'listing_status', 'hi_res_image_link'])
            
            # Format the response
            response = {
                'status': 'success',
                'data': properties
            }
            
            return http.Response(
                json.dumps(response),
                content_type='application/json',
                status=200
            )
            
        except Exception as e:
            return http.Response(
                json.dumps({
                    'status': 'error',
                    'message': str(e)
                }),
                content_type='application/json',
                status=500
            ) 