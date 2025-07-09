from odoo import http
from odoo.http import request, Response
import json
import logging
from .cors_utils import get_cors_headers

_logger = logging.getLogger(__name__)


class InstalledLocationController(http.Controller):
    @http.route('/api/installed-locations', type='http', auth='none', methods=['GET', 'OPTIONS'], csrf=False)
    def get_installed_locations(self, **kwargs):
        _logger.info(f"InstalledLocationController.get_installed_locations called with kwargs: {kwargs}")

        # Handle preflight OPTIONS request
        if request.httprequest.method == 'OPTIONS':
            return Response(
                status=200,
                headers=get_cors_headers(request)
            )

        # Get app_id from parameters or use default
        app_id = kwargs.get('appId', '6867d1537079188afca5013c')
        _logger.info(f"Using app_id: {app_id}")

        # Hardcode company_id
        company_id = 'Ipg8nKDPLYKsbtodR6LN'
        _logger.info(f"Using hardcoded company_id: {company_id}")

        # Call the fetch_installed_locations function from the model
        installed_location_model = request.env['installed.location'].sudo()
        _logger.info(f"Calling fetch_installed_locations with company_id={company_id}, app_id={app_id}")
        result = installed_location_model.fetch_installed_locations(
            company_id=company_id,
            app_id=app_id,
            limit=500
        )
        _logger.info(f"fetch_installed_locations result: {result}")
        if not result.get('success'):
            _logger.error(f"Failed to fetch installed locations: {result.get('error')}")
            return Response(
                json.dumps({'error': result.get('error', 'Failed to fetch installed locations')}),
                content_type='application/json',
                status=400,
                headers=get_cors_headers(request)
            )
        # Get the updated locations from the database
        locations = request.env['installed.location'].sudo().search([
            ('app_id', '=', app_id)
        ])
        data = []
        mock_defaults = {
            'automationGroup': 'Template: Generic Default',
            'adAccounts': 3,
            'totalAdSpend': '$123.45',
            'costPerConversion': '12%',
            'newContacts': 150,
            'newContactsChange': '+10%',
            'medianAIQualityGrade': 'Lead Grade B (4/5)',
            'medianAIQualityGradeColor': 'bg-green-700 text-green-300',
            'touchRate': '1.23%',
            'touchRateChange': '+5%',
            'engagementRate': '45.67%',
            'engagementRateChange': '+8%',
            'speedToLead': '30%',
            'medianAISalesGrade': 'Sales Grade C (3/5)',
            'medianAISalesGradeColor': 'bg-yellow-700 text-yellow-300',
            'closeRate': '2.34%',
            'revenuePerContact': '$56.78',
            'grossROAS': '80%',
        }
        for loc in locations:
            data.append({
                'location_id': loc.location_id or '',
                'location': loc.name or '',
                'automationGroup': loc.automation_group or mock_defaults['automationGroup'],
                'adAccounts': loc.ad_accounts if loc.ad_accounts not in [None, '', 0] else mock_defaults['adAccounts'],
                'totalAdSpend': loc.total_ad_spend or mock_defaults['totalAdSpend'],
                'costPerConversion': loc.cost_per_conversion or mock_defaults['costPerConversion'],
                'newContacts': loc.new_contacts if loc.new_contacts not in [None, '', 0] else mock_defaults[
                    'newContacts'],
                'newContactsChange': loc.new_contacts_change or mock_defaults['newContactsChange'],
                'medianAIQualityGrade': loc.median_ai_quality_grade or mock_defaults['medianAIQualityGrade'],
                'medianAIQualityGradeColor': loc.median_ai_quality_grade_color or mock_defaults[
                    'medianAIQualityGradeColor'],
                'touchRate': loc.touch_rate or mock_defaults['touchRate'],
                'touchRateChange': loc.touch_rate_change or mock_defaults['touchRateChange'],
                'engagementRate': loc.engagement_rate or mock_defaults['engagementRate'],
                'engagementRateChange': loc.engagement_rate_change or mock_defaults['engagementRateChange'],
                'speedToLead': loc.speed_to_lead or mock_defaults['speedToLead'],
                'medianAISalesGrade': loc.median_ai_sales_grade or mock_defaults['medianAISalesGrade'],
                'medianAISalesGradeColor': loc.median_ai_sales_grade_color or mock_defaults['medianAISalesGradeColor'],
                'closeRate': loc.close_rate or mock_defaults['closeRate'],
                'revenuePerContact': loc.revenue_per_contact or mock_defaults['revenuePerContact'],
                'grossROAS': loc.gross_roas or mock_defaults['grossROAS'],
            })
        # Log the data for debugging
        request.env['ir.logging'].sudo().create({
            'name': 'InstalledLocationController',
            'type': 'server',
            'level': 'info',
            'dbname': request.env.cr.dbname,
            'message': f"Fetched installed locations: {json.dumps(data)}",
            'path': __file__,
            'func': 'get_installed_locations',
            'line': 0,
        })
        return Response(
            json.dumps({'locations': data}),
            content_type='application/json',
            status=200,
            headers=get_cors_headers(request)
        )

    @http.route('/api/get-location-users', type='http', auth='none', methods=['GET', 'OPTIONS'], csrf=False)
    def get_location_users(self, **kwargs):
        _logger.info(f"get_location_users called with kwargs: {kwargs}")
        if request.httprequest.method == 'OPTIONS':
            return Response(status=200, headers=get_cors_headers(request))
        location_id = kwargs.get('location_id')
        if not location_id:
            return Response(json.dumps({'success': False, 'error': 'location_id is required'}),
                            content_type='application/json', status=400, headers=get_cors_headers(request))
        app_id = '6867d1537079188afca5013c'
        company_id = 'Ipg8nKDPLYKsbtodR6LN'
        # Get agency access token (same as fetch_location_details logic)
        app = request.env['cyclsales.application'].sudo().search([
            ('app_id', '=', app_id),
            ('is_active', '=', True)
        ], limit=1)
        if not app or not app.access_token:
            return Response(json.dumps({'success': False, 'error': 'No valid access token found for this app_id.'}),
                            content_type='application/json', status=400, headers=get_cors_headers(request))
        access_token = app.access_token
        # Find the installed.location record
        loc = request.env['installed.location'].sudo().search([('location_id', '=', location_id)], limit=1)
        if not loc:
            return Response(json.dumps({'success': False, 'error': 'Location not found'}),
                            content_type='application/json', status=404, headers=get_cors_headers(request))
        # Call the fetch_location_users method
        result = loc.fetch_location_users(company_id, location_id, access_token)
        if result and result.get('success'):
            return Response(
                json.dumps({
                    'success': True,
                    'message': f"User data fetched and processed. {result.get('created_count', 0)} users created, {result.get('updated_count', 0)} users updated.",
                    'created_count': result.get('created_count', 0),
                    'updated_count': result.get('updated_count', 0),
                    'total_users': result.get('total_users', 0)
                }),
                content_type='application/json',
                status=200,
                headers=get_cors_headers(request)
            )
        else:
            return Response(
                json.dumps({
                    'success': False,
                    'error': 'Failed to fetch and process user data'
                }),
                content_type='application/json',
                status=500,
                headers=get_cors_headers(request)
            )

    @http.route('/api/location-users', type='http', auth='none', methods=['GET', 'OPTIONS'], csrf=False)
    def get_location_users_from_db(self, **kwargs):
        _logger.info(f"get_location_users_from_db called with kwargs: {kwargs}")
        if request.httprequest.method == 'OPTIONS':
            return Response(status=200, headers=get_cors_headers(request))

        location_id = kwargs.get('location_id')
        if not location_id:
            return Response(
                json.dumps({'success': False, 'error': 'location_id is required'}),
                content_type='application/json',
                status=400,
                headers=get_cors_headers(request)
            )

        # Fetch users from our database
        users = request.env['ghl.location.user'].sudo().search([
            ('location_id', '=', location_id),
            ('deleted', '=', False)  # Only non-deleted users
        ])

        user_data = []
        for user in users:
            user_info = {
                'id': user.id,
                'external_id': user.external_id,
                'name': user.name or '',
                'first_name': user.first_name or '',
                'last_name': user.last_name or '',
                'email': user.email or '',
                'phone': user.phone or '',
                'extension': user.extension or '',
                'scopes': user.scopes or '',
                'role': user.roles_id.role if user.roles_id else '',
                'role_type': user.roles_id.type if user.roles_id else '',
                'permissions': {}
            }

            # Add permissions if available
            if user.permissions_id:
                permissions = user.permissions_id
                user_info['permissions'] = {
                    'campaigns_enabled': permissions.campaigns_enabled,
                    'contacts_enabled': permissions.contacts_enabled,
                    'workflows_enabled': permissions.workflows_enabled,
                    'opportunities_enabled': permissions.opportunities_enabled,
                    'dashboard_stats_enabled': permissions.dashboard_stats_enabled,
                    'appointments_enabled': permissions.appointments_enabled,
                    'conversations_enabled': permissions.conversations_enabled,
                    'settings_enabled': permissions.settings_enabled,
                    'marketing_enabled': permissions.marketing_enabled,
                }

            user_data.append(user_info)

        return Response(
            json.dumps({
                'success': True,
                'users': user_data,
                'total_users': len(user_data)
            }),
            content_type='application/json',
            status=200,
            headers=get_cors_headers(request)
        )

    @http.route('/api/get-location-contacts', type='http', auth='none', methods=['GET', 'OPTIONS'], csrf=False)
    def get_location_contacts(self, **kwargs):
        _logger.info(f"get_location_contacts called with kwargs: {kwargs}")
        if request.httprequest.method == 'OPTIONS':
            return Response(status=200, headers=get_cors_headers(request))
        location_id = kwargs.get('location_id')
        if not location_id:
            return Response(json.dumps({'success': False, 'error': 'location_id is required'}),
                            content_type='application/json', status=400, headers=get_cors_headers(request))
        app_id = '6867d1537079188afca5013c'
        company_id = 'Ipg8nKDPLYKsbtodR6LN'
        # Get agency access token (same as fetch_location_details logic)
        app = request.env['cyclsales.application'].sudo().search([
            ('app_id', '=', app_id),
            ('is_active', '=', True)
        ], limit=1)
        if not app or not app.access_token:
            return Response(json.dumps({'success': False, 'error': 'No valid access token found for this app_id.'}),
                            content_type='application/json', status=400, headers=get_cors_headers(request))
        access_token = app.access_token
        # Find the installed.location record
        loc = request.env['installed.location'].sudo().search([('location_id', '=', location_id)], limit=1)
        if not loc:
            return Response(json.dumps({'success': False, 'error': 'Location not found'}),
                            content_type='application/json', status=404, headers=get_cors_headers(request))
        # Call the fetch_location_contacts method
        result = loc.fetch_location_contacts(company_id, location_id, access_token)

        # Sync GHL tasks for all contacts in this location (fetch from API and update Odoo)
        task_sync_result = request.env['ghl.contact.task'].sudo().sync_all_contact_tasks(access_token, location_id, company_id)
        _logger.info(f"[get-location-contacts] GHL contact task sync result: {json.dumps(task_sync_result)}")

        # Sync GHL conversations for this location
        _logger.info(f"Starting conversation sync for location: {location_id}")
        conversation_sync_result = {'success': False, 'message': 'No sync attempted'}
        
        try:
            # Call conversation sync method using the same agency token
            conversation_sync_result = request.env['ghl.contact.conversation'].sudo().sync_conversations_for_location(
                access_token,
                location_id,
                company_id
            )
            
            if conversation_sync_result['success']:
                _logger.info(f"Conversation sync successful: {conversation_sync_result['message']}")
            else:
                _logger.error(f"Conversation sync failed: {conversation_sync_result['message']}")
        except Exception as e:
            _logger.error(f"Error during conversation sync: {str(e)}")
            conversation_sync_result = {'success': False, 'message': f'Sync error: {str(e)}'}

        # Sync GHL opportunities for this location
        _logger.info(f"Starting opportunity sync for location: {location_id}")
        opportunity_sync_result = {'success': False, 'message': 'No sync attempted'}
        try:
            opportunity_sync_result = request.env['ghl.contact.opportunity'].sudo().sync_opportunities_for_location(
                access_token,
                location_id,
                company_id
            )
            if opportunity_sync_result.get('success', False):
                _logger.info(f"Opportunity sync successful: {opportunity_sync_result}")
            else:
                _logger.error(f"Opportunity sync failed: {opportunity_sync_result}")
        except Exception as e:
            _logger.error(f"Error during opportunity sync: {str(e)}")
            opportunity_sync_result = {'success': False, 'message': f'Sync error: {str(e)}'}

        if result and result.get('success'):
            return Response(
                json.dumps({
                    'success': True,
                    'message': f"Contact data fetched and processed. {result.get('created_count', 0)} contacts created, {result.get('updated_count', 0)} contacts updated.",
                    'created_count': result.get('created_count', 0),
                    'updated_count': result.get('updated_count', 0),
                    'total_contacts': result.get('total_contacts', 0),
                    'task_sync': task_sync_result,  # Include GHL sync result for debugging
                    'conversation_sync': conversation_sync_result,  # Include conversation sync result for debugging
                    'opportunity_sync': opportunity_sync_result,  # Include opportunity sync result for debugging
                }),
                content_type='application/json',
                status=200,
                headers=get_cors_headers(request)
            )
        else:
            return Response(
                json.dumps({
                    'success': False,
                    'error': 'Failed to fetch and process contact data',
                    'task_sync': task_sync_result,  # Include GHL sync result for debugging
                    'conversation_sync': conversation_sync_result,  # Include conversation sync result for debugging
                    'opportunity_sync': opportunity_sync_result,  # Include opportunity sync result for debugging
                }),
                content_type='application/json',
                status=500,
                headers=get_cors_headers(request)
            )

    @http.route('/api/location-contacts', type='http', auth='none', methods=['GET', 'OPTIONS'], csrf=False)
    def get_location_contacts_from_db(self, **kwargs):
        _logger.info(f"get_location_contacts_from_db called with kwargs: {kwargs}")
        if request.httprequest.method == 'OPTIONS':
            return Response(status=200, headers=get_cors_headers(request))

        location_id = kwargs.get('location_id')
        if not location_id:
            import json
            return Response(
                json.dumps({'success': False, 'error': 'location_id is required'}),
                content_type='application/json',
                status=400,
                headers=get_cors_headers(request)
            ) 
        # Always sync contacts and tasks from GHL API before returning data
        app_id = '6867d1537079188afca5013c'
        company_id = 'Ipg8nKDPLYKsbtodR6LN'
        app = request.env['cyclsales.application'].sudo().search([
            ('app_id', '=', app_id),
            ('is_active', '=', True)
        ], limit=1)
        if app and app.access_token:
            access_token = app.access_token
            loc = request.env['installed.location'].sudo().search([('location_id', '=', location_id)], limit=1)
            if loc:
                # Sync contacts (fetches from GHL and updates Odoo DB)
                loc.fetch_location_contacts(company_id, location_id, access_token)
                # Sync tasks for all contacts
                request.env['ghl.contact.task'].sudo().sync_all_contact_tasks(access_token, location_id, company_id)

        # Fetch contacts from our database
        contacts = request.env['ghl.location.contact'].sudo().search([
            ('location_id.location_id', '=', location_id)
        ])

        # Log the number of contacts and their external_ids for debugging
        _logger.info(f"[location-contacts] Found {len(contacts)} contacts for location_id={location_id}")
        if contacts:
            _logger.info(f"[location-contacts] Contact external_ids: {[c.external_id for c in contacts]}")

        contact_data = []
        for contact in contacts:
            # Parse engagement summary and last message from JSON if they exist
            engagement_summary = []
            last_message = []

            if contact.engagement_summary:
                try:
                    import json
                    engagement_summary = json.loads(contact.engagement_summary)
                except:
                    engagement_summary = []

            if contact.last_message:
                try:
                    import json
                    last_message = json.loads(contact.last_message)
                except:
                    last_message = []

            # Parse tags
            contact_tags = []
            if contact.tags:
                try:
                    import json
                    contact_tags = json.loads(contact.tags)
                    if not isinstance(contact_tags, list):
                        contact_tags = [contact_tags]
                except:
                    contact_tags = []

            assigned_user_name = contact.assigned_to or ''
            if contact.assigned_to:
                _logger.info(f"Looking up assigned user with external_id: {contact.assigned_to}")
                assigned_user = request.env['ghl.location.user'].sudo().search([
                    ('external_id', '=', contact.assigned_to)
                ], limit=1)
                if assigned_user:
                    assigned_user_name = assigned_user.name or f"{assigned_user.first_name or ''} {assigned_user.last_name or ''}".strip()
                    _logger.info(f"Found assigned user: {assigned_user_name}")
                else:
                    _logger.warning(f"No user found with external_id: {contact.assigned_to}")
            
            # Fetch tasks for this contact
            tasks = request.env['ghl.contact.task'].sudo().search([
                ('contact_id', '=', contact.id)
            ])
            
            tasks_data = []
            for task in tasks:
                tasks_data.append({
                    'id': task.id,
                    'external_id': task.external_id,
                    'title': task.title,
                    'body': task.body or '',
                    'due_date': task.due_date.isoformat() if task.due_date else '',
                    'completed': task.completed,
                    'is_overdue': task.is_overdue,
                    'days_until_due': task.days_until_due,
                    'assigned_to': task.assigned_to or '',
                    'assigned_user_name': task.assigned_user_id.name if task.assigned_user_id else '',
                    'create_date': task.create_date.isoformat() if task.create_date else '',
                    'write_date': task.write_date.isoformat() if task.write_date else '',
                })
            
            # Fetch conversations for this contact
            conversations = request.env['ghl.contact.conversation'].sudo().search([
                ('contact_id', '=', contact.id)
            ])
            
            conversations_data = []
            for conversation in conversations:
                conversations_data.append({
                    'id': conversation.id,
                    'ghl_id': conversation.ghl_id,
                    'last_message_body': conversation.last_message_body or '',
                    'last_message_type': conversation.last_message_type or '',
                    'type': conversation.type or '',
                    'unread_count': conversation.unread_count or 0,
                    'full_name': conversation.full_name or '',
                    'contact_name': conversation.contact_name or '',
                    'email': conversation.email or '',
                    'phone': conversation.phone or '',
                    'display_name': conversation.display_name or '',
                    'create_date': conversation.create_date.isoformat() if conversation.create_date else '',
                    'write_date': conversation.write_date.isoformat() if conversation.write_date else '',
                })
            
            contact_info = {
                'id': contact.id,
                'external_id': contact.external_id,
                'name': contact.name or '',
                'email': contact.email or '',
                'timezone': contact.timezone or '',
                'country': contact.country or '',
                'source': contact.source or '',
                'date_added': contact.date_added.isoformat() if contact.date_added else '',
                'business_id': contact.business_id or '',
                'followers': contact.followers or '',
                'tag_list': contact.tag_list or '',
                'custom_fields_count': len(contact.custom_field_ids),
                'attributions_count': len(contact.attribution_ids),
                # AI and analytics fields for frontend table
                'ai_status': contact.ai_status or 'not_contacted',
                'ai_summary': contact.ai_summary or 'Read',
                'ai_quality_grade': contact.ai_quality_grade or 'no_grade',
                'ai_sales_grade': contact.ai_sales_grade or 'no_grade',
                'crm_tasks': contact.crm_tasks or 'no_tasks',
                'category': contact.category or 'manual',
                'channel': contact.channel or 'manual',
                'created_by': contact.created_by or '',
                'attribution': contact.attribution or '',
                'assigned_to': assigned_user_name,
                'speed_to_lead': contact.speed_to_lead or '',
                'touch_summary': contact.touch_summary or 'no_touches',
                'engagement_summary': engagement_summary,
                'last_touch_date': contact.last_touch_date.isoformat() if contact.last_touch_date else '',
                'last_message': last_message,
                'total_pipeline_value': contact.total_pipeline_value or 0.0,
                'opportunities': contact.opportunities or 0,
                'contact_tags': contact_tags,
                # Add tasks data
                'tasks': tasks_data,
                'tasks_count': len(tasks_data),
                # Add conversations data
                'conversations': conversations_data,
                'conversations_count': len(conversations_data),
            }

            # Add custom fields if available
            if contact.custom_field_ids:
                contact_info['custom_fields'] = []
                for cf in contact.custom_field_ids:
                    contact_info['custom_fields'].append({
                        'id': cf.custom_field_id,
                        'value': cf.value,
                    })

            # Add attributions if available
            if contact.attribution_ids:
                contact_info['attributions'] = []
                for attr in contact.attribution_ids:
                    contact_info['attributions'].append({
                        'url': attr.url or '',
                        'campaign': attr.campaign or '',
                        'utm_source': attr.utm_source or '',
                        'utm_medium': attr.utm_medium or '',
                        'referrer': attr.referrer or '',
                        'ip': attr.ip or '',
                        'medium': attr.medium or '',
                    })

            contact_data.append(contact_info)
        import json
        return Response(
            json.dumps({
                'success': True,
                'contacts': contact_data,
                'total_contacts': len(contact_data)
            }),
            content_type='application/json',
            status=200,
            headers=get_cors_headers(request)
        )

    @http.route('/api/location-name', type='http', auth='none', methods=['GET', 'OPTIONS'], csrf=False)
    def get_location_name(self, **kwargs):
        if request.httprequest.method == 'OPTIONS':
            return Response(status=200, headers=get_cors_headers(request))
        location_id = kwargs.get('location_id')
        if not location_id:
            return Response(json.dumps({'success': False, 'error': 'location_id is required'}),
                            content_type='application/json', status=400, headers=get_cors_headers(request))
        loc = request.env['installed.location'].sudo().search([('location_id', '=', location_id)], limit=1)
        if not loc:
            return Response(json.dumps({'success': False, 'error': 'Location not found'}),
                            content_type='application/json', status=404, headers=get_cors_headers(request))
        return Response(json.dumps({'success': True, 'location_id': location_id, 'name': loc.name or ''}),
                        content_type='application/json', status=200, headers=get_cors_headers(request))
