from odoo import http
from odoo.http import request, Response
import json
import logging
import requests
from odoo.fields import Datetime

_logger = logging.getLogger(__name__)


class ZillowPropertyController(http.Controller):

    @http.route('/api/zillow/properties', type='http', auth='public', methods=['GET'], csrf=False)
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
                status=200
            )

        except Exception as e:
            _logger.error(f"Error in get_zillow_properties: {str(e)}")
            return http.Response(
                json.dumps({
                    'status': 'error',
                    'message': str(e)
                }),
                content_type='application/json',
                status=500
            )

    @http.route('/api/zillow/send-to-cyclsales', type='http', auth='public', methods=['POST'], csrf=False)
    def send_to_cyclsales(self, **kwargs):
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
                    status=400
                )

            # Fetch properties from zillow.property model
            _logger.info(f"[FETCH] Attempting to fetch properties with IDs: {property_ids}")
            properties = request.env['zillow.property'].sudo().browse(property_ids)
            _logger.info(f"[FETCH] Found {len(properties)} properties")

            webhook_url = "https://services.leadconnectorhq.com/hooks/N1D3b2rc7RAqs4k7qdFY/webhook-trigger/47dabb25-a458-43ec-a0e6-8832251239a5"

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

                payload = {
                    "listing_agent": agent.display_name if agent else '',
                    "baths": detail.bathrooms,
                    "beds": detail.bedrooms,
                    "sqft": detail.living_area,
                    "lot_size": detail.lot_size,
                    "year_built": detail.year_built,
                    "address": prop.street_address,
                    "property_type": detail.home_type,
                    "asking_price": detail.price,
                    "realtor": agent.display_name if agent else '',
                    "realtor_email": agent.email if agent else '',
                    "realtor_phone": agent.phone_number if agent else '',
                    "description": detail.description,
                    # Add attribution information
                    "agent_email": detail.agent_email,
                    "agent_license_number": detail.agent_license_number,
                    "agent_name": detail.agent_name,
                    "agent_phone_number": detail.agent_phone_number,
                    "attribution_title": detail.attribution_title,
                    "broker_name": detail.broker_name,
                    "broker_phone_number": detail.broker_phone_number,
                    "buyer_agent_member_state_license": detail.buyer_agent_member_state_license,
                    "buyer_agent_name": detail.buyer_agent_name,
                    "buyer_brokerage_name": detail.buyer_brokerage_name,
                    "co_agent_license_number": detail.co_agent_license_number,
                    "co_agent_name": detail.co_agent_name,
                    "co_agent_number": detail.co_agent_number,
                }

                _logger.info(f"[WEBHOOK] Preparing payload for property {prop.id}: {json.dumps(payload, default=str)}")

                try:
                    _logger.info(f"[WEBHOOK] Sending request to webhook for property {prop.id}")
                    resp = requests.post(webhook_url, json=payload, timeout=10)
                    _logger.info(
                        f"[WEBHOOK] Response for property {prop.id}: Status={resp.status_code}, Body={resp.text}")

                    # If webhook call was successful, mark the property as sent
                    if resp.status_code == 200:
                        current_user = request.env.user
                        prop.write({
                            'sent_to_cyclsales_by': [(4, current_user.id)],
                            'last_sent_to_cyclsales': Datetime.now()
                        })
                        _logger.info(
                            f"[UPDATE] Marked property {prop.id} as sent to CyclSales by user {current_user.id}")

                    results.append({
                        'property_id': prop.id,
                        'status': resp.status_code,
                        'response': resp.text
                    })
                except Exception as e:
                    _logger.error(f"[WEBHOOK] Error for property {prop.id}: {str(e)}")
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
                status=200
            )

        except json.JSONDecodeError as e:
            _logger.error(f"[ERROR] JSON parsing error: {str(e)}")
            return http.Response(
                json.dumps({'success': False, 'error': 'Invalid JSON data'}),
                content_type='application/json',
                status=400
            )
        except Exception as e:
            _logger.error(f"[ERROR] Unexpected error in send_to_cyclsales: {str(e)}")
            return http.Response(
                json.dumps({'success': False, 'error': str(e)}),
                content_type='application/json',
                status=500
            )
