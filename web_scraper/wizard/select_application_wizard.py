# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class SelectApplicationWizard(models.TransientModel):
    _name = 'select.application.wizard'
    _description = 'Select Application for Transcript Fetch'

    application_id = fields.Many2one(
        'cyclsales.application',
        string='Application',
        required=True,
        domain=[('is_active', '=', True)],
        help='Select the application to use for fetching the transcript'
    )
    
    message_id = fields.Many2one(
        'ghl.contact.message',
        string='Message',
        required=True,
        help='The message for which to fetch the transcript'
    )
    
    available_applications = fields.Many2many(
        'cyclsales.application',
        string='Available Applications',
        compute='_compute_available_applications',
        help='Applications that are available for use'
    )

    @api.depends()
    def _compute_available_applications(self):
        """Compute available applications based on active status and token validity"""
        for record in self:
            applications = self.env['cyclsales.application'].search([
                ('is_active', '=', True)
            ])
            record.available_applications = applications

    @api.onchange('application_id')
    def _onchange_application_id(self):
        """Show warnings when application is selected"""
        if self.application_id:
            status = self.application_id.token_status
            if status == 'expired':
                return {
                    'warning': {
                        'title': _('Token Expired'),
                        'message': _('The selected application has an expired token. It will be automatically refreshed if possible.')
                    }
                }
            elif status == 'missing':
                return {
                    'warning': {
                        'title': _('No Token'),
                        'message': _('The selected application has no access token. Please configure it first.')
                    }
                }

    def action_fetch_transcript(self):
        """Fetch transcript using the selected application"""
        self.ensure_one()
        
        if not self.application_id:
            raise ValidationError(_('Please select an application first.'))
        
        if not self.message_id:
            raise ValidationError(_('No message specified.'))
        
        # Check token status
        if self.application_id.token_status == 'expired':
            if not self.application_id.refresh_token:
                raise ValidationError(_('The selected application has an expired token and no refresh token available. Please refresh the token manually.'))
            
            # Try to refresh the token
            try:
                self.application_id.action_refresh_token()
                # Re-read the application to get updated status
                self.application_id = self.application_id.browse(self.application_id.id)
                if self.application_id.token_status == 'expired':
                    raise ValidationError(_('Failed to refresh the token. Please try refreshing it manually.'))
            except Exception as e:
                raise ValidationError(_('Failed to refresh the token: %s') % str(e))
        
        elif self.application_id.token_status == 'missing':
            raise ValidationError(_('The selected application has no access token. Please configure it first.'))
        
        # Fetch transcript using the selected application
        transcript_model = self.env['ghl.contact.message.transcript']
        result = transcript_model.fetch_transcript_for_message(
            self.message_id.id, 
            app_id=self.application_id.app_id
        )
        
        if result.get('success'):
            # Update call duration from transcript data
            self.message_id.update_call_duration_from_transcript()
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Success'),
                    'message': result.get('message', _('Transcript fetched successfully')),
                    'type': 'success',
                }
            }
        else:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Error'),
                    'message': result.get('error', _('Unknown error occurred')),
                    'type': 'danger',
                }
            } 