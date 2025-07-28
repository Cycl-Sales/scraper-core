# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request, Response
import json
import logging
_logger = logging.getLogger(__name__)

class AutomationTemplateController(http.Controller):
    def serialize_template(template):
        def serialize_call_transcript_setting(rec):
            return {
                'id': rec.id,
                'enabled': rec.enabled,
                'add_user_data': rec.add_user_data,
                'update_contact_name': rec.update_contact_name,
                'improve_speaker_accuracy': rec.improve_speaker_accuracy,
                'improve_word_accuracy': rec.improve_word_accuracy,
                'assign_speaker_labels': rec.assign_speaker_labels,
                'save_full_transcript': rec.save_full_transcript,
                'save_transcript_url': rec.save_transcript_url,
            }
        def serialize_extract_detail(rec):
            return {
                'id': rec.id,
                'question': rec.question,
            }
        def serialize_call_summary_setting(rec):
            return {
                'id': rec.id,
                'enabled': rec.enabled,
                'add_url_to_note': rec.add_url_to_note,
                'update_summary_field': rec.update_summary_field,
                'create_contact_note': rec.create_contact_note,
                'extract_detail_ids': [serialize_extract_detail(ed) for ed in rec.extract_detail_ids],
            }
        def serialize_sales_rule(rec):
            return {
                'id': rec.id,
                'rule_text': rec.rule_text,
            }
        def serialize_ai_sales_scoring_setting(rec):
            return {
                'id': rec.id,
                'enabled': rec.enabled,
                'framework': rec.framework,
                'rule_ids': [serialize_sales_rule(r) for r in rec.rule_ids],
            }
        def serialize_run_contact_automations_setting(rec):
            return {
                'id': rec.id,
                'enabled': rec.enabled,
                'disable_for_tag': rec.disable_for_tag,
                'after_inactivity': rec.after_inactivity,
                'inactivity_hours': rec.inactivity_hours,
                'after_min_duration': rec.after_min_duration,
                'min_duration_seconds': rec.min_duration_seconds,
                'after_message_count': rec.after_message_count,
                'message_count': rec.message_count,
            }
        def serialize_status_option(rec):
            return {
                'id': rec.id,
                'name': rec.name,
                'description': rec.description,
                'icon': rec.icon,
                'color': rec.color,
            }
        def serialize_contact_status_setting(rec):
            return {
                'id': rec.id,
                'enabled': rec.enabled,
                'add_status_tag': rec.add_status_tag,
                'update_status_field': rec.update_status_field,
                'status_option_ids': [serialize_status_option(opt) for opt in rec.status_option_ids],
            }
        def serialize_ai_contact_scoring_setting(rec):
            return {
                'id': rec.id,
                'enabled': rec.enabled,
                'use_notes_for_context': rec.use_notes_for_context,
                'update_score_field': rec.update_score_field,
                'add_score_tag': rec.add_score_tag,
                'examples_rules': rec.examples_rules,
            }
        def serialize_full_contact_summary_setting(rec):
            return {
                'id': rec.id,
                'enabled': rec.enabled,
                'use_call_summary_fields': rec.use_call_summary_fields,
                'update_status_summary': rec.update_status_summary,
                'create_summary_note': rec.create_summary_note,
                'delete_old_summary': rec.delete_old_summary,
            }
        def serialize_value_example(rec):
            return {
                'id': rec.id,
                'example_text': rec.example_text,
            }
        def serialize_contact_value_setting(rec):
            return {
                'id': rec.id,
                'enabled': rec.enabled,
                'update_value_field': rec.update_value_field,
                'use_value_override': rec.use_value_override,
                'value_example_ids': [serialize_value_example(ve) for ve in rec.value_example_ids],
            }
        def serialize_task_rule(rec):
            return {
                'id': rec.id,
                'rule_text': rec.rule_text,
            }
        def serialize_task_generation_setting(rec):
            return {
                'id': rec.id,
                'enabled': rec.enabled,
                'auto_complete_tasks': rec.auto_complete_tasks,
                'auto_reschedule_tasks': rec.auto_reschedule_tasks,
                'task_rule_ids': [serialize_task_rule(tr) for tr in rec.task_rule_ids],
            }
        return {
            'id': template.id,
            'name': template.name,
            'location_id': template.location_id.id if template.location_id else None,
            'parent_template_id': template.parent_template_id.id if template.parent_template_id else None,
            'is_default': template.is_default,
            'business_context': template.business_context,
            'call_transcript_setting_ids': [serialize_call_transcript_setting(x) for x in template.call_transcript_setting_ids],
            'call_summary_setting_ids': [serialize_call_summary_setting(x) for x in template.call_summary_setting_ids],
            'ai_sales_scoring_setting_ids': [serialize_ai_sales_scoring_setting(x) for x in template.ai_sales_scoring_setting_ids],
            'run_contact_automations_setting_ids': [serialize_run_contact_automations_setting(x) for x in template.run_contact_automations_setting_ids],
            'contact_status_setting_ids': [serialize_contact_status_setting(x) for x in template.contact_status_setting_ids],
            'ai_contact_scoring_setting_ids': [serialize_ai_contact_scoring_setting(x) for x in template.ai_contact_scoring_setting_ids],
            'full_contact_summary_setting_ids': [serialize_full_contact_summary_setting(x) for x in template.full_contact_summary_setting_ids],
            'contact_value_setting_ids': [serialize_contact_value_setting(x) for x in template.contact_value_setting_ids],
            'task_generation_setting_ids': [serialize_task_generation_setting(x) for x in template.task_generation_setting_ids],
        }

    @http.route('/api/automation_template/update', type='json', auth='user', methods=['POST'], csrf=False)
    def update_automation_template(self, **kwargs):
        """
        Update or create an automation template for a given location (sub-account).
        Expects JSON body with at least 'location_id' and fields to update.
        """
        data = getattr(request, 'jsonrequest', {}) or {}
        print('API CALL: /api/automation_template/update with data:', data)
        _logger.warning('API CALL: /api/automation_template/update with data: %s', data)
        if not data or 'location_id' not in data:
            print('ERROR: location_id is required')
            _logger.warning('ERROR: location_id is required')
            return {'error': 'location_id is required'}
        location_id = data['location_id']
        # Find or create the template for this location
        template = request.env['automation.template'].sudo().search([('location_id', '=', location_id)], limit=1)
        if not template:
            # Optionally, inherit from default template
            default_template = request.env['automation.template'].sudo().search([('is_default', '=', True)], limit=1)
            vals = {'location_id': location_id}
            if default_template:
                vals['parent_template_id'] = default_template.id
            template = request.env['automation.template'].sudo().create(vals)
        # Update fields from data (ignore location_id and id)
        update_fields = {k: v for k, v in data.items() if k not in ['id', 'location_id']}
        if update_fields:
            template.sudo().write(update_fields)
        # Return updated template as JSON
        result = serialize_template(template)
        print('Returning updated automation template:', result)
        _logger.warning('Returning updated automation template: %s', result)
        return result 

    @http.route('/api/automation_template/get', type='json', auth='user', methods=['POST'], csrf=False)
    def get_automation_template(self, **kwargs):
        """
        Fetch the automation template for a given location (sub-account).
        Expects JSON body with 'location_id'.
        """
        data = getattr(request, 'jsonrequest', {}) or {}
        if not data or 'location_id' not in data:
            return {'error': 'location_id is required'}
        location_id = data['location_id']
        template = request.env['automation.template'].sudo().search([('location_id', '=', location_id)], limit=1)
        if not template:
            # Optionally, return the default template if exists
            default_template = request.env['automation.template'].sudo().search([('is_default', '=', True)], limit=1)
            if default_template:
                result = serialize_template(default_template)
                print('Returning default automation template data:', result)
                _logger.info('Returning default automation template data: %s', result)
                return result
            else:
                return {}
        result = serialize_template(template)
        print('Returning automation template data:', result)
        _logger.info('Returning automation template data: %s', result)
        return result 

    @http.route('/api/automation_template/get_by_id', type='json', auth='user', methods=['POST'], csrf=False)
    def get_automation_template_by_id(self, **kwargs):
        params = getattr(request, 'jsonrequest', {}) or {}
        # If JSON-RPC, use params['params'], else use params directly
        if 'params' in params:
            data = params['params']
        else:
            data = params
        print('API CALL: /api/automation_template/get_by_id with data:', data)
        _logger.warning('API CALL: /api/automation_template/get_by_id with data: %s', data)
        template_id = data.get('id')
        if not template_id:
            print('ERROR: id is required')
            _logger.warning('ERROR: id is required')
            return {'error': 'id is required'}
        template = request.env['automation.template'].sudo().browse(template_id)
        if not template.exists():
            print('ERROR: template not found')
            _logger.warning('ERROR: template not found')
            return {'error': 'template not found'}
        result = serialize_template(template)
        print('Returning automation template by id:', result)
        _logger.warning('Returning automation template by id: %s', result)
        return result

    @http.route('/api/automation_template/list', type='json', auth='user', methods=['POST'], csrf=False)
    def list_automation_templates(self, **kwargs):
        """
        List all automation templates (id and name only).
        """
        print('API CALL: /api/automation_template/list')
        _logger.warning('API CALL: /api/automation_template/list')
        templates = request.env['automation.template'].sudo().search([])
        data = [{'id': t.id, 'name': t.name} for t in templates]
        print('Returning template list:', data)
        _logger.warning('Returning template list: %s', data)
        return {'templates': data} 