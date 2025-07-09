from odoo import models, fields, api
import requests
import logging
import json
from datetime import datetime

_logger = logging.getLogger(__name__)

class GhlContactOpportunityCustomField(models.Model):
    _name = 'ghl.contact.opportunity.custom.field'
    _description = 'GHL Contact Opportunity Custom Field'

    opportunity_id = fields.Many2one('ghl.contact.opportunity', string='Opportunity', ondelete='cascade')
    custom_field_id = fields.Char(string='Custom Field ID')
    field_value = fields.Char(string='Field Value')

class GhlContactOpportunity(models.Model):
    _name = 'ghl.contact.opportunity'
    _description = 'GHL Contact Opportunity'
    _order = 'created_at desc'

    external_id = fields.Char('External ID', required=True, index=True)
    name = fields.Char('Name', required=True)
    monetary_value = fields.Float('Monetary Value')
    pipeline_id = fields.Char('Pipeline ID')
    pipeline_stage_id = fields.Char('Pipeline Stage ID')
    assigned_to = fields.Many2one('ghl.location.user', string='Assigned To', ondelete='set null')
    assigned_to_external = fields.Char('Assigned To (GHL External ID)')
    status = fields.Selection([
        ('open', 'Open'),
        ('won', 'Won'),
        ('lost', 'Lost'),
        ('abandoned', 'Abandoned'),
        ('deleted', 'Deleted'),
    ], string='Status', default='open')
    source = fields.Char('Source')
    last_status_change_at = fields.Datetime('Last Status Change At')
    last_stage_change_at = fields.Datetime('Last Stage Change At')
    last_action_date = fields.Datetime('Last Action Date')
    index_version = fields.Integer('Index Version')
    created_at = fields.Datetime('Created At')
    updated_at = fields.Datetime('Updated At')
    contact_id = fields.Many2one('ghl.location.contact', string='Contact', ondelete='set null')
    contact_external_id = fields.Char('Contact External ID')
    location_id = fields.Many2one('installed.location', string='Location', ondelete='set null')
    location_external_id = fields.Char('Location External ID')

    # Sub-models/fields
    notes = fields.Text('Notes')  # Store as JSON string or comma-separated
    tasks = fields.Text('Tasks')  # Store as JSON string or comma-separated
    calendar_events = fields.Text('Calendar Events')  # Store as JSON string or comma-separated
    custom_field_ids = fields.One2many('ghl.contact.opportunity.custom.field', 'opportunity_id', string='Custom Fields')
    followers = fields.Text('Followers')  # Store as JSON string or comma-separated

    _sql_constraints = [
        ('external_id_uniq', 'unique(external_id)', 'Opportunity external_id must be unique!'),
    ]

    def _get_location_token(self, app_access_token, location_id, company_id):
        """
        Get location-specific access token using agency token
        """
        try:
            token_url = "https://services.leadconnectorhq.com/oauth/locationToken"
            headers = {
                'Accept': 'application/json',
                'Content-Type': 'application/x-www-form-urlencoded',
                'Authorization': f'Bearer {app_access_token}',
                'Version': '2021-07-28',
            }
            data = {
                'companyId': company_id,
                'locationId': location_id,
            }
            
            token_resp = requests.post(token_url, headers=headers, data=data)
            if token_resp.status_code not in (200, 201):
                return {
                    'success': False,
                    'message': f"Failed to get location token: {token_resp.text}"
                }
                
            token_json = token_resp.json()
            location_token = token_json.get('access_token')
            
            if not location_token:
                return {
                    'success': False,
                    'message': 'No access_token in location token response'
                }
            
            return {
                'success': True,
                'access_token': location_token
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'Error getting location token: {str(e)}'
            }

    def fetch_opportunities_from_ghl_api(self, location_id, access_token, limit=100):
        """
        Fetch opportunities from the GHL API for a given location_id.
        Args:
            location_id (str): GHL location ID
            access_token (str): GHL OAuth access token
            limit (int): Number of records to fetch (default 500)
        Returns:
            dict: API response or error info
        """
        url = f"https://services.leadconnectorhq.com/opportunities/search?location_id={location_id}&limit={limit}"
        headers = {
            'Accept': 'application/json',
            'Authorization': f'Bearer {access_token}',
            'Version': '2021-07-28',
        }
        try:
            _logger.info(f"Fetching GHL opportunities from {url}")
            response = requests.get(url, headers=headers, timeout=30)
            _logger.info(f"GHL opportunities API response: {response.status_code} {response.text[:500]}")
            if response.status_code == 200:
                return {
                    'success': True,
                    'opportunities': response.json().get('opportunities', [])
                }
            else:
                return {
                    'success': False,
                    'status_code': response.status_code,
                    'error': response.text
                }
        except Exception as e:
            _logger.error(f"Error fetching opportunities from GHL API: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    @api.model
    def sync_opportunities_for_location(self, app_access_token, location_id, company_id=None):
        """
        Sync opportunities for a specific location using two-step token process
        
        Args:
            app_access_token (str): Agency-level access token
            location_id (str): GHL location ID
            company_id (str): Company ID
            
        Returns:
            dict: Result with success status and sync details
        """
        try:
            _logger.info(f"Starting opportunity sync for location {location_id}")
            
            # Validate company_id is provided
            if not company_id:
                return {
                    'success': False,
                    'message': 'company_id is required for opportunity sync',
                    'created': 0,
                    'updated': 0,
                    'errors': ['company_id is required']
                }
            
            _logger.info(f"Using company_id: {company_id}")
            
            # Step 1: Get location token using agency token
            location_token_result = self._get_location_token(app_access_token, location_id, company_id)
            
            if not location_token_result['success']:
                return {
                    'success': False,
                    'message': f"Failed to get location token: {location_token_result['message']}",
                    'created': 0,
                    'updated': 0,
                    'errors': []
                }
            
            location_token = location_token_result['access_token']
            
            # Step 2: Fetch opportunities using location token
            opportunities_result = self.fetch_opportunities_from_ghl_api(location_id, location_token, 100)
            
            if not opportunities_result['success']:
                return {
                    'success': False,
                    'message': f"Failed to fetch opportunities: {opportunities_result.get('error', 'Unknown error')}",
                    'created': 0,
                    'updated': 0,
                    'errors': []
                }
            
            # Step 3: Process and save opportunities
            return self._process_opportunities(opportunities_result['opportunities'], location_id, company_id)
            
        except Exception as e:
            _logger.error(f"Error in sync_opportunities_for_location: {str(e)}")
            return {
                'success': False,
                'message': f'Unexpected error: {str(e)}',
                'created': 0,
                'updated': 0,
                'errors': []
            }

    def _process_opportunities(self, opportunities_data, location_id, company_id):
        """
        Process and save opportunities data to Odoo
        """
        try:
            created_count = 0
            updated_count = 0
            errors = []
            
            # Find the installed.location record
            installed_location = self.env['installed.location'].search([
                ('location_id', '=', location_id)
            ], limit=1)
            
            if not installed_location:
                return {
                    'success': False,
                    'message': f'Location {location_id} not found in Odoo',
                    'created': 0,
                    'updated': 0,
                    'errors': [f'Location {location_id} not found']
                }
            
            for opportunity_data in opportunities_data:
                try:
                    ghl_id = opportunity_data.get('id')
                    if not ghl_id:
                        continue
                    
                    # Check if opportunity already exists
                    existing_opportunity = self.search([
                        ('external_id', '=', ghl_id)
                    ], limit=1)
                    
                    # Prepare opportunity values
                    opportunity_values = {
                        'external_id': ghl_id,
                        'name': opportunity_data.get('name', ''),
                        'monetary_value': opportunity_data.get('monetaryValue', 0.0),
                        'pipeline_id': opportunity_data.get('pipelineId', ''),
                        'pipeline_stage_id': opportunity_data.get('pipelineStageId', ''),
                        'assigned_to_external': opportunity_data.get('assignedTo', ''),
                        'status': opportunity_data.get('status', 'open'),
                        'source': opportunity_data.get('source', ''),
                        'contact_external_id': opportunity_data.get('contactId', ''),
                        'location_external_id': location_id,
                        'location_id': installed_location.id,
                        'index_version': opportunity_data.get('indexVersion', 0),
                        'notes': json.dumps(opportunity_data.get('notes', [])) if opportunity_data.get('notes') else '',
                        'tasks': json.dumps(opportunity_data.get('tasks', [])) if opportunity_data.get('tasks') else '',
                        'calendar_events': json.dumps(opportunity_data.get('calendarEvents', [])) if opportunity_data.get('calendarEvents') else '',
                        'followers': json.dumps(opportunity_data.get('followers', [])) if opportunity_data.get('followers') else '',
                    }
                    
                    # Parse datetime fields
                    date_field_mapping = {
                        'lastStatusChangeAt': 'last_status_change_at',
                        'lastStageChangeAt': 'last_stage_change_at', 
                        'lastActionDate': 'last_action_date',
                        'createdAt': 'created_at',
                        'updatedAt': 'updated_at'
                    }
                    
                    for api_field, model_field in date_field_mapping.items():
                        date_value = opportunity_data.get(api_field)
                        if date_value:
                            try:
                                # Convert to naive datetime for Odoo
                                parsed_date = datetime.fromisoformat(date_value.replace('Z', '+00:00'))
                                if parsed_date.tzinfo:
                                    parsed_date = parsed_date.replace(tzinfo=None)
                                opportunity_values[model_field] = parsed_date
                            except (ValueError, TypeError) as e:
                                _logger.warning(f"Could not parse date '{date_value}' for field {api_field}: {e}")
                    
                    # Link to contact if exists
                    contact_external_id = opportunity_data.get('contactId')
                    if contact_external_id:
                        contact = self.env['ghl.location.contact'].search([
                            ('external_id', '=', contact_external_id),
                            ('location_id.location_id', '=', location_id)
                        ], limit=1)
                        if contact:
                            opportunity_values['contact_id'] = contact.id
                    
                    # Link to assigned user if exists
                    assigned_to_external = opportunity_data.get('assignedTo')
                    if assigned_to_external:
                        assigned_user = self.env['ghl.location.user'].search([
                            ('external_id', '=', assigned_to_external),
                            ('location_id.location_id', '=', location_id)
                        ], limit=1)
                        if assigned_user:
                            opportunity_values['assigned_to'] = assigned_user.id
                    
                    if existing_opportunity:
                        # Update existing opportunity
                        existing_opportunity.write(opportunity_values)
                        updated_count += 1
                        _logger.info(f"Updated opportunity {ghl_id}")
                    else:
                        # Create new opportunity
                        self.create(opportunity_values)
                        created_count += 1
                        _logger.info(f"Created opportunity {ghl_id}")
                        
                except Exception as e:
                    error_msg = f"Error processing opportunity {opportunity_data.get('id', 'unknown')}: {str(e)}"
                    errors.append(error_msg)
                    _logger.error(error_msg)
            
            _logger.info(f"Opportunity sync completed for location {location_id}: {created_count} created, {updated_count} updated")
            
            return {
                'success': True,
                'message': f'Successfully synced opportunities: {created_count} created, {updated_count} updated',
                'created': created_count,
                'updated': updated_count,
                'errors': errors
            }
            
        except Exception as e:
            _logger.error(f"Error processing opportunities: {str(e)}")
            return {
                'success': False,
                'message': f'Error processing opportunities: {str(e)}',
                'created': 0,
                'updated': 0,
                'errors': [str(e)]
            } 