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
    external_id = fields.Char('External ID', related='ghl_id', store=True)  # Alias for ghl_id
    contact_id = fields.Many2one('ghl.location.contact', string='Contact', required=True, ondelete='cascade')
    location_id = fields.Many2one('installed.location', string='Location', required=True, ondelete='cascade')
    
    # Conversation details
    channel = fields.Char('Channel')  # Add channel field
    status = fields.Char('Status')  # Add status field
    subject = fields.Char('Subject')  # Add subject field
    last_message = fields.Text('Last Message')  # Add last_message field
    date_created = fields.Datetime('Date Created')  # Add date_created field
    date_modified = fields.Datetime('Date Modified')  # Add date_modified field
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
    def fetch_conversations_from_ghl(self, location_token, location_id, company_id=None, max_pages=None):
        """
        Fetch conversations from GHL API for a specific location with pagination support
        
        Args:
            location_token (str): Location-level access token
            location_id (str): GHL location ID
            company_id (str): Company ID (optional, for logging)
            max_pages (int): Maximum number of pages to fetch (None for unlimited)
            
        Returns:
            dict: Result with success status and data
        """
        from .ghl_api_utils import fetch_conversations_with_pagination
        try:
            _logger.info(f"Fetching conversations for location {location_id} with pagination (max_pages: {max_pages})")
            
            result = fetch_conversations_with_pagination(location_token, location_id, max_pages)
            
            if result['success']:
                _logger.info(f"Successfully fetched {result['total_items']} conversations from {result['total_pages']} pages")
                return {
                    'success': True,
                    'conversations': result['items'],
                    'total': result['total_items'],
                    'pages_fetched': result['total_pages'],
                    'message': f'Successfully fetched {result["total_items"]} conversations from {result["total_pages"]} pages'
                }
            else:
                _logger.error(f"Failed to fetch conversations: {result.get('error')}")
                return {
                    'success': False,
                    'conversations': [],
                    'total': 0,
                    'pages_fetched': 0,
                    'message': result.get('error', 'Failed to fetch conversations')
                }
                
        except Exception as e:
            _logger.error(f"Unexpected error while fetching conversations: {str(e)}")
            import traceback
            _logger.error(f"Full traceback: {traceback.format_exc()}")
            return {
                'success': False,
                'conversations': [],
                'total': 0,
                'pages_fetched': 0,
                'message': f'Unexpected error: {str(e)}'
            }
    
    @api.model
    def sync_conversations_for_location(self, app_access_token, location_id, company_id=None, max_pages=None):
        """
        Sync conversations for a specific location using two-step token process with pagination support
        
        Args:
            app_access_token (str): Agency-level access token
            location_id (str): GHL location ID
            company_id (str): Company ID
            max_pages (int): Maximum number of pages to fetch (None for unlimited)
            
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
            
            # Step 2: Fetch conversations using location token with pagination
            conversations_result = self.fetch_conversations_from_ghl(location_token, location_id, company_id, max_pages)
            
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

    def sync_conversations_for_contact(self, access_token, location_id, contact_id, limit=100):
        """
        Sync conversations for a specific contact using the /conversations/search endpoint.
        After syncing conversations, fetch all messages for each conversation.
        """
        import requests
        import logging
        import json
        _logger = logging.getLogger(__name__)
        
        def ms_to_datetime(ms):
            if not ms:
                return None
            try:
                if isinstance(ms, datetime):
                    return ms
                ms = int(ms)
                return datetime.utcfromtimestamp(ms / 1000.0)
            except Exception:
                return None
        
        # Get company_id from ghl.agency.token (same as other models)
        agency_token = self.env['ghl.agency.token'].sudo().search([], order='create_date desc', limit=1)
        if not agency_token:
            return {
                'success': False,
                'message': 'No agency token found. Please ensure ghl.agency.token is configured.',
                'created': 0,
                'updated': 0,
                'errors': ['No agency token found']
            }
        
        company_id = agency_token.company_id
        if not company_id:
            return {
                'success': False,
                'message': 'No company_id found in agency token.',
                'created': 0,
                'updated': 0,
                'errors': ['No company_id found']
            }
        
        try:
            # Step 1: Get location token using agency token
            location_token_result = self._get_location_token(access_token, location_id, company_id)
            if not location_token_result.get('success'):
                return {
                    'success': False,
                    'message': f"Failed to get location token: {location_token_result.get('error', 'Unknown error')}",
                    'created': 0,
                    'updated': 0,
                    'errors': []
                }
            
            location_token = location_token_result.get('access_token')
            
            # Step 2: Fetch conversations using location token
            url = f"https://services.leadconnectorhq.com/conversations/search?locationId={location_id}&contactId={contact_id}&limit={limit}"
            headers = {
                'Accept': 'application/json',
                'Authorization': f'Bearer {location_token}',
                'Version': '2021-07-28',
            }
            
            _logger.info(f"Fetching conversations for contact {contact_id} at location {location_id}")
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                conversations = data.get('conversations', [])
                _logger.info(f"Found {len(conversations)} conversations for contact {contact_id}")
                
                # Find the installed location and contact records
                installed_location = self.env['installed.location'].sudo().search([
                    ('location_id', '=', location_id)
                ], limit=1)
                
                if not installed_location:
                    return {
                        'success': False,
                        'message': f'No installed location found for location_id: {location_id}',
                        'created': 0,
                        'updated': 0,
                        'errors': []
                    }
                
                contact_record = self.env['ghl.location.contact'].sudo().search([
                    ('external_id', '=', contact_id),
                    ('location_id', '=', installed_location.id)
                ], limit=1)
                
                if not contact_record:
                    return {
                        'success': False,
                        'message': f'No contact record found for external_id: {contact_id}',
                        'created': 0,
                        'updated': 0,
                        'errors': []
                    }
                
                created_count = 0
                updated_count = 0
                message_sync_results = []
                
                for conv_data in conversations:
                    try:
                        # Extract conversation data
                        conv_id = conv_data.get('id')
                        if not conv_id:
                            continue
                        
                        # Check if conversation already exists
                        existing_conv = self.sudo().search([
                            ('ghl_id', '=', conv_id),
                            ('contact_id', '=', contact_record.id)
                        ], limit=1)
                        
                        # Prepare conversation values
                        conv_vals = {
                            'ghl_id': conv_id,
                            'contact_id': contact_record.id,
                            'location_id': installed_location.id,
                            'subject': conv_data.get('title', ''),  # Map 'title' from API to 'subject' field
                            'status': conv_data.get('status', ''),
                            'date_created': ms_to_datetime(conv_data.get('dateCreated')),
                            'date_modified': ms_to_datetime(conv_data.get('dateUpdated')),
                            'last_message': conv_data.get('lastMessage', ''),
                            'unread_count': conv_data.get('unreadCount', 0),
                            'channel': conv_data.get('channel', ''),
                        }
                        
                        # Create or update conversation
                        if existing_conv:
                            existing_conv.write(conv_vals)
                            updated_count += 1
                            conversation_record = existing_conv
                            _logger.info(f"Updated conversation {conv_id} for contact {contact_id}")
                        else:
                            conversation_record = self.sudo().create(conv_vals)
                            created_count += 1
                            _logger.info(f"Created conversation {conv_id} for contact {contact_id}")
                        
                        # Fetch messages for this conversation
                        message_result = self.env['ghl.contact.message'].sudo().fetch_messages_for_conversation(
                            conversation_id=conv_id,
                            access_token=location_token,  # Use location token
                            location_id=installed_location.id,
                            contact_id=contact_record.id,
                            limit=100
                        )
                        
                        message_sync_results.append({
                            'conversation_id': conv_id,
                            'success': message_result.get('success', False),
                            'message_count': message_result.get('message_count', 0),
                            'error': message_result.get('error') if not message_result.get('success') else None
                        })
                        
                    except Exception as e:
                        _logger.error(f"Error processing conversation {conv_data.get('id', 'unknown')}: {e}")
                        continue
                
                _logger.info(f"Conversation sync completed for contact {contact_id}: {created_count} created, {updated_count} updated")
                return {
                    'success': True,
                    'message': f'Successfully synced {len(conversations)} conversations',
                    'created': created_count,
                    'updated': updated_count,
                    'total_conversations': len(conversations),
                    'message_sync_results': message_sync_results,
                    'errors': []
                }
            else:
                _logger.error(f"Failed to fetch conversations. Status: {response.status_code}, Response: {response.text}")
                return {
                    'success': False,
                    'message': f'API request failed with status {response.status_code}',
                    'created': 0,
                    'updated': 0,
                    'errors': [f'API error: {response.status_code} {response.text}']
                }
                
        except Exception as e:
            _logger.error(f"Error in sync_conversations_for_contact: {str(e)}")
            return {
                'success': False,
                'message': f'Unexpected error: {str(e)}',
                'created': 0,
                'updated': 0,
                'errors': [str(e)]
            } 

    def sync_conversations_for_contact_with_location_token(self, location_token, location_id, contact_id, limit=100):
        """
        Sync conversations for a specific contact using a location token directly.
        After syncing conversations, fetch all messages for each conversation.
        """
        import requests
        import logging
        import json
        _logger = logging.getLogger(__name__)
        
        def ms_to_datetime(ms):
            if not ms:
                return None
            try:
                if isinstance(ms, datetime):
                    return ms
                ms = int(ms)
                return datetime.utcfromtimestamp(ms / 1000.0)
            except Exception:
                return None

        try:
            # Fetch conversations using location token
            url = f"https://services.leadconnectorhq.com/conversations/search?locationId={location_id}&contactId={contact_id}&limit={limit}"
            headers = {
                'Accept': 'application/json',
                'Authorization': f'Bearer {location_token}',
                'Version': '2021-07-28',
            }
            
            _logger.info(f"Fetching conversations for contact {contact_id} at location {location_id}")
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                conversations = data.get('conversations', [])
                _logger.info(f"Found {len(conversations)} conversations for contact {contact_id}")
                
                # Find the installed location and contact records
                installed_location = self.env['installed.location'].sudo().search([
                    ('location_id', '=', location_id)
                ], limit=1)
                
                if not installed_location:
                    return {
                        'success': False,
                        'message': f'No installed location found for location_id: {location_id}',
                        'created': 0,
                        'updated': 0,
                        'errors': []
                    }
                
                contact_record = self.env['ghl.location.contact'].sudo().search([
                    ('external_id', '=', contact_id),
                    ('location_id', '=', installed_location.id)
                ], limit=1)
                
                if not contact_record:
                    return {
                        'success': False,
                        'message': f'No contact record found for external_id: {contact_id}',
                        'created': 0,
                        'updated': 0,
                        'errors': []
                    }
                
                created_count = 0
                updated_count = 0
                message_sync_results = []
                
                for conv_data in conversations:
                    try:
                        # Extract conversation data
                        conv_id = conv_data.get('id')
                        if not conv_id:
                            continue
                        
                        # Check if conversation already exists
                        existing_conv = self.sudo().search([
                            ('ghl_id', '=', conv_id),
                            ('contact_id', '=', contact_record.id)
                        ], limit=1)
                        
                        # Prepare conversation values
                        conv_vals = {
                            'ghl_id': conv_id,
                            'contact_id': contact_record.id,
                            'location_id': installed_location.id,
                            'subject': conv_data.get('title', ''),  # Map 'title' from API to 'subject' field
                            'status': conv_data.get('status', ''),
                            'date_created': ms_to_datetime(conv_data.get('dateCreated')),
                            'date_modified': ms_to_datetime(conv_data.get('dateUpdated')),
                            'last_message': conv_data.get('lastMessage', ''),
                            'unread_count': conv_data.get('unreadCount', 0),
                            'channel': conv_data.get('channel', ''),
                        }
                        
                        # Create or update conversation
                        if existing_conv:
                            existing_conv.write(conv_vals)
                            updated_count += 1
                            conversation_record = existing_conv
                            _logger.info(f"Updated conversation {conv_id} for contact {contact_id}")
                        else:
                            conversation_record = self.sudo().create(conv_vals)
                            created_count += 1
                            _logger.info(f"Created conversation {conv_id} for contact {contact_id}")
                        
                        # Fetch messages for this conversation
                        message_result = self.env['ghl.contact.message'].sudo().fetch_messages_for_conversation(
                            conversation_id=conv_id,
                            access_token=location_token,  # Use location token
                            location_id=installed_location.id,
                            contact_id=contact_record.id,
                            limit=100
                        )
                        
                        message_sync_results.append({
                            'conversation_id': conv_id,
                            'success': message_result.get('success', False),
                            'message_count': message_result.get('message_count', 0),
                            'error': message_result.get('error') if not message_result.get('success') else None
                        })
                        
                    except Exception as e:
                        _logger.error(f"Error processing conversation {conv_data.get('id', 'unknown')}: {e}")
                        continue
                
                _logger.info(f"Conversation sync completed for contact {contact_id}: {created_count} created, {updated_count} updated")
                return {
                    'success': True,
                    'message': f'Successfully synced {len(conversations)} conversations',
                    'created': created_count,
                    'updated': updated_count,
                    'total_conversations': len(conversations),
                    'message_sync_results': message_sync_results,
                    'errors': []
                }
            else:
                _logger.error(f"Failed to fetch conversations. Status: {response.status_code}, Response: {response.text}")
                return {
                    'success': False,
                    'message': f'API request failed with status {response.status_code}',
                    'created': 0,
                    'updated': 0,
                    'errors': [f'API error: {response.status_code} {response.text}']
                }
                
        except Exception as e:
            _logger.error(f"Error in sync_conversations_for_contact_with_location_token: {str(e)}")
            return {
                'success': False,
                'message': f'Unexpected error: {str(e)}',
                'created': 0,
                'updated': 0,
                'errors': [str(e)]
            } 

    def action_fetch_messages(self):
        """
        Button to fetch all messages for this conversation from the GHL API.
        Requires the conversation to have a valid ghl_id and a valid access token for the location.
        """
        self.ensure_one()
        
        # Find the access token for this location
        app = self.env['cyclsales.application'].sudo().search([
            ('app_id', '=', self.location_id.app_id),
            ('is_active', '=', True)
        ], limit=1)
        if not app or not app.access_token:
            raise ValidationError(_('No valid access token found for this location.'))
        
        # Get company_id from ghl.agency.token (same as other models)
        agency_token = self.env['ghl.agency.token'].sudo().search([], order='create_date desc', limit=1)
        if not agency_token:
            raise ValidationError(_('No agency token found. Please ensure ghl.agency.token is configured.'))
        
        company_id = agency_token.company_id
        if not company_id:
            raise ValidationError(_('No company_id found in agency token.'))
        
        try:
            # Step 1: Get location token using agency token
            location_token_result = self._get_location_token(app.access_token, self.location_id.location_id, company_id)
            _logger.info(f"Location token result type: {type(location_token_result)}, Result: {location_token_result}")
            
            if not isinstance(location_token_result, dict):
                raise ValidationError(_('Location token result is not a dictionary: %s') % str(location_token_result))
                
            if not location_token_result.get('success'):
                raise ValidationError(_('Failed to get location token: %s') % location_token_result.get('error', 'Unknown error'))
            
            location_token = location_token_result.get('access_token')
            _logger.info(f"Location token: {location_token[:20] if location_token else 'None'}...")
            
            # Step 2: Fetch messages using location token
            _logger.info(f"About to call fetch_messages_for_conversation with conversation_id={self.ghl_id}")
            try:
                result = self.env['ghl.contact.message'].sudo().fetch_messages_for_conversation(
                    conversation_id=self.ghl_id,
                    access_token=location_token,  # Use location token, not agency token
                    location_id=self.location_id.id,
                    contact_id=self.contact_id.id,
                    limit=100
                )
                _logger.info(f"fetch_messages_for_conversation completed successfully")
            except Exception as e:
                _logger.error(f"Exception in fetch_messages_for_conversation: {str(e)}")
                import traceback
                _logger.error(f"Full traceback: {traceback.format_exc()}")
                raise
            
            # Debug: Check what result contains
            _logger.info(f"Result type: {type(result)}, Result: {result}")
            _logger.info(f"About to check result.get('success')")
            
            if isinstance(result, dict) and result.get('success'):
                message_count = result.get('total_messages', 0)
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': 'Success',
                        'message': f'Successfully fetched {message_count} messages for this conversation.',
                        'type': 'success',
                    }
                }
            else:
                error_msg = result.get("error", "Unknown error") if isinstance(result, dict) else str(result)
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': 'Error',
                        'message': f'Failed to fetch messages: {error_msg}',
                        'type': 'danger',
                    }
                }
                
        except Exception as e:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Error',
                    'message': f'Exception occurred while fetching messages: {str(e)}',
                    'type': 'danger',
                }
            } 
    
    def action_update_touch_information(self):
        """
        Button to update touch information for all contacts with messages
        """
        try:
            result = self.env['ghl.location.contact'].sudo().update_all_contacts_touch_information()
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Success',
                    'message': f'Updated touch information for {result.get("contacts_updated", 0)} contacts.',
                    'type': 'success',
                }
            }
        except Exception as e:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Error',
                    'message': f'Error updating touch information: {str(e)}',
                    'type': 'danger',
                }
            }
            
    def _map_message_type(self, message_type):
        """
        Map numeric message type from GHL API to string values expected by the model
        """
        if not message_type:
            return ''
        
        # GHL API message type mapping
        type_mapping = {
            1: 'TYPE_CALL',
            2: 'TYPE_SMS', 
            3: 'TYPE_EMAIL',
            4: 'TYPE_SMS_REVIEW_REQUEST',
            5: 'TYPE_WEBCHAT',
            6: 'TYPE_SMS_NO_SHOW_REQUEST',
            7: 'TYPE_NO_SHOW',
            8: 'TYPE_CAMPAIGN_SMS',
            9: 'TYPE_CAMPAIGN_CALL',
            10: 'TYPE_CAMPAIGN_EMAIL',
            11: 'TYPE_CAMPAIGN_VOICEMAIL',
            12: 'TYPE_FACEBOOK',
            13: 'TYPE_CAMPAIGN_FACEBOOK',
            14: 'TYPE_CAMPAIGN_MANUAL_CALL',
            15: 'TYPE_CAMPAIGN_MANUAL_SMS',
            16: 'TYPE_GMB',
            17: 'TYPE_CAMPAIGN_GMB',
            18: 'TYPE_REVIEW',
            19: 'TYPE_INSTAGRAM',
            20: 'TYPE_WHATSAPP',
            21: 'TYPE_CUSTOM_SMS',
            22: 'TYPE_CUSTOM_EMAIL',
            23: 'TYPE_CUSTOM_PROVIDER_SMS',
            24: 'TYPE_CUSTOM_PROVIDER_EMAIL',
            25: 'TYPE_IVR_CALL',
            26: 'TYPE_ACTIVITY_CONTACT',
            27: 'TYPE_ACTIVITY_INVOICE',
            28: 'TYPE_ACTIVITY_PAYMENT',
            29: 'TYPE_ACTIVITY_OPPORTUNITY',
            30: 'TYPE_LIVE_CHAT',
            31: 'TYPE_LIVE_CHAT_INFO_MESSAGE',
            32: 'TYPE_ACTIVITY_APPOINTMENT',
            33: 'TYPE_FACEBOOK_COMMENT',
            34: 'TYPE_INSTAGRAM_COMMENT',
            35: 'TYPE_CUSTOM_CALL',
            36: 'TYPE_INTERNAL_COMMENT',
        }
        
        return type_mapping.get(message_type, '')

    def _map_conversation_type(self, conversation_type):
        """
        Map numeric conversation type from GHL API to string values expected by the model
        """
        if not conversation_type:
            return ''
        
        # GHL API conversation type mapping
        type_mapping = {
            1: 'TYPE_PHONE',
            2: 'TYPE_SMS',
            3: 'TYPE_EMAIL',
            4: 'TYPE_CHAT',
        }
        
        return type_mapping.get(conversation_type, '')

    def fetch_conversation_single(self, location_token, conversation_id):
        """
        Fetch a single conversation from GHL using the location token and conversation ID.
        :return: The created/updated conversation record, or None on failure
        """ 
        url = f"https://services.leadconnectorhq.com/conversations/{conversation_id}"
        headers = {
            'Accept': 'application/json',
            'Authorization': f'Bearer {location_token}',
            'Version': '2021-04-15',
        }
        try:
            resp = requests.get(url, headers=headers)
            _logger.info(f"[GHLContactConversation] fetch_conversation_single response: {resp.status_code} {resp.text}")
            if resp.status_code != 200:
                _logger.error(f"Failed to fetch conversation: {resp.text}")
                return None
            data = resp.json()
            if not data:
                _logger.error(f"No conversation data in response: {resp.text}")
                return None
            # Map fields
            vals = {
                'ghl_id': data.get('id'),  # Required field
                'contact_id': data.get('contactId'),
                'location_id': data.get('locationId'),   
                'unread_count': data.get('unreadCount'),
                'type': self._map_conversation_type(data.get('type')),
                'last_message_body': data.get('lastMessageBody', ''),
                'last_message_type': self._map_message_type(data.get('lastMessageType')),
                'full_name': data.get('fullName', ''),
                'contact_name': data.get('contactName', ''),
                'email': data.get('email', ''),
                'phone': data.get('phone', ''),
            }
            # Find installed.location by locationId
            installed_location = self.env['installed.location'].search([
                ('location_id', '=', vals['location_id'])
            ], limit=1)
            if not installed_location:
                _logger.error(f"No installed.location found for locationId: {vals['location_id']}")
                return None
            vals['location_id'] = installed_location.id
            # Find contact by contactId and location
            contact = self.env['ghl.location.contact'].search([
                ('external_id', '=', vals['contact_id']),
                ('location_id', '=', installed_location.id)
            ], limit=1)
            if not contact:
                _logger.warning(f"No ghl.location.contact found for contactId: {vals['contact_id']} at location {installed_location.id}")
            else:
                vals['contact_id'] = contact.id
            # Create or update conversation
            conversation = self.sudo().search([
                ('ghl_id', '=', vals['ghl_id']),
                ('location_id', '=', installed_location.id)
            ], limit=1)
            if conversation:
                conversation.write(vals)
            else:
                conversation = self.sudo().create(vals)
            return conversation
        except Exception as e:
            _logger.error(f"Error fetching single conversation: {e}")
            return None 