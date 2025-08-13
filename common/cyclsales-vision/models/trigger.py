from odoo import models, fields, api, _
import json
import logging
from datetime import timedelta

_logger = logging.getLogger(__name__)

class CyclSalesVisionTrigger(models.Model):
    _name = 'cyclsales.vision.trigger'
    _description = 'CyclSales Vision GHL Workflow Trigger'
    _order = 'create_date desc'

    external_id = fields.Char('External ID', required=True, index=True)
    key = fields.Char('Trigger Key')
    filters = fields.Text('Filters (JSON)')
    event_type = fields.Char('Event Type')
    target_url = fields.Char('Target URL')
    location_id = fields.Many2one('installed.location', string='Location')
    workflow_id = fields.Char('Workflow ID')
    company_id = fields.Char('Company ID')
    meta_key = fields.Char('Meta Key')
    meta_version = fields.Char('Meta Version')
    
    # Status tracking fields
    status = fields.Selection([
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('processing', 'Processing'),
        ('error', 'Error')
    ], default='active', string='Status')
    last_triggered = fields.Datetime('Last Triggered')
    trigger_count = fields.Integer('Trigger Count', default=0)
    error_message = fields.Text('Last Error Message')

    _sql_constraints = [
        ('external_id_uniq', 'unique(external_id)', 'Trigger external ID must be unique!'),
    ]

    @api.model
    def create_or_update_from_webhook(cls, payload):
        trigger_data = payload.get('triggerData', {})
        meta = payload.get('meta', {})
        extras = payload.get('extras', {})
        external_id = trigger_data.get('id')
        event_type = trigger_data.get('eventType')
        
        vals = {
            'external_id': external_id,
            'key': trigger_data.get('key'),
            'filters': json.dumps(trigger_data.get('filters', [])),
            'event_type': event_type,
            'target_url': trigger_data.get('targetUrl'),
            'workflow_id': extras.get('workflowId'),
            'company_id': extras.get('companyId'),
            'meta_key': meta.get('key'),
            'meta_version': meta.get('version'),
        }
        
        # Set status based on event type
        if event_type == 'DELETED':
            vals['status'] = 'inactive'
            vals['error_message'] = 'Trigger deleted in GHL'
        elif event_type in ['CREATED', 'UPDATED']:
            vals['status'] = 'active'
            vals['error_message'] = False
        
        # Link to installed.location if possible
        location_id_val = extras.get('locationId')
        if location_id_val:
            location = cls.env['installed.location'].search([('location_id', '=', location_id_val)], limit=1)
            if location:
                vals['location_id'] = location.id
        
        trigger = cls.sudo().search([('external_id', '=', external_id)], limit=1)
        if trigger:
            trigger.write(vals)
        else:
            trigger = cls.sudo().create(vals)
        
        _logger.info(f"[Trigger Webhook] {'Updated' if trigger else 'Created'} trigger {external_id} with status: {vals.get('status', 'active')}")
        return trigger

    @api.model
    def update_trigger_status(cls, external_id, status, error_message=None):
        """
        Update trigger status explicitly
        
        Args:
            external_id (str): The external ID of the trigger
            status (str): New status ('active', 'inactive', 'processing', 'error')
            error_message (str, optional): Error message if applicable
        """
        trigger = cls.sudo().search([('external_id', '=', external_id)], limit=1)
        if trigger:
            vals = {'status': status}
            if error_message:
                vals['error_message'] = error_message
            elif status == 'active':
                vals['error_message'] = False
                
            trigger.write(vals)
            _logger.info(f"[Trigger Status] Updated trigger {external_id} status to: {status}")
            return trigger
        else:
            _logger.warning(f"[Trigger Status] Trigger {external_id} not found for status update")
            return False

    def execute_workflow(self, event_data=None, context_data=None):
        """
        Execute workflow for this trigger with provided data
        
        Args:
            event_data (dict): Data from the triggering event (e.g., call data, contact data)
            context_data (dict): Additional context data (e.g., user info, timestamp)
        
        Returns:
            dict: Result of workflow execution
        """
        self.ensure_one()
        
        try:
            # Early validation for call processing workflows
            if self.key in ['call_processing', 'cs_ai_call_summary'] or self.event_type == 'CALL':
                # Check call duration
                call_duration = event_data.get('callDuration', 0) if event_data else 0
                _logger.info(f"[Trigger Workflow] Call duration: {call_duration} seconds")
                
                if call_duration < 19:
                    _logger.info(f"[Trigger Workflow] Call duration ({call_duration}s) < 19s. Skipping workflow execution.")
                    return {
                        'success': True,
                        'message': f'Call duration ({call_duration} seconds) is below minimum threshold (19 seconds). Workflow skipped.',
                        'call_duration_seconds': call_duration,
                        'workflow_skipped': True
                    }
                
                # Check for active workflows for this location
                location_id = event_data.get('locationId') if event_data else None
                if location_id:
                    active_workflows = self.env['cyclsales.vision.trigger'].sudo().search([
                        ('location_id.location_id', '=', location_id),
                        ('status', '=', 'active')
                    ])
                    
                    if not active_workflows:
                        _logger.info(f"[Trigger Workflow] No active workflows found for location {location_id}. Skipping workflow execution.")
                        return {
                            'success': True,
                            'message': f'No active workflows found for location {location_id}. Workflow skipped.',
                            'location_id': location_id,
                            'workflow_skipped': True
                        }
                    
                    _logger.info(f"[Trigger Workflow] Found {len(active_workflows)} active workflows for location {location_id}")
            
            # Update status to processing
            self.write({
                'status': 'processing',
                'last_triggered': fields.Datetime.now()
            })
            
            # Prepare workflow context
            workflow_context = {
                'trigger': self,
                'event_data': event_data or {},
                'context_data': context_data or {},
                'location': self.location_id,
                'timestamp': fields.Datetime.now()
            }
            
            _logger.info(f"[Trigger Workflow] Executing workflow for trigger {self.external_id} with key {self.key}")
            _logger.info(f"[Trigger Workflow] Received event_data: {event_data}")
            _logger.info(f"[Trigger Workflow] Context data: {context_data}")
            
            # Execute based on trigger key
            if self.key == 'call_processing' or self.key == 'cs_ai_call_summary' or self.event_type == 'CALL':
                result = self._execute_call_processing(workflow_context)
            elif self.key == 'contact_enrichment' or self.event_type == 'CONTACT_CREATED':
                result = self._execute_contact_enrichment(workflow_context)
            elif self.key == 'lead_scoring' or self.event_type == 'LEAD_STATUS_CHANGED':
                result = self._execute_lead_scoring(workflow_context)
            elif self.key == 'ai_summary':
                result = self._execute_ai_summary_workflow(workflow_context)
            elif self.key == 'crm_update':
                result = self._execute_crm_update_workflow(workflow_context)
            elif self.key == 'notification_send':
                result = self._execute_notification_workflow(workflow_context)
            elif self.key == 'task_create':
                result = self._execute_task_creation_workflow(workflow_context)
            else:
                result = self._execute_default_workflow(workflow_context)
            
            # Update success status
            self.write({
                'status': 'active',
                'trigger_count': self.trigger_count + 1,
                'error_message': False
            })
            
            _logger.info(f"[Trigger Workflow] Successfully executed workflow for trigger {self.external_id}")
            return result
            
        except Exception as e:
            error_msg = f"Error executing workflow: {str(e)}"
            _logger.error(f"[Trigger Workflow] {error_msg}", exc_info=True)
            
            # Update error status
            self.write({
                'status': 'error',
                'error_message': error_msg
            })
            
            return {
                'success': False,
                'error': error_msg,
                'trigger_id': self.id
            }
 
    def _execute_call_processing(self, context):
        """Execute call processing workflow"""
        try:
            _logger.info(f"[Call Processing] Starting call processing workflow")
            
            # Extract data from context
            event_data = context.get('event_data', {})
            message_id = event_data.get('messageId')
            contact_id = event_data.get('contactId')
            call_duration = event_data.get('callDuration', 0)
            _logger.info(f"[Call Processing] Call context: {context}")
            # Extract custom prompt from event data (nested structure)
            custom_prompt = None
            if 'data' in event_data and isinstance(event_data['data'], dict):
                custom_prompt = event_data['data'].get('cs_vision_summary_prompt')
            else:
                custom_prompt = event_data.get('cs_vision_summary_prompt')
            
            # Fail fast if no custom prompt provided
            if not custom_prompt:
                _logger.warning("[Call Processing] Missing required field: cs_vision_summary_prompt")
                return {
                    "success": False,
                    "error_code": "missing_field",
                    "message": "Missing required field: cs_vision_summary_prompt",
                }
            
            _logger.info(f"[Call Processing] Event data keys: {list(event_data.keys())}")
            _logger.info(f"[Call Processing] Custom prompt found: {bool(custom_prompt)}")
            if custom_prompt:
                _logger.info(f"[Call Processing] Custom prompt: {custom_prompt[:100]}...")
            
            # Check for minimum duration requirement (must be provided by caller)
            minimum_duration = context.get('cs_vision_call_minimum_duration')
            if minimum_duration is None:
                _logger.warning("[Call Processing] Missing required field: cs_vision_call_minimum_duration")
                return {
                    "success": False,
                    "error_code": "missing_field",
                    "message": "Missing required field: cs_vision_call_minimum_duration",
                }

            # Coerce minimum_duration to int if provided as string
            try:
                minimum_duration = int(minimum_duration)
            except Exception:
                _logger.warning(f"[Call Processing] Invalid cs_vision_call_minimum_duration: {minimum_duration}")
                return {
                    "success": False,
                    "error_code": "invalid_field",
                    "message": "cs_vision_call_minimum_duration must be an integer",
                    "field": "cs_vision_call_minimum_duration",
                }
            
            if call_duration < minimum_duration:
                _logger.info(f"[Call Processing] Call duration ({call_duration}s) < minimum ({minimum_duration}s). Skipping AI processing.")
                
                # Get transcript records for human-readable format
                message_record = self.env['ghl.contact.message'].sudo().search([
                    ('ghl_id', '=', message_id)
                ], limit=1)
                
                transcript_text = ""
                if message_record:
                    transcript_records = self.env['ghl.contact.message.transcript'].sudo().search([
                        ('message_id', '=', message_record.id)
                    ], order='sentence_index asc')
                    
                    if transcript_records:
                        for record in transcript_records:
                            speaker = "Agent" if record.media_channel == "agent" else "Customer"
                            time_range = f"[{record.start_time_seconds:.1f}s - {record.end_time_seconds:.1f}s]"
                            transcript_text += f"{speaker} {time_range}: {record.transcript}\n"
                
                return {
                    "success": True,
                    "message": f"Call duration ({call_duration} seconds) is below minimum threshold ({minimum_duration} seconds). AI processing skipped.",
                    "call_duration_seconds": call_duration,
                    "minimum_duration_required": minimum_duration,
                    "summary": "Call too short for analysis",
                    "keywords": [],
                    "sentiment": "neutral",
                    "action_items": [],
                    "confidence_score": 0.0,
                    "duration_analyzed": f"{call_duration} seconds",
                    "speakers_detected": 0,
                    "raw_transcript_array": transcript_text.strip()
                }
            
            # Continue with normal AI processing
            _logger.info(f"[Call Processing] Proceeding with AI processing for message: {message_id}")
            
            # Generate AI summary with custom prompt
            summary = self._generate_call_summary(message_id, contact_id, custom_prompt=custom_prompt)
            
            if summary:
                _logger.info(f"[Call Processing] AI summary generated successfully")
                return summary
            else:
                _logger.warning(f"[Call Processing] Failed to generate AI summary")
                return {
                    "success": False,
                    "message": "Failed to generate AI summary",
                    "summary": "Error generating summary",
                    "keywords": [],
                    "sentiment": "neutral",
                    "action_items": [],
                    "confidence_score": 0.0,
                    "duration_analyzed": "Unknown",
                    "speakers_detected": 0,
                    "raw_transcript_array": ""
                }
                
        except Exception as e:
            _logger.error(f"[Call Processing] Error in call processing workflow: {str(e)}", exc_info=True)
            return {
                "success": False,
                "message": f"Error in call processing: {str(e)}",
                "summary": "Error processing call",
                "keywords": [],
                "sentiment": "neutral",
                "action_items": [],
                "confidence_score": 0.0,
                "duration_analyzed": "Unknown",
                "speakers_detected": 0,
                "raw_transcript_array": ""
            }

    def _execute_ai_summary_workflow(self, context):
        """Execute AI summary workflow"""
        try:
            event_data = context.get('event_data', {})
            
            message_id = event_data.get('messageId')
            contact_id = event_data.get('contactId')
            recording_url = event_data.get('attachments', [None])[0]
            
            result = {
                'success': True,
                'workflow_type': 'ai_summary',
                'summary_data': {}
            }
            
            # Generate AI summary
            if message_id and recording_url:
                summary = self._generate_call_summary(message_id, contact_id, recording_url)
                if summary:
                    result['summary_data'] = summary
                    
                    # Update conversation with summary
                    self._update_conversation_with_summary(message_id, summary)
                    
                    # Create summary record
                    summary_record = self._create_summary_record(message_id, contact_id, summary)
                    if summary_record:
                        result['summary_record_id'] = summary_record
            
            return result
            
        except Exception as e:
            _logger.error(f"[AI Summary] Error: {str(e)}", exc_info=True)
            return {'success': False, 'error': str(e)}

    def _execute_contact_enrichment(self, context):
        """Execute contact enrichment workflow"""
        try:
            event_data = context.get('event_data', {})
            contact_id = event_data.get('contactId')
            
            result = {
                'success': True,
                'workflow_type': 'contact_enrichment',
                'enrichment_data': {}
            }
            
            if contact_id:
                # Find contact
                contact = self.env['ghl.location.contact'].sudo().search([
                    ('external_id', '=', contact_id),
                    ('location_id', '=', self.location_id.id)
                ], limit=1)
                
                if contact:
                    # Enrich contact data
                    enriched_data = self._enrich_contact_data(contact, event_data)
                    if enriched_data:
                        contact.write(enriched_data)
                        result['enrichment_data'] = enriched_data
                        
                        # Update lead score if applicable
                        lead_score = self._calculate_lead_score(contact, event_data)
                        if lead_score:
                            result['lead_score'] = lead_score
            
            return result
            
        except Exception as e:
            _logger.error(f"[Contact Enrichment] Error: {str(e)}", exc_info=True)
            return {'success': False, 'error': str(e)}

    def _execute_crm_update_workflow(self, context):
        """Execute CRM update workflow"""
        try:
            event_data = context.get('event_data', {})
            
            result = {
                'success': True,
                'workflow_type': 'crm_update',
                'crm_updates': []
            }
            
            # Update CRM records based on event data
            contact_id = event_data.get('contactId')
            if contact_id:
                # Find or create CRM lead/opportunity
                crm_record = self._find_or_create_crm_record(contact_id, event_data)
                if crm_record:
                    # Update CRM record
                    updates = self._update_crm_record(crm_record, event_data)
                    result['crm_updates'].extend(updates)
            
            return result
            
        except Exception as e:
            _logger.error(f"[CRM Update] Error: {str(e)}", exc_info=True)
            return {'success': False, 'error': str(e)}

    def _execute_notification_workflow(self, context):
        """Execute notification workflow"""
        try:
            event_data = context.get('event_data', {})
            
            result = {
                'success': True,
                'workflow_type': 'notification',
                'notifications_sent': []
            }
            
            # Send notifications based on trigger configuration
            notification_config = self._get_notification_config()
            
            for notification in notification_config:
                sent = self._send_notification(notification, event_data)
                if sent:
                    result['notifications_sent'].append(notification['type'])
            
            return result
            
        except Exception as e:
            _logger.error(f"[Notification] Error: {str(e)}", exc_info=True)
            return {'success': False, 'error': str(e)}

    def _execute_task_creation_workflow(self, context):
        """Execute task creation workflow"""
        try:
            event_data = context.get('event_data', {})
            
            result = {
                'success': True,
                'workflow_type': 'task_creation',
                'tasks_created': []
            }
            
            # Create tasks based on event data
            task_configs = self._get_task_configs()
            
            for task_config in task_configs:
                if self._should_create_task(task_config, event_data):
                    task = self._create_task(task_config, event_data)
                    if task:
                        result['tasks_created'].append({
                            'task_id': task.id,
                            'title': task.title,
                            'type': task_config['type']
                        })
            
            return result
            
        except Exception as e:
            _logger.error(f"[Task Creation] Error: {str(e)}", exc_info=True)
            return {'success': False, 'error': str(e)}

    def _execute_default_workflow(self, context):
        """Execute default workflow for unknown trigger types"""
        try:
            event_data = context.get('event_data', {})
            
            result = {
                'success': True,
                'workflow_type': 'default',
                'message': f"Default workflow executed for trigger {self.key}",
                'event_data_keys': list(event_data.keys())
            }
            
            # Log the event
            self._log_workflow_event(event_data)
            
            return result
            
        except Exception as e:
            _logger.error(f"[Default Workflow] Error: {str(e)}", exc_info=True)
            return {'success': False, 'error': str(e)}

    # Helper methods for workflow execution
    def _generate_call_summary(self, message_id, contact_id, recording_url=None, custom_prompt=None):
        """Generate AI summary for call"""
        try:
            # Get the AI service
            ai_service = self.env['cyclsales.vision.ai'].sudo().get_default_ai_service()
            if ai_service:
                # Get the message record to fetch transcript
                message_record = self.env['ghl.contact.message'].sudo().search([
                    ('ghl_id', '=', message_id)
                ], limit=1)
                
                transcript = None
                location_id = None
                transcript_records = None
                
                if message_record:
                    # Get location from the message record
                    if hasattr(message_record, 'location_id') and message_record.location_id:
                        location_id = message_record.location_id.id
                    elif hasattr(message_record, 'conversation_id') and message_record.conversation_id:
                        # Try to get location from conversation
                        if hasattr(message_record, 'conversation_id', 'location_id') and message_record.conversation_id.location_id:
                            location_id = message_record.conversation_id.location_id.id
                    
                    # Always try to fetch transcript from GHL API
                    try:
                        transcript_result = self.env['ghl.contact.message.transcript'].sudo().fetch_transcript_for_message(message_record.id)
                        
                        if transcript_result.get('success'):
                            # Get the newly fetched transcript records
                            transcript_records = self.env['ghl.contact.message.transcript'].sudo().search([
                                ('message_id', '=', message_record.id)
                            ], order='sentence_index asc')
                            
                            if transcript_records:
                                transcript = transcript_records.get_full_transcript_text()
                                _logger.info(f"[AI Call Summary] Successfully fetched transcript: {len(transcript)} characters")
                            else:
                                _logger.warning(f"[AI Call Summary] No transcript records found after API fetch")
                        else:
                            _logger.warning(f"[AI Call Summary] Failed to fetch transcript from GHL API: {transcript_result.get('error')}")
                    except Exception as fetch_error:
                        _logger.error(f"[AI Call Summary] Error fetching transcript from GHL API: {str(fetch_error)}")
                    
                    # Fallback to message body if no transcript available
                    if not transcript and message_record.body:
                        transcript = message_record.body
                        _logger.info(f"[AI Call Summary] Using message body as fallback transcript")
                
                # Fallback to trigger's location if not found
                if not location_id and self.location_id:
                    location_id = self.location_id.id
                
                if transcript:
                    _logger.info(f"[AI Call Summary] Generating AI summary for message {message_id}")
                    summary = ai_service.generate_summary(
                        message_id=message_id,
                        contact_id=contact_id,
                        recording_url=recording_url,
                        transcript=transcript,
                        location_id=location_id,
                        custom_prompt=custom_prompt
                    )
                    
                    # Add raw transcript array to the response
                    if summary and transcript_records:
                        transcript_text = ""
                        for record in transcript_records:
                            speaker = "Agent" if record.media_channel == "agent" else "Customer"
                            time_range = f"[{record.start_time_seconds:.1f}s - {record.end_time_seconds:.1f}s]"
                            transcript_text += f"{speaker} {time_range}: {record.transcript}\n"
                        
                        summary['raw_transcript_array'] = transcript_text.strip()
                    
                    return summary
                else:
                    _logger.warning(f"[AI Call Summary] No transcript available for message {message_id}")
                    return {
                        'summary': f"No transcript available for call message {message_id}",
                        'keywords': ['call', 'no_transcript'],
                        'sentiment': 'neutral',
                        'action_items': ['Fetch transcript manually'],
                        'confidence_score': 0.0,
                        'duration_analyzed': 'Unknown',
                        'speakers_detected': 0,
                        'raw_transcript_array': ''
                    }
            else:
                # Fallback: create basic summary
                return {
                    'summary': f"Call summary for message {message_id}",
                    'keywords': ['call', 'summary'],
                    'sentiment': 'neutral',
                    'action_items': [],
                    'confidence_score': 0.0,
                    'duration_analyzed': 'Unknown',
                    'speakers_detected': 0,
                    'raw_transcript_array': ''
                }
        except Exception as e:
            _logger.error(f"Error generating call summary: {str(e)}")
            return None

    def _create_follow_up_task(self, event_data):
        """Create follow-up task for call"""
        try:
            contact_id = event_data.get('contactId')
            call_duration = event_data.get('callDuration', 0)
            
            if contact_id:
                contact = self.env['ghl.location.contact'].sudo().search([
                    ('external_id', '=', contact_id),
                    ('location_id', '=', self.location_id.id)
                ], limit=1)
                
                if contact:
                    task = self.env['ghl.contact.task'].sudo().create({
                        'contact_id': contact.id,
                        'title': f"Follow-up from {call_duration}s call",
                        'body': f"Call duration: {call_duration} seconds",
                        'due_date': fields.Datetime.now() + timedelta(days=1)
                    })
                    return task.id
        except Exception as e:
            _logger.error(f"Error creating follow-up task: {str(e)}")
        return None

    def _update_contact_call_info(self, contact_id, event_data):
        """Update contact with call information"""
        try:
            contact = self.env['ghl.location.contact'].sudo().search([
                ('external_id', '=', contact_id),
                ('location_id', '=', self.location_id.id)
            ], limit=1)
            
            if contact:
                # Only update fields that exist in the model
                updates = {
                    'last_touch_date': fields.Datetime.now(),
                }
                
                # Log call information instead of trying to update non-existent fields
                call_duration = event_data.get('callDuration', 0)
                _logger.info(f"[Contact Update] Call info for contact {contact_id}: duration={call_duration}s, direction={event_data.get('direction')}")
                
                contact.write(updates)
                return True
        except Exception as e:
            _logger.error(f"Error updating contact call info: {str(e)}")
        return False

    def execute_workflow_from_ui(self):
        """Execute workflow from UI button - for testing purposes"""
        self.ensure_one()
        
        # Create sample event data for testing
        sample_event_data = {
            'messageId': f'test_message_{self.id}',
            'contactId': f'test_contact_{self.id}',
            'direction': 'inbound',
            'callDuration': 300,  # 5 minutes
            'attachments': ['https://example.com/recording.mp3'],
            'locationId': self.location_id.location_id if self.location_id else None,
            'companyId': self.company_id
        }
        
        # Execute the workflow
        result = self.execute_workflow(
            event_data=sample_event_data,
            context_data={'source': 'ui_test'}
        )
        
        # Show result to user
        if result.get('success'):
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Workflow Executed',
                    'message': f"Workflow executed successfully. Actions taken: {', '.join(result.get('actions_taken', []))}",
                    'type': 'success',
                }
            }
        else:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Workflow Error',
                    'message': f"Error executing workflow: {result.get('error', 'Unknown error')}",
                    'type': 'danger',
                }
            }

    def _send_call_notification(self, event_data):
        """Send notification for call event"""
        try:
            # Implement notification logic here
            # This could send email, SMS, or create internal notifications
            _logger.info(f"Sending call notification for event: {event_data}")
            return True
        except Exception as e:
            _logger.error(f"Error sending call notification: {str(e)}")
            return False

    def _execute_lead_scoring(self, context):
        """Execute lead scoring workflow"""
        try:
            event_data = context.get('event_data', {})
            
            result = {
                'success': True,
                'workflow_type': 'lead_scoring',
                'score_data': {}
            }
            
            # Implement lead scoring logic here
            contact_id = event_data.get('contactId')
            if contact_id:
                # Calculate lead score based on various factors
                score = self._calculate_lead_score_from_event(event_data)
                if score:
                    result['score_data'] = score
            
            return result
            
        except Exception as e:
            _logger.error(f"[Lead Scoring] Error: {str(e)}", exc_info=True)
            return {'success': False, 'error': str(e)}

    def _calculate_lead_score_from_event(self, event_data):
        """Calculate lead score from event data"""
        try:
            score = 0
            factors = []
            
            # Factor 1: Call duration
            call_duration = event_data.get('callDuration', 0)
            if call_duration > 300:  # 5 minutes
                score += 20
                factors.append('long_call')
            elif call_duration > 60:  # 1 minute
                score += 10
                factors.append('medium_call')
            
            # Factor 2: Call direction
            if event_data.get('direction') == 'inbound':
                score += 15
                factors.append('inbound_call')
            
            # Factor 3: Contact history
            contact_id = event_data.get('contactId')
            if contact_id:
                contact = self.env['ghl.location.contact'].sudo().search([
                    ('external_id', '=', contact_id),
                    ('location_id', '=', self.location_id.id)
                ], limit=1)
                
                if contact:
                    # Add score based on contact history
                    if contact.task_ids:
                        score += 5
                        factors.append('has_tasks')
                    
                    if contact.conversation_ids:
                        score += 5
                        factors.append('has_conversations')
            
            return {
                'score': score,
                'factors': factors,
                'level': 'hot' if score >= 30 else 'warm' if score >= 15 else 'cold'
            }
            
        except Exception as e:
            _logger.error(f"Error calculating lead score: {str(e)}")
            return None

    def _get_location_token(self):
        """Get location access token for API calls"""
        if self.location_id:
            app = self.env['cyclsales.application'].sudo().search([
                ('app_id', '=', '684c5cc0736d09f78555981f')
            ], limit=1)
            
            if app:
                return self.location_id.fetch_location_token(app.access_token, app.company_id)
        return None

    def _log_workflow_event(self, event_data):
        """Log workflow event for debugging"""
        try:
            # Check if the model exists before trying to create
            if 'workflow.event.log' in self.env:
                self.env['workflow.event.log'].sudo().create({
                    'trigger_id': self.id,
                    'event_type': self.event_type,
                    'event_data': json.dumps(event_data),
                    'timestamp': fields.Datetime.now()
                })
            else:
                _logger.info(f"[Workflow Log] workflow.event.log model not available, skipping log creation")
        except Exception as e:
            _logger.error(f"Error logging workflow event: {str(e)}")

    # Additional helper methods can be added here as needed
    def _enrich_contact_data(self, contact, event_data):
        """Enrich contact data based on event"""
        # Implement contact enrichment logic
        return {}

    def _calculate_lead_score(self, contact, event_data):
        """Calculate lead score based on event data"""
        # Implement lead scoring logic
        return None

    def _find_or_create_crm_record(self, contact_id, event_data):
        """Find or create CRM record for contact"""
        # Implement CRM record logic
        return None

    def _update_crm_record(self, crm_record, event_data):
        """Update CRM record with event data"""
        # Implement CRM update logic
        return []

    def _get_notification_config(self):
        """Get notification configuration for this trigger"""
        # Implement notification config logic
        return []

    def _send_notification(self, notification_config, event_data):
        """Send notification based on configuration"""
        # Implement notification sending logic
        return False

    def _get_task_configs(self):
        """Get task configurations for this trigger"""
        # Implement task config logic
        return []

    def _should_create_task(self, task_config, event_data):
        """Determine if task should be created based on event data"""
        # Implement task creation logic
        return False

    def _create_task(self, task_config, event_data):
        """Create task based on configuration"""
        # Implement task creation logic
        return None

    def _update_conversation_with_summary(self, message_id, summary):
        """Update conversation with AI summary"""
        # Implement conversation update logic
        pass

    def _create_summary_record(self, message_id, contact_id, summary):
        """Create summary record"""
        # Implement summary record creation logic
        return None

    def force_generate_ai_summary(self, message_id):
        """
        Force generate AI summary for a specific message (for testing)
        """
        try:
            _logger.info(f"[Force AI Summary] Generating AI summary for message {message_id}")
            
            # Get the message record
            message_record = self.env['ghl.contact.message'].sudo().search([
                ('ghl_id', '=', message_id)
            ], limit=1)
            
            if not message_record:
                return {
                    'success': False,
                    'error': f'Message {message_id} not found'
                }
            
            # Generate summary with force flag
            summary_result = self._generate_call_summary(
                message_id=message_id,
                contact_id=message_record.contact_id.external_id if message_record.contact_id else None
            )
            
            if summary_result:
                return {
                    'success': True,
                    'summary': summary_result,
                    'message': f'Successfully generated AI summary for message {message_id}'
                }
            else:
                return {
                    'success': False,
                    'error': 'Failed to generate AI summary'
                }
                
        except Exception as e:
            _logger.error(f"[Force AI Summary] Error: {str(e)}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }

 