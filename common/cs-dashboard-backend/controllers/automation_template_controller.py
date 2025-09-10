# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request, Response
import json
import logging
from .cors_utils import get_cors_headers

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
            'automation_group': template.automation_group,
            'parent_template_id': template.parent_template_id.id if template.parent_template_id else None,
            'is_default': template.is_default,
            'business_context': template.business_context,
            'call_transcript_setting_ids': [serialize_call_transcript_setting(x) for x in
                                            template.call_transcript_setting_ids],
            'call_summary_setting_ids': [serialize_call_summary_setting(x) for x in template.call_summary_setting_ids],
            'ai_sales_scoring_setting_ids': [serialize_ai_sales_scoring_setting(x) for x in
                                             template.ai_sales_scoring_setting_ids],
            'run_contact_automations_setting_ids': [serialize_run_contact_automations_setting(x) for x in
                                                    template.run_contact_automations_setting_ids],
            'contact_status_setting_ids': [serialize_contact_status_setting(x) for x in
                                           template.contact_status_setting_ids],
            'ai_contact_scoring_setting_ids': [serialize_ai_contact_scoring_setting(x) for x in
                                               template.ai_contact_scoring_setting_ids],
            'full_contact_summary_setting_ids': [serialize_full_contact_summary_setting(x) for x in
                                                 template.full_contact_summary_setting_ids],
            'contact_value_setting_ids': [serialize_contact_value_setting(x) for x in
                                          template.contact_value_setting_ids],
            'task_generation_setting_ids': [serialize_task_generation_setting(x) for x in
                                            template.task_generation_setting_ids],
        }

    @http.route('/api/automation_template/update', type='http', auth='none', methods=['POST', 'OPTIONS'], csrf=False)
    def update_automation_template(self, **kwargs):
        """
        Update or create an automation template for a given location (sub-account).
        Implements copy-on-write pattern: if updating a default template, creates a new location-specific template.
        """
        if request.httprequest.method == 'OPTIONS':
            return Response(status=200, headers=get_cors_headers(request))

        # Get JSON data from request
        data = getattr(request, 'jsonrequest', {}) or {}
        
        # Try parsing the raw request body if no data from jsonrequest
        if not data:
            try:
                import json
                raw_body = request.httprequest.get_data(as_text=True)
                if raw_body:
                    data = json.loads(raw_body)
            except Exception as e:
                _logger.error('Error parsing request body: %s', str(e))
                return Response(
                    json.dumps({'error': 'Invalid JSON in request body'}),
                    content_type='application/json',
                    status=400,
                    headers=get_cors_headers(request)
                )
        
        # _logger.info('API CALL: /api/automation_template/update for location_id: %s, automation_group: %s', 
        #             data.get('location_id'), data.get('automation_group'))  # Reduced logging for production

        # Check if we have location_id or automation_group
        location_id = data.get('location_id')
        automation_group = data.get('automation_group')

        if not location_id and not automation_group:
            _logger.error('Missing required parameter: location_id or automation_group')
            return Response(
                json.dumps({'error': 'location_id or automation_group is required'}),
                content_type='application/json',
                status=400,
                headers=get_cors_headers(request)
            )

        # Find existing template
        template = False
        installed_location = None

        if location_id:
            # Find the installed.location record by GHL location_id
            installed_location = request.env['installed.location'].sudo().search([
                ('location_id', '=', location_id)
            ], limit=1)

            if not installed_location:
                _logger.error('No installed location found for location_id: %s', location_id)
                return Response(
                    json.dumps({'error': f'No installed location found for location_id: {location_id}'}),
                    content_type='application/json',
                    status=404,
                    headers=get_cors_headers(request)
                )

            # Check if the installed location has an automation template directly assigned
            if installed_location.automation_template_id:
                template = installed_location.automation_template_id
                # _logger.info('Found directly assigned template: %s (ID: %s)', template.name, template.id)  # Reduced logging for production

        if not template and automation_group:
            # Try to find template by automation_group
            template = request.env['automation.template'].sudo().search([
                ('automation_group', '=', automation_group)
            ], limit=1)
            if template:
                # _logger.info('Found template by automation_group: %s (ID: %s)', template.name, template.id)  # Reduced logging for production

        if not template and location_id and installed_location:
            # If no template is directly assigned, look for a template with matching automation_group
            if installed_location.automation_group:
                template = request.env['automation.template'].sudo().search([
                    ('automation_group', '=', installed_location.automation_group)
                ], limit=1)
                if template:
                    # _logger.info('Found template by automation_group: %s (ID: %s)', template.name, template.id)  # Reduced logging for production

        # Check if we're trying to update a default template
        if template and template.is_default:
            _logger.info('Creating location-specific copy of default template')

            # Create a new location-specific template based on the default
            if location_id and installed_location:
                # Use location name for the new template (without location_id)
                new_template_name = f"{installed_location.name} - Automation Template"
                new_template_vals = {
                    'name': new_template_name,
                    'parent_template_id': template.id,
                    'is_default': False,
                    'is_custom': True,
                    'business_context': template.business_context,
                    # Don't set automation_group to avoid sharing between locations
                }
            elif automation_group:
                new_template_name = f"{automation_group} - Custom Template"
                new_template_vals = {
                    'name': new_template_name,
                    'parent_template_id': template.id,
                    'is_default': False,
                    'is_custom': True,
                    'business_context': template.business_context,
                    'automation_group': automation_group,
                }
            else:
                return Response(
                    json.dumps({'error': 'Cannot create template without location_id or automation_group'}),
                    content_type='application/json',
                    status=400,
                    headers=get_cors_headers(request)
                )

            # Create the new template
            template = request.env['automation.template'].sudo().create(new_template_vals)

            # Copy all settings from the default template
            self._copy_template_settings(template, template.parent_template_id)

            # Update the installed location to point to the new template
            if location_id and installed_location:
                installed_location.automation_template_id = template.id
                _logger.info('Updated location %s to use new template: %s', installed_location.name, template.name)

            _logger.info('Created new location-specific template: %s (ID: %s)', template.name, template.id)

        if not template:
            # Create a new custom template for this location/group
            if location_id and installed_location:
                # Use location name for uniqueness (without location_id)
                template_name = f"{installed_location.name} - Automation Template"
                template = self._create_location_template(installed_location, template_name)
            elif automation_group:
                template_name = f"{automation_group} - Custom Template"
                template = self._create_group_template(automation_group, template_name)
            else:
                return Response(
                    json.dumps({'error': 'Cannot create template without location_id or automation_group'}),
                    content_type='application/json',
                    status=400,
                    headers=get_cors_headers(request)
                )

        # Update fields from data (ignore location_id, id, is_default, appId, and all One2many fields)
        one2many_fields = [
            'call_transcript_setting_ids', 'call_summary_setting_ids', 'ai_sales_scoring_setting_ids',
            'run_contact_automations_setting_ids', 'contact_status_setting_ids', 'ai_contact_scoring_setting_ids',
            'full_contact_summary_setting_ids', 'contact_value_setting_ids', 'task_generation_setting_ids'
        ]

        # Don't update the name if we just created a new location-specific template
        fields_to_ignore = ['id', 'location_id', 'is_default', 'appId', 'name'] + one2many_fields

        # If we just created a new template, don't overwrite the name
        if template.is_custom and template.parent_template_id:
            # This is a newly created custom template, preserve its location-specific name
            update_fields = {k: v for k, v in data.items() if k not in fields_to_ignore}
        else:
            # This is an existing template, allow name updates
            update_fields = {k: v for k, v in data.items() if
                             k not in ['id', 'location_id', 'is_default', 'appId'] + one2many_fields}

        if update_fields:
            template.sudo().write(update_fields)

        # Handle One2many fields separately
        self._update_template_settings(template, data)

        # Return updated template as JSON
        result = AutomationTemplateController.serialize_template(template)
        _logger.info('Successfully updated automation template: %s', template.name)
        return Response(
            json.dumps(result),
            content_type='application/json',
            status=200,
            headers=get_cors_headers(request)
        )

    def _update_template_settings(self, template, data):
        """
        Update the nested settings for a template.
        """
        _logger.info('Updating settings for template %s', template.id)

        def is_real_database_id(id_value):
            """Check if an ID is a real database ID (reasonable range) vs a temporary frontend ID"""
            if not id_value:
                return False
            # Database IDs are typically small positive integers
            # Frontend temporary IDs from Date.now() are very large numbers (timestamps)
            return isinstance(id_value, int) and 0 < id_value < 1000000

        # Update call transcript settings
        if 'call_transcript_setting_ids' in data and data['call_transcript_setting_ids']:
            # Get existing setting IDs to check for deletions
            existing_setting_ids = {setting.id for setting in template.call_transcript_setting_ids}
            updated_setting_ids = {setting_data.get('id') for setting_data in data['call_transcript_setting_ids'] if
                                   is_real_database_id(setting_data.get('id'))}

            # Delete settings that are no longer present
            for setting_id in existing_setting_ids - updated_setting_ids:
                setting = request.env['automation.call.transcript.setting'].sudo().browse(setting_id)
                if setting.exists():
                    setting.unlink()

            for setting_data in data['call_transcript_setting_ids']:
                if is_real_database_id(setting_data.get('id')):
                    # Update existing setting
                    setting = request.env['automation.call.transcript.setting'].sudo().browse(setting_data['id'])
                    if setting.exists():
                        setting.write({
                            'enabled': setting_data.get('enabled', False),
                            'add_user_data': setting_data.get('add_user_data', False),
                            'update_contact_name': setting_data.get('update_contact_name', False),
                            'improve_speaker_accuracy': setting_data.get('improve_speaker_accuracy', False),
                            'improve_word_accuracy': setting_data.get('improve_word_accuracy', False),
                            'assign_speaker_labels': setting_data.get('assign_speaker_labels', False),
                            'save_full_transcript': setting_data.get('save_full_transcript', False),
                            'save_transcript_url': setting_data.get('save_transcript_url', False),
                        })
                else:
                    # Create new setting
                    request.env['automation.call.transcript.setting'].sudo().create({
                        'template_id': template.id,
                        'enabled': setting_data.get('enabled', False),
                        'add_user_data': setting_data.get('add_user_data', False),
                        'update_contact_name': setting_data.get('update_contact_name', False),
                        'improve_speaker_accuracy': setting_data.get('improve_speaker_accuracy', False),
                        'improve_word_accuracy': setting_data.get('improve_word_accuracy', False),
                        'assign_speaker_labels': setting_data.get('assign_speaker_labels', False),
                        'save_full_transcript': setting_data.get('save_full_transcript', False),
                        'save_transcript_url': setting_data.get('save_transcript_url', False),
                    })

        # Update call summary settings
        if 'call_summary_setting_ids' in data and data['call_summary_setting_ids']:
            # Get existing setting IDs to check for deletions
            existing_setting_ids = {setting.id for setting in template.call_summary_setting_ids}
            updated_setting_ids = {setting_data.get('id') for setting_data in data['call_summary_setting_ids'] if
                                   is_real_database_id(setting_data.get('id'))}

            # Delete settings that are no longer present
            for setting_id in existing_setting_ids - updated_setting_ids:
                setting = request.env['automation.call.summary.setting'].sudo().browse(setting_id)
                if setting.exists():
                    setting.unlink()

            for setting_data in data['call_summary_setting_ids']:
                if is_real_database_id(setting_data.get('id')):
                    # Update existing setting
                    setting = request.env['automation.call.summary.setting'].sudo().browse(setting_data['id'])
                    if setting.exists():
                        setting.write({
                            'enabled': setting_data.get('enabled', False),
                            'add_url_to_note': setting_data.get('add_url_to_note', False),
                            'update_summary_field': setting_data.get('update_summary_field', False),
                            'create_contact_note': setting_data.get('create_contact_note', False),
                        })

                        # Handle extract details deletion and updates
                        if 'extract_detail_ids' in setting_data:
                            # Get existing detail IDs to check for deletions
                            existing_detail_ids = {detail.id for detail in setting.extract_detail_ids}
                            updated_detail_ids = {detail_data.get('id') for detail_data in
                                                  setting_data['extract_detail_ids'] if
                                                  is_real_database_id(detail_data.get('id'))}

                            # Delete details that are no longer present
                            for detail_id in existing_detail_ids - updated_detail_ids:
                                detail = request.env['automation.extract.detail'].sudo().browse(detail_id)
                                if detail.exists():
                                    detail.unlink()

                            for detail_data in setting_data['extract_detail_ids']:
                                if is_real_database_id(detail_data.get('id')):
                                    detail = request.env['automation.extract.detail'].sudo().browse(detail_data['id'])
                                    if detail.exists():
                                        detail.write({
                                            'question': detail_data.get('question', ''),
                                        })
                                else:
                                    # Create new extract detail
                                    request.env['automation.extract.detail'].sudo().create({
                                        'call_summary_setting_id': setting.id,
                                        'question': detail_data.get('question', ''),
                                    })
                else:
                    # Create new setting
                    new_setting = request.env['automation.call.summary.setting'].sudo().create({
                        'template_id': template.id,
                        'enabled': setting_data.get('enabled', False),
                        'add_url_to_note': setting_data.get('add_url_to_note', False),
                        'update_summary_field': setting_data.get('update_summary_field', False),
                        'create_contact_note': setting_data.get('create_contact_note', False),
                    })

                    # Create extract details for new setting
                    if 'extract_detail_ids' in setting_data:
                        for detail_data in setting_data['extract_detail_ids']:
                            request.env['automation.extract.detail'].sudo().create({
                                'call_summary_setting_id': new_setting.id,
                                'question': detail_data.get('question', ''),
                            })

        # Update AI sales scoring settings
        if 'ai_sales_scoring_setting_ids' in data and data['ai_sales_scoring_setting_ids']:
            # Get existing setting IDs to check for deletions
            existing_setting_ids = {setting.id for setting in template.ai_sales_scoring_setting_ids}
            updated_setting_ids = {setting_data.get('id') for setting_data in data['ai_sales_scoring_setting_ids'] if
                                   is_real_database_id(setting_data.get('id'))}

            # Delete settings that are no longer present
            for setting_id in existing_setting_ids - updated_setting_ids:
                setting = request.env['automation.ai.sales.scoring.setting'].sudo().browse(setting_id)
                if setting.exists():
                    setting.unlink()

            for setting_data in data['ai_sales_scoring_setting_ids']:
                if is_real_database_id(setting_data.get('id')):
                    # Update existing setting
                    setting = request.env['automation.ai.sales.scoring.setting'].sudo().browse(setting_data['id'])
                    if setting.exists():
                        setting.write({
                            'enabled': setting_data.get('enabled', False),
                            'framework': setting_data.get('framework', ''),
                        })

                        # Handle sales rules deletion and updates
                        if 'rule_ids' in setting_data:
                            # Get existing rule IDs to check for deletions
                            existing_rule_ids = {rule.id for rule in setting.rule_ids}
                            updated_rule_ids = {rule_data.get('id') for rule_data in setting_data['rule_ids'] if
                                                is_real_database_id(rule_data.get('id'))}

                            # Delete rules that are no longer present
                            for rule_id in existing_rule_ids - updated_rule_ids:
                                rule = request.env['automation.sales.rule'].sudo().browse(rule_id)
                                if rule.exists():
                                    rule.unlink()

                            for rule_data in setting_data['rule_ids']:
                                if is_real_database_id(rule_data.get('id')):
                                    rule = request.env['automation.sales.rule'].sudo().browse(rule_data['id'])
                                    if rule.exists():
                                        rule.write({
                                            'rule_text': rule_data.get('rule_text', ''),
                                        })
                                else:
                                    # Create new sales rule
                                    request.env['automation.sales.rule'].sudo().create({
                                        'sales_scoring_setting_id': setting.id,
                                        'rule_text': rule_data.get('rule_text', ''),
                                    })
                else:
                    # Create new setting
                    new_setting = request.env['automation.ai.sales.scoring.setting'].sudo().create({
                        'template_id': template.id,
                        'enabled': setting_data.get('enabled', False),
                        'framework': setting_data.get('framework', ''),
                    })

                    # Create sales rules for new setting
                    if 'rule_ids' in setting_data:
                        for rule_data in setting_data['rule_ids']:
                            request.env['automation.sales.rule'].sudo().create({
                                'sales_scoring_setting_id': new_setting.id,
                                'rule_text': rule_data.get('rule_text', ''),
                            })

        # Update run contact automations settings
        if 'run_contact_automations_setting_ids' in data and data['run_contact_automations_setting_ids']:
            # Get existing setting IDs to check for deletions
            existing_setting_ids = {setting.id for setting in template.run_contact_automations_setting_ids}
            updated_setting_ids = {setting_data.get('id') for setting_data in
                                   data['run_contact_automations_setting_ids'] if
                                   is_real_database_id(setting_data.get('id'))}

            # Delete settings that are no longer present
            for setting_id in existing_setting_ids - updated_setting_ids:
                setting = request.env['automation.run.contact.automations.setting'].sudo().browse(setting_id)
                if setting.exists():
                    setting.unlink()

            for setting_data in data['run_contact_automations_setting_ids']:
                if is_real_database_id(setting_data.get('id')):
                    # Update existing setting
                    setting = request.env['automation.run.contact.automations.setting'].sudo().browse(
                        setting_data['id'])
                    if setting.exists():
                        setting.write({
                            'enabled': setting_data.get('enabled', False),
                            'disable_for_tag': setting_data.get('disable_for_tag', False),
                            'after_inactivity': setting_data.get('after_inactivity', False),
                            'inactivity_hours': setting_data.get('inactivity_hours', 0),
                            'after_min_duration': setting_data.get('after_min_duration', False),
                            'min_duration_seconds': setting_data.get('min_duration_seconds', 0),
                            'after_message_count': setting_data.get('after_message_count', False),
                            'message_count': setting_data.get('message_count', 0),
                        })
                else:
                    # Create new setting
                    request.env['automation.run.contact.automations.setting'].sudo().create({
                        'template_id': template.id,
                        'enabled': setting_data.get('enabled', False),
                        'disable_for_tag': setting_data.get('disable_for_tag', False),
                        'after_inactivity': setting_data.get('after_inactivity', False),
                        'inactivity_hours': setting_data.get('inactivity_hours', 0),
                        'after_min_duration': setting_data.get('after_min_duration', False),
                        'min_duration_seconds': setting_data.get('min_duration_seconds', 0),
                        'after_message_count': setting_data.get('after_message_count', False),
                        'message_count': setting_data.get('message_count', 0),
                    })

        # Update contact status settings
        if 'contact_status_setting_ids' in data and data['contact_status_setting_ids']:
            # Get existing setting IDs to check for deletions
            existing_setting_ids = {setting.id for setting in template.contact_status_setting_ids}
            updated_setting_ids = {setting_data.get('id') for setting_data in data['contact_status_setting_ids'] if
                                   is_real_database_id(setting_data.get('id'))}

            # Delete settings that are no longer present
            for setting_id in existing_setting_ids - updated_setting_ids:
                setting = request.env['automation.contact.status.setting'].sudo().browse(setting_id)
                if setting.exists():
                    setting.unlink()

            for setting_data in data['contact_status_setting_ids']:
                if is_real_database_id(setting_data.get('id')):
                    # Update existing setting
                    setting = request.env['automation.contact.status.setting'].sudo().browse(setting_data['id'])
                    if setting.exists():
                        setting.write({
                            'enabled': setting_data.get('enabled', False),
                            'add_status_tag': setting_data.get('add_status_tag', False),
                            'update_status_field': setting_data.get('update_status_field', False),
                        })

                        # Handle status options deletion and updates
                        if 'status_option_ids' in setting_data:
                            # Get existing option IDs to check for deletions
                            existing_option_ids = {option.id for option in setting.status_option_ids}
                            updated_option_ids = {option_data.get('id') for option_data in
                                                  setting_data['status_option_ids'] if
                                                  is_real_database_id(option_data.get('id'))}

                            # Delete options that are no longer present
                            for option_id in existing_option_ids - updated_option_ids:
                                option = request.env['automation.status.option'].sudo().browse(option_id)
                                if option.exists():
                                    option.unlink()

                            for option_data in setting_data['status_option_ids']:
                                if is_real_database_id(option_data.get('id')):
                                    option = request.env['automation.status.option'].sudo().browse(option_data['id'])
                                    if option.exists():
                                        option.write({
                                            'name': option_data.get('name', ''),
                                            'description': option_data.get('description', ''),
                                            'icon': option_data.get('icon', ''),
                                            'color': option_data.get('color', ''),
                                        })
                                else:
                                    # Create new status option
                                    request.env['automation.status.option'].sudo().create({
                                        'contact_status_setting_id': setting.id,
                                        'name': option_data.get('name', ''),
                                        'description': option_data.get('description', ''),
                                        'icon': option_data.get('icon', ''),
                                        'color': option_data.get('color', ''),
                                    })
                else:
                    # Create new setting
                    new_setting = request.env['automation.contact.status.setting'].sudo().create({
                        'template_id': template.id,
                        'enabled': setting_data.get('enabled', False),
                        'add_status_tag': setting_data.get('add_status_tag', False),
                        'update_status_field': setting_data.get('update_status_field', False),
                    })

                    # Create status options for new setting
                    if 'status_option_ids' in setting_data:
                        for option_data in setting_data['status_option_ids']:
                            request.env['automation.status.option'].sudo().create({
                                'contact_status_setting_id': new_setting.id,
                                'name': option_data.get('name', ''),
                                'description': option_data.get('description', ''),
                                'icon': option_data.get('icon', ''),
                                'color': option_data.get('color', ''),
                            })

        # Update AI contact scoring settings
        if 'ai_contact_scoring_setting_ids' in data and data['ai_contact_scoring_setting_ids']:
            # Get existing setting IDs to check for deletions
            existing_setting_ids = {setting.id for setting in template.ai_contact_scoring_setting_ids}
            updated_setting_ids = {setting_data.get('id') for setting_data in data['ai_contact_scoring_setting_ids'] if
                                   is_real_database_id(setting_data.get('id'))}

            # Delete settings that are no longer present
            for setting_id in existing_setting_ids - updated_setting_ids:
                setting = request.env['automation.ai.contact.scoring.setting'].sudo().browse(setting_id)
                if setting.exists():
                    setting.unlink()

            for setting_data in data['ai_contact_scoring_setting_ids']:
                if is_real_database_id(setting_data.get('id')):
                    # Update existing setting
                    setting = request.env['automation.ai.contact.scoring.setting'].sudo().browse(setting_data['id'])
                    if setting.exists():
                        setting.write({
                            'enabled': setting_data.get('enabled', False),
                            'use_notes_for_context': setting_data.get('use_notes_for_context', False),
                            'update_score_field': setting_data.get('update_score_field', False),
                            'add_score_tag': setting_data.get('add_score_tag', False),
                            'examples_rules': setting_data.get('examples_rules', ''),
                        })
                else:
                    # Create new setting
                    request.env['automation.ai.contact.scoring.setting'].sudo().create({
                        'template_id': template.id,
                        'enabled': setting_data.get('enabled', False),
                        'use_notes_for_context': setting_data.get('use_notes_for_context', False),
                        'update_score_field': setting_data.get('update_score_field', False),
                        'add_score_tag': setting_data.get('add_score_tag', False),
                        'examples_rules': setting_data.get('examples_rules', ''),
                    })

        # Update full contact summary settings
        if 'full_contact_summary_setting_ids' in data and data['full_contact_summary_setting_ids']:
            # Get existing setting IDs to check for deletions
            existing_setting_ids = {setting.id for setting in template.full_contact_summary_setting_ids}
            updated_setting_ids = {setting_data.get('id') for setting_data in data['full_contact_summary_setting_ids']
                                   if is_real_database_id(setting_data.get('id'))}

            # Delete settings that are no longer present
            for setting_id in existing_setting_ids - updated_setting_ids:
                setting = request.env['automation.full.contact.summary.setting'].sudo().browse(setting_id)
                if setting.exists():
                    setting.unlink()

            for setting_data in data['full_contact_summary_setting_ids']:
                if is_real_database_id(setting_data.get('id')):
                    # Update existing setting
                    setting = request.env['automation.full.contact.summary.setting'].sudo().browse(setting_data['id'])
                    if setting.exists():
                        setting.write({
                            'enabled': setting_data.get('enabled', False),
                            'use_call_summary_fields': setting_data.get('use_call_summary_fields', False),
                            'update_status_summary': setting_data.get('update_status_summary', False),
                            'create_summary_note': setting_data.get('create_summary_note', False),
                            'delete_old_summary': setting_data.get('delete_old_summary', False),
                        })
                else:
                    # Create new setting
                    request.env['automation.full.contact.summary.setting'].sudo().create({
                        'template_id': template.id,
                        'enabled': setting_data.get('enabled', False),
                        'use_call_summary_fields': setting_data.get('use_call_summary_fields', False),
                        'update_status_summary': setting_data.get('update_status_summary', False),
                        'create_summary_note': setting_data.get('create_summary_note', False),
                        'delete_old_summary': setting_data.get('delete_old_summary', False),
                    })

        # Update contact value settings
        if 'contact_value_setting_ids' in data and data['contact_value_setting_ids']:
            # Get existing setting IDs to check for deletions
            existing_setting_ids = {setting.id for setting in template.contact_value_setting_ids}
            updated_setting_ids = {setting_data.get('id') for setting_data in data['contact_value_setting_ids'] if
                                   is_real_database_id(setting_data.get('id'))}

            # Delete settings that are no longer present
            for setting_id in existing_setting_ids - updated_setting_ids:
                setting = request.env['automation.contact.value.setting'].sudo().browse(setting_id)
                if setting.exists():
                    setting.unlink()

            for setting_data in data['contact_value_setting_ids']:
                if is_real_database_id(setting_data.get('id')):
                    # Update existing setting
                    setting = request.env['automation.contact.value.setting'].sudo().browse(setting_data['id'])
                    if setting.exists():
                        setting.write({
                            'enabled': setting_data.get('enabled', False),
                            'update_value_field': setting_data.get('update_value_field', False),
                            'use_value_override': setting_data.get('use_value_override', False),
                        })

                        # Handle value examples deletion and updates
                        if 'value_example_ids' in setting_data:
                            # Get existing example IDs to check for deletions
                            existing_example_ids = {example.id for example in setting.value_example_ids}
                            updated_example_ids = {example_data.get('id') for example_data in
                                                   setting_data['value_example_ids'] if
                                                   is_real_database_id(example_data.get('id'))}

                            # Delete examples that are no longer present
                            for example_id in existing_example_ids - updated_example_ids:
                                example = request.env['automation.contact.value.example'].sudo().browse(example_id)
                                if example.exists():
                                    example.unlink()

                            for example_data in setting_data['value_example_ids']:
                                if is_real_database_id(example_data.get('id')):
                                    example = request.env['automation.contact.value.example'].sudo().browse(
                                        example_data['id'])
                                    if example.exists():
                                        example.write({
                                            'example_text': example_data.get('example_text', ''),
                                        })
                                else:
                                    # Create new value example
                                    request.env['automation.contact.value.example'].sudo().create({
                                        'contact_value_setting_id': setting.id,
                                        'example_text': example_data.get('example_text', ''),
                                    })
                else:
                    # Create new setting
                    new_setting = request.env['automation.contact.value.setting'].sudo().create({
                        'template_id': template.id,
                        'enabled': setting_data.get('enabled', False),
                        'update_value_field': setting_data.get('update_value_field', False),
                        'use_value_override': setting_data.get('use_value_override', False),
                    })

                    # Create value examples for new setting
                    if 'value_example_ids' in setting_data:
                        for example_data in setting_data['value_example_ids']:
                            request.env['automation.contact.value.example'].sudo().create({
                                'contact_value_setting_id': new_setting.id,
                                'example_text': example_data.get('example_text', ''),
                            })

        # Update task generation settings
        if 'task_generation_setting_ids' in data and data['task_generation_setting_ids']:
            # Get existing setting IDs to check for deletions
            existing_setting_ids = {setting.id for setting in template.task_generation_setting_ids}
            updated_setting_ids = {setting_data.get('id') for setting_data in data['task_generation_setting_ids'] if
                                   is_real_database_id(setting_data.get('id'))}

            # Delete settings that are no longer present
            for setting_id in existing_setting_ids - updated_setting_ids:
                setting = request.env['automation.task.generation.setting'].sudo().browse(setting_id)
                if setting.exists():
                    setting.unlink()

            for setting_data in data['task_generation_setting_ids']:
                if is_real_database_id(setting_data.get('id')):
                    # Update existing setting
                    setting = request.env['automation.task.generation.setting'].sudo().browse(setting_data['id'])
                    if setting.exists():
                        setting.write({
                            'enabled': setting_data.get('enabled', False),
                            'auto_complete_tasks': setting_data.get('auto_complete_tasks', False),
                            'auto_reschedule_tasks': setting_data.get('auto_reschedule_tasks', False),
                        })

                        # Handle task rules deletion and updates
                        if 'task_rule_ids' in setting_data:
                            # Get existing rule IDs to check for deletions
                            existing_rule_ids = {rule.id for rule in setting.task_rule_ids}
                            updated_rule_ids = {rule_data.get('id') for rule_data in setting_data['task_rule_ids'] if
                                                is_real_database_id(rule_data.get('id'))}

                            # Delete rules that are no longer present
                            for rule_id in existing_rule_ids - updated_rule_ids:
                                rule = request.env['automation.task.rule'].sudo().browse(rule_id)
                                if rule.exists():
                                    rule.unlink()

                            for rule_data in setting_data['task_rule_ids']:
                                if is_real_database_id(rule_data.get('id')):
                                    rule = request.env['automation.task.rule'].sudo().browse(rule_data['id'])
                                    if rule.exists():
                                        rule.write({
                                            'rule_text': rule_data.get('rule_text', ''),
                                        })
                                else:
                                    # Create new task rule
                                    request.env['automation.task.rule'].sudo().create({
                                        'task_generation_setting_id': setting.id,
                                        'rule_text': rule_data.get('rule_text', ''),
                                    })
                else:
                    # Create new setting
                    new_setting = request.env['automation.task.generation.setting'].sudo().create({
                        'template_id': template.id,
                        'enabled': setting_data.get('enabled', False),
                        'auto_complete_tasks': setting_data.get('auto_complete_tasks', False),
                        'auto_reschedule_tasks': setting_data.get('auto_reschedule_tasks', False),
                    })

                    # Create task rules for new setting
                    if 'task_rule_ids' in setting_data:
                        for rule_data in setting_data['task_rule_ids']:
                            request.env['automation.task.rule'].sudo().create({
                                'task_generation_setting_id': new_setting.id,
                                'rule_text': rule_data.get('rule_text', ''),
                            })

    def _copy_template_settings(self, new_template, source_template):
        """
        Copy all settings from source template to new template.
        This creates deep copies of all related settings.
        """
        _logger.info('Copying settings from template %s to %s', source_template.id, new_template.id)

        # Copy call transcript settings
        for setting in source_template.call_transcript_setting_ids:
            new_setting = request.env['automation.call.transcript.setting'].sudo().create({
                'template_id': new_template.id,
                'enabled': setting.enabled,
                'add_user_data': setting.add_user_data,
                'update_contact_name': setting.update_contact_name,
                'improve_speaker_accuracy': setting.improve_speaker_accuracy,
                'improve_word_accuracy': setting.improve_word_accuracy,
                'assign_speaker_labels': setting.assign_speaker_labels,
                'save_full_transcript': setting.save_full_transcript,
                'save_transcript_url': setting.save_transcript_url,
            })

        # Copy call summary settings with extract details
        for setting in source_template.call_summary_setting_ids:
            new_setting = request.env['automation.call.summary.setting'].sudo().create({
                'template_id': new_template.id,
                'enabled': setting.enabled,
                'add_url_to_note': setting.add_url_to_note,
                'update_summary_field': setting.update_summary_field,
                'create_contact_note': setting.create_contact_note,
            })
            # Copy extract details
            for detail in setting.extract_detail_ids:
                request.env['automation.extract.detail'].sudo().create({
                    'call_summary_setting_id': new_setting.id,
                    'question': detail.question,
                })

        # Copy AI sales scoring settings with rules
        for setting in source_template.ai_sales_scoring_setting_ids:
            new_setting = request.env['automation.ai.sales.scoring.setting'].sudo().create({
                'template_id': new_template.id,
                'enabled': setting.enabled,
                'framework': setting.framework,
            })
            # Copy sales rules
            for rule in setting.rule_ids:
                request.env['automation.sales.rule'].sudo().create({
                    'sales_scoring_setting_id': new_setting.id,
                    'rule_text': rule.rule_text,
                })

        # Copy run contact automations settings
        for setting in source_template.run_contact_automations_setting_ids:
            request.env['automation.run.contact.automations.setting'].sudo().create({
                'template_id': new_template.id,
                'enabled': setting.enabled,
                'disable_for_tag': setting.disable_for_tag,
                'after_inactivity': setting.after_inactivity,
                'inactivity_hours': setting.inactivity_hours,
                'after_min_duration': setting.after_min_duration,
                'min_duration_seconds': setting.min_duration_seconds,
                'after_message_count': setting.after_message_count,
                'message_count': setting.message_count,
            })

        # Copy contact status settings with status options
        for setting in source_template.contact_status_setting_ids:
            new_setting = request.env['automation.contact.status.setting'].sudo().create({
                'template_id': new_template.id,
                'enabled': setting.enabled,
                'add_status_tag': setting.add_status_tag,
                'update_status_field': setting.update_status_field,
            })
            # Copy status options
            for option in setting.status_option_ids:
                request.env['automation.status.option'].sudo().create({
                    'contact_status_setting_id': new_setting.id,
                    'name': option.name,
                    'description': option.description,
                    'icon': option.icon,
                    'color': option.color,
                })

        # Copy AI contact scoring settings
        for setting in source_template.ai_contact_scoring_setting_ids:
            request.env['automation.ai.contact.scoring.setting'].sudo().create({
                'template_id': new_template.id,
                'enabled': setting.enabled,
                'use_notes_for_context': setting.use_notes_for_context,
                'update_score_field': setting.update_score_field,
                'add_score_tag': setting.add_score_tag,
                'examples_rules': setting.examples_rules,
            })

        # Copy full contact summary settings
        for setting in source_template.full_contact_summary_setting_ids:
            request.env['automation.full.contact.summary.setting'].sudo().create({
                'template_id': new_template.id,
                'enabled': setting.enabled,
                'use_call_summary_fields': setting.use_call_summary_fields,
                'update_status_summary': setting.update_status_summary,
                'create_summary_note': setting.create_summary_note,
                'delete_old_summary': setting.delete_old_summary,
            })

        # Copy contact value settings with value examples
        for setting in source_template.contact_value_setting_ids:
            new_setting = request.env['automation.contact.value.setting'].sudo().create({
                'template_id': new_template.id,
                'enabled': setting.enabled,
                'update_value_field': setting.update_value_field,
                'use_value_override': setting.use_value_override,
            })
            # Copy value examples
            for example in setting.value_example_ids:
                request.env['automation.contact.value.example'].sudo().create({
                    'contact_value_setting_id': new_setting.id,
                    'example_text': example.example_text,
                })

        # Copy task generation settings with task rules
        for setting in source_template.task_generation_setting_ids:
            new_setting = request.env['automation.task.generation.setting'].sudo().create({
                'template_id': new_template.id,
                'enabled': setting.enabled,
                'auto_complete_tasks': setting.auto_complete_tasks,
                'auto_reschedule_tasks': setting.auto_reschedule_tasks,
            })
            # Copy task rules
            for rule in setting.task_rule_ids:
                request.env['automation.task.rule'].sudo().create({
                    'task_generation_setting_id': new_setting.id,
                    'rule_text': rule.rule_text,
                })

        _logger.info('Successfully copied all settings from template %s to %s', source_template.id, new_template.id)

    def _create_location_template(self, installed_location, template_name):
        """Create a new automation template for a specific location"""
        # First, clean up any existing templates for this location
        self._cleanup_duplicate_templates_for_location(installed_location)

        default_template = request.env['automation.template'].sudo().search([('is_default', '=', True)], limit=1)

        vals = {
            'name': template_name,
            'is_default': False,
            'is_custom': True,
            # Don't set automation_group to avoid sharing between locations
            # Note: We don't set location_id here to avoid direct linking
            # The installed.location will be linked via the computed field
        }

        if default_template:
            vals['parent_template_id'] = default_template.id
            vals['business_context'] = default_template.business_context

        template = request.env['automation.template'].sudo().create(vals)

        # Copy settings from default template if it exists
        if default_template:
            self._copy_template_settings(template, default_template)

        # Assign this template to the installed location
        installed_location.automation_template_id = template.id

        _logger.info('Created new location template: %s for location: %s', template.name, installed_location.name)

        return template

    def _create_group_template(self, automation_group, template_name):
        """Create a new automation template for an automation group"""
        # First, clean up any existing templates for this automation group
        self._cleanup_duplicate_templates_for_group(automation_group)

        default_template = request.env['automation.template'].sudo().search([('is_default', '=', True)], limit=1)

        vals = {
            'name': template_name,
            'is_default': False,
            'is_custom': True,
            'automation_group': automation_group,
        }

        if default_template:
            vals['parent_template_id'] = default_template.id
            vals['business_context'] = default_template.business_context

        template = request.env['automation.template'].sudo().create(vals)

        # Copy settings from default template if it exists
        if default_template:
            self._copy_template_settings(template, default_template)

        _logger.info('Created new group template: %s for group: %s', template.name, automation_group)

        return template

    def _cleanup_duplicate_templates_for_location(self, installed_location):
        """Remove duplicate templates for a specific location, keeping only the most recent one"""
        # Find all custom templates for this location by name pattern (without location_id)
        location_name_pattern = f"{installed_location.name} - Automation Template"
        existing_templates = request.env['automation.template'].sudo().search([
            ('name', '=', location_name_pattern),
            ('is_custom', '=', True)
        ])

        if len(existing_templates) > 1:
            _logger.warning('Found %d templates for location %s. Cleaning up duplicates...', 
                          len(existing_templates), installed_location.name)

            # Keep the most recent template (highest ID) and delete the rest
            templates_to_delete = existing_templates.sorted('id', reverse=True)[1:]

            for template in templates_to_delete:
                _logger.info('Deleting duplicate template: %s (ID: %s)', template.name, template.id)
                template.unlink()

            _logger.info('Cleaned up %d duplicate templates for location %s', 
                        len(templates_to_delete), installed_location.name)

    def _cleanup_duplicate_templates_for_group(self, automation_group):
        """Remove duplicate templates for a specific automation group, keeping only the most recent one"""
        # Find all custom templates for this automation group
        existing_templates = request.env['automation.template'].sudo().search([
            ('automation_group', '=', automation_group),
            ('is_custom', '=', True)
        ])

        if len(existing_templates) > 1:
            _logger.warning('Found %d templates for automation group %s. Cleaning up duplicates...', 
                          len(existing_templates), automation_group)

            # Keep the most recent template (highest ID) and delete the rest
            templates_to_delete = existing_templates.sorted('id', reverse=True)[1:]

            for template in templates_to_delete:
                _logger.info('Deleting duplicate template: %s (ID: %s)', template.name, template.id)
                template.unlink()

            _logger.info('Cleaned up %d duplicate templates for automation group %s', 
                        len(templates_to_delete), automation_group)

    @http.route('/api/automation_template/get', type='http', auth='none', methods=['POST', 'OPTIONS'], csrf=False)
    def get_automation_template(self, **kwargs):
        """
        Fetch the automation template for a given location or automation group.
        Expects JSON body with 'location_id' or 'automation_group'.
        """
        if request.httprequest.method == 'OPTIONS':
            return Response(status=200, headers=get_cors_headers(request))

        # Get JSON data from request
        data = getattr(request, 'jsonrequest', {}) or {}
        
        # Try parsing the raw request body if no data from jsonrequest
        if not data:
            try:
                import json
                raw_body = request.httprequest.get_data(as_text=True)
                if raw_body:
                    data = json.loads(raw_body)
            except Exception as e:
                _logger.error('Error parsing request body: %s', str(e))
                return Response(
                    json.dumps({'error': 'Invalid JSON in request body'}),
                    content_type='application/json',
                    status=400,
                    headers=get_cors_headers(request)
                )

        location_id = data.get('location_id')
        automation_group = data.get('automation_group')

        _logger.info('API CALL: /api/automation_template/get for location_id: %s, automation_group: %s', 
                    location_id, automation_group)

        if not location_id and not automation_group:
            _logger.error('Missing required parameter: location_id or automation_group')
            return Response(
                json.dumps({'error': 'location_id or automation_group is required'}),
                content_type='application/json',
                status=400,
                headers=get_cors_headers(request)
            )

        template = False
        if automation_group:
            # First try to find template by automation_group
            template = request.env['automation.template'].sudo().search([
                ('automation_group', '=', automation_group)
            ], limit=1)
            if template:
                # _logger.info('Found template by automation_group: %s (ID: %s)', template.name, template.id)  # Reduced logging for production

        if not template and location_id:
            # Find the installed.location record first
            installed_location = request.env['installed.location'].sudo().search([
                ('location_id', '=', location_id)
            ], limit=1)

            if installed_location:
                _logger.info('Found installed.location: %s (ID: %s)', installed_location.name, installed_location.id)

                # Now search for template by the installed.location record
                # Check if the installed location has an automation template directly assigned
                if installed_location.automation_template_id:
                    template = installed_location.automation_template_id
                    # _logger.info('Found directly assigned template: %s (ID: %s)', template.name, template.id)  # Reduced logging for production
                else:
                    # If no template is directly assigned, look for a template with matching automation_group
                    if installed_location.automation_group:
                        template = request.env['automation.template'].sudo().search([
                            ('automation_group', '=', installed_location.automation_group)
                        ], limit=1)
                        if template:
                            # _logger.info('Found template by automation_group: %s (ID: %s)', template.name, template.id)  # Reduced logging for production
                        else:
                            _logger.warning('No template found for automation_group: %s', installed_location.automation_group)
                    else:
                        _logger.warning('No automation_group set for location: %s', installed_location.name)

                if template:
                    _logger.info('Found template: %s (ID: %s)', template.name, template.id)
                else:
                    _logger.warning('No template found for location_id: %s', location_id)
            else:
                _logger.warning('No installed.location found for location_id: %s', location_id)

        if not template:
            # Optionally, return the default template if exists
            _logger.info('No specific template found, checking for default template')
            default_template = request.env['automation.template'].sudo().search([('is_default', '=', True)], limit=1)
            if default_template:
                result = AutomationTemplateController.serialize_template(default_template)
                _logger.info('Returning default automation template: %s', default_template.name)
                return Response(
                    json.dumps(result),
                    content_type='application/json',
                    status=200,
                    headers=get_cors_headers(request)
                )
            else:
                _logger.warning('No default template found, returning empty result')
                return Response(
                    json.dumps({}),
                    content_type='application/json',
                    status=200,
                    headers=get_cors_headers(request)
                )

        result = AutomationTemplateController.serialize_template(template)
        _logger.info('Returning automation template: %s', template.name)
        return Response(
            json.dumps(result),
            content_type='application/json',
            status=200,
            headers=get_cors_headers(request)
        )

    @http.route('/api/automation_template/get_by_id', type='json', auth='user', methods=['POST'], csrf=False)
    def get_automation_template_by_id(self, **kwargs):
        params = getattr(request, 'jsonrequest', {}) or {}
        # If JSON-RPC, use params['params'], else use params directly
        if 'params' in params:
            data = params['params']
        else:
            data = params
        _logger.info('API CALL: /api/automation_template/get_by_id for template_id: %s', data.get('id'))
        template_id = data.get('id')
        if not template_id:
            _logger.error('Missing required parameter: id')
            return {'error': 'id is required'}
        template = request.env['automation.template'].sudo().browse(template_id)
        if not template.exists():
            _logger.error('Template not found for id: %s', template_id)
            return {'error': 'template not found'}
        result = AutomationTemplateController.serialize_template(template)
        _logger.info('Returning automation template by id: %s', template.name)
        return result

    @http.route('/api/automation_template/cleanup_duplicates', type='json', auth='user', methods=['POST'], csrf=False)
    def cleanup_duplicate_templates(self, **kwargs):
        """Clean up duplicate templates for all locations and automation groups"""
        try:
            # Clean up location-based duplicates
            installed_locations = request.env['installed.location'].sudo().search([])
            for location in installed_locations:
                self._cleanup_duplicate_templates_for_location(location)

            # Clean up automation group duplicates
            automation_groups = request.env['automation.template'].sudo().search([
                ('automation_group', '!=', False)
            ]).mapped('automation_group')

            for group in set(automation_groups):
                self._cleanup_duplicate_templates_for_group(group)

            return {'success': True, 'message': 'Duplicate templates cleaned up successfully'}
        except Exception as e:
            _logger.error('Error cleaning up duplicate templates: %s', str(e))
            return {'error': f'Error cleaning up duplicates: {str(e)}'}

    @http.route('/api/automation_template/list', type='http', auth='none', methods=['POST', 'OPTIONS'], csrf=False)
    def list_automation_templates(self, **kwargs):
        """
        List all automation templates (id and name only).
        """
        if request.httprequest.method == 'OPTIONS':
            return Response(status=200, headers=get_cors_headers(request))

        data = getattr(request, 'jsonrequest', {}) or {}
        app_id = data.get('appId')

        _logger.info('API CALL: /api/automation_template/list')

        # Get all templates
        templates = request.env['automation.template'].sudo().search([])

        # If app_id is provided, filter templates by automation groups that have locations with this app
        if app_id:
            # Get automation groups that have locations with this app
            app = request.env['cyclsales.application'].sudo().search([
                ('app_id', '=', app_id),
                ('is_active', '=', True)
            ], limit=1)

            if app:
                # Get locations that have this app installed
                locations = request.env['installed.location'].sudo().search([
                    ('application_ids', 'in', app.id),
                    ('is_installed', '=', True)
                ])

                # Get automation groups from these locations
                automation_groups = locations.mapped('automation_group')

                # Filter templates by these automation groups
                templates = templates.filtered(lambda t:
                                               t.automation_group in automation_groups or
                                               t.location_id in locations or
                                               t.is_default
                                               )

        data = [{
            'id': t.id,
            'name': t.name,
            'automation_group': t.automation_group,
            'is_default': t.is_default,
            'is_custom': t.is_custom,
            'parent_template_id': t.parent_template_id.id if t.parent_template_id else None
        } for t in templates]
        _logger.info('Returning %d templates', len(data))
        return Response(
            json.dumps({'templates': data}),
            content_type='application/json',
            status=200,
            headers=get_cors_headers(request)
        )

    @http.route('/api/automation_template/fix_location_templates', type='json', auth='user', methods=['POST'],
                csrf=False)
    def fix_location_templates(self, **kwargs):
        """
        Fix template sharing issues by ensuring each location has its own unique template.
        This is a utility endpoint to resolve the issue where multiple locations share the same template.
        """
        data = getattr(request, 'jsonrequest', {}) or {}
        app_id = data.get('appId')

        _logger.info('API CALL: /api/automation_template/fix_location_templates')

        if not app_id:
            return Response(
                json.dumps({'error': 'appId is required'}))

        # Get all installed locations for this app
        app = request.env['cyclsales.application'].sudo().search([
            ('app_id', '=', app_id),
            ('is_active', '=', True)
        ], limit=1)

        if not app:
            return Response(json.dumps({'error': f'No active application found for appId: {app_id}'}))

        locations = request.env['installed.location'].sudo().search([
            ('application_ids', 'in', app.id),
            ('is_installed', '=', True)
        ])

        fixed_locations = []
        issues_found = []

        for location in locations:
            _logger.info('Processing location: %s (%s)', location.name, location.location_id)

            # Check if this location has a template assigned
            if location.automation_template_id:
                template = location.automation_template_id
                _logger.info('Location %s has template: %s (ID: %s)', location.name, template.name, template.id)

                # Check if this template is shared with other locations
                other_locations_with_same_template = request.env['installed.location'].sudo().search([
                    ('automation_template_id', '=', template.id),
                    ('id', '!=', location.id)
                ])

                if other_locations_with_same_template:
                    _logger.warning('Template %s is shared between %s and %d other locations', 
                                  template.name, location.name, len(other_locations_with_same_template))
                    issues_found.append({
                        'location_name': location.name,
                        'location_id': location.location_id,
                        'template_name': template.name,
                        'template_id': template.id,
                        'shared_with': [loc.name for loc in other_locations_with_same_template]
                    })

                    # Create a new unique template for this location
                    new_template_name = f"{location.name} - Automation Template"

                    # Check if a unique template already exists for this location
                    existing_unique_template = request.env['automation.template'].sudo().search([
                        ('name', '=', new_template_name),
                        ('is_custom', '=', True)
                    ], limit=1)

                    if existing_unique_template:
                        # Use the existing unique template
                        location.automation_template_id = existing_unique_template.id
                        _logger.info('Assigned existing unique template: %s to location %s', 
                                   existing_unique_template.name, location.name)
                    else:
                        # Create a new unique template
                        new_template_vals = {
                            'name': new_template_name,
                            'is_default': False,
                            'is_custom': True,
                            'business_context': template.business_context,
                        }

                        if template.parent_template_id:
                            new_template_vals['parent_template_id'] = template.parent_template_id.id

                        new_template = request.env['automation.template'].sudo().create(new_template_vals)

                        # Copy settings from the current template
                        self._copy_template_settings(new_template, template)

                        # Assign the new template to this location
                        location.automation_template_id = new_template.id

                        _logger.info('Created new unique template: %s for location %s', new_template.name, location.name)

                    fixed_locations.append({
                        'location_name': location.name,
                        'location_id': location.location_id,
                        'new_template_name': new_template_name,
                        'action': 'created_new_template' if not existing_unique_template else 'assigned_existing_template'
                    })
                else:
                    _logger.info('Location %s has unique template: %s', location.name, template.name)
            else:
                _logger.warning('Location %s has no template assigned', location.name)

        return {
            'success': True,
            'issues_found': issues_found,
            'fixed_locations': fixed_locations,
            'total_locations_processed': len(locations),
            'message': f'Processed {len(locations)} locations. Found {len(issues_found)} template sharing issues and fixed {len(fixed_locations)} locations.'
        }
