from odoo import http
from odoo.http import request, Response
import json
import logging
import requests
from odoo.fields import Datetime
from datetime import datetime, timedelta
from .cors_utils import get_cors_headers
from odoo.addons.web_scraper.controllers.cors_utils import get_cors_headers
from odoo.fields import Datetime, Date
import time

_logger = logging.getLogger(__name__)


def get_all_custom_fields(location_access_token):
    """Fetches all custom fields for a given location."""
    _logger.info("Fetching all custom fields from GHL...")
    custom_fields_url = "https://services.leadconnectorhq.com/customFields/"
    headers = {
        'Accept': 'application/json',
        'Authorization': f'Bearer {location_access_token}',
        'Version': '2021-07-28'
    }
    try:
        resp = requests.get(custom_fields_url, headers=headers, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        fields = data.get('customFields', [])
        _logger.info(f"Successfully fetched {len(fields)} custom fields.")
        return {field['name'].lower(): field['id'] for field in fields}
    except Exception as e:
        _logger.error(f"Failed to fetch custom fields: {e}")
        return {}


class ZillowPropertyController(http.Controller):

    @http.route('/api/zillow/properties', type='http', auth='none', methods=['GET'], csrf=False)
    def get_zillow_properties(self, **kwargs):
        try:
            # Get all Zillow property records with listing agent data
            properties = request.env['zillow.property.detail'].sudo().search_read([],
                                                                                  fields=['id', 'name', 'street',
                                                                                          'city', 'state', 'zip_code',
                                                                                          'price', 'bedrooms',
                                                                                          'bathrooms', 'square_feet',
                                                                                          'property_type',
                                                                                          'listing_status',
                                                                                          'hi_res_image_link',
                                                                                          'listing_agent_id', 'zpid',
                                                                                          'sent_by_current_user',
                                                                                          'sent_to_cyclsales_count'])

            # Add agent info to each property
            for prop in properties:
                prop['home_type'] = prop.get('home_type').replace('_', ' ').title() if prop.get('home_type') else ''
                agent = prop.get('listing_agent_id')
                agent_id = None
                if agent:
                    if isinstance(agent, (list, tuple)) and len(agent) >= 1:
                        agent_id = agent[0]
                    elif isinstance(agent, int):
                        agent_id = agent
                # if prop.get('id') == 2:
                _logger.info(f"[DEBUG] Property detail record id=2: {prop.get('id')}")
                if agent_id:
                    agent_rec = request.env['zillow.property.listing.agent'].sudo().browse(agent_id)
                    if agent_rec.exists():
                        prop['listingAgent'] = {
                            'id': agent_rec.id,
                            'property_id': agent_rec.property_id.id,
                            'name': agent_rec.display_name or '',
                            'business_name': agent_rec.business_name or '',
                            'phone': f"{agent_rec.phone_area_code or ''}-{agent_rec.phone_prefix or ''}-{agent_rec.phone_number or ''}",
                            'profile_url': agent_rec.profile_url or '',
                            'email': agent_rec.email or '',
                            'license_number': agent_rec.license_number or '',
                            'license_state': agent_rec.license_state or '',
                            'badge_type': agent_rec.badge_type or '',
                            'encoded_zuid': agent_rec.encoded_zuid or '',
                            'first_name': agent_rec.first_name or '',
                            'image_url': agent_rec.image_url or '',
                            'image_height': agent_rec.image_height,
                            'image_width': agent_rec.image_width,
                            'rating_average': agent_rec.rating_average,
                            'recent_sales': agent_rec.recent_sales,
                            'review_count': agent_rec.review_count,
                            'reviews_url': agent_rec.reviews_url or '',
                            'services_offered': agent_rec.services_offered or '',
                            'username': agent_rec.username or '',
                            'write_review_url': agent_rec.write_review_url or '',
                            'is_zpro': agent_rec.is_zpro,
                        }
                        if prop.get('id') == 2:
                            _logger.info(
                                f"[DEBUG] Attached agent info for property id=2: {json.dumps(prop['listingAgent'], default=str)}")
                    else:
                        prop['listingAgent'] = None
                else:
                    prop['listingAgent'] = None

            # Format the response
            response = {
                'status': 'success',
                'data': properties
            }

            return http.Response(
                json.dumps(response),
                content_type='application/json',
                status=200,
                headers=get_cors_headers(request)
            )

        except Exception as e:
            _logger.error(f"Error in get_zillow_properties: {str(e)}")
            return http.Response(
                json.dumps({
                    'status': 'error',
                    'message': str(e)
                }),
                content_type='application/json',
                status=500,
                headers=get_cors_headers(request)
            )

    @http.route('/api/zillow/send-to-cyclsales', type='http', auth='none', methods=['POST', 'OPTIONS'], cors='*', csrf=False)
    def send_to_cyclsales(self, **kwargs):
        if request.httprequest.method == 'OPTIONS':
            return http.Response(headers=get_cors_headers(request))
        try:
            _logger.info("=== Starting send_to_cyclsales process ===")

            # Get the raw request data
            raw_data = request.httprequest.get_data(as_text=True)
            _logger.info(f"[REQUEST] Raw request data: {raw_data}")

            # Parse the JSON data
            data = json.loads(raw_data)
            _logger.info(f"[REQUEST] Parsed request data: {data}")

            property_ids = data.get('property_ids', [])
            _logger.info(f"[REQUEST] Received property_ids: {property_ids}")

            if not property_ids:
                _logger.warning("[VALIDATION] No property IDs provided")
                return http.Response(
                    json.dumps({'success': False, 'error': 'No property IDs provided'}),
                    content_type='application/json',
                    status=400,
                    headers=get_cors_headers(request)
                )

            # Get location ID from request
            location_id = data.get('locationId')
            if not location_id:
                _logger.error("[CONFIG] No location ID provided in request")
                return http.Response(
                    json.dumps({
                        'success': False,
                        'error': 'Location ID is required. Please provide a valid location ID.'
                    }),
                    content_type='application/json',
                    status=400,
                    headers=get_cors_headers(request)
                )

            # Find the GHL location record
            ghl_location = request.env['ghl.location'].sudo().search([('location_id', '=', location_id)], limit=1)
            if not ghl_location:
                _logger.error(f"[CONFIG] No GHL location found for ID: {location_id}")
                return http.Response(
                    json.dumps({
                        'success': False,
                        'error': 'Invalid GHL location ID provided.'
                    }),
                    content_type='application/json',
                    status=400,
                    headers=get_cors_headers(request)
                )

            # Fetch properties from zillow.property model
            _logger.info(f"[FETCH] Attempting to fetch properties with IDs: {property_ids}")
            properties = request.env['zillow.property'].sudo().browse(property_ids)
            _logger.info(f"[FETCH] Found {len(properties)} properties")

            # Get API configuration from system parameters
            ICP = request.env['ir.config_parameter'].sudo()

            # Get the GHL agency token
            agency_token = request.env['ghl.agency.token'].sudo().search([], limit=1)
            if not agency_token:
                _logger.error("[CONFIG] No GHL agency token found")
                return http.Response(
                    json.dumps({
                        'success': False,
                        'error': 'No GHL agency token found. Please configure GHL OAuth integration first.'
                    }),
                    content_type='application/json',
                    status=500,
                    headers=get_cors_headers(request)
                )

            # Check if token is expired
            current_time = Datetime.now()
            token_expiry = agency_token.token_expiry
            _logger.info(f"[TOKEN] Current time: {current_time}, Token expiry: {token_expiry}")
            
            if token_expiry < current_time:
                _logger.error("[CONFIG] GHL agency token has expired")
                # Try to refresh the token
                try:
                    refresh_url = "https://services.leadconnectorhq.com/oauth/token"
                    refresh_payload = {
                        "client_id": agency_token.company_id,
                        "grant_type": "refresh_token",
                        "refresh_token": agency_token.refresh_token
                    }
                    refresh_headers = {
                        'Content-Type': 'application/json'
                    }
                    
                    _logger.info("[TOKEN] Attempting to refresh token...")
                    refresh_response = requests.post(refresh_url, json=refresh_payload, headers=refresh_headers)
                    
                    if refresh_response.status_code == 200:
                        refresh_data = refresh_response.json()
                        agency_token.write({
                            'access_token': refresh_data['access_token'],
                            'refresh_token': refresh_data['refresh_token'],
                            'token_expiry': Datetime.now() + timedelta(seconds=refresh_data['expires_in'])
                        })
                        _logger.info("[TOKEN] Successfully refreshed token")
                    else:
                        _logger.error(f"[TOKEN] Failed to refresh token: {refresh_response.text}")
                        return http.Response(
                            json.dumps({
                                'success': False,
                                'error': 'Failed to refresh GHL token. Please re-authenticate.'
                            }),
                            content_type='application/json',
                            status=500,
                            headers=get_cors_headers(request)
                        )
                except Exception as e:
                    _logger.error(f"[TOKEN] Error refreshing token: {str(e)}")
                    return http.Response(
                        json.dumps({
                            'success': False,
                            'error': 'Error refreshing GHL token. Please re-authenticate.'
                        }),
                        content_type='application/json',
                        status=500,
                        headers=get_cors_headers(request)
                    )

            agency_access_token = agency_token.access_token
            company_id = agency_token.company_id
            _logger.info(f"[TOKEN] Using agency token: {agency_access_token[:10]}...{agency_access_token[-10:] if len(agency_access_token) > 20 else ''}")
            _logger.info(f"[CONFIG] Using GHL agency token for location ID: {location_id}")

            # Step 1: Get location access token
            location_token_url = "https://services.leadconnectorhq.com/oauth/locationToken"
            location_token_headers = {
                "Accept": "application/json",
                "Content-Type": "application/x-www-form-urlencoded",
                "Version": "2021-07-28",
                "Authorization": f"Bearer {agency_access_token}"
            }
            location_token_data = {
                "companyId": company_id,
                "locationId": location_id
            }
            try:
                location_token_resp = requests.post(location_token_url, headers=location_token_headers, data=location_token_data)
                _logger.info(f"[TOKEN] Location token response: {location_token_resp.status_code} {location_token_resp.text}")
                if location_token_resp.status_code not in [200, 201]:
                    return http.Response(
                        json.dumps({
                            'success': False,
                            'error': f'Failed to get location access token: {location_token_resp.text}'
                        }),
                        content_type='application/json',
                        status=500,
                        headers=get_cors_headers(request)
                    )
                location_access_token = location_token_resp.json().get('access_token')
                if not location_access_token:
                    return http.Response(
                        json.dumps({
                            'success': False,
                            'error': 'No access_token in location token response.'
                        }),
                        content_type='application/json',
                        status=500,
                        headers=get_cors_headers(request)
                    )
            except Exception as e:
                _logger.error(f"[TOKEN] Error getting location access token: {str(e)}")
                return http.Response(
                    json.dumps({
                        'success': False,
                        'error': f'Error getting location access token: {str(e)}'
                    }),
                    content_type='application/json',
                    status=500,
                    headers=get_cors_headers(request)
                )

            api_url = "https://services.leadconnectorhq.com/contacts/"
            update_contact_url_template = "https://services.leadconnectorhq.com/contacts/{}"

            all_custom_fields = get_all_custom_fields(location_access_token)
            if not all_custom_fields:
                _logger.warning("[CONFIG] Could not fetch custom fields. Proceeding without custom field updates.")

            results = []
            for prop in properties:
                _logger.info(f"[PROCESS] Processing property ID: {prop.id}")

                # Get property detail
                detail = request.env['zillow.property.detail'].sudo().search([
                    ('property_id', '=', prop.id)
                ], limit=1)

                if not detail:
                    _logger.warning(f"[PROCESS] No detail found for property {prop.id}")
                    results.append({
                        'property_id': prop.id,
                        'status': 'error',
                        'response': 'No property detail found'
                    })
                    continue

                _logger.info(f"[PROCESS] Found property detail ID: {detail.id}")

                # Get agent info
                agent = detail.listing_agent_id
                _logger.info(
                    f"[PROCESS] Agent info for property {prop.id}: {agent.display_name if agent else 'No agent'}")
                agent_email = detail.agent_email or ''
                agent_name = detail.agent_name or ''
                # Prepare the payload according to the new API schema
                payload = {
                    "locationId": location_id,
                    "firstName": agent_name.split()[0] if agent_name else '',
                    "lastName": ' '.join(agent_name.split()[1:]) if agent_name else '',
                    "name": agent_name if agent_name else '',
                    "email": detail.agent_email if detail.agent_email else None,
                    "phone": detail.agent_phone_number or '',
                    "address1": prop.street_address or '',
                    "city": prop.city or '',
                    "state": prop.state or '',
                    "postalCode": prop.zipcode or '',
                    "timezone": "America/New_York",  # Default to EST
                    "dnd": False,
                    "tags": ["Zillow Agent", "Property Agent"],
                    "source": "Zillow Integration",
                    "country": "US",
                    "companyName": detail.broker_name or '',
                }

                _logger.info(f"[API] Preparing payload for property {prop.id}: {json.dumps(payload, default=str)}")

                try:
                    _logger.info(f"[API] Sending request to GHL API for property {prop.id}")
                    headers = {
                        'Accept': 'application/json',
                        'Authorization': f'Bearer {location_access_token.strip()}',
                        'Content-Type': 'application/json',
                        'Version': '2021-07-28'
                    }
                    
                    resp = requests.post(api_url, json=payload, headers=headers, timeout=10)
                    _logger.info(
                        f"[API] Response for property {prop.id}: Status={resp.status_code}, Body={resp.text}")

                    resp_data = {}
                    try:
                        resp_data = resp.json()
                    except json.JSONDecodeError:
                        _logger.error(f"[API] Failed to decode JSON response for property {prop.id}")
                        resp_data = {'raw_response': resp.text}

                    if resp.status_code not in [200, 201]:
                        _logger.error(f"[API][ERROR] Failed to create contact for property {prop.id}. Status: {resp.status_code}, Response: {resp.text}, Payload: {json.dumps(payload, default=str)}")

                    if resp.status_code == 401:
                        _logger.error(f"[API] Authentication failed for property {prop.id}. Token may have expired or has insufficient permissions.")
                        # Try to get more details about the error
                        try:
                            error_data = resp.json()
                            _logger.error(f"[API] Error details: {error_data}")
                        except Exception as e:
                            _logger.error(f"[API] Error parsing error details: {str(e)}")
                        results.append({
                            'property_id': prop.id,
                            'status': resp.status_code,
                            'response': 'Authentication failed. Please check token permissions and ensure it has access to the contacts API.'
                        })
                        continue

                    if resp.status_code in [200, 201] and 'contact' in resp_data:
                        contact_id = resp_data['contact'].get('id')
                        if contact_id and all_custom_fields:
                            _logger.info(f"[UPDATE] Preparing custom fields for contact {contact_id}")
                            
                            custom_field_payload = { "customField": {} }
                            
                            field_mapping = {
                                'property type': detail.home_type,
                                'beds': prop.bedrooms,
                                'baths': prop.bathrooms,
                                'sqft': prop.living_area,
                                'lot size': f"{prop.lot_area_value} {prop.lot_area_unit}" if prop.lot_area_value and prop.lot_area_unit else (prop.lot_area_value or ''),
                                'year built': detail.year_built,
                                'link to pictures': prop.hi_res_image_link,
                                'asking price': detail.price,
                                'occupancy': 'Tenant' if detail.is_non_owner_occupied else 'Owner',
                                'condition': detail.description,
                            }
                            
                            for field_name, value in field_mapping.items():
                                if field_name in all_custom_fields and value:
                                    field_id = all_custom_fields[field_name]
                                    custom_field_payload["customField"][field_id] = str(value)

                            if custom_field_payload["customField"]:
                                update_url = update_contact_url_template.format(contact_id)
                                update_headers = headers.copy()
                                del update_headers['Accept'] # PUT request might not need Accept
                                _logger.info(f"[UPDATE] Sending custom field update to {update_url} with payload: {json.dumps(custom_field_payload, default=str)}")
                                
                                update_resp = requests.put(update_url, json=custom_field_payload, headers=update_headers, timeout=10)
                                
                                if update_resp.status_code == 200:
                                    _logger.info(f"[UPDATE] Successfully updated custom fields for contact {contact_id}")
                                else:
                                    _logger.error(f"[UPDATE][ERROR] Failed to update custom fields for contact {contact_id}. Status: {update_resp.status_code}, Response: {update_resp.text}")
                            else:
                                _logger.info(f"[UPDATE] No custom fields to update for contact {contact_id}")
                    
                    if resp.status_code in [200, 201]:
                        prop.write({
                            'sent_to_ghl_locations': [(4, ghl_location.id)],
                            'last_sent_to_cyclsales': Datetime.now()
                        })
                        _logger.info(
                            f"[UPDATE] Marked property {prop.id} as sent to GHL location {ghl_location.id}")

                    results.append({
                        'property_id': prop.id,
                        'status': resp.status_code,
                        'response': resp.text if isinstance(resp.text, str) else json.dumps(resp_data)
                    })
                except Exception as e:
                    _logger.error(f"[API][EXCEPTION] Error for property {prop.id}: {str(e)}. Payload: {json.dumps(payload, default=str)}")
                    results.append({
                        'property_id': prop.id,
                        'status': 'error',
                        'response': str(e)
                    })

            _logger.info(f"[COMPLETE] Processed {len(results)} properties")
            return http.Response(
                json.dumps({
                    'success': True,
                    'message': 'Properties processed',
                    'results': results
                }),
                content_type='application/json',
                status=200,
                headers=get_cors_headers(request)
            )

        except json.JSONDecodeError as e:
            _logger.error(f"[ERROR] JSON parsing error: {str(e)}")
            return http.Response(
                json.dumps({'success': False, 'error': 'Invalid JSON data'}),
                content_type='application/json',
                status=400,
                headers=get_cors_headers(request)
            )
        except Exception as e:
            _logger.error(f"[ERROR] Unexpected error in send_to_cyclsales: {str(e)}")
            return http.Response(
                json.dumps({'success': False, 'error': str(e)}),
                content_type='application/json',
                status=500,
                headers=get_cors_headers(request)
            )
