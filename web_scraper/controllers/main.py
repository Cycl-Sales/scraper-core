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

            # Get total count first
            total_count = request.env['zillow.property'].sudo().search_count(domain)

            # Check each zipcode and fetch data if needed
            ICPSudo = request.env['ir.config_parameter'].sudo()
            api_host = ICPSudo.get_param('web_scraper.rapidapi_host', 'zillow56.p.rapidapi.com')
            api_key = ICPSudo.get_param('web_scraper.rapidapi_key')

            if not api_key:
                return Response(
                    json.dumps({'error': 'RapidAPI key is not configured.'}),
                    content_type='application/json',
                    status=500,
                    headers=[('Access-Control-Allow-Origin', '*')]
                )

            headers = {
                'x-rapidapi-host': api_host,
                'x-rapidapi-key': api_key
            }
            print("api_key", api_key)
            for zipcode in allowed_zipcodes:
                try:
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
                                        print(
                                            f"Successfully processed property {properties_processed} for zipcode {zipcode}")

                                    except Exception as e:
                                        print(f"Error processing property data for zipcode {zipcode}: {str(e)}")
                                        continue

                            except Exception as e:
                                print(f"Error fetching data from API for zipcode {zipcode}: {str(e)}")
                                continue
                        else:
                            print(f"Already have enough properties ({existing_count}) for zipcode {zipcode}")

                    except Exception as e:
                        # Rollback the zipcode transaction
                        print(f"Error in main zipcode processing for {zipcode}: {str(e)}")
                        continue

                except Exception as e:
                    print(f"Error creating cursor for zipcode {zipcode}: {str(e)}")
                    continue

            # Recalculate total count after fetching new data
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
                        zproperty['home_type'] = zdetail.home_type.replace('_',
                                                                           ' ').title() if zdetail.home_type else ''
                        zproperty['hi_res_image_link'] = zdetail.hi_res_image_link
                        zproperty['hdp_url'] = zdetail.hdp_url
                        # Refactored: Get listing agent from agent_ids where associated_agent_type == 'listAgent'
                        listing_agent = zdetail.agent_ids.filtered(lambda a: a.associated_agent_type == 'listAgent')
                        if listing_agent:
                            agent = listing_agent[0]
                            zproperty['listingAgent'] = {
                                'name': agent.member_full_name or '',
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
    def search_properties(self, **kwargs):
        logger = logging.getLogger(__name__)
        try:
            ICPSudo = request.env['ir.config_parameter'].sudo()
            api_host = ICPSudo.get_param('web_scraper.rapidapi_host', 'zillow56.p.rapidapi.com')
            api_key = ICPSudo.get_param('web_scraper.rapidapi_key')

            address = kwargs.get('address', '').strip()
            location = kwargs.get('location', '').strip()
            logger.info(f"[Zillow Search] Incoming params: address='{address}', location='{location}'")

            if not api_key:
                logger.error("[Zillow Search] RapidAPI key missing!")
                return Response(
                    json.dumps({'error': 'RapidAPI key is not configured.'}),
                    content_type='application/json',
                    status=500,
                    headers=[('Access-Control-Allow-Origin', '*')]
                )

            # Try address search first if address is provided
            if address:
                try:
                    rapidapi_url = f'https://{api_host}/search_address'
                    params = {'address': address}
                    headers = {
                        'x-rapidapi-host': api_host,
                        'x-rapidapi-key': api_key
                    }
                    logger.info(f"[Zillow Search] Calling /search_address with params: {params}")
                    response = requests.get(rapidapi_url, headers=headers, params=params)
                    logger.info(f"[Zillow Search] RapidAPI /search_address status: {response.status_code}")
                    response.raise_for_status()
                    data = response.json()
                    logger.info(f"[Zillow Search] RapidAPI /search_address response: {data}")

                    # If data is valid and has a zpid or address, treat as a successful address search
                    if data and (data.get('zpid') or data.get('address')):
                        # --- Create or update zillow.property record ---
                        zpid = data.get('zpid') or address
                        address_data = data.get('address', {})
                        vals = {
                            'zpid': zpid,
                            'street_address': address_data.get('streetAddress'),
                            'city': address_data.get('city'),
                            'state': address_data.get('state'),
                            'zipcode': address_data.get('zipcode'),
                            'price': float(data['price']) if data.get('price') else False,
                            'bedrooms': int(data['bedrooms']) if data.get('bedrooms') else False,
                            'bathrooms': float(data['bathrooms']) if data.get('bathrooms') else False,
                            'living_area': float(data['livingArea']) if data.get('livingArea') else False,
                            'lot_area_value': float(data['lotSize']) if data.get('lotSize') else False,
                            'home_status': data.get('homeStatus'),
                            'home_type': data.get('homeType'),
                            'latitude': float(data['latitude']) if data.get('latitude') else False,
                            'longitude': float(data['longitude']) if data.get('longitude') else False,
                            'zestimate': float(data['zestimate']) if data.get('zestimate') else False,
                            'rent_zestimate': float(data['rentZestimate']) if data.get('rentZestimate') else False,
                            'tax_assessed_value': float(data['taxAssessedValue']) if data.get(
                                'taxAssessedValue') else False,
                            'time_on_zillow': data.get('timeOnZillow'),
                            'days_on_zillow': int(data['daysOnZillow']) if data.get('daysOnZillow') else False,
                            'price_change': float(data['priceChange']) if data.get('priceChange') else False,
                            'date_price_changed': data.get('datePriceChanged'),
                            'provider_listing_id': data.get('providerListingID'),
                            'hi_res_image_link': data.get('hiResImageLink'),
                            'hdp_url': data.get('hdpUrl'),
                        }
                        vals.update({
                            'is_featured': data.get('isFeatured', False),
                            'is_non_owner_occupied': data.get('isNonOwnerOccupied', False),
                            'is_preforeclosure_auction': data.get('isPreforeclosureAuction', False),
                            'is_premier_builder': data.get('isPremierBuilder', False),
                            'is_showcase_listing': data.get('isShowcaseListing', False),
                            'is_unmappable': data.get('isUnmappable', False),
                            'is_zillow_owned': data.get('isZillowOwned', False),
                            'is_fsba': data.get('isFSBA', False),
                            'is_for_auction': data.get('isForAuction', False),
                            'is_new_home': data.get('isNewHome', False),
                            'is_open_house': data.get('isOpenHouse', False),
                        })
                        property_obj = request.env['zillow.property'].sudo().search([('zpid', '=', vals['zpid'])],
                                                                                    limit=1)
                        if property_obj:
                            property_obj.write(vals)
                            logger.info(f"[Zillow Search] Updated zillow.property {vals['zpid']}")
                        else:
                            property_obj = request.env['zillow.property'].sudo().create(vals)
                            logger.info(f"[Zillow Search] Created zillow.property {vals['zpid']}")

                        # --- Handle listingAgents ---
                        # Find or create property detail
                        property_detail = request.env['zillow.property.detail'].sudo().search([('zpid', '=', zpid)],
                                                                                              limit=1)
                        if not property_detail and property_obj:
                            property_detail = request.env['zillow.property.detail'].sudo().search(
                                [('property_id', '=', property_obj.id)], limit=1)
                        listing_agents = data.get('listingAgents', [])
                        main_listing_agent = None
                        if property_detail:
                            # Remove old agents
                            property_detail.agent_ids.unlink()
                            for agent in listing_agents:
                                agent_rec = request.env['zillow.property.agent'].sudo().create({
                                    'property_id': property_detail.id,
                                    'associated_agent_type': agent.get('associatedAgentType'),
                                    'member_full_name': agent.get('memberFullName'),
                                    'member_state_license': agent.get('memberStateLicense'),
                                })
                                if not main_listing_agent and agent.get(
                                        'associatedAgentType') == 'listAgent' and agent.get('memberFullName'):
                                    main_listing_agent = agent_rec
                            if main_listing_agent:
                                property_detail.listing_agent_id = main_listing_agent.id
                        # Prepare agent info for response
                        agent_info = None
                        if main_listing_agent:
                            agent_info = {
                                'id': main_listing_agent.id,
                                'property_id': main_listing_agent.property_id.id,
                                'name': main_listing_agent.member_full_name,
                                'license_number': main_listing_agent.member_state_license,
                                'agent_type': main_listing_agent.associated_agent_type,
                            }
                        return Response(
                            json.dumps(
                                {'success': True, 'properties': [data], 'type': 'address', 'listingAgent': agent_info}),
                            content_type='application/json',
                            headers=[('Access-Control-Allow-Origin', '*')]
                        )
                except Exception as e:
                    logger.warning(
                        f"[Zillow Search] /search_address failed or returned no data: {str(e)}. Falling back to general search.")
                # If address search fails or returns no data, fall through to general search

            # Fallback: use /search for general location/domain
            if location:
                try:
                    rapidapi_url = f'https://{api_host}/search'
                    params = {
                        'location': location,
                        'output': 'json',
                        'status': kwargs.get('status', 'forSale'),
                        'sortSelection': kwargs.get('sortSelection', 'priorityscore'),
                        'listing_type': kwargs.get('listing_type', 'by_agent'),
                        'doz': kwargs.get('doz', 'any')
                    }
                    headers = {
                        'x-rapidapi-host': api_host,
                        'x-rapidapi-key': api_key
                    }
                    logger.info(f"[Zillow Search] Calling /search with params: {params}")
                    response = requests.get(rapidapi_url, headers=headers, params=params)
                    logger.info(f"[Zillow Search] RapidAPI /search status: {response.status_code}")
                    response.raise_for_status()
                    data = response.json()
                    logger.info(f"[Zillow Search] RapidAPI /search response: {data}")
                    properties = data.get('results', []) if isinstance(data, dict) else []
                    return Response(
                        json.dumps({'success': True, 'properties': properties, 'type': 'search'}),
                        content_type='application/json',
                        headers=[('Access-Control-Allow-Origin', '*')]
                    )
                except Exception as e:
                    logger.error(f"[Zillow Search] RapidAPI /search error: {str(e)}")
                    return Response(
                        json.dumps({'error': f'RapidAPI /search error: {str(e)}'}),
                        content_type='application/json',
                        status=500,
                        headers=[('Access-Control-Allow-Origin', '*')]
                    )
            logger.warning("[Zillow Search] No address or location provided, or both searches failed.")
            return Response(
                json.dumps({'error': 'No address or location provided, or no results found.'}),
                content_type='application/json',
                status=400,
                headers=[('Access-Control-Allow-Origin', '*')]
            )
        except Exception as e:
            logger.error(f"[Zillow Search] Fatal error: {str(e)}")
            return Response(
                json.dumps({'error': f'Fatal error: {str(e)}'}),
                content_type='application/json',
                status=500,
                headers=[('Access-Control-Allow-Origin', '*')]
            )
