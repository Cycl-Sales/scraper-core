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
            
            # Early validation: Check call duration
            call_duration = data.get('callDuration', 0)
            _logger.info(f"[GHL Call Summary] Call duration: {call_duration} seconds")
            
            if call_duration < 19:
                _logger.info(f"[GHL Call Summary] Call duration is less than 20 seconds ({call_duration}s)... skipping...")
                return Response(
                    json.dumps({
                        'status': 'ignored', 
                        'reason': f'Call duration ({call_duration} seconds) is below minimum threshold (19 seconds)',
                        'call_duration_seconds': call_duration
                    }),
                    content_type='application/json',
                    status=200
                )
            
            # Early validation: Check for active workflows
            location_id_str = data.get('locationId')
            if location_id_str:
                # Get location record to get the name
                location_record = request.env['installed.location'].sudo().search([
                    ('location_id', '=', location_id_str)
                ], limit=1)
                
                location_name = location_record.name if location_record else 'Unknown Location'
                
                active_workflows = request.env['cyclsales.vision.trigger'].sudo().search([
                    ('location_id.location_id', '=', location_id_str),
                    ('status', '=', 'active')
                ])
                
                if not active_workflows:
                    _logger.info(f"[GHL Call Summary] No active workflow found in location '{location_name}' ({location_id_str}). Skipping process...")
                    return Response(
                        json.dumps({
                            'status': 'ignored', 
                            'reason': f'No active workflows found for location {location_name} ({location_id_str})',
                            'location_id': location_id_str,
                            'location_name': location_name
                        }),
                        content_type='application/json',
                        status=200
                    )
                
                _logger.info(f"[GHL Call Summary] Found {len(active_workflows)} active workflows for location '{location_name}' ({location_id_str})")
            
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
            
            # Extract minimum duration from call data
            minimum_duration = call_data.get('cs_vision_call_minimum_duration', 20)
            
            # Find relevant triggers for this location and call event
            triggers = request.env['cyclsales.vision.trigger'].sudo().search([
                ('location_id', '=', location.id), 
                ('status', '=', 'active')
            ])
            
            _logger.info(f"[Workflow Trigger] Found {len(triggers)} active triggers for location {location.id}")
            
            if not triggers:
                _logger.info(f"[Workflow Trigger] No active triggers found for location {location.id}")
                return []
            
            workflow_results = []
            
            for trigger in triggers:
                try:
                    # Pass the raw webhook data directly to the trigger's execute_workflow method
                    # Include minimum duration in context data
                    context_data = {
                        'source': 'call_summary_webhook',
                        'cs_vision_call_minimum_duration': minimum_duration
                    }
                    
                    result = trigger.execute_workflow(
                        event_data=call_data,
                        context_data=context_data
                    )
                    
                    workflow_results.append({
                        'trigger_id': trigger.id,
                        'trigger_key': trigger.key,
                        'result': result
                    })
                    
                    _logger.info(f"[Workflow Trigger] Executed workflow for trigger {trigger.external_id}")
                    
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
            
            # Make the request to GHL
            response = requests.post(
                trigger.target_url,
                headers=headers,
                json=call_data,
                timeout=30
            )
            
            if response.status_code == 200:
                _logger.info(f"[GHL Trigger] Success - Status: {response.status_code}")
                return {
                    'success': True,
                    'status_code': response.status_code,
                    'response': response.json() if response.text else {}
                }
            else:
                _logger.error(f"[GHL Trigger] Failed - Status: {response.status_code} | Response: {response.text}")
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
            # Handle nested data structure
            # Check if data is nested under 'data' key
            if 'data' in data and isinstance(data['data'], dict):
                nested_data = data['data']
                summary_prompt = nested_data.get('cs_vision_call_transcript') or nested_data.get('cs_vision_summary_prompt')
                message_id = nested_data.get('cs_vision_ai_message_id')
                minimum_duration = data.get('cs_vision_call_minimum_duration', 20)
                custom_api_key = nested_data.get('cs_vision_openai_api_key')
            else:
                # Direct field access for backward compatibility
                summary_prompt = data.get('cs_vision_call_transcript') or data.get('cs_vision_summary_prompt')
                message_id = data.get('cs_vision_ai_message_id')
                minimum_duration = data.get('cs_vision_call_minimum_duration', 20)
                custom_api_key = data.get('cs_vision_openai_api_key')
            
            # Clean the summary prompt by removing test instructions
            if summary_prompt:
                # Remove common test instructions that might be in the prompt
                test_instructions = [
                    'Make sure to append the text "This is an example: " on the summary field.',
                    'Make sure to append the text "This is an example: "',
                    'append the text "This is an example: "',
                    'This is an example: '
                ]
                
                cleaned_prompt = summary_prompt
                for instruction in test_instructions:
                    cleaned_prompt = cleaned_prompt.replace(instruction, '').strip()
                
                if cleaned_prompt != summary_prompt:
                    _logger.info(f"[AI Call Summary] Cleaned prompt by removing test instructions")
                    summary_prompt = cleaned_prompt
            
            # Critical validation logging only
            if not message_id:
                _logger.warning("[AI Call Summary] No message ID provided")
                return self._get_default_ai_summary()
            
            if not summary_prompt:
                _logger.warning("[AI Call Summary] No summary prompt provided")
                return self._get_default_ai_summary()
            
            _logger.info(f"[AI Call Summary] Processing message ID: {message_id}")
            
            # Get the message record to fetch actual transcript
            message_record = request.env['ghl.contact.message'].sudo().search([
                ('ghl_id', '=', message_id)
            ], limit=1)
            
            if not message_record:
                _logger.warning(f"[AI Call Summary] Message record not found for GHL ID: {message_id}")
                return self._get_default_ai_summary()
            
            # Fetch actual transcript from GHL API
            actual_transcript = None
            try:
                transcript_result = request.env['ghl.contact.message.transcript'].sudo().fetch_transcript_for_message(message_record.id)
                
                if transcript_result.get('success'):
                    # Get the newly fetched transcript records
                    transcript_records = request.env['ghl.contact.message.transcript'].sudo().search([
                        ('message_id', '=', message_record.id)
                    ], order='sentence_index asc')
                    
                    if transcript_records:
                        # Get the actual transcript text
                        actual_transcript = transcript_records.get_full_transcript_text()
                        _logger.info(f"[AI Call Summary] Successfully fetched transcript: {len(actual_transcript)} characters")
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
            
            # Check call duration against minimum duration
            if minimum_duration > 19:
                # Calculate call duration from transcript records
                transcript_records = request.env['ghl.contact.message.transcript'].sudo().search([
                    ('message_id', '=', message_record.id)
                ], order='sentence_index asc')
                
                if transcript_records:
                    # Get the last transcript record's end time to calculate total duration
                    last_record = transcript_records[-1]
                    call_duration_seconds = last_record.end_time_seconds
                    
                    if call_duration_seconds < minimum_duration:
                        _logger.info(f"[AI Call Summary] Call duration ({call_duration_seconds}s) < minimum ({minimum_duration}s). Skipping AI processing.")
                        
                        # Convert transcript records to human-readable format
                        transcript_text = ""
                        for record in transcript_records:
                            speaker = "Agent" if record.media_channel == "agent" else "Customer"
                            time_range = f"[{record.start_time_seconds:.1f}s - {record.end_time_seconds:.1f}s]"
                            transcript_text += f"{speaker} {time_range}: {record.transcript}\n"
                        
                        return {
                            "success": True,
                            "message": f"Call duration ({call_duration_seconds} seconds) is below minimum threshold ({minimum_duration} seconds). AI processing skipped.",
                            "call_duration_seconds": call_duration_seconds,
                            "minimum_duration_required": minimum_duration,
                            "summary": "Call too short for analysis",
                            "keywords": [],
                            "sentiment": "neutral",
                            "action_items": [],
                            "confidence_score": 0.0,
                            "duration_analyzed": f"{call_duration_seconds} seconds",
                            "speakers_detected": 0,
                            "raw_transcript_array": transcript_text.strip()
                        }
            
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
            
            # Get OpenAI API key - prioritize custom API key if provided
            api_key = None
            if custom_api_key:
                api_key = custom_api_key
                _logger.info(f"[AI Call Summary] Using custom API key")
            else:
                api_key = request.env['ir.config_parameter'].sudo().get_param('web_scraper.openai_api_key')
                _logger.info(f"[AI Call Summary] Using system API key")
            
            if not api_key:
                _logger.error("[AI Call Summary] No OpenAI API key available")
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
            
            # Try to parse the JSON response
            try:
                # Clean the response text to extract JSON
                import re
                json_match = re.search(r'\{.*\}', ai_response_text, re.DOTALL)
                if json_match:
                    ai_summary = json.loads(json_match.group())
                else:
                    ai_summary = json.loads(ai_response_text)
                
                _logger.info(f"[AI Call Summary] Successfully generated AI summary")
                
                # Convert transcript records to human-readable format
                transcript_text = ""
                for record in transcript_records:
                    speaker = "Agent" if record.media_channel == "agent" else "Customer"
                    time_range = f"[{record.start_time_seconds:.1f}s - {record.end_time_seconds:.1f}s]"
                    transcript_text += f"{speaker} {time_range}: {record.transcript}\n"
                
                # Add raw transcript array to the response
                ai_summary['raw_transcript_array'] = transcript_text.strip()
                
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
            'speakers_detected': 0,
            'raw_transcript_array': '[]'
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
            post_data = dict(request.params)
            
            # Try to parse JSON from request body
            data = {}
            if raw_data and raw_data != b'{}':
                try:
                    data = json.loads(raw_data)
                except Exception as e:
                    _logger.error(f"[Call Transcription] JSON decode error: {str(e)}")
                    # If JSON parsing fails, try to use POST parameters
                    data = post_data
            else:
                # If no raw data, use POST parameters
                data = post_data
            
            _logger.info(f"[Call Transcription] Processing request with {len(data)} fields")
            
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
