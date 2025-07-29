from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import json
import logging
import requests
from datetime import datetime

_logger = logging.getLogger(__name__)


class GhlContactMessageTranscript(models.Model):
    _name = 'ghl.contact.message.transcript'
    _description = 'GHL Contact Message Transcript'
    _order = 'sentence_index asc'
    _rec_name = 'transcript'

    # Related fields
    message_id = fields.Many2one('ghl.contact.message', string='Message', required=True, ondelete='cascade')
    contact_id = fields.Many2one('ghl.location.contact', string='Contact', related='message_id.contact_id', store=True)
    location_id = fields.Many2one('installed.location', string='Location', related='message_id.location_id', store=True)

    # Transcript fields from API
    media_channel = fields.Char('Media Channel')
    sentence_index = fields.Integer('Sentence Index', required=True)
    start_time = fields.Integer('Start Time (milliseconds)')
    end_time = fields.Integer('End Time (milliseconds)')
    transcript = fields.Text('Transcript Text', required=True)
    confidence = fields.Float('Confidence Score', digits=(3, 2))

    # Computed fields for display
    start_time_seconds = fields.Float('Start Time (seconds)', compute='_compute_time_seconds', store=True)
    end_time_seconds = fields.Float('End Time (seconds)', compute='_compute_time_seconds', store=True)
    duration = fields.Float('Duration (seconds)', compute='_compute_duration', store=True)

    # Computed fields
    display_name = fields.Char('Display Name', compute='_compute_display_name', store=True)

    _sql_constraints = [
        ('unique_sentence_per_message', 'unique(message_id, sentence_index)',
         'Sentence index must be unique per message!'),
    ]

    @api.depends('start_time', 'end_time')
    def _compute_time_seconds(self):
        """Compute time values in seconds for display"""
        for record in self:
            record.start_time_seconds = record.start_time / 1000.0 if record.start_time else 0.0
            record.end_time_seconds = record.end_time / 1000.0 if record.end_time else 0.0

    @api.depends('start_time', 'end_time')
    def _compute_duration(self):
        """Compute duration in seconds"""
        for record in self:
            if record.start_time and record.end_time:
                record.duration = (record.end_time - record.start_time) / 1000.0
            else:
                record.duration = 0.0

    @api.depends('transcript', 'sentence_index')
    def _compute_display_name(self):
        """Compute display name for the record"""
        for record in self:
            if record.transcript:
                # Truncate transcript to 50 characters for display
                transcript_preview = record.transcript[:50] + '...' if len(
                    record.transcript) > 50 else record.transcript
                record.display_name = f"Sentence {record.sentence_index}: {transcript_preview}"
            else:
                record.display_name = f"Sentence {record.sentence_index}"

    @api.constrains('sentence_index')
    def _check_sentence_index(self):
        """Ensure sentence index is positive"""
        for record in self:
            if record.sentence_index < 0:
                raise ValidationError(_('Sentence index must be a positive number.'))

    @api.constrains('start_time', 'end_time')
    def _check_time_consistency(self):
        """Ensure end time is after start time"""
        for record in self:
            if record.start_time and record.end_time and record.start_time >= record.end_time:
                raise ValidationError(_('End time must be after start time.'))

    @api.constrains('confidence')
    def _check_confidence_range(self):
        """Ensure confidence is between 0 and 1"""
        for record in self:
            if record.confidence and (record.confidence < 0 or record.confidence > 1):
                raise ValidationError(_('Confidence score must be between 0 and 1.'))

    def name_get(self):
        """Custom name_get method"""
        result = []
        for record in self:
            name = record.display_name or f"Transcript {record.id}"
            result.append((record.id, name))
        return result

    @api.model
    def create_from_api_data(self, message_id, transcript_data):
        """
        Create transcript records from API data
        Args:
            message_id (int): ID of the ghl.contact.message record
            transcript_data (list): List of transcript objects from API
        Returns:
            list: Created transcript records
        """
        if not transcript_data or not isinstance(transcript_data, list):
            return []

        created_records = []
        for item in transcript_data:
            # Handle time values - convert decimal strings to integers (milliseconds)
            start_time_str = item.get('startTime', '0')
            end_time_str = item.get('endTime', '0')

            try:
                # Convert decimal seconds to integer milliseconds
                start_time = int(float(start_time_str) * 1000) if start_time_str else 0
                end_time = int(float(end_time_str) * 1000) if end_time_str else 0
            except (ValueError, TypeError):
                start_time = 0
                end_time = 0
                _logger.warning(f"Invalid time values: startTime={start_time_str}, endTime={end_time_str}")

            vals = {
                'message_id': message_id,
                'media_channel': str(item.get('mediaChannel', '')),
                'sentence_index': int(item.get('sentenceIndex', 0)),
                'start_time': start_time,
                'end_time': end_time,
                'transcript': item.get('transcript', ''),
                'confidence': float(item.get('confidence', 0.0)),
            }

            try:
                record = self.create(vals)
                created_records.append(record)
            except Exception as e:
                _logger.error(f"Error creating transcript record: {str(e)}")
                continue

        _logger.info(f"Created {len(created_records)} transcript records for message {message_id}")
        return created_records

    def get_full_transcript_text(self):
        """
        Get the complete transcript text for the message
        Returns:
            str: Complete transcript text
        """
        transcripts = self.search([
            ('message_id', '=', self.message_id.id)
        ], order='sentence_index asc')

        return ' '.join([t.transcript for t in transcripts if t.transcript])

    def get_transcript_summary(self):
        """
        Get a summary of the transcript
        Returns:
            dict: Summary information
        """
        transcripts = self.search([
            ('message_id', '=', self.message_id.id)
        ], order='sentence_index asc')

        if not transcripts:
            return {
                'total_sentences': 0,
                'total_duration': 0,
                'call_duration_seconds': 0,
                'call_duration_formatted': '0:00',
                'average_confidence': 0,
                'full_text': ''
            }

        total_duration = sum(t.duration for t in transcripts if t.duration)
        avg_confidence = sum(t.confidence for t in transcripts if t.confidence) / len(transcripts)
        full_text = ' '.join([t.transcript for t in transcripts if t.transcript])

        # Format duration as MM:SS
        minutes = int(total_duration // 60)
        seconds = int(total_duration % 60)
        duration_formatted = f"{minutes}:{seconds:02d}"

        return {
            'total_sentences': len(transcripts),
            'total_duration': total_duration,
            'call_duration_seconds': int(total_duration),
            'call_duration_formatted': duration_formatted,
            'average_confidence': round(avg_confidence, 2),
            'full_text': full_text
        }

    @api.model
    def fetch_transcript_for_message(self, message_id, app_id='684c5cc0736d09f78555981f'):
        """
        Fetch transcript from GHL API for a specific message
        Args:
            message_id (int): ID of the ghl.contact.message record
        Returns:
            dict: API response result
        """
        message = self.env['ghl.contact.message'].browse(message_id)

        if not message.exists() or message.message_type != 'TYPE_CALL':
            return {
                'success': False,
                'error': 'Message is not a call message'
            }

        try:
            # Step 1: Get agency access token
            app = self.env['cyclsales.application'].sudo().search([
                ('app_id', '=', app_id)
            ], limit=1)
            if not app or not app.access_token:
                _logger.error("No agency access token found")
                return {
                    'success': False,
                    'error': 'No agency access token found'
                }

            # Step 2: Get location access token using installed.location.fetch_location_token method
            location = message.location_id
            company_id = app.company_id

            _logger.info(f"[Transcript Fetch] Message ID: {message.id}")
            _logger.info(f"[Transcript Fetch] Message GHL ID: {message.ghl_id}")
            _logger.info(f"[Transcript Fetch] Location record: {location}")
            _logger.info(f"[Transcript Fetch] Location ID field: {location.location_id if location else 'None'}")
            _logger.info(f"[Transcript Fetch] Company ID: {company_id}")
            _logger.info(
                f"[Transcript Fetch] App access token: {app.access_token[:20] if app.access_token else 'None'}...")

            # Use the installed.location.fetch_location_token method
            location_token = location.fetch_location_token(
                agency_token=app.access_token,
                company_id=company_id
            )

            _logger.info(f"[Transcript Fetch] Location token: {location_token[:20] if location_token else 'None'}...")

            if not location_token:
                _logger.error(f"Failed to get location token from installed.location.fetch_location_token")
                return {
                    'success': False,
                    'error': "Failed to get location token from installed.location.fetch_location_token"
                }

            # Build API URL
            base_url = "https://services.leadconnectorhq.com"
            url = f"{base_url}/conversations/locations/{location.location_id}/messages/{message.ghl_id}/transcription"
            _logger.info(f"[Transcript Fetch] API URL: {url}")

            headers = {
                'Accept': 'application/json',
                'Authorization': f'Bearer {location_token}',
                'Version': '2021-04-15'
            }

            _logger.info(f"[Transcript Fetch] Fetching transcript for message {message.ghl_id}")

            response = requests.get(url, headers=headers, timeout=30)
            _logger.info(f"[Transcript Fetch] Response status: {response.status_code}")
            _logger.info(f"[Transcript Fetch] Response text: {response.text[:200]}...")

            if response.status_code == 200:
                transcript_data = response.json()

                # Clear existing transcripts for this message
                existing_transcripts = self.search([('message_id', '=', message_id)])
                existing_transcripts.unlink()

                # Create new transcript records
                created_records = self.create_from_api_data(message_id, transcript_data)

                # Get transcript summary for duration info
                transcript_summary = self.get_transcript_summary()

                return {
                    'success': True,
                    'message': f'Successfully fetched {len(created_records)} transcript segments',
                    'count': len(created_records),
                    'call_duration_seconds': transcript_summary.get('call_duration_seconds', 0),
                    'call_duration_formatted': transcript_summary.get('call_duration_formatted', '0:00'),
                    'total_sentences': transcript_summary.get('total_sentences', 0),
                    'average_confidence': transcript_summary.get('average_confidence', 0)
                }
            else:
                _logger.error(f"API error: {response.status_code} {response.text}")
                return {
                    'success': False,
                    'error': f'API error: {response.status_code} {response.text}',
                    'status_code': response.status_code
                }

        except Exception as e:
            _logger.error(f"Exception while fetching transcript: {str(e)}")
            import traceback
            _logger.error(f"Full traceback: {traceback.format_exc()}")
            return {
                'success': False,
                'error': f'Exception: {str(e)}'
            }
