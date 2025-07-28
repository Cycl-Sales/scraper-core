from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import requests
import json
import logging
from datetime import datetime

_logger = logging.getLogger(__name__)


class GhlContactMessage(models.Model):
    _name = 'ghl.contact.message'
    _description = 'GHL Contact Message'
    _order = 'date_added desc'
    _rec_name = 'display_name'

    # GHL API fields
    ghl_id = fields.Char('GHL ID', required=True, index=True)
    external_id = fields.Char('External ID', related='ghl_id')  # Alias for ghl_id
    contact_id = fields.Many2one('ghl.location.contact', string='Contact', required=True, ondelete='cascade')
    location_id = fields.Many2one('installed.location', string='Location', required=True, ondelete='cascade')
    conversation_id = fields.Many2one('ghl.contact.conversation', string='Conversation', ondelete='cascade')

    # Message details
    type = fields.Integer('Type')
    message_type = fields.Selection([
        ('TYPE_CALL', 'Call'),
        ('TYPE_SMS', 'SMS'),
        ('TYPE_EMAIL', 'Email'),
        ('TYPE_SMS_REVIEW_REQUEST', 'SMS Review Request'),
        ('TYPE_WEBCHAT', 'Webchat'),
        ('TYPE_SMS_NO_SHOW_REQUEST', 'SMS No Show Request'),
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
    ], string='Message Type')
    body = fields.Text('Message Body')
    direction = fields.Selection([
        ('inbound', 'Inbound'),
        ('outbound', 'Outbound'),
    ], string='Direction')
    status = fields.Selection([
        ('completed', 'Completed'),
        ('no-answer', 'No Answer'),
        ('canceled', 'Canceled'),
        ('connected', 'Connected'),
        ('disconnected', 'Disconnected'),
        ('pending', 'Pending'),
        ('failed', 'Failed'),
        ('sent', 'Sent'),
        ('delivered', 'Delivered'),
        ('read', 'Read'),
    ], string='Status')
    content_type = fields.Char('Content Type')
    source = fields.Char('Source')
    user_id = fields.Many2one('ghl.location.user', string='User')  # Keep as Char for API data
    user_id_rel = fields.Many2one('ghl.location.user', string='User',
                                  domain="[('external_id', '=', user_id.id)]")
    conversation_provider_id = fields.Char('Conversation Provider ID')

    # Dates
    date_added = fields.Datetime('Date Added')

    # Related fields
    attachment_ids = fields.One2many('ghl.contact.message.attachment', 'message_id', string='Attachments')
    meta_id = fields.Many2one('ghl.contact.message.meta', string='Meta Data')
    transcript_ids = fields.One2many('ghl.contact.message.transcript', 'message_id', string='Transcripts')

    # Audio recording fields
    recording_data = fields.Binary('Recording Data', attachment=True)
    recording_filename = fields.Char('Recording Filename')
    recording_content_type = fields.Char('Recording Content Type')
    recording_size = fields.Integer('Recording Size (bytes)')
    recording_fetched = fields.Boolean('Recording Fetched', default=False)

    # Computed fields
    display_name = fields.Char('Display Name', compute='_compute_display_name', store=True)

    _sql_constraints = [
        ('unique_ghl_id', 'unique(ghl_id)', 'GHL ID must be unique!'),
    ]

    @api.model_create_multi
    def create(self, vals_list):
        """Override create to automatically fetch recordings for call messages"""
        records = super().create(vals_list)

        # Link user relationship for new records
        for record in records:
            if record.user_id and not record.user_id_rel:
                self._link_user_relationship(record)

        # For now, let's not auto-fetch on create to avoid cursor issues
        # Users can manually fetch recordings and transcripts using the buttons
        _logger.info(
            f"Created {len(records)} messages. Use 'Fetch Recording' and 'Fetch Transcript' buttons to get data.")

        return records

    def write(self, vals):
        """Override write to automatically fetch recordings for call messages"""
        result = super().write(vals)

        # Link user relationship for updated records
        for record in self:
            if record.user_id and not record.user_id_rel:
                self._link_user_relationship(record)

        # For now, let's not auto-fetch on write to avoid cursor issues
        # Users can manually fetch recordings using the button

        return result

    def _link_user_relationship(self, record):
        """Link the user_id_rel field to the corresponding ghl.location.user record"""
        if record.user_id:
            user_record = self.env['ghl.location.user'].sudo().search([
                ('external_id', '=', record.user_id.external_id)
            ], limit=1)

            if user_record:
                record.user_id_rel = user_record.id
                _logger.info(f"Linked message {record.id} to user {user_record.name} (external_id: {record.user_id})")
            else:
                _logger.warning(f"No user found with external_id: {record.user_id} for message {record.id}")

    @api.depends('body', 'contact_id', 'ghl_id')
    def _compute_display_name(self):
        for record in self:
            if record.body:
                # Truncate body to 50 characters for display
                body_preview = record.body[:50] + '...' if len(record.body) > 50 else record.body
                record.display_name = f"{body_preview} - {record.contact_id.name or 'Unknown'}"
            elif record.contact_id:
                record.display_name = f"Message - {record.contact_id.name}"
            else:
                record.display_name = f"Message {record.ghl_id}"

    @api.constrains('contact_id', 'location_id')
    def _check_contact_location_consistency(self):
        for record in self:
            if record.contact_id and record.location_id:
                if record.contact_id.location_id != record.location_id:
                    raise ValidationError(_('Contact location must match message location.'))

    def name_get(self):
        result = []
        for record in self:
            name = record.display_name or f"Message {record.ghl_id}"
            result.append((record.id, name))
        return result

    @api.model
    def fetch_messages_for_conversation(self, conversation_id, access_token, location_id=None, contact_id=None,
                                        limit=100, type_filter=None):
        """
        Fetch all messages for a conversation from the GHL API, handling pagination.
        Args:
            conversation_id (str): GHL conversation ID
            access_token (str): Location-specific Bearer token for API (should be location token, not agency token)
            location_id (int): Odoo installed.location ID (optional, for linking)
            contact_id (int): Odoo ghl.location.contact ID (optional, for linking)
            limit (int): Page size (max per request)
            type_filter (str): Comma-separated message types (optional)
        Returns:
            dict: Sync results
        """
        import requests
        import time
        import logging
        from datetime import datetime
        import re
        _logger = logging.getLogger(__name__)

        def parse_iso_date(date_str):
            """Parse ISO 8601 date string to Python datetime (naive)"""
            if not date_str:
                return None
            try:
                # Remove timezone info and parse
                date_str = re.sub(r'\.\d+Z$', 'Z', date_str)  # Remove milliseconds if present
                dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                # Convert to naive datetime (remove timezone info)
                return dt.replace(tzinfo=None)
            except Exception as e:
                _logger.warning(f"Could not parse date '{date_str}': {e}")
                return None

        base_url = f"https://services.leadconnectorhq.com/conversations/{conversation_id}/messages"
        headers = {
            'Accept': 'application/json',
            'Authorization': f'Bearer {access_token}',
            'Version': '2021-07-28',  # Updated to match other API calls
        }
        params = {
            'limit': limit if limit < 100 else 100,
        }
        if type_filter:
            params['type'] = type_filter

        all_messages = []
        last_message_id = None
        page = 0

        try:
            while True:
                if last_message_id:
                    params['lastMessageId'] = last_message_id

                _logger.info(f"Fetching messages for conversation {conversation_id} with params: {params}")
                response = requests.get(base_url, headers=headers, params=params, timeout=30)

                if response.status_code != 200:
                    _logger.error(
                        f"Failed to fetch messages for conversation {conversation_id}: {response.status_code} {response.text}")
                    return {
                        'success': False,
                        'error': f'API error: {response.status_code} {response.text}',
                        'created_count': 0,
                        'updated_count': 0,
                        'total_messages': 0,
                    }

                _logger.info(f"Response status: {response.status_code}")
                data = response.json()
                _logger.info(
                    f"Response data type: {type(data)}, keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")

                # Handle nested messages structure
                messages_container = data.get('messages', {})
                if isinstance(messages_container, dict):
                    messages = messages_container.get('messages', [])
                    next_page = messages_container.get('nextPage', False)
                    last_message_id_from_response = messages_container.get('lastMessageId')
                else:
                    # Fallback for direct messages array
                    messages = messages_container if isinstance(messages_container, list) else []
                    next_page = data.get('nextPage', False)
                    last_message_id_from_response = None

                _logger.info(f"Messages type: {type(messages)}, Found {len(messages)} messages")
                if messages:
                    _logger.info(f"First message type: {type(messages[0])}, First message ID: {messages[0].get('id')}")

                if not messages:
                    break

                all_messages.extend(messages)

                # If nextPage is not true, break
                if not next_page:
                    break

                # Prepare for next page (only if we have messages)
                if messages:
                    last_message_id = messages[-1]['id']
                    page += 1
                    time.sleep(0.1)  # Be gentle to the API
                else:
                    break

        except Exception as e:
            _logger.error(f"Exception while fetching messages for conversation {conversation_id}: {str(e)}")
            import traceback
            _logger.error(f"Full traceback: {traceback.format_exc()}")
            return {
                'success': False,
                'error': f'Exception: {str(e)}',
                'created_count': 0,
                'updated_count': 0,
                'total_messages': 0,
            }

        created_count = 0
        updated_count = 0

        for msg in all_messages:
            try:
                # Check if msg is a string (message ID) or a dictionary (full message data)
                if isinstance(msg, str):
                    _logger.warning(f"Message is a string (ID): {msg}, skipping detailed processing")
                    continue
                elif not isinstance(msg, dict):
                    _logger.warning(f"Message is not a dictionary: {type(msg)}, value: {msg}, skipping")
                    continue

                ghl_id = msg.get('id')

                # Find the conversation record
                conversation_record = self.env['ghl.contact.conversation'].search([('ghl_id', '=', conversation_id)],
                                                                                  limit=1)

                user_record = self.env['ghl.location.user'].search([('external_id', '=', msg.get('userId'))], limit=1)

                # If user not found, try to fetch it from GHL API
                if not user_record and msg.get('userId'):
                    # Get required parameters for fetch_user_by_id
                    app = self.env['cyclsales.application'].sudo().search([('is_active', '=', True)], limit=1)
                    company_id = 'Ipg8nKDPLYKsbtodR6LN'  # Hardcoded company ID

                    if app and app.access_token and location_id:
                        location_record = self.env['cyclsales.application'].sudo().search([], limit=1)
                        if location_record.exists():
                            # Call the fetch_user_by_id method
                            self.env['ghl.location.user'].fetch_user_by_id(
                                user_id=msg.get('userId'),
                                location_id=msg.get('locationId'),
                                company_id=company_id,
                                app_access_token=app.access_token
                            )
                            # Try to find the user again after fetching
                            user_record = self.env['ghl.location.user'].search(
                                [('external_id', '=', msg.get('userId'))], limit=1)

                print(user_record)
                print(msg)
                vals = {
                    'ghl_id': ghl_id,
                    'conversation_id': conversation_record.id if conversation_record else False,
                    'contact_id': contact_id or False,
                    'location_id': location_id or False,
                    'type': msg.get('type'),
                    'message_type': msg.get('messageType'),
                    'body': msg.get('body'),
                    'direction': msg.get('direction'),
                    'status': msg.get('status'),
                    'content_type': msg.get('contentType'),
                    'source': msg.get('source'),
                    'user_id': user_record.id,
                    'conversation_provider_id': msg.get('conversationProviderId'),
                    'date_added': parse_iso_date(msg.get('dateAdded')),
                }

                # Attachments
                attachments = msg.get('attachments', [])
                # Meta
                meta = msg.get('meta')

                existing = self.sudo().search([('ghl_id', '=', ghl_id)], limit=1)
                if existing:
                    existing.write(vals)
                    updated_count += 1
                    message_rec = existing
                else:
                    try:
                        message_rec = self.sudo().create(vals)
                        created_count += 1
                    except Exception as create_error:
                        # Check if duplicate error
                        if 'duplicate key value violates unique constraint' in str(
                                create_error) or 'already exists' in str(create_error):
                            _logger.warning(
                                f"Duplicate detected for message {ghl_id} during create. Attempting to update instead.")
                            # Try to find and update the existing message
                            try:
                                existing_msg = self.sudo().search([('ghl_id', '=', ghl_id)], limit=1)
                                if existing_msg:
                                    existing_msg.write(vals)
                                    updated_count += 1
                                    message_rec = existing_msg
                                    _logger.info(f"Updated existing message {ghl_id} after duplicate detection")
                                else:
                                    _logger.error(f"Duplicate detected but message {ghl_id} not found for update")
                                    continue
                            except Exception as update_error:
                                _logger.error(
                                    f"Error updating message {ghl_id} after duplicate detection: {update_error}")
                                continue
                        else:
                            _logger.error(f"Error creating message {ghl_id}: {create_error}")
                            continue

                # Handle attachments
                if attachments:
                    # Remove old attachments
                    message_rec.attachment_ids.unlink()
                    for att_url in attachments:
                        self.env['ghl.contact.message.attachment'].sudo().create({
                            'message_id': message_rec.id,
                            'attachment_url': att_url,
                        })

                # Handle meta
                if meta:
                    if message_rec.meta_id:
                        message_rec.meta_id.unlink()
                    self.env['ghl.contact.message.meta'].sudo().create_from_api_data(message_rec.id, meta)

                # Update contact's touch information
                if message_rec.contact_id:
                    try:
                        message_rec.contact_id.update_touch_information()
                    except Exception as e:
                        _logger.warning(
                            f"Error updating touch information for contact {message_rec.contact_id.id}: {str(e)}")

            except Exception as e:
                msg_id = msg.get('id', 'unknown') if isinstance(msg, dict) else str(msg)
                _logger.error(f"Error processing message {msg_id}: {str(e)}")
                continue

        _logger.info(
            f"Returning result: created_count={created_count}, updated_count={updated_count}, total_messages={len(all_messages)}")
        result = {
            'success': True,
            'created_count': created_count,
            'updated_count': updated_count,
            'total_messages': len(all_messages),
        }
        _logger.info(f"Result type: {type(result)}, Result: {result}")
        return result

    def fetch_recording_url(self, location_id=None, message_id=None):
        """
        Fetch recording URL for a message from GHL API.
        Args:
            location_id (str): GHL location ID (defaults to self.location_id.location_id)
            message_id (str): GHL message ID (defaults to self.ghl_id)
        Returns:
            dict: API response with recording URL
        """
        import requests
        import logging
        _logger = logging.getLogger(__name__)

        # Use defaults if not provided
        if not location_id:
            location_id = self.location_id.location_id if self.location_id else None
        if not message_id:
            message_id = self.ghl_id

        if not location_id or not message_id:
            _logger.error(f"Missing required parameters: location_id={location_id}, message_id={message_id}")
            return {
                'success': False,
                'error': 'Missing location_id or message_id'
            }

        # Step 1: Get agency access token
        app = self.env['cyclsales.application'].sudo().search([
            ('is_active', '=', True)
        ], limit=1)

        if not app or not app.access_token:
            _logger.error("No agency access token found")
            return {
                'success': False,
                'error': 'No agency access token found'
            }

        # Step 2: Get location access token using existing method
        company_id = 'Ipg8nKDPLYKsbtodR6LN'  # Hardcoded company ID
        location_token_result = self.env['ghl.contact.conversation'].sudo()._get_location_token(
            app_access_token=app.access_token,
            location_id=location_id,
            company_id=company_id
        )

        if not location_token_result.get('success'):
            _logger.error(f"Failed to get location token: {location_token_result.get('message', 'Unknown error')}")
            return {
                'success': False,
                'error': f"Failed to get location token: {location_token_result.get('message', 'Unknown error')}"
            }

        location_token = location_token_result.get('access_token')

        # Step 3: Fetch recording URL using location token
        url = f"https://services.leadconnectorhq.com/conversations/messages/{message_id}/locations/{location_id}/recording"

        headers = {
            'Accept': 'application/json',
            'Authorization': f'Bearer {location_token}',
            'Version': '2021-07-28',
        }

        try:
            _logger.info(f"Fetching recording URL for message {message_id} at location {location_id}")
            response = requests.get(url, headers=headers, timeout=30)

            _logger.info(f"Recording API response status: {response.status_code}")
            _logger.info(f"Recording API response headers: {dict(response.headers)}")

            if response.status_code == 200:
                # The API returns the audio file directly, not JSON
                content_type = response.headers.get('Content-Type', '')
                content_disposition = response.headers.get('Content-Disposition', '')

                _logger.info(
                    f"Recording API returned audio file: Content-Type={content_type}, Content-Disposition={content_disposition}")

                # Extract filename from content-disposition header
                filename = "recording.wav"  # default
                if content_disposition:
                    import re
                    filename_match = re.search(r'filename="([^"]+)"', content_disposition)
                    if filename_match:
                        filename = filename_match.group(1)

                # Save the audio file to a temporary location
                import tempfile
                import os

                # Create a unique filename based on message ID
                safe_filename = f"ghl_recording_{message_id}_{filename}"
                temp_dir = tempfile.gettempdir()
                file_path = os.path.join(temp_dir, safe_filename)

                with open(file_path, 'wb') as f:
                    f.write(response.content)

                _logger.info(f"Audio file saved to: {file_path}")

                # Save to database - encode binary data as base64 for Odoo Binary field
                import base64
                recording_data_b64 = base64.b64encode(response.content).decode('utf-8')

                _logger.info(f"Original response content length: {len(response.content)} bytes")
                _logger.info(f"Base64 encoded data length: {len(recording_data_b64)} characters")
                _logger.info(f"Content-Type from API: {content_type}")
                _logger.info(f"Filename from API: {filename}")

                self.write({
                    'recording_data': recording_data_b64,
                    'recording_filename': filename,
                    'recording_content_type': content_type,
                    'recording_size': len(response.content),
                    'recording_fetched': True
                })

                _logger.info(f"Recording data saved to database for message {self.id}")

                # Verify the data was saved correctly
                saved_record = self.env['ghl.contact.message'].browse(self.id)
                _logger.info(
                    f"Saved recording_data length: {len(saved_record.recording_data) if saved_record.recording_data else 0}")
                _logger.info(f"Saved recording_size: {saved_record.recording_size}")
                _logger.info(f"Saved recording_fetched: {saved_record.recording_fetched}")

                return {
                    'success': True,
                    'content_type': content_type,
                    'filename': filename,
                    'file_path': file_path,
                    'file_size': len(response.content),
                    'message': f'Recording saved to database and file: {file_path}'
                }
            else:
                _logger.error(f"Failed to fetch recording: {response.status_code} {response.text}")
                return {
                    'success': False,
                    'error': f'API error: {response.status_code} {response.text}',
                    'status_code': response.status_code
                }

        except Exception as e:
            _logger.error(f"Exception while fetching recording for message {message_id}: {str(e)}")
            import traceback
            _logger.error(f"Full traceback: {traceback.format_exc()}")
            return {
                'success': False,
                'error': f'Exception: {str(e)}'
            }

    def download_recording(self):
        """
        Download the recording file from the database
        """
        self.ensure_one()

        if not self.recording_data or not self.recording_fetched:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'No Recording',
                    'message': 'No recording available for this message',
                    'type': 'warning',
                }
            }

        return {
            'type': 'ir.actions.act_url',
            'url': f'/api/ghl-message/{self.id}/recording',
            'target': 'self',
        }

    def play_recording(self):
        """
        Play the recording in the browser
        """
        self.ensure_one()

        if not self.recording_data or not self.recording_fetched:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'No Recording',
                    'message': 'No recording available for this message',
                    'type': 'warning',
                }
            }

        return {
            'type': 'ir.actions.act_url',
            'url': f'/api/ghl-message/{self.id}/recording?play=true',
            'target': 'new',
        }

    def refetch_recording(self):
        """
        Re-fetch the recording (useful if the data is corrupted or empty)
        """
        self.ensure_one()

        if self.message_type != 'TYPE_CALL':
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Not a Call',
                    'message': 'This message is not a call message',
                    'type': 'warning',
                }
            }

        # Clear existing data
        self.write({
            'recording_data': False,
            'recording_filename': False,
            'recording_content_type': False,
            'recording_size': 0,
            'recording_fetched': False
        })

        # Fetch new recording
        result = self.fetch_recording_url()

        if result.get('success'):
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Success',
                    'message': 'Recording re-fetched successfully',
                    'type': 'success',
                }
            }
        else:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Error',
                    'message': f'Failed to re-fetch recording: {result.get("error", "Unknown error")}',
                    'type': 'danger',
                }
            }

    def fetch_transcript(self):
        """
        Fetch transcript for this call message
        """
        self.ensure_one()

        if self.message_type != 'TYPE_CALL':
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Not a Call',
                    'message': 'This message is not a call message',
                    'type': 'warning',
                }
            }

        # Use the transcript model to fetch
        transcript_model = self.env['ghl.contact.message.transcript']
        result = transcript_model.fetch_transcript_for_message(self.id)

        if result.get('success'):
            # Update call duration from transcript data
            self.update_call_duration_from_transcript()

            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Success',
                    'message': result.get('message', 'Transcript fetched successfully'),
                    'type': 'success',
                }
            }
        else:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Error',
                    'message': f'Failed to fetch transcript: {result.get("error", "Unknown error")}',
                    'type': 'danger',
                }
            }

    def get_transcript_summary(self):
        """
        Get transcript summary for this message
        """
        self.ensure_one()

        if not self.transcript_ids:
            return {
                'has_transcript': False,
                'total_sentences': 0,
                'total_duration': 0,
                'call_duration_seconds': 0,
                'call_duration_formatted': '0:00',
                'average_confidence': 0,
                'full_text': ''
            }

        summary = self.transcript_ids[0].get_transcript_summary()
        summary['has_transcript'] = True
        return summary

    def update_call_duration_from_transcript(self):
        """
        Update the call duration in meta record based on transcript data
        """
        self.ensure_one()

        if self.message_type != 'TYPE_CALL':
            return False

        if not self.transcript_ids:
            return False

        # Get duration from transcript summary
        transcript_summary = self.get_transcript_summary()
        call_duration = transcript_summary.get('call_duration_seconds', 0)

        if call_duration > 0:
            # Update or create meta record
            if self.meta_id:
                self.meta_id.write({
                    'call_duration': call_duration
                })
            else:
                # Create new meta record
                meta_record = self.env['ghl.contact.message.meta'].create({
                    'message_id': self.id,
                    'call_duration': call_duration,
                    'call_status': 'completed'  # Default status
                })
                self.write({'meta_id': meta_record.id})

            _logger.info(f"Updated call duration for message {self.id}: {call_duration} seconds")
            return True

        return False

    def fetch_message_single(self, location_token, message_id):
        """
        Fetch a single message from GHL using the location token and message ID.
        :return: The created/updated message record, or None on failure
        """
        url = f"https://services.leadconnectorhq.com/conversations/messages/{message_id}"
        headers = {
            'Accept': 'application/json',
            'Authorization': f'Bearer {location_token}',
            'Version': '2021-04-15',
        }
        try:
            resp = requests.get(url, headers=headers)
            _logger.info(f"[GhlContactMessage] fetch_message_single response: {resp.status_code} {resp.text}")
            if resp.status_code != 200:
                _logger.error(f"Failed to fetch message: {resp.text}")
                return None
            data = resp.json()
            if not data:
                _logger.error(f"No message data in response: {resp.text}")
                return None
            # Map fields
            vals = {
                'ghl_id': data.get('id'),
                'type': data.get('type'),
                'message_type': data.get('messageType'),
                'body': data.get('body'),
                'direction': data.get('direction'),
                'status': data.get('status'),
                'content_type': data.get('contentType'),
                'source': data.get('source'),
                'conversation_provider_id': data.get('conversationProviderId'),
            }
            # Parse dateAdded
            date_added = data.get('dateAdded')
            if date_added:
                try:
                    vals['date_added'] = datetime.strptime(date_added.replace('Z', ''), '%Y-%m-%dT%H:%M:%S.%f')
                except Exception:
                    try:
                        vals['date_added'] = datetime.strptime(date_added.replace('Z', ''), '%Y-%m-%dT%H:%M:%S')
                    except Exception:
                        _logger.warning(f"Could not parse date: {date_added}")
                        vals['date_added'] = False
            # Find installed.location by locationId
            location_id_val = data.get('locationId')
            installed_location = self.env['installed.location'].search([
                ('location_id', '=', location_id_val)
            ], limit=1)
            if not installed_location:
                _logger.error(f"No installed.location found for locationId: {location_id_val}")
                return None
            vals['location_id'] = installed_location.id
            # Find contact by contactId and location
            contact_id_val = data.get('contactId')
            contact = self.env['ghl.location.contact'].search([
                ('external_id', '=', contact_id_val),
                ('location_id', '=', installed_location.id)
            ], limit=1)
            if not contact:
                _logger.warning(
                    f"No ghl.location.contact found for contactId: {contact_id_val} at location {installed_location.id}")
            else:
                vals['contact_id'] = contact.id
            # Find conversation by conversationId and location
            conversation_id_val = data.get('conversationId')
            conversation = self.env['ghl.contact.conversation'].search([
                ('external_id', '=', conversation_id_val),
                ('location_id', '=', installed_location.id)
            ], limit=1)
            if conversation:
                vals['conversation_id'] = conversation.id
            # Find user by userId
            user_id_val = data.get('userId')
            user = self.env['ghl.location.user'].search([
                ('external_id', '=', user_id_val)
            ], limit=1)
            if user:
                vals['user_id'] = user.id
            # Create or update message
            message = self.sudo().search([
                ('ghl_id', '=', vals['ghl_id'])
            ], limit=1)
            if message:
                message.write(vals)
            else:
                message = self.sudo().create(vals)
            # Handle attachments
            attachments = data.get('attachments', [])
            if attachments:
                message.attachment_ids.unlink()
                for att_url in attachments:
                    self.env['ghl.contact.message.attachment'].sudo().create({
                        'message_id': message.id,
                        'attachment_url': att_url,
                    })
            # Handle meta
            meta = data.get('meta')
            if meta:
                if message.meta_id:
                    message.meta_id.unlink()
                self.env['ghl.contact.message.meta'].sudo().create_from_api_data(message.id, meta)
            return message
        except Exception as e:
            _logger.error(f"Error fetching single message: {e}")
            return None


class GhlContactMessageAttachment(models.Model):
    _name = 'ghl.contact.message.attachment'
    _description = 'GHL Contact Message Attachment'

    message_id = fields.Many2one('ghl.contact.message', string='Message', required=True, ondelete='cascade')
    attachment_url = fields.Char('Attachment URL')
    attachment_name = fields.Char('Attachment Name')
    attachment_type = fields.Char('Attachment Type')
    attachment_size = fields.Integer('Attachment Size')

    # Computed fields
    display_name = fields.Char('Display Name', compute='_compute_display_name', store=True)

    @api.depends('attachment_name', 'attachment_url')
    def _compute_display_name(self):
        for record in self:
            if record.attachment_name:
                record.display_name = record.attachment_name
            elif record.attachment_url:
                record.display_name = record.attachment_url.split('/')[-1]
            else:
                record.display_name = 'Unknown Attachment'


class GhlContactMessageMeta(models.Model):
    _name = 'ghl.contact.message.meta'
    _description = 'GHL Contact Message Meta Data'

    message_id = fields.Many2one('ghl.contact.message', string='Message', required=True, ondelete='cascade')

    # Call related fields
    call_duration = fields.Integer('Call Duration (seconds)')
    call_status = fields.Selection([
        ('completed', 'Completed'),
        ('missed', 'Missed'),
        ('no_answer', 'No Answer'),
        ('busy', 'Busy'),
        ('failed', 'Failed'),
    ], string='Call Status')

    # Email related fields
    email_message_ids = fields.Text('Email Message IDs')  # JSON string of message IDs

    # Computed fields
    display_name = fields.Char('Display Name', compute='_compute_display_name', store=True)

    @api.depends('call_duration', 'call_status', 'email_message_ids')
    def _compute_display_name(self):
        for record in self:
            if record.call_duration:
                record.display_name = f"Call: {record.call_duration}s - {record.call_status or 'Unknown'}"
            elif record.email_message_ids:
                record.display_name = f"Email: {len(record.email_message_ids.split(','))} messages"
            else:
                record.display_name = 'Meta Data'

    @api.model
    def create_from_api_data(self, message_id, meta_data):
        """Create meta record from API data"""
        if not meta_data:
            return False

        vals = {
            'message_id': message_id,
            'call_duration': meta_data.get('callDuration'),
            'call_status': meta_data.get('callStatus'),
        }

        # Handle email data
        email_data = meta_data.get('email', {})
        if email_data and 'messageIds' in email_data:
            message_ids = email_data['messageIds']
            if isinstance(message_ids, list):
                vals['email_message_ids'] = json.dumps(message_ids)
            else:
                vals['email_message_ids'] = str(message_ids)

        return self.create(vals)
