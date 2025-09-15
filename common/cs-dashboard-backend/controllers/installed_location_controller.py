from odoo import http, api, SUPERUSER_ID
from odoo.http import request, Response
import json
import logging
from .cors_utils import get_cors_headers
import threading
import time

_logger = logging.getLogger(__name__)


class InstalledLocationController(http.Controller):

    def _get_app_id_from_request(self, kwargs):
        """Helper method to get app_id from request parameters with fallback"""
        app_id = kwargs.get('appId') or '6867d1537079188afca5013c'  # Default fallback
        return app_id

    @http.route('/api/installed-locations', type='http', auth='none', methods=['GET', 'OPTIONS'], csrf=False)
    def get_installed_locations(self, **kwargs):
        """
        Fast version that returns cached data immediately and triggers background sync
        """
        # Handle preflight OPTIONS request
        if request.httprequest.method == 'OPTIONS':
            return Response(
                status=200,
                headers=get_cors_headers(request)
            )

        # Get app_id from parameters or use default
        app_id = kwargs.get('appId', '6867d1537079188afca5013c')

        # Hardcode company_id
        company_id = 'Ipg8nKDPLYKsbtodR6LN'

        # Capture database name before starting background thread
        dbname = request.env.cr.dbname

        # Start background sync in a separate thread (non-blocking)
        def background_sync():
            # Create a new database cursor for the background thread
            from odoo import api, SUPERUSER_ID
            from odoo.modules.registry import Registry
            import time
            from datetime import datetime

            # Use the captured dbname instead of accessing request
            current_dbname = dbname

            max_retries = 3
            retry_delay = 2  # seconds

            # Small delay to avoid immediate concurrency with main request
            time.sleep(0.5)

            # Set sync status to "in_progress"
            try:
                registry = Registry(current_dbname)
                with registry.cursor() as cr:
                    env = api.Environment(cr, SUPERUSER_ID, {})
                    config = env['res.config.settings'].sudo().search([], limit=1)
                    if not config:
                        config = env['res.config.settings'].sudo().create({})
                    config.write({
                        'ghl_locations_sync_status': 'in_progress',
                        'ghl_locations_sync_started': datetime.now(),
                        'ghl_locations_sync_app_id': app_id
                    })
                    cr.commit()
            except Exception as e:
                _logger.error('Error setting sync status: %s', str(e))

            for attempt in range(max_retries):
                try:
                    # Get the registry and create a new environment with a fresh cursor
                    registry = Registry(current_dbname)
                    with registry.cursor() as cr:
                        # Create a new environment with the fresh cursor
                        env = api.Environment(cr, SUPERUSER_ID, {})

                        # Call the fetch_installed_locations function from the model
                        installed_location_model = env['installed.location'].sudo()
                        result = installed_location_model.fetch_installed_locations(
                            company_id=company_id,
                            app_id=app_id,
                            limit=500
                        )

                        # Update sync status to "completed"
                        config = env['res.config.settings'].sudo().search([], limit=1)
                        if not config:
                            config = env['res.config.settings'].sudo().create({})
                        config.write({
                            'ghl_locations_sync_status': 'completed',
                            'ghl_locations_sync_completed': datetime.now(),
                            'ghl_locations_sync_result': str(result.get('success', False))
                        })

                        # Commit the transaction
                        cr.commit()
                        break  # Success, exit retry loop

                except Exception as e:
                    _logger.error('Background sync error on attempt %d: %s', attempt + 1, str(e))

                    # If it's a concurrency error, wait and retry
                    if "concurrent update" in str(e) or "transaction is aborted" in str(e):
                        if attempt < max_retries - 1:  # Don't sleep on last attempt
                            time.sleep(retry_delay)
                            retry_delay *= 2  # Exponential backoff
                        else:
                            _logger.error('Max retries reached for background sync')
                            # Set sync status to "failed"
                            try:
                                registry = Registry(current_dbname)
                                with registry.cursor() as cr:
                                    env = api.Environment(cr, SUPERUSER_ID, {})
                                    config = env['res.config.settings'].sudo().search([], limit=1)
                                    if not config:
                                        config = env['res.config.settings'].sudo().create({})
                                    config.write({
                                        'ghl_locations_sync_status': 'failed',
                                        'ghl_locations_sync_error': str(e)
                                    })
                            except Exception as update_error:
                                _logger.error('Error updating sync status to failed: %s', str(update_error))
                    else:
                        # For non-concurrency errors, don't retry
                        _logger.error('Non-concurrency error, not retrying: %s', str(e))
                        import traceback
                        _logger.error('Background sync full traceback: %s', traceback.format_exc())

                        # Set sync status to "failed"
                        try:
                            registry = Registry(current_dbname)
                            with registry.cursor() as cr:
                                env = api.Environment(cr, SUPERUSER_ID, {})
                                config = env['res.config.settings'].sudo().search([], limit=1)
                                if not config:
                                    config = env['res.config.settings'].sudo().create({})
                                config.write({
                                    'ghl_locations_sync_status': 'failed',
                                    'ghl_locations_sync_error': str(e)
                                })
                                pass  # No action needed when sync status is set to failed
                        except Exception as update_error:
                            _logger.error('Error updating sync status to failed: %s', str(update_error))
                        break

        # Start background sync thread
        sync_thread = threading.Thread(target=background_sync)
        sync_thread.daemon = True
        sync_thread.start()

        # Immediately return data from database (cached)
        try:
            locations = request.env['installed.location'].sudo().search([
                ('app_id', '=', app_id)
            ]).with_context(prefetch_fields=['automation_template_id'])
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
                    'automationGroup': loc.get_automation_group_name(),
                    'adAccounts': loc.ad_accounts if loc.ad_accounts not in [None, '', 0] else mock_defaults[
                        'adAccounts'],
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
                    'medianAISalesGradeColor': loc.median_ai_sales_grade_color or mock_defaults[
                        'medianAISalesGradeColor'],
                    'closeRate': loc.close_rate or mock_defaults['closeRate'],
                    'revenuePerContact': loc.revenue_per_contact or mock_defaults['revenuePerContact'],
                    'grossROAS': loc.gross_roas or mock_defaults['grossROAS'],
                })

            return Response(
                json.dumps({
                    'locations': data,
                    'message': 'Data returned from cache. Background sync in progress.',
                    'sync_status': 'background'
                }),
                content_type='application/json',
                status=200,
                headers=get_cors_headers(request)
            )

        except Exception as e:
            _logger.error('Error in fast installed locations endpoint: %s', str(e))
            return Response(
                json.dumps({
                    'error': f'Error fetching locations: {str(e)}'
                }),
                content_type='application/json',
                status=500,
                headers=get_cors_headers(request)
            )

    @http.route('/api/installed-locations-fresh', type='http', auth='none', methods=['GET', 'OPTIONS'], csrf=False)
    def get_installed_locations_fresh(self, **kwargs):
        """
        Fresh data endpoint that forces immediate sync and returns updated data
        """

        # Handle preflight OPTIONS request
        if request.httprequest.method == 'OPTIONS':
            return Response(
                status=200,
                headers=get_cors_headers(request)
            )

        # Get app_id from parameters or use default
        app_id = kwargs.get('appId', '6867d1537079188afca5013c')
        
        # Hardcode company_id
        company_id = 'Ipg8nKDPLYKsbtodR6LN'
        
        # Call the fetch_installed_locations function from the model (synchronous)
        installed_location_model = request.env['installed.location'].sudo()

        result = installed_location_model.fetch_installed_locations(
            company_id=company_id,
            app_id=app_id,
            limit=500,
            fetch_details=True  # Fetch details for the overview page refresh
        )
        if not result.get('success'):
            _logger.error('Failed to fetch installed locations: %s', result.get('error'))
            return Response(
                json.dumps({'error': result.get('error', 'Failed to fetch installed locations')}),
                content_type='application/json',
                status=400,
                headers=get_cors_headers(request)
            )

        # Get the updated locations from the database
        locations = request.env['installed.location'].sudo().search([
            ('app_id', '=', app_id)
        ]).with_context(prefetch_fields=['automation_template_id'])
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
                'automationGroup': loc.get_automation_group_name(),
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

        return Response(
            json.dumps({
                'locations': data,
                'message': 'Data refreshed successfully.',
                'sync_status': 'fresh'
            }),
            content_type='application/json',
            status=200,
            headers=get_cors_headers(request)
        )

    @http.route('/api/installed-locations-sync-status', type='http', auth='none', methods=['GET', 'OPTIONS'],
                csrf=False)
    def get_installed_locations_sync_status(self, **kwargs):
        """
        Get the current sync status for installed locations
        """

        # Handle preflight OPTIONS request
        if request.httprequest.method == 'OPTIONS':
            return Response(
                status=200,
                headers=get_cors_headers(request)
            )

        try:
            # Get sync status from config settings
            config = request.env['res.config.settings'].sudo().search([], limit=1)

            if not config:
                return Response(
                    json.dumps({
                        'status': 'unknown',
                        'message': 'No sync status available'
                    }),
                    content_type='application/json',
                    status=200,
                    headers=get_cors_headers(request)
                )

            sync_status = getattr(config, 'ghl_locations_sync_status', 'unknown')
            sync_started = getattr(config, 'ghl_locations_sync_started', None)
            sync_completed = getattr(config, 'ghl_locations_sync_completed', None)
            sync_result = getattr(config, 'ghl_locations_sync_result', None)
            sync_error = getattr(config, 'ghl_locations_sync_error', None)

            response_data = {
                'status': sync_status,
                'started': sync_started.isoformat() if sync_started else None,
                'completed': sync_completed.isoformat() if sync_completed else None,
                'result': sync_result,
                'error': sync_error
            }

            # If sync is completed, also return the latest data
            if sync_status == 'completed':
                app_id = kwargs.get('appId', '6867d1537079188afca5013c')
                locations = request.env['installed.location'].sudo().search([
                    ('app_id', '=', app_id)
                ]).with_context(prefetch_fields=['automation_template_id'])

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
                        'automationGroup': loc.get_automation_group_name(),
                        'adAccounts': loc.ad_accounts if loc.ad_accounts not in [None, '', 0] else mock_defaults[
                            'adAccounts'],
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
                        'medianAISalesGradeColor': loc.median_ai_sales_grade_color or mock_defaults[
                            'medianAISalesGradeColor'],
                        'closeRate': loc.close_rate or mock_defaults['closeRate'],
                        'revenuePerContact': loc.revenue_per_contact or mock_defaults['revenuePerContact'],
                        'grossROAS': loc.gross_roas or mock_defaults['grossROAS'],
                    })

                response_data['locations'] = data
                response_data['total_locations'] = len(data)

            return Response(
                json.dumps(response_data),
                content_type='application/json',
                status=200,
                headers=get_cors_headers(request)
            )

        except Exception as e:
            _logger.error('Error getting sync status: %s', str(e))
            return Response(
                json.dumps({
                    'status': 'error',
                    'error': f'Error getting sync status: {str(e)}'
                }),
                content_type='application/json',
                status=500,
                headers=get_cors_headers(request)
            )

    @http.route('/api/get-location-users', type='http', auth='none', methods=['GET', 'OPTIONS'], csrf=False)
    def get_location_users(self, **kwargs):
        if request.httprequest.method == 'OPTIONS':
            return Response(status=200, headers=get_cors_headers(request))
        location_id = kwargs.get('location_id')
        if not location_id:
            return Response(json.dumps({'success': False, 'error': 'location_id is required'}),
                            content_type='application/json', status=400, headers=get_cors_headers(request))
        app_id = self._get_app_id_from_request(kwargs)
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

        # Check if the app is still installed on this location
        if app not in loc.application_ids:
            _logger.warning('App %s is not installed on location %s', app.name, location_id)
            return Response(
                json.dumps({
                    'success': False,
                    'error': f'App {app.name} is not installed on this location',
                    'location_id': location_id,
                    'app_id': app_id
                }),
                content_type='application/json',
                status=403,
                headers=get_cors_headers(request)
            )

        # Check if location is marked as installed
        if not loc.is_installed:
            _logger.warning('Location %s is not marked as installed', location_id)
            return Response(
                json.dumps({
                    'success': False,
                    'error': 'Location is not installed',
                    'location_id': location_id
                }),
                content_type='application/json',
                status=403,
                headers=get_cors_headers(request)
            )

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
        task_sync_result = request.env['ghl.contact.task'].sudo().sync_all_contact_tasks(access_token, location_id,
                                                                                         company_id)
        # Sync GHL conversations for this location (contact by contact)

        conversation_sync_result = {'success': False, 'message': 'No sync attempted'}

        try:
            # Get all contacts for this location
            contacts = request.env['ghl.location.contact'].sudo().search([
                ('location_id.location_id', '=', location_id)
            ])

            total_created = 0
            total_updated = 0
            total_contacts_synced = 0

            for contact in contacts:
                try:
                    # Call conversation sync method for each contact
                    contact_result = request.env['ghl.contact.conversation'].sudo().sync_conversations_for_contact(
                        access_token,
                        location_id,
                        contact.external_id
                    )

                    if contact_result.get('success'):
                        total_created += contact_result.get('created_count', 0)
                        total_updated += contact_result.get('updated_count', 0)
                        total_contacts_synced += 1
                        
                    else:
                        _logger.error('Conversation sync failed for contact %s: %s', 
                                     contact.external_id, contact_result.get('error'))
                except Exception as contact_error:
                    _logger.error('Error syncing conversations for contact %s: %s', 
                                 contact.external_id, str(contact_error))

            conversation_sync_result = {
                'success': total_contacts_synced > 0,
                'message': f'Synced conversations for {total_contacts_synced} contacts. Created: {total_created}, Updated: {total_updated}',
                'total_contacts_synced': total_contacts_synced,
                'total_created': total_created,
                'total_updated': total_updated
            }

            if not conversation_sync_result['success']:
                _logger.error('Conversation sync failed: %s', conversation_sync_result['message'])
        except Exception as e:
            _logger.error('Error during conversation sync: %s', str(e))
            conversation_sync_result = {'success': False, 'message': f'Sync error: {str(e)}'}

        # Sync GHL opportunities for this location
        opportunity_sync_result = {'success': False, 'message': 'No sync attempted'}
        try:
            opportunity_sync_result = request.env['ghl.contact.opportunity'].sudo().sync_opportunities_for_location(
                access_token,
                location_id,
                company_id
            )
            if not opportunity_sync_result.get('success', False):
                _logger.error('Opportunity sync failed: %s', opportunity_sync_result)
        except Exception as e:
            _logger.error('Error during opportunity sync: %s', str(e))
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

    @http.route('/api/get-location-contacts-fast', type='http', auth='none', methods=['GET', 'OPTIONS'], csrf=False)
    def get_location_contacts_fast(self, **kwargs):
        """
        Optimized version of get_location_contacts that:
        1. Returns data immediately from database
        2. Triggers background sync for fresh data
        3. Uses optimized database queries
        """
        if request.httprequest.method == 'OPTIONS':
            return Response(status=200, headers=get_cors_headers(request))
        import json
        location_id = kwargs.get('location_id')
        if not location_id:
            return Response(
                json.dumps({'success': False, 'error': 'location_id is required'}),
                content_type='application/json',
                status=400,
                headers=get_cors_headers(request)
            )

        # Get app configuration
        app_id = '6867d1537079188afca5013c'
        company_id = 'Ipg8nKDPLYKsbtodR6LN'
        app = request.env['cyclsales.application'].sudo().search([
            ('app_id', '=', app_id),
            ('is_active', '=', True)
        ], limit=1)

        if not app or not app.access_token:
            return Response(
                json.dumps({'success': False, 'error': 'No valid access token found for this app_id.'}),
                content_type='application/json',
                status=400,
                headers=get_cors_headers(request)
            )

        # Find the installed location
        loc = request.env['installed.location'].sudo().search([('location_id', '=', location_id)], limit=1)
        if not loc:
            return Response(
                json.dumps({'success': False, 'error': 'Location not found'}),
                content_type='application/json',
                status=404,
                headers=get_cors_headers(request)
            )

        # Capture dbname before starting background thread
        dbname = request.env.cr.dbname

        # Start background sync in a separate thread (non-blocking)
        def background_sync():
            from odoo import api, SUPERUSER_ID
            from odoo.modules.registry import Registry
            from datetime import datetime
            import time
            dbname = request.env.cr.dbname
            max_retries = 3
            retry_delay = 2
            # Set sync status to in_progress with retry logic
            for attempt in range(max_retries):
                try:
                    registry = Registry(dbname)
                    with registry.cursor() as cr:
                        env = api.Environment(cr, SUPERUSER_ID, {})
                        config = env['res.config.settings'].sudo().search([], limit=1)
                        if not config:
                            config = env['res.config.settings'].sudo().create({})
                        config.write({
                            'ghl_contacts_sync_status': 'in_progress',
                            'ghl_contacts_sync_started': datetime.now(),
                            'ghl_contacts_sync_location_id': location_id
                        })
                        cr.commit()
                        break
                except Exception as e:
                    if "concurrent update" in str(e) or "serialize access" in str(e):
                        if attempt < max_retries - 1:
                            _logger.warning('Concurrency error setting in_progress status, retrying in %d seconds...', retry_delay)
                            time.sleep(retry_delay)
                            retry_delay *= 2
                        else:
                            _logger.error('Max retries reached for setting in_progress status')
                    else:
                        _logger.error('Error setting contacts sync status to in_progress: %s', str(e))
                        break
            try:
                registry = Registry(dbname)
                # --- Contact Sync ---
                with registry.cursor() as cr:
                    env = api.Environment(cr, SUPERUSER_ID, {})
                    app_record = env['cyclsales.application'].search([
                        ('app_id', '=', app_id),
                        ('is_active', '=', True)
                    ], limit=1)
                    if not app_record or not app_record.access_token:
                        _logger.error('No valid access token found in background sync')
                        return
                    access_token = app_record.access_token
                    loc_record = env['installed.location'].search([('location_id', '=', location_id)], limit=1)
                    if not loc_record:
                        _logger.error('Location not found in background sync: %s', location_id)
                        return
                    result = loc_record.fetch_location_contacts(company_id, location_id, access_token)
                    cr.commit()
                # --- Task Sync ---
                with registry.cursor() as cr:
                    env = api.Environment(cr, SUPERUSER_ID, {})
                    task_result = env['ghl.contact.task'].sync_all_contact_tasks_optimized(
                        access_token, location_id, company_id
                    )
                    cr.commit()
                # --- Conversation Sync ---
                with registry.cursor() as cr:
                    env = api.Environment(cr, SUPERUSER_ID, {})
                    # Per-contact conversation sync is handled elsewhere if needed
                    # If you want to keep the old logic, you can loop here
                    # For now, just log that this step is isolated
                    # Example: conv_result = ...
                    cr.commit()
                # --- Opportunity Sync ---
                with registry.cursor() as cr:
                    env = api.Environment(cr, SUPERUSER_ID, {})
                    opp_result = env['ghl.contact.opportunity'].sync_opportunities_for_location(
                        access_token, location_id, company_id, max_pages=None
                    )   
                    cr.commit()
                # Set sync status to completed
                with registry.cursor() as cr:
                    env = api.Environment(cr, SUPERUSER_ID, {})
                    config = env['res.config.settings'].sudo().search([], limit=1)
                    if not config:
                        config = env['res.config.settings'].sudo().create({})
                    for attempt in range(max_retries):
                        try:
                            config.write({
                                'ghl_contacts_sync_status': 'completed',
                                'ghl_contacts_sync_completed': datetime.now(),
                                'ghl_contacts_sync_result': str(result.get('success', False)),
                                'ghl_contacts_sync_location_id': location_id
                            })
                            cr.commit()
                            break
                        except Exception as e:
                            if "concurrent update" in str(e) or "serialize access" in str(e):
                                if attempt < max_retries - 1:
                                    _logger.warning('Concurrency error on completed, retrying in %d seconds...', retry_delay)
                                    time.sleep(retry_delay)
                                    retry_delay *= 2
                                else:
                                    _logger.error('Max retries reached for config write (completed phase)')
                            else:
                                _logger.error('Error setting contacts sync status to completed: %s', str(e))
                                break
            except Exception as e:
                _logger.error('Background sync error: %s', str(e))
                import traceback
                _logger.error('Background sync full traceback: %s', traceback.format_exc())
                # Now open a NEW cursor/context to write the failed status
                for attempt in range(3):
                    try:
                        with registry.cursor() as cr:
                            env = api.Environment(cr, SUPERUSER_ID, {})
                            config = env['res.config.settings'].sudo().search([], limit=1)
                            if not config:
                                config = env['res.config.settings'].sudo().create({})
                            config.write({
                                'ghl_contacts_sync_status': 'failed',
                                'ghl_contacts_sync_error': str(e),
                                'ghl_contacts_sync_location_id': location_id
                            })
                            cr.commit()
                        break
                    except Exception as update_error:
                        if "concurrent update" in str(update_error) or "serialize access" in str(update_error):
                            if attempt < 2:
                                _logger.warning('Concurrency error on failed, retrying in 2 seconds...')
                                time.sleep(2)
                            else:
                                _logger.error('Max retries reached for config write (failed phase)')
                        else:
                            _logger.error('Error updating contacts sync status to failed: %s', str(update_error))
                            break

        # Start background sync thread
        sync_thread = threading.Thread(target=background_sync)
        sync_thread.daemon = True
        sync_thread.start()

        # Immediately return data from database (optimized queries)
        try:
            # Use optimized query with prefetch_related
            contacts = request.env['ghl.location.contact'].sudo().search([
                ('location_id.location_id', '=', location_id)
            ])

            # Prefetch related data to avoid N+1 queries
            contacts.mapped('custom_field_ids')
            contacts.mapped('attribution_ids')

            # Get all tasks for these contacts in one query
            all_tasks = request.env['ghl.contact.task'].sudo().search([
                ('contact_id', 'in', contacts.ids)
            ])

            # Get all conversations for these contacts in one query
            all_conversations = request.env['ghl.contact.conversation'].sudo().search([
                ('contact_id', 'in', contacts.ids)
            ])

            # Get all users for assigned_to lookups
            assigned_user_ids = list(set([c.assigned_to for c in contacts if c.assigned_to]))
            users = request.env['ghl.location.user'].sudo().search([
                ('external_id', 'in', assigned_user_ids)
            ])
            user_map = {u.external_id: u for u in users}

            contact_data = []
            for contact in contacts:
                # Parse JSON fields once
                engagement_summary = []
                last_message = []
                contact_tags = []

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

                if contact.tags:
                    try:
                        import json
                        contact_tags = json.loads(contact.tags)
                        if not isinstance(contact_tags, list):
                            contact_tags = [contact_tags]
                    except:
                        contact_tags = []

                # Get assigned user name from preloaded map
                assigned_user_name = contact.assigned_to or ''
                if contact.assigned_to and contact.assigned_to in user_map:
                    user = user_map[contact.assigned_to]
                    assigned_user_name = user.name or f"{user.first_name or ''} {user.last_name or ''}".strip()

                # Get tasks for this contact from preloaded data
                contact_tasks = [t for t in all_tasks if t.contact_id.id == contact.id]
                tasks_data = []
                for task in contact_tasks:
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

                # Get conversations for this contact from preloaded data
                contact_conversations = [c for c in all_conversations if c.contact_id.id == contact.id]
                conversations_data = []
                for conversation in contact_conversations:
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
                    'ai_status': contact.ai_status if contact.ai_status else '<span style="color: #6b7280;">Not Contacted</span>',
                    'ai_summary': contact.ai_summary if contact.ai_summary else 'Read',
                    'ai_reasoning': contact.ai_reasoning if contact.ai_reasoning else '<span style="color: #6b7280;">No analysis available</span>',
                    'ai_quality_grade': contact.ai_quality_grade if contact.ai_quality_grade else 'no_grade',
                    'ai_sales_grade': contact.ai_sales_grade if contact.ai_sales_grade else 'no_grade',
                    'crm_tasks': contact.crm_tasks or 'no_tasks',
                    'category': contact.category or 'manual',
                    'channel': contact.channel or 'manual',
                    'created_by': contact.created_by or '',
                    'attribution': contact.attribution or '',
                    'assigned_to': assigned_user_name,
                    'speed_to_lead': contact.speed_to_lead or '',
                    'touch_summary': self._compute_touch_summary_for_contact(contact),
                    'engagement_summary': engagement_summary,
                    'last_touch_date': self._compute_last_touch_date_for_contact(contact),
                    'last_message': self._compute_last_message_for_contact(contact),
                    'total_pipeline_value': contact.total_pipeline_value or 0.0,
                    'opportunities': contact.opportunities or 0,
                    'contact_tags': contact_tags,
                    'tasks': tasks_data,
                    'tasks_count': len(tasks_data),
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

            return Response(
                json.dumps({
                    'success': True,
                    'contacts': contact_data,
                    'total_contacts': len(contact_data),
                    'message': 'Data returned from cache. Background sync in progress.',
                    'sync_status': 'background'
                }),
                content_type='application/json',
                status=200,
                headers=get_cors_headers(request)
            )

        except Exception as e:
            _logger.error('Error in fast contacts endpoint: %s', str(e))
            return Response(
                json.dumps({
                    'success': False,
                    'error': f'Error fetching contacts: {str(e)}'
                }),
                content_type='application/json',
                status=500,
                headers=get_cors_headers(request)
            )

    @http.route('/api/location-contacts', type='http', auth='none', methods=['GET', 'OPTIONS'], csrf=False)
    def get_location_contacts_from_db(self, **kwargs):
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

        # ALWAYS SYNC FRESH DATA FROM GHL API BEFORE RETURNING
        app_id = self._get_app_id_from_request(kwargs)
        company_id = 'Ipg8nKDPLYKsbtodR6LN'
        app = request.env['cyclsales.application'].sudo().search([
            ('app_id', '=', app_id),
            ('is_active', '=', True)
        ], limit=1)

        sync_summary = {
            'contacts_synced': False,
            'tasks_synced': False,
            'conversations_synced': False,
            'opportunities_synced': False,
            'messages_fetched': 0,
            'touch_info_updated': 0
        }

        if app and app.access_token:
            access_token = app.access_token
            loc = request.env['installed.location'].sudo().search([('location_id', '=', location_id)], limit=1)
            if loc:
                # Check if the app is still installed on this location
                if app not in loc.application_ids:
                    _logger.warning('App %s is not installed on location %s', app.name, location_id)
                    return Response(
                        json.dumps({
                            'success': False,
                            'error': f'App {app.name} is not installed on this location',
                            'location_id': location_id,
                            'app_id': app_id
                        }),
                        content_type='application/json',
                        status=403,
                        headers=get_cors_headers(request)
                    )

                # Check if location is marked as installed
                if not loc.is_installed:
                    _logger.warning('Location %s is not marked as installed', location_id)
                    return Response(
                        json.dumps({
                            'success': False,
                            'error': 'Location is not installed',
                            'location_id': location_id
                        }),
                        content_type='application/json',
                        status=403,
                        headers=get_cors_headers(request)
                    )
                # SYNC CONTACTS (fetches from GHL and updates Odoo DB)
                contact_sync_result = loc.fetch_location_contacts(company_id, location_id, access_token)
                sync_summary['contacts_synced'] = contact_sync_result.get('success', False)

                # SYNC TASKS FOR ALL CONTACTS
                task_sync_result = request.env['ghl.contact.task'].sudo().sync_all_contact_tasks(access_token,
                                                                                                 location_id,
                                                                                                 company_id)
                sync_summary['tasks_synced'] = task_sync_result.get('success', False)

                # SYNC CONVERSATIONS FOR ALL CONTACTS
                contacts = request.env['ghl.location.contact'].sudo().search([
                    ('location_id.location_id', '=', location_id)
                ])

                total_conversations_created = 0
                total_conversations_updated = 0
                total_contacts_synced = 0

                for contact in contacts:
                    try:
                        conv_result = request.env['ghl.contact.conversation'].sudo().sync_conversations_for_contact(
                            access_token, location_id, contact.external_id
                        )
                        if conv_result.get('success'):
                            total_conversations_created += conv_result.get('created_count', 0)
                            total_conversations_updated += conv_result.get('updated_count', 0)
                            total_contacts_synced += 1
                    except Exception as e:
                        _logger.error(f"Error syncing conversations for contact {contact.external_id}: {str(e)}")

                sync_summary['conversations_synced'] = total_contacts_synced > 0

                # SYNC OPPORTUNITIES FOR THIS LOCATION  
                opportunity_sync_result = request.env['ghl.contact.opportunity'].sudo().sync_opportunities_for_location(
                    access_token, location_id, company_id
                )
                sync_summary['opportunities_synced'] = opportunity_sync_result.get('success', False)

                # SYNC MESSAGES FOR ALL CONVERSATIONS TO GET FRESH TOUCH DATA
                conversations = request.env['ghl.contact.conversation'].sudo().search([
                    ('contact_id.location_id.location_id', '=', location_id)
                ])

                total_messages_fetched = 0
                for conversation in conversations:
                    try:
                        # Get location token for this conversation's contact
                        location_token_result = request.env['ghl.contact.conversation'].sudo()._get_location_token(
                            access_token, conversation.contact_id.location_id.location_id, company_id
                        )

                        if location_token_result['success']:
                            message_result = request.env['ghl.contact.message'].sudo().fetch_messages_for_conversation(
                                conversation_id=conversation.ghl_id,
                                access_token=location_token_result['access_token'],
                                location_id=conversation.contact_id.location_id.id,
                                contact_id=conversation.contact_id.id,
                                limit=100
                            )
                            if message_result.get('success'):
                                total_messages_fetched += message_result.get('total_messages', 0)
                    except Exception as e:
                        _logger.error(f"Error fetching messages for conversation {conversation.ghl_id}: {str(e)}")

                sync_summary['messages_fetched'] = total_messages_fetched

                # UPDATE TOUCH INFORMATION FOR ALL CONTACTS
                touch_update_result = request.env['ghl.location.contact'].sudo().update_all_contacts_touch_information()
                sync_summary['touch_info_updated'] = touch_update_result.get('contacts_updated', 0)

        # Fetch fresh contacts from our database after all syncs
        contacts = request.env['ghl.location.contact'].sudo().search([
            ('location_id.location_id', '=', location_id)
        ])

        # Log the number of contacts and their external_ids for debugging
        if contacts:
            pass  # No action needed when contacts exist

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
                assigned_user = request.env['ghl.location.user'].sudo().search([
                    ('external_id', '=', contact.assigned_to)
                ], limit=1)
                if assigned_user:
                    assigned_user_name = assigned_user.name or f"{assigned_user.first_name or ''} {assigned_user.last_name or ''}".strip()  
                else:
                    _logger.warning(f"No user found with external_id: {contact.assigned_to}")

            # Get fresh computed touch information
            touch_summary = self._compute_touch_summary_for_contact(contact)
            last_touch_date = self._compute_last_touch_date_for_contact(contact)
            last_message_data = self._compute_last_message_for_contact(contact)

            # Fetch fresh tasks for this contact
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

            # Fetch fresh conversations for this contact
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
                'ai_status': contact.ai_status if contact.ai_status else '<span style="color: #6b7280;">Not Contacted</span>',
                'ai_summary': contact.ai_summary if contact.ai_summary else 'Read',
                'ai_reasoning': contact.ai_reasoning if contact.ai_reasoning else '<span style="color: #6b7280;">No analysis available</span>',
                'ai_quality_grade': contact.ai_quality_grade if contact.ai_quality_grade else 'no_grade',
                'ai_sales_grade': contact.ai_sales_grade if contact.ai_sales_grade else 'no_grade',
                'crm_tasks': contact.crm_tasks or 'no_tasks',
                'category': contact.category or 'manual',
                'channel': contact.channel or 'manual',
                'created_by': contact.created_by or '',
                'attribution': contact.attribution or '',
                'assigned_to': assigned_user_name,
                'speed_to_lead': contact.speed_to_lead or '',
                'touch_summary': touch_summary,
                'engagement_summary': engagement_summary,
                'last_touch_date': last_touch_date,
                'last_message': last_message_data,
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
                'total_contacts': len(contact_data),
                'sync_summary': sync_summary
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

    @http.route('/api/location-contacts-count', type='http', auth='none', methods=['GET', 'OPTIONS'], csrf=False)
    def get_location_contacts_count(self, **kwargs):
        """
        Get the total number of contacts for a location using the /contacts/search endpoint
        """
        if request.httprequest.method == 'OPTIONS':
            return Response(status=200, headers=get_cors_headers(request))

        location_id = kwargs.get('location_id')
        selected_user = kwargs.get('selected_user', '')  # Add support for user filtering
        if not location_id:
            _logger.error("Missing location_id param")
            return Response(
                json.dumps({'success': False, 'error': 'location_id is required'}),
                content_type='application/json',
                status=400,
                headers=get_cors_headers(request)
            )
        try:
            app_id = self._get_app_id_from_request(kwargs)
            app = request.env['cyclsales.application'].sudo().search([
                ('app_id', '=', app_id),
                ('is_active', '=', True)
            ], limit=1)

            if not app or not app.access_token:
                _logger.error("No valid access token found for this app_id.")
                return Response(
                    json.dumps({'success': False, 'error': 'No valid access token found for this app_id.'}),
                    content_type='application/json',
                    status=400,
                    headers=get_cors_headers(request)
                )
            loc = request.env['installed.location'].sudo().search([('location_id', '=', location_id)], limit=1)
            if not loc:
                _logger.error("Location not found in DB")
                return Response(
                    json.dumps({'success': False, 'error': 'Location not found'}),
                    content_type='application/json',
                    status=404,
                    headers=get_cors_headers(request)
                )

            # Check if the app is still installed on this location
            if app not in loc.application_ids:
                _logger.warning('App %s is not installed on location %s', app.name, location_id)
                return Response(
                    json.dumps({
                        'success': False,
                        'error': f'App {app.name} is not installed on this location',
                        'location_id': location_id,
                        'app_id': app_id
                    }),
                    content_type='application/json',
                    status=403,
                    headers=get_cors_headers(request)
                )

            # Check if location is marked as installed
            if not loc.is_installed:
                _logger.warning('Location %s is not marked as installed', location_id)
                return Response(
                    json.dumps({
                        'success': False,
                        'error': 'Location is not installed',
                        'location_id': location_id
                    }),
                    content_type='application/json',
                    status=403,
                    headers=get_cors_headers(request)
                )

            # If user filtering is applied, get count from GHL API with filter
            if selected_user and selected_user.strip(): 
                filtered_count_result = self._get_filtered_contacts_count_from_ghl(
                    location_id, selected_user, app.access_token, 'Ipg8nKDPLYKsbtodR6LN'
                )


                if filtered_count_result.get('success'):
                    filtered_count = filtered_count_result.get('total_contacts', 0)

                    return Response(
                        json.dumps({
                            'success': True,
                            'total_contacts': filtered_count,
                            'location_id': location_id,
                            'user_filter': selected_user,
                            'is_filtered': True,
                            'source': 'ghl_api'
                        }),
                        content_type='application/json',
                        status=200,
                        headers=get_cors_headers(request)
                    )
                else:
                    _logger.warning(
                        f"GHL API filtered count failed: {filtered_count_result.get('error')}, falling back to database")
                    # Fallback to database count if GHL API fails
                    domain = [('location_id.location_id', '=', location_id)]
                    domain.append(('assigned_to', '=', selected_user))
                    filtered_count = request.env['ghl.location.contact'].sudo().search_count(domain)

                    return Response(
                        json.dumps({
                            'success': True,
                            'total_contacts': filtered_count,
                            'location_id': location_id,
                            'user_filter': selected_user,
                            'is_filtered': True,
                            'source': 'database_fallback'
                        }),
                        content_type='application/json',
                        status=200,
                        headers=get_cors_headers(request)
                    )
            else:
                # No user filter, get total count from GHL API
                result = loc.fetch_contacts_count(app.access_token, 'Ipg8nKDPLYKsbtodR6LN')

                if result.get('success'):
                    return Response(
                        json.dumps({
                            'success': True,
                            'total_contacts': result.get('total_contacts', 0),
                            'location_id': location_id,
                            'is_filtered': False,
                            'source': 'ghl_api'
                        }),
                        content_type='application/json',
                        status=200,
                        headers=get_cors_headers(request)
                    )
                else:
                    _logger.error(f"fetch_contacts_count error: {result.get('error')}")
                    return Response(
                        json.dumps({
                            'success': False,
                            'error': result.get('error', 'Failed to fetch contacts count')
                        }),
                        content_type='application/json',
                        status=500,
                        headers=get_cors_headers(request)
                    )
        except Exception as e:
            import traceback
            tb = traceback.format_exc()
            _logger.error(f"Exception in get_location_contacts_count: {str(e)}\n{tb}")
            return Response(
                json.dumps({'success': False, 'error': str(e), 'traceback': tb}),
                content_type='application/json',
                status=500,
                headers=get_cors_headers(request)
            )

    @http.route('/api/location-contacts-lazy', type='http', auth='none', methods=['GET', 'OPTIONS'], csrf=False)
    def get_location_contacts_lazy(self, **kwargs):
        """
        Fetch contacts for a location using lazy loading (10 contacts at a time)
        MODIFIED: Always fetches fresh data from GHL API and syncs all contact details
        """
        if request.httprequest.method == 'OPTIONS':
            return Response(status=200, headers=get_cors_headers(request))

        location_id = kwargs.get('location_id')
        page = int(kwargs.get('page', 1))
        limit = int(kwargs.get('limit', 10))
        if not location_id:
            _logger.error("Missing location_id param")
            return Response(
                json.dumps({'success': False, 'error': 'location_id is required'}),
                content_type='application/json',
                status=400,
                headers=get_cors_headers(request)
            )
        try:
            app_id = self._get_app_id_from_request(kwargs)
            company_id = 'Ipg8nKDPLYKsbtodR6LN'
            app = request.env['cyclsales.application'].sudo().search([
                ('app_id', '=', app_id),
                ('is_active', '=', True)
            ], limit=1)

            if not app or not app.access_token:
                _logger.error("No valid access token found for this app_id.")
                return Response(
                    json.dumps({'success': False, 'error': 'No valid access token found for this app_id.'}),
                    content_type='application/json',
                    status=400,
                    headers=get_cors_headers(request)
                )
            loc = request.env['installed.location'].sudo().search([('location_id', '=', location_id)], limit=1) # noqa: F841
            if not loc:
                _logger.error("Location not found in DB")
                return Response(
                    json.dumps({'success': False, 'error': 'Location not found'}),
                    content_type='application/json',
                    status=404,
                    headers=get_cors_headers(request)
                )

            # Check if the app is still installed on this location
            if app not in loc.application_ids:
                _logger.warning('App %s is not installed on location %s', app.name, location_id)
                return Response(
                    json.dumps({
                        'success': False,
                        'error': f'App {app.name} is not installed on this location',
                        'location_id': location_id,
                        'app_id': app_id
                    }),
                    content_type='application/json',
                    status=403,
                    headers=get_cors_headers(request)
                )

            # Check if location is marked as installed
            if not loc.is_installed:
                _logger.warning('Location %s is not marked as installed', location_id)
                return Response(
                    json.dumps({
                        'success': False,
                        'error': 'Location is not installed',
                        'location_id': location_id
                    }),
                    content_type='application/json',
                    status=403,
                    headers=get_cors_headers(request)
                )

            # ALWAYS FETCH FRESH DATA FROM GHL API

            result = loc.fetch_location_contacts_lazy(company_id, location_id, app.access_token, page=page, limit=limit)

            if result.get('success'):
                # SYNC TASKS FOR ALL CONTACTS IN THIS LOCATION

                task_sync_result = request.env['ghl.contact.task'].sudo().sync_all_contact_tasks(
                    app.access_token, location_id, company_id
                )


                # SYNC CONVERSATIONS FOR ALL CONTACTS IN THIS LOCATION

                contacts = request.env['ghl.location.contact'].sudo().search([
                    ('location_id.location_id', '=', location_id)
                ])

                total_conversations_created = 0
                total_conversations_updated = 0
                total_contacts_synced = 0

                for contact in contacts:
                    try:
                        conv_result = request.env['ghl.contact.conversation'].sudo().sync_conversations_for_contact(
                            app.access_token, location_id, contact.external_id
                        )
                        if conv_result.get('success'):
                            total_conversations_created += conv_result.get('created_count', 0)
                            total_conversations_updated += conv_result.get('updated_count', 0)
                            total_contacts_synced += 1
                    except Exception as e:
                        _logger.error(f"Error syncing conversations for contact {contact.external_id}: {str(e)}")

                # SYNC OPPORTUNITIES FOR THIS LOCATION

                opportunity_sync_result = request.env['ghl.contact.opportunity'].sudo().sync_opportunities_for_location(
                    app.access_token, location_id, company_id
                )


                # SYNC MESSAGES FOR ALL CONVERSATIONS TO GET FRESH TOUCH DATA

                conversations = request.env['ghl.contact.conversation'].sudo().search([
                    ('contact_id.location_id.location_id', '=', location_id)
                ])

                total_messages_fetched = 0
                for conversation in conversations:
                    try:
                        # Get location token for this conversation's contact
                        location_token_result = request.env['ghl.contact.conversation'].sudo()._get_location_token(
                            app.access_token, conversation.contact_id.location_id.location_id, company_id
                        )

                        if location_token_result['success']:
                            message_result = request.env['ghl.contact.message'].sudo().fetch_messages_for_conversation(
                                conversation_id=conversation.ghl_id,
                                access_token=location_token_result['access_token'],
                                location_id=conversation.contact_id.location_id.id,
                                contact_id=conversation.contact_id.id,
                                limit=100
                            )
                            if message_result.get('success'):
                                total_messages_fetched += message_result.get('total_messages', 0)
                    except Exception as e:
                        _logger.error(f"Error fetching messages for conversation {conversation.ghl_id}: {str(e)}")

                # UPDATE TOUCH INFORMATION FOR ALL CONTACTS

                touch_update_result = request.env['ghl.location.contact'].sudo().update_all_contacts_touch_information()


                # Fetch fresh contact data from database after all syncs
                contacts = request.env['ghl.location.contact'].sudo().search([
                    ('location_id.location_id', '=', location_id)
                ], order='date_added desc', limit=limit, offset=(page - 1) * limit)

                contact_data = []
                for contact in contacts:
                    # Parse basic data only
                    engagement_summary = []
                    last_message = []
                    contact_tags = []

                    if contact.engagement_summary:
                        try:
                            engagement_summary = json.loads(contact.engagement_summary)
                        except:
                            engagement_summary = []
                    if contact.last_message:
                        try:
                            last_message = json.loads(contact.last_message)
                        except:
                            last_message = []
                    if contact.tags:
                        try:
                            contact_tags = json.loads(contact.tags)
                            if not isinstance(contact_tags, list):
                                contact_tags = [contact_tags]
                        except:
                            contact_tags = []

                    assigned_user_name = contact.assigned_to or ''
                    if contact.assigned_to:
                        assigned_user = request.env['ghl.location.user'].sudo().search([
                            ('external_id', '=', contact.assigned_to)
                        ], limit=1)
                        if assigned_user:
                            assigned_user_name = assigned_user.name or f"{assigned_user.first_name or ''} {assigned_user.last_name or ''}".strip()

                    # Get fresh computed touch information
                    touch_summary = self._compute_touch_summary_for_contact(contact)
                    last_touch_date = self._compute_last_touch_date_for_contact(contact)
                    last_message_data = self._compute_last_message_for_contact(contact)

                    # Get fresh task and conversation counts
                    tasks_count = request.env['ghl.contact.task'].sudo().search_count([
                        ('contact_id', '=', contact.id)
                    ])
                    conversations_count = request.env['ghl.contact.conversation'].sudo().search_count([
                        ('contact_id', '=', contact.id)
                    ])

                    contact_info = {
                        'id': contact.id,
                        'external_id': contact.external_id,
                        'name': contact.name or f"{contact.first_name or ''} {contact.last_name or ''}".strip() or '',
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
                        'ai_status': contact.ai_status if contact.ai_status else '<span style="color: #6b7280;">Not Contacted</span>',
                        'ai_summary': contact.ai_summary if contact.ai_summary else 'Read',
                        'ai_reasoning': contact.ai_reasoning if contact.ai_reasoning else '<span style="color: #6b7280;">No analysis available</span>',
                        'ai_quality_grade': contact.ai_quality_grade if contact.ai_quality_grade else 'no_grade',
                        'ai_sales_grade': contact.ai_sales_grade if contact.ai_sales_grade else 'no_grade',
                        'crm_tasks': contact.crm_tasks or 'no_tasks',
                        'category': contact.category or 'manual',
                        'channel': contact.channel or 'manual',
                        'created_by': contact.created_by or '',
                        'attribution': contact.attribution or '',
                        'assigned_to': assigned_user_name,
                        'speed_to_lead': contact.speed_to_lead or '',
                        'touch_summary': touch_summary,
                        'engagement_summary': engagement_summary,
                        'last_touch_date': last_touch_date,
                        'last_message': last_message_data,
                        'total_pipeline_value': contact.total_pipeline_value or 0.0,
                        'opportunities': contact.opportunities or 0,
                        'contact_tags': contact_tags,
                        'details_fetched': True,  # Always true since we sync everything fresh
                        'has_tasks': tasks_count > 0,
                        'has_conversations': conversations_count > 0,
                        'tasks_count': tasks_count,
                        'conversations_count': conversations_count,
                        'conversations_count_basic': conversations_count,
                    }

                    contact_data.append(contact_info)

                return Response(
                    json.dumps({
                        'success': True,
                        'contacts': contact_data,
                        'total_contacts': result.get('total_contacts', 0),
                        'page': page,
                        'limit': limit,
                        'has_more': result.get('has_more', False),
                        'created_count': result.get('created_count', 0),
                        'updated_count': result.get('updated_count', 0),
                        'sync_summary': {
                            'tasks_synced': task_sync_result.get('success', False),
                            'conversations_created': total_conversations_created,
                            'conversations_updated': total_conversations_updated,
                            'contacts_with_conversations': total_contacts_synced,
                            'opportunities_synced': opportunity_sync_result.get('success', False),
                            'messages_fetched': total_messages_fetched,
                            'touch_info_updated': touch_update_result.get('contacts_updated', 0)
                        }
                    }),
                    content_type='application/json',
                    status=200,
                    headers=get_cors_headers(request)
                )
            else:
                _logger.error(f"fetch_location_contacts_lazy error: {result.get('error')}")
                return Response(
                    json.dumps({
                        'success': False,
                        'error': result.get('error', 'Failed to fetch contacts')
                    }),
                    content_type='application/json',
                    status=500,
                    headers=get_cors_headers(request)
                )
        except Exception as e:
            import traceback
            tb = traceback.format_exc()
            _logger.error(f"Exception in get_location_contacts_lazy: {str(e)}\n{tb}")
            return Response(
                json.dumps({'success': False, 'error': str(e), 'traceback': tb}),
                content_type='application/json',
                status=500,
                headers=get_cors_headers(request)
            )

    @http.route('/api/contact-details', type='http', auth='none', methods=['GET', 'OPTIONS'], csrf=False)
    def get_contact_details(self, **kwargs):
        """
        Get detailed contact information including tasks, conversations, and opportunities
        """
        if request.httprequest.method == 'OPTIONS':
            return Response(status=200, headers=get_cors_headers(request))

        contact_id = kwargs.get('contact_id')
        if not contact_id:
            return Response(
                json.dumps({'success': False, 'error': 'contact_id is required'}),
                content_type='application/json',
                status=400,
                headers=get_cors_headers(request)
            )

        try:
            contact = request.env['ghl.location.contact'].sudo().browse(int(contact_id))
            if not contact.exists():
                return Response(
                    json.dumps({'success': False, 'error': 'Contact not found'}),
                    content_type='application/json',
                    status=404,
                    headers=get_cors_headers(request)
                )

            # Get app access token for API calls
            app = request.env['cyclsales.application'].sudo().search([
                ('is_active', '=', True)
            ], limit=1)

            if not app or not app.access_token:
                return Response(
                    json.dumps({'success': False, 'error': 'No valid access token found'}),
                    content_type='application/json',
                    status=400,
                    headers=get_cors_headers(request)
                )

            # Sync conversations for this contact if needed
            conversations_count = request.env['ghl.contact.conversation'].sudo().search_count([
                ('contact_id', '=', contact.id)
            ])

            if conversations_count == 0:
                try:
                    # Sync conversations for this contact
                    conv_result = request.env['ghl.contact.conversation'].sudo().sync_conversations_for_contact(
                        app.access_token, contact.location_id.location_id, contact.external_id
                    )
                    if conv_result.get('success'):
                        pass
                    else:
                        _logger.warning(
                            f"Failed to sync conversations for contact {contact.id}: {conv_result.get('error')}")
                except Exception as conv_error:
                    _logger.warning(f"Exception syncing conversations for contact {contact.id}: {str(conv_error)}")

            # Sync tasks for this contact if needed
            tasks_count = request.env['ghl.contact.task'].sudo().search_count([
                ('contact_id', '=', contact.id)
            ])

            if tasks_count == 0:
                try:
                    # Sync tasks for this contact
                    company_id = 'Ipg8nKDPLYKsbtodR6LN'
                    task_result = request.env['ghl.contact.task'].sudo().sync_contact_tasks_from_ghl(
                        contact.id, app.access_token, contact.location_id.location_id, company_id
                    )
                    if task_result.get('success'):
                        pass
                    else:
                        _logger.warning(f"Failed to sync tasks for contact {contact.id}: {task_result.get('error')}")
                except Exception as task_error:
                    _logger.warning(f"Exception syncing tasks for contact {contact.id}: {str(task_error)}")

            # Update touch information for this contact with retry mechanism
            try:
                # Compute touch summary with message fetching
                touch_summary = self._compute_touch_summary_for_contact(contact)
                last_touch_date = self._compute_last_touch_date_for_contact(contact)
                last_message_data = self._compute_last_message_for_contact(contact)

                # Update the contact with new touch information using retry mechanism
                self._update_contact_touch_info_with_retry(contact, {
                    'touch_summary': touch_summary,
                    'last_touch_date': last_touch_date if last_touch_date else False,
                    'last_message': last_message_data
                })


            except Exception as touch_error:
                _logger.warning(f"Exception updating touch information for contact {contact.id}: {str(touch_error)}")

            # Get tasks for this contact (after potential sync)
            tasks = request.env['ghl.contact.task'].sudo().search([
                ('contact_id', '=', contact.id)
            ])
            tasks_data = []
            for task in tasks:
                tasks_data.append({
                    'id': task.id,
                    'title': task.title or '',
                    'description': task.description or '',
                    'due_date': task.due_date.isoformat() if task.due_date else '',
                    'completed': task.completed or False,
                    'is_overdue': task.is_overdue or False,
                    'location_name': task.location_id.name if task.location_id else ''
                })

            # Get conversations for this contact (after potential sync)
            conversations = request.env['ghl.contact.conversation'].sudo().search([
                ('contact_id', '=', contact.id)
            ])
            conversations_data = []
            for conv in conversations:
                conversations_data.append({
                    'id': conv.id,
                    'conversation_id': conv.ghl_id or '',
                    'subject': conv.subject or '',
                    'location_name': conv.location_id.name if conv.location_id else '',
                    'date_created': conv.date_created.isoformat() if conv.date_created else '',
                    'last_message_date': conv.last_message_date.isoformat() if conv.last_message_date else '',
                    'message_count': conv.message_count or 0,
                    'last_message_type': conv.last_message_type or '',
                    'last_message_body': conv.last_message_body or ''
                })

            # Get messages for this contact
            messages = request.env['ghl.contact.message'].sudo().search([
                ('contact_id', '=', contact.id)
            ], order='create_date desc', limit=50)  # Limit to recent messages
            messages_data = []
            for msg in messages:
                messages_data.append({
                    'id': msg.id,
                    'ghl_id': msg.ghl_id or '',
                    'body': msg.body or '',
                    'message_type': msg.message_type or '',
                    'direction': msg.direction or '',
                    'date_added': msg.create_date.isoformat() if msg.create_date else '',
                    'conversation_id': msg.conversation_id.ghl_id if msg.conversation_id else ''
                })

            return Response(
                json.dumps({
                    'success': True,
                    'contact': {
                        'id': contact.id,
                        'name': contact.name or '',
                        'ai_status': contact.ai_status if contact.ai_status else '<span style="color: #6b7280;">Not Contacted</span>',
                        'ai_summary': contact.ai_summary if contact.ai_summary else 'AI analysis pending',
                        'ai_reasoning': contact.ai_reasoning if contact.ai_reasoning else '<span style="color: #6b7280;">No analysis available</span>',
                        'ai_quality_grade': contact.ai_quality_grade if contact.ai_quality_grade else 'no_grade',
                        'ai_sales_grade': contact.ai_sales_grade if contact.ai_sales_grade else 'no_grade',
                        'ai_sales_reasoning': contact.ai_sales_reasoning if contact.ai_sales_reasoning else '<span style="color: #6b7280;">No sales grade analysis available</span>',
                        'tasks': tasks_data,
                        'tasks_count': len(tasks_data),
                        'conversations': conversations_data,
                        'conversations_count': len(conversations_data),
                        'messages': messages_data,
                        'messages_count': len(messages_data),
                        'touch_summary': contact.touch_summary or 'no_touches',
                        'last_touch_date': contact.last_touch_date.isoformat() if contact.last_touch_date else '',
                        'last_message': contact.last_message or '',
                        'details_fetched': True
                    }
                }),
                content_type='application/json',
                status=200,
                headers=get_cors_headers(request)
            )

        except Exception as e:
            import traceback
            tb = traceback.format_exc()
            _logger.error(f"Exception in get_contact_details: {str(e)}\n{tb}")
            return Response(
                json.dumps({'success': False, 'error': str(e), 'traceback': tb}),
                content_type='application/json',
                status=500,
                headers=get_cors_headers(request)
            )

    @http.route('/api/sync-contact-conversations', type='http', auth='none', methods=['POST', 'OPTIONS'], csrf=False)
    def sync_contact_conversations(self, **kwargs):
        """
        Sync conversations for a specific contact using the /conversations/search endpoint.
        Expects JSON body with location_id and contact_id.
        """
        import json
        import logging
        _logger = logging.getLogger(__name__)
        if request.httprequest.method == 'OPTIONS':
            return Response(status=200, headers=get_cors_headers(request))
        try:
            data = request.httprequest.get_json() or {}
            location_id = data.get('location_id') or kwargs.get('location_id')
            contact_id = data.get('contact_id') or kwargs.get('contact_id')
            if not location_id or not contact_id:
                return Response(json.dumps({'success': False, 'error': 'location_id and contact_id are required'}),
                                content_type='application/json', status=400, headers=get_cors_headers(request))
            app_id = '6867d1537079188afca5013c'
            app = request.env['cyclsales.application'].sudo().search([
                ('app_id', '=', app_id),
                ('is_active', '=', True)
            ], limit=1)
            if not app or not app.access_token:
                return Response(json.dumps({'success': False, 'error': 'No valid access token found for this app_id.'}),
                                content_type='application/json', status=400, headers=get_cors_headers(request))
            access_token = app.access_token
            # Call the new model method for this contact only
            result = request.env['ghl.contact.conversation'].sudo().sync_conversations_for_contact(access_token,
                                                                                                   location_id,
                                                                                                   contact_id)
            return Response(json.dumps(result), content_type='application/json',
                            status=200 if result.get('success') else 500, headers=get_cors_headers(request))
        except Exception as e:
            import traceback
            tb = traceback.format_exc()
            _logger.error(f"Exception in sync_contact_conversations: {str(e)}\n{tb}")
            return Response(json.dumps({'success': False, 'error': str(e), 'traceback': tb}),
                            content_type='application/json', status=500, headers=get_cors_headers(request))

    @http.route('/api/sync-contact-opportunities', type='http', auth='none', methods=['POST', 'OPTIONS'], csrf=False)
    def sync_contact_opportunities(self, **kwargs):
        """
        On-demand API endpoint to sync all opportunities for a specific contact.
        Expects JSON body with location_id and contact_id (optionally company_id, app_id).
        """
        if request.httprequest.method == 'OPTIONS':
            return Response(status=200, headers=get_cors_headers(request))
        try:
            data = request.httprequest.get_json() or {}
            location_id = data.get('location_id') or kwargs.get('location_id')
            contact_id = data.get('contact_id') or kwargs.get('contact_id')
            company_id = data.get('company_id') or kwargs.get('company_id') or 'Ipg8nKDPLYKsbtodR6LN'
            app_id = data.get('app_id') or kwargs.get('app_id') or '6867d1537079188afca5013c'
            if not location_id or not contact_id:
                return Response(json.dumps({'success': False, 'error': 'location_id and contact_id are required'}),
                                content_type='application/json', status=400, headers=get_cors_headers(request))
            # Get agency access token
            app = request.env['cyclsales.application'].sudo().search([
                ('app_id', '=', app_id),
                ('is_active', '=', True)
            ], limit=1)
            if not app or not app.access_token:
                return Response(json.dumps({'success': False, 'error': 'No valid access token found for this app_id.'}),
                                content_type='application/json', status=400, headers=get_cors_headers(request))
            access_token = app.access_token
            # Call the sync_opportunities_for_contact model method
            result = request.env['ghl.contact.opportunity'].sudo().sync_opportunities_for_contact(
                access_token, location_id, contact_id, company_id
            )
            return Response(json.dumps(result), content_type='application/json', status=200,
                            headers=get_cors_headers(request))
        except Exception as e:
            import traceback
            tb = traceback.format_exc()
            _logger.error(f"Exception in sync_contact_opportunities: {str(e)}\n{tb}")
            return Response(json.dumps({'success': False, 'error': str(e), 'traceback': tb}),
                            content_type='application/json', status=500, headers=get_cors_headers(request))

    # --- Add this helper at the top of the class (after _logger) ---
    def _background_sync_opps_for_contacts(self, location_id, contact_external_ids, app_access_token, company_id):
        opportunity_model = request.env['ghl.contact.opportunity'].sudo()
        for contact_id in contact_external_ids:
            try:
                opportunity_model.sync_opportunities_for_contact(
                    app_access_token, location_id, contact_id, company_id
                )
            except Exception as e:
                _logger.error(f"Error syncing opportunities for contact {contact_id}: {e}")

    @http.route('/api/update-touch-information', type='http', auth='none', methods=['POST', 'OPTIONS'], csrf=False)
    def update_touch_information(self, **kwargs):
        """
        Update touch information for all contacts that have messages
        """
        if request.httprequest.method == 'OPTIONS':
            return Response(status=200, headers=get_cors_headers(request))

        try:
            # Update touch information for all contacts with messages
            result = request.env['ghl.location.contact'].sudo().update_all_contacts_touch_information()

            return Response(
                json.dumps({
                    'success': True,
                    'message': f'Updated touch information for {result.get("contacts_updated", 0)} contacts',
                    'contacts_updated': result.get('contacts_updated', 0)
                }),
                content_type='application/json',
                status=200,
                headers=get_cors_headers(request)
            )

        except Exception as e:
            import traceback
            tb = traceback.format_exc()
            _logger.error(f"Exception in update_touch_information: {str(e)}\n{tb}")
            return Response(
                json.dumps({'success': False, 'error': str(e), 'traceback': tb}),
                content_type='application/json',
                status=500,
                headers=get_cors_headers(request)
            )

    @http.route('/api/sync-contact-details-background', type='http', auth='none', methods=['POST', 'OPTIONS'],
                csrf=False)
    def sync_contact_details_background(self, **kwargs):
        """
        Trigger background sync of detailed contact data (tasks, conversations) for a location
        """
        if request.httprequest.method == 'OPTIONS':
            return Response(status=200, headers=get_cors_headers(request))

        try:
            # Parse JSON body for POST requests
            import json
            data = {}
            if request.httprequest.method == 'POST':
                try:
                    data = json.loads(request.httprequest.data.decode('utf-8'))
                except:
                    data = {}

            location_id = data.get('location_id') or kwargs.get('location_id')
            if not location_id:
                return Response(
                    json.dumps({'success': False, 'error': 'location_id is required'}),
                    content_type='application/json',
                    status=400,
                    headers=get_cors_headers(request)
                )

            # Get app configuration
            app_id = '6867d1537079188afca5013c'
            company_id = 'Ipg8nKDPLYKsbtodR6LN'
            app = request.env['cyclsales.application'].sudo().search([
                ('app_id', '=', app_id),
                ('is_active', '=', True)
            ], limit=1)

            if not app or not app.access_token:
                return Response(
                    json.dumps({'success': False, 'error': 'No valid access token found'}),
                    content_type='application/json',
                    status=400,
                    headers=get_cors_headers(request)
                )

            # Find the installed location
            loc = request.env['installed.location'].sudo().search([('location_id', '=', location_id)], limit=1)
            if not loc:
                return Response(
                    json.dumps({'success': False, 'error': 'Location not found'}),
                    content_type='application/json',
                    status=404,
                    headers=get_cors_headers(request)
                )

            # Trigger background sync
            result = loc.sync_contact_details_background(company_id, location_id, app.access_token)

            if result.get('success'):
                return Response(
                    json.dumps({
                        'success': True,
                        'message': result.get('message', 'Background sync started'),
                        'processed': result.get('processed', 0)
                    }),
                    content_type='application/json',
                    status=200,
                    headers=get_cors_headers(request)
                )
            else:
                return Response(
                    json.dumps({
                        'success': False,
                        'error': result.get('error', 'Background sync failed')
                    }),
                    content_type='application/json',
                    status=500,
                    headers=get_cors_headers(request)
                )

        except Exception as e:
            import traceback
            tb = traceback.format_exc()
            _logger.error(f"Exception in sync_contact_details_background: {str(e)}\n{tb}")
            return Response(
                json.dumps({'success': False, 'error': str(e), 'traceback': tb}),
                content_type='application/json',
                status=500,
                headers=get_cors_headers(request)
            )

    @http.route('/api/fetch-messages-for-contact/<int:contact_id>', type='http', auth='none',
                methods=['POST', 'OPTIONS'], csrf=False)
    def fetch_messages_for_contact(self, contact_id, **kwargs):
        """
        Fetch messages for a specific contact's conversations
        """
        if request.httprequest.method == 'OPTIONS':
            return Response(status=200, headers=get_cors_headers(request))

        try:
            contact = request.env['ghl.location.contact'].sudo().browse(contact_id)
            if not contact.exists():
                return Response(
                    json.dumps({'success': False, 'error': 'Contact not found'}),
                    content_type='application/json',
                    status=404,
                    headers=get_cors_headers(request)
                )

            # Get conversations for this contact
            conversations = request.env['ghl.contact.conversation'].sudo().search([
                ('contact_id', '=', contact_id)
            ])

            if not conversations:
                return Response(
                    json.dumps({'success': False, 'error': 'No conversations found for this contact'}),
                    content_type='application/json',
                    status=404,
                    headers=get_cors_headers(request)
                )

            # Get access token
            app_id = '6867d1537079188afca5013c'
            company_id = 'Ipg8nKDPLYKsbtodR6LN'

            app = request.env['cyclsales.application'].sudo().search([
                ('app_id', '=', app_id),
                ('is_active', '=', True)
            ], limit=1)

            if not app or not app.access_token:
                return Response(
                    json.dumps({'success': False, 'error': 'No valid access token found'}),
                    content_type='application/json',
                    status=400,
                    headers=get_cors_headers(request)
                )

            # Get location token
            location_token_result = request.env['ghl.contact.conversation'].sudo()._get_location_token(
                app.access_token, contact.location_id.location_id, company_id
            )

            if not location_token_result['success']:
                return Response(
                    json.dumps({'success': False,
                                'error': f"Failed to get location token: {location_token_result['message']}"}),
                    content_type='application/json',
                    status=400,
                    headers=get_cors_headers(request)
                )

            location_token = location_token_result['access_token']

            # Fetch messages for each conversation
            total_messages_fetched = 0
            conversations_processed = 0

            for conversation in conversations:
                try:
                    # Check if conversation already has messages
                    existing_messages = request.env['ghl.contact.message'].sudo().search([
                        ('conversation_id', '=', conversation.id)
                    ])

                    if existing_messages:
                        
                        continue

                    # Fetch messages for this conversation
                    message_result = request.env['ghl.contact.message'].sudo().fetch_messages_for_conversation(
                        conversation_id=conversation.ghl_id,
                        access_token=location_token,
                        location_id=contact.location_id.id,
                        contact_id=contact.id,
                        limit=100
                    )

                    if message_result.get('success'):
                        messages_fetched = message_result.get('total_messages', 0)
                        total_messages_fetched += messages_fetched

                    else:
                        _logger.error(
                            f"Failed to fetch messages for conversation {conversation.ghl_id}: {message_result.get('error')}")

                    conversations_processed += 1

                except Exception as e:
                    _logger.error(f"Error fetching messages for conversation {conversation.ghl_id}: {str(e)}")
                    continue

            # Update contact's touch information
            if total_messages_fetched > 0:
                contact.update_touch_information()

            return Response(
                json.dumps({
                    'success': True,
                    'message': f'Processed {conversations_processed} conversations, fetched {total_messages_fetched} messages',
                    'conversations_processed': conversations_processed,
                    'total_messages_fetched': total_messages_fetched,
                    'touch_summary_updated': contact.touch_summary
                }),
                content_type='application/json',
                status=200,
                headers=get_cors_headers(request)
            )

        except Exception as e:
            import traceback
            tb = traceback.format_exc()
            _logger.error(f"Exception in fetch_messages_for_contact: {str(e)}\n{tb}")
            return Response(
                json.dumps({'success': False, 'error': str(e), 'traceback': tb}),
                content_type='application/json',
                status=500,
                headers=get_cors_headers(request)
            )

    @http.route('/api/update-touch-info/<int:contact_id>', type='http', auth='none', methods=['POST', 'OPTIONS'],
                csrf=False)
    def update_touch_info(self, contact_id, **kwargs):
        import json
        """
        Manually update touch information for a specific contact
        """
        if request.httprequest.method == 'OPTIONS':
            return Response(status=200, headers=get_cors_headers(request))

        try:
            contact = request.env['ghl.location.contact'].sudo().browse(contact_id)
            if not contact.exists():
                return Response(
                    json.dumps({'success': False, 'error': 'Contact not found'}),
                    content_type='application/json',
                    status=404,
                    headers=get_cors_headers(request)
                )

            # Get messages for this contact
            messages = request.env['ghl.contact.message'].sudo().search([
                ('contact_id', '=', contact_id)
            ])


            # Count messages by type
            message_counts = {}
            for message in messages:
                message_type = message.message_type or 'UNKNOWN'
                message_counts[message_type] = message_counts.get(message_type, 0) + 1

            # Create touch summary string
            touch_parts = []
            for msg_type, count in message_counts.items():
                # Map message types to readable names
                type_name = contact._get_message_type_display_name(msg_type)
                touch_parts.append(f"{count} {type_name}")

            touch_summary = ', '.join(touch_parts) if touch_parts else 'no_touches'

            # Get last message
            last_message = messages.sorted('date_added', reverse=True)[0] if messages else None

            # Prepare update values
            update_vals = {
                'touch_summary': touch_summary,
                'last_touch_date': last_message.date_added if last_message else False,
            }

            # Add last message content
            if last_message and last_message.body:
                import json
                message_data = {
                    'body': last_message.body,
                    'type': last_message.message_type,
                    'direction': last_message.direction,
                    'date_added': last_message.date_added.isoformat() if last_message.date_added else '',
                    'id': last_message.ghl_id
                }
                update_vals['last_message'] = json.dumps(message_data)
            else:
                update_vals['last_message'] = ''

            # Update the contact with retry mechanism
            self._update_contact_touch_info_with_retry(contact, update_vals)

            return Response(
                json.dumps({
                    'success': True,
                    'message': f'Updated touch information for contact {contact_id}',
                    'touch_summary': touch_summary,
                    'last_touch_date': update_vals['last_touch_date'].isoformat() if update_vals[
                        'last_touch_date'] else None,
                    'message_counts': message_counts
                }),
                content_type='application/json',
                status=200,
                headers=get_cors_headers(request)
            )

        except Exception as e:
            import traceback
            tb = traceback.format_exc()
            _logger.error(f"Exception in update_touch_info: {str(e)}\n{tb}")
            return Response(
                json.dumps({'success': False, 'error': str(e), 'traceback': tb}),
                content_type='application/json',
                status=500,
                headers=get_cors_headers(request)
            )

    def _compute_touch_summary_for_contact(self, contact):
        """Compute touch summary for a contact - OUTBOUND touches only (from our side)
        Always fetches fresh data from GHL API to ensure real-time accuracy
        """
        import logging
        _logger = logging.getLogger(__name__)

        try:
            # Always try to fetch fresh messages from GHL API first

            # Get conversations for this contact
            conversations = request.env['ghl.contact.conversation'].sudo().search([
                ('contact_id', '=', contact.id)
            ])

            if conversations:
                # Get the app access token
                app = request.env['cyclsales.application'].sudo().search([
                    ('is_active', '=', True)
                ], limit=1)

                if app and app.access_token:
                    # Get location token using the contact's actual location ID
                    from odoo.addons.web_scraper.models.ghl_api_utils import get_location_token
                    company_id = 'Ipg8nKDPLYKsbtodR6LN'
                    contact_location_id = contact.location_id.location_id if contact.location_id else None
                    if not contact_location_id:
                        _logger.warning(f"No location ID found for contact {contact.name}")
                        # continue
                    location_token = get_location_token(app.access_token, company_id, contact_location_id)

                    if location_token:
                        # Force fetch fresh messages for all conversations
                        for conversation in conversations:
                            if conversation.ghl_id:
                                try:

                                    message_result = request.env[
                                        'ghl.contact.message'].sudo().fetch_messages_for_conversation(
                                        conversation_id=conversation.ghl_id,
                                        access_token=location_token,
                                        location_id=contact.location_id.id,
                                        contact_id=contact.id,
                                        limit=100  # Fetch more messages to get accurate counts
                                    )
                                    if message_result.get('success'):
                                        pass
                                    else:
                                        _logger.warning(
                                            f"Failed to fetch fresh messages for conversation {conversation.ghl_id}: {message_result.get('error')}")
                                except Exception as e:
                                    _logger.error(
                                        f"Error fetching fresh messages for conversation {conversation.ghl_id}: {str(e)}")

            # Now get messages from database (should be fresh after API calls)
            messages = request.env['ghl.contact.message'].sudo().search([
                ('contact_id', '=', contact.id)
            ])

            # If still no messages after fresh fetch, return no_touches
            if not messages:
                pass
                return 'no_touches'

            # Filter for OUTBOUND messages only (from our side)
            outbound_messages = messages.filtered(lambda m: m.direction == 'outbound')

            # Count outbound messages by type
            message_counts = {}
            for message in outbound_messages:
                message_type = message.message_type or 'UNKNOWN'
                message_counts[message_type] = message_counts.get(message_type, 0) + 1

            # Create touch summary string in the format expected by frontend: "3 SMS, 1 PHONE CALL"
            touch_parts = []
            for msg_type, count in message_counts.items():
                # Map message types to readable names
                type_name = contact._get_message_type_display_name(msg_type)
                touch_parts.append(f"{count} {type_name}")

            result = ', '.join(touch_parts) if touch_parts else 'no_touches'
            return result

        except Exception as e:
            _logger.error(f"Error computing touch summary for contact {contact.id}: {str(e)}")
            return 'no_touches'

    def _compute_last_touch_date_for_contact(self, contact):
        """Compute last touch date for a contact on-the-fly"""
        # First try to get from existing messages
        last_message = request.env['ghl.contact.message'].sudo().search([
            ('contact_id', '=', contact.id)
        ], order='create_date desc', limit=1)

        if last_message and last_message.create_date:
            return last_message.create_date.isoformat()

        # If no messages, try to fetch them (this will be handled by _compute_touch_summary_for_contact)
        return ''

    def _compute_last_message_content_for_contact(self, contact):
        """Compute last message content for a contact on-the-fly"""
        # Get the most recent message for this contact
        last_message = request.env['ghl.contact.message'].sudo().search([
            ('contact_id', '=', contact.id)
        ], order='create_date desc', limit=1)

        if last_message and last_message.body:
            # Return the complete message data with all fields
            return {
                'body': last_message.body,
                'type': last_message.message_type,
                'direction': last_message.direction,
                'source': last_message.source or '',
                'date_added': last_message.create_date.isoformat() if last_message.create_date else '',
                'id': last_message.ghl_id
            }

        return None

    def _compute_engagement_summary_for_contact(self, contact):
        """Compute engagement summary for a contact - ALL touches (both inbound and outbound)
        Always fetches fresh data from GHL API to ensure real-time accuracy
        """
        import logging
        _logger = logging.getLogger(__name__)

        try:
            # Always try to fetch fresh messages from GHL API first (same as touch summary)

            # Get conversations for this contact
            conversations = request.env['ghl.contact.conversation'].sudo().search([
                ('contact_id', '=', contact.id)
            ])

            if conversations:
                # Get the app access token
                app = request.env['cyclsales.application'].sudo().search([
                    ('is_active', '=', True)
                ], limit=1)

                if app and app.access_token:
                    # Get location token using the contact's actual location ID
                    from odoo.addons.web_scraper.models.ghl_api_utils import get_location_token
                    company_id = 'Ipg8nKDPLYKsbtodR6LN'
                    contact_location_id = contact.location_id.location_id if contact.location_id else None
                    if not contact_location_id:
                        _logger.warning(f"No location ID found for contact {contact.name}")
                        # continue
                    location_token = get_location_token(app.access_token, company_id, contact_location_id)

                    if location_token:
                        # Force fetch fresh messages for all conversations
                        for conversation in conversations:
                            if conversation.ghl_id:
                                try:

                                    message_result = request.env[
                                        'ghl.contact.message'].sudo().fetch_messages_for_conversation(
                                        conversation_id=conversation.ghl_id,
                                        access_token=location_token,
                                        location_id=contact.location_id.id,
                                        contact_id=contact.id,
                                        limit=100  # Fetch more messages to get accurate counts
                                    )
                                    if message_result.get('success'):
                                        pass
                                    else:
                                        _logger.warning(
                                            f"Failed to fetch fresh messages for engagement - conversation {conversation.ghl_id}: {message_result.get('error')}")
                                except Exception as e:
                                    _logger.error(
                                        f"Error fetching fresh messages for engagement - conversation {conversation.ghl_id}: {str(e)}")

            # Now get all messages from database (should be fresh after API calls)
            messages = request.env['ghl.contact.message'].sudo().search([
                ('contact_id', '=', contact.id)
            ])

            # If no messages after fresh fetch, return empty array
            if not messages:
                return []

            # Group ALL messages by type and count them (both inbound and outbound)
            engagement_data = []
            message_counts = {}


            for message in messages:
                message_type = message.message_type or 'UNKNOWN'
                message_counts[message_type] = message_counts.get(message_type, 0) + 1

            # Convert to the format expected by frontend
            for msg_type, count in message_counts.items():
                engagement_data.append({
                    'type': msg_type,
                    'count': count,
                    'icon': self._get_engagement_icon(msg_type),
                    'color': self._get_engagement_color(msg_type)
                })

            return engagement_data

        except Exception as e:
            _logger.error(f"Error computing engagement summary for contact {contact.id}: {str(e)}")
            return []

    def _compute_speed_to_lead_for_contact(self, contact):
        """Compute speed to lead for a contact on-the-fly"""
        # Calculate time between contact creation and first interaction
        if not contact.date_added:
            return ''

        # Get the first message/interaction
        first_message = request.env['ghl.contact.message'].sudo().search([
            ('contact_id', '=', contact.id)
        ], order='create_date asc', limit=1)

        if first_message and first_message.create_date:
            # Calculate time difference
            from datetime import datetime
            contact_date = contact.date_added
            first_interaction_date = first_message.create_date

            if isinstance(contact_date, str):
                contact_date = datetime.fromisoformat(contact_date.replace('Z', '+00:00'))
            if isinstance(first_interaction_date, str):
                first_interaction_date = datetime.fromisoformat(first_interaction_date.replace('Z', '+00:00'))

            time_diff = first_interaction_date - contact_date
            hours = time_diff.total_seconds() / 3600

            if hours < 1:
                return f"{int(time_diff.total_seconds() / 60)} minutes"
            elif hours < 24:
                return f"{int(hours)} hours"
            else:
                days = hours / 24
                return f"{int(days)} days"

        return 'No response'

    def _get_engagement_icon(self, message_type):
        """Get icon for engagement type"""
        icon_mapping = {
            'TYPE_SMS': '📱',
            'TYPE_CALL': '📞',
            'TYPE_EMAIL': '📧',
            'TYPE_WEBCHAT': '💬',
            'TYPE_FACEBOOK': '📘',
            'TYPE_WHATSAPP': '📱',
            'TYPE_REVIEW': '⭐',
            'TYPE_APPOINTMENT': '📅',
            'TYPE_OPPORTUNITY': '💰',
        }
        return icon_mapping.get(message_type, '📄')

    def _get_engagement_color(self, message_type):
        """Get color for engagement type"""
        color_mapping = {
            'TYPE_SMS': 'border-green-500 text-green-300',
            'TYPE_CALL': 'border-blue-500 text-blue-300',
            'TYPE_EMAIL': 'border-purple-500 text-purple-300',
            'TYPE_WEBCHAT': 'border-orange-500 text-orange-300',
            'TYPE_FACEBOOK': 'border-blue-600 text-blue-300',
            'TYPE_WHATSAPP': 'border-green-600 text-green-300',
            'TYPE_REVIEW': 'border-yellow-500 text-yellow-300',
            'TYPE_APPOINTMENT': 'border-indigo-500 text-indigo-300',
            'TYPE_OPPORTUNITY': 'border-emerald-500 text-emerald-300',
        }
        return color_mapping.get(message_type, 'border-slate-500 text-slate-300')

    def _fetch_fresh_contacts_from_ghl(self, location_token, location_id, page, limit, company_id):
        """
        Fetch fresh contacts from GHL API with pagination support
        """
        import requests
        import json
        from datetime import datetime
        
        try:
            # Use the correct GHL API search endpoint with proper pagination
            # Based on GHL API documentation: https://highlevel.stoplight.io/docs/integrations/dbe4f3a00a106-search-contacts
            url = f"https://services.leadconnectorhq.com/contacts/search"
            headers = {
                'Accept': 'application/json',
                'Authorization': f'Bearer {location_token}',
                'Version': '2021-07-28',
                'Content-Type': 'application/json'
            }
            
            # Prepare search payload with pagination
            # GHL API expects 'pageLimit' instead of 'limit'
            search_payload = {
                "locationId": location_id,
                "pageLimit": limit,
                "page": page
            }
            
            response = requests.post(url, headers=headers, data=json.dumps(search_payload), timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                contacts_data = data.get('contacts', [])
                
                # Find the installed location
                installed_location = request.env['installed.location'].sudo().search([
                    ('location_id', '=', location_id)
                ], limit=1)
                
                if not installed_location:
                    return {
                        'success': False,
                        'message': f'No installed location found for location_id: {location_id}',
                        'contacts': []
                    }
                
                # Process and create/update contacts
                processed_contacts = []
                for contact_data in contacts_data:
                    try:
                        # Prepare contact values
                        contact_vals = {
                            'external_id': contact_data.get('id'),
                            'location_id': installed_location.id,
                            'name': contact_data.get('name', ''),
                            'first_name': contact_data.get('firstName', ''),
                            'last_name': contact_data.get('lastName', ''),
                            'email': contact_data.get('email', ''),
                            'phone': contact_data.get('phone', ''),
                            'timezone': contact_data.get('timezone', ''),
                            'country': contact_data.get('country', ''),
                            'source': contact_data.get('source', ''),
                            'date_added': self._parse_iso_date(contact_data.get('dateAdded')),
                            'business_id': contact_data.get('businessId', ''),
                            'followers': contact_data.get('followers', ''),
                            'tag_list': contact_data.get('tagList', ''),
                        }
                        
                        # Create or update contact
                        existing_contact = request.env['ghl.location.contact'].sudo().search([
                            ('external_id', '=', contact_vals['external_id']),
                            ('location_id', '=', installed_location.id)
                        ], limit=1)
                        
                        if existing_contact:
                            existing_contact.write(contact_vals)
                            processed_contacts.append(existing_contact)
                        else:
                            new_contact = request.env['ghl.location.contact'].sudo().create(contact_vals)
                            processed_contacts.append(new_contact)
                            
                    except Exception as contact_error:
                        _logger.warning(f"Could not process contact {contact_data.get('id', 'unknown')}: {str(contact_error)}")
                        continue
                
                return {
                    'success': True,
                    'message': f'Successfully fetched {len(processed_contacts)} contacts from GHL API',
                    'contacts': processed_contacts
                }
                
            else:
                return {
                    'success': False,
                    'message': f'GHL API error: {response.status_code} {response.text}',
                    'contacts': []
                }
                
        except Exception as e:
            _logger.error(f"Error fetching fresh contacts from GHL API: {str(e)}")
            return {
                'success': False,
                'message': f'Unexpected error: {str(e)}',
                'contacts': []
            }

    def _parse_iso_date(self, date_string):
        """Parse ISO date string to datetime object"""
        if not date_string:
            return None
        try:
            # Handle different date formats from GHL API
            if 'T' in date_string:
                # ISO format with time
                return datetime.fromisoformat(date_string.replace('Z', '+00:00'))
            else:
                # Date only format
                return datetime.strptime(date_string, '%Y-%m-%d')
        except Exception:
            return None

