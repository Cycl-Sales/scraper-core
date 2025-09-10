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
                # Check if we've already determined this message has no recording
                if message.recording_checked and not message.recording_available:
                    _logger.info(f"Message {message_id} has been checked and confirmed to have no recording")
                    return Response(
                        'No recording available for this message',
                        status=404,
                        content_type='text/plain',
                        headers=get_cors_headers(request)
                    )
                
                _logger.info(f"Recording not available for message {message_id}, attempting to fetch it")
                
                # Try to fetch the recording automatically
                if message.message_type == 'TYPE_CALL':
                    # Get app_id from request parameters
                    app_id = request.httprequest.args.get('appId', '6867d1537079188afca5013c')
                    
                    # Attempt to fetch the recording
                    fetch_result = message.fetch_recording_url(app_id=app_id)
                    
                    if fetch_result.get('success'):
                        _logger.info(f"Successfully fetched recording for message {message_id}")
                        # Refresh the message record to get the updated data
                        message = request.env['ghl.contact.message'].sudo().browse(message_id)
                    elif fetch_result.get('no_recording'):
                        # Message has been marked as having no recording
                        _logger.info(f"Message {message_id} confirmed to have no recording available")
                        return Response(
                            'No recording available for this message',
                            status=404,
                            content_type='text/plain',
                            headers=get_cors_headers(request)
                        )
                    else:
                        _logger.warning(f"Failed to fetch recording for message {message_id}: {fetch_result.get('error', 'Unknown error')}")
                        return Response(
                            f'No recording available for this message. Fetch failed: {fetch_result.get("error", "Unknown error")}',
                            status=404,
                            content_type='text/plain',
                            headers=get_cors_headers(request)
                        )
                else:
                    _logger.warning(f"Message {message_id} is not a call message, cannot fetch recording")
                    return Response(
                        'No recording available for this message (not a call message)',
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