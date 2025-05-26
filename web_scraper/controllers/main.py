from odoo import http
from odoo.http import request, Response
import json
import requests
import urllib.parse
from odoo.fields import Datetime


class ZillowPropertyController(http.Controller):
    @http.route('/api/zillow/properties', type='http', auth='user', cors='*', csrf=False)
    def get_properties(self, **kwargs):
        try:
            # Get pagination parameters
            page = int(kwargs.get('page', 1))
            page_size = int(kwargs.get('page_size', 10))
            
            # Get total count first
            total_count = request.env['zillow.property'].sudo().search_count([])
            
            # Calculate offset and limit
            offset = (page - 1) * page_size
            
            # Get paginated property data
            properties = request.env['zillow.property'].sudo().search_read(
                [],
                ['id', 'zpid', 'street_address', 'city', 'state', 'price',
                 'bedrooms', 'bathrooms', 'living_area', 'home_status', 'home_type',
                 'sent_to_cyclsales_count'],
                offset=offset,
                limit=page_size
            )

            # For each property, get its detail record
            for zproperty in properties:
                detail = request.env['zillow.property.detail'].sudo().search(
                    [('property_id', '=', zproperty['id'])],
                )
                if detail:
                    for zdetail in detail:
                        zproperty['hi_res_image_link'] = zdetail.hi_res_image_link
                        zproperty['hdp_url'] = zdetail.hdp_url
                else:
                    zproperty['hi_res_image_link'] = False
                    zproperty['hdp_url'] = False

                # Add sent status for current user
                property_obj = request.env['zillow.property'].sudo().browse(zproperty['id'])
                zproperty['sent_by_current_user'] = request.env.user.id in property_obj.sent_to_cyclsales_by.ids

            return Response(
                json.dumps({
                    'properties': properties,
                    'total_results': total_count,
                    'page': page,
                    'page_size': page_size,
                    'total_pages': (total_count + page_size - 1) // page_size
                }),
                content_type='application/json',
                headers=[('Access-Control-Allow-Origin', '*')]
            )
        except Exception as e:
            return Response(
                json.dumps({'error': str(e)}),
                content_type='application/json',
                status=500,
                headers=[('Access-Control-Allow-Origin', '*')]
            )

    @http.route('/api/zillow/property/send-to-cyclsales', type='http', auth='user', methods=['POST'], cors='*', csrf=False)
    def send_to_cyclsales(self, **post):
        try:
            property_ids = json.loads(post.get('property_ids', '[]'))
            if not property_ids:
                return Response(
                    json.dumps({'error': 'No properties selected'}),
                    content_type='application/json',
                    status=400,
                    headers=[('Access-Control-Allow-Origin', '*')]
                )

            properties = request.env['zillow.property'].sudo().browse(property_ids)
            sent_count = 0
            already_sent = 0

            for property in properties:
                if property.action_send_to_cyclsales(request.env.user.id):
                    sent_count += 1
                else:
                    already_sent += 1

            return Response(
                json.dumps({
                    'success': True,
                    'message': f'Successfully sent {sent_count} properties to CyclSales. {already_sent} properties were already sent.',
                    'sent_count': sent_count,
                    'already_sent': already_sent
                }),
                content_type='application/json',
                headers=[('Access-Control-Allow-Origin', '*')]
            )
        except Exception as e:
            return Response(
                json.dumps({'error': str(e)}),
                content_type='application/json',
                status=500,
                headers=[('Access-Control-Allow-Origin', '*')]
            )

    @http.route('/api/zillow/property/<int:property_id>/fetch', type='http', auth='none', methods=['POST'], cors='*',
                csrf=False)
    def fetch_property_data(self, property_id):
        try:
            property = request.env['zillow.property'].sudo().browse(property_id)
            property.action_fetch_property_data()
            return Response(
                json.dumps({'success': True}),
                content_type='application/json',
                headers=[('Access-Control-Allow-Origin', '*')]
            )
        except Exception as e:
            return Response(
                json.dumps({'error': str(e)}),
                content_type='application/json',
                status=500,
                headers=[('Access-Control-Allow-Origin', '*')]
            )

    @http.route('/api/zillow/search', type='http', auth='user', methods=['GET'], cors='*', csrf=False)
    def search_properties(self, **kwargs):
        try:
            ICPSudo = request.env['ir.config_parameter'].sudo()
            api_host = ICPSudo.get_param('web_scraper.rapidapi_host', 'zillow56.p.rapidapi.com')
            api_key = ICPSudo.get_param('web_scraper.rapidapi_key')

            if not api_host or not api_key:
                return Response(
                    json.dumps({'error': 'API credentials not configured'}),
                    content_type='application/json',
                    status=500,
                    headers=[('Access-Control-Allow-Origin', '*')]
                )

            # Get the Zillow URL from the frontend
            frontend_url = kwargs.get('url', '')
            if not frontend_url:
                return Response(
                    json.dumps({'error': 'No URL provided'}),
                    content_type='application/json',
                    status=400,
                    headers=[('Access-Control-Allow-Origin', '*')]
                )

            try:
                parsed = urllib.parse.urlparse(frontend_url)
                if not parsed.scheme or not parsed.netloc:
                    raise ValueError('Invalid URL format')
                
                # Validate that it's a Zillow URL
                if not parsed.netloc.endswith('zillow.com'):
                    raise ValueError('URL must be from zillow.com')
                
                # Get the search query state from the URL
                qs = urllib.parse.parse_qs(parsed.query)
                if 'searchQueryState' not in qs:
                    raise ValueError('Missing searchQueryState parameter')
                
                search_query_state = json.loads(qs['searchQueryState'][0])
                
                # Validate required fields in searchQueryState
                required_fields = ['pagination', 'mapBounds', 'filterState']
                for field in required_fields:
                    if field not in search_query_state:
                        raise ValueError(f'Missing required field: {field}')
                
                # Validate mapBounds
                map_bounds = search_query_state['mapBounds']
                required_bounds = ['west', 'east', 'south', 'north']
                for bound in required_bounds:
                    if bound not in map_bounds:
                        raise ValueError(f'Missing required map bound: {bound}')
                
            except (ValueError, json.JSONDecodeError) as e:
                return Response(
                    json.dumps({'error': str(e)}),
                    content_type='application/json',
                    status=400,
                    headers=[('Access-Control-Allow-Origin', '*')]
                )

            # Build the RapidAPI request
            rapidapi_url = f'https://{api_host}/search_url'
            params = {
                'url': frontend_url,
                'output': 'json',
                'listing_type': kwargs.get('listing_type', 'by_agent')
            }
            if 'page' in kwargs:
                params['page'] = kwargs['page']

            headers = {
                'x-rapidapi-host': api_host,
                'x-rapidapi-key': api_key
            }

            response = requests.get(rapidapi_url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()
            
            # Process and store the results in Odoo
            properties = []
            for item in data.get('results', []):
                try:
                    # Skip items without required fields
                    if not item.get('zpid') or not item.get('streetAddress'):
                        continue

                    # Main property fields
                    property_vals = {
                        'zpid': str(item.get('zpid')),  # Ensure zpid is string
                        'street_address': item.get('streetAddress'),
                        'city': item.get('city'),
                        'state': item.get('state'),
                        'zipcode': item.get('zipcode'),
                        'price': float(item.get('price', 0)) if item.get('price') else False,
                        'bedrooms': int(item.get('bedrooms', 0)) if item.get('bedrooms') else False,
                        'bathrooms': float(item.get('bathrooms', 0)) if item.get('bathrooms') else False,
                        'living_area': float(item.get('livingArea', 0)) if item.get('livingArea') else False,
                        'home_status': item.get('homeStatus'),
                        'home_type': item.get('homeType'),
                        'latitude': float(item.get('latitude', 0)) if item.get('latitude') else False,
                        'longitude': float(item.get('longitude', 0)) if item.get('longitude') else False,
                    }

                    # Create or update property
                    try:
                        property_obj = request.env['zillow.property'].sudo().search([('zpid', '=', property_vals['zpid'])], limit=1)
                        if property_obj:
                            property_obj.write(property_vals)
                        else:
                            property_obj = request.env['zillow.property'].sudo().create(property_vals)
                    except Exception as e:
                        print(f"Error creating/updating property: {str(e)}")
                        continue

                    # Detail fields
                    detail_vals = {
                        'zpid': str(item.get('zpid')),  # Ensure zpid is string
                        'property_id': property_obj.id,
                        'hi_res_image_link': item.get('imgSrc'),  # Updated to use imgSrc
                        'hdp_url': f"https://www.zillow.com/homedetails/{item.get('zpid')}_zpid/",  # Construct HDP URL
                        'bedrooms': property_vals['bedrooms'],
                        'bathrooms': property_vals['bathrooms'],
                        'living_area': property_vals['living_area'],
                        'price': property_vals['price'],
                        'state': property_vals['state'],
                        'zipcode': property_vals['zipcode'],
                        'home_status': property_vals['home_status'],
                        'home_type': property_vals['home_type'],
                        'latitude': property_vals['latitude'],
                        'longitude': property_vals['longitude'],
                        'last_checked': Datetime.now(),
                        'last_updated': Datetime.now(),
                    }

                    # Create or update detail
                    try:
                        detail_obj = request.env['zillow.property.detail'].sudo().search([('zpid', '=', detail_vals['zpid'])], limit=1)
                        if detail_obj:
                            detail_obj.write(detail_vals)
                        else:
                            detail_obj = request.env['zillow.property.detail'].sudo().create(detail_vals)
                    except Exception as e:
                        print(f"Error creating/updating property detail: {str(e)}")
                        continue

                    # Add to response
                    properties.append({
                        'id': property_obj.id,
                        'zpid': property_obj.zpid,
                        'street_address': property_obj.street_address,
                        'city': property_obj.city,
                        'state': property_obj.state,
                        'price': property_obj.price,
                        'bedrooms': property_obj.bedrooms,
                        'bathrooms': property_obj.bathrooms,
                        'living_area': property_obj.living_area,
                        'home_status': property_obj.home_status,
                        'home_type': property_obj.home_type,
                        'hi_res_image_link': detail_obj.hi_res_image_link,
                        'hdp_url': detail_obj.hdp_url,
                    })
                except Exception as e:
                    print(f"Error processing property: {str(e)}")
                    continue

            # Pagination parameters
            page = int(kwargs.get('page', 1))
            page_size = int(kwargs.get('page_size', 10))

            total_results = len(properties)
            total_pages = max(1, (total_results + page_size - 1) // page_size)
            start = (page - 1) * page_size
            end = start + page_size
            paginated_properties = properties[start:end]

            return Response(
                json.dumps({
                    'success': True,
                    'properties': paginated_properties,
                    'total_results': total_results,
                    'total_pages': total_pages,
                    'page': page,
                    'results_per_page': page_size
                }),
                content_type='application/json',
                headers=[('Access-Control-Allow-Origin', '*')]
            )
        except Exception as e:
            return Response(
                json.dumps({'error': str(e)}),
                content_type='application/json',
                status=500,
                headers=[('Access-Control-Allow-Origin', '*')]
            )
