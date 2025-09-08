# -*- coding: utf-8 -*-

from odoo import http
from odoo.http import request, Response
import json
import logging
from datetime import datetime, timedelta
from .cors_utils import get_cors_headers

_logger = logging.getLogger(__name__)


# Add your Cycl Sales dashboard controllers here


# class Custom/webScraper/common/cs-dashboard-backend(http.Controller):
#     @http.route('/custom/web_scraper/common/cs-dashboard-backend/custom/web_scraper/common/cs-dashboard-backend', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/custom/web_scraper/common/cs-dashboard-backend/custom/web_scraper/common/cs-dashboard-backend/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('custom/web_scraper/common/cs-dashboard-backend.listing', {
#             'root': '/custom/web_scraper/common/cs-dashboard-backend/custom/web_scraper/common/cs-dashboard-backend',
#             'objects': http.request.env['custom/web_scraper/common/cs-dashboard-backend.custom/web_scraper/common/cs-dashboard-backend'].search([]),
#         })

#     @http.route('/custom/web_scraper/common/cs-dashboard-backend/custom/web_scraper/common/cs-dashboard-backend/objects/<model("custom/web_scraper/common/cs-dashboard-backend.custom/web_scraper/common/cs-dashboard-backend"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('custom/web_scraper/common/cs-dashboard-backend.object', {
#             'object': obj
#         })

class DashboardController(http.Controller):

    @http.route('/api/dashboard/metrics', type='http', auth='none', methods=['GET'], csrf=False)
    def get_dashboard_metrics(self, **kwargs):
        """Get dashboard metrics including contacts, opportunities, and revenue data"""
        try:
            # Get location ID from query params
            location_id = kwargs.get('locationId', 'demo-location')

            # Get contacts count
            contacts = request.env['ghl.contact'].sudo().search([('location_id', '=', location_id)])
            total_contacts = len(contacts) if contacts else 0

            # Calculate total pipeline value
            total_pipeline_value = sum(contacts.mapped('total_pipeline_value')) if contacts else 0

            # Get opportunities count
            opportunities_count = sum(contacts.mapped('opportunities_count')) if contacts else 0

            # Calculate conversion rate (simplified)
            conversion_rate = (opportunities_count / total_contacts * 100) if total_contacts > 0 else 0

            # Calculate average deal size
            average_deal_size = (total_pipeline_value / opportunities_count) if opportunities_count > 0 else 0

            metrics = {
                'id': 1,
                'totalContacts': total_contacts or 0,
                'totalOpportunities': opportunities_count or 0,
                'totalRevenue': total_pipeline_value or 0,
                'conversionRate': round(conversion_rate, 2) if conversion_rate is not None else 0,
                'averageDealSize': round(average_deal_size, 2) if average_deal_size is not None else 0,
                'dateCalculated': datetime.now().isoformat(),
                'locationId': location_id or ''
            }

            return Response(
                json.dumps(metrics),
                content_type='application/json',
                headers=get_cors_headers(request)
            )

        except Exception as e:
            _logger.error(f"Error getting dashboard metrics: {str(e)}")
            return Response(
                json.dumps({'error': str(e)}),
                content_type='application/json',
                status=500,
                headers=get_cors_headers(request)
            )

    @http.route('/api/dashboard/contacts', type='http', auth='none', methods=['GET'], csrf=False)
    def get_contacts(self, **kwargs):
        """Get contacts list with optional filtering"""
        try:
            location_id = kwargs.get('locationId', 'demo-location')
            limit = int(kwargs.get('limit', 50))
            offset = int(kwargs.get('offset', 0))

            # Search contacts
            domain = [('location_id', '=', location_id)]
            contacts = request.env['ghl.contact'].sudo().search(domain, limit=limit, offset=offset)

            contacts_data = []
            for contact in contacts:
                contact_data = {
                    'id': contact.ghl_id,
                    'firstName': contact.first_name,
                    'lastName': contact.last_name,
                    'email': contact.email or '',
                    'phone': contact.phone or '',
                    'companyName': contact.company_name or '',
                    'source': contact.source or 'other',
                    'tags': contact.get_tags_list(),
                    'customFields': contact.custom_fields or '{}',
                    'dateCreated': contact.date_created.isoformat() if contact.date_created else None,
                    'dateUpdated': contact.date_updated.isoformat() if contact.date_updated else None,
                    'locationId': contact.location_id,
                    'aiStatus': contact.ai_status,
                    'aiSummary': contact.ai_summary,
                    'aiQualityGrade': contact.ai_quality_grade,
                    'aiSalesGrade': contact.ai_sales_grade,
                    'totalPipelineValue': contact.total_pipeline_value,
                    'opportunitiesCount': contact.opportunities_count
                }
                contacts_data.append(contact_data)

            return Response(
                json.dumps(contacts_data),
                content_type='application/json',
                headers=get_cors_headers(request)
            )

        except Exception as e:
            _logger.error(f"Error getting contacts: {str(e)}")
            return Response(
                json.dumps({'error': str(e)}),
                content_type='application/json',
                status=500,
                headers=get_cors_headers(request)
            )

    @http.route('/api/dashboard/contacts/<string:contact_id>', type='http', auth='none', methods=['GET'], csrf=False)
    def get_contact_detail(self, contact_id, **kwargs):
        """Get detailed contact information"""
        try:
            contact = request.env['ghl.contact'].sudo().search([('ghl_id', '=', contact_id)], limit=1)

            if not contact:
                return Response(
                    json.dumps({'error': 'Contact not found'}),
                    content_type='application/json',
                    status=404,
                    headers=get_cors_headers(request)
                )

            contact_data = {
                'id': contact.ghl_id,
                'firstName': contact.first_name,
                'lastName': contact.last_name,
                'email': contact.email or '',
                'phone': contact.phone or '',
                'companyName': contact.company_name or '',
                'source': contact.source or 'other',
                'tags': contact.get_tags_list(),
                'customFields': contact.custom_fields or '{}',
                'dateCreated': contact.date_created.isoformat() if contact.date_created else None,
                'dateUpdated': contact.date_updated.isoformat() if contact.date_updated else None,
                'locationId': contact.location_id,
                'assignedTo': contact.assigned_to,
                'aiStatus': contact.ai_status,
                'aiSummary': contact.ai_summary,
                'aiQualityGrade': contact.ai_quality_grade,
                'aiSalesGrade': contact.ai_sales_grade,
                'crmTasks': contact.crm_tasks,
                'category': contact.category,
                'channel': contact.channel,
                'createdBy': contact.created_by,
                'attribution': contact.attribution,
                'speedToLead': contact.speed_to_lead,
                'touchSummary': contact.touch_summary,
                'engagementSummary': contact.engagement_summary,
                'lastTouchDate': contact.last_touch_date.isoformat() if contact.last_touch_date else None,
                'totalPipelineValue': contact.total_pipeline_value,
                'opportunitiesCount': contact.opportunities_count
            }

            return Response(
                json.dumps(contact_data),
                content_type='application/json',
                headers=get_cors_headers(request)
            )

        except Exception as e:
            _logger.error(f"Error getting contact detail: {str(e)}")
            return Response(
                json.dumps({'error': str(e)}),
                content_type='application/json',
                status=500,
                headers=get_cors_headers(request)
            )

    @http.route('/api/dashboard/contacts', type='http', auth='none', methods=['POST'], csrf=False)
    def create_contact(self, **kwargs):
        """Create a new contact"""
        try:
            data = request.httprequest.get_json()

            # Validate required fields
            if not data.get('firstName') or not data.get('lastName') or not data.get('locationId'):
                return Response(
                    json.dumps({'error': 'firstName, lastName, and locationId are required'}),
                    content_type='application/json',
                    status=400,
                    headers=get_cors_headers(request)
                )

            # Create contact
            contact_vals = {
                'first_name': data['firstName'],
                'last_name': data['lastName'],
                'email': data.get('email', ''),
                'phone': data.get('phone', ''),
                'company_name': data.get('companyName', ''),
                'source': data.get('source', 'other'),
                'location_id': data['locationId'],
                'ghl_id': f"contact_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                'custom_fields': data.get('customFields', '{}')
            }

            contact = request.env['ghl.contact'].sudo().create(contact_vals)

            # Add tags if provided
            if data.get('tags'):
                for tag_name in data['tags']:
                    contact.add_tag(tag_name)

            return Response(
                json.dumps({'success': True, 'contactId': contact.ghl_id}),
                content_type='application/json',
                status=201,
                headers=get_cors_headers(request)
            )

        except Exception as e:
            _logger.error(f"Error creating contact: {str(e)}")
            return Response(
                json.dumps({'error': str(e)}),
                content_type='application/json',
                status=500,
                headers=get_cors_headers(request)
            )

    @http.route('/api/dashboard/contacts/<string:contact_id>', type='http', auth='none', methods=['PUT'], csrf=False)
    def update_contact(self, contact_id, **kwargs):
        """Update an existing contact"""
        try:
            contact = request.env['ghl.contact'].sudo().search([('ghl_id', '=', contact_id)], limit=1)

            if not contact:
                return Response(
                    json.dumps({'error': 'Contact not found'}),
                    content_type='application/json',
                    status=404,
                    headers=get_cors_headers(request)
                )

            data = request.httprequest.get_json()

            # Update fields
            update_vals = {}
            if 'firstName' in data:
                update_vals['first_name'] = data['firstName']
            if 'lastName' in data:
                update_vals['last_name'] = data['lastName']
            if 'email' in data:
                update_vals['email'] = data['email']
            if 'phone' in data:
                update_vals['phone'] = data['phone']
            if 'companyName' in data:
                update_vals['company_name'] = data['companyName']
            if 'source' in data:
                update_vals['source'] = data['source']
            if 'customFields' in data:
                update_vals['custom_fields'] = data['customFields']

            contact.write(update_vals)

            # Update tags if provided
            if 'tags' in data:
                # Clear existing tags and add new ones
                contact.tags = [(5, 0, 0)]  # Clear all tags
                for tag_name in data['tags']:
                    contact.add_tag(tag_name)

            return Response(
                json.dumps({'success': True}),
                content_type='application/json',
                headers=get_cors_headers(request)
            )

        except Exception as e:
            _logger.error(f"Error updating contact: {str(e)}")
            return Response(
                json.dumps({'error': str(e)}),
                content_type='application/json',
                status=500,
                headers=get_cors_headers(request)
            )

    @http.route('/api/dashboard/analytics/call-volume', type='http', auth='none', methods=['GET'], csrf=False)
    def get_call_volume_analytics(self, **kwargs):
        """Get raw call data for analytics"""
        try:
            location_id = kwargs.get('locationId', 'location_id')

            # If no specific location or demo location, get all call records
            if not location_id or location_id == 'demo-location':
                domain = [('message_type', '=', 'TYPE_CALL')]
            else:
                domain = [
                    ('location_id.location_id', '=', location_id),
                    ('message_type', '=', 'TYPE_CALL')
                ]

            # Get call messages by location for analytics (same data source as call table)
            call_messages = request.env['ghl.contact.message'].sudo().search(domain)

            # Return raw call data for frontend processing
            raw_data = []
            for call in call_messages:
                # Calculate duration from transcript if meta_id.call_duration is not available
                calculated_duration = None
                if call.meta_id and call.meta_id.call_duration:
                    calculated_duration = call.meta_id.call_duration
                else:
                    # Try to calculate from transcript data
                    transcript_records = request.env['ghl.contact.message.transcript'].sudo().search([
                        ('message_id', '=', call.id)
                    ])
                    if transcript_records:
                        calculated_duration = sum(t.duration for t in transcript_records if t.duration)
                
                # Get user name from user_id
                user_name = None
                if call.user_id:
                    try:
                        user_name = call.user_id.name if hasattr(call.user_id, 'name') else str(call.user_id)
                    except:
                        user_name = str(call.user_id)
                
                call_data = {
                    'id': call.id,
                    'direction': call.direction,
                    'user_id': user_name,
                    'date_added': call.date_added.isoformat() if call.date_added else None,
                    'meta': {
                        'call_duration': calculated_duration
                    },
                    'contact_id': {
                        'id': call.contact_id.id if call.contact_id else None,
                        'source': call.contact_id.source if call.contact_id and call.contact_id.source else 'Unknown Source',
                        'name': call.contact_id.name if call.contact_id else None
                    } if call.contact_id else None
                }
                raw_data.append(call_data)
            return Response(
                json.dumps(raw_data),
                content_type='application/json',
                headers=get_cors_headers(request)
            )

        except Exception as e:
            _logger.error(f"Error getting call volume analytics: {str(e)}")
            return Response(
                json.dumps({'error': str(e)}),
                content_type='application/json',
                status=500,
                headers=get_cors_headers(request)
            )

    @http.route('/api/dashboard/analytics/engagement', type='http', auth='none', methods=['GET'], csrf=False)
    def get_engagement_analytics(self, **kwargs):
        """Get raw call data for engagement analytics"""
        try:
            location_id = kwargs.get('locationId', 'demo-location')

            # If no specific location or demo location, get all call records
            if not location_id or location_id == 'demo-location':
                domain = [('message_type', '=', 'TYPE_CALL')]
            else:
                domain = [
                    ('location_id.location_id', '=', location_id),
                    ('message_type', '=', 'TYPE_CALL')
                ]

            # Get call messages by location for engagement analysis (same data source as call table)
            call_messages = request.env['ghl.contact.message'].sudo().search(domain)

            # Return raw call data for frontend processing
            raw_data = []
            for call in call_messages:
                # Calculate duration from transcript if meta_id.call_duration is not available
                calculated_duration = None
                if call.meta_id and call.meta_id.call_duration:
                    calculated_duration = call.meta_id.call_duration
                else:
                    # Try to calculate from transcript data
                    transcript_records = request.env['ghl.contact.message.transcript'].sudo().search([
                        ('message_id', '=', call.id)
                    ])
                    if transcript_records:
                        calculated_duration = sum(t.duration for t in transcript_records if t.duration)
                
                # Get user name from user_id
                user_name = None
                if call.user_id:
                    try:
                        user_name = call.user_id.name if hasattr(call.user_id, 'name') else str(call.user_id)
                    except:
                        user_name = str(call.user_id)
                
                call_data = {
                    'id': call.id,
                    'direction': call.direction,
                    'user_id': user_name,
                    'date_added': call.date_added.isoformat() if call.date_added else None,
                    'meta': {
                        'call_duration': calculated_duration
                    },
                    'contact_id': {
                        'id': call.contact_id.id if call.contact_id else None,
                        'source': call.contact_id.source if call.contact_id and call.contact_id.source else 'Unknown Source',
                        'name': call.contact_id.name if call.contact_id else None
                    } if call.contact_id else None
                }
                raw_data.append(call_data) 
 
            return Response(
                json.dumps(raw_data),
                content_type='application/json',
                headers=get_cors_headers(request)
            )

        except Exception as e:
            _logger.error(f"Error getting engagement analytics: {str(e)}")
            return Response(
                json.dumps({'error': str(e)}),
                content_type='application/json',
                status=500,
                headers=get_cors_headers(request)
            )

    @http.route('/api/dashboard/analytics/pipeline', type='http', auth='none', methods=['GET'], csrf=False)
    def get_pipeline_analytics(self, **kwargs):
        """Get pipeline analytics data"""
        try:
            location_id = kwargs.get('locationId', 'demo-location')

            # Get contacts with pipeline values
            contacts = request.env['ghl.contact'].sudo().search([
                ('location_id', '=', location_id),
                ('total_pipeline_value', '>', 0)
            ])

            # Calculate monthly pipeline values (simplified)
            pipeline_data = []
            for i in range(6):
                month_date = datetime.now() - timedelta(days=30 * i)
                month_name = month_date.strftime('%b')

                # Calculate pipeline value for this month (simplified calculation)
                monthly_value = sum(contacts.mapped('total_pipeline_value')) / 6

                pipeline_data.append({
                    'month': month_name,
                    'value': f"{monthly_value:.2f}",
                    'date': month_date.isoformat()
                })

            return Response(
                json.dumps(pipeline_data),
                content_type='application/json',
                headers=get_cors_headers(request)
            )

        except Exception as e:
            _logger.error(f"Error getting pipeline analytics: {str(e)}")
            return Response(
                json.dumps({'error': str(e)}),
                content_type='application/json',
                status=500,
                headers=get_cors_headers(request)
            )


class CORSPreflightController(http.Controller):
    @http.route('/api/dashboard/<path:anything>', type='http', auth='none', methods=['OPTIONS'], csrf=False)
    def cors_preflight(self, **kwargs):
        return Response(
            "",
            status=200,
            headers=get_cors_headers(request)
        )
