from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import logging
import requests
import json
from datetime import datetime
import time

_logger = logging.getLogger(__name__)

class GhlContactTask(models.Model):
    _name = 'ghl.contact.task'
    _description = 'GHL Contact Task'
    _order = 'due_date desc, create_date desc'

    # Basic fields
    external_id = fields.Char('External ID', required=True, index=True)
    title = fields.Char('Title', required=True)
    body = fields.Text('Body')
    due_date = fields.Datetime('Due Date')
    completed = fields.Boolean('Completed', default=False)
    
    # Relationships
    contact_id = fields.Many2one('ghl.location.contact', string='Contact', required=True, ondelete='cascade')
    
    # Assigned user (could be a string from GHL or related to ghl.location.user)
    assigned_to = fields.Char('Assigned To (GHL ID)')
    assigned_user_id = fields.Many2one('ghl.location.user', string='Assigned User', 
                                     domain="[('location_id', '=', contact_id.location_id)]")
    
    # Computed fields
    name = fields.Char('Name', compute='_compute_name', store=True)
    is_overdue = fields.Boolean('Is Overdue', compute='_compute_is_overdue', store=True)
    days_until_due = fields.Integer('Days Until Due', compute='_compute_days_until_due')
    
    # Relationships
    location_id = fields.Many2one('installed.location', string='Location', 
                                 domain="[('location_id', '=', contact_id.location_id)]", 
                                 compute='_compute_location_id', store=True)
    
    # Metadata
    create_date = fields.Datetime('Created Date', readonly=True)
    write_date = fields.Datetime('Last Updated', readonly=True)
    
    _sql_constraints = [
        ('unique_external_id_per_contact', 'unique(external_id, contact_id)', 
         'External ID must be unique per contact!')
    ]

    @api.depends('title', 'contact_id.name')
    def _compute_name(self):
        for record in self:
            if record.title and record.contact_id.name:
                record.name = f"{record.title} - {record.contact_id.name}"
            elif record.title:
                record.name = record.title
            else:
                record.name = f"Task - {record.contact_id.name or 'Unknown Contact'}"

    @api.depends('due_date', 'completed')
    def _compute_is_overdue(self):
        from datetime import datetime
        now = datetime.now()
        for record in self:
            if record.completed or not record.due_date:
                record.is_overdue = False
            else:
                record.is_overdue = record.due_date < now

    @api.depends('due_date')
    def _compute_days_until_due(self):
        from datetime import datetime
        now = datetime.now()
        for record in self:
            if not record.due_date:
                record.days_until_due = 0
            else:
                delta = record.due_date - now
                record.days_until_due = delta.days

    @api.depends('contact_id.location_id')
    def _compute_location_id(self):
        for record in self:
            if record.contact_id and record.contact_id.location_id:
                # Find the installed.location record with matching location_id
                installed_location = self.env['installed.location'].search([
                    ('location_id', '=', record.contact_id.location_id.id)
                ], limit=1)
                record.location_id = installed_location.id if installed_location else False
            else:
                record.location_id = False

    @api.model_create_multi
    def create(self, vals):
        def assign_user(val):
            try:
                # Auto-assign user if assigned_to matches a ghl.location.user
                if val.get('assigned_to') and val.get('contact_id'):
                    _logger.info(f"Creating task with assigned_to: {val.get('assigned_to')}, contact_id: {val.get('contact_id')}")
                    contact = self.env['ghl.location.contact'].browse(val['contact_id'])
                    _logger.info(f"Contact found: {contact.exists()}, location_id: {contact.location_id if contact.exists() else 'N/A'}")
                    if contact and contact.location_id:
                        installed_location = self.env['installed.location'].search([
                            ('location_id', '=', contact.location_id.id)
                        ], limit=1)
                        if installed_location:
                            user = self.env['ghl.location.user'].search([
                                ('external_id', '=', val['assigned_to']),
                                ('location_id', '=', contact.location_id.id)
                            ], limit=1)
                            _logger.info(f"User found: {user.exists() if user else False}")
                            if user:
                                val['assigned_user_id'] = user.id
            except Exception as e:
                _logger.error(f"Error in create method: {str(e)}")
                # Continue with creation even if auto-assignment fails
        # If vals is a list, handle each dict in the list
        if isinstance(vals, list):
            for val in vals:
                assign_user(val)
            return super(GhlContactTask, self).create(vals)
        else:
            assign_user(vals)
            return super(GhlContactTask, self).create(vals)

    def write(self, vals):
        # Auto-assign user if assigned_to is being updated
        if vals.get('assigned_to'):
            # Get location_id from contact if not directly provided
            location_id = vals.get('location_id')
            if not location_id and vals.get('contact_id'):
                contact = self.env['ghl.location.contact'].browse(vals['contact_id'])
                location_id = contact.location_id if contact else False
            elif not location_id:
                # Use existing contact's location_id
                for record in self:
                    if record.contact_id and record.contact_id.location_id:
                        location_id = record.contact_id.location_id
                        break
            
            if location_id:
                user = self.env['ghl.location.user'].search([
                    ('external_id', '=', vals['assigned_to']),
                    ('location_id', '=', location_id.id)
                ], limit=1)
                if user:
                    vals['assigned_user_id'] = user.id
        return super().write(vals)

    def toggle_completed(self):
        """Toggle the completed status of the task"""
        for record in self:
            record.completed = not record.completed

    def mark_as_completed(self):
        """Mark the task as completed"""
        self.write({'completed': True})

    def mark_as_incomplete(self):
        """Mark the task as incomplete"""
        self.write({'completed': False})

    @api.constrains('due_date')
    def _check_due_date(self):
        for record in self:
            if record.due_date and record.due_date < fields.Datetime.now():
                # Allow past due dates but warn
                _logger.warning(f"Task {record.name} has a past due date: {record.due_date}")

    def name_get(self):
        result = []
        for record in self:
            name = record.name or f"Task {record.external_id}"
            result.append((record.id, name))
        return result

    def fetch_ghl_tasks(self, contact_external_id, app_access_token, location_id, company_id):
        """
        Fetch tasks for a specific contact from GHL API
        
        Args:
            contact_external_id (str): The external ID of the contact
            app_access_token (str): GHL OAuth agency access token
            location_id (str): GHL location ID
            company_id (str): GHL company ID
            
        Returns:
            dict: API response with tasks data
        """
        try:
            # Step 1: Get location access token
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
            # _logger.info(f"Location token response for tasks: {token_resp.status_code} {token_resp.text}")
            if token_resp.status_code not in (200, 201):
                _logger.error(f"Failed to get location token for tasks: {token_resp.text}")
                return {
                    'error': True,
                    'status_code': token_resp.status_code,
                    'message': token_resp.text
                }
                
            token_json = token_resp.json()
            location_token = token_json.get('access_token')
            if not location_token:
                _logger.error(f"No access_token in location token response for tasks: {token_json}")
                return {
                    'error': True,
                    'message': 'No access_token in location token response'
                }
            
            # Step 2: Fetch tasks using location token
            url = f"https://services.leadconnectorhq.com/contacts/{contact_external_id}/tasks"
            
            task_headers = {
                'Accept': 'application/json',
                'Authorization': f'Bearer {location_token}',
                'Version': '2021-07-28'
            }
            
            _logger.info(f"Fetching tasks for contact {contact_external_id} from GHL API")
            
            response = requests.get(url, headers=task_headers, timeout=30)
            
            if response.status_code == 200:
                tasks_data = response.json()
                
                # Check if tasks_data is a list or dict
                if isinstance(tasks_data, list):
                    _logger.info(f"API returned list with {len(tasks_data)} items for contact {contact_external_id}")
                    return {'tasks': tasks_data}
                elif isinstance(tasks_data, dict):
                    _logger.info(f"Successfully fetched {len(tasks_data.get('tasks', []))} tasks for contact {contact_external_id}")
                    return tasks_data
                else:
                    _logger.error(f"Unexpected response type for contact {contact_external_id}: {type(tasks_data)}")
                    return {'tasks': []}
            else:
                _logger.error(f"Failed to fetch tasks from GHL API. Status: {response.status_code}, Response: {response.text}")
                return {
                    'error': True,
                    'status_code': response.status_code,
                    'message': response.text
                }
        except requests.exceptions.RequestException as e:
            _logger.error(f"Request error while fetching GHL tasks: {str(e)}")
            return {
                'error': True,
                'message': f"Request error: {str(e)}"
            }
        except Exception as e:
            _logger.error(f"Unexpected error while fetching GHL tasks: {str(e)}")
            return {
                'error': True,
                'message': f"Unexpected error: {str(e)}"
            }

    def sync_contact_tasks_from_ghl(self, contact_id, app_access_token, location_id, company_id):
        """
        Sync tasks for a specific contact from GHL API and create/update local records
        
        Args:
            contact_id (int): Odoo contact record ID
            app_access_token (str): GHL OAuth agency access token
            location_id (str): GHL location ID
            company_id (str): GHL company ID
            
        Returns:
            dict: Sync results with created/updated counts
        """
        try:
            # Get the contact record
            contact = self.env['ghl.location.contact'].browse(contact_id)
            if not contact.exists():
                return {
                    'error': True,
                    'message': f"Contact with ID {contact_id} not found"
                }
            # Fetch tasks from GHL API
            api_response = self.fetch_ghl_tasks(contact.external_id, app_access_token, location_id, company_id)
            
            if api_response.get('error'):
                return api_response
            
            tasks_data = api_response.get('tasks', [])
            _logger.info(f"Processing {len(tasks_data)} tasks for contact {contact.name}")
            created_count = 0
            updated_count = 0
            
            for i, task_data in enumerate(tasks_data):
                _logger.info(f"Processing task {i+1}/{len(tasks_data)} for contact {contact.external_id}: {json.dumps(task_data, indent=2)}")
                task_external_id = task_data.get('id')
                if not task_external_id:
                    continue
                
                # Check if task already exists
                existing_task = self.search([
                    ('external_id', '=', task_external_id),
                    ('contact_id', '=', contact_id)
                ], limit=1)
                
                # Prepare task values
                task_vals = {
                    'external_id': task_external_id,
                    'title': task_data.get('title', ''),
                    'body': task_data.get('body', ''),
                    'contact_id': contact_id,
                    'assigned_to': task_data.get('assignedTo'),
                    'completed': task_data.get('completed', False),
                }
                
                # Parse due date if available
                due_date_str = task_data.get('dueDate')
                if due_date_str:
                    try:
                        # GHL typically returns ISO format datetime
                        due_date = datetime.fromisoformat(due_date_str.replace('Z', '+00:00'))
                        # Convert to naive datetime (remove timezone info) for Odoo
                        if due_date.tzinfo:
                            due_date = due_date.replace(tzinfo=None)
                        task_vals['due_date'] = due_date
                    except (ValueError, TypeError) as e:
                        _logger.warning(f"Could not parse due date '{due_date_str}' for task {task_external_id}: {e}")
                
                if existing_task:
                    # Update existing task
                    try:
                        existing_task.write('task_vals')
                        updated_count += 1
                        _logger.info(f"Updated task {task_external_id} for contact {contact.external_id}")
                    except Exception as e:
                        _logger.error(f"Error updating task {task_external_id}: {str(e)}")
                        continue
                else:
                    # Create new task
                    try:
                        self.create(task_vals)
                        created_count += 1
                        _logger.info(f"Created task {task_external_id} for contact {contact.external_id}")
                    except Exception as e:
                        _logger.error(f"Error creating task {task_external_id}: {str(e)}")
                        continue
            
            return {
                'success': True,
                'created_count': created_count,
                'updated_count': updated_count,
                'total_tasks': len(tasks_data)
            }
            
        except Exception as e:
            _logger.error(f"Error syncing tasks for contact {contact_id}: {str(e)}")
            return {
                'error': True,
                'message': f"Sync error: {str(e)}"
            }

    def sync_all_contact_tasks(self, app_access_token, location_id, company_id):
        """
        Sync tasks for all contacts in a location from GHL API
        
        Args:
            app_access_token (str): GHL OAuth agency access token
            location_id (str): GHL location ID
            company_id (str): GHL company ID
            
        Returns:
            dict: Overall sync results
        """
        try:
            _logger.info(f"[task sync] Looking for contacts with location_id={location_id}")
            contacts = self.env['ghl.location.contact'].search([
                ('location_id.location_id', '=', location_id)
            ])
            _logger.info(f"[task sync] Found {len(contacts)} contacts for location_id={location_id}")
            
            total_created = 0
            total_updated = 0
            total_contacts = len(contacts)
            errors = []
            
            for contact in contacts:
                result = self.sync_contact_tasks_from_ghl(contact.id, app_access_token, location_id, company_id)
                
                if result.get('error'):
                    errors.append(f"Contact {contact.external_id}: {result.get('message', 'Unknown error')}")
                else:
                    total_created += result.get('created_count', 0)
                    total_updated += result.get('updated_count', 0)
            
            return {
                'success': True,
                'total_contacts_processed': total_contacts,
                'total_tasks_created': total_created,
                'total_tasks_updated': total_updated,
                'errors': errors
            }
            
        except Exception as e:
            _logger.error(f"Error in bulk task sync: {str(e)}")
            return {
                'error': True,
                'message': f"Bulk sync error: {str(e)}"
            }

    def sync_all_contact_tasks_optimized(self, app_access_token, location_id, company_id):
        """
        Optimized version of sync_all_contact_tasks that:
        1. Gets location token once instead of per contact
        2. Uses bulk operations where possible
        3. Reduces API calls by batching
        4. Uses more efficient database queries
        
        Args:
            app_access_token (str): GHL OAuth agency access token
            location_id (str): GHL location ID
            company_id (str): GHL company ID
            
        Returns:
            dict: Overall sync results
        """
        try:
            _logger.info(f"[optimized task sync] Starting for location_id={location_id}")
            
            # Get contacts for this location
            contacts = self.env['ghl.location.contact'].search([
                ('location_id.location_id', '=', location_id)
            ])
            _logger.info(f"[optimized task sync] Found {len(contacts)} contacts")
            
            if not contacts:
                return {
                    'success': True,
                    'total_contacts_processed': 0,
                    'total_tasks_created': 0,
                    'total_tasks_updated': 0,
                    'errors': []
                }
            
            # Step 1: Get location token once (instead of per contact)
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
                _logger.error(f"Failed to get location token for optimized task sync: {token_resp.text}")
                return {
                    'error': True,
                    'message': f"Failed to get location token: {token_resp.text}",
                    'total_contacts_processed': 0,
                    'total_tasks_created': 0,
                    'total_tasks_updated': 0,
                    'errors': []
                }
                
            token_json = token_resp.json()
            location_token = token_json.get('access_token')
            if not location_token:
                _logger.error(f"No access_token in location token response for optimized task sync: {token_json}")
                return {
                    'error': True,
                    'message': 'No access_token in location token response',
                    'total_contacts_processed': 0,
                    'total_tasks_created': 0,
                    'total_tasks_updated': 0,
                    'errors': []
                }
            
            # Step 2: Get all existing tasks for these contacts in one query
            existing_tasks = self.search([
                ('contact_id', 'in', contacts.ids)
            ])
            existing_task_map = {}
            for task in existing_tasks:
                key = (task.external_id, task.contact_id.id)
                existing_task_map[key] = task
            
            _logger.info(f"[optimized task sync] Found {len(existing_tasks)} existing tasks")
            
            # Step 3: Process contacts in batches to avoid overwhelming the API
            batch_size = 10  # Process 10 contacts at a time
            total_created = 0
            total_updated = 0
            errors = []
            
            for i in range(0, len(contacts), batch_size):
                batch_contacts = contacts[i:i + batch_size]
                _logger.info(f"[optimized task sync] Processing batch {i//batch_size + 1}, contacts {i+1}-{min(i+batch_size, len(contacts))}")
                
                # Process each contact in the batch
                for contact in batch_contacts:
                    try:
                        # Fetch tasks for this contact using pagination
                        from .ghl_api_utils import fetch_contact_tasks_with_pagination
                        tasks_result = fetch_contact_tasks_with_pagination(location_token, contact.external_id)
                        
                        if tasks_result['success']:
                            tasks_list = tasks_result['items']
                            _logger.info(f"Fetched {len(tasks_list)} tasks for contact {contact.external_id} from {tasks_result['total_pages']} pages")
                        else:
                            _logger.warning(f"Failed to fetch tasks for contact {contact.external_id}: {tasks_result.get('error')}")
                            continue
                            
                        # Process tasks for this contact
                        for task_data in tasks_list:
                            task_external_id = task_data.get('id')
                            if not task_external_id:
                                continue
                            
                            # Check if task already exists
                            task_key = (task_external_id, contact.id)
                            existing_task = existing_task_map.get(task_key)
                            
                            # Prepare task values
                            task_vals = {
                                'external_id': task_external_id,
                                'title': task_data.get('title', ''),
                                'body': task_data.get('body', ''),
                                'contact_id': contact.id,
                                'assigned_to': task_data.get('assignedTo'),
                                'completed': task_data.get('completed', False),
                            }
                            
                            # Parse due date if available
                            due_date_str = task_data.get('dueDate')
                            if due_date_str:
                                try:
                                    due_date = datetime.fromisoformat(due_date_str.replace('Z', '+00:00'))
                                    if due_date.tzinfo:
                                        due_date = due_date.replace(tzinfo=None)
                                    task_vals['due_date'] = due_date
                                except (ValueError, TypeError) as e:
                                    _logger.warning(f"Could not parse due date '{due_date_str}' for task {task_external_id}: {e}")
                            
                            if existing_task:
                                # Update existing task
                                existing_task.write(task_vals)
                                total_updated += 1
                            else:
                                # Create new task
                                self.create(task_vals)
                                total_created += 1
                            
                    except Exception as e:
                        error_msg = f"Error processing contact {contact.external_id}: {str(e)}"
                        errors.append(error_msg)
                        _logger.error(error_msg)
                        continue
                
                # Small delay between batches to be respectful to the API
                if i + batch_size < len(contacts):
                    time.sleep(0.5)
            
            _logger.info(f"[optimized task sync] Completed: {total_created} created, {total_updated} updated, {len(errors)} errors")
            
            return {
                'success': True,
                'total_contacts_processed': len(contacts),
                'total_tasks_created': total_created,
                'total_tasks_updated': total_updated,
                'errors': errors
            }
            
        except Exception as e:
            _logger.error(f"Error in optimized bulk task sync: {str(e)}")
            return {
                'error': True,
                'message': f"Optimized bulk sync error: {str(e)}",
                'total_contacts_processed': 0,
                'total_tasks_created': 0,
                'total_tasks_updated': 0,
                'errors': [str(e)]
            }

    def action_sync_tasks_for_contact(self):
        """
        Action method to sync tasks for the current contact from GHL API
        This method can be called from UI buttons
        """
        self.ensure_one()
        
        # Get the contact's location to find the access token
        contact = self.contact_id
        if not contact:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Error',
                    'message': 'No contact associated with this task',
                    'type': 'danger',
                }
            }
        
        # Get the location to find the access token
        location = self.env['ghl.location'].search([
            ('location_id', '=', contact.location_id.id)
        ], limit=1)
        
        if not location:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Error',
                    'message': f'Location {contact.location_id} not found in Odoo',
                    'type': 'danger',
                }
            }
        
        # Get the access token from the location's OAuth configuration
        # This assumes you have OAuth configuration stored somewhere
        # You might need to adjust this based on your OAuth setup
        oauth_config = self.env['ghl.oauth.config'].search([
            ('location_id', '=', location.location_id.id)
        ], limit=1)
        
        if not oauth_config or not oauth_config.access_token:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Error',
                    'message': 'No valid access token found for this location',
                    'type': 'danger',
                }
            }
        
        # Sync tasks for this contact
        # Use hardcoded company_id since contact model doesn't have this field
        company_id = 'Ipg8nKDPLYKsbtodR6LN'  # Same as used in controller
        result = self.sync_contact_tasks_from_ghl(
            contact.id, 
            oauth_config.access_token, 
            contact.location_id,
            company_id
        )
        
        if result.get('error'):
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Sync Error',
                    'message': result.get('message', 'Unknown error occurred'),
                    'type': 'danger',
                }
            }
        else:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Success',
                    'message': f"Synced {result.get('created_count', 0)} new tasks and updated {result.get('updated_count', 0)} existing tasks",
                    'type': 'success',
                }
            } 