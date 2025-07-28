# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request, Response
import json
import logging

_logger = logging.getLogger(__name__)

class CyclSalesVisionTriggerController(http.Controller):
    @http.route('/cs-vision/trigger-webhook', type='json', auth='none', methods=['POST'], csrf=False)
    def cs_vision_trigger_webhook(self, **post):
        try:
            raw_data = request.httprequest.data
            _logger.info(f"[CyclSalesVisionTrigger] Received webhook: {raw_data}")
            try:
                payload = json.loads(raw_data)
            except Exception as e:
                _logger.error(f"[CyclSalesVisionTrigger] JSON decode error: {str(e)} | Raw data: {raw_data}")
                return Response(json.dumps({'status': 'error', 'message': 'Invalid JSON', 'details': str(e)}), content_type='application/json', status=400)
            
            # Extract trigger data and event type
            trigger_data = payload.get('triggerData', {})
            event_type = trigger_data.get('eventType')
            external_id = trigger_data.get('id')
            
            _logger.info(f"[CyclSalesVisionTrigger] Processing event type: {event_type} for trigger: {external_id}")
            
            if event_type == 'DELETED':
                # Handle trigger deletion - set status to inactive
                trigger = request.env['cyclsales.vision.trigger'].sudo().update_trigger_status(
                    external_id, 'inactive', 'Trigger deleted in GHL'
                )
                if trigger:
                    _logger.info(f"[CyclSalesVisionTrigger] Marked trigger {external_id} as inactive (deleted)")
                    return Response(json.dumps({
                        'status': 'success', 
                        'message': 'Trigger marked as inactive',
                        'trigger_id': trigger.id
                    }), content_type='application/json')
                else:
                    _logger.warning(f"[CyclSalesVisionTrigger] Trigger {external_id} not found for deletion")
                    return Response(json.dumps({
                        'status': 'warning', 
                        'message': 'Trigger not found for deletion'
                    }), content_type='application/json')
            elif event_type in ['CREATED', 'UPDATED']:
                # Handle normal trigger creation/update
                trigger = request.env['cyclsales.vision.trigger'].sudo().create_or_update_from_webhook(payload)
                _logger.info(f"[CyclSalesVisionTrigger] {'Created' if event_type == 'CREATED' else 'Updated'} trigger {external_id}")
                return Response(json.dumps({
                    'status': 'success', 
                    'message': f'Trigger {event_type.lower()} successfully',
                    'trigger_id': trigger.id
                }), content_type='application/json')
            else:
                # Handle unknown event types
                _logger.warning(f"[CyclSalesVisionTrigger] Unknown event type: {event_type} for trigger {external_id}")
                return Response(json.dumps({
                    'status': 'warning', 
                    'message': f'Unknown event type: {event_type}'
                }), content_type='application/json')
                
        except Exception as e:
            _logger.error(f"[CyclSalesVisionTrigger] Unexpected error: {str(e)}", exc_info=True)
            return Response(json.dumps({'status': 'error', 'message': str(e)}), content_type='application/json', status=500) 