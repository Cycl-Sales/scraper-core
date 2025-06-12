from odoo import http
from odoo.http import request, Response
import json
import requests
import urllib.parse
from odoo.fields import Datetime
import logging


class ZillowPropertyController(http.Controller):
    @http.route('/api/zillow/properties', type='http', auth='user', cors='*', csrf=False)
    def get_properties(self, **kwargs):
        try:
            # Get locationId from request
            location_id = kwargs.get('locationId')
            if not location_id:
                return Response(
                    json.dumps({'error': 'locationId is required'}),
                    content_type='application/json',
                    status=400,
                    headers=[('Access-Control-Allow-Origin', '*')]
                )

            # Find the GHL location record
            ghl_location = request.env['ghl.location'].sudo().search([('location_id', '=', location_id)], limit=1)
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
                 'sent_to_cyclsales_count', 'zipcode'],
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

            # For each property, attach its detail record (if any)
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

    @http.route('/api/zillow/property/send-to-cyclsales', type='http', auth='user', methods=['POST'], cors='*',
                csrf=False)
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
    def search_properties_new(self, **kwargs):
        logger = logging.getLogger(__name__)
        try:
            location_id = kwargs.get('locationId')
            address = kwargs.get('address', '').strip()
            location = kwargs.get('location', '').strip()
            # If address is empty, use locationId as location
            if not address and not location and location_id:
                location = location_id
            ghl_location = request.env['ghl.location'].sudo().search([('location_id', '=', location_id)], limit=1)
            print("ghl_location", ghl_location)
            allowed_zipcodes = ghl_location.market_location_id.zipcode_ids.mapped(
                'zip_code') if ghl_location and ghl_location.market_location_id else []
            print("Allowed Zipcodes: ", allowed_zipcodes)
            logger.info(f"[Zillow Search] Starting search for location_id: {location_id}")
            logger.info(f"[Zillow Search] Found {len(allowed_zipcodes)} allowed zipcodes: {allowed_zipcodes}")

            # Only error if ALL are missing
            if not address and not location and not allowed_zipcodes:
                logger.warning("[Zillow Search] No address, location, or allowed zipcodes provided.")
                return self._error_response("No address, location, or allowed zipcodes provided, or no results found.")

            if not location_id:
                logger.error("[Zillow Search] locationId is required")
                return self._error_response('locationId is required')
            if not ghl_location or not ghl_location.market_location_id:
                logger.error(f"[Zillow Search] Invalid or unlinked locationId: {location_id}")
                return self._error_response('Invalid or unlinked locationId')
            if not allowed_zipcodes:
                logger.error(f"[Zillow Search] No ZIP codes configured for location: {location_id}")
                return self._error_response('No ZIP codes configured for this location')

            # Get RapidAPI credentials
            api_host, api_key = self._get_rapidapi_keys()
            headers = {'x-rapidapi-host': api_host, 'x-rapidapi-key': api_key}
            rapidapi_url = f'https://{api_host}/search_url'

            all_property_ids = []
            page = int(kwargs.get('page', 1))
            page_size = int(kwargs.get('page_size', 100))
            properties_per_zipcode = max(1, page_size // len(allowed_zipcodes))

            logger.info(
                f"[Zillow Search] Search parameters - Page: {page}, Page Size: {page_size}, Properties per zipcode: {properties_per_zipcode}")

            # Search through each zipcode
            for index, zipcode in enumerate(allowed_zipcodes, 1):
                try:
                    logger.info(f"[Zillow Search] Processing zipcode {index}/{len(allowed_zipcodes)}: {zipcode}")

                    # Build search query state for this zipcode
                    searchQueryState = self._build_search_query_state(kwargs, [zipcode])
                    # Add mapBounds if provided
                    # if kwargs.get('west') and kwargs.get('east') and kwargs.get('south') and kwargs.get('north'):
                    #     searchQueryState['mapBounds'] = {
                    #         'west': float(kwargs['west']),
                    #         'east': float(kwargs['east']),
                    #         'south': float(kwargs['south']),
                    #         'north': float(kwargs['north']),
                    #     }
                    zillow_url = self._build_zillow_url(searchQueryState, path='/homes/for_sale/2_p/')
                    logger.info(f"[Zillow Search] Generated Zillow URL for zipcode {zipcode}: {zillow_url}")

                    # Call RapidAPI with the constructed URL
                    rapidapi_params = {
                        'url': zillow_url,
                        'page': page,
                        'output': 'json',
                        'listing_type': 'by_agent',
                        'page_size': properties_per_zipcode
                    }
                    logger.info(
                        f"[Zillow Search] Calling /search_url for zipcode {zipcode} with params: {rapidapi_params}")
                    response = requests.get(rapidapi_url, headers=headers, params=rapidapi_params)
                    logger.info(
                        f"[Zillow Search] RapidAPI /search_url status for zipcode {zipcode}: {response.status_code}")
                    response.raise_for_status()
                    data = response.json()

                    # Process the response for this zipcode
                    properties_data = data.get('results', []) if isinstance(data, dict) else []
                    logger.info(f"[Zillow Search] Found {len(properties_data)} properties for zipcode {zipcode}")

                    property_ids = self._create_zillow_properties(properties_data, [zipcode])
                    logger.info(f"[Zillow Search] Created/Updated {len(property_ids)} properties for zipcode {zipcode}")
                    all_property_ids.extend(property_ids)

                except Exception as e:
                    logger.error(f"[Zillow Search] Error processing zipcode {zipcode}: {str(e)}", exc_info=True)
                    continue

            logger.info(f"[Zillow Search] Completed search. Total properties found: {len(all_property_ids)}")
            # Return combined results
            return self._build_properties_response(all_property_ids)

        except Exception as e:
            logger.error(f"[Zillow Search] Error in search_properties_new: {str(e)}", exc_info=True)
            return self._error_response(str(e), status=500)

    def _build_search_query_state(self, kwargs, allowed_zipcodes):
        # Use frontend map bounds if provided, otherwise use defaults from the cURL sample
        map_bounds = {
            "west": float(kwargs.get('west', -112.39143704189931)),
            "east": float(kwargs.get('east', -110.78468655361806)),
            "south": float(kwargs.get('south', 32.79032628812945)),
            "north": float(kwargs.get('north', 33.7227901388417))
        }
        state = {
            "pagination": {"currentPage": int(kwargs.get('page', 1))},
            "mapBounds": map_bounds,
            "isMapVisible": True,
            "filterState": {
                "con": {"value": False},
                "apa": {"value": False},
                "mf": {"value": False},
                "ah": {"value": True},
                "sort": {"value": "globalrelevanceex"},
                "land": {"value": False},
                "manu": {"value": False},
                "apco": {"value": False}
            },
            "isListVisible": True
        }
        return state

    def _build_zillow_url(self, searchQueryState, path='/homes/for_sale/2_p/'):
        base_url = f'https://www.zillow.com{path}'
        sqs_json = json.dumps(searchQueryState, separators=(',', ':'))
        params = {'searchQueryState': sqs_json}
        return base_url + '?' + urllib.parse.urlencode(params)

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
        created_properties = []
        for property_data in properties_data:
            address_data = property_data.get('address', {})
            zipcode = address_data.get('zipcode') or address_data.get('zip_code')
            if not zipcode and allowed_zipcodes:
                zipcode = allowed_zipcodes[0]
            if zipcode not in allowed_zipcodes:
                continue
            zpid = property_data.get('zpid')
            if not zpid:
                continue
            existing_property = request.env['zillow.property'].sudo().search([('zpid', '=', zpid)], limit=1)
            if not existing_property:
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
            headers=[('Access-Control-Allow-Origin', '*')]
        )

    def _error_response(self, message, status=400):
        return Response(
            json.dumps({'error': message}),
            content_type='application/json',
            status=status,
            headers=[('Access-Control-Allow-Origin', '*')]
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
