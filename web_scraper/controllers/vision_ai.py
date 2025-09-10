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
            try:
                r_data = json.loads(raw_data)
                data = r_data.get('data')
            except Exception as e:
                _logger.error(f"[VisionAI] JSON decode error: {str(e)} | Raw data: {raw_data}")
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
            attachment_urls = data.get('cs_vision_attachment')
            instructions = data.get('cs_vision_instruction')
            custom_api_key = data.get('cs_vision_openai_api_key')

            if not attachment_urls or not instructions:
                _logger.warning(f"[VisionAI] Missing required fields: attachment_urls={attachment_urls}, instructions={instructions}")
                error_response = {
                    'error_code': 'missing_fields',
                    'message': 'attachment_urls and instructions are required',
                    'details': {'attachment_urls': attachment_urls, 'instructions': instructions}
                }
                return Response(
                    json.dumps(error_response),
                    content_type='application/json',
                    status=400,
                    headers=get_cors_headers(request)
                )

            # Get OpenAI API key from request data or system parameters
            api_key = custom_api_key or request.env['ir.config_parameter'].sudo().get_param('web_scraper.openai_api_key')
            if not api_key:
                _logger.error("[VisionAI] OpenAI API key not configured. Please provide cs_vision_openai_api_key or configure system parameter web_scraper.openai_api_key")
                error_response = {
                    'error_code': 'no_api_key',
                    'message': 'OpenAI API key not configured. Please provide cs_vision_openai_api_key or configure system parameter web_scraper.openai_api_key'
                }
                return Response(
                    json.dumps(error_response),
                    content_type='application/json',
                    status=500,
                    headers=get_cors_headers(request)
                )

            # Download the file content
            try:
                response = requests.get(attachment_urls)
                response.raise_for_status()
                file_content = response.content
            except Exception as e:
                _logger.error(f"[VisionAI] Error downloading file from {attachment_urls}: {str(e)}")
                error_response = {
                    'error_code': 'download_failed',
                    'message': f'Error downloading file from {attachment_urls}',
                    'details': str(e)
                }
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
                    content.append({
                        'type': 'image_url',
                        'image_url': {
                            'url': f"data:image/jpeg;base64,{base64_content}"
                        }
                    })
                except Exception as e:
                    _logger.error(f"[VisionAI] Base64 encoding error: {str(e)}")
                    error_response = {
                        'error_code': 'base64_error',
                        'message': 'Failed to encode image as base64',
                        'details': str(e)
                    }
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
                except Exception as e:
                    _logger.error(f"[VisionAI] PDF processing error: {str(e)}")
                    error_response = {
                        'error_code': 'pdf_processing_error',
                        'message': 'Failed to process PDF document',
                        'details': str(e)
                    }
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

            # Make the request to OpenAI
            try:
                response = requests.post(
                    'https://api.openai.com/v1/chat/completions',
                    headers=headers,
                    json=payload
                )
            except Exception as e:
                _logger.error(f"[VisionAI] Error making request to OpenAI: {str(e)}")
                error_response = {
                    'error_code': 'openai_request_failed',
                    'message': 'Failed to connect to OpenAI API',
                    'details': str(e)
                }
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
            except Exception as e:
                _logger.error(f"[VisionAI] Error parsing OpenAI response: {str(e)} | Response: {response.text}")
                error_response = {
                    'error_code': 'openai_response_parse_error',
                    'message': 'Failed to parse OpenAI response',
                    'details': str(e),
                    'raw_response': response.text
                }
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
            return Response(
                json.dumps(error_response),
                content_type='application/json',
                status=500,
                headers=get_cors_headers(request)
            ) 

    @http.route('/cs-vision-ai-analyzer', type='http', auth='none', methods=['POST', 'OPTIONS'], cors='*', csrf=False)
    def cs_vision_ai_analyzer(self, **post):
        """Analyze images using OpenAI Vision API"""
        try:
            # Handle OPTIONS request for CORS
            if request.httprequest.method == 'OPTIONS':
                return Response(
                    json.dumps({'status': 'ok'}),
                    content_type='application/json',
                    status=200,
                    headers=get_cors_headers(request)
                )

            # Get data from request
            raw_data = request.httprequest.data
            data = {}
            if raw_data:
                try:
                    data = json.loads(raw_data)
                except Exception as e:
                    _logger.error(f"[VisionAI] JSON decode error: {str(e)}")
                    return Response(
                        json.dumps({'error': 'Invalid JSON data'}),
                        content_type='application/json',
                        status=400,
                        headers=get_cors_headers(request)
                    )

            # Extract parameters
            attachment_urls = data.get('attachment_urls')
            instructions = data.get('instructions', 'Describe this image in detail.')
            custom_api_key = data.get('cs_vision_openai_api_key')

            if not attachment_urls:
                error_response = {
                    'error_code': 'missing_attachment_urls',
                    'message': 'attachment_urls is required'
                }
                return Response(
                    json.dumps(error_response),
                    content_type='application/json',
                    status=400,
                    headers=get_cors_headers(request)
                )

            # Get the AI service model for usage logging
            ai_service = request.env['cyclsales.vision.ai'].sudo().search([('is_active', '=', True)], limit=1)
            if not ai_service:
                # Create a default AI service if none exists
                ai_service = request.env['cyclsales.vision.ai'].sudo().create({
                    'name': 'Default OpenAI GPT-4 Vision Service',
                    'model_type': 'gpt-4o',
                    'base_url': 'https://api.openai.com/v1',
                    'max_tokens': 300,
                    'temperature': 0.3,
                    'is_active': True
                })

            # Get OpenAI API key from request data or system parameters
            api_key = custom_api_key or request.env['ir.config_parameter'].sudo().get_param('web_scraper.openai_api_key')
            if not api_key:
                _logger.error("[VisionAI] OpenAI API key not configured. Please provide cs_vision_openai_api_key or configure system parameter web_scraper.openai_api_key")
                error_response = {
                    'error_code': 'no_api_key',
                    'message': 'OpenAI API key not configured. Please provide cs_vision_openai_api_key or configure system parameter web_scraper.openai_api_key'
                }   
                return Response(
                    json.dumps(error_response),
                    content_type='application/json',
                    status=500,
                    headers=get_cors_headers(request)
                )

            # Download the file content
            try:
                response = requests.get(attachment_urls)
                response.raise_for_status()
                file_content = response.content
            except Exception as e:
                _logger.error(f"[VisionAI] Error downloading file from {attachment_urls}: {str(e)}")
                error_response = {
                    'error_code': 'download_failed',
                    'message': f'Error downloading file from {attachment_urls}',
                    'details': str(e)
                }
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
                    content.append({
                        'type': 'image_url',
                        'image_url': {
                            'url': f"data:image/jpeg;base64,{base64_content}"
                        }
                    })
                except Exception as e:
                    _logger.error(f"[VisionAI] Base64 encoding error: {str(e)}")
                    error_response = {
                        'error_code': 'base64_error',
                        'message': 'Failed to encode image as base64',
                        'details': str(e)
                    }
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
                except Exception as e:
                    _logger.error(f"[VisionAI] PDF processing error: {str(e)}")
                    error_response = {
                        'error_code': 'pdf_error',
                        'message': 'Failed to process PDF document',
                        'details': str(e)
                    }
                    return Response(
                        json.dumps(error_response),
                        content_type='application/json',
                        status=500,
                        headers=get_cors_headers(request)
                    )

            # Create a custom prompt for vision analysis
            vision_prompt = f"""Analyze the provided {file_type} and provide a detailed description.

Instructions: {instructions}

Please provide a comprehensive analysis of the {file_type} content, including:
- Visual elements and their significance
- Text content (if any)
- Overall context and purpose
- Any relevant details that would be useful for understanding the content

Return your analysis as a detailed description."""

            # Use the AI service model to generate analysis with usage logging
            try:
                # For vision analysis, we need to use a different approach since the AI service model
                # is designed for text-based analysis. We'll create a usage log manually and then
                # make the API call with proper logging.
                
                # Create usage log entry
                usage_log = request.env['cyclsales.vision.ai.usage.log'].sudo().create_usage_log(
                    location_id=data.get('location_id', 'unknown'),
                    ai_service_id=ai_service.id,
                    request_type='vision_analysis',
                    message_id=data.get('message_id', 'vision_analysis'),
                    contact_id=data.get('contact_id', 'unknown'),
                    conversation_id=data.get('conversation_id', 'unknown')
                )
                
                if usage_log:
                    usage_log.write({'status': 'processing'})

                # Prepare the request to OpenAI
                headers = {
                    'Authorization': f'Bearer {api_key}',
                    'Content-Type': 'application/json'
                }
                
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

                # Make the request to OpenAI
                try:
                    response = requests.post(
                        'https://api.openai.com/v1/chat/completions',
                        headers=headers,
                        json=payload
                    )
                except Exception as e:
                    _logger.error(f"[VisionAI] Error making request to OpenAI: {str(e)}")
                    if usage_log:
                        usage_log.update_failure(f"Request failed: {str(e)}", "REQUEST_FAILED")
                    error_response = {
                        'error_code': 'openai_request_failed',
                        'message': 'Failed to connect to OpenAI API',
                        'details': str(e)
                    }
                    return Response(
                        json.dumps(error_response),
                        content_type='application/json',
                        status=500,
                        headers=get_cors_headers(request)
                    )

                if response.status_code != 200:
                    _logger.error(f"[VisionAI] OpenAI API error: {response.status_code} | {response.text}")
                    if usage_log:
                        usage_log.update_failure(f"API error: {response.status_code}", f"HTTP_{response.status_code}")
                    error_response = {
                        'error_code': 'openai_api_error',
                        'message': 'OpenAI API returned an error',
                        'status_code': response.status_code,
                        'details': response.text
                    }
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
                    
                    # Update usage log with token information and success
                    if usage_log and 'usage' in result:
                        usage = result['usage']
                        usage_log.write({
                            'input_tokens': usage.get('prompt_tokens', 0),
                            'output_tokens': usage.get('completion_tokens', 0),
                            'response_length': len(description),
                            'response_summary': description[:500]  # Store first 500 chars
                        })
                        usage_log.update_success({'description': description})
                    
                    # Update AI service usage statistics
                    ai_service._record_success()
                    
                except Exception as e:
                    _logger.error(f"[VisionAI] Error parsing OpenAI response: {str(e)} | Response: {response.text}")
                    if usage_log:
                        usage_log.update_failure(f"Parse error: {str(e)}", "PARSE_ERROR")
                    error_response = {
                        'error_code': 'openai_response_parse_error',
                        'message': 'Failed to parse OpenAI response',
                        'details': str(e),
                        'raw_response': response.text
                    }
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
                return Response(
                    json.dumps(success_response),
                    content_type='application/json',
                    headers=get_cors_headers(request)
                )

            except Exception as e:
                _logger.error(f"[VisionAI] Error in vision analysis: {str(e)}", exc_info=True)
                if usage_log:
                    usage_log.update_failure(str(e), "EXCEPTION")
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

        except Exception as e:
            _logger.error(f"[VisionAI] Unexpected error in vision analysis: {str(e)}", exc_info=True)
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

    @http.route('/cs-vision-ai', type='http', auth='none', methods=['POST', 'OPTIONS'], cors='*', csrf=False)
    def cs_vision_ai_receiver(self, **post):
        try:
            raw_data = request.httprequest.data 
            try:
                data = json.loads(raw_data)
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