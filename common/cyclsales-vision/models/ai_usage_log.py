# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import json
import logging

_logger = logging.getLogger(__name__)

class CyclSalesVisionAIUsageLog(models.Model):
    _name = 'cyclsales.vision.ai.usage.log'
    _description = 'CyclSales Vision AI Usage Log'
    _order = 'create_date desc'
    _rec_name = 'display_name'

    # Basic Information
    name = fields.Char('Log Entry', compute='_compute_name', store=True)
    display_name = fields.Char('Display Name', compute='_compute_display_name', store=True)
    
    # Location and User Information
    location_id = fields.Many2one('installed.location', string='Location', required=False, index=True)
    company_id = fields.Char('Company ID', help='Company identifier')
    user_id = fields.Many2one('res.users', string='User', default=lambda self: self.env.user)
    
    # AI Service Information
    ai_service_id = fields.Many2one('cyclsales.vision.ai', string='AI Service', required=True)
    model_type = fields.Selection([
        ('gpt-4o', 'GPT-4o'),
        ('gpt-4', 'GPT-4'),
        ('gpt-3.5-turbo', 'GPT-3.5 Turbo'),
        ('claude-3', 'Claude 3'),
        ('custom', 'Custom Model')
    ], string='Model Type', related='ai_service_id.model_type', store=True)
    
    # Request Details
    request_type = fields.Selection([
        ('call_summary', 'Call Summary'),
        ('transcript_analysis', 'Transcript Analysis'),
        ('contact_analysis', 'Contact Analysis'),
        ('custom_prompt', 'Custom Prompt'),
        ('test_connection', 'Test Connection'),
        ('other', 'Other')
    ], string='Request Type', required=True, default='call_summary')
    
    status = fields.Selection([
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('timeout', 'Timeout'),
        ('rate_limited', 'Rate Limited')
    ], string='Status', required=True, default='pending', index=True)
    
    # Content Information
    message_id = fields.Char('Message ID', help='GHL Message ID if applicable')
    contact_id = fields.Char('Contact ID', help='GHL Contact ID if applicable')
    conversation_id = fields.Char('Conversation ID', help='GHL Conversation ID if applicable')
    
    # Request/Response Data
    input_tokens = fields.Integer('Input Tokens', help='Number of tokens in the input')
    output_tokens = fields.Integer('Output Tokens', help='Number of tokens in the output')
    total_tokens = fields.Integer('Total Tokens', compute='_compute_total_tokens', store=True)
    
    # Cost Information
    cost_per_1k_tokens = fields.Float('Cost per 1K Tokens', digits=(10, 6), help='Cost per 1000 tokens')
    total_cost = fields.Float('Total Cost', compute='_compute_total_cost', store=True, digits=(10, 6))
    
    # Request Details
    prompt_length = fields.Integer('Prompt Length', help='Length of the prompt in characters')
    response_length = fields.Integer('Response Length', help='Length of the response in characters')
    
    # Timing Information
    request_start_time = fields.Datetime('Request Start Time')
    request_end_time = fields.Datetime('Request End Time')
    processing_duration = fields.Float('Processing Duration (seconds)', compute='_compute_duration', store=True)
    
    # Error Information
    error_message = fields.Text('Error Message', help='Detailed error message if request failed')
    error_code = fields.Char('Error Code', help='Error code from AI service')
    
    # Response Data
    response_summary = fields.Text('Response Summary', help='Generated summary from AI')
    response_keywords = fields.Text('Response Keywords', help='Generated keywords from AI')
    response_sentiment = fields.Selection([
        ('positive', 'Positive'),
        ('negative', 'Negative'),
        ('neutral', 'Neutral')
    ], string='Response Sentiment')
    
    # Metadata
    api_version = fields.Char('API Version', default='2021-07-28')
    request_id = fields.Char('Request ID', help='Unique identifier for this request')
    
    # Billing Information
    is_billable = fields.Boolean('Billable', default=True, help='Whether this request should be billed')
    billing_period = fields.Selection([
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('annually', 'Annually')
    ], string='Billing Period', default='monthly')
    
    # Computed fields
    @api.depends('location_id', 'request_type', 'create_date')
    def _compute_name(self):
        for record in self:
            if record.location_id and record.request_type:
                record.name = f"{record.location_id.name} - {record.request_type.replace('_', ' ').title()}"
            else:
                record.name = f"AI Usage Log - {record.id}"

    @api.depends('location_id', 'request_type', 'status', 'create_date')
    def _compute_display_name(self):
        for record in self:
            if record.location_id:
                status_icon = {
                    'success': '✅',
                    'failed': '❌',
                    'pending': '⏳',
                    'processing': '🔄',
                    'timeout': '⏰',
                    'rate_limited': '🚫'
                }.get(record.status, '❓')
                
                record.display_name = f"{status_icon} {record.location_id.name} - {record.request_type.replace('_', ' ').title()}"

    @api.depends('input_tokens', 'output_tokens')
    def _compute_total_tokens(self):
        for record in self:
            record.total_tokens = (record.input_tokens or 0) + (record.output_tokens or 0)

    @api.depends('total_tokens', 'cost_per_1k_tokens')
    def _compute_total_cost(self):
        for record in self:
            if record.total_tokens and record.cost_per_1k_tokens:
                record.total_cost = (record.total_tokens / 1000) * record.cost_per_1k_tokens
            else:
                record.total_cost = 0.0

    @api.depends('request_start_time', 'request_end_time')
    def _compute_duration(self):
        for record in self:
            if record.request_start_time and record.request_end_time:
                duration = (record.request_end_time - record.request_start_time).total_seconds()
                record.processing_duration = duration
            else:
                record.processing_duration = 0.0

    # Business Logic Methods
    def create_usage_log(self, location_id, ai_service_id, request_type, **kwargs):
        """
        Create a new usage log entry
        """
        # Get the AI service record to access its cost_per_1k_tokens
        ai_service = None
        if isinstance(ai_service_id, int):
            ai_service = self.env['cyclsales.vision.ai'].browse(ai_service_id)
        elif hasattr(ai_service_id, 'cost_per_1k_tokens'):
            ai_service = ai_service_id
        
        cost_per_1k_tokens = 0.0
        if ai_service and hasattr(ai_service, 'cost_per_1k_tokens'):
            cost_per_1k_tokens = ai_service.cost_per_1k_tokens
        
        # Handle location_id - if it's a string or None, try to find a default location
        final_location_id = None
        if isinstance(location_id, int):
            final_location_id = location_id
        elif isinstance(location_id, str) and location_id != 'unknown':
            # Try to find location by name or other identifier
            location = self.env['installed.location'].search([('location_id', '=', location_id)], limit=1)
            if location:
                final_location_id = location.id
        
        # If no valid location found, try to get a default location
        if not final_location_id:
            default_location = self.env['installed.location'].search([], limit=1)
            if default_location:
                final_location_id = default_location.id
        
        log_data = {
            'ai_service_id': ai_service_id if isinstance(ai_service_id, int) else ai_service_id.id,
            'request_type': request_type,
            'status': 'pending',
            'request_start_time': fields.Datetime.now(),
            'cost_per_1k_tokens': cost_per_1k_tokens,
            **kwargs
        }
        
        # Only add location_id if we have a valid one
        if final_location_id:
            log_data['location_id'] = final_location_id
        
        import logging
        _logger = logging.getLogger(__name__)
        _logger.info(f"[Usage Log] Creating usage log with data: {log_data}")
        
        try:
            result = self.create(log_data)
            _logger.info(f"[Usage Log] Successfully created usage log: {result.id}")
            return result
        except Exception as e:
            _logger.error(f"[Usage Log] Failed to create usage log: {str(e)}")
            raise

    def update_success(self, response_data=None, **kwargs):
        """
        Update log entry for successful request
        """
        update_data = {
            'status': 'success',
            'request_end_time': fields.Datetime.now(),
            **kwargs
        }
        
        if response_data:
            if isinstance(response_data, dict):
                update_data.update({
                    'response_summary': response_data.get('summary', ''),
                    'response_keywords': json.dumps(response_data.get('keywords', [])),
                    'response_sentiment': response_data.get('sentiment', 'neutral')
                })
        
        self.write(update_data)

    def update_failure(self, error_message, error_code=None, **kwargs):
        """
        Update log entry for failed request
        """
        update_data = {
            'status': 'failed',
            'request_end_time': fields.Datetime.now(),
            'error_message': error_message,
            'error_code': error_code,
            **kwargs
        }
        
        self.write(update_data)

    def get_location_usage_summary(self, location_id, date_from=None, date_to=None):
        """
        Get usage summary for a specific location
        """
        domain = [('location_id', '=', location_id)]
        
        if date_from:
            domain.append(('create_date', '>=', date_from))
        if date_to:
            domain.append(('create_date', '<=', date_to))
        
        logs = self.search(domain)
        
        return {
            'total_requests': len(logs),
            'successful_requests': len(logs.filtered(lambda l: l.status == 'success')),
            'failed_requests': len(logs.filtered(lambda l: l.status == 'failed')),
            'total_tokens': sum(logs.mapped('total_tokens')),
            'total_cost': sum(logs.mapped('total_cost')),
            'average_duration': sum(logs.mapped('processing_duration')) / len(logs) if logs else 0,
            'request_types': logs.mapped('request_type')
        }

    def get_billing_report(self, location_ids=None, date_from=None, date_to=None):
        """
        Generate billing report for locations
        """
        domain = [('is_billable', '=', True)]
        
        if location_ids:
            domain.append(('location_id', 'in', location_ids))
        if date_from:
            domain.append(('create_date', '>=', date_from))
        if date_to:
            domain.append(('create_date', '<=', date_to))
        
        logs = self.search(domain)
        
        report = {}
        for log in logs:
            location_name = log.location_id.name
            if location_name not in report:
                report[location_name] = {
                    'location_id': log.location_id.id,
                    'total_requests': 0,
                    'total_tokens': 0,
                    'total_cost': 0.0,
                    'request_types': {}
                }
            
            report[location_name]['total_requests'] += 1
            report[location_name]['total_tokens'] += log.total_tokens or 0
            report[location_name]['total_cost'] += log.total_cost or 0.0
            
            request_type = log.request_type
            if request_type not in report[location_name]['request_types']:
                report[location_name]['request_types'][request_type] = 0
            report[location_name]['request_types'][request_type] += 1
        
        return report

    # Constraints
    _sql_constraints = [
        ('request_id_uniq', 'unique(request_id)', 'Request ID must be unique!'),
    ]

    @api.constrains('location_id', 'ai_service_id')
    def _check_required_fields(self):
        for record in self:
            if not record.location_id:
                raise ValidationError(_('Location is required for AI usage logging.'))
            if not record.ai_service_id:
                raise ValidationError(_('AI Service is required for AI usage logging.'))

    # Action Methods
    def action_retry_request(self):
        """
        Retry a failed request
        """
        for record in self:
            if record.status == 'failed':
                # Reset status and try again
                record.write({
                    'status': 'pending',
                    'request_start_time': fields.Datetime.now(),
                    'error_message': False,
                    'error_code': False
                })
                _logger.info(f"Retrying AI request for log ID: {record.id}")

    def action_view_location_logs(self):
        """
        Action to view all logs for a specific location
        """
        return {
            'name': _('AI Usage Logs'),
            'type': 'ir.actions.act_window',
            'res_model': 'cyclsales.vision.ai.usage.log',
            'view_mode': 'tree,form',
            'domain': [('location_id', '=', self.location_id.id)],
            'context': {'default_location_id': self.location_id.id}
        } 