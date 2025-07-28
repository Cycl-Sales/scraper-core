from odoo import http
from odoo.http import request, Response
import json
import requests
import base64
from .cors_utils import get_cors_headers
import logging
import PyPDF2
import io

_logger = logging.getLogger(__name__)

class VisionAIController(http.Controller):
    @http.route('/cs-vision-ai/vision', type='http', auth='none', methods=['POST', 'OPTIONS'], cors='*', csrf=False)
    def analyze_vision(self, **post):
        try:
            # Log the raw request data
            raw_data = request.httprequest.data
            _logger.info(f"[VisionAI] Received request: {raw_data}")
            try:
                r_data = json.loads(raw_data)
                data = r_data.get('data')
                _logger.info(f"[VisionAI] Parsed JSON: {data}")
            except Exception as e:
                _logger.error(f"[VisionAI] JSON decode error: {str(e)} | Raw data: {raw_data}")
                error_response = {
                    'error_code': 'invalid_json',
                    'message': 'Invalid JSON in request body',
                    'details': str(e)
                }
                _logger.info(f"[VisionAI] Returning error response: {error_response}")
                return Response(
                    json.dumps(error_response),
                    content_type='application/json',
                    status=400,
                    headers=get_cors_headers(request)
                ) 
            attachment_urls = data.get('cs_vision_attachment')
            instructions = data.get('cs_vision_instruction')
            custom_api_key = data.get('cs_vision_openai_api_key')
            _logger.info(f"[VisionAI] attachment_urls: {attachment_urls}, instructions: {instructions}")

            if not attachment_urls or not instructions:
                _logger.warning(f"[VisionAI] Missing required fields: attachment_urls={attachment_urls}, instructions={instructions}")
                error_response = {
                    'error_code': 'missing_fields',
                    'message': 'attachment_urls and instructions are required',
                    'details': {'attachment_urls': attachment_urls, 'instructions': instructions}
                }
                _logger.info(f"[VisionAI] Returning error response: {error_response}")
                return Response(
                    json.dumps(error_response),
                    content_type='application/json',
                    status=400,
                    headers=get_cors_headers(request)
                )

            # Get OpenAI API key from request data or system parameters
            api_key = custom_api_key or request.env['ir.config_parameter'].sudo().get_param('web_scraper.openai_api_key')
            _logger.info(f"[VisionAI] Using OpenAI API key: {'custom' if custom_api_key else 'system' if api_key else 'not set'}")
            if not api_key:
                _logger.error("[VisionAI] OpenAI API key not configured. Please provide cs_vision_openai_api_key or configure system parameter web_scraper.openai_api_key")
                error_response = {
                    'error_code': 'no_api_key',
                    'message': 'OpenAI API key not configured. Please provide cs_vision_openai_api_key or configure system parameter web_scraper.openai_api_key'
                }
                _logger.info(f"[VisionAI] Returning error response: {error_response}")
                return Response(
                    json.dumps(error_response),
                    content_type='application/json',
                    status=500,
                    headers=get_cors_headers(request)
                )

            # Download the file content
            try:
                _logger.info(f"[VisionAI] Downloading file from: {attachment_urls}")
                response = requests.get(attachment_urls)
                response.raise_for_status()
                file_content = response.content
                _logger.info(f"[VisionAI] File downloaded successfully. Size: {len(file_content)} bytes")
            except Exception as e:
                _logger.error(f"[VisionAI] Error downloading file from {attachment_urls}: {str(e)}")
                error_response = {
                    'error_code': 'download_failed',
                    'message': f'Error downloading file from {attachment_urls}',
                    'details': str(e)
                }
                _logger.info(f"[VisionAI] Returning error response: {error_response}")
                return Response(
                    json.dumps(error_response),
                    content_type='application/json',
                    status=400,
                    headers=get_cors_headers(request)
                )

            # Determine file type from URL
            file_type = 'image'
            if attachment_urls.lower().endswith('.pdf'):
                file_type = 'pdf'
            _logger.info(f"[VisionAI] Detected file type: {file_type}")

            # Prepare the content based on file type
            content = [
                {
                    'type': 'text',
                    'text': instructions
                }
            ]

            if file_type == 'image':
                # Convert image content to base64
                try:
                    base64_content = base64.b64encode(file_content).decode('utf-8')
                    _logger.info(f"[VisionAI] Image encoded to base64. Length: {len(base64_content)}")
                    content.append({
                        'type': 'image_url',
                        'image_url': {
                            'url': f"data:image/jpeg;base64,{base64_content}"
                        }
                    })
                    _logger.info(f"[VisionAI] Added image_url to OpenAI payload.")
                except Exception as e:
                    _logger.error(f"[VisionAI] Base64 encoding error: {str(e)}")
                    error_response = {
                        'error_code': 'base64_error',
                        'message': 'Failed to encode image as base64',
                        'details': str(e)
                    }
                    _logger.info(f"[VisionAI] Returning error response: {error_response}")
                    return Response(
                        json.dumps(error_response),
                        content_type='application/json',
                        status=500,
                        headers=get_cors_headers(request)
                    )
            else:  # PDF
                try:
                    # Extract text from PDF
                    pdf_file = io.BytesIO(file_content)
                    pdf_reader = PyPDF2.PdfReader(pdf_file)
                    pdf_text = ""
                    for page in pdf_reader.pages:
                        pdf_text += page.extract_text() + "\n"
                    
                    # Add PDF text to the content
                    content.append({
                        'type': 'text',
                        'text': f"Here is the content of the PDF document:\n\n{pdf_text}"
                    })
                    _logger.info(f"[VisionAI] Added PDF text to OpenAI payload. Text length: {len(pdf_text)}")
                except Exception as e:
                    _logger.error(f"[VisionAI] PDF processing error: {str(e)}")
                    error_response = {
                        'error_code': 'pdf_processing_error',
                        'message': 'Failed to process PDF document',
                        'details': str(e)
                    }
                    _logger.info(f"[VisionAI] Returning error response: {error_response}")
                    return Response(
                        json.dumps(error_response),
                        content_type='application/json',
                        status=500,
                        headers=get_cors_headers(request)
                    )

            # Prepare the request to OpenAI
            headers = {
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            }
            _logger.info(f"[VisionAI] Prepared OpenAI headers.")

            payload = {
                'model': 'gpt-4o',
                'messages': [
                    {
                        'role': 'user',
                        'content': content
                    }
                ],
                'max_tokens': 300
            }
            _logger.info(f"[VisionAI] OpenAI payload prepared: {json.dumps(payload)[:500]}... (truncated)")

            # Make the request to OpenAI
            try:
                _logger.info(f"[VisionAI] Sending request to OpenAI API.")
                response = requests.post(
                    'https://api.openai.com/v1/chat/completions',
                    headers=headers,
                    json=payload
                )
                _logger.info(f"[VisionAI] OpenAI API responded with status {response.status_code}")
            except Exception as e:
                _logger.error(f"[VisionAI] Error making request to OpenAI: {str(e)}")
                error_response = {
                    'error_code': 'openai_request_failed',
                    'message': 'Failed to connect to OpenAI API',
                    'details': str(e)
                }
                _logger.info(f"[VisionAI] Returning error response: {error_response}")
                return Response(
                    json.dumps(error_response),
                    content_type='application/json',
                    status=500,
                    headers=get_cors_headers(request)
                )

            if response.status_code != 200:
                _logger.error(f"[VisionAI] OpenAI API error: {response.status_code} | {response.text}")
                error_response = {
                    'error_code': 'openai_api_error',
                    'message': 'OpenAI API returned an error',
                    'status_code': response.status_code,
                    'details': response.text
                }
                _logger.info(f"[VisionAI] Returning error response: {error_response}")
                return Response(
                    json.dumps(error_response),
                    content_type='application/json',
                    status=response.status_code,
                    headers=get_cors_headers(request)
                )

            # Parse the response
            try:
                result = response.json()
                description = result['choices'][0]['message']['content']
                _logger.info(f"[VisionAI] OpenAI response parsed successfully. Description: {description}")
            except Exception as e:
                _logger.error(f"[VisionAI] Error parsing OpenAI response: {str(e)} | Response: {response.text}")
                error_response = {
                    'error_code': 'openai_response_parse_error',
                    'message': 'Failed to parse OpenAI response',
                    'details': str(e),
                    'raw_response': response.text
                }
                _logger.info(f"[VisionAI] Returning error response: {error_response}")
                return Response(
                    json.dumps(error_response),
                    content_type='application/json',
                    status=500,
                    headers=get_cors_headers(request)
                )

            success_response = {
                'status_code': 200,
                'response': {
                    'description': description
                }
            }
            _logger.info(f"[VisionAI] Returning success response: {success_response}")
            return Response(
                json.dumps(success_response),
                content_type='application/json',
                headers=get_cors_headers(request)
            )

        except Exception as e:
            _logger.error(f"[VisionAI] Unexpected error in vision analysis: {str(e)}", exc_info=True)
            error_response = {
                'error_code': 'unexpected_error',
                'message': 'An unexpected error occurred',
                'details': str(e)
            }
            _logger.info(f"[VisionAI] Returning error response: {error_response}")
            return Response(
                json.dumps(error_response),
                content_type='application/json',
                status=500,
                headers=get_cors_headers(request)
            ) 

    @http.route('/cs-vision-ai', type='http', auth='none', methods=['POST', 'OPTIONS'], cors='*', csrf=False)
    def cs_vision_ai_receiver(self, **post):
        try:
            raw_data = request.httprequest.data
            _logger.info(f"[CSVisionAI] Received request: {raw_data}")
            try:
                data = json.loads(raw_data)
                _logger.info(f"[CSVisionAI] Parsed JSON: {data}")
            except Exception as e:
                _logger.error(f"[CSVisionAI] JSON decode error: {str(e)} | Raw data: {raw_data}")
                error_response = {
                    'error_code': 'invalid_json',
                    'message': 'Invalid JSON in request body',
                    'details': str(e)
                }
                return Response(
                    json.dumps(error_response),
                    content_type='application/json',
                    status=400,
                    headers=get_cors_headers(request)
                )
            # Just return a success response
            success_response = {
                'status_code': 200,
                'message': 'CS Vision AI data received successfully.'
            }
            return Response(
                json.dumps(success_response),
                content_type='application/json',
                headers=get_cors_headers(request)
            )
        except Exception as e:
            _logger.error(f"[CSVisionAI] Unexpected error: {str(e)}", exc_info=True)
            error_response = {
                'error_code': 'unexpected_error',
                'message': 'An unexpected error occurred',
                'details': str(e)
            }
            return Response(
                json.dumps(error_response),
                content_type='application/json',
                status=500,
                headers=get_cors_headers(request)
            ) 