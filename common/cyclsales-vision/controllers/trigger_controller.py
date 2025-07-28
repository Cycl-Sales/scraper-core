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
            trigger = request.env['cyclsales.vision.trigger'].sudo().create_or_update_from_webhook(payload)
            return Response(json.dumps({'status': 'success', 'trigger_id': trigger.id}), content_type='application/json')
        except Exception as e:
            _logger.error(f"[CyclSalesVisionTrigger] Unexpected error: {str(e)}", exc_info=True)
            return Response(json.dumps({'status': 'error', 'message': str(e)}), content_type='application/json', status=500) 