from odoo import http
from odoo.http import request, Response
import logging
import base64
from .cors_utils import get_cors_headers

_logger = logging.getLogger(__name__)

class GhlContactMessageController(http.Controller):
    
    @http.route('/api/ghl-message/<int:message_id>/recording', type='http', auth='none', methods=['GET', 'OPTIONS'], csrf=False)
    def download_recording(self, message_id, **kwargs):
        """
        Download recording for a GHL message
        """
        if request.httprequest.method == 'OPTIONS':
            return Response(status=200, headers=get_cors_headers(request))
            
        try:
            
            # Get the message record
            message = request.env['ghl.contact.message'].sudo().browse(message_id)
            
            if not message.exists():
                return Response(
                    'Message not found',
                    status=404,
                    content_type='text/plain',
                    headers=get_cors_headers(request)
                )
            
            
            if not message.recording_data or not message.recording_fetched:
                _logger.warning(f"No recording available for message {message_id}: recording_fetched={message.recording_fetched}, has_data={bool(message.recording_data)}")
                return Response(
                    'No recording available for this message',
                    status=404,
                    content_type='text/plain',
                    headers=get_cors_headers(request)
                )
            
            
            if not message.recording_data:
                return Response(
                    'No recording data found',
                    status=404,
                    content_type='text/plain',
                    headers=get_cors_headers(request)
                )
            
            try:
                recording_data = base64.b64decode(message.recording_data)
            except Exception as decode_error:
                _logger.error(f"Error decoding recording data: {str(decode_error)}")
                return Response(
                    f'Error decoding recording data: {str(decode_error)}',
                    status=500,
                    content_type='text/plain',
                    headers=get_cors_headers(request)
                )
            
            # Check if this is for playing or downloading
            play_mode = kwargs.get('play', False)
            
            # Set proper headers for audio file
            if play_mode:
                # For playing in browser
                headers = {
                    'Content-Type': message.recording_content_type or 'audio/mpeg',
                    'Content-Length': str(len(recording_data)),
                    'Cache-Control': 'no-cache',
                    'Accept-Ranges': 'bytes',
                }
            else:
                # For downloading
                headers = {
                    'Content-Type': message.recording_content_type or 'audio/mpeg',
                    'Content-Disposition': f'attachment; filename="{message.recording_filename or "recording.mp3"}"',
                    'Content-Length': str(len(recording_data)),
                    'Cache-Control': 'no-cache',
                }
            
            # Add CORS headers
            headers.update(get_cors_headers(request))
            
            
            return Response(
                recording_data,
                headers=headers
            )
            
        except Exception as e:
            _logger.error(f"Error serving recording for message {message_id}: {str(e)}")
            return Response(
                f'Error serving recording: {str(e)}',
                status=500,
                content_type='text/plain',
                headers=get_cors_headers(request)
            ) 