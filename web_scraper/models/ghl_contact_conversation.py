from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import requests
import json
import logging
from datetime import datetime

_logger = logging.getLogger(__name__)


class GhlContactConversation(models.Model):
    _name = 'ghl.contact.conversation'
    _description = 'GHL Contact Conversation'
    _order = 'create_date desc'
    _rec_name = 'full_name'

    # GHL API fields
    ghl_id = fields.Char('GHL ID', required=True, index=True)
    contact_id = fields.Many2one('ghl.location.contact', string='Contact', required=True, ondelete='cascade')
    location_id = fields.Many2one('installed.location', string='Location', required=True, ondelete='cascade')
    
    # Conversation details
    last_message_body = fields.Text('Last Message Body')
    last_message_type = fields.Selection([
        ('TYPE_CALL', 'Call'),
        ('TYPE_SMS', 'SMS'),
        ('TYPE_EMAIL', 'Email'),
        ('TYPE_SMS_REVIEW_REQUEST', 'SMS Review Request'),
        ('TYPE_WEBCHAT', 'Webchat'),
        ('TYPE_SMS_NO_SHOW_REQUEST', 'SMS No Show Request'),
        ('TYPE_NO_SHOW', 'No Show'),
        ('TYPE_CAMPAIGN_SMS', 'Campaign SMS'),
        ('TYPE_CAMPAIGN_CALL', 'Campaign Call'),
        ('TYPE_CAMPAIGN_EMAIL', 'Campaign Email'),
        ('TYPE_CAMPAIGN_VOICEMAIL', 'Campaign Voicemail'),
        ('TYPE_FACEBOOK', 'Facebook'),
        ('TYPE_CAMPAIGN_FACEBOOK', 'Campaign Facebook'),
        ('TYPE_CAMPAIGN_MANUAL_CALL', 'Campaign Manual Call'),
        ('TYPE_CAMPAIGN_MANUAL_SMS', 'Campaign Manual SMS'),
        ('TYPE_GMB', 'Google My Business'),
        ('TYPE_CAMPAIGN_GMB', 'Campaign Google My Business'),
        ('TYPE_REVIEW', 'Review'),
        ('TYPE_INSTAGRAM', 'Instagram'),
        ('TYPE_WHATSAPP', 'WhatsApp'),
        ('TYPE_CUSTOM_SMS', 'Custom SMS'),
        ('TYPE_CUSTOM_EMAIL', 'Custom Email'),
        ('TYPE_CUSTOM_PROVIDER_SMS', 'Custom Provider SMS'),
        ('TYPE_CUSTOM_PROVIDER_EMAIL', 'Custom Provider Email'),
        ('TYPE_IVR_CALL', 'IVR Call'),
        ('TYPE_ACTIVITY_CONTACT', 'Activity Contact'),
        ('TYPE_ACTIVITY_INVOICE', 'Activity Invoice'),
        ('TYPE_ACTIVITY_PAYMENT', 'Activity Payment'),
        ('TYPE_ACTIVITY_OPPORTUNITY', 'Activity Opportunity'),
        ('TYPE_LIVE_CHAT', 'Live Chat'),
        ('TYPE_LIVE_CHAT_INFO_MESSAGE', 'Live Chat Info Message'),
        ('TYPE_ACTIVITY_APPOINTMENT', 'Activity Appointment'),
        ('TYPE_FACEBOOK_COMMENT', 'Facebook Comment'),
        ('TYPE_INSTAGRAM_COMMENT', 'Instagram Comment'),
        ('TYPE_CUSTOM_CALL', 'Custom Call'),
        ('TYPE_INTERNAL_COMMENT', 'Internal Comment'),
    ], string='Last Message Type')
    type = fields.Selection([
        ('TYPE_PHONE', 'Phone'),
        ('TYPE_SMS', 'SMS'),
        ('TYPE_EMAIL', 'Email'),
        ('TYPE_CHAT', 'Chat'),
    ], string='Conversation Type')
    unread_count = fields.Integer('Unread Count', default=0)
    
    # Contact information
    full_name = fields.Char('Full Name')
    contact_name = fields.Char('Contact Name')
    email = fields.Char('Email')
    phone = fields.Char('Phone')
    
    # Metadata
    create_date = fields.Datetime('Created Date', readonly=True)
    write_date = fields.Datetime('Last Updated', readonly=True)
    
    # Computed fields
    display_name = fields.Char('Display Name', compute='_compute_display_name', store=True)
    
    _sql_constraints = [
        ('unique_ghl_id', 'unique(ghl_id)', 'GHL ID must be unique!'),
    ]
    
    @api.depends('full_name', 'contact_name', 'ghl_id')
    def _compute_display_name(self):
        for record in self:
            if record.full_name:
                record.display_name = record.full_name
            elif record.contact_name:
                record.display_name = record.contact_name
            else:
                record.display_name = f"Conversation {record.ghl_id}"
    
    @api.constrains('contact_id', 'location_id')
    def _check_contact_location_consistency(self):
        for record in self:
            if record.contact_id and record.location_id:
                # Compare contact's location_id with conversation's location_id
                # Both are now Many2one fields pointing to installed.location
                if record.contact_id.location_id != record.location_id:
                    raise ValidationError(_('Contact location must match conversation location.'))
    
    def name_get(self):
        result = []
        for record in self:
            name = record.display_name or f"Conversation {record.ghl_id}"
            result.append((record.id, name))
        return result
    
    @api.model
    def fetch_conversations_from_ghl(self, location_token, location_id, company_id=None):
        """
        Fetch conversations from GHL API for a specific location
        
        Args:
            location_token (str): Location-level access token
            location_id (str): GHL location ID
            company_id (str): Company ID (optional, for logging)
            
        Returns:
            dict: Result with success status and data
        """
        try:
            _logger.info(f"Fetching conversations for location {location_id}")
            
            # GHL API endpoint for conversations
            url = f"https://services.leadconnectorhq.com/conversations/search"
            
            headers = {
                'Accept': 'application/json',
                'Authorization': f'Bearer {location_token}',
                'Version': '2021-04-15'
            }
            
            params = {
                'locationId': location_id
            }
            
            _logger.info(f"Making conversations API request to: {url}")
            _logger.info(f"Request params: {params}")
            # Don't log headers to avoid exposing access token
            
            response = requests.get(url, headers=headers, params=params, timeout=30)
            
            _logger.info(f"GHL conversations API response status: {response.status_code}")
            if response.status_code == 200:
                _logger.info(f"GHL conversations API response length: {len(response.text)} characters")
            else:
                _logger.error(f"GHL conversations API error response: {response.text[:200]}...")
            
            if response.status_code == 200:
                data = response.json()
                conversations = data.get('conversations', [])
                total = data.get('total', 0)
                
                _logger.info(f"Successfully fetched {len(conversations)} conversations (total: {total})")
                
                return {
                    'success': True,
                    'conversations': conversations,
                    'total': total,
                    'message': f'Successfully fetched {len(conversations)} conversations'
                }
            else:
                _logger.error(f"Failed to fetch conversations. Status: {response.status_code}, Response: {response.text}")
                return {
                    'success': False,
                    'conversations': [],
                    'total': 0,
                    'message': f'API request failed with status {response.status_code}: {response.text}'
                }
                
        except requests.exceptions.RequestException as e:
            _logger.error(f"Request exception while fetching conversations: {str(e)}")
            return {
                'success': False,
                'conversations': [],
                'total': 0,
                'message': f'Request failed: {str(e)}'
            }
        except Exception as e:
            _logger.error(f"Unexpected error while fetching conversations: {str(e)}")
            return {
                'success': False,
                'conversations': [],
                'total': 0,
                'message': f'Unexpected error: {str(e)}'
            }
    
    @api.model
    def sync_conversations_for_location(self, app_access_token, location_id, company_id=None):
        """
        Sync conversations for a specific location using two-step token process
        
        Args:
            app_access_token (str): Agency-level access token
            location_id (str): GHL location ID
            company_id (str): Company ID
            
        Returns:
            dict: Result with success status and sync details
        """
        try:
            _logger.info(f"Starting conversation sync for location {location_id}")
            
            # Validate company_id is provided
            if not company_id:
                return {
                    'success': False,
                    'message': 'company_id is required for conversation sync',
                    'created': 0,
                    'updated': 0,
                    'errors': ['company_id is required']
                }
            
            _logger.info(f"Using company_id: {company_id}")
            
            # Step 1: Get location token using agency token
            location_token_result = self._get_location_token(app_access_token, location_id, company_id)
            
            if not location_token_result['success']:
                return {
                    'success': False,
                    'message': f"Failed to get location token: {location_token_result['message']}",
                    'created': 0,
                    'updated': 0,
                    'errors': []
                }
            
            location_token = location_token_result['access_token']
            
            # Step 2: Fetch conversations using location token
            conversations_result = self.fetch_conversations_from_ghl(location_token, location_id, company_id)
            
            if not conversations_result['success']:
                return {
                    'success': False,
                    'message': f"Failed to fetch conversations: {conversations_result['message']}",
                    'created': 0,
                    'updated': 0,
                    'errors': []
                }
            
            # Step 3: Process and save conversations
            return self._process_conversations(conversations_result['conversations'], location_id, company_id)
            
        except Exception as e:
            _logger.error(f"Error in sync_conversations_for_location: {str(e)}")
            return {
                'success': False,
                'message': f'Unexpected error: {str(e)}',
                'created': 0,
                'updated': 0,
                'errors': []
            }
    
    def _get_location_token(self, app_access_token, location_id, company_id=None):
        """
        Get location token using agency token (same as in ghl_contact_task)
        """
        try:
            url = "https://services.leadconnectorhq.com/oauth/locationToken"
            
            headers = {
                'Accept': 'application/json',
                'Content-Type': 'application/x-www-form-urlencoded',
                'Authorization': f'Bearer {app_access_token}',
                'Version': '2021-07-28',
            }
            
            data = {
                'companyId': company_id,
                'locationId': location_id
            }
            
            _logger.info(f"Getting location token for location {location_id}")
            
            response = requests.post(url, headers=headers, data=data, timeout=30)
            
            _logger.info(f"Location token response for conversations: {response.status_code}")
            if response.status_code != 201:
                _logger.error(f"Location token error response: {response.text[:200]}...")
            
            if response.status_code == 201:
                token_data = response.json()
                return {
                    'success': True,
                    'access_token': token_data.get('access_token'),
                    'message': 'Location token obtained successfully'
                }
            else:
                _logger.error(f"Failed to get location token. Status: {response.status_code}, Response: {response.text}")
                return {
                    'success': False,
                    'access_token': None,
                    'message': f'Failed to get location token: {response.status_code} - {response.text}'
                }
                
        except Exception as e:
            _logger.error(f"Error getting location token: {str(e)}")
            return {
                'success': False,
                'access_token': None,
                'message': f'Error getting location token: {str(e)}'
            }
    
    def _process_conversations(self, conversations_data, location_id, company_id=None):
        """
        Process and save conversations to database
        """
        try:
            created_count = 0
            updated_count = 0
            errors = []
            
            # Get the installed location record
            installed_location = self.env['installed.location'].search([('location_id', '=', location_id)], limit=1)
            if not installed_location:
                errors.append(f"Installed location not found for location_id: {location_id}")
                return {
                    'success': False,
                    'message': f"Installed location not found for location_id: {location_id}",
                    'created': 0,
                    'updated': 0,
                    'errors': errors
                }
            
            _logger.info(f"Processing {len(conversations_data)} conversations for location {location_id}")
            
            # Track statistics
            missing_contacts = 0
            processed_conversations = 0
            
            for conversation_data in conversations_data:
                try:
                    ghl_id = conversation_data.get('id')
                    contact_id = conversation_data.get('contactId')
                    
                    if not ghl_id:
                        errors.append("Conversation missing GHL ID")
                        continue
                    
                    # Find the contact record
                    contact = self.env['ghl.location.contact'].search([('external_id', '=', contact_id)], limit=1)
                    if not contact:
                        missing_contacts += 1
                        _logger.warning(f"Contact not found for contact_id: {contact_id} (conversation: {ghl_id})")
                        continue
                    
                    processed_conversations += 1
                    
                    # Check if conversation already exists
                    existing_conversation = self.search([('ghl_id', '=', ghl_id)], limit=1)
                    
                    # Prepare conversation values
                    conversation_values = {
                        'ghl_id': ghl_id,
                        'contact_id': contact.id,
                        'location_id': installed_location.id,
                        'last_message_body': conversation_data.get('lastMessageBody', ''),
                        'last_message_type': conversation_data.get('lastMessageType', ''),
                        'type': conversation_data.get('type', ''),
                        'unread_count': conversation_data.get('unreadCount', 0),
                        'full_name': conversation_data.get('fullName', ''),
                        'contact_name': conversation_data.get('contactName', ''),
                        'email': conversation_data.get('email', ''),
                        'phone': conversation_data.get('phone', ''),
                    }
                    
                    if existing_conversation:
                        # Update existing conversation
                        existing_conversation.write(conversation_values)
                        updated_count += 1
                        _logger.info(f"Updated conversation {ghl_id}")
                    else:
                        # Create new conversation
                        self.create(conversation_values)
                        created_count += 1
                        _logger.info(f"Created conversation {ghl_id}")
                        
                except Exception as e:
                    error_msg = f"Error processing conversation {conversation_data.get('id', 'unknown')}: {str(e)}"
                    errors.append(error_msg)
                    _logger.error(error_msg)
            
            _logger.info(f"Conversation sync completed for location {location_id}: {created_count} created, {updated_count} updated, {missing_contacts} missing contacts, {processed_conversations} processed")
            
            return {
                'success': True,
                'message': f'Successfully synced conversations: {created_count} created, {updated_count} updated, {missing_contacts} missing contacts',
                'created': created_count,
                'updated': updated_count,
                'missing_contacts': missing_contacts,
                'processed_conversations': processed_conversations,
                'errors': errors
            }
            
        except Exception as e:
            _logger.error(f"Error processing conversations: {str(e)}")
            return {
                'success': False,
                'message': f'Error processing conversations: {str(e)}',
                'created': 0,
                'updated': 0,
                'errors': [str(e)]
            } 