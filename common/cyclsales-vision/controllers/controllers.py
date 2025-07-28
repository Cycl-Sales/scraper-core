# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request, Response
import json
import logging

_logger = logging.getLogger(__name__)


class CyclSalesVisionController(http.Controller):
    @http.route('/cs-vision-ai/call-summary', type='json', auth='none', methods=['POST'], csrf=False)
    def cs_vision_ai_call_summary(self, **post):
        try:
            # Accept raw JSON body
            raw_data = request.httprequest.data
            try:
                data = json.loads(raw_data)
                _logger.info(f"[GHL Call Summary] Received webhook: {data}")
            except Exception as e:
                _logger.error(f"[GHL Call Summary] JSON decode error: {str(e)} | Raw data: {raw_data}")
                return Response(
                    json.dumps({
                        'error_code': 'invalid_json',
                        'message': 'Invalid JSON in request body',
                        'details': str(e)
                    }),
                    content_type='application/json',
                    status=400
                )
            # Only process if messageType == 'CALL'
            message_type = data.get('messageType')
            if message_type != 'CALL':
                _logger.info(f"[GHL Call Summary] Ignored non-call messageType: {message_type}")
                return Response(
                    json.dumps({'status': 'ignored', 'reason': 'Non-call messageType'}),
                    content_type='application/json',
                    status=200
                )
            # Validate required fields
            required_fields = ['messageId', 'contactId', 'direction', 'callDuration', 'attachments']
            missing = [f for f in required_fields if f not in data]
            if missing:
                _logger.warning(f"[GHL Call Summary] Missing fields: {missing}")
                return Response(
                    json.dumps({
                        'error_code': 'missing_fields',
                        'message': f'Missing required fields: {missing}',
                        'details': data
                    }),
                    content_type='application/json',
                    status=400
                )
            # Get App Object
            app_obj = request.env['cyclsales.application'].sudo().search([('app_id', '=', '684c5cc0736d09f78555981f')],
                                                                         limit=1)
            if not app_obj:
                _logger.warning(f"[GHL Call Summary] App not found: 684c5cc0736d09f78555981f")
                return Response(
                    json.dumps({'status': 'ignored', 'reason': 'App not found'}),
                    content_type='application/json',
                    status=200
                )
            location_id = request.env['installed.location'].sudo().search([('location_id', '=', data['locationId'])],
                                                                          limit=1)
            if not location_id:
                _logger.warning(f"[GHL Call Summary] Location not found: {data['locationId']}")
                return Response(
                    json.dumps({'status': 'ignored', 'reason': 'Location not found'}),
                    content_type='application/json',
                    status=200
                )
            # Once the location is fetched, we now need to get it's access token
            access_token = location_id.sudo().fetch_location_token(app_obj.access_token, app_obj.company_id)
            if not access_token:
                _logger.warning(f"[GHL Call Summary] Access token not found: {location_id.location_id}")
                return Response(
                    json.dumps({'status': 'ignored', 'reason': 'Access token not found'}),
                    content_type='application/json',
                    status=200
                )
            print("Token: ", access_token)
            # Let's now search the contact
            contact_obj = request.env['ghl.location.contact'].sudo().search([('contact_id', '=', data['contactId'])],
                                                                            limit=1)
            if not contact_obj:
                contact_obj = request.env['ghl.location.contact'].sudo().fetch_contact_single(
                    location_token=access_token,
                    contact_id=data['contactId'])
            if not contact_obj:
                _logger.warning(f"[GHL Call Summary] Contact not found: {data['contactId']}")
                return Response(
                    json.dumps({'status': 'ignored', 'reason': 'Contact not found'}),
                    content_type='application/json',
                    status=200
                )
            # We now have to fetch the conversation object
            conversation_obj = request.env['ghl.contact.conversation'].sudo().fetch_conversation_single(
                location_token=access_token, conversation_id=data['messageId'])
            if not conversation_obj:
                _logger.warning(f"[GHL Call Summary] Conversation not found: {data['messageId']}")
                return Response(
                    json.dumps({'status': 'ignored', 'reason': 'Conversation not found'}),
                    content_type='application/json',
                    status=200,
                )
            # We now have to fetch the message object
            message_obj = request.env['ghl.contact.message'].sudo().fetch_message_single(location_token=access_token,
                                                                                         message_id=data['messageId'])
            if not message_obj:
                _logger.warning(f"[GHL Call Summary] Message not found: {data['messageId']}")
                return Response(
                    json.dumps({'status': 'ignored', 'reason': 'Message not found'}),
                    content_type='application/json',
                    status=200,
                )
            return Response(
                json.dumps({'status': 'success', 'message': 'Webhook received.'}),
                content_type='application/json',
                status=200
            )
        except Exception as e:
            _logger.error(f"[GHL Call Summary] Unexpected error: {str(e)}", exc_info=True)
            return Response(
                json.dumps({
                    'error_code': 'unexpected_error',
                    'message': 'An unexpected error occurred',
                    'details': str(e)
                }),
                content_type='application/json',
                status=500
            )

    @http.route('/cs-vision-ai/perform-summary', type='json', auth='none', methods=['POST'], csrf=False)
    def cs_vision_ai_perform_summary(self, **post):
        try:
            raw_data = request.httprequest.data
            try:
                data = json.loads(raw_data)
                _logger.info(f"[GHL Perform Summary] Received: {data}")
            except Exception as e:
                _logger.error(f"[GHL Perform Summary] JSON decode error: {str(e)} | Raw data: {raw_data}")
                return Response(
                    json.dumps({
                        'error_code': 'invalid_json',
                        'message': 'Invalid JSON in request body',
                        'details': str(e)
                    }),
                    content_type='application/json',
                    status=400
                )
            # Validate required fields
            required_fields = ['messageId', 'contactId', 'direction', 'attachments']
            missing = [f for f in required_fields if f not in data]
            if missing:
                _logger.warning(f"[GHL Perform Summary] Missing fields: {missing}")
                return Response(
                    json.dumps({
                        'error_code': 'missing_fields',
                        'message': f'Missing required fields: {missing}',
                        'details': data
                    }),
                    content_type='application/json',
                    status=400
                )
            # Extract fields
            message_id = data['messageId']
            contact_id = data['contactId']
            direction = data['direction']
            recording_url = data['attachments'][0]
            custom_prompt = data.get('customPrompt')
            # Optionally: fetch transcript or audio (stubbed)
            transcript = data.get('transcript', None)  # If provided
            # --- OpenAI Integration Stub ---
            # In production, fetch transcript/audio, call OpenAI API, etc.
            # For now, return a stubbed summary
            summary = "This is a summary of the call between the agent and the customer."
            keywords = ["pricing", "follow-up"]
            insights = "Customer was hesitant but interested."
            # Optionally, use custom_prompt to influence summary (not implemented in stub)
            response = {
                "summary": summary,
                "status": "success",
                "keywords": keywords,
                "insights": insights
            }
            return Response(
                json.dumps(response),
                content_type='application/json',
                status=200
            )
        except Exception as e:
            _logger.error(f"[GHL Perform Summary] Unexpected error: {str(e)}", exc_info=True)
            return Response(
                json.dumps({
                    'error_code': 'unexpected_error',
                    'message': 'An unexpected error occurred',
                    'details': str(e)
                }),
                content_type='application/json',
                status=500
            )
