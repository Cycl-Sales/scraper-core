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
                _logger.error(f"Error setting sync status: {str(e)}")

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
                    _logger.error(f"Background sync error on attempt {attempt + 1}: {str(e)}")

                    # If it's a concurrency error, wait and retry
                    if "concurrent update" in str(e) or "transaction is aborted" in str(e):
                        if attempt < max_retries - 1:  # Don't sleep on last attempt
                            time.sleep(retry_delay)
                            retry_delay *= 2  # Exponential backoff
                        else:
                            _logger.error("Max retries reached for background sync")
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
                                _logger.error(f"Error updating sync status to failed: {str(update_error)}")
                    else:
                        # For non-concurrency errors, don't retry
                        _logger.error(f"Non-concurrency error, not retrying: {str(e)}")
                        import traceback
                        _logger.error(f"Background sync full traceback: {traceback.format_exc()}")

                        # Set sync status to "failed"
                        try:
                            registry = Registry(current_dbname)
                            with registry.cursor() as cr:
                                env = api.Environment(cr, SUPERUSER_ID, {})
                                config = env['res.config.settings'].sudo().search([], limit=1)
                                if not config:
                                    config = env['res.config.settings'].sudo().create({})
                                    _logger.info(
                                        "Created new res.config.settings record for sync status tracking (failed phase, non-concurrency error).")
                                config.write({
                                    'ghl_locations_sync_status': 'failed',
                                    'ghl_locations_sync_error': str(e)
                                })
                                _logger.info(f"Set sync status to failed on config id={config.id}")
                        except Exception as update_error:
                            _logger.error(f"Error updating sync status to failed: {str(update_error)}")
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
            _logger.error(f"Error in fast installed locations endpoint: {str(e)}")
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
        _logger.info(f"Using app_id: {app_id}")

        # Hardcode company_id
        company_id = 'Ipg8nKDPLYKsbtodR6LN'
        _logger.info(f"Using hardcoded company_id: {company_id}")

        # Call the fetch_installed_locations function from the model (synchronous)
        installed_location_model = request.env['installed.location'].sudo()
        _logger.info(f"Calling fetch_installed_locations with company_id={company_id}, app_id={app_id}")
        result = installed_location_model.fetch_installed_locations(
            company_id=company_id,
            app_id=app_id,
            limit=500,
            fetch_details=True  # Fetch details for the overview page refresh
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
            _logger.error(f"Error getting sync status: {str(e)}")
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
            _logger.warning(f"App {app.name} is not installed on location {location_id}")
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
            _logger.warning(f"Location {location_id} is not marked as installed")
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
        _logger.info(f"[get-location-contacts] GHL contact task sync result: {json.dumps(task_sync_result)}")

        # Sync GHL conversations for this location (contact by contact)
        _logger.info(f"Starting conversation sync for location: {location_id}")
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
                        _logger.info(
                            f"Conversation sync successful for contact {contact.external_id}: {contact_result}")
                    else:
                        _logger.error(
                            f"Conversation sync failed for contact {contact.external_id}: {contact_result.get('error')}")
                except Exception as contact_error:
                    _logger.error(
                        f"Error syncing conversations for contact {contact.external_id}: {str(contact_error)}")

            conversation_sync_result = {
                'success': total_contacts_synced > 0,
                'message': f'Synced conversations for {total_contacts_synced} contacts. Created: {total_created}, Updated: {total_updated}',
                'total_contacts_synced': total_contacts_synced,
                'total_created': total_created,
                'total_updated': total_updated
            }

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
                        _logger.info(f"Set contacts sync status to in_progress for location {location_id}")
                        break
                except Exception as e:
                    if "concurrent update" in str(e) or "serialize access" in str(e):
                        if attempt < max_retries - 1:
                            _logger.warning(
                                f"Concurrency error setting in_progress status, retrying in {retry_delay} seconds...")
                            time.sleep(retry_delay)
                            retry_delay *= 2
                        else:
                            _logger.error("Max retries reached for setting in_progress status")
                    else:
                        _logger.error(f"Error setting contacts sync status to in_progress: {str(e)}")
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
                        _logger.error("No valid access token found in background sync")
                        return
                    access_token = app_record.access_token
                    loc_record = env['installed.location'].search([('location_id', '=', location_id)], limit=1)
                    if not loc_record:
                        _logger.error(f"Location not found in background sync: {location_id}")
                        return
                    result = loc_record.fetch_location_contacts(company_id, location_id, access_token)
                    _logger.info(f"Background contact sync result: {result}")
                    cr.commit()
                # --- Task Sync ---
                with registry.cursor() as cr:
                    env = api.Environment(cr, SUPERUSER_ID, {})
                    task_result = env['ghl.contact.task'].sync_all_contact_tasks_optimized(
                        access_token, location_id, company_id
                    )
                    _logger.info(f"Background optimized task sync result: {task_result}")
                    cr.commit()
                # --- Conversation Sync ---
                with registry.cursor() as cr:
                    env = api.Environment(cr, SUPERUSER_ID, {})
                    # Per-contact conversation sync is handled elsewhere if needed
                    # If you want to keep the old logic, you can loop here
                    # For now, just log that this step is isolated
                    _logger.info(f"Background conversation sync step (isolated cursor)")
                    # Example: conv_result = ...
                    cr.commit()
                # --- Opportunity Sync ---
                with registry.cursor() as cr:
                    env = api.Environment(cr, SUPERUSER_ID, {})
                    opp_result = env['ghl.contact.opportunity'].sync_opportunities_for_location(
                        access_token, location_id, company_id, max_pages=None
                    )
                    _logger.info(f"Background opportunity sync result: {opp_result}")
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
                                    _logger.warning(
                                        f"Concurrency error on completed, retrying in {retry_delay} seconds...")
                                    time.sleep(retry_delay)
                                    retry_delay *= 2
                                else:
                                    _logger.error("Max retries reached for config write (completed phase)")
                            else:
                                _logger.error(f"Error setting contacts sync status to completed: {str(e)}")
                                break
            except Exception as e:
                _logger.error(f"Background sync error: {str(e)}")
                import traceback
                _logger.error(f"Background sync full traceback: {traceback.format_exc()}")
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
                                _logger.warning(f"Concurrency error on failed, retrying in 2 seconds...")
                                time.sleep(2)
                            else:
                                _logger.error("Max retries reached for config write (failed phase)")
                        else:
                            _logger.error(f"Error updating contacts sync status to failed: {str(update_error)}")
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
            _logger.error(f"Error in fast contacts endpoint: {str(e)}")
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
        _logger.info(f"Syncing fresh data from GHL API for location: {location_id}")
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
                    _logger.warning(f"App {app.name} is not installed on location {location_id}")
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
                    _logger.warning(f"Location {location_id} is not marked as installed")
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
                _logger.info(f"Syncing contacts for location: {location_id}")
                contact_sync_result = loc.fetch_location_contacts(company_id, location_id, access_token)
                sync_summary['contacts_synced'] = contact_sync_result.get('success', False)
                _logger.info(f"Contact sync result: {contact_sync_result}")

                # SYNC TASKS FOR ALL CONTACTS
                _logger.info(f"Syncing tasks for location: {location_id}")
                task_sync_result = request.env['ghl.contact.task'].sudo().sync_all_contact_tasks(access_token,
                                                                                                 location_id,
                                                                                                 company_id)
                sync_summary['tasks_synced'] = task_sync_result.get('success', False)
                _logger.info(f"Task sync result: {task_sync_result}")

                # SYNC CONVERSATIONS FOR ALL CONTACTS
                _logger.info(f"Syncing conversations for location: {location_id}")
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
                _logger.info(f"Syncing opportunities for location: {location_id}")
                opportunity_sync_result = request.env['ghl.contact.opportunity'].sudo().sync_opportunities_for_location(
                    access_token, location_id, company_id
                )
                sync_summary['opportunities_synced'] = opportunity_sync_result.get('success', False)
                _logger.info(f"Opportunity sync result: {opportunity_sync_result}")

                # SYNC MESSAGES FOR ALL CONVERSATIONS TO GET FRESH TOUCH DATA
                _logger.info(f"Syncing messages for all conversations to get fresh touch data")
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
                _logger.info(f"Updating touch information for all contacts")
                touch_update_result = request.env['ghl.location.contact'].sudo().update_all_contacts_touch_information()
                sync_summary['touch_info_updated'] = touch_update_result.get('contacts_updated', 0)
                _logger.info(f"Touch update result: {touch_update_result}")

        # Fetch fresh contacts from our database after all syncs
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
            _logger.info(f"App found: {app}")
            if not app or not app.access_token:
                _logger.error("No valid access token found for this app_id.")
                return Response(
                    json.dumps({'success': False, 'error': 'No valid access token found for this app_id.'}),
                    content_type='application/json',
                    status=400,
                    headers=get_cors_headers(request)
                )
            loc = request.env['installed.location'].sudo().search([('location_id', '=', location_id)], limit=1)
            _logger.info(f"Installed location found: {loc}")
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
                _logger.warning(f"App {app.name} is not installed on location {location_id}")
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
                _logger.warning(f"Location {location_id} is not marked as installed")
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
                _logger.info(f"User filter applied: {selected_user}, getting filtered count from GHL API")

                # Get filtered count directly from GHL API
                _logger.info(
                    f"Calling _get_filtered_contacts_count_from_ghl with: location_id={location_id}, selected_user={selected_user}")
                filtered_count_result = self._get_filtered_contacts_count_from_ghl(
                    location_id, selected_user, app.access_token, 'Ipg8nKDPLYKsbtodR6LN'
                )
                _logger.info(f"_get_filtered_contacts_count_from_ghl returned: {filtered_count_result}")

                if filtered_count_result.get('success'):
                    filtered_count = filtered_count_result.get('total_contacts', 0)
                    _logger.info(f"GHL API filtered contacts count: {filtered_count}")

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
                _logger.info(f"fetch_contacts_count result: {result}")
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
            _logger.info(f"App found: {app}")
            if not app or not app.access_token:
                _logger.error("No valid access token found for this app_id.")
                return Response(
                    json.dumps({'success': False, 'error': 'No valid access token found for this app_id.'}),
                    content_type='application/json',
                    status=400,
                    headers=get_cors_headers(request)
                )
            loc = request.env['installed.location'].sudo().search([('location_id', '=', location_id)], limit=1)
            _logger.info(f"Installed location found: {loc}")
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
                _logger.warning(f"App {app.name} is not installed on location {location_id}")
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
                _logger.warning(f"Location {location_id} is not marked as installed")
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
            _logger.info(f"Fetching fresh contact data from GHL API for location: {location_id}")
            result = loc.fetch_location_contacts_lazy(company_id, location_id, app.access_token, page=page, limit=limit)
            _logger.info(f"fetch_location_contacts_lazy result: {result}")

            if result.get('success'):
                # SYNC TASKS FOR ALL CONTACTS IN THIS LOCATION
                _logger.info(f"Syncing tasks for location: {location_id}")
                task_sync_result = request.env['ghl.contact.task'].sudo().sync_all_contact_tasks(
                    app.access_token, location_id, company_id
                )
                _logger.info(f"Task sync result: {task_sync_result}")

                # SYNC CONVERSATIONS FOR ALL CONTACTS IN THIS LOCATION
                _logger.info(f"Syncing conversations for location: {location_id}")
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
                _logger.info(f"Syncing opportunities for location: {location_id}")
                opportunity_sync_result = request.env['ghl.contact.opportunity'].sudo().sync_opportunities_for_location(
                    app.access_token, location_id, company_id
                )
                _logger.info(f"Opportunity sync result: {opportunity_sync_result}")

                # SYNC MESSAGES FOR ALL CONVERSATIONS TO GET FRESH TOUCH DATA
                _logger.info(f"Syncing messages for all conversations to get fresh touch data")
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
                _logger.info(f"Updating touch information for all contacts")
                touch_update_result = request.env['ghl.location.contact'].sudo().update_all_contacts_touch_information()
                _logger.info(f"Touch update result: {touch_update_result}")

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
                        _logger.info(f"Successfully synced conversations for contact {contact.id}")
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
                        _logger.info(f"Successfully synced tasks for contact {contact.id}")
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

                _logger.info(f"Updated touch information for contact {contact.id}: {touch_summary}")
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
        _logger.info(f"fetch_messages_for_contact called for contact_id: {contact_id}")
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
                        _logger.info(
                            f"Conversation {conversation.ghl_id} already has {len(existing_messages)} messages, skipping")
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
                        _logger.info(f"Fetched {messages_fetched} messages for conversation {conversation.ghl_id}")
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
        _logger.info(f"update_touch_info called for contact_id: {contact_id}")
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

            _logger.info(f"Found {len(messages)} messages for contact {contact_id}")

            # Count messages by type
            message_counts = {}
            for message in messages:
                message_type = message.message_type or 'UNKNOWN'
                message_counts[message_type] = message_counts.get(message_type, 0) + 1

            _logger.info(f"Message counts: {message_counts}")

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
            _logger.info(f"Fetching fresh messages from GHL API for contact {contact.external_id}")

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
                                    _logger.info(f"Fetching fresh messages for conversation {conversation.ghl_id}")
                                    message_result = request.env[
                                        'ghl.contact.message'].sudo().fetch_messages_for_conversation(
                                        conversation_id=conversation.ghl_id,
                                        access_token=location_token,
                                        location_id=contact.location_id.id,
                                        contact_id=contact.id,
                                        limit=100  # Fetch more messages to get accurate counts
                                    )
                                    if message_result.get('success'):
                                        _logger.info(
                                            f"Successfully fetched fresh messages for conversation {conversation.ghl_id}")
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
                _logger.info(f"No messages found for contact {contact.id} after fresh GHL API fetch")
                return 'no_touches'

            # Filter for OUTBOUND messages only (from our side)
            outbound_messages = messages.filtered(lambda m: m.direction == 'outbound')

            _logger.info(
                f"Touch summary: {len(messages)} total messages, {len(outbound_messages)} outbound messages for contact {contact.id}")

            # Count outbound messages by type
            message_counts = {}
            for message in outbound_messages:
                message_type = message.message_type or 'UNKNOWN'
                message_counts[message_type] = message_counts.get(message_type, 0) + 1
                _logger.info(f"Outbound message type: {message_type}, count: {message_counts[message_type]}")

            # Create touch summary string in the format expected by frontend: "3 SMS, 1 PHONE CALL"
            touch_parts = []
            for msg_type, count in message_counts.items():
                # Map message types to readable names
                type_name = contact._get_message_type_display_name(msg_type)
                touch_parts.append(f"{count} {type_name}")

            result = ', '.join(touch_parts) if touch_parts else 'no_touches'
            _logger.info(f"Touch summary (outbound only) for contact {contact.id}: {result}")
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
            _logger.info(f"Fetching fresh messages from GHL API for engagement summary - contact {contact.external_id}")

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
                                    _logger.info(
                                        f"Fetching fresh messages for engagement - conversation {conversation.ghl_id}")
                                    message_result = request.env[
                                        'ghl.contact.message'].sudo().fetch_messages_for_conversation(
                                        conversation_id=conversation.ghl_id,
                                        access_token=location_token,
                                        location_id=contact.location_id.id,
                                        contact_id=contact.id,
                                        limit=100  # Fetch more messages to get accurate counts
                                    )
                                    if message_result.get('success'):
                                        _logger.info(
                                            f"Successfully fetched fresh messages for engagement - conversation {conversation.ghl_id}")
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
                _logger.info(f"No messages found for contact {contact.id} after fresh GHL API fetch")
                return []

            # Group ALL messages by type and count them (both inbound and outbound)
            engagement_data = []
            message_counts = {}

            _logger.info(f"Processing {len(messages)} messages for engagement summary for contact {contact.id}")

            for message in messages:
                message_type = message.message_type or 'UNKNOWN'
                message_counts[message_type] = message_counts.get(message_type, 0) + 1
                _logger.info(
                    f"Message type: {message_type}, direction: {message.direction}, count: {message_counts[message_type]}")

            # Convert to the format expected by frontend
            for msg_type, count in message_counts.items():
                engagement_data.append({
                    'type': msg_type,
                    'count': count,
                    'icon': self._get_engagement_icon(msg_type),
                    'color': self._get_engagement_color(msg_type)
                })

            _logger.info(
                f"Engagement summary (all touches) for contact {contact.id}: {len(engagement_data)} types - {engagement_data}")
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

    def _trigger_ghl_sync_for_contacts(self, contacts, access_token, company_id, location_id, app_id):
        """
        Trigger GHL API sync for contacts to ensure fresh data
        This method forces fresh data fetching from Go High Level API
        """
        import threading
        import time
        from datetime import datetime
        
        _logger.info(f"Starting GHL API sync for {len(contacts)} contacts")
        
        # Capture database name before starting background thread
        db_name = request.env.cr.dbname
        
        def sync_contacts_background():
            max_retries = 3
            retry_delay = 1
            
            for attempt in range(max_retries):
                try:
                    # Create a new environment for background thread
                    from odoo import api, SUPERUSER_ID
                    from odoo.modules.registry import Registry
                    import psycopg2
                    
                    # Use the captured database name
                    current_db_name = db_name

                    # Create a new environment for the background thread
                    registry = Registry(current_db_name)
                    with registry.cursor() as cr:
                        env = api.Environment(cr, SUPERUSER_ID, {})

                        # Get location token for GHL API calls
                        from odoo.addons.web_scraper.models.ghl_api_utils import get_location_token
                        location_token = get_location_token(access_token, company_id, location_id)

                        if not location_token:
                            _logger.error("Failed to get location token for GHL sync")
                            return

                        success_count = 0
                        error_count = 0

                        for contact in contacts:
                            try:
                                # Get the correct location ID for this contact
                                contact_location_id = contact.location_id.location_id if contact.location_id else location_id

                                # Sync conversations and messages for this contact
                                conversation_result = env[
                                    'ghl.contact.conversation'].sudo().sync_conversations_for_contact_with_location_token(
                                    location_token, contact_location_id, contact.external_id
                                )

                                if conversation_result.get('success'):
                                    # Sync tasks for this contact
                                    try:
                                        env['ghl.contact.task'].sync_contact_tasks_from_ghl(
                                            contact.id, access_token, location_id, company_id
                                        )
                                    except Exception as task_error:
                                        _logger.error(f"Error syncing tasks for contact {contact.name}: {str(task_error)}")
                                    
                                    success_count += 1
                                else:
                                    _logger.warning(f"Failed to sync conversations for contact {contact.name}: {conversation_result.get('error')}")
                                    error_count += 1

                            except Exception as contact_error:
                                _logger.error(f"Error syncing contact {contact.name}: {str(contact_error)}")
                                error_count += 1
                                continue

                        _logger.info(f"GHL API sync completed: {success_count} successful, {error_count} failed out of {len(contacts)} contacts")
                        return  # Success, exit retry loop

                except (psycopg2.errors.SerializationFailure, psycopg2.errors.DeadlockDetected) as db_error:
                    if attempt < max_retries - 1:
                        _logger.warning(f"Database concurrency error (attempt {attempt + 1}/{max_retries}): {str(db_error)}. Retrying in {retry_delay} seconds...")
                        time.sleep(retry_delay)
                        retry_delay *= 2  # Exponential backoff
                        continue
                    else:
                        _logger.error(f"Database concurrency error after {max_retries} attempts: {str(db_error)}")
                        return
                except Exception as e:
                    _logger.error(f"Error in background GHL sync: {str(e)}")
                    import traceback
                    _logger.error(f"Full traceback: {traceback.format_exc()}")
                    return  # Don't retry for non-concurrency errors

        # Start background sync in a separate thread
        sync_thread = threading.Thread(target=sync_contacts_background, daemon=True)
        sync_thread.start()

        _logger.info("GHL API sync started in background thread")

    @http.route('/api/sync-contact-data', type='http', auth='none', methods=['POST', 'OPTIONS'], csrf=False)
    def sync_contact_data(self, **kwargs):
        """
        Manual endpoint to force sync data for a specific contact from GHL API
        """
        if request.httprequest.method == 'OPTIONS':
            return Response(status=200, headers=get_cors_headers(request))

        try:
            data = json.loads(request.httprequest.data.decode('utf-8'))
            contact_id = data.get('contact_id')
            location_id = data.get('location_id')
            app_id = data.get('app_id') or kwargs.get('appId')

            if not contact_id or not location_id:
                return Response(
                    json.dumps({'success': False, 'error': 'contact_id and location_id are required'}),
                    content_type='application/json',
                    status=400,
                    headers=get_cors_headers(request)
                )

            if not app_id:
                return Response(
                    json.dumps({'success': False, 'error': 'app_id is required'}),
                    content_type='application/json',
                    status=400,
                    headers=get_cors_headers(request)
                )

            # Get the contact
            contact = request.env['ghl.location.contact'].sudo().search([
                ('id', '=', contact_id)
            ], limit=1)

            if not contact:
                return Response(
                    json.dumps({'success': False, 'error': 'Contact not found'}),
                    content_type='application/json',
                    status=404,
                    headers=get_cors_headers(request)
                )

            # Get app access token using the correct app_id
            app = request.env['cyclsales.application'].sudo().search([
                ('app_id', '=', app_id),
                ('is_active', '=', True)
            ], limit=1)

            if not app or not app.access_token:
                return Response(
                    json.dumps({'success': False, 'error': f'No valid access token found for app_id: {app_id}'}),
                    content_type='application/json',
                    status=400,
                    headers=get_cors_headers(request)
                )

            # Get company_id from agency token
            agency_token = request.env['ghl.agency.token'].sudo().search([], order='create_date desc', limit=1)
            if not agency_token:
                return Response(
                    json.dumps({'success': False, 'error': 'No agency token found'}),
                    content_type='application/json',
                    status=400,
                    headers=get_cors_headers(request)
                )

            company_id = agency_token.company_id
            _logger.info(f"Using company_id from agency token: {company_id}")
            _logger.info(
                f"Agency token details: company_id={agency_token.company_id}, access_token={agency_token.access_token[:20] if agency_token.access_token else 'None'}...")

            # Get location token
            from odoo.addons.web_scraper.models.ghl_api_utils import get_location_token
            _logger.info(
                f"Getting location token for app_id: {app_id}, company_id: {company_id}, location_id: {location_id}")
            _logger.info(f"Using app access_token: {app.access_token[:20]}...")
            location_token = get_location_token(app.access_token, company_id, location_id)
            _logger.info(f"Location token result: {location_token[:20] if location_token else 'None'}...")

            if not location_token:
                return Response(
                    json.dumps({'success': False, 'error': 'Failed to get location token'}),
                    content_type='application/json',
                    status=400,
                    headers=get_cors_headers(request)
                )

            _logger.info(
                f"Manually syncing data for contact {contact.name} (ID: {contact.id}, External ID: {contact.external_id})")

            # Get the correct location ID for this contact
            contact_location_id = contact.location_id.location_id if contact.location_id else location_id
            _logger.info(
                f"Using location ID: {contact_location_id} for contact {contact.name} (requested location_id: {location_id})")

            # Sync conversations and messages using the correct parameter order
            conversation_result = request.env[
                'ghl.contact.conversation'].sudo().sync_conversations_for_contact_with_location_token(
                location_token, contact_location_id, contact.external_id
            )

            # Check messages after sync
            all_messages = request.env['ghl.contact.message'].sudo().search([
                ('contact_id', '=', contact.id)
            ])

            _logger.info(f"Manual sync completed for {contact.name}: {len(all_messages)} messages found")

            return Response(
                json.dumps({
                    'success': True,
                    'message': f'Successfully synced data for {contact.name}',
                    'conversation_sync': conversation_result,
                    'messages_found': len(all_messages)
                }),
                content_type='application/json',
                status=200,
                headers=get_cors_headers(request)
            )

        except Exception as e:
            _logger.error(f"Error in sync_contact_data: {str(e)}")
            import traceback
            _logger.error(f"Full traceback: {traceback.format_exc()}")
            return Response(
                json.dumps({'success': False, 'error': str(e)}),
                content_type='application/json',
                status=500,
                headers=get_cors_headers(request)
            )

    def _compute_last_message_for_contact(self, contact):
        """Compute last message for a contact on-the-fly"""
        # First try to get from existing messages
        last_message = request.env['ghl.contact.message'].sudo().search([
            ('contact_id', '=', contact.id)
        ], order='date_added desc', limit=1)

        if last_message and last_message.body:
            import json
            message_data = {
                'body': last_message.body,
                'type': last_message.message_type,
                'direction': last_message.direction,
                'date_added': last_message.date_added.isoformat() if last_message.date_added else '',
                'id': last_message.ghl_id
            }
            return json.dumps(message_data)
        else:
            # If no messages, try to fetch them (this will be handled by _compute_touch_summary_for_contact)
            # For now, return empty string
            return ''

    @http.route('/api/location-contacts-optimized', type='http', auth='none', methods=['GET', 'OPTIONS'], csrf=False)
    def get_location_contacts_optimized(self, **kwargs):
        """
        Optimized endpoint that returns basic contact data immediately and fetches fresh data from GHL API in background
        - Returns contact names from Odoo immediately
        - Triggers GHL API sync for fresh data in background
        - Ensures real-time data from Go High Level
        """
        if request.httprequest.method == 'OPTIONS':
            return Response(status=200, headers=get_cors_headers(request))

        location_id = kwargs.get('location_id')
        page = int(kwargs.get('page', 1))
        limit = int(kwargs.get('limit', 10))
        selected_user = kwargs.get('selected_user', '')  # New parameter for user filtering

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
                _logger.warning(f"App {app.name} is not installed on location {location_id}")
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
                _logger.warning(f"Location {location_id} is not marked as installed")
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

            # STEP 1: Ensure we have enough contacts fetched from GHL API to cover the requested page
            _logger.info(f"Ensuring we have contacts up to page {page} from GHL API for location: {location_id}")

            # Check how many contacts we currently have in the database
            current_contact_count = request.env['ghl.location.contact'].sudo().search_count([
                ('location_id.location_id', '=', location_id)
            ])

            # Calculate how many contacts we need for the requested page
            contacts_needed = page * limit

            # If we don't have enough contacts, fetch more from GHL API
            if current_contact_count < contacts_needed:
                _logger.info(
                    f"Need {contacts_needed} contacts, have {current_contact_count}. Fetching more from GHL API...")

                # Calculate how many pages we need to fetch
                pages_to_fetch = (contacts_needed - current_contact_count + limit - 1) // limit
                start_page = (current_contact_count // limit) + 1

                for fetch_page in range(start_page, start_page + pages_to_fetch):
                    _logger.info(f"Fetching page {fetch_page} from GHL API...")
                    result = loc.fetch_location_contacts_lazy(company_id, location_id, app.access_token,
                                                              page=fetch_page, limit=limit)

                    if not result.get('success'):
                        _logger.error(f"Failed to fetch page {fetch_page}: {result.get('error')}")
                        break

                    # Check if we got any new contacts
                    new_contact_count = request.env['ghl.location.contact'].sudo().search_count([
                        ('location_id.location_id', '=', location_id)
                    ])

                    if new_contact_count <= current_contact_count:
                        _logger.info(f"No new contacts fetched on page {fetch_page}, stopping")
                        break

                    current_contact_count = new_contact_count
                    _logger.info(f"Now have {current_contact_count} contacts after fetching page {fetch_page}")
            else:
                _logger.info(f"Already have {current_contact_count} contacts, sufficient for page {page}")

            # Get the result for the requested page
            result = loc.fetch_location_contacts_lazy(company_id, location_id, app.access_token, page=page, limit=limit)
            _logger.info(f"fetch_location_contacts_lazy result for page {page}: {result}")

            if not result.get('success'):
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

            # STEP 2: Get the contacts for the requested page from the database
            # Now that we've ensured we have enough contacts, we can properly paginate
            _logger.info(f"Querying database for page {page} with limit={limit}, offset={(page - 1) * limit}")

            # Build the domain for filtering contacts
            domain = [('location_id.location_id', '=', location_id)]

            # Add user filtering if selected_user is provided
            if selected_user and selected_user.strip():
                _logger.info(f"Filtering contacts by selected user (external_id): {selected_user}")

                # Since the frontend now sends the external_id directly, use it for filtering
                domain.append(('assigned_to', '=', selected_user))

                # Log the domain for debugging
                _logger.info(f"Applied user filter domain: {domain}")

            # First, let's see what contacts we have in total (with user filter if applicable)
            all_contacts = request.env['ghl.location.contact'].sudo().search(domain, order='date_added desc')

            _logger.info(f"Total contacts in database (with user filter): {len(all_contacts)}")


            # Now get the paginated contacts
            contacts = request.env['ghl.location.contact'].sudo().search(domain, order='date_added desc', limit=limit,
                                                                         offset=(page - 1) * limit)


            # Debug: Check if we have any contacts at all for this location
            if len(contacts) == 0:
                _logger.warning(f"No contacts found for location {location_id}. Checking if location exists...")
                location_check = request.env['installed.location'].sudo().search([
                    ('location_id', '=', location_id)
                ], limit=1)
                if location_check:
                    _logger.info(f"Location {location_id} exists in installed.location table")
                    # Check if there are any contacts at all for this location
                    all_contacts_for_location = request.env['ghl.location.contact'].sudo().search([
                        ('location_id.location_id', '=', location_id)
                    ])
                    _logger.info(f"Total contacts for location {location_id}: {len(all_contacts_for_location)}")
                else:
                    _logger.error(f"Location {location_id} not found in installed.location table")

            for contact in contacts:
                _logger.info(
                    f"Contact {contact.id} (external_id: {contact.external_id}) - AI fields in DB: status='{contact.ai_status}', summary='{contact.ai_summary}', quality='{contact.ai_quality_grade}', sales='{contact.ai_sales_grade}'")

            # STEP 3: Return basic contact data immediately and trigger GHL API sync
            contact_data = []
            contact_ids_for_background = []

            # STEP 3A: Trigger GHL API sync for fresh data in background
            _logger.info(f"Triggering GHL API sync for {len(contacts)} contacts to ensure fresh data")
            self._trigger_ghl_sync_for_contacts(contacts, app.access_token, company_id, location_id, app_id)

            for contact in contacts:
                contact_ids_for_background.append(contact.id)

                # Parse basic data from Odoo (immediate response)
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

                # Force fresh data computation from GHL API
                # These methods will now fetch fresh data from GHL API
                touch_summary = self._compute_touch_summary_for_contact(contact)
                last_touch_date = self._compute_last_touch_date_for_contact(contact)
                last_message_data = self._compute_last_message_content_for_contact(contact)
                engagement_summary = self._compute_engagement_summary_for_contact(contact)
                speed_to_lead = self._compute_speed_to_lead_for_contact(contact)

                # Debug: Log the computed field values
                _logger.info(f"Contact {contact.id} computed field values (fresh from GHL):")
                _logger.info(f"  touch_summary: '{touch_summary}'")
                _logger.info(f"  last_touch_date: '{last_touch_date}'")
                _logger.info(f"  last_message_data: '{last_message_data}'")
                _logger.info(f"  speed_to_lead: '{speed_to_lead}'")
                _logger.info(f"  engagement_summary: '{engagement_summary}'")

                # Get fresh counts from GHL API
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
                    'ai_summary': contact.ai_summary if contact.ai_summary else 'AI analysis pending',
                    'ai_reasoning': contact.ai_reasoning if contact.ai_reasoning else '<span style="color: #6b7280;">No analysis available</span>',
                    'ai_quality_grade': contact.ai_quality_grade if contact.ai_quality_grade else 'no_grade',
                    'ai_sales_grade': contact.ai_sales_grade if contact.ai_sales_grade else 'no_grade',
                    'ai_sales_reasoning': contact.ai_sales_reasoning if contact.ai_sales_reasoning else '<span style="color: #6b7280;">No sales grade analysis available</span>',
                    'crm_tasks': contact.crm_tasks or 'no_tasks',
                    'category': contact.category or 'manual',
                    'channel': contact.channel or 'manual',
                    'created_by': contact.created_by or '',
                    'attribution': contact.attribution or '',
                    'assigned_to': assigned_user_name,
                    'speed_to_lead': speed_to_lead,
                    'touch_summary': touch_summary,
                    'engagement_summary': engagement_summary,
                    'last_touch_date': last_touch_date,
                    'last_message': last_message_data,
                    'total_pipeline_value': contact.total_pipeline_value or 0.0,
                    'opportunities': contact.opportunities or 0,
                    'contact_tags': contact_tags,
                    'details_fetched': False,  # Details will be fetched on-demand
                    'has_tasks': tasks_count > 0,
                    'has_conversations': conversations_count > 0,
                    'tasks_count': tasks_count,
                    'conversations_count': conversations_count,
                    'conversations_count_basic': conversations_count,
                    'loading_details': False,  # No loading state initially
                }

                # Debug: Log AI fields for this contact
                _logger.info(
                    f"Contact {contact.id} (external_id: {contact.external_id}) - AI fields in DB: status='{contact.ai_status}', summary='{contact.ai_summary}', quality='{contact.ai_quality_grade}', sales='{contact.ai_sales_grade}'")
                _logger.info(
                    f"Contact {contact.id} AI fields being sent to frontend: status={contact_info['ai_status']}, summary={contact_info['ai_summary'][:50]}..., quality={contact_info['ai_quality_grade']}, sales={contact_info['ai_sales_grade']}")

                # Additional debug: Check if AI fields are actually saved
                if contact.ai_status and contact.ai_status != 'not_contacted':
                    _logger.info(
                        f"Contact {contact.id} has AI data: status='{contact.ai_status}', summary='{contact.ai_summary[:100] if contact.ai_summary else 'None'}...'")
                else:
                    _logger.info(f"Contact {contact.id} has NO AI data or default values")

                contact_data.append(contact_info)

            # STEP 4: Start background sync for detailed data (only for current page contacts)
            # DISABLED: Only start background sync if explicitly requested
            background_sync_enabled = kwargs.get('background_sync', 'false').lower() == 'true'

            if contact_ids_for_background and background_sync_enabled:
                # Capture database name before starting background thread
                dbname = request.env.cr.dbname

                def background_sync_details():
                    from odoo import api, SUPERUSER_ID
                    from odoo.modules.registry import Registry
                    import time
                    from datetime import datetime

                    current_dbname = dbname
                    max_retries = 3
                    retry_delay = 2

                    # Small delay to avoid immediate concurrency
                    time.sleep(0.5)

                    try:
                        registry = Registry(current_dbname)

                        # Get fresh access token
                        with registry.cursor() as cr:
                            env = api.Environment(cr, SUPERUSER_ID, {})
                            app_record = env['cyclsales.application'].search([
                                ('app_id', '=', app_id),
                                ('is_active', '=', True)
                            ], limit=1)
                            if not app_record or not app_record.access_token:
                                _logger.error("No valid access token found in background sync")
                                return
                            access_token = app_record.access_token

                        # Sync detailed data for each contact
                        for contact_id in contact_ids_for_background:
                            try:
                                with registry.cursor() as cr:
                                    env = api.Environment(cr, SUPERUSER_ID, {})
                                    contact = env['ghl.location.contact'].browse(contact_id)
                                    if not contact.exists():
                                        continue

                                    # Mark contact as having details fetched first with retry mechanism
                                    try:
                                        self._update_contact_touch_info_with_retry(contact, {'details_fetched': True})
                                        cr.commit()
                                    except Exception as write_error:
                                        _logger.error(
                                            f"Background: Error marking contact {contact.external_id} as details_fetched: {str(write_error)}")
                                        cr.rollback()

                                    _logger.info(f"Background: Starting sync for contact {contact.external_id}")

                            except Exception as e:
                                _logger.error(f"Background: Error preparing contact {contact_id}: {str(e)}")
                                continue

                            # Sync tasks for this contact (separate transaction)
                            try:
                                with registry.cursor() as cr:
                                    env = api.Environment(cr, SUPERUSER_ID, {})
                                    contact = env['ghl.location.contact'].browse(contact_id)
                                    if contact.exists():
                                        _logger.info(f"Background: Syncing tasks for contact {contact.external_id}")
                                        try:
                                            env['ghl.contact.task'].sync_contact_tasks_from_ghl(
                                                contact.id, access_token, contact.location_id.location_id, company_id
                                            )
                                            cr.commit()
                                        except Exception as task_error:
                                            _logger.error(
                                                f"Background: Error syncing tasks for contact {contact.external_id}: {str(task_error)}")
                                            cr.rollback()
                            except Exception as e:
                                _logger.error(
                                    f"Background: Error in task sync transaction for contact {contact_id}: {str(e)}")

                            # Sync conversations for this contact (separate transaction)
                            try:
                                with registry.cursor() as cr:
                                    env = api.Environment(cr, SUPERUSER_ID, {})
                                    contact = env['ghl.location.contact'].browse(contact_id)
                                    if contact.exists():
                                        _logger.info(
                                            f"Background: Syncing conversations for contact {contact.external_id}")
                                        try:
                                            env['ghl.contact.conversation'].sync_conversations_for_contact(
                                                access_token, contact.location_id.location_id, contact.external_id
                                            )
                                            cr.commit()
                                        except Exception as conv_error:
                                            _logger.error(
                                                f"Background: Error syncing conversations for contact {contact.external_id}: {str(conv_error)}")
                                            cr.rollback()
                            except Exception as e:
                                _logger.error(
                                    f"Background: Error in conversation sync transaction for contact {contact_id}: {str(e)}")

                            # Sync opportunities for this contact (separate transaction)
                            try:
                                with registry.cursor() as cr:
                                    env = api.Environment(cr, SUPERUSER_ID, {})
                                    contact = env['ghl.location.contact'].browse(contact_id)
                                    if contact.exists():
                                        _logger.info(
                                            f"Background: Syncing opportunities for contact {contact.external_id}")
                                        try:
                                            env['ghl.contact.opportunity'].sync_opportunities_for_contact(
                                                access_token, contact.location_id.location_id, contact.external_id,
                                                company_id
                                            )
                                            cr.commit()
                                        except Exception as opp_error:
                                            _logger.error(
                                                f"Background: Error syncing opportunities for contact {contact.external_id}: {str(opp_error)}")
                                            cr.rollback()
                            except Exception as e:
                                _logger.error(
                                    f"Background: Error in opportunity sync transaction for contact {contact_id}: {str(e)}")

                            # Fetch messages for conversations (separate transaction per conversation)
                            try:
                                with registry.cursor() as cr:
                                    env = api.Environment(cr, SUPERUSER_ID, {})
                                    contact = env['ghl.location.contact'].browse(contact_id)
                                    if contact.exists():
                                        try:
                                            conversations = env['ghl.contact.conversation'].search([
                                                ('contact_id', '=', contact_id)
                                            ])
                                            cr.commit()
                                        except Exception as conv_search_error:
                                            _logger.error(
                                                f"Background: Error searching conversations for contact {contact.external_id}: {str(conv_search_error)}")
                                            cr.rollback()
                                            continue

                                        for conversation in conversations:
                                            # Each conversation gets its own transaction
                                            try:
                                                with registry.cursor() as conv_cr:
                                                    conv_env = api.Environment(conv_cr, SUPERUSER_ID, {})
                                                    try:
                                                        location_token_result = conv_env[
                                                            'ghl.contact.conversation']._get_location_token(
                                                            access_token,
                                                            conversation.contact_id.location_id.location_id, company_id
                                                        )

                                                        if location_token_result['success']:
                                                            conv_env[
                                                                'ghl.contact.message'].fetch_messages_for_conversation(
                                                                conversation_id=conversation.ghl_id,
                                                                access_token=location_token_result['access_token'],
                                                                location_id=conversation.contact_id.location_id.id,
                                                                contact_id=conversation.contact_id.id,
                                                                limit=100
                                                            )
                                                            conv_cr.commit()
                                                            _logger.info(
                                                                f"Background: Successfully fetched messages for conversation {conversation.ghl_id}")
                                                        else:
                                                            _logger.error(
                                                                f"Background: Failed to get location token for conversation {conversation.ghl_id}")
                                                    except Exception as msg_error:
                                                        _logger.error(
                                                            f"Background: Error fetching messages for conversation {conversation.ghl_id}: {str(msg_error)}")
                                                        conv_cr.rollback()
                                            except Exception as conv_transaction_error:
                                                _logger.error(
                                                    f"Background: Error in conversation transaction for {conversation.ghl_id}: {str(conv_transaction_error)}")
                            except Exception as e:
                                _logger.error(
                                    f"Background: Error in message sync transaction for contact {contact_id}: {str(e)}")

                            # Update touch information for this contact (separate transaction)
                            try:
                                with registry.cursor() as cr:
                                    env = api.Environment(cr, SUPERUSER_ID, {})
                                    contact = env['ghl.location.contact'].browse(contact_id)
                                    if contact.exists():
                                        try:
                                            contact.update_touch_information()
                                            cr.commit()
                                        except Exception as touch_error:
                                            _logger.error(
                                                f"Background: Error updating touch information for contact {contact.external_id}: {str(touch_error)}")
                                            cr.rollback()
                            except Exception as e:
                                _logger.error(
                                    f"Background: Error in touch update transaction for contact {contact_id}: {str(e)}")

                            _logger.info(f"Background: Completed detailed sync for contact {contact_id}")

                        _logger.info(
                            f"Background: Completed detailed sync for {len(contact_ids_for_background)} contacts")

                    except Exception as e:
                        _logger.error(f"Background sync error: {str(e)}")
                        import traceback
                        _logger.error(f"Background sync full traceback: {traceback.format_exc()}")

                # Start background sync thread
                sync_thread = threading.Thread(target=background_sync_details)
                sync_thread.daemon = True
                sync_thread.start()
                _logger.info(f"Started background sync for {len(contact_ids_for_background)} contacts")

            # Get the actual total count from the database (respecting user filter if applied)
            total_contacts_in_db = request.env['ghl.location.contact'].sudo().search_count(domain)

            # Calculate if there are more pages
            has_more_pages = (page * limit) < total_contacts_in_db

            # Debug logging
            _logger.info(f"Returning contacts data for location {location_id}:")
            _logger.info(f"  User filter applied: {selected_user if selected_user else 'None'}")
            _logger.info(f"  Total contacts in DB (with filter): {total_contacts_in_db}")
            _logger.info(f"  Contact data length: {len(contact_data)}")
            _logger.info(f"  Page: {page}, Limit: {limit}, Has more: {has_more_pages}")
            _logger.info(f"  First few contacts: {contact_data[:2] if contact_data else 'No contacts'}")

            return Response(
                json.dumps({
                    'success': True,
                    'contacts': contact_data,
                    'total_contacts': total_contacts_in_db,
                    'page': page,
                    'limit': limit,
                    'has_more': has_more_pages,
                    'created_count': result.get('created_count', 0),
                    'updated_count': result.get('updated_count', 0),
                    'message': 'Basic data returned. Background sync disabled by default.',
                    'background_sync_started': False,  # Always false now
                    'contacts_syncing': 0  # Always 0 now
                }),
                content_type='application/json',
                status=200,
                headers=get_cors_headers(request)
            )

        except Exception as e:
            import traceback
            tb = traceback.format_exc()
            _logger.error(f"Exception in get_location_contacts_optimized: {str(e)}\n{tb}")
            return Response(
                json.dumps({'success': False, 'error': str(e), 'traceback': tb}),
                content_type='application/json',
                status=500,
                headers=get_cors_headers(request)
            )

    @http.route('/api/location-contacts-search', type='http', auth='none', methods=['GET', 'OPTIONS'], csrf=False)
    def search_location_contacts(self, **kwargs):
        """
        Search contacts by name in real-time with GHL API integration
        
        This endpoint provides a hybrid search approach:
        1. First searches the local Odoo database for contacts
        2. If insufficient local results (< threshold), searches GoHighLevel API
        3. Combines and deduplicates results from both sources
        4. Optionally creates new contact records from GHL API results
        
        Configuration options (via res.config.settings):
        - ghl_enable_api_search: Enable/disable GHL API search
        - ghl_search_threshold: Minimum local results before skipping GHL API
        - ghl_search_limit: Maximum contacts to fetch from GHL API
        - ghl_api_timeout: Timeout for GHL API requests
        - ghl_auto_create_contacts: Auto-create contacts from GHL API results
        - final_contact_limit: Maximum total contacts to return
        - local_search_limit: Maximum contacts from local search
        - cross_location_limit: Maximum contacts from cross-location search
        
        GHL API search uses 'contains' operator on firstNameLowerCase and lastNameLowerCase fields
        as per the GHL API documentation.
        """
        if request.httprequest.method == 'OPTIONS':
            return Response(status=200, headers=get_cors_headers(request))

        location_id = kwargs.get('location_id')
        search_term = kwargs.get('search', '').strip()
        selected_user = kwargs.get('selected_user', '')  # New parameter for user filtering

        _logger.info(
            f"Search request - location_id: {location_id}, search_term: '{search_term}', selected_user: '{selected_user}'")

        if not location_id:
            return Response(
                json.dumps({'success': False, 'error': 'location_id is required'}),
                content_type='application/json',
                status=400,
                headers=get_cors_headers(request)
            )

        if not search_term:
            return Response(
                json.dumps({'success': False, 'error': 'search term is required'}),
                content_type='application/json',
                status=400,
                headers=get_cors_headers(request)
            )

        try:
            import time
            start_time = time.time()

            app_id = self._get_app_id_from_request(kwargs)
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

            # Check if GHL API search is enabled in configuration
            config = request.env['res.config.settings'].sudo().search([], limit=1)
            ghl_search_enabled = config.ghl_enable_api_search if config and hasattr(config,
                                                                                    'ghl_enable_api_search') else True
            ghl_auto_create = config.ghl_auto_create_contacts if config and hasattr(config,
                                                                                    'ghl_auto_create_contacts') else True

            # Initialize all configuration variables with defaults
            ghl_threshold = config.ghl_search_threshold if config and hasattr(config, 'ghl_search_threshold') else 10
            ghl_search_limit = config.ghl_search_limit if config and hasattr(config, 'ghl_search_limit') else 50
            ghl_api_timeout = config.ghl_api_timeout if config and hasattr(config, 'ghl_api_timeout') else 10
            final_contact_limit = config.final_contact_limit if config and hasattr(config,
                                                                                   'final_contact_limit') else 50
            local_search_limit = config.local_search_limit if config and hasattr(config, 'local_search_limit') else 50
            cross_location_limit = config.cross_location_limit if config and hasattr(config,
                                                                                     'cross_location_limit') else 50

            _logger.info(f"GHL API search enabled: {ghl_search_enabled}, auto-create contacts: {ghl_auto_create}")
            _logger.info(
                f"GHL search threshold: {ghl_threshold}, limit: {ghl_search_limit}, timeout: {ghl_api_timeout}")

            # Search contacts in database by name (case-insensitive)
            _logger.info(f"Searching for term: '{search_term}' in location: {location_id}")

            # First, let's see what contacts exist in this location
            all_location_contacts = request.env['ghl.location.contact'].sudo().search([
                ('location_id.location_id', '=', location_id)
            ])

            # First, find the installed.location record
            installed_location = request.env['installed.location'].sudo().search([
                ('location_id', '=', location_id)
            ], limit=1)

            if not installed_location:
                return Response(
                    json.dumps({'success': False, 'error': f'No location found with ID: {location_id}'}),
                    content_type='application/json',
                    status=400,
                    headers=get_cors_headers(request)
                )

            # Perform case-insensitive search across multiple fields with OR logic
            search_conditions = [
                ('location_id', '=', installed_location.id),
                '|',
                ('name', 'ilike', f'%{search_term}%'),
                ('first_name', 'ilike', f'%{search_term}%'),
                ('last_name', 'ilike', f'%{search_term}%'),
                ('email', 'ilike', f'%{search_term}%')
            ]
            _logger.info(f"Search conditions: {search_conditions}")

            # Build user filter domain if selected_user is provided
            user_filter_domain = []
            if selected_user and selected_user.strip():
                _logger.info(f"Adding user filter to search: {selected_user}")
                # Find the user by name to get their external_id
                user_record = request.env['ghl.location.user'].sudo().search([
                    ('location_id', '=', location_id),
                    '|',
                    ('name', '=', selected_user),
                    '&', ('first_name', '!=', False), ('last_name', '!=', False),
                    ('first_name', 'ilike', selected_user.split()[0] if selected_user.split() else ''),
                    ('last_name', 'ilike', selected_user.split()[-1] if len(selected_user.split()) > 1 else '')
                ], limit=1)

                if user_record:
                    _logger.info(
                        f"Found user record for search: {user_record.name} with external_id: {user_record.external_id}")
                    user_filter_domain = [('assigned_to', '=', user_record.external_id)]
                else:
                    _logger.warning(f"No user found with name: {selected_user} for search")
                    # If no user found, return empty result
                    return Response(
                        json.dumps({
                            'success': True,
                            'contacts': [],
                            'total_contacts': 0
                        }),
                        content_type='application/json',
                        headers=get_cors_headers(request)
                    )

            # Use direct searches for each field to avoid database corruption issues
            name_contacts = request.env['ghl.location.contact'].sudo().search([
                                                                                  ('location_id', '=',
                                                                                   installed_location.id),
                                                                                  ('name', 'ilike', f'%{search_term}%')
                                                                              ] + user_filter_domain)

            first_name_contacts = request.env['ghl.location.contact'].sudo().search([
                                                                                        ('location_id', '=',
                                                                                         installed_location.id),
                                                                                        ('first_name', 'ilike',
                                                                                         f'%{search_term}%')
                                                                                    ] + user_filter_domain)

            last_name_contacts = request.env['ghl.location.contact'].sudo().search([
                                                                                       ('location_id', '=',
                                                                                        installed_location.id),
                                                                                       ('last_name', 'ilike',
                                                                                        f'%{search_term}%')
                                                                                   ] + user_filter_domain)

            email_contacts = request.env['ghl.location.contact'].sudo().search([
                                                                                   ('location_id', '=',
                                                                                    installed_location.id),
                                                                                   (
                                                                                   'email', 'ilike', f'%{search_term}%')
                                                                               ] + user_filter_domain)

            # Combine all results and remove duplicates
            all_contact_ids = set()
            for contact in name_contacts:
                all_contact_ids.add(contact.id)
            for contact in first_name_contacts:
                all_contact_ids.add(contact.id)
            for contact in last_name_contacts:
                all_contact_ids.add(contact.id)
            for contact in email_contacts:
                all_contact_ids.add(contact.id)

            contacts = request.env['ghl.location.contact'].sudo().browse(list(all_contact_ids))
            contacts = contacts.sorted('date_added', reverse=True)[:local_search_limit]  # Sort and limit

            # Debug: Check for contacts with search term in last_name specifically
            bar_lastname_contacts = request.env['ghl.location.contact'].sudo().search([
                ('location_id', '=', installed_location.id),
                ('last_name', 'ilike', f'%{search_term}%')
            ])
            _logger.info(f"Contacts with '{search_term}' in last_name: {len(bar_lastname_contacts)}")
            for contact in bar_lastname_contacts:
                _logger.info(f"Contact with '{search_term}' in last_name: {contact.name} (ID: {contact.id})")

            # If no results in current location, search across all locations
            if not contacts:
                _logger.info(f"No results found in location {location_id}, searching across all locations")
                search_domain = [
                    '|',
                    ('name', 'ilike', f'%{search_term}%'),
                    ('first_name', 'ilike', f'%{search_term}%'),
                    ('last_name', 'ilike', f'%{search_term}%'),
                    ('email', 'ilike', f'%{search_term}%')
                ]
                # Add user filter if provided
                if user_filter_domain:
                    search_domain.extend(user_filter_domain)
                contacts = request.env['ghl.location.contact'].sudo().search(search_domain, order='date_added desc',
                                                                             limit=cross_location_limit)

            _logger.info(f"Search found {len(contacts)} contacts matching '{search_term}'")

            # If we have sufficient local results, use them
            if len(contacts) >= ghl_threshold:
                _logger.info(f"Sufficient local results ({len(contacts)} >= {ghl_threshold}), skipping GHL API call")
                use_ghl_api = False
            else:
                _logger.info(f"Insufficient local results ({len(contacts)} < {ghl_threshold}), will try GHL API")
                use_ghl_api = True

            # Try GHL API search if we have insufficient local results and it's enabled
            ghl_contacts = []
            if use_ghl_api and ghl_search_enabled and app.access_token:
                try:
                    _logger.info(f"Searching GHL API for term: '{search_term}' in location: {location_id}")

                    # Step 1: Get location-specific access token using existing function
                    _logger.info("Getting location access token from GHL API...")

                    # Get the company_id from the app
                    app_company_id = app.company_id or company_id
                    _logger.info(f"Using company_id: {app_company_id} for location token request")

                    # Use the existing get_location_token function from ghl_api_utils
                    from odoo.addons.web_scraper.models.ghl_api_utils import get_location_token
                    location_token = get_location_token(
                        app.access_token,
                        app_company_id,
                        location_id
                    )

                    if not location_token:
                        _logger.error("Failed to get location access token")
                        raise Exception("Failed to get location access token")

                    _logger.info("Successfully obtained location access token")
                    _logger.info(
                        f"Location token: {location_token[:20]}...{location_token[-20:] if len(location_token) > 40 else ''}")

                    # Step 2: Prepare GHL API search query using the correct format
                    # First try with the simple query field for better performance
                    ghl_search_query = {
                        "locationId": location_id,
                        "page": 1,
                        "pageLimit": ghl_search_limit,
                        "query": search_term,  # Simple text search across all fields
                        "sort": [
                            {
                                "field": "firstNameLowerCase",
                                "direction": "asc"
                            }
                        ]
                    }

                    # If we want more specific control, we can use filters instead:
                    # ghl_search_query = {
                    #     "locationId": location_id,
                    #     "page": 1,
                    #     "pageLimit": ghl_search_limit,
                    #     "filters": [
                    #         {
                    #             "group": "OR",
                    #             "filters": [
                    #                 {
                    #                     "field": "firstNameLowerCase",
                    #                     "operator": "contains",
                    #                     "value": search_term.lower()
                    #                 },
                    #                 {
                    #                     "field": "lastNameLowerCase",
                    #                     "operator": "contains", 
                    #                     "value": search_term.lower()
                    #                 }
                    #             ]
                    #         }
                    #     ],
                    #     "sort": [
                    #         {
                    #             "field": "firstNameLowerCase",
                    #             "direction": "asc"
                    #                 }
                    #         ]
                    # }

                    # Add user filter if provided
                    if user_filter_domain and selected_user:
                        ghl_search_query["assignedTo"] = user_filter_domain[0][2]  # Get the external_id

                    _logger.info(f"GHL API search query: {ghl_search_query}")

                    # Step 3: Make GHL API call with location token
                    import requests
                    ghl_url = "https://services.leadconnectorhq.com/contacts/search"
                    ghl_headers = {
                        "Authorization": f"Bearer {location_token}",
                        "Version": "2021-07-28",
                        "Content-Type": "application/json"
                    }

                    ghl_response = requests.post(
                        ghl_url,
                        json=ghl_search_query,
                        headers=ghl_headers,
                        timeout=ghl_api_timeout
                    )

                    if ghl_response.status_code == 200:
                        ghl_data = ghl_response.json()
                        ghl_contacts = ghl_data.get('contacts', [])
                        _logger.info(f"GHL API returned {len(ghl_contacts)} contacts")
                        _logger.info(f"GHL API response data keys: {list(ghl_data.keys())}")

                        # Log the first contact structure for debugging
                        if ghl_contacts:
                            first_contact = ghl_contacts[0]
                            _logger.info(f"First contact structure: {list(first_contact.keys())}")
                            _logger.info(f"Sample contact data: {first_contact}")

                        # Process GHL contacts and add them to local database if they don't exist
                        for ghl_contact in ghl_contacts:
                            # Check if contact already exists
                            existing_contact = request.env['ghl.location.contact'].sudo().search([
                                ('external_id', '=', ghl_contact.get('id'))
                            ], limit=1)

                            if not existing_contact and ghl_auto_create:
                                # Create new contact record
                                try:
                                    # Map GHL API fields to our model fields
                                    new_contact_data = {
                                        'external_id': ghl_contact.get('id'),
                                        'location_id': installed_location.id,
                                        'first_name': ghl_contact.get('firstName', ''),
                                        'last_name': ghl_contact.get('lastName', ''),
                                        'email': ghl_contact.get('email', ''),
                                        'assigned_to': ghl_contact.get('assignedTo'),
                                        'source': ghl_contact.get('source', ''),
                                        'tags': json.dumps(ghl_contact.get('tags', [])),
                                        'ai_status': 'ghl_fresh',
                                        'ai_summary': 'Contact fetched from GHL API'
                                    }

                                    # Handle date parsing for GHL API ISO format
                                    if ghl_contact.get('dateAdded'):
                                        try:
                                            from datetime import datetime
                                            # Parse ISO 8601 format from GHL API
                                            date_added = datetime.fromisoformat(
                                                ghl_contact.get('dateAdded').replace('Z', '+00:00'))
                                            new_contact_data['date_added'] = date_added
                                        except Exception as e:
                                            _logger.warning(
                                                f"Could not parse dateAdded '{ghl_contact.get('dateAdded')}': {str(e)}")
                                            # Don't set date_added if parsing fails

                                    # Add optional fields if they exist
                                    if ghl_contact.get('timezone'):
                                        new_contact_data['timezone'] = ghl_contact.get('timezone')
                                    if ghl_contact.get('country'):
                                        new_contact_data['country'] = ghl_contact.get('country')
                                    if ghl_contact.get('businessId'):
                                        new_contact_data['business_id'] = ghl_contact.get('businessId')
                                    if ghl_contact.get('businessName'):
                                        new_contact_data['business_id'] = ghl_contact.get('businessName')
                                    if ghl_contact.get('phone'):
                                        # Store phone in engagement_summary since we don't have a phone field
                                        if 'engagement_summary' not in new_contact_data:
                                            new_contact_data['engagement_summary'] = json.dumps({})
                                        current_engagement = json.loads(new_contact_data['engagement_summary']) if \
                                        new_contact_data['engagement_summary'] else {}
                                        current_engagement['phone'] = ghl_contact.get('phone')
                                        current_engagement['additional_phones'] = ghl_contact.get('additionalPhones',
                                                                                                  [])
                                        new_contact_data['engagement_summary'] = json.dumps(current_engagement)

                                    # Handle custom fields if they exist
                                    if ghl_contact.get('customFields'):
                                        # Store custom fields in engagement_summary
                                        if 'engagement_summary' not in new_contact_data:
                                            new_contact_data['engagement_summary'] = json.dumps({})
                                        current_engagement = json.loads(new_contact_data['engagement_summary']) if \
                                        new_contact_data['engagement_summary'] else {}
                                        current_engagement['custom_fields'] = ghl_contact.get('customFields')
                                        current_engagement['ghl_data'] = {
                                            'address': ghl_contact.get('address'),
                                            'city': ghl_contact.get('city'),
                                            'state': ghl_contact.get('state'),
                                            'postal_code': ghl_contact.get('postalCode'),
                                            'website': ghl_contact.get('website'),
                                            'type': ghl_contact.get('type'),
                                            'dnd': ghl_contact.get('dnd'),
                                            'valid_email': ghl_contact.get('validEmail'),
                                            'date_updated': ghl_contact.get('dateUpdated'),
                                            'date_of_birth': ghl_contact.get('dateOfBirth'),
                                            'opportunities': ghl_contact.get('opportunities', [])
                                        }
                                        new_contact_data['engagement_summary'] = json.dumps(current_engagement)

                                    new_contact = request.env['ghl.location.contact'].sudo().create(new_contact_data)
                                    _logger.info(
                                        f"Created new contact from GHL API: {new_contact.name} (ID: {new_contact.id})")

                                    # Add to contacts list for this search
                                    contacts = contacts | new_contact

                                except Exception as e:
                                    _logger.error(f"Error creating contact from GHL API: {str(e)}")
                                    continue
                            else:
                                # Contact exists, add to results if not already included
                                if existing_contact.id not in [c.id for c in contacts]:
                                    contacts = contacts | existing_contact

                    else:
                        _logger.warning(
                            f"GHL API search failed with status {ghl_response.status_code}: {ghl_response.text}")

                except Exception as e:
                    _logger.error(f"Error searching GHL API: {str(e)}")
                    # Continue with local results only
                    # Log the error but don't fail the entire search
                    ghl_contacts = []
                    use_ghl_api = False

            # Re-sort and limit contacts after potential GHL additions
            contacts = contacts.sorted('date_added', reverse=True)[:final_contact_limit]

            contact_data = []
            for contact in contacts:
                # Get basic counts
                tasks_count = request.env['ghl.contact.task'].sudo().search_count([
                    ('contact_id', '=', contact.id)
                ])
                conversations_count = request.env['ghl.contact.conversation'].sudo().search_count([
                    ('contact_id', '=', contact.id)
                ])

                # Parse JSON fields
                contact_tags = []
                if contact.tags:
                    try:
                        contact_tags = json.loads(contact.tags)
                        if not isinstance(contact_tags, list):
                            contact_tags = [contact_tags]
                    except:
                        contact_tags = []

                engagement_summary = []
                if contact.engagement_summary:
                    try:
                        engagement_summary = json.loads(contact.engagement_summary)
                    except:
                        engagement_summary = []

                last_message = []
                if contact.last_message:
                    try:
                        last_message = json.loads(contact.last_message)
                    except:
                        last_message = []

                assigned_user_name = contact.assigned_to or ''
                if contact.assigned_to:
                    assigned_user = request.env['ghl.location.user'].sudo().search([
                        ('external_id', '=', contact.assigned_to)
                    ], limit=1)
                    if assigned_user:
                        assigned_user_name = assigned_user.name or f"{assigned_user.first_name or ''} {assigned_user.last_name or ''}".strip()

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
                    'ai_summary': contact.ai_summary if contact.ai_summary else 'AI analysis pending',
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
                    'touch_summary': contact.touch_summary or 'no_touches',
                    'engagement_summary': engagement_summary,
                    'last_touch_date': contact.last_touch_date.isoformat() if contact.last_touch_date else '',
                    'last_message': contact.last_message or '',
                    'total_pipeline_value': contact.total_pipeline_value or 0.0,
                    'opportunities': contact.opportunities or 0,
                    'contact_tags': contact_tags,
                    'details_fetched': False,
                    'has_tasks': tasks_count > 0,
                    'has_conversations': conversations_count > 0,
                    'tasks_count': tasks_count,
                    'conversations_count': conversations_count,
                    'conversations_count_basic': conversations_count,
                    'loading_details': False,
                    'location_name': contact.location_id.name if contact.location_id else '',
                    'location_id': contact.location_id.location_id if contact.location_id else '',
                }

                contact_data.append(contact_info)

            # Calculate performance metrics
            total_time = time.time() - start_time

            # Prepare response message
            response_message = f'Found {len(contact_data)} contacts matching "{search_term}"'
            if ghl_contacts:
                response_message += f' (including {len(ghl_contacts)} fresh from GHL API)'
            elif use_ghl_api and ghl_search_enabled:
                response_message += ' (GHL API search attempted but no new contacts found)'

            return Response(
                json.dumps({
                    'success': True,
                    'contacts': contact_data,
                    'total_contacts': len(contact_data),
                    'search_term': search_term,
                    'ghl_api_used': use_ghl_api,
                    'ghl_api_enabled': ghl_search_enabled,
                    'ghl_contacts_found': len(ghl_contacts),
                    'local_contacts_found': len(contact_data) - len(ghl_contacts),
                    'performance': {
                        'total_time_ms': round(total_time * 1000, 2),
                        'contacts_per_second': round(len(contact_data) / total_time, 2) if total_time > 0 else 0
                    },
                    'config': {
                        'ghl_search_enabled': ghl_search_enabled,
                        'ghl_auto_create_contacts': ghl_auto_create,
                        'ghl_search_threshold': ghl_threshold,
                        'ghl_search_limit': ghl_search_limit,
                        'ghl_api_timeout': ghl_api_timeout,
                        'final_contact_limit': final_contact_limit,
                        'local_search_limit': local_search_limit,
                        'cross_location_limit': cross_location_limit
                    },
                    'message': response_message
                }),
                content_type='application/json',
                status=200,
                headers=get_cors_headers(request)
            )

        except Exception as e:
            import traceback
            tb = traceback.format_exc()
            _logger.error(f"Exception in search_location_contacts: {str(e)}\n{tb}")
            return Response(
                json.dumps({'success': False, 'error': str(e), 'traceback': tb}),
                content_type='application/json',
                status=500,
                headers=get_cors_headers(request)
            )

    @http.route('/api/contact-sync-status', type='http', auth='none', methods=['GET', 'OPTIONS'], csrf=False)
    def get_contact_sync_status(self, **kwargs):
        import json
        """
        Check sync status for specific contacts and return detailed data if ready
        """
        if request.httprequest.method == 'OPTIONS':
            return Response(status=200, headers=get_cors_headers(request))

        try:
            contact_ids = kwargs.get('contact_ids', '')
            if not contact_ids:
                return Response(
                    json.dumps({'success': False, 'error': 'contact_ids parameter is required'}),
                    content_type='application/json',
                    status=400,
                    headers=get_cors_headers(request)
                )

            # Parse contact IDs
            contact_id_list = [int(cid.strip()) for cid in contact_ids.split(',') if cid.strip().isdigit()]
            if not contact_id_list:
                return Response(
                    json.dumps({'success': False, 'error': 'No valid contact IDs provided'}),
                    content_type='application/json',
                    status=400,
                    headers=get_cors_headers(request)
                )

            contacts_data = []
            sync_status = {
                'all_ready': True,
                'ready_contacts': 0,
                'pending_contacts': 0,
                'total_contacts': len(contact_id_list)
            }

            for contact_id in contact_id_list:
                try:
                    contact = request.env['ghl.location.contact'].sudo().browse(contact_id)
                    if not contact.exists():
                        _logger.warning(f"Contact {contact_id} not found")
                        continue

                    # Check if contact has details fetched
                    details_fetched = contact.details_fetched

                    if details_fetched:
                        sync_status['ready_contacts'] += 1

                        # Get detailed data for ready contacts
                        # Get fresh tasks for this contact
                        tasks = request.env['ghl.contact.task'].sudo().search([
                            ('contact_id', '=', contact_id)
                        ])

                        tasks_data = []
                        for task in tasks:
                            tasks_data.append({
                                'id': task.id,
                                'external_id': task.external_id,
                                'title': task.title,
                                'body': task.body,
                                'due_date': task.due_date.isoformat() if task.due_date else '',
                                'completed': task.completed,
                                'assigned_to': task.assigned_to,
                                'create_date': task.create_date.isoformat() if task.create_date else '',
                                'write_date': task.write_date.isoformat() if task.write_date else '',
                            })

                        # Get fresh conversations for this contact
                        conversations = request.env['ghl.contact.conversation'].sudo().search([
                            ('contact_id', '=', contact_id)
                        ])

                        conversations_data = []
                        for conversation in conversations:
                            # Get messages for this conversation
                            conv_messages = request.env['ghl.contact.message'].sudo().search([
                                ('conversation_id', '=', conversation.id)
                            ], order='date_added desc')

                            # Calculate touch summary for this conversation
                            conv_message_counts = {}
                            for message in conv_messages:
                                message_type = message.message_type or 'UNKNOWN'
                                conv_message_counts[message_type] = conv_message_counts.get(message_type, 0) + 1

                            # Create touch summary string
                            conv_touch_parts = []
                            for msg_type, count in conv_message_counts.items():
                                # Map message types to readable names
                                type_name = contact._get_message_type_display_name(msg_type)
                                conv_touch_parts.append(f"{count} {type_name}")

                            conv_touch_summary = ', '.join(conv_touch_parts) if conv_touch_parts else 'no_touches'

                            # Get last message
                            conv_last_message = conv_messages[0] if conv_messages else None
                            conv_last_message_data = None
                            if conv_last_message:
                                import json
                                conv_last_message_data = {
                                    'body': conv_last_message.body,
                                    'type': conv_last_message.message_type,
                                    'direction': conv_last_message.direction,
                                    'source': conv_last_message.source or '',
                                    'date_added': conv_last_message.date_added.isoformat() if conv_last_message.date_added else '',
                                    'id': conv_last_message.ghl_id
                                }

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
                                'touch_summary': conv_touch_summary,
                                'last_touch_date': conv_last_message.date_added.isoformat() if conv_last_message and conv_last_message.date_added else '',
                                'last_message': conv_last_message_data,
                                'messages_count': len(conv_messages)
                            })

                        # Get fresh opportunities for this contact
                        opportunities = request.env['ghl.contact.opportunity'].sudo().search([
                            ('contact_id', '=', contact_id)
                        ])

                        opportunities_data = []
                        for opportunity in opportunities:
                            opportunities_data.append({
                                'id': opportunity.id,
                                'external_id': opportunity.external_id,
                                'name': opportunity.name,
                                'title': opportunity.title,
                                'description': opportunity.description,
                                'stage': opportunity.stage,
                                'expected_close_date': opportunity.expected_close_date.isoformat() if opportunity.expected_close_date else '',
                                'date_created': opportunity.date_created.isoformat() if opportunity.date_created else '',
                                'date_modified': opportunity.date_modified.isoformat() if opportunity.date_modified else '',
                                'monetary_value': opportunity.monetary_value,
                                'pipeline_id': opportunity.pipeline_id,
                                'pipeline_stage_id': opportunity.pipeline_stage_id,
                                'assigned_to': opportunity.assigned_to_external,
                                'status': opportunity.status,
                                'source': opportunity.source,
                                'contact_external_id': opportunity.contact_external_id,
                                'location_external_id': opportunity.location_external_id,
                                'index_version': opportunity.index_version,
                                'notes': opportunity.notes,
                                'tasks': opportunity.tasks,
                                'calendar_events': opportunity.calendar_events,
                                'followers': opportunity.followers,
                            })

                        # Get fresh computed touch information
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
                        last_message = messages.sorted('create_date', reverse=True)[0] if messages else None
                        last_touch_date = last_message.create_date if last_message else False

                        # Get last message content
                        last_message_data = None
                        if last_message and last_message.body:
                            import json
                            last_message_data = {
                                'body': last_message.body,
                                'type': last_message.message_type,
                                'direction': last_message.direction,
                                'source': last_message.source or '',
                                'date_added': last_message.create_date.isoformat() if last_message.create_date else '',
                                'id': last_message.ghl_id
                            }

                        contact_data = {
                            'contact_id': contact.id,
                            'external_id': contact.external_id,
                            'name': contact.name,
                            'email': contact.email,
                            'timezone': contact.timezone,
                            'country': contact.country,
                            'source': contact.source,
                            'date_added': contact.date_added.isoformat() if contact.date_added else '',
                            'business_id': contact.business_id,
                            'followers': contact.followers,
                            'tag_list': contact.tag_list,
                            'custom_fields_count': len(contact.custom_field_ids),
                            'attributions_count': len(contact.attribution_ids),
                            'ai_status': contact.ai_status,
                            'ai_summary': contact.ai_summary,
                            'ai_reasoning': contact.ai_reasoning,
                            'ai_quality_grade': contact.ai_quality_grade,
                            'ai_sales_grade': contact.ai_sales_grade,
                            'crm_tasks': contact.crm_tasks,
                            'category': contact.category,
                            'channel': contact.channel,
                            'created_by': contact.created_by,
                            'attribution': contact.attribution,
                            'assigned_to': contact.assigned_user_name,
                            'speed_to_lead': contact.speed_to_lead,
                            # FRESH COMPUTED TOUCH INFORMATION
                            'touch_summary': touch_summary,
                            'last_touch_date': last_touch_date.isoformat() if last_touch_date else '',
                            'last_message': last_message_data,
                            'total_pipeline_value': contact.total_pipeline_value,
                            'opportunities': contact.opportunities,
                            'details_fetched': True,
                            'has_tasks': len(tasks_data) > 0,
                            'has_conversations': len(conversations_data) > 0,
                            'tasks_count': len(tasks_data),
                            'conversations_count': len(conversations_data),
                            'tasks': tasks_data,
                            'conversations': conversations_data,
                            'opportunities': opportunities_data,
                            'loading_details': False,
                        }

                        contacts_data.append(contact_data)
                    else:
                        sync_status['pending_contacts'] += 1
                        sync_status['all_ready'] = False

                        # Return basic data for pending contacts
                        contact_data = {
                            'contact_id': contact.id,
                            'external_id': contact.external_id,
                            'name': contact.name,
                            'details_fetched': False,
                            'loading_details': True,
                        }
                        contacts_data.append(contact_data)

                except Exception as e:
                    _logger.error(f"Error processing contact {contact_id}: {str(e)}")
                    sync_status['pending_contacts'] += 1
                    sync_status['all_ready'] = False
                    continue

            return Response(
                json.dumps({
                    'success': True,
                    'contacts': contacts_data,
                    'sync_status': sync_status
                }),
                content_type='application/json',
                status=200,
                headers=get_cors_headers(request)
            )

        except Exception as e:
            import traceback
            tb = traceback.format_exc()
            _logger.error(f"Exception in get_contact_sync_status: {str(e)}\n{tb}")
            return Response(
                json.dumps({'success': False, 'error': str(e), 'traceback': tb}),
                content_type='application/json',
                status=500,
                headers=get_cors_headers(request)
            )

    @http.route('/api/contact-call-messages/<int:contact_id>', type='http', auth='none', methods=['GET', 'OPTIONS'],
                csrf=False)
    def get_contact_call_messages(self, contact_id, **kwargs):
        """
        Fetch call messages for a specific contact by their database ID.
        Returns messages where message_type is 'TYPE_CALL'.
        """
        _logger.info(f"get_contact_call_messages called for contact_id: {contact_id}")

        if request.httprequest.method == 'OPTIONS':
            return Response(status=200, headers=get_cors_headers(request))

        import json

        try:
            # Find the contact by ID
            contact = request.env['ghl.location.contact'].sudo().browse(contact_id)
            if not contact.exists():
                return Response(
                    json.dumps({'success': False, 'error': 'Contact not found'}),
                    content_type='application/json',
                    status=404,
                    headers=get_cors_headers(request)
                )

            # Fetch call messages for this contact
            call_messages = request.env['ghl.contact.message'].sudo().search([
                ('contact_id', '=', contact_id),
                ('message_type', '=', 'TYPE_CALL')
            ], order='date_added desc')

            # Format the messages for frontend
            messages_data = []
            for message in call_messages:
                # Debug logging for the first message
                if len(messages_data) == 0:
                    _logger.info(
                        f"Debug - First message data: id={message.id}, meta_id={message.meta_id}, meta_id.call_duration={message.meta_id.call_duration if message.meta_id else 'None'}")

                if not message.recording_data:
                    try:
                        message.fetch_recording_url()
                    except Exception as e:
                        _logger.error(f"Error fetching recording URL for message {message.id}: {str(e)}")
                        continue
                if message.recording_data and not message.transcript_ids:
                    try:
                        # Get app_id from kwargs or use the correct one for this location
                        app_id = kwargs.get('appId') or '6867d1537079188afca5013c'  # Use the correct app_id
                        request.env['ghl.contact.message.transcript'].sudo().fetch_transcript_for_message(
                            message_id=message.id, app_id=app_id)
                    except Exception as e:
                        _logger.error(f"Error fetching transcript URL for message {message.id}: {str(e)}")
                        continue

                # Calculate duration from transcript if meta_id.call_duration is not available
                calculated_duration = None
                if message.meta_id and message.meta_id.call_duration:
                    calculated_duration = message.meta_id.call_duration
                else:
                    # Try to calculate from transcript data
                    transcript_records = request.env['ghl.contact.message.transcript'].sudo().search([
                        ('message_id', '=', message.id)
                    ])
                    if transcript_records:
                        calculated_duration = sum(t.duration for t in transcript_records if t.duration)
                        # Debug logging for transcript-based duration calculation
                        if len(messages_data) == 0:
                            _logger.info(
                                f"Debug - Transcript-based duration: {calculated_duration} seconds from {len(transcript_records)} transcript records")
                    else:
                        # Debug logging when no transcript records found
                        if len(messages_data) == 0:
                            _logger.info(f"Debug - No transcript records found for message {message.id}")

                message_data = {
                    'id': message.id,
                    'ghl_id': message.ghl_id,
                    'message_type': message.message_type,
                    'body': message.body or '',
                    'direction': message.direction or '',
                    'status': message.status or '',
                    'content_type': message.content_type or '',
                    'source': message.source or '',
                    'user_id': message.user_id.name or '',
                    'conversation_provider_id': message.conversation_provider_id or '',
                    'date_added': message.date_added.isoformat() if message.date_added else None,
                    'conversation_id': message.conversation_id.ghl_id if message.conversation_id else None,
                    'location_id': message.location_id.location_id if message.location_id else None,
                    # Include meta data if available
                    'meta': {
                        'call_duration': calculated_duration,
                        'call_status': message.meta_id.call_status if message.meta_id and message.meta_id.call_status else None,
                    } if message.meta_id or calculated_duration else None,
                    # Include AI analysis data
                    'ai_call_grade': message.ai_call_grade or None,
                    'ai_call_summary_generated': message.ai_call_summary_generated or False,
                    'ai_call_summary_date': message.ai_call_summary_date.isoformat() if message.ai_call_summary_date else None,
                    # Include contact info
                    'contact': {
                        'id': contact.id,
                        'name': contact.name,
                        'external_id': contact.external_id,
                        'email': contact.email,
                        'phone': '',
                    },
                    # Include recording URL if available
                    'recording_url': f'/api/ghl-message/{message.id}/recording' if message.recording_fetched else None,
                    'recording_filename': message.recording_filename or None,
                    'recording_size': message.recording_size or None,
                    'recording_content_type': message.recording_content_type or None,
                }
                messages_data.append(message_data)

            _logger.info(f"Found {len(messages_data)} call messages for contact {contact_id}")

            return Response(
                json.dumps({
                    'success': True,
                    'contact': {
                        'id': contact.id,
                        'name': contact.name,
                        'external_id': contact.external_id,
                        'email': contact.email,
                        'phone': '',
                        'location_id': contact.location_id.location_id if contact.location_id else None,
                    },
                    'call_messages': messages_data,
                    'total_messages': len(messages_data),
                    'message': f'Successfully fetched {len(messages_data)} call messages'
                }),
                content_type='application/json',
                status=200,
                headers=get_cors_headers(request)
            )

        except Exception as e:
            import traceback
            tb = traceback.format_exc()
            _logger.error(f"Exception in get_contact_call_messages: {str(e)}\n{tb}")
            return Response(
                json.dumps({'success': False, 'error': str(e), 'traceback': tb}),
                content_type='application/json',
                status=500,
                headers=get_cors_headers(request)
            )

    @http.route('/api/call-details/<int:message_id>', type='http', auth='none', methods=['GET', 'OPTIONS'], csrf=False)
    def get_call_details(self, message_id, **kwargs):
        """
        Fetch detailed call information including transcript, duration, and metadata
        for a specific message ID.
        """
        _logger.info(f"get_call_details called for message_id: {message_id}")

        # Handle preflight OPTIONS request
        if request.httprequest.method == 'OPTIONS':
            return Response(status=200, headers=get_cors_headers(request))

        import json

        try:
            # Find the message by ID
            message = request.env['ghl.contact.message'].sudo().browse(message_id)
            if not message.exists():
                return Response(
                    json.dumps({'success': False, 'error': 'Message not found'}),
                    content_type='application/json',
                    status=404,
                    headers=get_cors_headers(request)
                )

            # Check if it's a call message
            if message.message_type != 'TYPE_CALL':
                return Response(
                    json.dumps({'success': False, 'error': 'Message is not a call message'}),
                    content_type='application/json',
                    status=400,
                    headers=get_cors_headers(request)
                )

            # Get contact information
            contact = message.contact_id
            if not contact.exists():
                return Response(
                    json.dumps({'success': False, 'error': 'Contact not found'}),
                    content_type='application/json',
                    status=404,
                    headers=get_cors_headers(request)
                )

            # Get transcript data
            transcript_records = request.env['ghl.contact.message.transcript'].sudo().search([
                ('message_id', '=', message_id)
            ], order='sentence_index asc')

            transcript_data = []
            total_duration = 0
            total_sentences = 0
            average_confidence = 0

            if transcript_records:
                total_duration = sum(t.duration for t in transcript_records if t.duration)
                total_sentences = len(transcript_records)
                confidence_sum = sum(t.confidence for t in transcript_records if t.confidence)
                average_confidence = round(confidence_sum / total_sentences, 2) if total_sentences > 0 else 0

                # Format transcript for frontend
                for transcript in transcript_records:
                    # Determine speaker based on media channel
                    speaker = "agent" if transcript.media_channel == "2" else "contact"
                    speaker_name = message.user_id.name if message.user_id and speaker == "agent" else contact.name

                    transcript_data.append({
                        'timestamp': f"{int(transcript.start_time_seconds // 60):02d}:{int(transcript.start_time_seconds % 60):02d}",
                        'speaker': speaker,
                        'speakerName': speaker_name,
                        'text': transcript.transcript,
                        'confidence': transcript.confidence,
                        'start_time': transcript.start_time_seconds,
                        'end_time': transcript.end_time_seconds,
                        'duration': transcript.duration,
                        'media_channel': transcript.media_channel
                    })

            # Format duration for display
            minutes = int(total_duration // 60)
            seconds = int(total_duration % 60)
            duration_formatted = f"{minutes}:{seconds:02d}"

            # Get call summary
            call_summary = {
                'outcome': message.body or 'No summary available',
                'keyPoints': [],
                'nextSteps': message.ai_next_steps.split('\n') if message.ai_next_steps else [],
                'sentiment': 'neutral'
            }

            # Get AI call summary if available
            ai_call_summary_html = message.ai_call_summary_html or ''
            ai_call_summary_generated = message.ai_call_summary_generated or False

            # Get AI analysis data from the message
            ai_analysis = {
                'overallScore': message.ai_overall_score or 7,
                'categories': {
                    'communication': message.ai_communication_score or 7,
                    'professionalism': message.ai_professionalism_score or 8,
                    'problemSolving': message.ai_problem_solving_score or 6,
                    'followUp': message.ai_followup_score or 7
                },
                'highlights': message.ai_highlights.split('\n') if message.ai_highlights else [],
                'improvements': message.ai_improvements.split('\n') if message.ai_improvements else [],
                'callIntent': message.ai_call_intent or 'Initial outreach',
                'satisfactionLevel': message.ai_satisfaction_level or 'medium'
            }

            # Add highlights based on transcript content
            if transcript_data:
                # Simple analysis based on transcript length and confidence
                if total_duration > 60:  # More than 1 minute
                    ai_analysis['highlights'].append('Engaging conversation')
                if average_confidence > 0.8:
                    ai_analysis['highlights'].append('Clear communication')
                if total_sentences > 10:
                    ai_analysis['highlights'].append('Detailed discussion')

                # Basic sentiment analysis
                positive_words = ['yes', 'great', 'good', 'interested', 'perfect', 'thanks', 'thank you']
                negative_words = ['no', 'not', 'bad', 'problem', 'issue', 'cancel']

                all_text = ' '.join([t['text'].lower() for t in transcript_data])
                positive_count = sum(1 for word in positive_words if word in all_text)
                negative_count = sum(1 for word in negative_words if word in all_text)

                if positive_count > negative_count:
                    ai_analysis['sentiment'] = 'positive'
                    ai_analysis['overallScore'] = 8
                elif negative_count > positive_count:
                    ai_analysis['sentiment'] = 'negative'
                    ai_analysis['overallScore'] = 5
                else:
                    ai_analysis['sentiment'] = 'neutral'
                    ai_analysis['overallScore'] = 7

            # Build the response data
            call_details = {
                'id': message.id,
                'ghl_id': message.ghl_id,
                'contactName': contact.name,
                'contactPhone': '',
                'callDate': message.date_added.strftime('%b %d, %Y') if message.date_added else 'Unknown',
                'callTime': message.date_added.strftime('%I:%M %p') if message.date_added else 'Unknown',
                'duration': duration_formatted,
                'duration_seconds': int(total_duration),
                'status': message.status or 'Unknown',
                'agent': message.user_id.name if message.user_id else 'Unknown',
                'direction': message.direction or 'unknown',
                'recordingUrl': f'/api/ghl-message/{message.id}/recording' if message.recording_fetched else '',
                'recording_fetched': message.recording_fetched,
                'transcript': transcript_data,
                'summary': call_summary,
                'aiAnalysis': ai_analysis,
                'aiCallSummary': {
                    'html': ai_call_summary_html,
                    'generated': ai_call_summary_generated,
                    'date': message.ai_call_summary_date.isoformat() if message.ai_call_summary_date else None
                },
                'callGrade': message.ai_call_grade or 'N/A',
                'meta': {
                    'call_duration': int(total_duration),
                    'call_status': message.meta_id.call_status if message.meta_id else None,
                    'total_sentences': total_sentences,
                    'average_confidence': average_confidence,
                    'has_transcript': len(transcript_data) > 0
                },
                'contact': {
                    'id': contact.id,
                    'name': contact.name,
                    'external_id': contact.external_id,
                    'email': contact.email,
                    'phone': '',
                    'location_id': contact.location_id.location_id if contact.location_id else None,
                }
            }

            _logger.info(f"Successfully fetched call details for message {message_id}")

            return Response(
                json.dumps({
                    'success': True,
                    'call_details': call_details,
                    'message': 'Successfully fetched call details'
                }),
                content_type='application/json',
                status=200,
                headers=get_cors_headers(request)
            )

        except Exception as e:
            import traceback
            tb = traceback.format_exc()
            _logger.error(f"Exception in get_call_details: {str(e)}\n{tb}")
            return Response(
                json.dumps({'success': False, 'error': str(e), 'traceback': tb}),
                content_type='application/json',
                status=500,
                headers=get_cors_headers(request)
            )

    @http.route('/api/run-ai-analysis/<int:contact_id>', type='http', auth='none', methods=['POST', 'OPTIONS'],
                csrf=False)
    def run_ai_analysis(self, contact_id, **kwargs):
        """Run AI analysis for a specific contact"""
        _logger.info(f"run_ai_analysis called for contact_id: {contact_id}")

        if request.httprequest.method == 'OPTIONS':
            return Response(status=200, headers=get_cors_headers(request))

        try:
            # Find the contact
            contact = request.env['ghl.location.contact'].sudo().browse(contact_id)
            if not contact.exists():
                _logger.error(f"Contact {contact_id} not found")
                return Response(
                    json.dumps({'success': False, 'error': 'Contact not found'}),
                    content_type='application/json',
                    status=404,
                    headers=get_cors_headers(request)
                )

            _logger.info(f"Running AI analysis for contact {contact_id} (name: {contact.name})")

            # Run AI analysis
            result = contact.run_ai_analysis()

            _logger.info(f"AI analysis result for contact {contact_id}: {result}")

            # Log the updated contact fields
            _logger.info(
                f"Contact {contact_id} AI fields after analysis: status='{contact.ai_status}', summary='{contact.ai_summary}', quality='{contact.ai_quality_grade}', sales='{contact.ai_sales_grade}'")

            # Force a database commit to ensure the data is saved
            request.env.cr.commit()
            _logger.info(f"Contact {contact_id} AI data committed to database")

            # Verify the data was actually saved by re-reading from database
            _logger.info(
                f"Contact {contact_id} AI fields after commit verification: status='{contact.ai_status}', summary='{contact.ai_summary}', quality='{contact.ai_quality_grade}', sales='{contact.ai_sales_grade}'")

            # Additional verification: Query the database directly
            contact_from_db = request.env['ghl.location.contact'].sudo().browse(contact_id)
            _logger.info(
                f"Contact {contact_id} AI fields from direct DB query: status='{contact_from_db.ai_status}', summary='{contact_from_db.ai_summary}', quality='{contact_from_db.ai_quality_grade}', sales='{contact_from_db.ai_sales_grade}'")

            if result.get('success'):
                return Response(
                    json.dumps({
                        'success': True,
                        'message': result.get('message', 'AI analysis completed successfully'),
                        'ai_status': contact.ai_status,
                        'ai_summary': contact.ai_summary,
                        'ai_quality_grade': contact.ai_quality_grade,
                        'ai_sales_grade': contact.ai_sales_grade
                    }),
                    content_type='application/json',
                    status=200,
                    headers=get_cors_headers(request)
                )
            else:
                return Response(
                    json.dumps({
                        'success': False,
                        'error': result.get('error', 'AI analysis failed')
                    }),
                    content_type='application/json',
                    status=500,
                    headers=get_cors_headers(request)
                )

        except Exception as e:
            _logger.error(f"Error in run_ai_analysis for contact {contact_id}: {str(e)}")
            return Response(
                json.dumps({'success': False, 'error': str(e)}),
                content_type='application/json',
                status=500,
                headers=get_cors_headers(request)
            )

    @http.route('/api/generate-call-summary/<int:message_id>', type='http', auth='none', methods=['POST', 'OPTIONS'],
                csrf=False)
    def generate_call_summary(self, message_id, **kwargs):
        """Generate AI call summary for a specific message"""
        _logger.info(f"generate_call_summary called for message_id: {message_id}")

        if request.httprequest.method == 'OPTIONS':
            return Response(status=200, headers=get_cors_headers(request))

        try:
            # Find the message
            message = request.env['ghl.contact.message'].sudo().browse(message_id)
            if not message.exists():
                _logger.error(f"Message {message_id} not found")
                return Response(
                    json.dumps({'success': False, 'error': 'Message not found'}),
                    content_type='application/json',
                    status=404,
                    headers=get_cors_headers(request)
                )

            if message.message_type != 'TYPE_CALL':
                return Response(
                    json.dumps({'success': False, 'error': 'Message is not a call message'}),
                    content_type='application/json',
                    status=400,
                    headers=get_cors_headers(request)
                )

            # Get API key from the message's location
            api_key = message.location_id.openai_api_key
            if not api_key:
                _logger.error(f"OpenAI API key not configured for location {message.location_id.id}")
                return Response(
                    json.dumps({'success': False,
                                'error': 'OpenAI API key not configured for this location. Please configure it in the location settings.'}),
                    content_type='application/json',
                    status=500,
                    headers=get_cors_headers(request)
                )

            _logger.info(f"Generating AI call summary for message {message_id}")

            # Generate AI call summary
            message.action_generate_ai_call_summary(api_key=api_key)

            _logger.info(f"Successfully generated AI call summary for message {message_id}")

            return Response(
                json.dumps({
                    'success': True,
                    'message': 'AI call summary generated successfully',
                    'ai_summary_generated': message.ai_call_summary_generated,
                    'ai_summary_date': message.ai_call_summary_date.isoformat() if message.ai_call_summary_date else None
                }),
                content_type='application/json',
                status=200,
                headers=get_cors_headers(request)
            )

        except Exception as e:
            _logger.error(f"Error in generate_call_summary for message {message_id}: {str(e)}")
            return Response(
                json.dumps({'success': False, 'error': str(e)}),
                content_type='application/json',
                status=500,
                headers=get_cors_headers(request)
            )

    @http.route('/api/location-openai-key/<string:location_id>', type='http', auth='none',
                methods=['GET', 'PUT', 'OPTIONS'], csrf=False)
    def manage_location_openai_key(self, location_id, **kwargs):
        """
        Get or update OpenAI API key for a specific location
        """
        _logger.info(f"Manage OpenAI API key called for location_id: {location_id}")

        # Handle preflight OPTIONS request
        if request.httprequest.method == 'OPTIONS':
            return Response(
                status=200,
                headers=get_cors_headers(request)
            )

        try:
            # Find the installed location
            installed_location = request.env['installed.location'].sudo().search([
                ('location_id', '=', location_id)
            ], limit=1)

            if not installed_location:
                return Response(
                    json.dumps({'error': 'Location not found'}),
                    content_type='application/json',
                    status=404,
                    headers=get_cors_headers(request)
                )

            if request.httprequest.method == 'GET':
                # Return the API key (masked for security)
                api_key = installed_location.openai_api_key
                masked_key = None
                if api_key:
                    # Show only first 7 characters and last 4 characters
                    if len(api_key) > 11:
                        masked_key = f"{api_key[:7]}...{api_key[-4:]}"
                    else:
                        masked_key = "***"  # For very short keys

                return Response(
                    json.dumps({
                        'location_id': location_id,
                        'location_name': installed_location.name,
                        'has_api_key': bool(api_key),
                        'masked_api_key': masked_key
                    }),
                    content_type='application/json',
                    headers=get_cors_headers(request)
                )

            elif request.httprequest.method == 'PUT':
                # Update the API key
                data = request.httprequest.get_json()
                if not data:
                    return Response(
                        json.dumps({'error': 'No data provided'}),
                        content_type='application/json',
                        status=400,
                        headers=get_cors_headers(request)
                    )

                new_api_key = data.get('openai_api_key')
                if new_api_key is None:
                    return Response(
                        json.dumps({'error': 'openai_api_key field is required'}),
                        content_type='application/json',
                        status=400,
                        headers=get_cors_headers(request)
                    )

                # Update the API key
                installed_location.write({'openai_api_key': new_api_key})

                _logger.info(f"Updated OpenAI API key for location {location_id}")

                return Response(
                    json.dumps({
                        'success': True,
                        'message': 'OpenAI API key updated successfully',
                        'location_id': location_id,
                        'location_name': installed_location.name
                    }),
                    content_type='application/json',
                    headers=get_cors_headers(request)
                )

        except Exception as e:
            _logger.error(f"Error in manage_location_openai_key: {str(e)}")
            return Response(
                json.dumps({'error': str(e)}),
                content_type='application/json',
                status=500,
                headers=get_cors_headers(request)
            )

    @http.route('/api/location-calls/<string:location_id>', type='http', auth='none', methods=['GET', 'OPTIONS'],
                csrf=False)
    def get_location_calls(self, location_id, **kwargs):
        """
        Get all call messages for a specific location with pagination and filtering
        """
        _logger.info(f"get_location_calls called for location_id: {location_id}")

        # Handle preflight OPTIONS request
        if request.httprequest.method == 'OPTIONS':
            return Response(
                status=200,
                headers=get_cors_headers(request)
            )

        try:
            # Get app_id from parameters
            app_id = self._get_app_id_from_request(kwargs)

            # Get pagination parameters
            page = int(kwargs.get('page', 1))
            limit = int(kwargs.get('limit', 10))
            offset = (page - 1) * limit

            # Get optional filters
            selected_user = kwargs.get('selected_user', '')
            search_term = kwargs.get('search', '')

            # Find the installed location
            installed_location = request.env['installed.location'].sudo().search([
                ('location_id', '=', location_id)
            ], limit=1)

            if not installed_location:
                return Response(
                    json.dumps({'success': False, 'error': 'Location not found'}),
                    content_type='application/json',
                    status=404,
                    headers=get_cors_headers(request)
                )

            # Build domain for call messages - directly search by location_id
            # This is simpler and more direct than the previous approach
            domain = [
                ('location_id.location_id', '=', location_id),
                ('message_type', '=', 'TYPE_CALL')
            ]
            _logger.info(f"Built domain for location {location_id}: {domain}")

            # Add user filter if specified
            if selected_user and selected_user.strip():
                # Search for contacts assigned to this user
                user_contacts = request.env['ghl.location.contact'].sudo().search([
                    ('location_id', '=', location_id),
                    ('assigned_to', '=', selected_user)
                ])
                if user_contacts:
                    user_contact_ids = [c.id for c in user_contacts]
                    # Filter to only show calls for contacts assigned to this user
                    domain = [
                        ('contact_id', 'in', user_contact_ids),
                        ('message_type', '=', 'TYPE_CALL')
                    ]
                    _logger.info(f"Applied user filter: {domain}")

            # Add search filter if specified
            if search_term and search_term.strip():
                # Search in contact names and phone numbers
                search_contacts = request.env['ghl.location.contact'].sudo().search([
                    ('location_id', '=', location_id),
                    ('|'),
                    ('first_name', 'ilike', search_term),
                    ('last_name', 'ilike', search_term),
                    ('phone', 'ilike', search_term)
                ])
                if search_contacts:
                    search_contact_ids = [c.id for c in search_contacts]
                    # Filter to only show calls for contacts matching search
                    domain = [
                        ('contact_id', 'in', search_contact_ids),
                        ('message_type', '=', 'TYPE_CALL')
                    ]
                    _logger.info(f"Applied search filter: {domain}")

            # Get total count
            total_calls = request.env['ghl.contact.message'].sudo().search_count(domain)
            _logger.info(f"Total calls found for domain {domain}: {total_calls}")
            _logger.info(f"Domain breakdown: location_id.location_id='{location_id}', message_type='TYPE_CALL'")

            # Debug: Let's also check the raw count without any filters
            raw_total = request.env['ghl.contact.message'].sudo().search_count([
                ('message_type', '=', 'TYPE_CALL')
            ])
            _logger.info(f"Raw total calls in system (no location filter): {raw_total}")

            # Debug: Check location-specific count
            location_total = request.env['ghl.contact.message'].sudo().search_count([
                ('location_id.location_id', '=', location_id)
            ])
            _logger.info(f"Total messages for location {location_id}: {location_total}")

            # Get paginated results
            call_messages = request.env['ghl.contact.message'].sudo().search(
                domain,
                order='date_added desc',
                limit=limit,
                offset=offset
            )
            _logger.info(f"Retrieved {len(call_messages)} call messages for pagination")

            # Debug: Let's also check what the first few messages look like
            if call_messages:
                first_message = call_messages[0]
                _logger.info(
                    f"First message debug: id={first_message.id}, contact_id={first_message.contact_id.id if first_message.contact_id else 'None'}, location_id={first_message.location_id.location_id if first_message.location_id else 'None'}")

            # Additional debugging: Let's check what call messages exist in the system
            all_call_messages = request.env['ghl.contact.message'].sudo().search([
                ('message_type', '=', 'TYPE_CALL')
            ], limit=5)
            _logger.info(
                f"Sample of all call messages in system: {[(m.id, m.contact_id.name if m.contact_id else 'None', m.location_id.location_id if m.location_id else 'None') for m in all_call_messages]}")

            # Prepare response data - use the same structure as the working endpoint
            calls_data = []
            for message in call_messages:
                # Get contact information
                contact = request.env['ghl.location.contact'].sudo().browse(
                    message.contact_id.id) if message.contact_id else None

                if contact:
                    # Calculate duration from transcript if meta_id.call_duration is not available
                    calculated_duration = None
                    if message.meta_id and message.meta_id.call_duration:
                        calculated_duration = message.meta_id.call_duration
                    else:
                        # Try to calculate from transcript data
                        transcript_records = request.env['ghl.contact.message.transcript'].sudo().search([
                            ('message_id', '=', message.id)
                        ])
                        if transcript_records:
                            calculated_duration = sum(t.duration for t in transcript_records if t.duration)

                    # Use the same data structure as the working endpoint
                    call_data = {
                        'id': message.id,
                        'ghl_id': message.ghl_id,
                        'message_type': message.message_type,
                        'body': message.body or '',
                        'direction': message.direction or '',
                        'status': message.status or '',
                        'content_type': message.content_type or '',
                        'source': message.source or '',
                        'user_id': message.user_id.name if message.user_id else '',
                        'conversation_provider_id': message.conversation_provider_id or '',
                        'date_added': message.date_added.isoformat() if message.date_added else None,
                        'conversation_id': message.conversation_id.ghl_id if message.conversation_id else None,
                        'location_id': message.location_id.location_id if message.location_id else None,
                        # Include meta data if available
                        'meta': {
                            'call_duration': calculated_duration,
                            'call_status': message.meta_id.call_status if message.meta_id and message.meta_id.call_status else None,
                        } if message.meta_id or calculated_duration else None,
                        # Include AI analysis data
                        'ai_call_grade': message.ai_call_grade or None,
                        'ai_call_summary_generated': message.ai_call_summary_generated or False,
                        'ai_call_summary_date': message.ai_call_summary_date.isoformat() if message.ai_call_summary_date else None,
                        # Include contact info
                        'contact': {
                            'id': contact.id,
                            'name': contact.name,
                            'external_id': contact.external_id,
                            'email': contact.email,
                            'phone': '',
                        },
                        # Include recording URL if available
                        'recording_url': f'/api/ghl-message/{message.id}/recording' if message.recording_fetched else None,
                        'recording_filename': message.recording_filename or None,
                        'recording_size': message.recording_size or None,
                        'recording_content_type': message.recording_content_type or None,
                        # Include transcript data if available
                        'transcript_fetched': message.transcript_fetched or False,
                        'transcript_ids': [
                            {
                                'id': t.id,
                                'sentence_index': t.sentence_index,
                                'start_time_seconds': t.start_time_seconds,
                                'end_time_seconds': t.end_time_seconds,
                                'transcript': t.transcript,
                                'confidence': t.confidence,
                                'duration': t.duration
                            } for t in message.transcript_ids.sorted('sentence_index')
                        ] if message.transcript_ids else [],
                    }
                    calls_data.append(call_data)

            _logger.info(f"Found {len(calls_data)} call messages for location {location_id}")
            _logger.info(f"Total calls count: {total_calls}, Page: {page}, Limit: {limit}")
            _logger.info(f"Response data: success={True}, calls_count={len(calls_data)}, total_calls={total_calls}")

            return Response(
                json.dumps({
                    'success': True,
                    'calls': calls_data,
                    'total_calls': total_calls,
                    'page': page,
                    'limit': limit,
                    'total_pages': (total_calls + limit - 1) // limit,
                    'message': f'Successfully fetched {len(calls_data)} call messages'
                }),
                content_type='application/json',
                headers=get_cors_headers(request)
            )

        except Exception as e:
            import traceback
            tb = traceback.format_exc()
            _logger.error(f"Exception in get_location_calls: {str(e)}\n{tb}")
            return Response(
                json.dumps({
                    'success': False,
                    'error': str(e),
                    'message': 'Failed to fetch call messages'
                }),
                content_type='application/json',
                status=500,
                headers=get_cors_headers(request)
            )

    @http.route('/api/fetch-transcript/<int:message_id>', type='http', auth='none', methods=['POST', 'OPTIONS'],
                csrf=False)
    def fetch_transcript_for_message(self, message_id, **kwargs):
        """
        Fetch transcript for a specific call message
        """
        _logger.info(f"fetch_transcript_for_message called for message_id: {message_id}")

        # Handle preflight OPTIONS request
        if request.httprequest.method == 'OPTIONS':
            return Response(
                status=200,
                headers=get_cors_headers(request)
            )

        try:
            # Get app_id from parameters
            app_id = self._get_app_id_from_request(kwargs)

            # Find the message
            message = request.env['ghl.contact.message'].sudo().browse(message_id)
            if not message.exists():
                return Response(
                    json.dumps({'success': False, 'error': 'Message not found'}),
                    content_type='application/json',
                    status=404,
                    headers=get_cors_headers(request)
                )

            if message.message_type != 'TYPE_CALL':
                return Response(
                    json.dumps({'success': False, 'error': 'Message is not a call message'}),
                    content_type='application/json',
                    status=400,
                    headers=get_cors_headers(request)
                )

            # Fetch transcript using the existing method
            transcript_result = request.env['ghl.contact.message.transcript'].sudo().fetch_transcript_for_message(
                message_id=message_id,
                app_id=app_id
            )

            if transcript_result.get('success'):
                # Get the updated transcript data
                transcript_records = request.env['ghl.contact.message.transcript'].sudo().search([
                    ('message_id', '=', message_id)
                ], order='sentence_index asc')

                transcript_data = []
                for record in transcript_records:
                    transcript_data.append({
                        'timestamp': f"{record.start_time_seconds:.1f}s",
                        'speaker': 'agent',  # Default to agent, could be enhanced later
                        'speakerName': 'Agent',
                        'text': record.transcript,
                        'confidence': record.confidence,
                        'duration': record.duration
                    })

                return Response(
                    json.dumps({
                        'success': True,
                        'transcript': transcript_data,
                        'message': transcript_result.get('message', 'Transcript fetched successfully'),
                        'call_duration_seconds': transcript_result.get('call_duration_seconds', 0),
                        'call_duration_formatted': transcript_result.get('call_duration_formatted', '0:00'),
                        'total_sentences': transcript_result.get('total_sentences', 0),
                        'average_confidence': transcript_result.get('average_confidence', 0)
                    }),
                    content_type='application/json',
                    headers=get_cors_headers(request)
                )
            else:
                return Response(
                    json.dumps({
                        'success': False,
                        'error': transcript_result.get('error', 'Failed to fetch transcript')
                    }),
                    content_type='application/json',
                    status=500,
                    headers=get_cors_headers(request)
                )

        except Exception as e:
            import traceback
            tb = traceback.format_exc()
            _logger.error(f"Exception in fetch_transcript_for_message: {str(e)}\n{tb}")
            return Response(
                json.dumps({
                    'success': False,
                    'error': str(e),
                    'message': 'Failed to fetch transcript'
                }),
                content_type='application/json',
                status=500,
                headers=get_cors_headers(request)
            )

    @http.route('/api/fetch-recording/<int:message_id>', type='http', auth='none', methods=['POST', 'OPTIONS'],
                csrf=False)
    def fetch_recording_for_message(self, message_id, **kwargs):
        """
        Fetch recording for a specific call message
        """
        _logger.info(f"fetch_recording_for_message called for message_id: {message_id}")

        # Handle preflight OPTIONS request
        if request.httprequest.method == 'OPTIONS':
            return Response(
                status=200,
                headers=get_cors_headers(request)
            )

        try:
            # Get app_id from parameters
            app_id = self._get_app_id_from_request(kwargs)

            # Find the message
            message = request.env['ghl.contact.message'].sudo().browse(message_id)
            if not message.exists():
                return Response(
                    json.dumps({'success': False, 'error': 'Message not found'}),
                    content_type='application/json',
                    status=404,
                    headers=get_cors_headers(request)
                )

            if message.message_type != 'TYPE_CALL':
                return Response(
                    json.dumps({'success': False, 'error': 'Message is not a call message'}),
                    content_type='application/json',
                    status=400,
                    headers=get_cors_headers(request)
                )

            # Check if recording is already fetched
            if message.recording_fetched and (message.recording_data or message.recording_filename):
                return Response(
                    json.dumps({
                        'success': True,
                        'message': 'Recording already fetched',
                        'recording_fetched': True,
                        'recording_url': f'/api/ghl-message/{message.id}/recording'
                    }),
                    content_type='application/json',
                    headers=get_cors_headers(request)
                )

            # Fetch recording using the existing method
            # Pass the app_id to the method
            recording_result = message.fetch_recording_url(app_id=app_id)

            if recording_result.get('success'):
                # Re-read the message to get updated recording data
                message = request.env['ghl.contact.message'].sudo().browse(message_id)

                return Response(
                    json.dumps({
                        'success': True,
                        'message': 'Recording fetched successfully',
                        'recording_fetched': message.recording_fetched,
                        'recording_url': f'/api/ghl-message/{message.id}/recording',
                        'recording_filename': message.recording_filename,
                        'recording_size': message.recording_size,
                        'recording_content_type': message.recording_content_type
                    }),
                    content_type='application/json',
                    headers=get_cors_headers(request)
                )
            else:
                return Response(
                    json.dumps({
                        'success': False,
                        'error': recording_result.get('error', 'Failed to fetch recording')
                    }),
                    content_type='application/json',
                    status=500,
                    headers=get_cors_headers(request)
                )

        except Exception as e:
            import traceback
            tb = traceback.format_exc()
            _logger.error(f"Exception in fetch_recording_for_message: {str(e)}\n{tb}")
            return Response(
                json.dumps({
                    'success': False,
                    'error': str(e),
                    'message': 'Failed to fetch recording'
                }),
                content_type='application/json',
                status=500,
                headers=get_cors_headers(request)
            )

    @http.route('/api/get-transcript/<int:message_id>', type='http', auth='none', methods=['GET', 'OPTIONS'],
                csrf=False)
    def get_transcript_for_message(self, message_id, **kwargs):
        """
        Get existing transcript for a specific call message
        """
        _logger.info(f"get_transcript_for_message called for message_id: {message_id}")

        # Handle preflight OPTIONS request
        if request.httprequest.method == 'OPTIONS':
            return Response(
                status=200,
                headers=get_cors_headers(request)
            )

        try:
            # Find the message
            message = request.env['ghl.contact.message'].sudo().browse(message_id)
            if not message.exists():
                return Response(
                    json.dumps({'success': False, 'error': 'Message not found'}),
                    content_type='application/json',
                    status=404,
                    headers=get_cors_headers(request)
                )

            if message.message_type != 'TYPE_CALL':
                return Response(
                    json.dumps({'success': False, 'error': 'Message is not a call message'}),
                    content_type='application/json',
                    status=400,
                    headers=get_cors_headers(request)
                )

            # Check if transcript exists and is fetched
            if not message.transcript_fetched or not message.transcript_ids:
                return Response(
                    json.dumps({
                        'success': False,
                        'error': 'No transcript available',
                        'transcript_fetched': message.transcript_fetched,
                        'transcript_count': len(message.transcript_ids)
                    }),
                    content_type='application/json',
                    status=404,
                    headers=get_cors_headers(request)
                )

            # Get existing transcript data
            transcript_records = message.transcript_ids.sorted('sentence_index')

            transcript_data = []
            for record in transcript_records:
                transcript_data.append({
                    'timestamp': f"{record.start_time_seconds:.1f}s",
                    'speaker': 'agent',  # Default to agent, could be enhanced later
                    'speakerName': 'Agent',
                    'text': record.transcript,
                    'confidence': record.confidence,
                    'duration': record.duration
                })

            return Response(
                json.dumps({
                    'success': True,
                    'transcript': transcript_data,
                    'message': f'Retrieved {len(transcript_data)} existing transcript segments',
                    'transcript_fetched': message.transcript_fetched,
                    'transcript_count': len(transcript_data)
                }),
                content_type='application/json',
                headers=get_cors_headers(request)
            )

        except Exception as e:
            import traceback
            tb = traceback.format_exc()
            _logger.error(f"Exception in get_transcript_for_message: {str(e)}\n{tb}")
            return Response(
                json.dumps({
                    'success': False,
                    'error': str(e),
                    'message': 'Failed to get transcript'
                }),
                content_type='application/json',
                status=500,
                headers=get_cors_headers(request)
            )

    @http.route('/api/location-openai-key/<string:location_id>/validate', type='http', auth='none',
                methods=['POST', 'OPTIONS'], csrf=False)
    def validate_location_openai_key(self, location_id, **kwargs):
        """
        Validate OpenAI API key for a specific location
        """
        _logger.info(f"Validate OpenAI API key called for location_id: {location_id}")

        # Handle preflight OPTIONS request
        if request.httprequest.method == 'OPTIONS':
            return Response(
                status=200,
                headers=get_cors_headers(request)
            )

        try:
            # Find the installed location
            installed_location = request.env['installed.location'].sudo().search([
                ('location_id', '=', location_id)
            ], limit=1)

            if not installed_location:
                return Response(
                    json.dumps({'error': 'Location not found'}),
                    content_type='application/json',
                    status=404,
                    headers=get_cors_headers(request)
                )

            data = request.httprequest.get_json()
            if not data:
                return Response(
                    json.dumps({'error': 'No data provided'}),
                    content_type='application/json',
                    status=400,
                    headers=get_cors_headers(request)
                )

            api_key = data.get('openai_api_key')
            if not api_key:
                return Response(
                    json.dumps({'error': 'openai_api_key field is required'}),
                    content_type='application/json',
                    status=400,
                    headers=get_cors_headers(request)
                )

            # Get the AI service model for usage logging
            ai_service = request.env['cyclsales.vision.ai'].sudo().search([('is_active', '=', True)], limit=1)
            if not ai_service:
                # Create a default AI service if none exists
                ai_service = request.env['cyclsales.vision.ai'].sudo().create({
                    'name': 'Default OpenAI GPT-4 Service',
                    'model_type': 'gpt-4o',
                    'base_url': 'https://api.openai.com/v1',
                    'max_tokens': 500,
                    'temperature': 0.3,
                    'is_active': True
                })

            # Create usage log entry for validation
            usage_log = request.env['cyclsales.vision.ai.usage.log'].sudo().create_usage_log(
                location_id=location_id,
                ai_service_id=ai_service.id,
                request_type='test_connection',
                message_id='api_key_validation',
                contact_id='validation',
                conversation_id='validation'
            )

            if usage_log:
                usage_log.write({'status': 'processing'})

            # Validate the API key by making a simple test request to OpenAI
            try:
                import requests

                # Test the API key with a simple request
                headers = {
                    'Authorization': f'Bearer {api_key}',
                    'Content-Type': 'application/json'
                }

                # Use a simple model list request to validate the key
                response = requests.get(
                    'https://api.openai.com/v1/models',
                    headers=headers,
                    timeout=10
                )

                if response.status_code == 200:
                    # Update usage log with success
                    if usage_log:
                        usage_log.write({
                            'input_tokens': 0,
                            'output_tokens': 0,
                            'response_length': 0
                        })
                        usage_log.update_success({'validation': 'success'})

                    # Update AI service usage statistics
                    ai_service._record_success()

                    return Response(
                        json.dumps({
                            'success': True,
                            'message': 'OpenAI API key is valid',
                            'location_id': location_id
                        }),
                        content_type='application/json',
                        headers=get_cors_headers(request)
                    )
                else:
                    # Update usage log with failure
                    if usage_log:
                        usage_log.update_failure(f"Invalid API key. Status: {response.status_code}",
                                                 f"HTTP_{response.status_code}")

                    # Update AI service error statistics
                    ai_service._record_error(f"Invalid API key. Status: {response.status_code}")

                    return Response(
                        json.dumps({
                            'success': False,
                            'error': f'Invalid API key. Status: {response.status_code}',
                            'location_id': location_id
                        }),
                        content_type='application/json',
                        status=400,
                        headers=get_cors_headers(request)
                    )

            except requests.exceptions.RequestException as e:
                # Update usage log with failure
                if usage_log:
                    usage_log.update_failure(f"Network error: {str(e)}", "NETWORK_ERROR")

                # Update AI service error statistics
                ai_service._record_error(f"Network error: {str(e)}")

                return Response(
                    json.dumps({
                        'success': False,
                        'error': f'Network error: {str(e)}',
                        'location_id': location_id
                    }),
                    content_type='application/json',
                    status=500,
                    headers=get_cors_headers(request)
                )

        except Exception as e:
            _logger.error(f"Error in validate_location_openai_key: {str(e)}")
            return Response(
                json.dumps({'error': str(e)}),
                content_type='application/json',
                status=500,
                headers=get_cors_headers(request)
            )

    @http.route('/api/update-all-contacts-ai-status', type='http', auth='none', methods=['POST', 'OPTIONS'], csrf=False)
    def update_all_contacts_ai_status(self, **kwargs):
        """Update AI status for all contacts based on their activity"""
        _logger.info("update_all_contacts_ai_status called")

        if request.httprequest.method == 'OPTIONS':
            return Response(status=200, headers=get_cors_headers(request))

        try:
            # Update AI status for all contacts
            result = request.env['ghl.location.contact'].sudo().update_all_contacts_ai_status()

            _logger.info(f"AI status update completed: {result}")

            return Response(
                json.dumps(result),
                content_type='application/json',
                status=200,
                headers=get_cors_headers(request)
            )

        except Exception as e:
            _logger.error(f"Error updating AI status for all contacts: {str(e)}")
            return Response(
                json.dumps({'success': False, 'error': str(e)}),
                content_type='application/json',
                status=500,
                headers=get_cors_headers(request)
            )

    @http.route('/api/run-ai-sales-grade-analysis/<int:contact_id>', type='http', auth='none',
                methods=['POST', 'OPTIONS'], csrf=False)
    def run_ai_sales_grade_analysis(self, contact_id, **kwargs):
        """Run AI sales grade analysis for a specific contact"""
        _logger.info(f"run_ai_sales_grade_analysis called for contact_id: {contact_id}")

        if request.httprequest.method == 'OPTIONS':
            return Response(status=200, headers=get_cors_headers(request))

        try:
            # Find the contact
            contact = request.env['ghl.location.contact'].sudo().browse(contact_id)
            if not contact.exists():
                _logger.error(f"Contact {contact_id} not found")
                return Response(
                    json.dumps({'success': False, 'error': 'Contact not found'}),
                    content_type='application/json',
                    status=404,
                    headers=get_cors_headers(request)
                )

            _logger.info(f"Running AI sales grade analysis for contact {contact_id} (name: {contact.name})")

            # Run AI sales grade analysis
            result = contact.run_ai_sales_grade_analysis()

            _logger.info(f"AI sales grade analysis result for contact {contact_id}: {result}")

            # Log the updated contact fields
            _logger.info(
                f"Contact {contact_id} AI sales grade fields after analysis: sales_grade='{contact.ai_sales_grade}', sales_reasoning='{contact.ai_sales_reasoning}'")

            # Force a database commit to ensure the data is saved
            request.env.cr.commit()
            _logger.info(f"Contact {contact_id} AI sales grade data committed to database")

            # Verify the data was actually saved by re-reading from database
            _logger.info(
                f"Contact {contact_id} AI sales grade fields after commit verification: sales_grade='{contact.ai_sales_grade}', sales_reasoning='{contact.ai_sales_reasoning}'")

            # Additional verification: Query the database directly
            contact_from_db = request.env['ghl.location.contact'].sudo().browse(contact_id)
            _logger.info(
                f"Contact {contact_id} AI sales grade fields from direct DB query: sales_grade='{contact_from_db.ai_sales_grade}', sales_reasoning='{contact_from_db.ai_sales_reasoning}'")

            if result.get('success'):
                return Response(
                    json.dumps({
                        'success': True,
                        'message': result.get('message', 'AI sales grade analysis completed successfully'),
                        'ai_sales_grade': contact.ai_sales_grade,
                        'ai_sales_reasoning': contact.ai_sales_reasoning
                    }),
                    content_type='application/json',
                    status=200,
                    headers=get_cors_headers(request)
                )
            else:
                return Response(
                    json.dumps({
                        'success': False,
                        'error': result.get('error', 'AI sales grade analysis failed')
                    }),
                    content_type='application/json',
                    status=500,
                    headers=get_cors_headers(request)
                )

        except Exception as e:
            _logger.error(f"Error in run_ai_sales_grade_analysis for contact {contact_id}: {str(e)}")
            return Response(
                json.dumps({'success': False, 'error': str(e)}),
                content_type='application/json',
                status=500,
                headers=get_cors_headers(request)
            )

    @http.route('/api/sync-location-contacts', type='http', auth='none', methods=['POST', 'OPTIONS'], csrf=False)
    def sync_location_contacts(self, **kwargs):
        """
        Manual endpoint to trigger full GHL API synchronization for a location
        This ensures all available contacts from GHL are fetched and stored locally
        """
        if request.httprequest.method == 'OPTIONS':
            return Response(status=200, headers=get_cors_headers(request))

        location_id = kwargs.get('location_id')
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

            loc = request.env['installed.location'].sudo().search([('location_id', '=', location_id)], limit=1)
            if not loc:
                _logger.error("Location not found in DB")
                return Response(
                    json.dumps({'success': False, 'error': 'Location not found'}),
                    content_type='application/json',
                    status=404,
                    headers=get_cors_headers(request)
                )

            # Start background sync in a separate thread
            def background_full_sync():
                from odoo import api, SUPERUSER_ID
                from odoo.modules.registry import Registry
                import time
                from datetime import datetime

                dbname = request.env.cr.dbname
                max_retries = 3
                retry_delay = 2

                # Small delay to avoid immediate concurrency
                time.sleep(0.5)

                for attempt in range(max_retries):
                    try:
                        _logger.info(f"Starting full GHL sync for location {location_id} (attempt {attempt + 1})")

                        registry = Registry(dbname)
                        with registry.cursor() as cr:
                            env = api.Environment(cr, SUPERUSER_ID, {})

                            # Get fresh app record
                            app_record = env['cyclsales.application'].search([
                                ('app_id', '=', app_id),
                                ('is_active', '=', True)
                            ], limit=1)

                            if not app_record or not app_record.access_token:
                                _logger.error("No valid access token found in background sync")
                                return

                            # Get location record
                            location_record = env['installed.location'].search([
                                ('location_id', '=', location_id)
                            ], limit=1)

                            if not location_record:
                                _logger.error(f"Location {location_id} not found in background sync")
                                return

                            # First, get total count from GHL API
                            ghl_count_result = location_record.fetch_contacts_count(
                                app_record.access_token, company_id
                            )

                            if ghl_count_result.get('success'):
                                ghl_total = ghl_count_result.get('total_contacts', 0)
                                _logger.info(f"GHL API reports {ghl_total} total contacts for location {location_id}")
                            else:
                                _logger.warning(f"Could not get GHL contact count: {ghl_count_result.get('error')}")
                                ghl_total = 0

                            # Check current local count
                            current_count = env['ghl.location.contact'].search_count([
                                ('location_id.location_id', '=', location_id)
                            ])
                            _logger.info(f"Local database has {current_count} contacts before sync")

                            # If we have significantly fewer contacts locally, do a full sync
                            if ghl_total > 0 and current_count < ghl_total * 0.8:
                                _logger.info(
                                    f"Local count ({current_count}) is significantly lower than GHL total ({ghl_total}). Starting full sync...")

                                # Use the comprehensive fetch method to get all contacts
                                sync_result = location_record.fetch_location_contacts_lazy(
                                    company_id, location_id, app_record.access_token, page=1, limit=100
                                )

                                if sync_result.get('success'):
                                    # Continue fetching until we have all contacts
                                    page = 2
                                    while True:
                                        # Check if we need more contacts
                                        current_local_count = env['ghl.location.contact'].search_count([
                                            ('location_id.location_id', '=', location_id)
                                        ])

                                        if current_local_count >= ghl_total * 0.95:  # Stop when we have 95% of contacts
                                            _logger.info(
                                                f"Reached 95% of GHL contacts ({current_local_count}/{ghl_total}), stopping sync")
                                            break

                                        _logger.info(f"Fetching page {page} for location {location_id}")
                                        page_result = location_record.fetch_location_contacts_lazy(
                                            company_id, location_id, app_record.access_token, page=page, limit=100
                                        )

                                        if not page_result.get('success'):
                                            _logger.error(f"Failed to fetch page {page}: {page_result.get('error')}")
                                            break

                                        # Check if we got new contacts
                                        new_count = env['ghl.location.contact'].search_count([
                                            ('location_id.location_id', '=', location_id)
                                        ])

                                        if new_count <= current_local_count:
                                            _logger.info(f"No new contacts on page {page}, stopping")
                                            break

                                        current_local_count = new_count
                                        page += 1

                                        # Add small delay to avoid overwhelming the API
                                        time.sleep(0.5)

                                        # Safety check to prevent infinite loops
                                        if page > 50:  # Max 50 pages
                                            _logger.warning("Reached maximum page limit (50), stopping sync")
                                            break

                                    final_count = env['ghl.location.contact'].search_count([
                                        ('location_id.location_id', '=', location_id)
                                    ])
                                    _logger.info(f"Full sync completed. Final count: {final_count}/{ghl_total}")
                                else:
                                    _logger.error(f"Failed to start full sync: {sync_result.get('error')}")
                            else:
                                _logger.info(f"Local database is sufficiently synced ({current_count}/{ghl_total})")

                            cr.commit()

                    except Exception as e:
                        _logger.error(f"Background sync error (attempt {attempt + 1}): {str(e)}")
                        if attempt < max_retries - 1:
                            time.sleep(retry_delay)
                        else:
                            _logger.error(f"All retry attempts failed for location {location_id}")

            # Start background sync thread
            sync_thread = threading.Thread(target=background_full_sync)
            sync_thread.daemon = True
            sync_thread.start()
            _logger.info(f"Started full GHL sync thread for location {location_id}")

            return Response(
                json.dumps({
                    'success': True,
                    'message': 'Full GHL synchronization started in background',
                    'location_id': location_id,
                    'sync_started': True
                }),
                content_type='application/json',
                headers=get_cors_headers(request)
            )

        except Exception as e:
            import traceback
            tb = traceback.format_exc()
            _logger.error(f"Exception in sync_location_contacts: {str(e)}\n{tb}")
            return Response(
                json.dumps({'success': False, 'error': str(e), 'traceback': tb}),
                content_type='application/json',
                status=500,
                headers=get_cors_headers(request)
            )

    def _get_filtered_contacts_count_from_ghl(self, location_id, selected_user, app_access_token, company_id):
        """
        Get filtered contact count directly from GHL API
        This ensures we get the real-time count, not just local database count
        """
        try:
            from odoo.addons.web_scraper.models.ghl_api_utils import get_location_token
            import requests

            # Get location access token
            location_token = get_location_token(app_access_token, company_id, location_id)
            if not location_token:
                _logger.error("Failed to get location access token for filtered count")
                return {'success': False, 'error': 'Failed to get location access token'}

            # Build the GHL API request with user filter
            url = "https://services.leadconnectorhq.com/contacts/search"
            headers = {
                'Accept': 'application/json',
                'Authorization': f'Bearer {location_token}',
                'Version': '2021-07-28',
            }

            # Base request body
            data = {
                'locationId': location_id,
                'pageLimit': 1,  # We only need count, not actual contacts
                'page': 1,
                'sort': [
                    {
                        'field': 'dateUpdated',
                        'direction': 'desc'
                    }
                ]
            }

            # Add user filter if specified
            if selected_user and selected_user.strip():
                # GHL API supports filtering by assignedTo using the proper filter structure
                # According to documentation: field="assignedTo", operator="eq", value=user_id
                data['filters'] = [
                    {
                        "field": "assignedTo",
                        "operator": "eq",
                        "value": selected_user
                    }
                ]
                _logger.info(f"Adding GHL API filter for user: {selected_user}")
                _logger.info(f"Filter structure: {data['filters']}")
                _logger.info(f"Using field 'assignedTo' with value '{selected_user}' (per GHL API docs)")

            _logger.info(f"Fetching filtered contacts count from GHL API for location {location_id}")
            _logger.info(f"Request data: {data}")

            # First, let's test without filters to see the base response structure
            if selected_user and selected_user.strip():
                _logger.info("Testing base response structure first...")
                base_data = data.copy()
                if 'filters' in base_data:
                    del base_data['filters']

                base_response = requests.post(url, headers=headers, json=base_data, timeout=30)
                if base_response.status_code == 200:
                    base_result = base_response.json()
                    _logger.info(f"Base response (no filters): {base_result}")
                    _logger.info(f"Base response keys: {list(base_result.keys())}")
                    if 'contacts' in base_result and base_result['contacts']:
                        sample_contact = base_result['contacts'][0]
                        _logger.info(f"Sample contact structure: {sample_contact}")
                        _logger.info(f"Sample contact keys: {list(sample_contact.keys())}")
                        # Look for user assignment fields
                        user_fields = [k for k in sample_contact.keys() if 'user' in k.lower() or 'assign' in k.lower()]
                        _logger.info(f"Potential user assignment fields: {user_fields}")

                        # Also check for any fields that might contain the user ID
                        if 'assignedTo' in sample_contact:
                            _logger.info(f"assignedTo value: {sample_contact['assignedTo']}")
                        if 'assignedToId' in sample_contact:
                            _logger.info(f"assignedToId value: {sample_contact['assignedToId']}")
                        if 'userId' in sample_contact:
                            _logger.info(f"userId value: {sample_contact['userId']}")
                        if 'assignedUserId' in sample_contact:
                            _logger.info(f"assignedUserId value: {sample_contact['assignedUserId']}")

            response = requests.post(url, headers=headers, json=data, timeout=30)
            if response.status_code == 200:
                result = response.json()
                total_count = result.get('total', 0)
                _logger.info(f"GHL API filtered contacts count for location {location_id}: {total_count}")
                _logger.info(f"GHL API response structure: {list(result.keys())}")
                _logger.info(f"GHL API response sample: {result}")

                # Compare filtered vs unfiltered counts
                if selected_user and selected_user.strip():
                    _logger.info(f"COMPARISON: Filtered count: {total_count}, Expected from GHL app: ~540")
                    if total_count < 100:  # If we're getting a very low count, the filter might not be working
                        _logger.warning(f"WARNING: Filtered count ({total_count}) is much lower than expected (540).")
                        _logger.warning(f"Check GHL API response for errors or incorrect filter structure.")
                    else:
                        _logger.info(f"SUCCESS: Filter working correctly. Got {total_count} contacts (expected ~540)")

                return {'success': True, 'total_contacts': total_count, 'is_filtered': bool(selected_user)}
            else:
                _logger.error(
                    f"GHL API filtered count failed. Status: {response.status_code}, Response: {response.text}")
                return {'success': False, 'error': f'GHL API request failed with status {response.status_code}'}

        except Exception as e:
            import traceback
            tb = traceback.format_exc()
            _logger.error(f"Error getting filtered contacts count from GHL API: {str(e)}")
            _logger.error(f"Full traceback: {tb}")
            return {'success': False, 'error': str(e), 'traceback': tb}

    def _update_contact_touch_info_with_retry(self, contact, update_data, max_retries=3):
        """
        Update contact touch information with retry mechanism to handle concurrent update errors.
        Uses individual transactions to prevent bulk UPDATE conflicts.
        
        Args:
            contact: The contact record to update
            update_data: Dictionary of fields to update
            max_retries: Maximum number of retry attempts (default: 3)
        
        Returns:
            bool: True if update was successful, False otherwise
        """
        import time
        import logging
        _logger = logging.getLogger(__name__)
        
        for attempt in range(max_retries):
            try:
                # Use a separate transaction for each contact update to prevent bulk UPDATE
                with request.env.registry.cursor() as new_cr:
                    new_env = api.Environment(new_cr, SUPERUSER_ID, {})
                    
                    # Re-fetch the contact from database to get latest version
                    fresh_contact = new_env['ghl.location.contact'].sudo().browse(contact.id)
                    if not fresh_contact.exists():
                        _logger.warning(f"Contact {contact.id} no longer exists")
                        return False
                    
                    # Perform the update on the fresh record
                    fresh_contact.write(update_data)
                    
                    # Commit the individual transaction
                    new_cr.commit()
                    
                    _logger.info(f"Successfully updated contact {contact.id} touch info on attempt {attempt + 1}")
                    return True
                
            except Exception as e:
                error_str = str(e)
                if ("could not serialize access due to concurrent update" in error_str or 
                    "transaction is aborted" in error_str or
                    "deadlock detected" in error_str) and attempt < max_retries - 1:
                    
                    # Wait with exponential backoff before retrying
                    wait_time = (2 ** attempt) * 0.1  # 0.1s, 0.2s, 0.4s
                    _logger.warning(f"Concurrent update error for contact {contact.id}, retrying in {wait_time}s (attempt {attempt + 1}/{max_retries})")
                    time.sleep(wait_time)
                    continue
                else:
                    _logger.error(f"Failed to update contact {contact.id} touch info after {attempt + 1} attempts: {error_str}")
                    # Don't re-raise the exception, just log it and return False
                    return False
        
        return False

    def _bulk_update_contacts_touch_info_with_retry(self, contact_updates, max_retries=3):
        """
        Bulk update multiple contacts' touch information with retry mechanism.
        This reduces the number of individual database operations and helps prevent conflicts.
        
        Args:
            contact_updates: List of tuples (contact_id, update_data)
            max_retries: Maximum number of retry attempts (default: 3)
        
        Returns:
            dict: Results with success count and failed contact IDs
        """
        import time
        import logging
        _logger = logging.getLogger(__name__)
        
        results = {
            'success_count': 0,
            'failed_contact_ids': [],
            'total_attempts': 0
        }
        
        for attempt in range(max_retries):
            try:
                # Group updates by contact ID to avoid duplicates
                unique_updates = {}
                for contact_id, update_data in contact_updates:
                    if contact_id not in unique_updates:
                        unique_updates[contact_id] = update_data
                    else:
                        # Merge update data for the same contact
                        unique_updates[contact_id].update(update_data)
                
                # Perform bulk update
                contact_ids = list(unique_updates.keys())
                contacts = request.env['ghl.location.contact'].sudo().browse(contact_ids)
                
                # Filter out non-existent contacts
                existing_contacts = contacts.filtered(lambda c: c.exists())
                if len(existing_contacts) != len(contact_ids):
                    missing_ids = set(contact_ids) - set(existing_contacts.ids)
                    _logger.warning(f"Some contacts no longer exist: {missing_ids}")
                
                # Update each contact
                for contact in existing_contacts:
                    try:
                        contact.write(unique_updates[contact.id])
                        results['success_count'] += 1
                    except Exception as e:
                        _logger.error(f"Failed to update contact {contact.id}: {str(e)}")
                        results['failed_contact_ids'].append(contact.id)
                
                # Force a flush to ensure all updates are applied
                request.env.flush_all()
                
                _logger.info(f"Bulk update completed: {results['success_count']} successful, {len(results['failed_contact_ids'])} failed")
                return results
                
            except Exception as e:
                error_str = str(e)
                results['total_attempts'] += 1
                
                if ("could not serialize access due to concurrent update" in error_str or 
                    "transaction is aborted" in error_str or
                    "deadlock detected" in error_str) and attempt < max_retries - 1:
                    
                    # Wait with exponential backoff before retrying
                    wait_time = (2 ** attempt) * 0.2  # 0.2s, 0.4s, 0.8s
                    _logger.warning(f"Bulk update concurrent error, retrying in {wait_time}s (attempt {attempt + 1}/{max_retries})")
                    time.sleep(wait_time)
                    continue
                else:
                    _logger.error(f"Bulk update failed after {attempt + 1} attempts: {error_str}")
                    # Mark all remaining contacts as failed
                    for contact_id, _ in contact_updates:
                        if contact_id not in results['failed_contact_ids']:
                            results['failed_contact_ids'].append(contact_id)
                    break
        
        return results

    def _safe_bulk_update_contacts_with_isolation(self, contact_updates, max_retries=3):
        """
        Safely perform bulk updates with proper transaction isolation to prevent serialization failures.
        This method uses a more conservative approach with smaller batch sizes and proper isolation.
        
        Args:
            contact_updates: List of tuples (contact_id, update_data)
            max_retries: Maximum number of retry attempts (default: 3)
        
        Returns:
            dict: Results with success count and failed contact IDs
        """
        import time
        import logging
        _logger = logging.getLogger(__name__)
        
        results = {
            'success_count': 0,
            'failed_contact_ids': [],
            'total_attempts': 0
        }
        
        # Process in smaller batches to reduce lock contention
        batch_size = 10
        batches = [contact_updates[i:i + batch_size] for i in range(0, len(contact_updates), batch_size)]
        
        for batch in batches:
            for attempt in range(max_retries):
                try:
                    # Use a new transaction for each batch
                    with request.env.registry.cursor() as new_cr:
                        new_env = api.Environment(new_cr, SUPERUSER_ID, {})
                        
                        # Group updates by contact ID
                        unique_updates = {}
                        for contact_id, update_data in batch:
                            if contact_id not in unique_updates:
                                unique_updates[contact_id] = update_data
                            else:
                                unique_updates[contact_id].update(update_data)
                        
                        # Get fresh contact records
                        contact_ids = list(unique_updates.keys())
                        contacts = new_env['ghl.location.contact'].sudo().browse(contact_ids)
                        
                        # Filter existing contacts
                        existing_contacts = contacts.filtered(lambda c: c.exists())
                        
                        # Update each contact individually to avoid bulk lock conflicts
                        for contact in existing_contacts:
                            try:
                                contact.write(unique_updates[contact.id])
                                results['success_count'] += 1
                            except Exception as e:
                                _logger.error(f"Failed to update contact {contact.id} in batch: {str(e)}")
                                results['failed_contact_ids'].append(contact.id)
                        
                        # Commit the batch
                        new_cr.commit()
                        _logger.info(f"Successfully processed batch of {len(existing_contacts)} contacts")
                        break  # Success, move to next batch
                        
                except Exception as e:
                    error_str = str(e)
                    results['total_attempts'] += 1
                    
                    if ("could not serialize access due to concurrent update" in error_str or 
                        "transaction is aborted" in error_str or
                        "deadlock detected" in error_str) and attempt < max_retries - 1:
                        
                        # Wait with exponential backoff before retrying
                        wait_time = (2 ** attempt) * 0.3  # 0.3s, 0.6s, 1.2s
                        _logger.warning(f"Batch update concurrent error, retrying in {wait_time}s (attempt {attempt + 1}/{max_retries})")
                        time.sleep(wait_time)
                        continue
                    else:
                        _logger.error(f"Batch update failed after {attempt + 1} attempts: {error_str}")
                        # Mark all contacts in this batch as failed
                        for contact_id, _ in batch:
                            if contact_id not in results['failed_contact_ids']:
                                results['failed_contact_ids'].append(contact_id)
                        break
        
        _logger.info(f"Safe bulk update completed: {results['success_count']} successful, {len(results['failed_contact_ids'])} failed")
        return results
