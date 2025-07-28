# -*- coding: utf-8 -*-
from odoo import models, fields, api

class AutomationTemplate(models.Model):
    _name = 'automation.template'
    _description = 'Automation Template'
    _order = 'name'

    name = fields.Char(required=True)
    location_id = fields.Many2one('installed.location', string='Location', ondelete='cascade', index=True)
    parent_template_id = fields.Many2one('automation.template', string='Parent Template')
    is_default = fields.Boolean(default=False)
    business_context = fields.Text()
    # Settings relations
    call_transcript_setting_ids = fields.One2many('automation.call.transcript.setting', 'template_id', string='Call Transcript Settings')
    call_summary_setting_ids = fields.One2many('automation.call.summary.setting', 'template_id', string='Call Summary Settings')
    ai_sales_scoring_setting_ids = fields.One2many('automation.ai.sales.scoring.setting', 'template_id', string='AI Sales Scoring Settings')
    run_contact_automations_setting_ids = fields.One2many('automation.run.contact.automations.setting', 'template_id', string='Run Contact Automations Settings')
    contact_status_setting_ids = fields.One2many('automation.contact.status.setting', 'template_id', string='Contact Status Settings')
    ai_contact_scoring_setting_ids = fields.One2many('automation.ai.contact.scoring.setting', 'template_id', string='AI Contact Scoring Settings')
    full_contact_summary_setting_ids = fields.One2many('automation.full.contact.summary.setting', 'template_id', string='Full Contact Summary Settings')
    contact_value_setting_ids = fields.One2many('automation.contact.value.setting', 'template_id', string='Contact Value Settings')
    task_generation_setting_ids = fields.One2many('automation.task.generation.setting', 'template_id', string='Task Generation Settings')

class AutomationCallTranscriptSetting(models.Model):
    _name = 'automation.call.transcript.setting'
    _description = 'Call Transcript Setting'
    template_id = fields.Many2one('automation.template', ondelete='cascade')
    enabled = fields.Boolean(default=True)
    add_user_data = fields.Boolean(default=True)
    update_contact_name = fields.Boolean(default=True)
    improve_speaker_accuracy = fields.Boolean(default=True)
    improve_word_accuracy = fields.Boolean(default=True)
    assign_speaker_labels = fields.Boolean(default=True)
    save_full_transcript = fields.Boolean(default=True)
    save_transcript_url = fields.Boolean(default=True)

class AutomationCallSummarySetting(models.Model):
    _name = 'automation.call.summary.setting'
    _description = 'Call Summary Setting'
    template_id = fields.Many2one('automation.template', ondelete='cascade')
    enabled = fields.Boolean(default=True)
    add_url_to_note = fields.Boolean(default=True)
    update_summary_field = fields.Boolean(default=True)
    create_contact_note = fields.Boolean(default=True)
    extract_detail_ids = fields.One2many('automation.extract.detail', 'call_summary_setting_id', string='Extract Details')

class AutomationExtractDetail(models.Model):
    _name = 'automation.extract.detail'
    _description = 'Automation Extract Detail'
    call_summary_setting_id = fields.Many2one('automation.call.summary.setting', ondelete='cascade')
    question = fields.Char()

class AutomationAISalesScoringSetting(models.Model):
    _name = 'automation.ai.sales.scoring.setting'
    _description = 'AI Sales Scoring Setting'
    template_id = fields.Many2one('automation.template', ondelete='cascade')
    enabled = fields.Boolean(default=True)
    framework = fields.Char()
    rule_ids = fields.One2many('automation.sales.rule', 'sales_scoring_setting_id', string='Rules')

class AutomationSalesRule(models.Model):
    _name = 'automation.sales.rule'
    _description = 'Automation Sales Rule'
    sales_scoring_setting_id = fields.Many2one('automation.ai.sales.scoring.setting', ondelete='cascade')
    rule_text = fields.Char()

class AutomationRunContactAutomationsSetting(models.Model):
    _name = 'automation.run.contact.automations.setting'
    _description = 'Run Contact Automations Setting'
    template_id = fields.Many2one('automation.template', ondelete='cascade')
    enabled = fields.Boolean(default=True)
    disable_for_tag = fields.Boolean(default=True)
    after_inactivity = fields.Boolean(default=True)
    inactivity_hours = fields.Integer(default=10)
    after_min_duration = fields.Boolean(default=True)
    min_duration_seconds = fields.Integer(default=20)
    after_message_count = fields.Boolean(default=True)
    message_count = fields.Integer(default=2)

class AutomationContactStatusSetting(models.Model):
    _name = 'automation.contact.status.setting'
    _description = 'Contact Status Setting'
    template_id = fields.Many2one('automation.template', ondelete='cascade')
    enabled = fields.Boolean(default=True)
    add_status_tag = fields.Boolean(default=True)
    update_status_field = fields.Boolean(default=True)
    status_option_ids = fields.One2many('automation.status.option', 'contact_status_setting_id', string='Status Options')

class AutomationStatusOption(models.Model):
    _name = 'automation.status.option'
    _description = 'Automation Status Option'
    contact_status_setting_id = fields.Many2one('automation.contact.status.setting', ondelete='cascade')
    name = fields.Char()
    description = fields.Text()
    icon = fields.Char()
    color = fields.Char()

class AutomationAIContactScoringSetting(models.Model):
    _name = 'automation.ai.contact.scoring.setting'
    _description = 'AI Contact Scoring Setting'
    template_id = fields.Many2one('automation.template', ondelete='cascade')
    enabled = fields.Boolean(default=True)
    use_notes_for_context = fields.Boolean(default=True)
    update_score_field = fields.Boolean(default=True)
    add_score_tag = fields.Boolean(default=False)
    examples_rules = fields.Text()

class AutomationFullContactSummarySetting(models.Model):
    _name = 'automation.full.contact.summary.setting'
    _description = 'Full Contact Summary Setting'
    template_id = fields.Many2one('automation.template', ondelete='cascade')
    enabled = fields.Boolean(default=True)
    use_call_summary_fields = fields.Boolean(default=True)
    update_status_summary = fields.Boolean(default=True)
    create_summary_note = fields.Boolean(default=True)
    delete_old_summary = fields.Boolean(default=True)

class AutomationContactValueSetting(models.Model):
    _name = 'automation.contact.value.setting'
    _description = 'Contact Value Setting'
    template_id = fields.Many2one('automation.template', ondelete='cascade')
    enabled = fields.Boolean(default=True)
    update_value_field = fields.Boolean(default=True)
    use_value_override = fields.Boolean(default=True)
    value_example_ids = fields.One2many('automation.contact.value.example', 'contact_value_setting_id', string='Value Examples')

class AutomationContactValueExample(models.Model):
    _name = 'automation.contact.value.example'
    _description = 'Automation Contact Value Example'
    contact_value_setting_id = fields.Many2one('automation.contact.value.setting', ondelete='cascade')
    example_text = fields.Text()

class AutomationTaskGenerationSetting(models.Model):
    _name = 'automation.task.generation.setting'
    _description = 'Task Generation Setting'
    template_id = fields.Many2one('automation.template', ondelete='cascade')
    enabled = fields.Boolean(default=True)
    auto_complete_tasks = fields.Boolean(default=True)
    auto_reschedule_tasks = fields.Boolean(default=True)
    task_rule_ids = fields.One2many('automation.task.rule', 'task_generation_setting_id', string='Task Rules')

class AutomationTaskRule(models.Model):
    _name = 'automation.task.rule'
    _description = 'Automation Task Rule'
    task_generation_setting_id = fields.Many2one('automation.task.generation.setting', ondelete='cascade')
    rule_text = fields.Text() 