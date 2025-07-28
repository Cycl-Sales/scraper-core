# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request, Response
import json
import logging

_logger = logging.getLogger(__name__)

class CyclSalesVisionSampleController(http.Controller):
    
    @http.route('/cs-vision/sample-endpoint', type='http', auth='none', methods=['POST', 'OPTIONS'], cors='*', csrf=False)
    def sample_endpoint(self, **post):
        """Sample endpoint to receive and process sample information"""
        try:
            # Handle OPTIONS request for CORS
            if request.httprequest.method == 'OPTIONS':
                return Response(
                    json.dumps({'status': 'ok'}),
                    content_type='application/json',
                    status=200,
                    headers={
                        'Access-Control-Allow-Origin': '*',
                        'Access-Control-Allow-Methods': 'POST, OPTIONS',
                        'Access-Control-Allow-Headers': 'Content-Type, Authorization'
                    }
                )
            
            # Get data from request body
            raw_data = request.httprequest.data
            _logger.info(f"[Sample Endpoint] Received raw data: {raw_data}")
            
            # Try to get data from POST parameters
            post_data = dict(request.params)
            _logger.info(f"[Sample Endpoint] POST parameters: {post_data}")
            
            # Parse JSON from request body
            data = {}
            if raw_data and raw_data != b'{}':
                try:
                    data = json.loads(raw_data)
                    _logger.info(f"[Sample Endpoint] Parsed JSON from body: {data}")
                except Exception as e:
                    _logger.error(f"[Sample Endpoint] JSON decode error: {str(e)} | Raw data: {raw_data}")
                    data = post_data
            else:
                data = post_data
            
            # Log request details
            _logger.info(f"[Sample Endpoint] Request headers: {dict(request.httprequest.headers)}")
            _logger.info(f"[Sample Endpoint] Request method: {request.httprequest.method}")
            _logger.info(f"[Sample Endpoint] Request URL: {request.httprequest.url}")
            
            # Log all received fields
            for key, value in data.items():
                _logger.info(f"[Sample Endpoint] Field '{key}': {value}")
            
            # Process the sample data (customize this based on your needs)
            processed_data = self._process_sample_data(data)
            
            # Return the processed data
            return Response(
                json.dumps({
                    'status': 'success',
                    'message': 'Sample data received and processed successfully',
                    'received_data': data,
                    'processed_data': processed_data,
                    'timestamp': request.env['ir.config_parameter'].sudo().get_param('web.base.url')
                }),
                content_type='application/json',
                status=200,
                headers={
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': 'POST, OPTIONS',
                    'Access-Control-Allow-Headers': 'Content-Type, Authorization'
                }
            )
            
        except Exception as e:
            _logger.error(f"[Sample Endpoint] Unexpected error: {str(e)}", exc_info=True)
            return Response(
                json.dumps({
                    'error_code': 'unexpected_error',
                    'message': 'An unexpected error occurred',
                    'details': str(e)
                }),
                content_type='application/json',
                status=500
            )

    @http.route('/cs-vision/sample-get', type='http', auth='none', methods=['GET'], cors='*', csrf=False)
    def sample_get_endpoint(self, **kwargs):
        """Sample GET endpoint to return sample data"""
        try:
            _logger.info(f"[Sample GET] Received GET request with parameters: {kwargs}")
            
            # Generate sample response data
            sample_data = {
                'message': 'Hello from sample GET endpoint!',
                'parameters_received': kwargs,
                'sample_fields': {
                    'field1': 'Sample value 1',
                    'field2': 'Sample value 2',
                    'field3': 'Sample value 3'
                },
                'status': 'active',
                'timestamp': '2025-07-28T19:50:00Z'
            }
            
            return Response(
                json.dumps(sample_data),
                content_type='application/json',
                status=200,
                headers={
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': 'GET',
                    'Access-Control-Allow-Headers': 'Content-Type, Authorization'
                }
            )
            
        except Exception as e:
            _logger.error(f"[Sample GET] Unexpected error: {str(e)}", exc_info=True)
            return Response(
                json.dumps({
                    'error_code': 'unexpected_error',
                    'message': 'An unexpected error occurred',
                    'details': str(e)
                }),
                content_type='application/json',
                status=500
            )

    def _process_sample_data(self, data):
        """
        Process the received sample data
        Customize this method based on your specific needs
        """
        try:
            processed = {
                'original_count': len(data),
                'fields_processed': list(data.keys()),
                'has_required_fields': 'sample_field' in data,
                'data_summary': f"Received {len(data)} fields: {', '.join(data.keys())}"
            }
            
            # Check for summary and keywords fields from GHL workflow
            if 'customData' in data:
                custom_data = data['customData']
                if isinstance(custom_data, dict):
                    processed['has_summary'] = 'summary' in custom_data
                    processed['has_keywords'] = 'keywords' in custom_data
                    processed['summary_value'] = custom_data.get('summary', 'Not found')
                    processed['keywords_value'] = custom_data.get('keywords', 'Not found')
                else:
                    processed['customData_type'] = type(custom_data).__name__
                    processed['customData_value'] = str(custom_data)
            
            # Also check for direct summary and keywords fields
            processed['direct_summary'] = data.get('summary', 'Not found')
            processed['direct_keywords'] = data.get('keywords', 'Not found')
            
            # Add any custom processing logic here
            if 'sample_field' in data:
                processed['sample_field_value'] = data['sample_field']
                processed['sample_field_length'] = len(str(data['sample_field']))
            
            return processed
            
        except Exception as e:
            _logger.error(f"[Sample Processing] Error processing data: {str(e)}")
            return {
                'error': 'Failed to process sample data',
                'details': str(e)
            } 