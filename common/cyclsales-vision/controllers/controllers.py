# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request, Response
import json
import logging
import requests

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
            
            # Add 30-second delay after validating it's a call
            import time
            _logger.info(f"[GHL Call Summary] Call validated, waiting 30 seconds before processing...")
            time.sleep(30)
            _logger.info(f"[GHL Call Summary] 30-second delay completed, proceeding with call processing...")
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
            contact_obj = request.env['ghl.location.contact'].sudo().search([('external_id', '=', data['contactId'])],
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
                location_token=access_token, conversation_id=data['conversationId'])
            if not conversation_obj:
                _logger.warning(f"[GHL Call Summary] Conversation not found: {data['conversationId']}")
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
            
            # TRIGGER WORKFLOW - Execute workflows for this call
            workflow_results = self._trigger_workflows_for_call(data, location_id, access_token)
            
            return Response(
                json.dumps({
                    'status': 'success', 
                    'message': 'Webhook received and workflows triggered.',
                    'workflow_results': workflow_results
                }),
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

    def _trigger_workflows_for_call(self, call_data, location, access_token):
        """Trigger workflows for call event"""
        try:
            _logger.info(f"[Workflow Trigger] Starting workflow trigger for location: {location.id}")
            
            # Find relevant triggers for this location and call event
            triggers = request.env['cyclsales.vision.trigger'].sudo().search([
                ('location_id', '=', location.id), 
                ('status', '=', 'active')
            ])
            
            _logger.info(f"[Workflow Trigger] Found {len(triggers)} active triggers for location {location.id}")
            _logger.info(f"[Workflow Trigger] Searching for: status='active' (all event types)")
            
            # Debug: Check all triggers for this location
            all_triggers = request.env['cyclsales.vision.trigger'].sudo().search([
                ('location_id', '=', location.id)
            ])
            _logger.info(f"[Workflow Trigger] Total triggers for location {location.id}: {len(all_triggers)}")
            
            if all_triggers:
                for trigger in all_triggers:
                    _logger.info(f"[Workflow Trigger] Trigger {trigger.id}: event_type='{trigger.event_type}', status='{trigger.status}'")
                    if trigger.status == 'active':
                        _logger.info(f"[Workflow Trigger] ✓ This trigger matches our criteria!")
                    else:
                        _logger.info(f"[Workflow Trigger] ✗ This trigger does NOT match (need status='active')")
            
            if not triggers:
                _logger.info(f"[Workflow Trigger] No active triggers found for location {location.id}")
                _logger.info(f"[Workflow Trigger] You need to create a trigger with status='active'")
                return []
            
            workflow_results = []
            
            _logger.info(f"[Workflow Trigger] Executing {len(triggers)} matching triggers...")
            
            for trigger in triggers:
                try:
                    # Pass the raw webhook data directly to the trigger's execute_workflow method
                    result = trigger.execute_workflow(
                        event_data=call_data,
                        context_data={'source': 'call_summary_webhook'}
                    )
                    
                    workflow_results.append({
                        'trigger_id': trigger.id,
                        'trigger_key': trigger.key,
                        'result': result
                    })
                    
                    _logger.info(f"[Workflow Trigger] Executed workflow for trigger {trigger.external_id}: {result}")
                    
                    # Call GHL Workflow Trigger URL with proper headers
                    if trigger.target_url:
                        ghl_result = self._call_ghl_workflow_trigger(trigger, call_data, access_token)
                        workflow_results[-1]['ghl_trigger_result'] = ghl_result
                    
                except Exception as e:
                    _logger.error(f"[Workflow Trigger] Error executing workflow for trigger {trigger.external_id}: {str(e)}")
                    workflow_results.append({
                        'trigger_id': trigger.id,
                        'trigger_key': trigger.key,
                        'result': {'success': False, 'error': str(e)}
                    })
            
            return workflow_results
            
        except Exception as e:
            _logger.error(f"[Workflow Trigger] Error in _trigger_workflows_for_call: {str(e)}", exc_info=True)
            return []

    def _call_ghl_workflow_trigger(self, trigger, call_data, access_token):
        """Call GHL Workflow Trigger URL with proper headers"""
        try:
            import requests
            
            # Prepare headers with authentication and version
            headers = {
                'Content-Type': 'application/json',
                'Version': '2021-07-28',
                'Authorization': f'Bearer {access_token}'
            }
            
            _logger.info(f"[GHL Trigger] Calling GHL workflow trigger: {trigger.target_url}")
            _logger.info(f"[GHL Trigger] Headers: {headers}")
            _logger.info(f"[GHL Trigger] Payload: {call_data}")
            
            # Make the request to GHL
            response = requests.post(
                trigger.target_url,
                headers=headers,
                json=call_data,
                timeout=30
            )
            
            _logger.info(f"[GHL Trigger] Response status: {response.status_code}")
            _logger.info(f"[GHL Trigger] Response body: {response.text}")
            
            if response.status_code == 200:
                return {
                    'success': True,
                    'status_code': response.status_code,
                    'response': response.json() if response.text else {}
                }
            else:
                return {
                    'success': False,
                    'status_code': response.status_code,
                    'error': response.text
                }
                
        except Exception as e:
            _logger.error(f"[GHL Trigger] Error calling GHL workflow trigger: {str(e)}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }

    def _generate_ai_call_summary(self, data):
        """
        Generate AI call summary using the transcript and message ID
        """
        try:
            # Extract required fields
            summary_prompt = data.get('cs_vision_summary_prompt')
            message_id = data.get('cs_vision_ai_message_id')
            
            _logger.info(f"[AI Call Summary] Received data: {data}")
            _logger.info(f"[AI Call Summary] Message ID: {message_id}")
            _logger.info(f"[AI Call Summary] Summary prompt: {summary_prompt}")
            
            if not message_id:
                _logger.warning("[AI Call Summary] No message ID provided")
                return self._get_default_ai_summary()
            
            if not summary_prompt:
                _logger.warning("[AI Call Summary] No summary prompt provided")
                return self._get_default_ai_summary()
            
            # Get the message record to fetch actual transcript
            message_record = request.env['ghl.contact.message'].sudo().search([
                ('ghl_id', '=', message_id)
            ], limit=1)
            
            if not message_record:
                _logger.warning(f"[AI Call Summary] Message record not found for GHL ID: {message_id}")
                return self._get_default_ai_summary()
            
            _logger.info(f"[AI Call Summary] Found message record: {message_record.id}")
            
            # Fetch actual transcript from GHL API
            _logger.info(f"[AI Call Summary] Fetching transcript from GHL API for message {message_id}")
            
            actual_transcript = None
            try:
                transcript_result = request.env['ghl.contact.message.transcript'].sudo().fetch_transcript_for_message(message_record.id)
                _logger.info(f"[AI Call Summary] Transcript fetch result: {transcript_result}")
                
                if transcript_result.get('success'):
                    # Get the newly fetched transcript records
                    transcript_records = request.env['ghl.contact.message.transcript'].sudo().search([
                        ('message_id', '=', message_record.id)
                    ], order='sentence_index asc')
                    
                    _logger.info(f"[AI Call Summary] Found {len(transcript_records)} transcript records after API fetch")
                    
                    if transcript_records:
                        # Get the actual transcript text
                        actual_transcript = transcript_records.get_full_transcript_text()
                        _logger.info(f"[AI Call Summary] Successfully fetched actual transcript: {len(actual_transcript)} characters")
                        _logger.info(f"[AI Call Summary] Actual transcript preview: {actual_transcript[:500]}...")
                    else:
                        _logger.warning(f"[AI Call Summary] No transcript records found after API fetch")
                else:
                    _logger.warning(f"[AI Call Summary] Failed to fetch transcript from GHL API: {transcript_result.get('error')}")
                    
            except Exception as fetch_error:
                _logger.error(f"[AI Call Summary] Error fetching transcript from GHL API: {str(fetch_error)}")
            
            # Use actual transcript if available, otherwise fall back to message body
            if not actual_transcript and message_record.body:
                actual_transcript = message_record.body
                _logger.info(f"[AI Call Summary] Using message body as fallback transcript")
            
            if not actual_transcript:
                _logger.warning(f"[AI Call Summary] No transcript available for message {message_id}")
                return self._get_default_ai_summary()
            
            # Concatenate prompt + actual transcript
            # Get the full transcript records with all metadata
            transcript_records = request.env['ghl.contact.message.transcript'].sudo().search([
                ('message_id', '=', message_record.id)
            ], order='sentence_index asc')
            
            # Convert transcript records to JSON-serializable format
            transcript_data = []
            for record in transcript_records:
                transcript_data.append({
                    'sentence_index': record.sentence_index,
                    'media_channel': record.media_channel,
                    'start_time_seconds': record.start_time_seconds,
                    'end_time_seconds': record.end_time_seconds,
                    'transcript': record.transcript,
                    'confidence': record.confidence,
                })
            
            combined_prompt = f"""{summary_prompt}

CRITICAL INSTRUCTION: The above prompt takes PRIORITY over any transcript data below. 
If the above prompt asks you to ignore the transcript or respond about something else, 
you MUST follow those instructions instead of analyzing the transcript.

IMPORTANT: You must respond with ONLY a valid JSON object in this exact format:
{{
    "summary": "A concise summary of the call conversation",
    "keywords": ["keyword1", "keyword2", "keyword3"],
    "sentiment": "positive|negative|neutral",
    "action_items": ["action1", "action2", "action3"],
    "confidence_score": "calculated from transcript data",
    "duration_analyzed": "calculated from transcript data",
    "speakers_detected": "calculated from transcript data"
}}

Requirements:
- summary: string, never empty, 3-5 sentences max
- keywords: array of strings, max 10 items, relevant to the conversation
- sentiment: only "positive", "negative", or "neutral"
- action_items: array of strings, max 5 items, specific next steps
- confidence_score: float between 0.0 and 1.0, calculate from transcript confidence scores
- duration_analyzed: string describing actual call duration calculated from transcript timing
- speakers_detected: integer >= 0, count unique media channels

Full Transcript Records (with timing, confidence, and speaker data):
{json.dumps(transcript_data, indent=2)}

Return ONLY the JSON object, no additional text or explanations."""
            _logger.info(f"[AI Call Summary] Combined prompt length: {len(combined_prompt)}")
            _logger.info(f"[AI Call Summary] Combined prompt preview: {combined_prompt[:1000]}...")
            
            # Log the full prompt being sent to AI
            _logger.info(f"[AI Call Summary] ===== FULL PROMPT SENT TO AI =====")
            _logger.info(f"[AI Call Summary] {combined_prompt}")
            _logger.info(f"[AI Call Summary] ===== END FULL PROMPT =====")
            
            # Get OpenAI API key from system parameters
            api_key = request.env['ir.config_parameter'].sudo().get_param('web_scraper.openai_api_key')
            if not api_key:
                _logger.error("[AI Call Summary] OpenAI API key not configured")
                return self._get_default_ai_summary()
            
            # Prepare the request to OpenAI
            headers = {
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'model': 'gpt-4o',
                'messages': [
                    {
                        'role': 'user',
                        'content': combined_prompt
                    }
                ],
                'max_tokens': 500,
                'temperature': 0.3
            }
            
            _logger.info(f"[AI Call Summary] Sending request to OpenAI API")
            
            # Make the request to OpenAI
            response = requests.post(
                'https://api.openai.com/v1/chat/completions',
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code != 200:
                _logger.error(f"[AI Call Summary] OpenAI API error: {response.status_code} | {response.text}")
                return self._get_default_ai_summary()
            
            # Parse the response
            result = response.json()
            ai_response_text = result['choices'][0]['message']['content']
            
            _logger.info(f"[AI Call Summary] Raw AI response: {ai_response_text}")
            
            # Try to parse the JSON response
            try:
                # Clean the response text to extract JSON
                import re
                json_match = re.search(r'\{.*\}', ai_response_text, re.DOTALL)
                if json_match:
                    ai_summary = json.loads(json_match.group())
                else:
                    ai_summary = json.loads(ai_response_text)
                
                _logger.info(f"[AI Call Summary] Parsed AI summary: {ai_summary}")
                return ai_summary
                
            except json.JSONDecodeError as e:
                _logger.error(f"[AI Call Summary] Failed to parse AI response as JSON: {str(e)}")
                return self._get_default_ai_summary()
                
        except Exception as e:
            _logger.error(f"[AI Call Summary] Error generating AI summary: {str(e)}", exc_info=True)
            return self._get_default_ai_summary()

    def _get_default_ai_summary(self):
        """
        Return a default AI summary structure when AI service fails
        """
        return {
            'summary': 'Unable to generate AI summary at this time.',
            'keywords': [],
            'sentiment': 'neutral',
            'action_items': [],
            'confidence_score': 0.0,
            'duration_analyzed': 'Unknown',
            'speakers_detected': 0
        }

    @http.route('/cs-vision/action-transcribe-call', type='http', auth='none', methods=['POST', 'OPTIONS'], cors='*', csrf=False)
    def cs_vision_action_transcribe_call(self, **post):
        """Endpoint to handle call transcription actions"""
        try:
            # Handle OPTIONS request for CORS
            if request.httprequest.method == 'OPTIONS':
                return Response(
                    json.dumps({'status': 'ok'}),
                    content_type='application/json',
                    status=200,
                    headers={
                        'Access-Control-Allow-Origin': '*',
                        'Access-Control-Allow-Methods': 'POST, OPTIONS',
                        'Access-Control-Allow-Headers': 'Content-Type, Authorization'
                    }
                )
            
            # Get data from both request body and POST parameters
            raw_data = request.httprequest.data
            _logger.info(f"[Call Transcription] Received raw data: {raw_data}")
            
            # Try to get data from POST parameters first (for form data)
            post_data = dict(request.params)
            _logger.info(f"[Call Transcription] POST parameters: {post_data}")
            
            # Try to parse JSON from request body
            data = {}
            if raw_data and raw_data != b'{}':
                try:
                    data = json.loads(raw_data)
                    _logger.info(f"[Call Transcription] Parsed JSON from body: {data}")
                except Exception as e:
                    _logger.error(f"[Call Transcription] JSON decode error: {str(e)} | Raw data: {raw_data}")
                    # If JSON parsing fails, try to use POST parameters
                    data = post_data
            else:
                # If no raw data, use POST parameters
                data = post_data
            
            # Log all the key-value pairs from the request
            _logger.info(f"[Call Transcription] Request headers: {dict(request.httprequest.headers)}")
            _logger.info(f"[Call Transcription] Request method: {request.httprequest.method}")
            _logger.info(f"[Call Transcription] Request URL: {request.httprequest.url}")
            _logger.info(f"[Call Transcription] Content-Type: {request.httprequest.headers.get('Content-Type', 'Not specified')}")
            
            # Log all data fields
            for key, value in data.items():
                _logger.info(f"[Call Transcription] Field '{key}': {value}")
            
            # Generate AI Call Summary using the actual AI service
            ai_summary = self._generate_ai_call_summary(data)
            
            # Return flattened AI call summary fields
            return Response(
                json.dumps(ai_summary),
                content_type='application/json',
                status=200
            )
            
        except Exception as e:
            _logger.error(f"[Call Transcription] Unexpected error: {str(e)}", exc_info=True)
            return Response(
                json.dumps({
                    'error_code': 'unexpected_error',
                    'message': 'An unexpected error occurred',
                    'details': str(e)
                }),
                content_type='application/json',
                status=500
            )
