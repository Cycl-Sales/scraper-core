from odoo import http
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
        _logger.info(f"Using app_id: {app_id}")
        return app_id
    
    @http.route('/api/installed-locations', type='http', auth='none', methods=['GET', 'OPTIONS'], csrf=False)
    def get_installed_locations(self, **kwargs):
        """
        Fast version that returns cached data immediately and triggers background sync
        """
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
                        _logger.info("Created new res.config.settings record for sync status tracking.")
                    config.write({
                        'ghl_locations_sync_status': 'in_progress',
                        'ghl_locations_sync_started': datetime.now(),
                        'ghl_locations_sync_app_id': app_id
                    })
                    _logger.info(f"Set sync status to in_progress on config id={config.id}")
                    cr.commit()
            except Exception as e:
                _logger.error(f"Error setting sync status: {str(e)}")

            for attempt in range(max_retries):
                try:
                    _logger.info(
                        f"Starting background sync for installed locations with app_id: {app_id} (attempt {attempt + 1})")

                    # Get the registry and create a new environment with a fresh cursor
                    registry = Registry(current_dbname)
                    with registry.cursor() as cr:
                        # Create a new environment with the fresh cursor
                        env = api.Environment(cr, SUPERUSER_ID, {})

                        # Call the fetch_installed_locations function from the model
                        installed_location_model = env['installed.location'].sudo()
                        _logger.info(f"Calling fetch_installed_locations with company_id={company_id}, app_id={app_id}")
                        result = installed_location_model.fetch_installed_locations(
                            company_id=company_id,
                            app_id=app_id,
                            limit=500
                        )
                        _logger.info(f"Background fetch_installed_locations result: {result}")

                        # Update sync status to "completed"
                        config = env['res.config.settings'].sudo().search([], limit=1)
                        if not config:
                            config = env['res.config.settings'].sudo().create({})
                            _logger.info(
                                "Created new res.config.settings record for sync status tracking (completed phase).")
                        config.write({
                            'ghl_locations_sync_status': 'completed',
                            'ghl_locations_sync_completed': datetime.now(),
                            'ghl_locations_sync_result': str(result.get('success', False))
                        })
                        _logger.info(f"Set sync status to completed on config id={config.id}")

                        # Commit the transaction
                        cr.commit()
                        _logger.info(f"Background sync completed successfully on attempt {attempt + 1}")
                        break  # Success, exit retry loop

                except Exception as e:
                    _logger.error(f"Background sync error on attempt {attempt + 1}: {str(e)}")

                    # If it's a concurrency error, wait and retry
                    if "concurrent update" in str(e) or "transaction is aborted" in str(e):
                        if attempt < max_retries - 1:  # Don't sleep on last attempt
                            _logger.info(f"Concurrency error detected, retrying in {retry_delay} seconds...")
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
                                        _logger.info(
                                            "Created new res.config.settings record for sync status tracking (failed phase).")
                                    config.write({
                                        'ghl_locations_sync_status': 'failed',
                                        'ghl_locations_sync_error': str(e)
                                    })
                                    _logger.info(f"Set sync status to failed on config id={config.id}")
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
        _logger.info(f"InstalledLocationController.get_installed_locations_fresh called with kwargs: {kwargs}")

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
        _logger.info(f"get_installed_locations_sync_status called with kwargs: {kwargs}")

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
        _logger.info(f"get_location_users called with kwargs: {kwargs}")
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
        _logger.info(f"get_location_contacts_fast called with kwargs: {kwargs}")
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
        _logger.info(f"get_location_contacts_count called with kwargs: {kwargs}")
        if request.httprequest.method == 'OPTIONS':
            return Response(status=200, headers=get_cors_headers(request))

        location_id = kwargs.get('location_id')
        _logger.info(f"location_id param: {location_id}")
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
            
            result = loc.fetch_contacts_count(app.access_token, 'Ipg8nKDPLYKsbtodR6LN')
            _logger.info(f"fetch_contacts_count result: {result}")
            if result.get('success'):
                return Response(
                    json.dumps({
                        'success': True,
                        'total_contacts': result.get('total_contacts', 0),
                        'location_id': location_id
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
        _logger.info(f"get_location_contacts_lazy called with kwargs: {kwargs}")
        if request.httprequest.method == 'OPTIONS':
            return Response(status=200, headers=get_cors_headers(request))

        location_id = kwargs.get('location_id')
        page = int(kwargs.get('page', 1))
        limit = int(kwargs.get('limit', 10))
        _logger.info(f"location_id param: {location_id}, page: {page}, limit: {limit}")
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
        DISABLED: Temporarily disabled to prevent automatic background sync
        """
        _logger.info(f"get_contact_details called with kwargs: {kwargs} - DISABLED")
        if request.httprequest.method == 'OPTIONS':
            return Response(status=200, headers=get_cors_headers(request))

        # Return a simple response indicating the endpoint is disabled
        return Response(
            json.dumps({
                'success': False, 
                'error': 'Contact details endpoint temporarily disabled to prevent background sync',
                'message': 'This endpoint is disabled to prevent automatic background sync. Please use manual sync when needed.'
            }),
            content_type='application/json',
            status=503,  # Service Unavailable
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
        _logger.info(f"update_touch_information called with kwargs: {kwargs}")
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
        _logger.info(f"sync_contact_details_background called with kwargs: {kwargs}")
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

    @http.route('/api/debug-contact/<int:contact_id>', type='http', auth='none', methods=['GET', 'OPTIONS'], csrf=False)
    def debug_contact(self, contact_id, **kwargs):
        """
        Debug endpoint to check what data exists for a specific contact
        """
        _logger.info(f"debug_contact called for contact_id: {contact_id}")
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

            # Get messages for this contact
            messages = request.env['ghl.contact.message'].sudo().search([
                ('contact_id', '=', contact_id)
            ])

            # Get messages for each conversation
            conversation_details = []
            for conv in conversations:
                conv_messages = request.env['ghl.contact.message'].sudo().search([
                    ('conversation_id', '=', conv.id)
                ])
                conversation_details.append({
                    'conversation_id': conv.id,
                    'ghl_id': conv.ghl_id,
                    'messages_count': len(conv_messages),
                    'messages': [{
                        'id': msg.id,
                        'ghl_id': msg.ghl_id,
                        'message_type': msg.message_type,
                        'body': msg.body[:100] + '...' if msg.body and len(msg.body) > 100 else msg.body,
                        'date_added': msg.date_added.isoformat() if msg.date_added else None
                    } for msg in conv_messages]
                })

            debug_data = {
                'contact_id': contact.id,
                'contact_name': contact.name,
                'external_id': contact.external_id,
                'conversations_count': len(conversations),
                'messages_count': len(messages),
                'touch_summary': contact.touch_summary,
                'last_touch_date': contact.last_touch_date.isoformat() if contact.last_touch_date else None,
                'conversations': conversation_details,
                'all_messages': [{
                    'id': msg.id,
                    'ghl_id': msg.ghl_id,
                    'conversation_id': msg.conversation_id.id if msg.conversation_id else None,
                    'message_type': msg.message_type,
                    'body': msg.body[:100] + '...' if msg.body and len(msg.body) > 100 else msg.body,
                    'date_added': msg.date_added.isoformat() if msg.date_added else None
                } for msg in messages]
            }

            return Response(
                json.dumps({
                    'success': True,
                    'debug_data': debug_data
                }, indent=2),
                content_type='application/json',
                status=200,
                headers=get_cors_headers(request)
            )

        except Exception as e:
            import traceback
            tb = traceback.format_exc()
            _logger.error(f"Exception in debug_contact: {str(e)}\n{tb}")
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

            # Update the contact
            contact.write(update_vals)

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
        """Compute touch summary for a contact on-the-fly"""
        messages = request.env['ghl.contact.message'].sudo().search([
            ('contact_id', '=', contact.id)
        ])

        if not messages:
            return 'no_touches'

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

        return ', '.join(touch_parts) if touch_parts else 'no_touches'

    def _compute_last_touch_date_for_contact(self, contact):
        """Compute last touch date for a contact on-the-fly"""
        last_message = request.env['ghl.contact.message'].sudo().search([
            ('contact_id', '=', contact.id)
        ], order='date_added desc', limit=1)

        return last_message.date_added.isoformat() if last_message and last_message.date_added else ''

    def _compute_last_message_for_contact(self, contact):
        """Compute last message for a contact on-the-fly"""
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
            return ''

    @http.route('/api/location-contacts-optimized', type='http', auth='none', methods=['GET', 'OPTIONS'], csrf=False)
    def get_location_contacts_optimized(self, **kwargs):
        """
        Optimized endpoint that returns basic contact data immediately and fetches detailed data in background
        Only fetches data for the contacts currently being displayed
        """
        _logger.info(f"get_location_contacts_optimized called with kwargs: {kwargs}")
        if request.httprequest.method == 'OPTIONS':
            return Response(status=200, headers=get_cors_headers(request))

        location_id = kwargs.get('location_id')
        page = int(kwargs.get('page', 1))
        limit = int(kwargs.get('limit', 10))
        _logger.info(f"location_id param: {location_id}, page: {page}, limit: {limit}")

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

            # STEP 1: Fetch basic contact data from GHL API (fast)
            _logger.info(f"Fetching basic contact data from GHL API for location: {location_id}")
            result = loc.fetch_location_contacts_lazy(company_id, location_id, app.access_token, page=page, limit=limit)
            _logger.info(f"fetch_location_contacts_lazy result: {result}")

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

            # STEP 2: Get the contacts that were just fetched (only the current page)
            contacts = request.env['ghl.location.contact'].sudo().search([
                ('location_id.location_id', '=', location_id)
            ], order='date_added desc', limit=limit, offset=(page - 1) * limit)
            
            _logger.info(f"Retrieved {len(contacts)} contacts from database for location {location_id}, page {page}")
            for contact in contacts:
                _logger.info(f"Contact {contact.id} (external_id: {contact.external_id}) - AI fields in DB: status='{contact.ai_status}', summary='{contact.ai_summary}', quality='{contact.ai_quality_grade}', sales='{contact.ai_sales_grade}'")

            # STEP 3: Return basic data immediately
            contact_data = []
            contact_ids_for_background = []

            for contact in contacts:
                contact_ids_for_background.append(contact.id)

                # Parse basic data
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

                # Get basic touch information (from existing data)
                touch_summary = self._compute_touch_summary_for_contact(contact)
                last_touch_date = self._compute_last_touch_date_for_contact(contact)
                last_message_data = self._compute_last_message_for_contact(contact)

                # Get basic counts (from existing data)
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
                    'ai_status': contact.ai_status or 'not_contacted',
                    'ai_summary': contact.ai_summary or 'AI analysis pending',
                    'ai_quality_grade': contact.ai_quality_grade or 'no_grade',
                    'ai_sales_grade': contact.ai_sales_grade or 'no_grade',
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
                    'details_fetched': False,  # Will be updated in background
                    'has_tasks': tasks_count > 0,
                    'has_conversations': conversations_count > 0,
                    'tasks_count': tasks_count,
                    'conversations_count': conversations_count,
                    'conversations_count_basic': conversations_count,
                    'loading_details': True,  # Frontend will show loading state
                }

                # Debug: Log AI fields for this contact
                _logger.info(f"Contact {contact.id} (external_id: {contact.external_id}) - AI fields in DB: status='{contact.ai_status}', summary='{contact.ai_summary}', quality='{contact.ai_quality_grade}', sales='{contact.ai_sales_grade}'")
                _logger.info(f"Contact {contact.id} AI fields being sent to frontend: status={contact_info['ai_status']}, summary={contact_info['ai_summary'][:50]}..., quality={contact_info['ai_quality_grade']}, sales={contact_info['ai_sales_grade']}")
                
                # Additional debug: Check if AI fields are actually saved
                if contact.ai_status and contact.ai_status != 'not_contacted':
                    _logger.info(f"Contact {contact.id} has AI data: status='{contact.ai_status}', summary='{contact.ai_summary[:100] if contact.ai_summary else 'None'}...'")
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

                                    # Mark contact as having details fetched first
                                    try:
                                        contact.write({'details_fetched': True})
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

    @http.route('/api/contact-sync-status', type='http', auth='none', methods=['GET', 'OPTIONS'], csrf=False)
    def get_contact_sync_status(self, **kwargs):
        import json
        """
        Check sync status for specific contacts and return detailed data if ready
        """
        _logger.info(f"get_contact_sync_status called with kwargs: {kwargs}")
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
                        last_message = messages.sorted('date_added', reverse=True)[0] if messages else None
                        last_touch_date = last_message.date_added if last_message else False

                        # Get last message content
                        last_message_data = None
                        if last_message and last_message.body:
                            import json
                            last_message_data = {
                                'body': last_message.body,
                                'type': last_message.message_type,
                                'direction': last_message.direction,
                                'date_added': last_message.date_added.isoformat() if last_message.date_added else '',
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
                        request.env['ghl.contact.message.transcript'].sudo().fetch_transcript_for_message(
                            message_id=message.id, app_id='684c5cc0736d09f78555981f')
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
                'nextSteps': [],
                'sentiment': 'neutral'
            }

            # Basic AI analysis based on transcript
            ai_analysis = {
                'overallScore': 7,
                'categories': {
                    'communication': 7,
                    'professionalism': 8,
                    'problemSolving': 6,
                    'followUp': 7
                },
                'highlights': [],
                'improvements': [],
                'callIntent': 'Initial outreach',
                'satisfactionLevel': 'medium'
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

    @http.route('/api/run-ai-analysis/<int:contact_id>', type='http', auth='none', methods=['POST', 'OPTIONS'], csrf=False)
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
            _logger.info(f"Contact {contact_id} AI fields after analysis: status='{contact.ai_status}', summary='{contact.ai_summary}', quality='{contact.ai_quality_grade}', sales='{contact.ai_sales_grade}'")
            
            # Force a database commit to ensure the data is saved
            request.env.cr.commit()
            _logger.info(f"Contact {contact_id} AI data committed to database")
            
            # Verify the data was actually saved by re-reading from database
            _logger.info(f"Contact {contact_id} AI fields after commit verification: status='{contact.ai_status}', summary='{contact.ai_summary}', quality='{contact.ai_quality_grade}', sales='{contact.ai_sales_grade}'")
            
            # Additional verification: Query the database directly
            contact_from_db = request.env['ghl.location.contact'].sudo().browse(contact_id)
            _logger.info(f"Contact {contact_id} AI fields from direct DB query: status='{contact_from_db.ai_status}', summary='{contact_from_db.ai_summary}', quality='{contact_from_db.ai_quality_grade}', sales='{contact_from_db.ai_sales_grade}'")
            
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

    @http.route('/api/debug-contact-ai/<int:contact_id>', type='http', auth='none', methods=['GET', 'OPTIONS'], csrf=False)
    def debug_contact_ai(self, contact_id, **kwargs):
        """
        Debug endpoint to check AI analysis status for a contact
        """
        _logger.info(f"Debug contact AI called for contact_id: {contact_id}")

        # Handle preflight OPTIONS request
        if request.httprequest.method == 'OPTIONS':
            return Response(
                status=200,
                headers=get_cors_headers(request)
            )

        try:
            contact = request.env['ghl.location.contact'].sudo().search([('id', '=', contact_id)], limit=1)
            if not contact:
                return Response(
                    json.dumps({'error': 'Contact not found'}),
                    content_type='application/json',
                    status=404,
                    headers=get_cors_headers(request)
                )

            # Get AI-related fields
            ai_data = {
                'contact_id': contact.id,
                'external_id': contact.external_id,
                'contact_name': contact.contact_name,
                'ai_status': contact.ai_status,
                'ai_summary': contact.ai_summary,
                'ai_quality_grade': contact.ai_quality_grade,
                'ai_sales_grade': contact.ai_sales_grade,
                'last_touch_date': contact.last_touch_date.isoformat() if contact.last_touch_date else None,
                'touch_summary': contact.touch_summary,
                'engagement_summary': contact.engagement_summary,
                'total_pipeline_value': contact.total_pipeline_value,
                'opportunities': contact.opportunities,
            }

            return Response(
                json.dumps(ai_data),
                content_type='application/json',
                headers=get_cors_headers(request)
            )

        except Exception as e:
            _logger.error(f"Error in debug_contact_ai: {str(e)}")
            return Response(
                json.dumps({'error': str(e)}),
                content_type='application/json',
                status=500,
                headers=get_cors_headers(request)
            )

    @http.route('/api/location-openai-key/<string:location_id>', type='http', auth='none', methods=['GET', 'PUT', 'OPTIONS'], csrf=False)
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

    @http.route('/api/location-openai-key/<string:location_id>/validate', type='http', auth='none', methods=['POST', 'OPTIONS'], csrf=False)
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
