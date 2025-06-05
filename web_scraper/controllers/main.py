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
            # Get locationId from request
            location_id = kwargs.get('locationId')
            print(f"locationID: {location_id}")
            if not location_id:
                print("locationId missing in request!")
                return Response(
                    json.dumps({'error': 'locationId is required'}),
                    content_type='application/json',
                    status=400,
                    headers=[('Access-Control-Allow-Origin', '*')]
                )

            # Find the GHL location record
            ghl_location = request.env['ghl.location'].sudo().search([('location_id', '=', location_id)], limit=1)
            print(f"ghl_location: {ghl_location}")
            if not ghl_location or not ghl_location.market_location_id:
                print("Invalid or unlinked locationId: ghl_location or market_location_id missing!")
                return Response(
                    json.dumps({'error': 'Invalid or unlinked locationId'}),
                    content_type='application/json',
                    status=400,
                    headers=[('Access-Control-Allow-Origin', '*')]
                )

            # Get allowed ZIP codes from the market location
            allowed_zipcodes = ghl_location.market_location_id.zipcode_ids.mapped('zip_code')
            print(f"allowed_zipcodes: {allowed_zipcodes}")
            if not allowed_zipcodes:
                print("No ZIP codes configured for this location!")
                return Response(
                    json.dumps({'error': 'No ZIP codes configured for this location'}),
                    content_type='application/json',
                    status=400,
                    headers=[('Access-Control-Allow-Origin', '*')]
                )

            # Get pagination parameters
            page = int(kwargs.get('page', 1))
            page_size = int(kwargs.get('page_size', 10))
            sort_column = kwargs.get('sort_column', 'street_address')
            sort_direction = kwargs.get('sort_direction', 'asc')
            allowed_columns = ['street_address', 'price', 'bedrooms', 'bathrooms', 'living_area', 'home_type', 'home_status', 'sent_to_cyclsales_count']
            if sort_column not in allowed_columns:
                sort_column = 'street_address'
            if sort_direction not in ['asc', 'desc']:
                sort_direction = 'asc'
            order = f"{sort_column} {sort_direction}"

            # Filter properties by allowed ZIP codes
            domain = [('zipcode', 'in', allowed_zipcodes)]

            # Get total count first
            total_count = request.env['zillow.property'].sudo().search_count(domain)

            # Calculate offset and limit
            offset = (page - 1) * page_size

            # Get paginated property data with sorting
            properties = request.env['zillow.property'].sudo().search_read(
                domain,
                ['id', 'zpid', 'street_address', 'city', 'state', 'price',
                 'bedrooms', 'bathrooms', 'living_area', 'home_status', 'home_type',
                 'sent_to_cyclsales_count', 'zipcode'],
                offset=offset,
                limit=page_size,
                order=order
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
                        # Attach listing agent info if present
                        if zdetail.listing_agent_id:
                            agent = zdetail.listing_agent_id
                            zproperty['listingAgent'] = {
                                'id': agent.id,
                                'property_id': agent.property_id.id,
                                'name': agent.display_name or '',
                                'business_name': agent.business_name or '',
                                'phone': f"{agent.phone_area_code or ''}-{agent.phone_prefix or ''}-{agent.phone_number or ''}",
                                'profile_url': agent.profile_url or '',
                                'email': agent.email or '',
                                'license_number': agent.license_number or '',
                                'license_state': agent.license_state or '',
                                'badge_type': agent.badge_type or '',
                                'encoded_zuid': agent.encoded_zuid or '',
                                'first_name': agent.first_name or '',
                                'image_url': agent.image_url or '',
                                'image_height': agent.image_height,
                                'image_width': agent.image_width,
                                'rating_average': agent.rating_average,
                                'recent_sales': agent.recent_sales,
                                'review_count': agent.review_count,
                                'reviews_url': agent.reviews_url or '',
                                'services_offered': agent.services_offered or '',
                                'username': agent.username or '',
                                'write_review_url': agent.write_review_url or '',
                                'is_zpro': agent.is_zpro,
                            }
                        else:
                            zproperty['listingAgent'] = None
                else:
                    zproperty['hi_res_image_link'] = False
                    zproperty['hdp_url'] = False
                    zproperty['listingAgent'] = None

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

    @http.route('/api/zillow/search_address', type='http', auth='user', methods=['GET'], cors='*', csrf=False)
    def search_address(self, **kwargs):
        try:
            ICPSudo = request.env['ir.config_parameter'].sudo()
            api_host = ICPSudo.get_param('web_scraper.rapidapi_host', 'zillow56.p.rapidapi.com')
            api_key = ICPSudo.get_param('web_scraper.rapidapi_key')
            address = kwargs.get('address', '')
            if not address:
                return Response(
                    json.dumps({'error': 'No address provided'}),
                    content_type='application/json',
                    status=400,
                    headers=[('Access-Control-Allow-Origin', '*')]
                )
            rapidapi_url = f'https://{api_host}/search_address'
            params = {'address': address}
            headers = {
                'x-rapidapi-host': api_host,
                'x-rapidapi-key': api_key
            }
            response = requests.get(rapidapi_url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()
            return Response(
                json.dumps({'success': True, 'data': data}),
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

            # Check for address parameter first
            address = kwargs.get('address', '')
            if address:
                # Try address search first
                try:
                    rapidapi_url = f'https://{api_host}/search_address'
                    params = {'address': address}
                    headers = {
                        'x-rapidapi-host': api_host,
                        'x-rapidapi-key': api_key
                    }
                    response = requests.get(rapidapi_url, headers=headers, params=params)
                    response.raise_for_status()
                    data = response.json()
                    # If we get a result, return it immediately
                    if data:
                        return Response(
                            json.dumps({'success': True, 'data': data}),
                            content_type='application/json',
                            headers=[('Access-Control-Allow-Origin', '*')]
                        )
                except Exception as e:
                    # If address search fails, fall back to normal search
                    pass

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
                if not parsed.netloc.endswith('zillow.com'):
                    raise ValueError('URL must be from zillow.com')
            except (ValueError, json.JSONDecodeError) as e:
                return Response(
                    json.dumps({'error': str(e)}),
                    content_type='application/json',
                    status=400,
                    headers=[('Access-Control-Allow-Origin', '*')]
                )

            # Build the RapidAPI request (send the full Zillow URL as 'url')
            rapidapi_url = f'https://{api_host}/search_url'
            params = {
                'url': frontend_url,
                'output': 'json',
                'listing_type': kwargs.get('listing_type', 'by_agent'),
                'page_size': 100,
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

            properties = []
            for item in data.get('results', []):
                try:
                    if not item.get('zpid') or not item.get('streetAddress'):
                        continue

                    # Start a new transaction for each property
                    with request.env.cr.savepoint():
                        # --- Main Property Fields ---
                        property_vals = {
                            'zpid': str(item.get('zpid')),
                            'street_address': item.get('streetAddress'),
                            'city': item.get('city'),
                            'state': item.get('state'),
                            'zipcode': item.get('zipcode'),
                            'country': item.get('country', 'USA'),
                            'price': float(item.get('price', 0)) if item.get('price') else False,
                            'bedrooms': int(item.get('bedrooms', 0)) if item.get('bedrooms') else False,
                            'bathrooms': float(item.get('bathrooms', 0)) if item.get('bathrooms') else False,
                            'living_area': float(item.get('livingArea', 0)) if item.get('livingArea') else False,
                            'lot_area_value': float(item.get('lotSize', 0)) if item.get('lotSize') else False,
                            'home_status': item.get('homeStatus'),
                            'home_type': item.get('homeType'),
                            'latitude': float(item.get('latitude', 0)) if item.get('latitude') else False,
                            'longitude': float(item.get('longitude', 0)) if item.get('longitude') else False,
                            'zestimate': float(item.get('zestimate', 0)) if item.get('zestimate') else False,
                            'rent_zestimate': float(item.get('rentZestimate', 0)) if item.get('rentZestimate') else False,
                            'tax_assessed_value': float(item.get('taxAssessedValue', 0)) if item.get('taxAssessedValue') else False,
                            'time_on_zillow': item.get('timeOnZillow'),
                            'days_on_zillow': int(item.get('daysOnZillow', 0)) if item.get('daysOnZillow') else False,
                            'price_change': float(item.get('priceChange', 0)) if item.get('priceChange') else False,
                            'date_price_changed': item.get('datePriceChanged'),
                            'provider_listing_id': item.get('providerListingID'),
                            'hi_res_image_link': item.get('imgSrc'),
                            'hdp_url': f"https://www.zillow.com/homedetails/{item.get('zpid')}_zpid/",
                            'last_fetched': Datetime.now(),
                            'sent_to_cyclsales_count': 0,  # Initialize to 0
                        }
                        
                        # Create or update property with proper error handling
                        try:
                            property_obj = request.env['zillow.property'].sudo().search([('zpid', '=', property_vals['zpid'])], limit=1)
                            if property_obj:
                                property_obj.write(property_vals)
                            else:
                                property_obj = request.env['zillow.property'].sudo().create(property_vals)
                        except Exception as e:
                            print(f"Error creating/updating property: {str(e)}")
                            continue

                        # --- Listing Agent ---
                        listing_agent_id = False
                        agent_info = item.get('listingAgent') or item.get('listing_agent')
                        if agent_info and isinstance(agent_info, dict):
                            try:
                                agent_vals = {
                                    'display_name': agent_info.get('name') or agent_info.get('display_name'),
                                    'business_name': agent_info.get('business_name'),
                                    'phone_area_code': '',
                                    'phone_prefix': '',
                                    'phone_number': '',
                                    'profile_url': agent_info.get('profile_url'),
                                }
                                # Parse phone if available
                                phone = agent_info.get('phone')
                                if phone and isinstance(phone, str):
                                    phone_parts = phone.split('-')
                                    if len(phone_parts) == 3:
                                        agent_vals['phone_area_code'] = phone_parts[0]
                                        agent_vals['phone_prefix'] = phone_parts[1]
                                        agent_vals['phone_number'] = phone_parts[2]
                                agent_rec = request.env['zillow.property.listing.agent'].sudo().search([
                                    ('display_name', '=', agent_vals['display_name']),
                                    ('business_name', '=', agent_vals['business_name']),
                                ], limit=1)
                                if agent_rec:
                                    agent_rec.write(agent_vals)
                                else:
                                    agent_rec = request.env['zillow.property.listing.agent'].sudo().create(agent_vals)
                                listing_agent_id = agent_rec.id
                            except Exception as e:
                                print(f"Error processing agent: {str(e)}")
                                continue

                        # --- Property Detail Fields ---
                        try:
                            detail_vals = {
                                'zpid': str(item.get('zpid')),
                                'property_id': property_obj.id,
                                'hi_res_image_link': item.get('imgSrc'),
                                'hdp_url': f"https://www.zillow.com/homedetails/{item.get('zpid')}_zpid/",
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
                                'listing_agent_id': listing_agent_id,
                                'currency': 'USD',
                                'country': property_vals['country'],
                                'zestimate': property_vals['zestimate'],
                                'description': item.get('description'),
                                'days_on_zillow': property_vals['days_on_zillow'],
                            }
                            detail_obj = request.env['zillow.property.detail'].sudo().search([('zpid', '=', detail_vals['zpid'])], limit=1)
                            if detail_obj:
                                detail_obj.write(detail_vals)
                            else:
                                detail_obj = request.env['zillow.property.detail'].sudo().create(detail_vals)
                        except Exception as e:
                            print(f"Error creating/updating detail: {str(e)}")
                            continue

                        # Add to response
                        properties.append({
                            'id': property_obj.id,
                            'zpid': property_obj.zpid,
                            'street_address': property_obj.street_address,
                            'city': property_obj.city,
                            'state': property_obj.state,
                            'zipcode': property_obj.zipcode,
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
