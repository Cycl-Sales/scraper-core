from odoo import models, fields, api
import requests
from odoo.exceptions import ValidationError
from odoo.tools.translate import _
import json


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
    conversation_ids = fields.One2many('ghl.contact.conversation', 'contact_id', string='Conversations')
    opportunity_ids = fields.One2many('ghl.contact.opportunity', 'contact_id', string='Opportunities')

    # Additional Fields
    tags = fields.Text(string='Tags')  # Store as JSON string for now
    business_id = fields.Char(string='Business ID')
    followers = fields.Char(string='Followers')
    details_fetched = fields.Boolean(string='Details Fetched', default=False)

    # Computed Fields
    name = fields.Char(string='Name', compute='_compute_name', store=True)
    tag_list = fields.Text(string='Tag List', compute='_compute_tag_list')
    assigned_user_name = fields.Char(string='Assigned User Name', compute='_compute_assigned_user_name', store=False)

    # AI and Analytics Fields (for frontend table)
    ai_status = fields.Selection(selection='_get_ai_status_selection', string='AI Status', default='not_contacted')

    ai_summary = fields.Char(string='AI Summary', default='AI analysis pending')
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

    touch_summary = fields.Char(string='Touch Summary', default='no_touches')

    engagement_summary = fields.Text(string='Engagement Summary')  # JSON string for complex data
    last_touch_date = fields.Datetime(string='Last Touch Date')
    last_message = fields.Text(string='Last Message')  # JSON string for complex data
    total_pipeline_value = fields.Float(string='Total Pipeline Value', default=0.0,
                                        compute='_compute_opportunity_stats', store=True)
    opportunities = fields.Integer(string='Opportunities', default=0, compute='_compute_opportunity_stats', store=True)

    # Constraints
    _sql_constraints = [
        ('external_id_location_uniq', 'unique(external_id, location_id)', 'Contact must be unique per location!')
    ]
    
    def _get_ai_status_selection(self):
        """Get AI status selection options from automation template"""
        # Default options
        default_options = [('not_contacted', 'Not Contacted')]
        
        # Get options from automation template if available
        if hasattr(self, 'location_id') and self.location_id and self.location_id.automation_template_id:
            contact_status_setting = self.location_id.automation_template_id.contact_status_setting_ids.filtered(lambda s: s.enabled)
            if contact_status_setting:
                status_options = contact_status_setting[0].status_option_ids
                return [(option.name, option.name) for option in status_options] + default_options
        
        return default_options

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

    @api.depends('opportunity_ids')
    def _compute_opportunity_stats(self):
        for rec in self:
            # Find all related opportunities
            opportunities = self.env['ghl.contact.opportunity'].search([('contact_id', '=', rec.id)])
            rec.opportunities = len(opportunities)
            rec.total_pipeline_value = sum(op.monetary_value or 0.0 for op in opportunities)

    def _compute_touch_summary(self):
        """Compute touch summary based on message types"""
        for contact in self:
            # Get all messages for this contact
            messages = self.env['ghl.contact.message'].search([
                ('contact_id', '=', contact.id)
            ])

            if not messages:
                contact.touch_summary = 'no_touches'
                continue

            # Count messages by type
            message_counts = {}
            for message in messages:
                message_type = message.message_type or 'UNKNOWN'
                message_counts[message_type] = message_counts.get(message_type, 0) + 1

            # Create touch summary string
            touch_parts = []
            for msg_type, count in message_counts.items():
                # Map message types to readable names
                type_name = self._get_message_type_display_name(msg_type)
                touch_parts.append(f"{count} {type_name}")

            if touch_parts:
                contact.touch_summary = ', '.join(touch_parts)
            else:
                contact.touch_summary = 'no_touches'

    def _get_message_type_display_name(self, message_type):
        """Convert message type to readable display name"""
        type_mapping = {
            'TYPE_SMS': 'SMS',
            'TYPE_CALL': 'PHONE CALL',
            'TYPE_EMAIL': 'EMAIL',
            'TYPE_SMS_REVIEW_REQUEST': 'SMS REVIEW',
            'TYPE_WEBCHAT': 'WEBCHAT',
            'TYPE_SMS_NO_SHOW_REQUEST': 'SMS NO SHOW',
            'TYPE_NO_SHOW': 'NO SHOW',
            'TYPE_CAMPAIGN_SMS': 'CAMPAIGN SMS',
            'TYPE_CAMPAIGN_CALL': 'CAMPAIGN CALL',
            'TYPE_CAMPAIGN_EMAIL': 'CAMPAIGN EMAIL',
            'TYPE_CAMPAIGN_VOICEMAIL': 'CAMPAIGN VOICEMAIL',
            'TYPE_FACEBOOK': 'FACEBOOK',
            'TYPE_CAMPAIGN_FACEBOOK': 'CAMPAIGN FACEBOOK',
            'TYPE_CAMPAIGN_MANUAL_CALL': 'MANUAL CALL',
            'TYPE_CAMPAIGN_MANUAL_SMS': 'MANUAL SMS',
            'TYPE_GMB': 'GOOGLE MY BUSINESS',
            'TYPE_CAMPAIGN_GMB': 'CAMPAIGN GMB',
            'TYPE_REVIEW': 'REVIEW',
            'TYPE_INSTAGRAM': 'INSTAGRAM',
            'TYPE_WHATSAPP': 'WHATSAPP',
            'TYPE_CUSTOM_SMS': 'CUSTOM SMS',
            'TYPE_CUSTOM_EMAIL': 'CUSTOM EMAIL',
            'TYPE_CUSTOM_PROVIDER_SMS': 'PROVIDER SMS',
            'TYPE_CUSTOM_PROVIDER_EMAIL': 'PROVIDER EMAIL',
            'TYPE_IVR_CALL': 'IVR CALL',
            'TYPE_ACTIVITY_CONTACT': 'ACTIVITY',
            'TYPE_ACTIVITY_INVOICE': 'INVOICE',
            'TYPE_ACTIVITY_PAYMENT': 'PAYMENT',
            'TYPE_ACTIVITY_OPPORTUNITY': 'OPPORTUNITY',
            'TYPE_LIVE_CHAT': 'LIVE CHAT',
            'TYPE_LIVE_CHAT_INFO_MESSAGE': 'CHAT INFO',
            'TYPE_ACTIVITY_APPOINTMENT': 'APPOINTMENT',
            'TYPE_FACEBOOK_COMMENT': 'FB COMMENT',
            'TYPE_INSTAGRAM_COMMENT': 'IG COMMENT',
            'TYPE_CUSTOM_CALL': 'CUSTOM CALL',
            'TYPE_INTERNAL_COMMENT': 'INTERNAL COMMENT',
        }
        return type_mapping.get(message_type, message_type.replace('TYPE_', ''))

    def _compute_last_touch_date(self):
        """Compute last touch date from most recent message"""
        for contact in self:
            # Get the most recent message for this contact
            last_message = self.env['ghl.contact.message'].search([
                ('contact_id', '=', contact.id)
            ], order='create_date desc', limit=1)

            if last_message and last_message.create_date:
                contact.last_touch_date = last_message.create_date
            else:
                contact.last_touch_date = False

    def _compute_last_message_content(self):
        """Compute last message content from most recent message"""
        for contact in self:
            # Get the most recent message for this contact
            last_message = self.env['ghl.contact.message'].search([
                ('contact_id', '=', contact.id)
            ], order='create_date desc', limit=1)

            if last_message and last_message.body:
                # Store as JSON for consistency with existing pattern
                import json
                message_data = {
                    'body': last_message.body,
                    'type': last_message.message_type,
                    'direction': last_message.direction,
                    'date_added': last_message.create_date.isoformat() if last_message.create_date else '',
                    'id': last_message.ghl_id
                }
                contact.last_message = json.dumps(message_data)
            else:
                contact.last_message = ''

    def update_touch_information(self):
        """Update touch summary, last touch date, and last message for this contact"""
        self._compute_touch_summary()
        self._compute_last_touch_date()
        self._compute_last_message_content()

    @api.model
    def update_all_contacts_touch_information(self):
        """Update touch information for all contacts that have messages"""
        import logging
        _logger = logging.getLogger(__name__)

        contacts_with_messages = self.search([
            ('id', 'in', self.env['ghl.contact.message'].search([]).mapped('contact_id.id'))
        ])

        _logger.info(f"Updating touch information for {len(contacts_with_messages)} contacts with messages")

        for contact in contacts_with_messages:
            try:
                contact.update_touch_information()
            except Exception as e:
                _logger.error(f"Error updating touch information for contact {contact.id}: {str(e)}")

        _logger.info("Touch information update completed")
        return {
            'success': True,
            'contacts_updated': len(contacts_with_messages)
        }

    ghl_contact_opportunity_ids = fields.One2many('ghl.contact.opportunity', 'contact_id', string='Opportunities')

    # AI Analysis Status
    ai_analysis_status = fields.Selection([
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed')
    ], string='AI Analysis Status', default='pending')

    ai_analysis_date = fields.Datetime(string='AI Analysis Date')
    ai_analysis_error = fields.Text(string='AI Analysis Error')

    @api.model
    def update_all_contacts_ai_analysis(self):
        """Update AI analysis status for all contacts that have messages and automation templates"""
        import logging
        _logger = logging.getLogger(__name__)
        
        # Get contacts with messages and automation templates
        contacts_with_messages = self.search([
            ('id', 'in', self.env['ghl.contact.message'].search([]).mapped('contact_id.id'))
        ])
        
        # Filter contacts that have automation templates
        contacts_with_templates = contacts_with_messages.filtered(
            lambda c: c.location_id and c.location_id.automation_template_id
        )
        
        contacts_without_templates = contacts_with_messages - contacts_with_templates
        
        _logger.info(f"Found {len(contacts_with_messages)} contacts with messages")
        _logger.info(f"Found {len(contacts_with_templates)} contacts with automation templates")
        _logger.info(f"Found {len(contacts_without_templates)} contacts without automation templates")
        
        if contacts_without_templates:
            _logger.warning(f"Contacts without automation templates: {contacts_without_templates.mapped('name')}")
        
        for contact in contacts_with_templates:
            try:
                contact.update_ai_analysis_status()
            except Exception as e:
                _logger.error(f"Error updating AI analysis status for contact {contact.id}: {str(e)}")
        
        _logger.info("AI analysis status update completed")
        return {
            'success': True,
            'contacts_updated': len(contacts_with_templates),
            'contacts_without_templates': len(contacts_without_templates)
        }

    def update_ai_analysis_status(self):
        """Update AI analysis status for this contact"""
        # Check if automation template is available
        if not self.location_id or not self.location_id.automation_template_id:
            self.ai_analysis_status = 'failed'
            self.ai_analysis_error = 'No automation template assigned to location'
            return {
                'success': False,
                'message': 'No automation template found. Please assign an automation template to the location first.'
            }
        
        # This method will be implemented in a subsequent edit to trigger AI analysis
        # For now, it will just set status to 'completed' and log a message
        self.ai_analysis_status = 'completed'
        self.ai_analysis_date = fields.Datetime.now()
        self.ai_analysis_error = ''
        return {
            'success': True,
            'message': 'AI analysis status updated to completed.'
        }

    def run_ai_analysis(self):
        """Run AI analysis for this specific contact using real AI service"""
        import logging
        _logger = logging.getLogger(__name__)
        
        try:
            # Set status to processing
            self.ai_analysis_status = 'processing'
            self.ai_analysis_error = ''
            
            # Get the automation template for this contact's location
            automation_template = self.location_id.automation_template_id
            if not automation_template:
                raise Exception("No automation template found for this contact's location. Please assign an automation template to the location first.")
            
            _logger.info(f"Starting AI analysis for contact {self.id} using template {automation_template.name}")
            
            # Get the AI service
            ai_service = self.env['cyclsales.vision.ai'].sudo().get_default_ai_service()
            if not ai_service:
                raise Exception("No active AI service found")
            
            # Prepare contact data for AI analysis
            contact_data = self._prepare_contact_data_for_ai()
            
            # Generate AI analysis using the AI service
            ai_result = self._generate_ai_analysis(ai_service, contact_data, automation_template)
            
            # Update contact fields with AI results
            self._update_contact_with_ai_results(ai_result)
            
            # Update status to completed
            self.ai_analysis_status = 'completed'
            self.ai_analysis_date = fields.Datetime.now()
            
            _logger.info(f"AI analysis completed successfully for contact {self.id}")
            
            return {
                'success': True,
                'message': 'AI analysis completed successfully using automation template',
                'ai_status': self.ai_status,
                'ai_summary': self.ai_summary,
                'ai_quality_grade': self.ai_quality_grade,
                'ai_sales_grade': self.ai_sales_grade
            }
            
        except Exception as e:
            _logger.error(f"Error running AI analysis for contact {self.id}: {str(e)}")
            self.ai_analysis_status = 'failed'
            self.ai_analysis_error = str(e)
            return {
                'success': False,
                'error': str(e)
            }

    def _prepare_contact_data_for_ai(self):
        """Prepare contact data for AI analysis"""
        import json

        # Get all messages for this contact
        messages = self.env['ghl.contact.message'].search([
            ('contact_id', '=', self.id)
        ], order='create_date asc')

        # Get conversations
        conversations = self.conversation_ids.sorted('create_date')

        # Get opportunities
        opportunities = self.opportunity_ids

        # Get tasks
        tasks = self.task_ids

        # Prepare conversation data
        conversation_data = []
        for conv in conversations:
            conv_messages = messages.filtered(lambda m: m.conversation_id == conv)
            conversation_data.append({
                'id': conv.ghl_id,
                'type': conv.type,
                'messages_count': len(conv_messages),
                'last_message': conv.last_message_body,
                'unread_count': conv.unread_count,
                'create_date': conv.create_date.isoformat() if conv.create_date else None
            })

        # Prepare message data
        message_data = []
        for msg in messages[:50]:  # Limit to last 50 messages
            message_data.append({
                'body': msg.body,
                'type': msg.message_type,
                'direction': msg.direction,
                'date': msg.create_date.isoformat() if msg.create_date else None
            })

        # Prepare opportunity data
        opportunity_data = []
        for opp in opportunities:
            opportunity_data.append({
                'name': opp.name,
                'stage': opp.stage,
                'monetary_value': opp.monetary_value,
                'status': opp.status,
                'date_created': opp.date_created.isoformat() if opp.date_created else None
            })

        # Prepare task data
        task_data = []
        for task in tasks:
            task_data.append({
                'title': task.title,
                'body': task.body,
                'completed': task.completed,
                'due_date': task.due_date.isoformat() if task.due_date else None
            })

        # Compile contact data
        contact_data = {
            'contact_info': {
                'name': self.name,
                'email': self.email,
                'phone': getattr(self, 'phone', ''),
                'source': self.source,
                'date_added': self.date_added.isoformat() if self.date_added else None,
                'tags': self.tag_list,
                'assigned_to': self.assigned_user_name
            },
            'engagement': {
                'conversations_count': len(conversations),
                'messages_count': len(messages),
                'opportunities_count': len(opportunities),
                'tasks_count': len(tasks),
                'touch_summary': self.touch_summary,
                'last_touch_date': self.last_touch_date.isoformat() if self.last_touch_date else None
            },
            'conversations': conversation_data,
            'messages': message_data,
            'opportunities': opportunity_data,
            'tasks': task_data
        }

        return contact_data

    def _generate_ai_analysis(self, ai_service, contact_data, automation_template):
        """Generate AI analysis using the AI service"""
        import json
        import logging
        _logger = logging.getLogger(__name__)

        # Create AI prompt for contact analysis
        prompt = self._create_ai_analysis_prompt(contact_data, automation_template)

        # Convert contact data to text for AI analysis
        contact_text = json.dumps(contact_data, indent=2)

        # Call the AI service
        ai_result = ai_service.generate_summary(
            message_id=f"contact_{self.id}",
            contact_id=self.id,
            transcript=contact_text,
            custom_prompt=prompt,
            location_id=self.location_id.id
        )

        _logger.info(f"AI analysis result for contact {self.id}: {ai_result}")

        return ai_result

    def _create_ai_analysis_prompt(self, contact_data, automation_template):
        """Create AI prompt for contact analysis using automation template settings"""
        # Get contact status options from automation template
        contact_status_setting = automation_template.contact_status_setting_ids.filtered(lambda s: s.enabled)
        status_options = []
        if contact_status_setting:
            status_options = contact_status_setting[0].status_option_ids
        
        # Get AI contact scoring rules from automation template
        ai_contact_scoring_setting = automation_template.ai_contact_scoring_setting_ids.filtered(lambda s: s.enabled)
        contact_scoring_rules = ""
        if ai_contact_scoring_setting:
            contact_scoring_rules = ai_contact_scoring_setting[0].examples_rules or ""
        
        # Get AI sales scoring rules from automation template
        ai_sales_scoring_setting = automation_template.ai_sales_scoring_setting_ids.filtered(lambda s: s.enabled)
        sales_scoring_rules = ""
        if ai_sales_scoring_setting:
            sales_scoring_rules = ai_sales_scoring_setting[0].framework or ""
        
        # Build status options for the prompt
        status_options_text = ""
        if status_options:
            status_options_text = "Available status options:\n"
            for option in status_options:
                status_options_text += f"- {option.name}: {option.description}\n"
        
        # Build the prompt
        prompt = f"""Analyze the following contact data and return a JSON response with exactly this structure:
{{
    "ai_status": "status_option_name",
    "ai_summary": "Detailed summary text (2-4 sentences)",
    "ai_quality_grade": "grade_a|grade_b|grade_c|no_grade",
    "ai_sales_grade": "grade_a|grade_b|grade_c|grade_d|no_grade",
    "analysis_reasoning": "Brief explanation of the analysis decisions"
}}

Business Context: {automation_template.business_context or 'No specific business context provided.'}

{status_options_text}

Contact Scoring Rules: {contact_scoring_rules}

Sales Scoring Rules: {sales_scoring_rules}

Requirements:
- ai_status: Choose from the available status options above based on engagement level and conversation quality
- ai_summary: Provide a detailed 2-4 sentence summary of the contact's engagement, key interactions, and current status. Include specific details about conversations, opportunities, and any notable patterns. If no meaningful interactions exist, provide a brief summary of the contact's basic information and lack of engagement.
- ai_quality_grade: Based on engagement quality and conversation depth using the contact scoring rules
- ai_sales_grade: Based on sales potential and opportunity value using the sales scoring rules
- analysis_reasoning: 2-3 sentences explaining your decisions

Contact Data:
{json.dumps(contact_data, indent=2)}

Return only the JSON object, no additional text."""
        
        return prompt

    def _update_contact_with_ai_results(self, ai_result):
        """Update contact fields with AI analysis results"""
        import logging
        _logger = logging.getLogger(__name__)
        
        try:
            # Extract AI results
            ai_status = ai_result.get('ai_status', 'not_contacted')
            ai_summary = ai_result.get('ai_summary', 'No summary available')
            ai_quality_grade = ai_result.get('ai_quality_grade', 'no_grade')
            ai_sales_grade = ai_result.get('ai_sales_grade', 'no_grade')
            
            # Get valid status options from automation template
            valid_statuses = ['not_contacted']  # Default fallback
            if self.location_id and self.location_id.automation_template_id:
                contact_status_setting = self.location_id.automation_template_id.contact_status_setting_ids.filtered(lambda s: s.enabled)
                if contact_status_setting:
                    valid_statuses = [option.name for option in contact_status_setting[0].status_option_ids]
                    valid_statuses.append('not_contacted')  # Always allow this fallback
            
            # Validate and set values
            valid_quality_grades = ['grade_a', 'grade_b', 'grade_c', 'no_grade']
            valid_sales_grades = ['grade_a', 'grade_b', 'grade_c', 'grade_d', 'no_grade']
            
            if ai_status in valid_statuses:
                self.ai_status = ai_status
            else:
                self.ai_status = 'not_contacted'
                _logger.warning(f"Invalid AI status '{ai_status}' for contact {self.id}. Valid options: {valid_statuses}")
            
            # Validate and set AI summary - should be a detailed text, not just "Read" or "No Summary"
            if ai_summary and isinstance(ai_summary, str) and len(ai_summary.strip()) > 0:
                # Ensure the summary is not just "Read" or "No Summary" - it should be detailed
                if ai_summary.lower() in ['read', 'no summary', 'no summary available']:
                    # Generate a basic summary if AI returned placeholder text
                    self.ai_summary = f"Contact {self.name or self.external_id} has been analyzed. {ai_summary}"
                else:
                    self.ai_summary = ai_summary
            else:
                self.ai_summary = f"Contact {self.name or self.external_id} has been analyzed. No detailed summary available."
            
            if ai_quality_grade in valid_quality_grades:
                self.ai_quality_grade = ai_quality_grade
            else:
                self.ai_quality_grade = 'no_grade'
                _logger.warning(f"Invalid AI quality grade '{ai_quality_grade}' for contact {self.id}")
            
            if ai_sales_grade in valid_sales_grades:
                self.ai_sales_grade = ai_sales_grade
            else:
                self.ai_sales_grade = 'no_grade'
                _logger.warning(f"Invalid AI sales grade '{ai_sales_grade}' for contact {self.id}")
            
            # Save the changes to the database
            self.write({
                'ai_status': self.ai_status,
                'ai_summary': self.ai_summary,
                'ai_quality_grade': self.ai_quality_grade,
                'ai_sales_grade': self.ai_sales_grade,
                'ai_analysis_status': 'completed',
                'ai_analysis_date': fields.Datetime.now(),
            })
            
            _logger.info(
                f"Updated contact {self.id} with AI results: status={self.ai_status}, summary={self.ai_summary[:100]}..., quality={self.ai_quality_grade}, sales={self.ai_sales_grade}")
             
        except Exception as e:
            _logger.error(f"Error updating contact {self.id} with AI results: {str(e)}")
            # Set default values on error and save to database
            error_values = {
                'ai_status': 'not_contacted',
                'ai_summary': f"Contact {self.name or self.external_id} has been analyzed. Error occurred during AI analysis.",
                'ai_quality_grade': 'no_grade',
                'ai_sales_grade': 'no_grade',
                'ai_analysis_status': 'failed',
                'ai_analysis_date': fields.Datetime.now(),
                'ai_analysis_error': str(e)
            }
            self.write(error_values)

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
        # Handle location_id string conversion
        if isinstance(vals, dict) and isinstance(vals.get('location_id'), str):
            installed_location = self.env['installed.location'].search([
                ('location_id', '=', vals['location_id'])
            ], limit=1)
            if installed_location:
                vals['location_id'] = installed_location.id
            else:
                # If no matching location found, raise error
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

    def action_fetch_conversations(self):
        """
        Button to fetch all conversations for this contact from the GHL API.
        Requires the contact to have a valid external_id, location, and access token.
        """
        self.ensure_one()

        # Validate required fields
        if not self.external_id:
            raise ValidationError(_('Contact must have a valid external_id to fetch conversations.'))

        if not self.location_id or not self.location_id.location_id:
            raise ValidationError(_('Contact must be associated with a valid location to fetch conversations.'))

        # Find the access token for this location's app
        app = self.env['cyclsales.application'].sudo().search([
            ('app_id', '=', self.location_id.app_id),
            ('is_active', '=', True)
        ], limit=1)

        if not app or not app.access_token:
            raise ValidationError(
                _('No valid access token found for this location. Please check the application configuration.'))

        # Hardcode company_id (same as controller)
        company_id = 'Ipg8nKDPLYKsbtodR6LN'

        try:
            # Step 1: Get location token using agency token and company_id
            location_token_result = self.env['ghl.contact.conversation'].sudo()._get_location_token(
                app_access_token=app.access_token,  # Agency access token
                location_id=self.location_id.location_id,  # GHL location ID
                company_id=company_id  # Company ID
            )

            if not location_token_result.get('success'):
                raise ValidationError(
                    _('Failed to get location token: %s') % location_token_result.get('message', 'Unknown error'))

            location_token = location_token_result.get('access_token')

            # Step 2: Call the conversation sync method with location token
            result = self.env['ghl.contact.conversation'].sudo().sync_conversations_for_contact_with_location_token(
                location_token=location_token,  # Location access token (not agency token)
                location_id=self.location_id.location_id,  # GHL location ID
                contact_id=self.external_id,  # Contact's external_id from GHL
                limit=100
            )

            if result.get('success'):
                # Show success notification with details
                message = _('Successfully fetched conversations for contact %s. Created: %d, Updated: %d') % (
                    self.name or self.external_id,
                    result.get('created_count', 0),
                    result.get('updated_count', 0)
                )

                # If messages were also synced, include that info
                if result.get('message_sync_results'):
                    total_messages = sum(
                        msg.get('messages_fetched', 0) for msg in result.get('message_sync_results', []))
                    if total_messages > 0:
                        message += _('. Messages fetched: %d') % total_messages

                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Conversations Fetched'),
                        'message': message,
                        'type': 'success',
                    }
                }
            else:
                # Show error notification
                error_msg = result.get('error', _('Unknown error occurred while fetching conversations.'))
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Error'),
                        'message': _('Failed to fetch conversations: %s') % error_msg,
                        'type': 'danger',
                    }
                }

        except Exception as e:
            # Show error notification for exceptions
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Error'),
                    'message': _('Exception occurred while fetching conversations: %s') % str(e),
                    'type': 'danger',
                }
            }

    @api.model
    def fetch_contacts_from_ghl_api_paginated(self, company_id, location_id, app_access_token, limit=10, skip=0):
        """
        Fetch contacts for a location using the GHL API with specific pagination parameters.
        Args:
            company_id (str): GHL company ID
            location_id (str): GHL location ID
            app_access_token (str): GHL agency access token
            limit (int): Number of contacts to fetch per page
            skip (int): Number of contacts to skip (for pagination)
        Returns:
            dict: API response with contacts data or error information
        """
        from .ghl_api_utils import get_location_token
        import logging
        _logger = logging.getLogger(__name__)

        try:
            # Step 1: Get location access token
            location_token = get_location_token(app_access_token, company_id, location_id)
            if not location_token:
                return {
                    'success': False,
                    'error': "Failed to get location access token"
                }
            # Step 2: Fetch contacts using POST /contacts/search with specific pagination
            url = "https://services.leadconnectorhq.com/contacts/search"
            headers = {
                'Accept': 'application/json',
                'Authorization': f'Bearer {location_token}',
                'Version': '2021-07-28',
            }
            # Calculate page number (1-based)
            page = (skip // limit) + 1
            # Prepare search data with correct pagination keys and sorting
            data = {
                'locationId': location_id,
                'pageLimit': limit,
                'page': page,
                'sort': [
                    {
                        'field': 'dateUpdated',
                        'direction': 'desc'
                    }
                ]
            }
            _logger.info(f"Fetching contacts for location {location_id} with pageLimit={limit}, page={page}")
            response = requests.post(url, headers=headers, json=data, timeout=30)
            if response.status_code == 200:
                result = response.json()
                contacts = result.get('contacts', [])
                total_count = result.get('total', 0)
                _logger.info(f"Successfully fetched {len(contacts)} contacts (total: {total_count}) for page {page}")
                
                # Log the first few contacts to see what we're getting
                for i, contact in enumerate(contacts[:3]):
                    contact_name = contact.get('contactName', 'Unknown')
                    contact_id = contact.get('id', 'Unknown')
                    _logger.info(f"GHL API Contact {i+1} on page {page}: ID={contact_id}, Name='{contact_name}'")
                return {
                    'success': True,
                    'contacts_data': contacts,
                    'total_contacts': total_count,
                    'has_more': (skip + limit) < total_count,
                    'page_info': {
                        'limit': limit,
                        'skip': skip,
                        'total': total_count,
                        'current_page': page
                    }
                }
            else:
                _logger.error(f"Failed to fetch contacts. Status: {response.status_code}, Response: {response.text}")
                return {
                    'success': False,
                    'error': f'API request failed with status {response.status_code}'
                }

        except Exception as e:
            _logger.error(f"Unexpected error while fetching contacts: {str(e)}")
            import traceback
            _logger.error(f"Full traceback: {traceback.format_exc()}")
            return {
                'success': False,
                'error': f"Unexpected error: {str(e)}"
            }

    @api.model
    def fetch_contacts_from_ghl_api(self, company_id, location_id, app_access_token, max_pages=None):
        """
        Fetch contacts for a location using the GHL API with pagination support (POST /contacts/search).
        Args:
            company_id (str): GHL company ID
            location_id (str): GHL location ID
            app_access_token (str): GHL agency access token
            max_pages (int): Maximum number of pages to fetch (None for unlimited)
        Returns:
            dict: API response with contacts data or error information
        """
        from .ghl_api_utils import get_location_token, fetch_contacts_with_pagination
        import logging
        _logger = logging.getLogger(__name__)
        try:
            # Step 1: Get location access token
            location_token = get_location_token(app_access_token, company_id, location_id)
            if not location_token:
                return {
                    'success': False,
                    'error': "Failed to get location access token"
                }
            # Step 2: Fetch all contacts using new pagination utility (POST /contacts/search)
            _logger.info(f"Fetching contacts for location {location_id} with pagination (max_pages: {max_pages})")
            result = fetch_contacts_with_pagination(location_token, location_id, max_pages)
            if result['success']:
                _logger.info(
                    f"Successfully fetched {result['total_items']} contacts from {result['total_pages']} pages")
                return {
                    'success': True,
                    'contacts_data': result['items'],
                    'meta': {
                        'total': result['total_count'],
                        'pages_fetched': result['total_pages'],
                        'items_fetched': result['total_items']
                    },
                    'total_contacts': result['total_items'],
                    'pages_fetched': result['total_pages']
                }
            else:
                return {
                    'success': False,
                    'error': result.get('error', 'Failed to fetch contacts')
                }
        except Exception as e:
            _logger.error(f"Unexpected error while fetching contacts: {str(e)}")
            import traceback
            _logger.error(f"Full traceback: {traceback.format_exc()}")
            return {
                'success': False,
                'error': f"Unexpected error: {str(e)}"
            }

    def fetch_contact_single(self, location_token, contact_id):
        """
        Fetch a single contact from GHL and create/update the record in Odoo.
        :param location_token: The location access token (string)
        :param contact_id: The GHL contact ID (string)
        :return: The created/updated contact record, or None on failure
        """
        import requests
        import logging
        from datetime import datetime
        _logger = logging.getLogger(__name__)
        url = f'https://services.leadconnectorhq.com/contacts/{contact_id}'
        headers = {
            'Accept': 'application/json',
            'Authorization': f'Bearer {location_token}',
            'Version': '2021-07-28',
        }
        try:
            resp = requests.get(url, headers=headers)
            _logger.info(f"[GHLLocationContact] fetch_contact_single response: {resp.status_code} {resp.text}")
            if resp.status_code != 200:
                _logger.error(f"Failed to fetch contact: {resp.text}")
                return None
            data = resp.json().get('contact')
            if not data:
                _logger.error(f"No contact data in response: {resp.text}")
                return None
            # Map fields
            vals = {
                'external_id': data.get('id'),
                'contact_name': data.get('name'),
                'first_name': data.get('firstName'),
                'last_name': data.get('lastName'),
                'email': data.get('email'),
                'timezone': data.get('timezone'),
                'country': data.get('country'),
                'source': data.get('source'),
                'date_added': data.get('dateAdded'),
                'business_id': data.get('businessId'),
                'assigned_to': data.get('assignedTo'),
                'tags': str(data.get('tags')) if data.get('tags') else None,
                'last_touch_date': data.get('lastActivity'),
                'details_fetched': True,
            }
            # Find installed.location by locationId
            location_id = data.get('locationId')
            installed_location = self.env['installed.location'].search([
                ('location_id', '=', location_id)
            ], limit=1)
            if not installed_location:
                _logger.error(f"No installed.location found for locationId: {location_id}")
                return None
            vals['location_id'] = installed_location.id
            # Parse datetimes
            for dt_field in ['date_added', 'last_touch_date']:
                if vals.get(dt_field):
                    try:
                        vals[dt_field] = datetime.strptime(vals[dt_field].replace('Z', ''), '%Y-%m-%dT%H:%M:%S.%f')
                    except Exception:
                        try:
                            vals[dt_field] = datetime.strptime(vals[dt_field].replace('Z', ''), '%Y-%m-%dT%H:%M:%S')
                        except Exception:
                            _logger.warning(f"Could not parse date: {vals[dt_field]}")
                            vals[dt_field] = False
            # Create or update contact
            contact = self.sudo().search([
                ('external_id', '=', vals['external_id']),
                ('location_id', '=', installed_location.id)
            ], limit=1)
            if contact:
                contact.write(vals)
            else:
                contact = self.sudo().create(vals)
            # Handle custom fields
            custom_fields = data.get('customFields', [])
            if custom_fields:
                contact.custom_field_ids.unlink()
                for cf in custom_fields:
                    self.env['ghl.location.contact.custom.field'].sudo().create({
                        'contact_id': contact.id,
                        'custom_field_id': cf.get('id'),
                        'value': cf.get('value'),
                    })
            # Handle attributions
            for attr_key in ['attributionSource', 'lastAttributionSource']:
                attr = data.get(attr_key)
                if attr:
                    self.env['ghl.location.contact.attribution'].sudo().create({
                        'contact_id': contact.id,
                        'url': attr.get('url'),
                        'campaign': attr.get('campaign'),
                        'utm_source': attr.get('utmSource'),
                        'utm_medium': attr.get('utmMedium'),
                        'utm_content': attr.get('utmContent'),
                        'referrer': attr.get('referrer'),
                        'campaign_id': attr.get('campaignId'),
                        'fbclid': attr.get('fbclid'),
                        'gclid': attr.get('gclid'),
                        'msclikid': attr.get('msclikid'),
                        'dclid': attr.get('dclid'),
                        'fbc': attr.get('fbc'),
                        'fbp': attr.get('fbp'),
                        'fb_event_id': attr.get('fbEventId'),
                        'user_agent': attr.get('userAgent'),
                        'ip': attr.get('ip'),
                        'medium': attr.get('medium'),
                        'medium_id': attr.get('mediumId'),
                    })
            return contact
        except Exception as e:
            _logger.error(f"Error fetching single contact: {e}")
            return None
