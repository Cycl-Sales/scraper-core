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
    
    # Status and tracking
    is_active = fields.Boolean('Active', default=True)
    last_used = fields.Datetime('Last Used')
    usage_count = fields.Integer('Usage Count', default=0)
    error_count = fields.Integer('Error Count', default=0)
    last_error = fields.Text('Last Error Message')
    
    # Call summary specific fields
    default_prompt_template = fields.Text('Default Prompt Template', default="""Analyze the following call transcript and return a JSON response with exactly this structure:
{
    "summary": "A concise summary of the call conversation",
    "keywords": ["keyword1", "keyword2", "keyword3"],
    "sentiment": "positive|negative|neutral",
    "action_items": ["action1", "action2", "action3"],
    "confidence_score": 0.85,
    "duration_analyzed": "5 minutes 23 seconds",
    "speakers_detected": 2
}

Requirements:
- summary: string, never empty, 2-3 sentences max
- keywords: array of strings, max 10 items, relevant to the conversation
- sentiment: only "positive", "negative", or "neutral"
- action_items: array of strings, max 5 items, specific next steps
- confidence_score: float between 0.0 and 1.0
- duration_analyzed: string describing duration
- speakers_detected: integer >= 0

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

    def generate_summary(self, message_id=None, contact_id=None, recording_url=None, transcript=None, custom_prompt=None):
        """
        Generate AI summary for call data
        """
        try:
            _logger.info(f"[AI Service] Generating summary for message_id: {message_id}, contact_id: {contact_id}")
            
            # Get API key from record or system parameters
            api_key = self.api_key or self.env['ir.config_parameter'].sudo().get_param('web_scraper.openai_api_key')
            if not api_key:
                _logger.error("[AI Service] No API key configured")
                return self._get_default_summary()
            
            # Prepare the prompt
            if custom_prompt:
                prompt = custom_prompt
            else:
                # Use string replacement instead of format to avoid JSON brace conflicts
                prompt = self.default_prompt_template.replace('{transcript}', transcript or "No transcript available")
            
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
                'max_tokens': self.max_tokens,
                'temperature': self.temperature
            }
            
            _logger.info(f"[AI Service] Sending request to {self.base_url}/chat/completions")
            
            # Make the API call
            response = requests.post(
                f'{self.base_url}/chat/completions',
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code != 200:
                _logger.error(f"[AI Service] API error: {response.status_code} | {response.text}")
                self._record_error(f"API error: {response.status_code}")
                return self._get_default_summary()
            
            # Parse the response
            result = response.json()
            ai_response_text = result['choices'][0]['message']['content']
            
            _logger.info(f"[AI Service] Raw AI response: {ai_response_text}")
            
            # Try to parse the JSON response
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
                
                return ai_summary
                
            except json.JSONDecodeError as e:
                _logger.error(f"[AI Service] Failed to parse AI response as JSON: {str(e)}")
                self._record_error(f"JSON parse error: {str(e)}")
                return self._get_default_summary()
                
        except Exception as e:
            _logger.error(f"[AI Service] Error generating summary: {str(e)}", exc_info=True)
            self._record_error(str(e))
            return self._get_default_summary()

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
            'speakers_detected': 0
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