# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import datetime
import json

# Add your Cycl Sales dashboard models here


# class custom/web_scraper/common/cs-dashboard-backend(models.Model):
#     _name = 'custom/web_scraper/common/cs-dashboard-backend.custom/web_scraper/common/cs-dashboard-backend'
#     _description = 'custom/web_scraper/common/cs-dashboard-backend.custom/web_scraper/common/cs-dashboard-backend'

#     name = fields.Char()
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         for record in self:
#             record.value2 = float(record.value) / 100

class GhlContact(models.Model):
    _name = 'ghl.contact'
    _description = 'GoHighLevel Contact'
    _order = 'date_created desc'

    # Basic Contact Information
    name = fields.Char(string='Full Name', compute='_compute_name', store=True)
    first_name = fields.Char(string='First Name', required=True)
    last_name = fields.Char(string='Last Name', required=True)
    email = fields.Char(string='Email')
    phone = fields.Char(string='Phone')
    company_name = fields.Char(string='Company Name')
    
    # Source and Classification
    source = fields.Selection([
        ('website', 'Website'),
        ('referral', 'Referral'),
        ('social_media', 'Social Media'),
        ('email_campaign', 'Email Campaign'),
        ('phone', 'Phone'),
        ('other', 'Other')
    ], string='Source', default='other')
    
    # Tags and Custom Fields
    tags = fields.Many2many('ghl.tag', string='Tags')
    custom_fields = fields.Text(string='Custom Fields (JSON)')
    
    # Location and Assignment
    location_id = fields.Char(string='Location ID', required=True)
    assigned_to = fields.Char(string='Assigned To')
    
    # AI Analysis Fields (from analytics table)
    ai_status = fields.Selection([
        ('analyzed', 'Analyzed'),
        ('pending', 'Pending'),
        ('failed', 'Failed')
    ], string='AI Status', default='pending')
    
    ai_summary = fields.Text(string='AI Summary')
    ai_quality_grade = fields.Selection([
        ('A', 'A'),
        ('B', 'B'),
        ('C', 'C'),
        ('D', 'D'),
        ('F', 'F')
    ], string='AI Quality Grade')
    
    ai_sales_grade = fields.Selection([
        ('A', 'A'),
        ('B', 'B'),
        ('C', 'C'),
        ('D', 'D'),
        ('F', 'F')
    ], string='AI Sales Grade')
    
    # CRM and Engagement
    crm_tasks = fields.Text(string='CRM Tasks')
    category = fields.Char(string='Category')
    channel = fields.Char(string='Channel')
    created_by = fields.Char(string='Created By')
    attribution = fields.Char(string='Attribution')
    speed_to_lead = fields.Char(string='Speed to Lead')
    touch_summary = fields.Text(string='Touch Summary')
    engagement_summary = fields.Text(string='Engagement Summary')
    last_touch_date = fields.Datetime(string='Last Touch Date')
    
    # Pipeline and Revenue
    total_pipeline_value = fields.Float(string='Total Pipeline Value', digits=(10, 2))
    opportunities_count = fields.Integer(string='Opportunities Count', default=0)
    
    # Timestamps
    date_created = fields.Datetime(string='Date Created', default=fields.Datetime.now)
    date_updated = fields.Datetime(string='Date Updated', default=fields.Datetime.now)
    
    # External ID
    ghl_id = fields.Char(string='GHL Contact ID', required=True)
    
    # Computed fields
    @api.depends('first_name', 'last_name')
    def _compute_name(self):
        for record in self:
            if record.first_name and record.last_name:
                record.name = f"{record.first_name} {record.last_name}"
            elif record.first_name:
                record.name = record.first_name
            elif record.last_name:
                record.name = record.last_name
            else:
                record.name = "Unknown"
    
    # Methods
    def get_custom_field_value(self, field_name):
        """Get value from custom_fields JSON"""
        if self.custom_fields:
            try:
                custom_data = json.loads(self.custom_fields)
                return custom_data.get(field_name)
            except json.JSONDecodeError:
                return None
        return None
    
    def set_custom_field_value(self, field_name, value):
        """Set value in custom_fields JSON"""
        custom_data = {}
        if self.custom_fields:
            try:
                custom_data = json.loads(self.custom_fields)
            except json.JSONDecodeError:
                custom_data = {}
        
        custom_data[field_name] = value
        self.custom_fields = json.dumps(custom_data)
    
    def get_tags_list(self):
        """Get tags as a list of strings"""
        return [tag.name for tag in self.tags]
    
    def add_tag(self, tag_name):
        """Add a tag to the contact"""
        tag = self.env['ghl.tag'].search([('name', '=', tag_name)], limit=1)
        if not tag:
            tag = self.env['ghl.tag'].create({'name': tag_name})
        self.tags = [(4, tag.id)]

class GhlTag(models.Model):
    _name = 'ghl.tag'
    _description = 'GoHighLevel Tag'
    
    name = fields.Char(string='Tag Name', required=True)
    color = fields.Char(string='Color', default='#3B82F6')
    description = fields.Text(string='Description')
    
    # Relations
    contact_ids = fields.Many2many('ghl.contact', string='Contacts')

