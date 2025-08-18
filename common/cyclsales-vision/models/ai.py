# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
import json
import logging
import requests
from datetime import datetime

_logger = logging.getLogger(__name__)

class CyclSalesVisionAI(models.Model):
    _name = 'cyclsales.vision.ai'
    _description = 'CyclSales Vision AI Service'
    _order = 'create_date desc'

    name = fields.Char('AI Service Name', required=True, default='OpenAI GPT-4')
    model_type = fields.Selection([
        ('gpt-4o', 'GPT-4o'),
        ('gpt-4', 'GPT-4'),
        ('gpt-3.5-turbo', 'GPT-3.5 Turbo'),
        ('claude-3', 'Claude 3'),
        ('custom', 'Custom Model')
    ], string='Model Type', default='gpt-4o', required=True)
    
    # Configuration
    api_key = fields.Char('API Key', help='API key for the AI service')
    base_url = fields.Char('Base URL', default='https://api.openai.com/v1', help='Base URL for API calls')
    max_tokens = fields.Integer('Max Tokens', default=500, help='Maximum tokens for response')
    temperature = fields.Float('Temperature', default=0.3, help='Creativity level (0.0-1.0)')
    cost_per_1k_tokens = fields.Float('Cost per 1K Tokens', default=0.03, digits=(10, 6), help='Cost per 1000 tokens for billing')
    
    # Status and tracking
    is_active = fields.Boolean('Active', default=True)
    last_used = fields.Datetime('Last Used')
    usage_count = fields.Integer('Usage Count', default=0)
    error_count = fields.Integer('Error Count', default=0)
    last_error = fields.Text('Last Error Message')
    
    # Call summary specific fields
    default_prompt_template = fields.Text('Default Prompt Template', default="""Analyze the following call transcript and return a JSON response with exactly this structure. Set the value of the "summary" field to be exactly the same as the custom prompt provided by the caller:
{
    "summary": "<same text as the provided custom prompt>",
    "keywords": ["keyword1", "keyword2", "keyword3"],
    "sentiment": "positive|negative|neutral",
    "action_items": ["action1", "action2", "action3"],
    "confidence_score": 0.85,
    "duration_analyzed": "calculated from transcript timing",
    "speakers_detected": "count from transcript data"
}

Requirements:
- summary: must mirror the exact custom prompt text provided by the workflow
- keywords: array of strings, max 10 items, relevant to the conversation
- sentiment: only "positive", "negative", or "neutral"
- action_items: array of strings, max 5 items, specific next steps
- confidence_score: float between 0.0 and 1.0
- duration_analyzed: string describing actual call duration calculated from transcript timing
- speakers_detected: integer >= 0, count unique speakers from transcript

Call Transcript:
{transcript}

Return only the JSON object, no additional text.""")
    
    # Computed fields
    status = fields.Selection([
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('error', 'Error'),
        ('testing', 'Testing')
    ], string='Status', compute='_compute_status', store=True)
    
    @api.depends('is_active', 'error_count', 'last_error')
    def _compute_status(self):
        for record in self:
            if not record.is_active:
                record.status = 'inactive'
            elif record.error_count > 5:
                record.status = 'error'
            elif record.last_error:
                record.status = 'testing'
            else:
                record.status = 'active'

    def generate_summary(self, message_id=None, contact_id=None, recording_url=None, transcript=None, custom_prompt=None, location_id=None, custom_api_key=None, call_duration=None, speakers_detected=None):
        """
        Generate AI summary for call data
        """
        # Create usage log entry
        usage_log = None
        try:
            # Ensure we have a valid AI service ID
            if not self.id:
                _logger.error("[AI Service] No valid AI service ID available")
                usage_log = None
            else:
                # Always create usage log, use 'unknown' as default location_id if not provided
                usage_location_id = location_id or 'unknown'
                usage_log = self.env['cyclsales.vision.ai.usage.log'].sudo().create_usage_log(
                    location_id=usage_location_id,
                    ai_service_id=self.id,
                    request_type='call_summary',
                    message_id=message_id,
                    contact_id=contact_id,
                    conversation_id=None,
                    request_id=f"req_{message_id}_{fields.Datetime.now().strftime('%Y%m%d_%H%M%S')}" if message_id else None
                )
                usage_log.write({'status': 'processing'})
                _logger.info(f"[AI Service] Created usage log entry: {usage_log.id}")
        except Exception as e:
            _logger.error(f"[AI Service] Failed to create usage log: {str(e)}")
            usage_log = None
        
        _logger.info(f"[AI Service] Generating summary for message_id: {message_id}, contact_id: {contact_id}")
        
        # DEBUG: Log the transcript being passed
        # Limit transcript logging to 100 characters to avoid log flooding
        logged_transcript = transcript[:100] + "..." if transcript and len(transcript) > 100 else transcript
        _logger.info(f"[AI Service] Transcript received: {logged_transcript}")
        _logger.info(f"[AI Service] Transcript type: {type(transcript)}")
        _logger.info(f"[AI Service] Transcript length: {len(transcript) if transcript else 0}")
        if transcript:
            _logger.info(f"[AI Service] Transcript preview (first 100 chars): {transcript[:100]}...")
        else:
            _logger.warning(f"[AI Service] No transcript provided!")
        
        # Get API key from record or system parameters
        api_key = self.api_key or self.env['ir.config_parameter'].sudo().get_param('web_scraper.openai_api_key')
        if not api_key:
            _logger.error("[AI Service] No API key configured")
            if usage_log:
                usage_log.update_failure("No API key configured", "NO_API_KEY")
            return self._get_default_summary()
        
        # Use custom API key if provided, otherwise use configured API key
        if custom_api_key:
            api_key = custom_api_key
            _logger.info(f"[AI Service] Using custom API key: {api_key[:10]}...")
        else:
            _logger.info(f"[AI Service] Using configured API key: {api_key[:10]}...")
        
        # Ensure we have a valid base URL
        base_url = self.base_url or 'https://api.openai.com/v1'
        if not base_url or base_url == 'False':
            base_url = 'https://api.openai.com/v1'
            _logger.warning(f"[AI Service] Invalid base_url '{self.base_url}', using default: {base_url}")
        
        # Prepare the prompt
        if custom_prompt:
            # If custom prompt is provided, combine it with the transcript and JSON format instructions
            transcript_for_prompt = transcript or "No transcript available"
            
            # Add call metadata if available
            metadata_info = ""
            if call_duration is not None:
                metadata_info += f"\nCall Duration: {call_duration} seconds"
            if speakers_detected is not None:
                metadata_info += f"\nSpeakers Detected: {speakers_detected}"
            
            prompt = f"""{custom_prompt}

Please provide your response in the following JSON format:
{{
    "summary": "{custom_prompt}",
    "keywords": ["keyword1", "keyword2", "keyword3"],
    "sentiment": "positive|negative|neutral",
    "action_items": ["action1", "action2", "action3"],
    "confidence_score": 0.85,
    "duration_analyzed": "{call_duration} seconds" if call_duration else "Unknown",
    "speakers_detected": {speakers_detected if speakers_detected else 0}
}}

Call Metadata:{metadata_info}

Call Transcript:
{transcript_for_prompt}"""
            _logger.info(f"[AI Service] Using custom prompt with transcript")
            _logger.info(f"[AI Service] Custom prompt: {custom_prompt[:100]}...")
        else:
            # Use string replacement instead of format to avoid JSON brace conflicts
            transcript_for_prompt = transcript or "No transcript available"
            _logger.info(f"[AI Service] Using default prompt template with transcript")
            _logger.info(f"[AI Service] No custom prompt provided")
            prompt = self.default_prompt_template.replace('{transcript}', transcript_for_prompt)
        
        # DEBUG: Log the final prompt being sent to AI
        _logger.info(f"[AI Service] Final prompt length: {len(prompt)}")
        _logger.info(f"[AI Service] Final prompt preview: {prompt[:1000]}...")
        
        # Update usage log with prompt length
        if usage_log:
            usage_log.write({'prompt_length': len(prompt)})
        
        # Prepare the request
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'model': self.model_type,
            'messages': [
                {
                    'role': 'user',
                    'content': prompt
                }
            ],
            'max_tokens': max(self.max_tokens or 500, 1),  # Ensure minimum value of 1
            'temperature': self.temperature or 0.3
        }
            
            # Validate and set model type
            model_type = self.model_type
            if not model_type or model_type == 'False':
                model_type = 'gpt-4o'  # Default to GPT-4o
                _logger.warning(f"[AI Service] Invalid model type '{self.model_type}', using default: {model_type}")
            
            # Update payload with validated model type
            payload['model'] = model_type
            
            _logger.info(f"[AI Service] Sending request to {base_url}/chat/completions")
            _logger.info(f"[AI Service] Model type: {model_type}")
            _logger.info(f"[AI Service] API key (first 10 chars): {api_key[:10]}..." if api_key else "No API key")
            _logger.info(f"[AI Service] Max tokens: {payload['max_tokens']}")
            _logger.info(f"[AI Service] Temperature: {payload['temperature']}")
            _logger.info(f"[AI Service] Payload keys: {list(payload.keys())}")
            
            # Make the API call
            response = requests.post(
                f'{base_url}/chat/completions',
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code != 200:
                _logger.error(f"[AI Service] API error: {response.status_code} | {response.text}")
                self._record_error(f"API error: {response.status_code}")
                if usage_log:
                    usage_log.update_failure(f"API error: {response.status_code}", f"HTTP_{response.status_code}")
                return self._get_default_summary()
            
            # Parse the response
            result = response.json()
            ai_response_text = result['choices'][0]['message']['content']
            
            _logger.info(f"[AI Service] Raw AI response: {ai_response_text}")
            
            # Update usage log with token information
            if usage_log and 'usage' in result:
                usage = result['usage']
                usage_log.write({
                    'input_tokens': usage.get('prompt_tokens', 0),
                    'output_tokens': usage.get('completion_tokens', 0),
                    'response_length': len(ai_response_text)
                })
            
            # Handle response - try to parse as JSON for both custom and standard prompts
            try:
                import re
                json_match = re.search(r'\{.*\}', ai_response_text, re.DOTALL)
                if json_match:
                    ai_summary = json.loads(json_match.group())
                else:
                    ai_summary = json.loads(ai_response_text)
                
                _logger.info(f"[AI Service] Parsed AI summary: {ai_summary}")
                
                # Update usage statistics
                self._record_success()
                
                # Update usage log with success
                if usage_log:
                    usage_log.update_success(ai_summary)
                
                return ai_summary
                
            except json.JSONDecodeError as e:
                _logger.error(f"[AI Service] Failed to parse AI response as JSON: {str(e)}")
                self._record_error(f"JSON parse error: {str(e)}")
                if usage_log:
                    usage_log.update_failure(f"JSON parse error: {str(e)}", "JSON_PARSE_ERROR")
                
                # Fallback: create a summary with the raw response as summary
                fallback_summary = {
                    'summary': ai_response_text,
                    'keywords': [],
                    'sentiment': 'neutral',
                    'action_items': [],
                    'confidence_score': 0.5,
                    'duration_analyzed': 'Unknown',
                    'speakers_detected': 0,
                    'raw_transcript_array': ''
                }
                
                _logger.warning(f"[AI Service] Using fallback summary due to JSON parse error")
                return fallback_summary
                
        except Exception as e:
            _logger.error(f"[AI Service] Error generating summary: {str(e)}", exc_info=True)
            self._record_error(str(e))
            if usage_log:
                usage_log.update_failure(str(e), "EXCEPTION")
            default_summary = self._get_default_summary()
            if custom_prompt is not None:
                default_summary['summary'] = custom_prompt
            return default_summary

    def _record_success(self):
        """Record successful API call"""
        self.write({
            'last_used': fields.Datetime.now(),
            'usage_count': self.usage_count + 1,
            'last_error': False
        })

    def _record_error(self, error_message):
        """Record API error"""
        self.write({
            'error_count': self.error_count + 1,
            'last_error': error_message,
            'last_used': fields.Datetime.now()
        })

    def _get_default_summary(self):
        """Return default summary when AI service fails"""
        return {
            'summary': 'Unable to generate AI summary at this time.',
            'keywords': [],
            'sentiment': 'neutral',
            'action_items': [],
            'confidence_score': 0.0,
            'duration_analyzed': 'Unknown',
            'speakers_detected': 0,
            'raw_transcript_array': ''
        }

    def test_connection(self):
        """Test the AI service connection"""
        try:
            _logger.info(f"[AI Service] Testing connection for {self.name}")
            
            # Simple test prompt
            test_prompt = "Respond with 'OK' if you can read this message."
            
            result = self.generate_summary(
                message_id='test',
                contact_id='test',
                transcript=test_prompt
            )
            
            if result and result.get('summary'):
                _logger.info(f"[AI Service] Connection test successful")
                return {
                    'success': True,
                    'message': 'Connection test successful',
                    'response': result
                }
            else:
                return {
                    'success': False,
                    'message': 'No valid response received'
                }
                
        except Exception as e:
            _logger.error(f"[AI Service] Connection test failed: {str(e)}")
            return {
                'success': False,
                'message': f'Connection test failed: {str(e)}'
            }

    def reset_error_count(self):
        """Reset error count and status"""
        self.write({
            'error_count': 0,
            'last_error': False
        })
        _logger.info(f"[AI Service] Reset error count for {self.name}")

    @api.model
    def get_default_ai_service(self):
        """Get the default AI service"""
        return self.search([('is_active', '=', True), ('status', '=', 'active')], limit=1)

    @api.model
    def ensure_usage_logging(self, api_call_func, *args, **kwargs):
        """
        Utility method to ensure all OpenAI API calls are logged through the usage logging system.
        
        This method should be used as a wrapper for any direct OpenAI API calls to ensure
        they are properly logged in the usage tracking system.
        
        Args:
            api_call_func: Function that makes the actual API call
            *args: Arguments to pass to the API call function
            **kwargs: Keyword arguments to pass to the API call function
        
        Returns:
            The result of the API call function
        """
        # Extract logging parameters from kwargs
        location_id = kwargs.pop('location_id', 'unknown')
        message_id = kwargs.pop('message_id', 'api_call')
        contact_id = kwargs.pop('contact_id', 'unknown')
        conversation_id = kwargs.pop('conversation_id', 'unknown')
        request_type = kwargs.pop('request_type', 'other')
        custom_api_key = kwargs.pop('custom_api_key', None)
        
        # Get or create AI service
        ai_service = self.search([('is_active', '=', True)], limit=1)
        if not ai_service:
            ai_service = self.create({
                'name': 'Default OpenAI GPT-4 Service',
                'model_type': 'gpt-4o',
                'base_url': 'https://api.openai.com/v1',
                'max_tokens': 500,
                'temperature': 0.3,
                'is_active': True
            })
        
        # Create usage log entry
        usage_log = None
        try:
            usage_log = self.env['cyclsales.vision.ai.usage.log'].sudo().create_usage_log(
                location_id=location_id,
                ai_service_id=ai_service.id,
                request_type=request_type,
                message_id=message_id,
                contact_id=contact_id,
                conversation_id=conversation_id
            )
            
            if usage_log:
                usage_log.write({'status': 'processing'})
        except Exception as e:
            _logger.error(f"[AI Service] Failed to create usage log: {str(e)}")
        
        try:
            # Make the actual API call
            result = api_call_func(*args, **kwargs)
            
            # Update usage log with success
            if usage_log:
                try:
                    # Try to extract token information from result if available
                    if isinstance(result, dict) and 'usage' in result:
                        usage = result['usage']
                        usage_log.write({
                            'input_tokens': usage.get('prompt_tokens', 0),
                            'output_tokens': usage.get('completion_tokens', 0),
                            'response_length': len(str(result.get('choices', [{}])[0].get('message', {}).get('content', '')))
                        })
                    
                    usage_log.update_success(result)
                except Exception as e:
                    _logger.error(f"[AI Service] Failed to update usage log with success: {str(e)}")
            
            # Update AI service usage statistics
            ai_service._record_success()
            
            return result
            
        except Exception as e:
            # Update usage log with failure
            if usage_log:
                try:
                    usage_log.update_failure(str(e), "EXCEPTION")
                except Exception as log_error:
                    _logger.error(f"[AI Service] Failed to update usage log with failure: {str(log_error)}")
            
            # Update AI service error statistics
            ai_service._record_error(str(e))
            
            # Re-raise the exception
            raise

    @api.model
    def make_openai_api_call(self, endpoint, method='POST', headers=None, data=None, 
                           location_id='unknown', message_id='api_call', contact_id='unknown', 
                           conversation_id='unknown', request_type='other', custom_api_key=None):
        """
        Make an OpenAI API call with automatic usage logging.
        
        This method ensures that all OpenAI API calls are properly logged in the usage tracking system.
        
        Args:
            endpoint: The OpenAI API endpoint (e.g., '/chat/completions', '/models')
            method: HTTP method ('GET' or 'POST')
            headers: Request headers
            data: Request data
            location_id: Location identifier for logging
            message_id: Message identifier for logging
            contact_id: Contact identifier for logging
            conversation_id: Conversation identifier for logging
            request_type: Type of request for logging
            custom_api_key: Custom API key to use
        
        Returns:
            The API response
        """
        import requests
        
        def api_call():
            # Get API key
            api_key = custom_api_key or self.env['ir.config_parameter'].sudo().get_param('web_scraper.openai_api_key')
            if not api_key:
                raise Exception("No OpenAI API key configured")
            
            # Prepare headers
            if headers is None:
                headers = {}
            
            if 'Authorization' not in headers:
                headers['Authorization'] = f'Bearer {api_key}'
            
            if 'Content-Type' not in headers:
                headers['Content-Type'] = 'application/json'
            
            # Make the request
            url = f"https://api.openai.com/v1{endpoint}"
            
            if method.upper() == 'GET':
                response = requests.get(url, headers=headers, timeout=30)
            else:
                response = requests.post(url, headers=headers, json=data, timeout=30)
            
            if response.status_code != 200:
                raise Exception(f"OpenAI API error: {response.status_code} | {response.text}")
            
            return response.json()
        
        # Use the ensure_usage_logging wrapper
        return self.ensure_usage_logging(
            api_call,
            location_id=location_id,
            message_id=message_id,
            contact_id=contact_id,
            conversation_id=conversation_id,
            request_type=request_type,
            custom_api_key=custom_api_key
        ) 