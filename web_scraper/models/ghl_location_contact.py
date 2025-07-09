from odoo import models, fields, api

class GHLLocationContactCustomField(models.Model):
    _name = 'ghl.location.contact.custom.field'
    _description = 'GHL Location Contact Custom Field'

    contact_id = fields.Many2one('ghl.location.contact', string='Contact', ondelete='cascade')
    custom_field_id = fields.Char(string='Custom Field ID')
    value = fields.Text(string='Value')

class GHLLocationContactAttribution(models.Model):
    _name = 'ghl.location.contact.attribution'
    _description = 'GHL Location Contact Attribution'

    contact_id = fields.Many2one('ghl.location.contact', string='Contact', ondelete='cascade')
    url = fields.Char(string='URL')
    campaign = fields.Char(string='Campaign')
    utm_source = fields.Char(string='UTM Source')
    utm_medium = fields.Char(string='UTM Medium')
    utm_content = fields.Char(string='UTM Content')
    referrer = fields.Char(string='Referrer')
    campaign_id = fields.Char(string='Campaign ID')
    fbclid = fields.Char(string='Facebook Click ID')
    gclid = fields.Char(string='Google Click ID')
    msclikid = fields.Char(string='Microsoft Click ID')
    dclid = fields.Char(string='DoubleClick Click ID')
    fbc = fields.Char(string='Facebook Browser Cookie')
    fbp = fields.Char(string='Facebook Browser Pixel')
    fb_event_id = fields.Char(string='Facebook Event ID')
    user_agent = fields.Char(string='User Agent')
    ip = fields.Char(string='IP Address')
    medium = fields.Char(string='Medium')
    medium_id = fields.Char(string='Medium ID')

class GHLLocationContact(models.Model):
    _name = 'ghl.location.contact'
    _description = 'GHL Location Contact'
    _order = 'date_added desc'

    # Basic Information
    external_id = fields.Char(string='External ID', required=True, index=True)
    location_id = fields.Many2one('installed.location', string='Location', required=True, ondelete='cascade')
    contact_name = fields.Char(string='Contact Name')
    first_name = fields.Char(string='First Name')
    last_name = fields.Char(string='Last Name')
    email = fields.Char(string='Email')
    timezone = fields.Char(string='Timezone')
    country = fields.Char(string='Country')
    source = fields.Char(string='Source')
    date_added = fields.Datetime(string='Date Added')
    
    # Relationships
    custom_field_ids = fields.One2many('ghl.location.contact.custom.field', 'contact_id', string='Custom Fields')
    attribution_ids = fields.One2many('ghl.location.contact.attribution', 'contact_id', string='Attributions')
    task_ids = fields.One2many('ghl.contact.task', 'contact_id', string='Tasks')
    
    # Additional Fields
    tags = fields.Text(string='Tags')  # Store as JSON string for now
    business_id = fields.Char(string='Business ID')
    followers = fields.Char(string='Followers')
    
    # Computed Fields
    name = fields.Char(string='Name', compute='_compute_name', store=True)
    tag_list = fields.Text(string='Tag List', compute='_compute_tag_list')
    assigned_user_name = fields.Char(string='Assigned User Name', compute='_compute_assigned_user_name', store=False)
    
    # AI and Analytics Fields (for frontend table)
    ai_status = fields.Selection([
        ('valid_lead', 'Valid Lead'),
        ('retention_path', 'Wants to Stay - Retention Path'),
        ('unqualified', 'Unqualified'),
        ('not_contacted', 'Not Contacted')
    ], string='AI Status', default='not_contacted')
    
    ai_summary = fields.Char(string='AI Summary', default='Read')
    ai_quality_grade = fields.Selection([
        ('grade_a', 'Lead Grade A'),
        ('grade_b', 'Lead Grade B'),
        ('grade_c', 'Lead Grade C'),
        ('no_grade', 'No Grade')
    ], string='AI Quality Grade', default='no_grade')
    
    ai_sales_grade = fields.Selection([
        ('grade_a', 'Sales Grade A'),
        ('grade_b', 'Sales Grade B'),
        ('grade_c', 'Sales Grade C'),
        ('grade_d', 'Sales Grade D'),
        ('no_grade', 'No Grade')
    ], string='AI Sales Grade', default='no_grade')
    
    crm_tasks = fields.Selection([
        ('overdue', '1 Overdue'),
        ('upcoming', '2 Upcoming'),
        ('no_tasks', 'No Tasks'),
        ('empty', '')
    ], string='CRM Tasks', default='no_tasks')
    
    category = fields.Selection([
        ('integration', 'Integration'),
        ('manual', 'Manual'),
        ('automated', 'Automated'),
        ('referral', 'Referral')
    ], string='Category', default='manual')
    
    channel = fields.Selection([
        ('integration', 'Integration'),
        ('manual', 'Manual'),
        ('automated', 'Automated'),
        ('referral', 'Referral')
    ], string='Channel', default='manual')
    
    created_by = fields.Char(string='Created By')
    attribution = fields.Char(string='Attribution')
    assigned_to = fields.Char(string='Assigned To')
    speed_to_lead = fields.Char(string='Speed to Lead')
    
    touch_summary = fields.Selection([
        ('no_touches', 'No Touches'),
        ('1_touch', '1 Touch'),
        ('2_touches', '2 Touches'),
        ('3_touches', '3 Touches')
    ], string='Touch Summary', default='no_touches')
    
    engagement_summary = fields.Text(string='Engagement Summary')  # JSON string for complex data
    last_touch_date = fields.Datetime(string='Last Touch Date')
    last_message = fields.Text(string='Last Message')  # JSON string for complex data
    total_pipeline_value = fields.Float(string='Total Pipeline Value', default=0.0, compute='_compute_opportunity_stats', store=True)
    opportunities = fields.Integer(string='Opportunities', default=0, compute='_compute_opportunity_stats', store=True)
    
    # Constraints
    _sql_constraints = [
        ('external_id_location_uniq', 'unique(external_id, location_id)', 'Contact must be unique per location!')
    ]
    
    @api.depends('contact_name', 'first_name', 'last_name', 'email', 'external_id')
    def _compute_name(self):
        for record in self:
            if record.contact_name:
                record.name = record.contact_name
            elif record.first_name or record.last_name:
                record.name = f"{record.first_name or ''} {record.last_name or ''}".strip()
            elif record.email:
                record.name = record.email
            else:
                record.name = f"Contact {record.external_id}"
    
    @api.depends('tags')
    def _compute_tag_list(self):
        for record in self:
            if record.tags:
                try:
                    import json
                    tag_data = json.loads(record.tags)
                    if isinstance(tag_data, list):
                        record.tag_list = ', '.join(tag_data)
                    else:
                        record.tag_list = str(tag_data)
                except:
                    record.tag_list = record.tags
            else:
                record.tag_list = ''
    
    @api.depends('assigned_to')
    def _compute_assigned_user_name(self):
        for record in self:
            if record.assigned_to:
                assigned_user = self.env['ghl.location.user'].sudo().search([
                    ('external_id', '=', record.assigned_to)
                ], limit=1)
                if assigned_user:
                    record.assigned_user_name = assigned_user.name or f"{assigned_user.first_name or ''} {assigned_user.last_name or ''}".strip()
                else:
                    record.assigned_user_name = record.assigned_to  # Fallback to external_id if user not found
            else:
                record.assigned_user_name = ''
    
    @api.depends('ghl_contact_opportunity_ids')
    def _compute_opportunity_stats(self):
        for rec in self:
            # Find all related opportunities
            opportunities = self.env['ghl.contact.opportunity'].search([('contact_id', '=', rec.id)])
            rec.opportunities = len(opportunities)
            rec.total_pipeline_value = sum(op.monetary_value or 0.0 for op in opportunities)

    ghl_contact_opportunity_ids = fields.One2many('ghl.contact.opportunity', 'contact_id', string='Opportunities')
    
    @api.model_create_multi
    def create(self, vals):
        """Override create to handle location_id relationship"""
        # Handle both single dict and list of dicts
        if isinstance(vals, list):
            # Process each dictionary in the list
            for val in vals:
                if isinstance(val, dict) and isinstance(val.get('location_id'), str):
                    installed_location = self.env['installed.location'].search([
                        ('location_id', '=', val['location_id'])
                    ], limit=1)
                    if installed_location:
                        val['location_id'] = installed_location.id
                    else:
                        # If no matching location found, create a placeholder or raise error
                        raise ValueError(f"No installed location found for location_id: {val['location_id']}")
        elif isinstance(vals, dict):
            # Single dictionary case
            if isinstance(vals.get('location_id'), str):
                installed_location = self.env['installed.location'].search([
                    ('location_id', '=', vals['location_id'])
                ], limit=1)
                if installed_location:
                    vals['location_id'] = installed_location.id
                else:
                    # If no matching location found, create a placeholder or raise error
                    raise ValueError(f"No installed location found for location_id: {vals['location_id']}")
        
        return super().create(vals)
    
    def write(self, vals):
        """Override write to handle location_id relationship"""
        # Handle both single dict and list of dicts
        if isinstance(vals, list):
            # Process each dictionary in the list
            for val in vals:
                if isinstance(val, dict) and isinstance(val.get('location_id'), str):
                    installed_location = self.env['installed.location'].search([
                        ('location_id', '=', val['location_id'])
                    ], limit=1)
                    if installed_location:
                        val['location_id'] = installed_location.id
                    else:
                        # If no matching location found, create a placeholder or raise error
                        raise ValueError(f"No installed location found for location_id: {val['location_id']}")
        elif isinstance(vals, dict):
            # Single dictionary case
            if isinstance(vals.get('location_id'), str):
                installed_location = self.env['installed.location'].search([
                    ('location_id', '=', vals['location_id'])
                ], limit=1)
                if installed_location:
                    vals['location_id'] = installed_location.id
                else:
                    # If no matching location found, create a placeholder or raise error
                    raise ValueError(f"No installed location found for location_id: {vals['location_id']}")
        
        return super().write(vals)
    
    def action_view_attributions(self):
        """Action to view contact attributions"""
        self.ensure_one()
        return {
            'name': f'Attributions for {self.name}',
            'type': 'ir.actions.act_window',
            'res_model': 'ghl.location.contact.attribution',
            'view_mode': 'list,form',
            'domain': [('contact_id', '=', self.id)],
            'context': {'default_contact_id': self.id},
        }
    
    def action_view_custom_fields(self):
        """Action to view contact custom fields"""
        self.ensure_one()
        return {
            'name': f'Custom Fields for {self.name}',
            'type': 'ir.actions.act_window',
            'res_model': 'ghl.location.contact.custom.field',
            'view_mode': 'list,form',
            'domain': [('contact_id', '=', self.id)],
            'context': {'default_contact_id': self.id},
        }
    
    def action_view_tasks(self):
        """Action to view contact tasks"""
        self.ensure_one()
        return {
            'name': f'Tasks for {self.name}',
            'type': 'ir.actions.act_window',
            'res_model': 'ghl.contact.task',
            'view_mode': 'list,form,kanban',
            'domain': [('contact_id', '=', self.id)],
            'context': {'default_contact_id': self.id, 'default_location_id': self.location_id},
        }

    @api.model
    def fetch_contacts_from_ghl_api(self, company_id, location_id, app_access_token):
        """
        Fetch contacts for a location using the GHL API.
        This method handles the API calls and returns the raw contact data.
        
        Args:
            company_id (str): GHL company ID
            location_id (str): GHL location ID
            app_access_token (str): GHL agency access token
            
        Returns:
            dict: API response with contacts data or error information
        """
        import requests
        import logging
        _logger = logging.getLogger(__name__)
        
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
            _logger.info(f"Location token response: {token_resp.status_code} {token_resp.text}")
            if token_resp.status_code not in (200, 201):
                _logger.error(f"Failed to get location token: {token_resp.text}")
                return {
                    'success': False,
                    'error': f"Failed to get location token: {token_resp.text}",
                    'status_code': token_resp.status_code
                }
                
            token_json = token_resp.json()
            location_token = token_json.get('access_token')
            if not location_token:
                _logger.error(f"No access_token in location token response: {token_json}")
                return {
                    'success': False,
                    'error': f"No access_token in location token response: {token_json}"
                }
                
            # Step 2: Fetch contacts
            contacts_url = f"https://services.leadconnectorhq.com/contacts/?locationId={location_id}&limit=100"
            contact_headers = {
                'Accept': 'application/json',
                'Authorization': f'Bearer {location_token}',
                'Version': '2021-07-28',
            }
            contacts_resp = requests.get(contacts_url, headers=contact_headers)
            _logger.info(f"Contacts API response: {contacts_resp.status_code} {contacts_resp.text}")
            
            if contacts_resp.status_code == 200:
                contacts_json = contacts_resp.json()
                _logger.info(f"Fetched contacts for location {location_id}: {contacts_json}")
                
                return {
                    'success': True,
                    'contacts_data': contacts_json.get('contacts', []),
                    'meta': contacts_json.get('meta', {}),
                    'trace_id': contacts_json.get('traceId', ''),
                    'total_contacts': len(contacts_json.get('contacts', []))
                }
            else:
                _logger.error(f"Failed to fetch contacts: {contacts_resp.text}")
                return {
                    'success': False,
                    'error': f"Failed to fetch contacts: {contacts_resp.text}",
                    'status_code': contacts_resp.status_code
                }
                
        except requests.exceptions.RequestException as e:
            _logger.error(f"Request error while fetching contacts: {str(e)}")
            return {
                'success': False,
                'error': f"Request error: {str(e)}"
            }
        except Exception as e:
            _logger.error(f"Unexpected error while fetching contacts: {str(e)}")
            return {
                'success': False,
                'error': f"Unexpected error: {str(e)}"
            } 