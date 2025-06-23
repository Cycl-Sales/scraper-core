from odoo import http
from odoo.http import request, Response, route
import json
import requests
import urllib.parse
from odoo.fields import Datetime
import logging
from .cors_utils import get_cors_headers
import time


class ZillowPropertyController(http.Controller):
    @http.route('/api/zillow/properties', type='http', auth='none', csrf=False)
    def get_properties(self, **kwargs):
        try:
            # Get locationId from request
            location_id = kwargs.get('locationId')
            if not location_id:
                return Response(
                    json.dumps({'error': 'locationId is required'}),
                    content_type='application/json',
                    status=400,
                    headers=get_cors_headers(request)
                )

            # Find the GHL location record
            ghl_location = request.env['ghl.location'].sudo().search([('location_id', '=', location_id)], limit=1)
            if not ghl_location or not ghl_location.market_location_id:
                print("Invalid or unlinked locationId: ghl_location or market_location_id missing!")
                return Response(
                    json.dumps({'error': 'Invalid or unlinked locationId'}),
                    content_type='application/json',
                    status=400,
                    headers=get_cors_headers(request)
                )

            # Get allowed ZIP codes from the market location
            allowed_zipcodes = ghl_location.market_location_id.zipcode_ids.mapped('zip_code')
            if not allowed_zipcodes:
                print("No ZIP codes configured for this location!")
                return Response(
                    json.dumps({'error': 'No ZIP codes configured for this location'}),
                    content_type='application/json',
                    status=400,
                    headers=get_cors_headers(request)
                )

            # Get pagination parameters
            page = int(kwargs.get('page', 1))
            page_size = int(kwargs.get('page_size', 10))
            sort_column = kwargs.get('sort_column', 'street_address')
            sort_direction = kwargs.get('sort_direction', 'asc')
            allowed_columns = ['street_address', 'price', 'bedrooms', 'bathrooms', 'living_area', 'home_type',
                               'home_status', 'sent_to_cyclsales_count']
            if sort_column not in allowed_columns:
                sort_column = 'street_address'
            if sort_direction not in ['asc', 'desc']:
                sort_direction = 'asc'
            order = f"{sort_column} {sort_direction}"

            # Filter properties by allowed ZIP codes
            domain = [('zipcode', 'in', allowed_zipcodes)]

            # --- Apply filters from frontend ---
            # Price
            min_price = kwargs.get('min_price')
            max_price = kwargs.get('max_price')
            if min_price:
                domain.append(('price', '>=', float(min_price)))
            if max_price:
                domain.append(('price', '<=', float(max_price)))
            # Bedrooms
            bedrooms = kwargs.get('bedrooms')
            if bedrooms:
                domain.append(('bedrooms', '>=', int(bedrooms)))
            # Bathrooms
            bathrooms = kwargs.get('bathrooms')
            if bathrooms:
                domain.append(('bathrooms', '>=', float(bathrooms)))
            # Living Area (sqft)
            sqft_min = kwargs.get('sqft_min')
            sqft_max = kwargs.get('sqft_max')
            if sqft_min:
                domain.append(('living_area', '>=', float(sqft_min)))
            if sqft_max:
                domain.append(('living_area', '<=', float(sqft_max)))
            # Lot Area
            lot_min = kwargs.get('lot_min')
            lot_max = kwargs.get('lot_max')
            if lot_min:
                domain.append(('lot_area_value', '>=', float(lot_min)))
            if lot_max:
                domain.append(('lot_area_value', '<=', float(lot_max)))
            # Year Built
            year_min = kwargs.get('year_min')
            year_max = kwargs.get('year_max')
            if year_min:
                domain.append(('year_built', '>=', int(year_min)))
            if year_max:
                domain.append(('year_built', '<=', int(year_max)))
            # Home Type
            home_type = kwargs.get('home_type')
            if home_type:
                if isinstance(home_type, list):
                    domain.append(('home_type', 'in', home_type))
                else:
                    domain.append(('home_type', '=', home_type))
            # Home Status
            home_status = kwargs.get('home_status')
            if home_status:
                domain.append(('home_status', '=', home_status))
            # Street address, city, state, or zipcode search (from search box)
            search_value = kwargs.get('search') or kwargs.get('address') or kwargs.get('street_address')
            if search_value:
                domain += ['|', '|', '|',
                           ('street_address', 'ilike', search_value),
                           ('city', 'ilike', search_value),
                           ('state', 'ilike', search_value),
                           ('zipcode', 'ilike', search_value),
                           ]

            # Listing type filter (for_sale, for_rent, sold)
            listing_type = kwargs.get('listing_type', 'for_sale')
            if listing_type == 'for_rent':
                domain.append(('home_status', '=', 'FOR_RENT'))
            elif listing_type == 'sold':
                domain.append(('home_status', '=', 'SOLD'))
            else:
                domain.append(('home_status', '=', 'FOR_SALE'))

            # Get total count
            total_count = request.env['zillow.property'].sudo().search_count(domain)

            # Calculate offset and limit
            offset = (page - 1) * page_size

            # Get paginated property data with sorting
            properties = request.env['zillow.property'].sudo().search_read(
                domain,
                ['id', 'zpid', 'street_address', 'city', 'state', 'price',
                 'bedrooms', 'bathrooms', 'living_area', 'home_status', 'home_type',
                 'sent_to_cyclsales_count', 'zipcode', 'sent_to_ghl_locations'],
                offset=offset,
                limit=page_size,
                order=order
            )

            # Batch fetch all details for these properties
            property_ids = [p['id'] for p in properties]
            details = request.env['zillow.property.detail'].sudo().search([('property_id', 'in', property_ids)])
            details_by_property = {}
            for d in details:
                details_by_property.setdefault(d.property_id.id, []).append(d)

            for zproperty in properties:
                detail_list = details_by_property.get(zproperty['id'], [])
                if detail_list:
                    # If multiple, just use the first for display
                    zdetail = detail_list[0]
                    zproperty['home_type'] = zdetail.home_type.replace('_', ' ').title() if zdetail.home_type else ''
                    zproperty['hi_res_image_link'] = zdetail.hi_res_image_link
                    zproperty['hdp_url'] = zdetail.hdp_url
                    # Refactored: Get listing agent from agent_ids where associated_agent_type == 'listAgent'
                    listing_agent = zdetail.agent_ids.filtered(lambda a: a.associated_agent_type == 'listAgent')
                    if listing_agent:
                        agent = listing_agent[0]
                        agent_name = agent.member_full_name
                        if not agent_name:
                            agent_name = zdetail.agent_name
                        zproperty['listingAgent'] = {
                            'name': agent_name,
                            'email': zdetail.agent_email or 'N/A',
                            'phone': zdetail.agent_phone_number or 'N/A',
                            'full_name': agent.member_full_name or '',
                            'state_license': agent.member_state_license or '',
                        }
                    else:
                        zproperty['listingAgent'] = None
                else:
                    zproperty['hi_res_image_link'] = False
                    zproperty['hdp_url'] = False
                    zproperty['listingAgent'] = None
                sent_to_ghl_locations = zproperty.get('sent_to_ghl_locations', [])
                zproperty['sent_to_cyclsales'] = False
                if location_id and sent_to_ghl_locations:
                    for record in sent_to_ghl_locations:
                        ghl_location_id = request.env['ghl.location'].sudo().browse(record)
                        if location_id in ghl_location_id.location_id:
                            zproperty['sent_to_cyclsales'] = True

            return Response(
                json.dumps({
                    'properties': properties,
                    'total_results': total_count,
                    'page': page,
                    'page_size': page_size,
                    'total_pages': (total_count + page_size - 1) // page_size
                }),
                content_type='application/json',
                headers=get_cors_headers(request)
            )
        except Exception as e:
            return Response(
                json.dumps({'error': str(e)}),
                content_type='application/json',
                status=500,
                headers=get_cors_headers(request)
            )

    @http.route('/api/zillow/property/send-to-cyclsales', type='http', auth='none', methods=['POST', 'OPTIONS'], cors='*', csrf=False)
    def send_to_cyclsales(self, **post):
        try:
            property_ids = json.loads(post.get('property_ids', '[]'))
            if not property_ids:
                return Response(
                    json.dumps({'error': 'No properties selected'}),
                    content_type='application/json',
                    status=400,
                    headers=get_cors_headers(request)
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
                headers=get_cors_headers(request)
            )
        except Exception as e:
            return Response(
                json.dumps({'error': str(e)}),
                content_type='application/json',
                status=500,
                headers=get_cors_headers(request)
            )

    @http.route('/api/zillow/property/<int:property_id>/fetch', type='http', auth='none', methods=['POST', 'OPTIONS'], cors='*', csrf=False)
    def fetch_property_data(self, property_id):
        try:
            property = request.env['zillow.property'].sudo().browse(property_id)
            property.action_fetch_property_data()
            return Response(
                json.dumps({'success': True}),
                content_type='application/json',
                headers=get_cors_headers(request)
            )
        except Exception as e:
            return Response(
                json.dumps({'error': str(e)}),
                content_type='application/json',
                status=500,
                headers=get_cors_headers(request)
            )

    @http.route('/api/zillow/search', type='http', auth='none', methods=['GET'], csrf=False)
    def search_properties_new(self, **kwargs):
        logger = logging.getLogger(__name__)
        try:
            # Immediately return a response to the frontend
            return Response(
                json.dumps({
                    'success': True,
                    'background_fetching': True,
                    'message': 'Your request is being processed in the background.'
                }),
                content_type='application/json',
                status=202,  # HTTP 202 Accepted
                headers=get_cors_headers(request)
            )

            location_id = kwargs.get('locationId')
            address = kwargs.get('address', '').strip()
            location = kwargs.get('location', '').strip()

            # Log all incoming parameters
            logger.info(f"[Zillow Search] All incoming parameters: {json.dumps(kwargs)}")

            if not location_id:
                logger.error("[Zillow Search] locationId is required")
                return self._error_response('locationId is required')

            # Get location details
            ghl_location = request.env['ghl.location'].sudo().search([('location_id', '=', location_id)], limit=1)
            if not ghl_location or not ghl_location.market_location_id:
                logger.error(f"[Zillow Search] Invalid or unlinked locationId: {location_id}")
                return self._error_response('Invalid or unlinked locationId')

            # Get ZIP codes
            allowed_zipcodes = ghl_location.market_location_id.zipcode_ids.mapped('zip_code')
            if not allowed_zipcodes:
                logger.error(f"[Zillow Search] No ZIP codes configured for location: {location_id}")
                return self._error_response('No ZIP codes configured for this location')

            # Get RapidAPI credentials
            api_host, api_key = self._get_rapidapi_keys()
            headers = {'x-rapidapi-host': api_host, 'x-rapidapi-key': api_key}

            # Determine search status based on listing type or home status
            listing_type = kwargs.get('listing_type', '').lower()
            home_status = kwargs.get('home_status', '').upper()

            if listing_type == 'for_rent' or home_status == 'FOR_RENT':
                status = 'forRent'
            elif listing_type == 'sold' or home_status == 'SOLD':
                status = 'sold'
            else:
                status = 'forSale'

            logger.info(f"[Zillow Search] Using status: {status}")

            all_properties = []
            seen_zpids = set()

            # Loop through all allowed zipcodes
            for zipcode in allowed_zipcodes:
                rapidapi_params = {
                    'location': zipcode,
                    'output': 'json',
                    'status': status,
                    'sortSelection': 'priorityscore',
                    'listing_type': 'by_agent',
                    'doz': 'any'
                }
                if kwargs.get('page'):
                    rapidapi_params['page'] = kwargs['page']
                if kwargs.get('page_size'):
                    rapidapi_params['page_size'] = kwargs['page_size']
                logger.info(f"[Zillow Search] Calling /search for zipcode {zipcode} with params: {rapidapi_params}")
                for attempt in range(3):  # Try up to 3 times
                    try:
                        response = requests.get(f'https://{api_host}/search', headers=headers, params=rapidapi_params)
                        response.raise_for_status()
                        data = response.json()
                        properties_data = data.get('results', []) if isinstance(data, dict) else []
                        logger.info(f"[Zillow Search] Found {len(properties_data)} properties for zipcode {zipcode}")
                        # Deduplicate by zpid
                        for prop in properties_data:
                            zpid = prop.get('zpid')
                            if zpid and zpid not in seen_zpids:
                                all_properties.append(prop)
                                seen_zpids.add(zpid)
                        break  # Success, break out of retry loop
                    except Exception as e:
                        logger.error(
                            f"[Zillow Search] Error fetching properties for zipcode {zipcode} (attempt {attempt + 1}): {str(e)}",
                            exc_info=True)
                        if attempt < 2:
                            logger.info(f"[Zillow Search] Waiting 5 seconds before retrying zipcode {zipcode}")
                            time.sleep(5)  # Wait longer if rate limited
                        else:
                            logger.info(f"[Zillow Search] Giving up on zipcode {zipcode} after 3 attempts.")
                    # No need to continue if successful
                time.sleep(1)  # Add a 1-second delay between requests

            logger.info(f"[Zillow Search] Total unique properties found: {len(all_properties)}")

            # Create/update properties
            property_ids = self._create_zillow_properties(all_properties, allowed_zipcodes)

            return self._build_properties_response(property_ids)

        except Exception as e:
            logger.error(f"[Zillow Search] Error in search_properties_new: {str(e)}", exc_info=True)
            return self._error_response(str(e), status=500)

    def _build_search_query_state(self, kwargs, allowed_zipcodes, city=None, state_abbr=None):
        zipcode = allowed_zipcodes[0]
        filter_state = {
            "sort": {"value": "globalrelevanceex"}
        }

        # Map home_status or listing_type to correct filterState key
        home_status = kwargs.get('home_status')
        listing_type = kwargs.get('listing_type')
        if not home_status and listing_type:
            if listing_type.lower() == 'for_rent':
                home_status = 'FOR_RENT'
            elif listing_type.lower() == 'sold':
                home_status = 'SOLD'
            else:
                home_status = 'FOR_SALE'
        if not home_status:
            home_status = 'FOR_SALE'

        # Set correct filterState key
        if home_status == 'FOR_RENT':
            filter_state['fr'] = {'value': True}
        elif home_status == 'SOLD':
            filter_state['sold'] = {'value': True}
        else:
            filter_state['fsba'] = {'value': True}

        # Price filters
        min_price = kwargs.get('min_price')
        max_price = kwargs.get('max_price')
        if min_price:
            filter_state['price'] = {'min': float(min_price)}
        if max_price:
            filter_state['price'] = filter_state.get('price', {})
            filter_state['price']['max'] = float(max_price)

        # Bedrooms filter
        bedrooms = kwargs.get('bedrooms')
        if bedrooms:
            filter_state['beds'] = {'min': int(bedrooms)}

        # Bathrooms filter
        bathrooms = kwargs.get('bathrooms')
        if bathrooms:
            filter_state['baths'] = {'min': float(bathrooms)}

        # Living Area (sqft) filters
        sqft_min = kwargs.get('sqft_min')
        sqft_max = kwargs.get('sqft_max')
        if sqft_min:
            filter_state['sqft'] = {'min': float(sqft_min)}
        if sqft_max:
            filter_state['sqft'] = filter_state.get('sqft', {})
            filter_state['sqft']['max'] = float(sqft_max)

        # Lot Area filters
        lot_min = kwargs.get('lot_min')
        lot_max = kwargs.get('lot_max')
        if lot_min:
            filter_state['lot'] = {'min': float(lot_min)}
        if lot_max:
            filter_state['lot'] = filter_state.get('lot', {})
            filter_state['lot']['max'] = float(lot_max)

        # Year Built filters
        year_min = kwargs.get('year_min')
        year_max = kwargs.get('year_max')
        if year_min:
            filter_state['yearBuilt'] = {'min': int(year_min)}
        if year_max:
            filter_state['yearBuilt'] = filter_state.get('yearBuilt', {})
            filter_state['yearBuilt']['max'] = int(year_max)

        # Home Type filter - using Zillow's actual filter keys
        home_type = kwargs.get('home_type')
        if home_type:
            if isinstance(home_type, list):
                for t in home_type:
                    if t and t.lower() != 'nan':
                        key = self._get_home_type_key(t)
                        if key:
                            filter_state[key] = {'value': True}
            elif home_type.lower() != 'nan':
                key = self._get_home_type_key(home_type)
                if key:
                    filter_state[key] = {'value': True}

        # Build the location string
        location_str = f"{city}, {state_abbr}" if city and state_abbr else zipcode

        state = {
            "pagination": {},
            "isMapVisible": True,
            "filterState": filter_state,
            "isListVisible": True,
            "usersSearchTerm": location_str,
            "regionSelection": [{"regionId": int(zipcode), "regionType": 6}],  # Changed to 6 for city search
            "category": "cat1"  # Added category as seen in Zillow's URL
        }

        # Add mapBounds if city and state are available
        if city and state_abbr:
            # Get the zipcode record to get lat/long bounds
            zipcode_rec = request.env['us.zipcode.reference'].sudo().search([('zip', '=', zipcode)], limit=1)
            if zipcode_rec and zipcode_rec.latitude and zipcode_rec.longitude:
                # Create a bounding box around the zipcode (approximately 2 mile radius)
                lat_offset = 0.029  # roughly 2 miles in latitude
                lon_offset = 0.029  # roughly 2 miles in longitude
                state["mapBounds"] = {
                    "west": float(zipcode_rec.longitude) - lon_offset,
                    "east": float(zipcode_rec.longitude) + lon_offset,
                    "south": float(zipcode_rec.latitude) - lat_offset,
                    "north": float(zipcode_rec.latitude) + lat_offset
                }

        return state

    def _build_zillow_url(self, searchQueryState, path='/homes/for_sale/2_p/'):
        logger = logging.getLogger(__name__)

        # Get the search location details
        users_search_term = searchQueryState.get('usersSearchTerm', '')
        region_selection = searchQueryState.get('regionSelection', [{}])[0]

        # Format the URL slug based on the search term
        if users_search_term:
            # Extract city and state if available
            parts = users_search_term.lower().split(',')
            if len(parts) >= 2:
                city = parts[0].strip()
                state = parts[1].strip().split()[0]  # Get state abbreviation
                url_slug = f"{city}-{state}"
                base_path = f"/{url_slug}/"
            else:
                # Default to homes/for_rent if we can't parse city-state
                base_path = '/homes/for_rent/'
        else:
            base_path = '/homes/for_rent/'

        logger.info(f"[Zillow URL Builder] Using base path: {base_path}")

        base_url = f'https://www.zillow.com{base_path}'
        sqs_json = json.dumps(searchQueryState, separators=(',', ':'))
        params = {'searchQueryState': sqs_json}
        final_url = base_url + '?' + urllib.parse.urlencode(params)
        logger.info(f"[Zillow URL Builder] Final URL: {final_url}")
        return final_url

    def _get_rapidapi_keys(self):
        ICPSudo = request.env['ir.config_parameter'].sudo()
        api_host = ICPSudo.get_param('web_scraper.rapidapi_host', 'zillow56.p.rapidapi.com')
        api_key = ICPSudo.get_param('web_scraper.rapidapi_key')
        return api_host, api_key

    def _call_rapidapi(self, zillow_url, api_host, api_key):
        headers = {'x-rapidapi-host': api_host, 'x-rapidapi-key': api_key}
        rapidapi_url = f'https://{api_host}/search_url'
        rapidapi_params = {
            'url': zillow_url,
            'page': 1,
            'output': 'json',
            'listing_type': 'by_agent',
            'page_size': 100
        }
        logging.info(f"[Zillow Search] Calling /search_url with params: {rapidapi_params}")
        response = requests.get(rapidapi_url, headers=headers, params=rapidapi_params)
        logging.info(f"[Zillow Search] RapidAPI /search_url status: {response.status_code}")
        response.raise_for_status()
        data = response.json()
        logging.info(f"[Zillow Search] RapidAPI /search_url response: {data}")
        return data.get('results', []) if isinstance(data, dict) else []

    def _create_zillow_properties(self, properties_data, allowed_zipcodes):
        logger = logging.getLogger(__name__)
        created_properties = []
        for property_data in properties_data:
            address_data = property_data.get('address', {})
            zipcode = address_data.get('zipcode') or address_data.get('zip_code')
            if not zipcode and allowed_zipcodes:
                zipcode = allowed_zipcodes[0]
            if zipcode not in allowed_zipcodes:
                logger.info(
                    f"Skipping property {property_data.get('zpid')} because zipcode {zipcode} not in allowed_zipcodes {allowed_zipcodes}")
                continue
            zpid = property_data.get('zpid')
            if not zpid:
                logger.info(f"Skipping property with missing zpid: {property_data}")
                continue
            existing_property = request.env['zillow.property'].sudo().search([('zpid', '=', zpid)], limit=1)
            if not existing_property:
                logger.info(f"Creating property with zpid {zpid}")
                vals = {
                    'zpid': zpid,
                    'street_address': address_data.get('streetAddress'),
                    'city': address_data.get('city'),
                    'state': address_data.get('state'),
                    'zipcode': zipcode,
                    'price': float(property_data['price']) if property_data.get('price') else False,
                    'bedrooms': int(property_data['bedrooms']) if property_data.get('bedrooms') else False,
                    'bathrooms': float(property_data['bathrooms']) if property_data.get('bathrooms') else False,
                    'living_area': float(property_data['livingArea']) if property_data.get('livingArea') else False,
                    'home_status': property_data.get('homeStatus'),
                    'home_type': property_data.get('homeType'),
                }
                created = request.env['zillow.property'].sudo().create(vals)
                created_properties.append(created.id)
            else:
                logger.info(f"Property with zpid {zpid} already exists, skipping creation")
                created_properties.append(existing_property.id)
        return created_properties

    def _build_properties_response(self, property_ids):
        properties = request.env['zillow.property'].sudo().browse(property_ids).read([
            'id', 'zpid', 'street_address', 'city', 'state', 'price',
            'bedrooms', 'bathrooms', 'living_area', 'home_status', 'home_type',
            'sent_to_cyclsales_count', 'zipcode'])
        return Response(
            json.dumps({
                'properties': properties,
                'total_results': len(properties),
                'page': 1,
                'page_size': 100,
                'total_pages': 1
            }),
            content_type='application/json',
            headers=get_cors_headers(request)
        )

    def _error_response(self, message, status=400):
        return Response(
            json.dumps({'error': message}),
            content_type='application/json',
            status=status,
            headers=get_cors_headers(request)
        )

    def _fetch_properties_from_api(self, allowed_zipcodes):
        """Helper method to fetch properties from the API for given zipcodes"""
        ICPSudo = request.env['ir.config_parameter'].sudo()
        api_host = ICPSudo.get_param('web_scraper.rapidapi_host', 'zillow56.p.rapidapi.com')
        api_key = ICPSudo.get_param('web_scraper.rapidapi_key')

        if not api_key:
            return False

        headers = {
            'x-rapidapi-host': api_host,
            'x-rapidapi-key': api_key
        }

        for zipcode in allowed_zipcodes:
            try:
                # Check existing properties for this zipcode
                existing_count = request.env['zillow.property'].sudo().search_count([('zipcode', '=', zipcode)])
                print(f"Found {existing_count} existing properties for zipcode {zipcode}")

                # Only fetch from API if we have less than 5 properties
                if existing_count < 5:
                    properties_needed = 5 - existing_count
                    print(f"Need to fetch {properties_needed} more properties for zipcode {zipcode}")
                    try:
                        rapidapi_url = f'https://{api_host}/search'
                        params = {
                            'location': zipcode,
                            'output': 'json',
                            'status': 'forSale',
                            'sortSelection': 'priorityscore',
                            'listing_type': 'by_agent',
                            'doz': 'any'
                        }

                        response = requests.get(rapidapi_url, headers=headers, params=params)
                        response.raise_for_status()
                        data = response.json()

                        # Extract properties from the response
                        properties_data = []
                        if isinstance(data, dict):
                            if 'results' in data:
                                properties_data = data['results']
                            elif 'searchResults' in data:
                                properties_data = data['searchResults'].get('listResults', [])

                        print(f"Found {len(properties_data)} properties in API response for zipcode {zipcode}")

                        # Get all zpids from the response
                        zpids = [p.get('zpid') for p in properties_data if p.get('zpid')]

                        # Check for existing property details and properties
                        existing_details = request.env['zillow.property.detail'].sudo().search(
                            [('zpid', 'in', zpids)])
                        existing_properties = request.env['zillow.property'].sudo().search(
                            [('zpid', 'in', zpids)])

                        # Get sets of existing zpids
                        existing_detail_zpids = set(existing_details.mapped('zpid'))
                        existing_property_zpids = set(existing_properties.mapped('zpid'))

                        # Filter out properties that already exist
                        properties_data = [
                            p for p in properties_data
                            if p.get('zpid')
                               and p.get('zpid') not in existing_detail_zpids
                               and p.get('zpid') not in existing_property_zpids
                        ]

                        print(
                            f"After filtering existing properties, {len(properties_data)} properties remain for zipcode {zipcode}")

                        # Process properties until we have enough
                        properties_processed = 0
                        for property_data in properties_data:
                            if properties_processed >= properties_needed:
                                break

                            # Skip if no zpid (invalid property)
                            if not property_data.get('zpid'):
                                print(f"Skipping property without zpid for zipcode {zipcode}")
                                continue

                            zpid = property_data.get('zpid')

                            try:
                                # Double check property doesn't exist (race condition protection)
                                existing_property = request.env['zillow.property'].sudo().search(
                                    [('zpid', '=', zpid)], limit=1)
                                if existing_property:
                                    print(f"Property with zpid {zpid} already exists, skipping")
                                    continue

                                address_data = property_data.get('address', {})
                                vals = {
                                    'zpid': zpid,
                                    'street_address': address_data.get('streetAddress'),
                                    'city': address_data.get('city'),
                                    'state': address_data.get('state'),
                                    'zipcode': zipcode,
                                    'price': float(property_data['price']) if property_data.get(
                                        'price') else False,
                                    'bedrooms': int(property_data['bedrooms']) if property_data.get(
                                        'bedrooms') else False,
                                    'bathrooms': float(property_data['bathrooms']) if property_data.get(
                                        'bathrooms') else False,
                                    'living_area': float(property_data['livingArea']) if property_data.get(
                                        'livingArea') else False,
                                    'home_status': property_data.get('homeStatus'),
                                    'home_type': property_data.get('homeType'),
                                }

                                # Create the property
                                request.env['zillow.property'].sudo().create(vals)

                                properties_processed += 1

                            except Exception as e:
                                print(f"Error processing property data for zipcode {zipcode}: {str(e)}")
                                continue
                    except Exception as e:
                        print(f"Error fetching data from API for zipcode {zipcode}: {str(e)}")
                        continue
                else:
                    print(f"Already have enough properties ({existing_count}) for zipcode {zipcode}")

            except Exception as e:
                print(f"Error processing zipcode {zipcode}: {str(e)}")
                continue

        return True

    def _get_home_type_key(self, home_type):
        """Map home types to Zillow's filter keys"""
        home_type_map = {
            'house': 'hhomeType',
            'houses': 'hhomeType',
            'apartment': 'apartmentType',
            'apartments': 'apartmentType',
            'townhouse': 'townhouseType',
            'townhomes': 'townhouseType',
            'condo': 'condoType',
            'condos': 'condoType',
            'manufactured': 'manufacturedType',
            'lot': 'lotType',
            'land': 'lotType',
            'multi-family': 'multiFamily'
        }
        return home_type_map.get(home_type.lower())


class CORSPreflightController(http.Controller):
    @route(['/api/zillow/<path:anything>'], type='http', auth='none', methods=['OPTIONS'], csrf=False)
    def cors_preflight(self, **kwargs):
        return Response(
            "",
            status=200,
            headers=get_cors_headers(request)
        )
