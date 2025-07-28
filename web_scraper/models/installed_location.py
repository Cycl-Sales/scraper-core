from odoo import models, fields, api, _
import requests
import logging
import json
from datetime import datetime
import threading

_logger = logging.getLogger(__name__)


class InstalledLocation(models.Model):
    _name = 'installed.location'
    _description = 'Installed GHL Location'
    _order = 'name'

    location_id = fields.Char(string='Location ID', required=True, index=True)
    name = fields.Char(string='Name', required=True)
    address = fields.Char(string='Address')
    is_installed = fields.Boolean(string='Is Installed', default=False)
    app_id = fields.Char(string='App ID')
    application_ids = fields.Many2many(
        'cyclsales.application',
        'cyclsales_application_location_rel',
        'location_id',
        'application_id',
        string='Installed Applications'
    )
    count = fields.Integer(string='Count')
    contacts_count = fields.Integer(string='Total Contacts', default=0,
                                    help='Total number of contacts for this location')
    install_to_future_locations = fields.Boolean(string='Install to Future Locations', default=False)
    detail_ids = fields.One2many('installed.location.detail', 'location_id', string='Location Details')
    automation_group = fields.Char(string='Automation Group')
    ad_accounts = fields.Integer(string='Ad Accounts')
    total_ad_spend = fields.Char(string='Total Ad Spend')
    cost_per_conversion = fields.Char(string='Cost per Conversion')
    new_contacts = fields.Integer(string='New Contacts')
    new_contacts_change = fields.Char(string='New Contacts Change')
    median_ai_quality_grade = fields.Char(string='Median AI Quality Grade')
    median_ai_quality_grade_color = fields.Char(string='Median AI Quality Grade Color')
    touch_rate = fields.Char(string='Touch Rate')
    touch_rate_change = fields.Char(string='Touch Rate Change')
    engagement_rate = fields.Char(string='Engagement Rate')
    engagement_rate_change = fields.Char(string='Engagement Rate Change')
    speed_to_lead = fields.Char(string='Speed to Lead')
    median_ai_sales_grade = fields.Char(string='Median AI Sales Grade')
    median_ai_sales_grade_color = fields.Char(string='Median AI Sales Grade Color')
    close_rate = fields.Char(string='Close Rate')
    revenue_per_contact = fields.Char(string='Revenue per Contact')
    gross_roas = fields.Char(string='Gross ROAS')

    def refresh_details(self):
        """Refresh location details from the GHL API"""
        # Find the access token from cyclsales.application
        app = self.env['cyclsales.application'].sudo().search([
            ('app_id', '=', self.app_id),
            ('is_active', '=', True)
        ], limit=1)
        if not app or not app.access_token:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Error',
                    'message': 'No valid access token found for this app_id.',
                    'type': 'danger',
                }
            }

        # Fetch details for this location
        self.fetch_location_details(self.location_id, app.access_token)

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Success',
                'message': 'Location details refreshed successfully.',
                'type': 'success',
            }
        }

    def fetch_location_details(self, location_id, access_token):
        url = f"https://services.leadconnectorhq.com/locations/{location_id}"
        headers = {
            'Accept': 'application/json',
            'Authorization': f'Bearer {access_token}',
            'Version': '2021-07-28',
        }
        _logger.info(f"Fetching details for location_id={location_id} with URL={url}")
        try:
            resp = requests.get(url, headers=headers)
            _logger.info(f"Details API response status: {resp.status_code}")
            _logger.info(f"Details API response text: {resp.text}")
            if resp.status_code == 200:
                details = resp.json()
                _logger.info(f"Parsed details JSON: {details}")

                # Extract location data from the nested structure
                location_data = details.get('location', {})
                if not location_data:
                    _logger.error(f"No location data found in response for location {location_id}")
                    return

                # Map API field names to Odoo field names for business
                business_vals = {}
                if location_data.get('business'):
                    business_data = location_data.get('business', {})
                    business_vals = {
                        'name': business_data.get('name'),
                        'address': business_data.get('address'),
                        'city': business_data.get('city'),
                        'state': business_data.get('state'),
                        'country': business_data.get('country'),
                        'postal_code': business_data.get('postalCode'),
                        'website': business_data.get('website'),
                        'timezone': business_data.get('timezone'),
                        'logo_url': business_data.get('logoUrl'),
                    }
                    _logger.info(f"Business values: {business_vals}")

                # Map API field names to Odoo field names for social
                social_vals = {}
                if location_data.get('social'):
                    social_data = location_data.get('social', {})
                    social_vals = {
                        'facebook_url': social_data.get('facebookUrl'),
                        'google_plus': social_data.get('googlePlus'),
                        'linked_in': social_data.get('linkedIn'),
                        'foursquare': social_data.get('foursquare'),
                        'twitter': social_data.get('twitter'),
                        'yelp': social_data.get('yelp'),
                        'instagram': social_data.get('instagram'),
                        'youtube': social_data.get('youtube'),
                        'pinterest': social_data.get('pinterest'),
                        'blog_rss': social_data.get('blogRss'),
                        'google_places_id': social_data.get('googlePlacesId'),
                    }
                    _logger.info(f"Social values: {social_vals}")

                # Map API field names to Odoo field names for settings
                settings_vals = {}
                if location_data.get('settings'):
                    settings_data = location_data.get('settings', {})
                    settings_vals = {
                        'allow_duplicate_contact': settings_data.get('allowDuplicateContact'),
                        'allow_duplicate_opportunity': settings_data.get('allowDuplicateOpportunity'),
                        'allow_facebook_name_merge': settings_data.get('allowFacebookNameMerge'),
                        'disable_contact_timezone': settings_data.get('disableContactTimezone'),
                    }
                    _logger.info(f"Settings values: {settings_vals}")

                # Map API field names to Odoo field names for reseller
                reseller_vals = {}
                if location_data.get('reseller'):
                    reseller_data = location_data.get('reseller', {})
                    # Add reseller fields as needed
                    _logger.info(f"Reseller values: {reseller_vals}")

                business = False
                social = False
                settings = False
                reseller = False

                if business_vals:
                    try:
                        business = self.env['location.business'].sudo().create(business_vals)
                        _logger.info(f"Created business record with ID: {business.id}")
                    except Exception as e:
                        _logger.error(f"Error creating business record: {e}")

                if social_vals:
                    try:
                        social = self.env['location.social'].sudo().create(social_vals)
                        _logger.info(f"Created social record with ID: {social.id}")
                    except Exception as e:
                        _logger.error(f"Error creating social record: {e}")

                if settings_vals:
                    try:
                        settings = self.env['location.settings'].sudo().create(settings_vals)
                        _logger.info(f"Created settings record with ID: {settings.id}")
                    except Exception as e:
                        _logger.error(f"Error creating settings record: {e}")

                if reseller_vals:
                    try:
                        reseller = self.env['location.reseller'].sudo().create(reseller_vals)
                        _logger.info(f"Created reseller record with ID: {reseller.id}")
                    except Exception as e:
                        _logger.error(f"Error creating reseller record: {e}")

                detail_vals = {
                    'location_id': self.id,
                    'company_id': location_data.get('companyId'),
                    'name': location_data.get('name'),
                    'domain': location_data.get('domain'),
                    'address': location_data.get('address'),
                    'city': location_data.get('city'),
                    'state': location_data.get('state'),
                    'logo_url': location_data.get('logoUrl'),
                    'country': location_data.get('country'),
                    'postal_code': location_data.get('postalCode'),
                    'website': location_data.get('website'),
                    'timezone': location_data.get('timezone'),
                    'first_name': location_data.get('firstName'),
                    'last_name': location_data.get('lastName'),
                    'email': location_data.get('email'),
                    'phone': location_data.get('phone'),
                    'business_id': business.id if business else False,
                    'social_id': social.id if social else False,
                    'settings_id': settings.id if settings else False,
                    'reseller_id': reseller.id if reseller else False,
                }
                _logger.info(f"Detail values to write/create: {detail_vals}")
                detail = self.env['installed.location.detail'].sudo().search([('location_id', '=', self.id)], limit=1)
                if detail:
                    _logger.info(f"Updating existing installed.location.detail id={detail.id}")
                    detail.write(detail_vals)
                    _logger.info(f"Updated detail record with values: {detail_vals}")
                else:
                    _logger.info(f"Creating new installed.location.detail for location_id={self.id}")
                    detail = self.env['installed.location.detail'].sudo().create(detail_vals)
                    _logger.info(f"Created detail record with ID: {detail.id}")
            else:
                _logger.error(f"Failed to fetch details for location {location_id}: {resp.text}")
        except Exception as e:
            _logger.error(f"Error fetching details for location {location_id}: {e}")

    def fetch_location_users(self, company_id, location_id, app_access_token):
        """
        Fetch users for a location using the GHL API and create/update user records.
        1. Get location access token
        2. Use it to fetch users
        3. Create/update user records in ghl.location.user model
        """
        import requests
        import logging
        _logger = logging.getLogger(__name__)

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

        try:
            token_resp = requests.post(token_url, headers=headers, data=data)
            _logger.info(f"Location token response: {token_resp.status_code} {token_resp.text}")
            if token_resp.status_code not in (200, 201):
                _logger.error(f"Failed to get location token: {token_resp.text}")
                return None

            token_json = token_resp.json()
            location_token = token_json.get('access_token')
            if not location_token:
                _logger.error(f"No access_token in location token response: {token_json}")
                return None

            # Step 2: Fetch users
            users_url = f"https://services.leadconnectorhq.com/users/?locationId={location_id}"
            user_headers = {
                'Accept': 'application/json',
                'Authorization': f'Bearer {location_token}',
                'Version': '2021-07-28',
            }
            users_resp = requests.get(users_url, headers=user_headers)
            _logger.info(f"Users API response: {users_resp.status_code} {users_resp.text}")

            if users_resp.status_code == 200:
                users_json = users_resp.json()
                _logger.info(f"Fetched users for location {location_id}: {users_json}")

                # Step 3: Process and create/update user records
                users_data = users_json.get('users', [])
                created_count = 0
                updated_count = 0

                for user_data in users_data:
                    try:
                        # Extract user data
                        external_id = user_data.get('id')  # Changed from '_id' to 'id'
                        name = user_data.get('name', '')
                        first_name = user_data.get('firstName', '')
                        last_name = user_data.get('lastName', '')
                        email = user_data.get('email', '')
                        phone = user_data.get('phone', '')
                        extension = user_data.get('extension', '')
                        scopes = user_data.get('scopes', '')
                        deleted = user_data.get('deleted', False)

                        # Check if user already exists
                        existing_user = self.env['ghl.location.user'].sudo().search([
                            ('external_id', '=', external_id),
                            ('location_id', '=', location_id)
                        ], limit=1)

                        # Prepare user values
                        user_vals = {
                            'external_id': external_id,
                            'name': name,
                            'first_name': first_name,
                            'last_name': last_name,
                            'email': email,
                            'phone': phone,
                            'extension': extension,
                            'scopes': scopes,
                            'deleted': deleted,
                            'location_id': location_id,
                            'profile_photo': user_data.get('profilePhoto', ''),
                            'membership_contact_id': user_data.get('membershipContactId', ''),
                            'freshdesk_contact_id': user_data.get('freshdeskContactId', ''),
                            'totp_enabled': user_data.get('totpEnabled', False),
                        }

                        # Handle permissions
                        permissions_data = user_data.get('permissions', {})
                        if permissions_data:
                            permissions_vals = {
                                'campaigns_enabled': permissions_data.get('campaignsEnabled', False),
                                'campaigns_read_only': permissions_data.get('campaignsReadOnly', False),
                                'contacts_enabled': permissions_data.get('contactsEnabled', False),
                                'workflows_enabled': permissions_data.get('workflowsEnabled', False),
                                'workflows_read_only': permissions_data.get('workflowsReadOnly', False),
                                'triggers_enabled': permissions_data.get('triggersEnabled', False),
                                'funnels_enabled': permissions_data.get('funnelsEnabled', False),
                                'websites_enabled': permissions_data.get('websitesEnabled', False),
                                'opportunities_enabled': permissions_data.get('opportunitiesEnabled', False),
                                'dashboard_stats_enabled': permissions_data.get('dashboardStatsEnabled', False),
                                'bulk_requests_enabled': permissions_data.get('bulkRequestsEnabled', False),
                                'appointments_enabled': permissions_data.get('appointmentsEnabled', False),
                                'reviews_enabled': permissions_data.get('reviewsEnabled', False),
                                'online_listings_enabled': permissions_data.get('onlineListingsEnabled', False),
                                'phone_call_enabled': permissions_data.get('phoneCallEnabled', False),
                                'conversations_enabled': permissions_data.get('conversationsEnabled', False),
                                'assigned_data_only': permissions_data.get('assignedDataOnly', False),
                                'adwords_reporting_enabled': permissions_data.get('adwordsReportingEnabled', False),
                                'membership_enabled': permissions_data.get('membershipEnabled', False),
                                'facebook_ads_reporting_enabled': permissions_data.get('facebookAdsReportingEnabled',
                                                                                       False),
                                'attributions_reporting_enabled': permissions_data.get('attributionsReportingEnabled',
                                                                                       False),
                                'settings_enabled': permissions_data.get('settingsEnabled', False),
                                'tags_enabled': permissions_data.get('tagsEnabled', False),
                                'lead_value_enabled': permissions_data.get('leadValueEnabled', False),
                                'marketing_enabled': permissions_data.get('marketingEnabled', False),
                                'agent_reporting_enabled': permissions_data.get('agentReportingEnabled', False),
                                'bot_service': permissions_data.get('botService', False),
                                'social_planner': permissions_data.get('socialPlanner', False),
                                'blogging_enabled': permissions_data.get('bloggingEnabled', False),
                                'invoice_enabled': permissions_data.get('invoiceEnabled', False),
                                'affiliate_manager_enabled': permissions_data.get('affiliateManagerEnabled', False),
                                'content_ai_enabled': permissions_data.get('contentAiEnabled', False),
                                'refunds_enabled': permissions_data.get('refundsEnabled', False),
                                'record_payment_enabled': permissions_data.get('recordPaymentEnabled', False),
                                'cancel_subscription_enabled': permissions_data.get('cancelSubscriptionEnabled', False),
                                'payments_enabled': permissions_data.get('paymentsEnabled', False),
                                'communities_enabled': permissions_data.get('communitiesEnabled', False),
                                'export_payments_enabled': permissions_data.get('exportPaymentsEnabled', False),
                            }

                            # Create or update permissions record
                            if existing_user and existing_user.permissions_id:
                                existing_user.permissions_id.write(permissions_vals)
                                permissions_record = existing_user.permissions_id
                            else:
                                permissions_record = self.env['ghl.location.user.permissions'].sudo().create(
                                    permissions_vals)

                            user_vals['permissions_id'] = permissions_record.id

                        # Handle roles
                        roles_data = user_data.get('roles', {})
                        if roles_data:
                            roles_vals = {
                                'type': roles_data.get('type', ''),
                                'role': roles_data.get('role', ''),
                                'restrict_sub_account': roles_data.get('restrictSubAccount', False),
                            }

                            # Create or update roles record
                            if existing_user and existing_user.roles_id:
                                existing_user.roles_id.write(roles_vals)
                                roles_record = existing_user.roles_id
                            else:
                                roles_record = self.env['ghl.location.user.roles'].sudo().create(roles_vals)

                            user_vals['roles_id'] = roles_record.id

                        # Handle lcphone
                        lcphone_data = user_data.get('lcPhone', {})
                        if lcphone_data:
                            # lcPhone is an object with phone IDs as keys, so we'll store it as JSON
                            lcphone_vals = {
                                'location_id': str(lcphone_data),  # Convert the object to string for now
                            }

                            # Create or update lcphone record
                            if existing_user and existing_user.lc_phone_id:
                                existing_user.lc_phone_id.write(lcphone_vals)
                                lcphone_record = existing_user.lc_phone_id
                            else:
                                lcphone_record = self.env['ghl.location.user.lcphone'].sudo().create(lcphone_vals)

                            user_vals['lc_phone_id'] = lcphone_record.id

                        # Create or update user record
                        if existing_user:
                            existing_user.write(user_vals)
                            updated_count += 1
                            _logger.info(f"Updated user record for external_id: {external_id}")
                        else:
                            self.env['ghl.location.user'].sudo().create(user_vals)
                            created_count += 1
                            _logger.info(f"Created user record for external_id: {external_id}")

                    except Exception as e:
                        _logger.error(f"Error processing user {user_data.get('_id', 'unknown')}: {e}")
                        continue

                _logger.info(
                    f"User sync completed for location {location_id}: {created_count} created, {updated_count} updated")
                return {
                    'success': True,
                    'created_count': created_count,
                    'updated_count': updated_count,
                    'total_users': len(users_data)
                }
            else:
                _logger.error(f"Failed to fetch users: {users_resp.text}")
                return None
        except Exception as e:
            _logger.error(f"Error fetching location users: {e}")
            return None

    @api.model
    def fetch_installed_locations(self, company_id, app_id, limit=500):
        """
        Fetch installed locations from the GHL API, using the access token from cyclsales.application.
        Args:
            company_id (str): The GHL company ID
            app_id (str): The GHL app ID
            limit (int): Max number of locations to fetch (default 500)
        Returns:
            dict: API response or error
        """
        # Find the access token from cyclsales.application
        app = self.env['cyclsales.application'].sudo().search([
            ('app_id', '=', app_id),
            ('is_active', '=', True)
        ], limit=1)
        if not app or not app.access_token:
            return {'success': False, 'error': 'No valid access token found for this app_id.'}
        access_token = app.access_token
        url = (
            f"https://services.leadconnectorhq.com/oauth/installedLocations?"
            f"limit={limit}&isInstalled=true&companyId={company_id}&appId={app_id}"
        )
        headers = {
            'Accept': 'application/json',
            'Authorization': f'Bearer {access_token}',
            'Version': '2021-07-28',
        }
        try:
            response = requests.get(url, headers=headers)
            print(response.json())
            print('123123')
            if response.status_code == 200:
                data = response.json()
                # Update count and install_to_future_locations on a dummy record (or all records)
                count = data.get('count')
                install_to_future = data.get('installToFutureLocations')
                for loc in data.get('locations', []):
                    vals = {
                        'location_id': loc.get('_id'),
                        'name': loc.get('name'),
                        'address': loc.get('address'),
                        'is_installed': loc.get('isInstalled', False),
                        'app_id': app_id,
                        'count': count,
                        'install_to_future_locations': install_to_future,
                    }
                    rec = self.sudo().search([('location_id', '=', vals['location_id']), ('app_id', '=', app_id)],
                                             limit=1)
                    if rec:
                        rec.write(vals)
                    else:
                        rec = self.sudo().create(vals)
                    # Fetch and sync details for this location
                    rec.fetch_location_details(loc.get('_id'), access_token)
                return {'success': True, 'data': data}
            else:
                return {'success': False, 'error': response.text, 'status_code': response.status_code}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def fetch_contacts_count(self, app_access_token, company_id):
        """
        Fetch the total number of contacts for this location using the /contacts/search endpoint
        """
        from .ghl_api_utils import get_location_token
        try:
            location_token = get_location_token(app_access_token, company_id, self.location_id)
            if not location_token:
                _logger.error("Failed to get location access token")
                return {'success': False, 'error': 'Failed to get location access token'}
            url = "https://services.leadconnectorhq.com/contacts/search"
            headers = {
                'Accept': 'application/json',
                'Authorization': f'Bearer {location_token}',
                'Version': '2021-07-28',
            }
            data = {'locationId': self.location_id, 'pageLimit': 1, 'page': 1}
            _logger.info(f"Fetching contacts count for location {self.location_id}")
            response = requests.post(url, headers=headers, json=data, timeout=30)
            if response.status_code == 200:
                result = response.json()
                total_count = result.get('total', 0)
                _logger.info(f"Total contacts count for location {self.location_id}: {total_count}")
                self.write({'contacts_count': total_count})
                return {'success': True, 'total_contacts': total_count}
            else:
                _logger.error(
                    f"Failed to fetch contacts count. Status: {response.status_code}, Response: {response.text}")
                return {'success': False, 'error': f'API request failed with status {response.status_code}'}
        except Exception as e:
            _logger.error(f"Error fetching contacts count for location {self.location_id}: {str(e)}")
            return {'success': False, 'error': str(e)}

    def fetch_location_contacts_lazy(self, company_id, location_id, app_access_token, page=1, limit=10):
        """
        Fetch contacts for a location using lazy loading (10 contacts at a time)
        OPTIMIZED: Returns basic contact data immediately, detailed data fetched separately
        """
        import logging
        import json
        import time
        from datetime import datetime
        from odoo import api, SUPERUSER_ID
        from odoo.modules.registry import Registry
        _logger = logging.getLogger(__name__)

        try:
            # Calculate skip value for pagination
            skip = (page - 1) * limit

            # Use the ghl.location.contact model to fetch contacts from API with pagination
            contact_model = self.env['ghl.location.contact']
            api_result = contact_model.fetch_contacts_from_ghl_api_paginated(
                company_id, location_id, app_access_token, limit=limit, skip=skip
            )

            if not api_result.get('success'):
                _logger.error(f"Failed to fetch contacts from API: {api_result.get('error')}")
                return {
                    'success': False,
                    'error': api_result.get('error', 'Failed to fetch contacts from API'),
                    'created_count': 0,
                    'updated_count': 0,
                    'total_contacts': 0,
                    'page': page,
                    'limit': limit
                }

            contacts_data = api_result.get('contacts_data', [])
            created_count = 0
            updated_count = 0
            max_retries = 3
            retry_delay = 1
            dbname = self.env.cr.dbname

            # OPTIMIZATION: Process contacts with minimal data fetching
            for contact_data in contacts_data:
                for attempt in range(max_retries):
                    try:
                        with Registry(dbname).cursor() as cr:
                            env = api.Environment(cr, SUPERUSER_ID, {})

                            # Extract basic contact data only
                            external_id = contact_data.get('id')
                            email = contact_data.get('email', '')
                            timezone = contact_data.get('timezone', '')
                            country = contact_data.get('country', '')
                            source = contact_data.get('source', '')
                            date_added_str = contact_data.get('dateAdded', '')
                            business_id = contact_data.get('businessId', '')
                            followers = contact_data.get('followers', [])
                            if isinstance(followers, list):
                                followers = json.dumps(followers)
                            else:
                                followers = str(followers)
                            tags = contact_data.get('tags', [])
                            if isinstance(tags, list):
                                tags = json.dumps(tags)
                            else:
                                tags = str(tags)
                            opportunities = contact_data.get('opportunities', [])
                            if isinstance(opportunities, list):
                                opportunities_count = len(opportunities)
                            else:
                                opportunities_count = int(opportunities) if opportunities else 0

                            # AI and analytics fields
                            ai_status = contact_data.get('aiStatus', 'not_contacted')
                            ai_summary = contact_data.get('aiSummary', 'Read')
                            ai_quality_grade = contact_data.get('aiQualityGrade', 'no_grade')
                            ai_sales_grade = contact_data.get('aiSalesGrade', 'no_grade')
                            crm_tasks = contact_data.get('crmTasks', 'no_tasks')
                            category = contact_data.get('category', 'manual')
                            channel = contact_data.get('channel', 'manual')
                            created_by = contact_data.get('createdBy', '')
                            attribution = contact_data.get('attribution', '')
                            assigned_to = contact_data.get('assignedTo', '')
                            speed_to_lead = contact_data.get('speedToLead', '')
                            touch_summary = contact_data.get('touchSummary', 'no_touches')
                            engagement_summary = contact_data.get('engagementSummary', '')
                            last_touch_date_str = contact_data.get('lastTouchDate', '')
                            last_message = contact_data.get('lastMessage', '')
                            total_pipeline_value = contact_data.get('totalPipelineValue', 0.0)

                            # Parse dates
                            date_added = False
                            if date_added_str:
                                try:
                                    date_added = datetime.strptime(date_added_str.replace('Z', ''),
                                                                   '%Y-%m-%dT%H:%M:%S.%f')
                                except:
                                    try:
                                        date_added = datetime.strptime(date_added_str.replace('Z', ''),
                                                                       '%Y-%m-%dT%H:%M:%S')
                                    except:
                                        _logger.warning(f"Could not parse date: {date_added_str}")

                            last_touch_date = False
                            if last_touch_date_str:
                                try:
                                    last_touch_date = datetime.strptime(last_touch_date_str.replace('Z', ''),
                                                                        '%Y-%m-%dT%H:%M:%S.%f')
                                except:
                                    try:
                                        last_touch_date = datetime.strptime(last_touch_date_str.replace('Z', ''),
                                                                            '%Y-%m-%dT%H:%M:%S')
                                    except:
                                        _logger.warning(f"Could not parse last touch date: {last_touch_date_str}")

                            # Process contact names
                            contact_name = contact_data.get('contactName', '')
                            first_name = contact_data.get('firstNameLowerCase', '')
                            last_name = contact_data.get('lastNameLowerCase', '')
                            if contact_name:
                                contact_name = contact_name.title()
                            if first_name:
                                first_name = first_name.title()
                            if last_name:
                                last_name = last_name.title()

                            # Find installed location
                            try:
                                installed_location = env['installed.location'].search([
                                    ('location_id', '=', location_id)
                                ], limit=1)
                                if not installed_location:
                                    _logger.error(f"No installed location found for location_id: {location_id}")
                                    break

                                existing_contact = env['ghl.location.contact'].sudo().search([
                                    ('external_id', '=', external_id),
                                    ('location_id', '=', installed_location.id)
                                ], limit=1)
                            except Exception as cursor_error:
                                if "could not serialize access due to concurrent update" in str(cursor_error):
                                    _logger.warning(
                                        f"Serialization error (search), retrying ({attempt + 1}/{max_retries}): {cursor_error}")
                                    cr.rollback()
                                    time.sleep(retry_delay)
                                    retry_delay *= 2
                                    continue
                                else:
                                    _logger.error(
                                        f"Database cursor error while searching for location/contact: {cursor_error}")
                                    cr.rollback()
                                    break

                            # Prepare contact values (BASIC DATA ONLY)
                            contact_vals = {
                                'external_id': external_id,
                                'location_id': installed_location.id,
                                'contact_name': contact_name,
                                'first_name': first_name,
                                'last_name': last_name,
                                'email': email,
                                'timezone': timezone,
                                'country': country,
                                'source': source,
                                'date_added': date_added,
                                'business_id': business_id,
                                'followers': followers,
                                'tags': tags,
                                'opportunities': opportunities_count,
                                'ai_status': ai_status,
                                'ai_summary': ai_summary,
                                'ai_quality_grade': ai_quality_grade,
                                'ai_sales_grade': ai_sales_grade,
                                'crm_tasks': crm_tasks,
                                'category': category,
                                'channel': channel,
                                'created_by': created_by,
                                'attribution': attribution,
                                'assigned_to': assigned_to,
                                'speed_to_lead': speed_to_lead,
                                'touch_summary': touch_summary,
                                'engagement_summary': engagement_summary,
                                'last_touch_date': last_touch_date,
                                'last_message': last_message,
                                'total_pipeline_value': total_pipeline_value,
                                # OPTIMIZATION: Mark that detailed data needs to be fetched
                                'details_fetched': False,
                            }

                            try:
                                if existing_contact:
                                    existing_contact.write(contact_vals)
                                    updated_count += 1
                                    _logger.info(f"Updated contact record for external_id: {external_id}")
                                else:
                                    env['ghl.location.contact'].sudo().create(contact_vals)
                                    created_count += 1
                                    _logger.info(f"Created contact record for external_id: {external_id}")
                                cr.commit()
                                break  # Success, exit retry loop
                            except Exception as write_error:
                                if "could not serialize access due to concurrent update" in str(write_error):
                                    _logger.warning(
                                        f"Serialization error (write), retrying ({attempt + 1}/{max_retries}): {write_error}")
                                    cr.rollback()
                                    time.sleep(retry_delay)
                                    retry_delay *= 2
                                    continue
                                else:
                                    _logger.error(f"Database error while writing contact: {write_error}")
                                    cr.rollback()
                                    break
                    except Exception as contact_error:
                        if "could not serialize access due to concurrent update" in str(contact_error):
                            _logger.warning(
                                f"Serialization error (outer), retrying ({attempt + 1}/{max_retries}): {contact_error}")
                            time.sleep(retry_delay)
                            retry_delay *= 2
                            continue
                        else:
                            _logger.error(f"Error processing contact data: {contact_error}")
                            break

            return {
                'success': True,
                'created_count': created_count,
                'updated_count': updated_count,
                'total_contacts': api_result.get('total_contacts', 0),
                'page': page,
                'limit': limit,
                'has_more': api_result.get('has_more', False)
            }

        except Exception as e:
            _logger.error(f"Error in fetch_location_contacts_lazy: {str(e)}")
            import traceback
            _logger.error(f"Full traceback: {traceback.format_exc()}")
            return {
                'success': False,
                'error': str(e),
                'created_count': 0,
                'updated_count': 0,
                'total_contacts': 0,
                'page': page,
                'limit': limit
            }

    def fetch_location_contacts(self, company_id, location_id, app_access_token):
        """
        Fetch contacts for a location using the GHL API and create/update contact records.
        This method now uses the ghl.location.contact model to fetch API data.
        IMPLEMENTATION: Only fetch first 2-3 pages (200-300 contacts) for lazy loading.
        """
        import logging
        import json
        from datetime import datetime
        _logger = logging.getLogger(__name__)

        try:
            # Use the ghl.location.contact model to fetch contacts from API with LIMITED pagination
            # Only fetch first 2-3 pages (200-300 contacts) for lazy loading
            contact_model = self.env['ghl.location.contact']
            api_result = contact_model.fetch_contacts_from_ghl_api(company_id, location_id, app_access_token,
                                                                   max_pages=3)

            if not api_result.get('success'):
                _logger.error(f"Failed to fetch contacts from API: {api_result.get('error')}")
                return {
                    'success': False,
                    'error': api_result.get('error', 'Failed to fetch contacts from API'),
                    'created_count': 0,
                    'updated_count': 0,
                    'total_contacts': 0
                }

            # Step 3: Process and create/update contact records
            contacts_data = api_result.get('contacts_data', [])
            created_count = 0
            updated_count = 0

            for contact_data in contacts_data:
                try:
                    # Extract contact data
                    external_id = contact_data.get('id')
                    email = contact_data.get('email', '')
                    timezone = contact_data.get('timezone', '')
                    country = contact_data.get('country', '')
                    source = contact_data.get('source', '')
                    date_added_str = contact_data.get('dateAdded', '')
                    business_id = contact_data.get('businessId', '')
                    followers = contact_data.get('followers', [])
                    if isinstance(followers, list):
                        followers = json.dumps(followers)
                    else:
                        followers = str(followers)

                    tags = contact_data.get('tags', [])
                    if isinstance(tags, list):
                        tags = json.dumps(tags)
                    else:
                        tags = str(tags)

                    opportunities = contact_data.get('opportunities', [])
                    if isinstance(opportunities, list):
                        opportunities_count = len(opportunities)
                    else:
                        opportunities_count = int(opportunities) if opportunities else 0

                    # Extract additional fields for frontend table
                    # AI and analytics fields (these might come from custom fields or other sources)
                    ai_status = contact_data.get('aiStatus', 'not_contacted')
                    ai_summary = contact_data.get('aiSummary', 'Read')
                    ai_quality_grade = contact_data.get('aiQualityGrade', 'no_grade')
                    ai_sales_grade = contact_data.get('aiSalesGrade', 'no_grade')
                    crm_tasks = contact_data.get('crmTasks', 'no_tasks')
                    category = contact_data.get('category', 'manual')
                    channel = contact_data.get('channel', 'manual')
                    created_by = contact_data.get('createdBy', '')
                    attribution = contact_data.get('attribution', '')
                    assigned_to = contact_data.get('assignedTo', '')
                    speed_to_lead = contact_data.get('speedToLead', '')
                    touch_summary = contact_data.get('touchSummary', 'no_touches')
                    engagement_summary = contact_data.get('engagementSummary', '')
                    last_touch_date_str = contact_data.get('lastTouchDate', '')
                    last_message = contact_data.get('lastMessage', '')
                    total_pipeline_value = contact_data.get('totalPipelineValue', 0.0)
                    opportunities = contact_data.get('opportunities', 0)

                    # Parse date
                    date_added = False
                    if date_added_str:
                        try:
                            date_added = datetime.strptime(date_added_str.replace('Z', ''), '%Y-%m-%dT%H:%M:%S.%f')
                        except:
                            try:
                                date_added = datetime.strptime(date_added_str.replace('Z', ''), '%Y-%m-%dT%H:%M:%S')
                            except:
                                _logger.warning(f"Could not parse date: {date_added_str}")

                    # Check if contact already exists
                    # First find the installed location record
                    try:
                        installed_location = self.env['installed.location'].search([
                            ('location_id', '=', location_id)
                        ], limit=1)

                        if not installed_location:
                            _logger.error(f"No installed location found for location_id: {location_id}")
                            continue

                        existing_contact = self.env['ghl.location.contact'].sudo().search([
                            ('external_id', '=', external_id),
                            ('location_id', '=', installed_location.id)
                        ], limit=1)
                    except Exception as cursor_error:
                        _logger.error(f"Database cursor error while searching for location/contact: {cursor_error}")
                        # Try to continue with the next contact
                        continue

                    # Parse last touch date
                    last_touch_date = False
                    if last_touch_date_str:
                        try:
                            last_touch_date = datetime.strptime(last_touch_date_str.replace('Z', ''),
                                                                '%Y-%m-%dT%H:%M:%S.%f')
                        except:
                            try:
                                last_touch_date = datetime.strptime(last_touch_date_str.replace('Z', ''),
                                                                    '%Y-%m-%dT%H:%M:%S')
                            except:
                                _logger.warning(f"Could not parse last touch date: {last_touch_date_str}")

                    # Prepare contact values
                    contact_name = contact_data.get('contactName', '')
                    first_name = contact_data.get('firstName', '')
                    last_name = contact_data.get('lastName', '')
                    # Proper-case names
                    if contact_name:
                        contact_name = contact_name.title()
                    if first_name:
                        first_name = first_name.title()
                    if last_name:
                        last_name = last_name.title()
                    contact_vals = {
                        'external_id': external_id,
                        'location_id': installed_location.id,
                        'contact_name': contact_name,
                        'first_name': first_name,
                        'last_name': last_name,
                        'email': email,
                        'timezone': timezone,
                        'country': country,
                        'source': source,
                        'date_added': date_added,
                        'business_id': business_id,
                        'followers': followers,
                        'tags': tags,
                        'opportunities': opportunities_count,
                        # AI and analytics fields
                        'ai_status': ai_status,
                        'ai_summary': ai_summary,
                        'ai_quality_grade': ai_quality_grade,
                        'ai_sales_grade': ai_sales_grade,
                        'crm_tasks': crm_tasks,
                        'category': category,
                        'channel': channel,
                        'created_by': created_by,
                        'attribution': attribution,
                        'assigned_to': assigned_to,
                        'speed_to_lead': speed_to_lead,
                        'touch_summary': touch_summary,
                        'engagement_summary': engagement_summary,
                        'last_touch_date': last_touch_date,
                        'last_message': last_message,
                        'total_pipeline_value': total_pipeline_value,
                        'details_fetched': False,
                    }

                    # Handle custom fields
                    custom_fields_data = contact_data.get('customFields', [])
                    if custom_fields_data:
                        try:
                            # Delete existing custom fields if updating
                            if existing_contact:
                                existing_contact.custom_field_ids.unlink()

                            # Create new custom fields
                            for cf_data in custom_fields_data:
                                if isinstance(cf_data, dict):
                                    # Ensure the contact exists before creating the custom field
                                    contact_check = self.env['ghl.location.contact'].sudo().search([
                                        ('external_id', '=', external_id),
                                        ('location_id', '=', installed_location.id)
                                    ], limit=1)
                                    if contact_check:
                                        try:
                                            self.env['ghl.location.contact.custom.field'].sudo().create({
                                                'contact_id': contact_check.id,
                                                'custom_field_id': cf_data.get('custom_field_id'),
                                                'value': cf_data.get('value'),
                                            })
                                        except Exception as cf_create_error:
                                            _logger.error(
                                                f"Error creating custom field for contact {external_id}: {cf_create_error}")
                                    else:
                                        _logger.error(
                                            f"Cannot create custom field: contact {external_id} does not exist (skipping custom field creation)")
                        except Exception as cf_error:
                            _logger.error(f"Error processing custom fields for contact {external_id}: {cf_error}")

                    # Handle attributions
                    attributions_data = contact_data.get('attributions', [])
                    if attributions_data:
                        try:
                            # Delete existing attributions if updating
                            if existing_contact:
                                existing_contact.attribution_ids.unlink()

                            # Create new attributions
                            for attr_data in attributions_data:
                                # Ensure attr_data is a dictionary
                                if not isinstance(attr_data, dict):
                                    _logger.warning(f"Skipping invalid attribution data (not a dict): {attr_data}")
                                    continue

                                attr_vals = {
                                    'contact_id': existing_contact.id if existing_contact else False,
                                    'url': attr_data.get('url', ''),
                                    'campaign': attr_data.get('campaign', ''),
                                    'utm_source': attr_data.get('utmSource', ''),
                                    'utm_medium': attr_data.get('utmMedium', ''),
                                    'utm_content': attr_data.get('utmContent', ''),
                                    'referrer': attr_data.get('referrer', ''),
                                    'campaign_id': attr_data.get('campaignId', ''),
                                    'fbclid': attr_data.get('fbclid', ''),
                                    'gclid': attr_data.get('gclid', ''),
                                    'msclikid': attr_data.get('msclikid', ''),
                                    'dclid': attr_data.get('dclid', ''),
                                    'fbc': attr_data.get('fbc', ''),
                                    'fbp': attr_data.get('fbp', ''),
                                    'fb_event_id': attr_data.get('fbEventId', ''),
                                    'user_agent': attr_data.get('userAgent', ''),
                                    'ip': attr_data.get('ip', ''),
                                    'medium': attr_data.get('medium', ''),
                                    'medium_id': attr_data.get('mediumId', ''),
                                }
                                self.env['ghl.location.contact.attribution'].sudo().create(attr_vals)
                        except Exception as attr_error:
                            _logger.error(f"Error processing attributions for contact {external_id}: {attr_error}")

                    # Create or update contact record
                    try:
                        if existing_contact:
                            existing_contact.write(contact_vals)
                            # Update custom fields and attributions with the correct contact_id
                            if custom_fields_data:
                                existing_contact.custom_field_ids.write({'contact_id': existing_contact.id})
                            if attributions_data:
                                existing_contact.attribution_ids.write({'contact_id': existing_contact.id})
                            updated_count += 1
                            _logger.info(f"Updated contact record for external_id: {external_id}")
                        else:
                            new_contact = self.env['ghl.location.contact'].sudo().create(contact_vals)
                            # Update custom fields and attributions with the correct contact_id
                            if custom_fields_data:
                                new_contact.custom_field_ids.write({'contact_id': new_contact.id})
                            if attributions_data:
                                new_contact.attribution_ids.write({'contact_id': new_contact.id})
                            created_count += 1
                            _logger.info(f"Created contact record for external_id: {external_id}")
                    except Exception as db_error:
                        print(contact_vals)
                        _logger.error(f"Database error while creating/updating contact {external_id}: {db_error}")
                        # Continue with next contact instead of failing completely
                        continue

                    # After creating/updating the contact, sync their opportunities in the background
                    if external_id:
                        try:
                            threading.Thread(
                                target=self._background_sync_opps_for_contacts,
                                args=(location_id, [external_id], app_access_token, company_id),
                                daemon=True
                            ).start()
                        except Exception as opp_sync_error:
                            _logger.error(
                                f"Error starting background thread for opportunities sync for contact {external_id}: {opp_sync_error}")

                except Exception as e:
                    _logger.error(f"Error processing contact {contact_data.get('id', 'unknown')}: {e}")
                    import traceback
                    _logger.error(f"Full traceback: {traceback.format_exc()}")
                    continue

            _logger.info(
                f"Contact sync completed for location {location_id}: {created_count} created, {updated_count} updated")
            return {
                'success': True,
                'created_count': created_count,
                'updated_count': updated_count,
                'total_contacts': len(contacts_data)
            }
        except Exception as e:
            _logger.error(f"Error fetching location contacts: {e}")
            return {
                'success': False,
                'error': f"Error fetching location contacts: {e}",
                'created_count': 0,
                'updated_count': 0,
                'total_contacts': 0
            }

    def _background_sync_opps_for_contacts(self, location_id, contact_external_ids, app_access_token, company_id):
        opportunity_model = self.env['ghl.contact.opportunity'].sudo()
        for contact_id in contact_external_ids:
            try:
                opportunity_model.sync_opportunities_for_contact(
                    app_access_token, location_id, contact_id, company_id
                )
            except Exception as e:
                _logger.error(f"Error syncing opportunities for contact {contact_id}: {e}")

    def sync_contact_details_background(self, company_id, location_id, app_access_token):
        """
        Background sync method to fetch detailed contact data (tasks, conversations) for contacts
        that don't have details_fetched=True
        """
        import logging
        _logger = logging.getLogger(__name__)

        try:
            # Find contacts that need detailed data
            contacts_needing_details = self.env['ghl.location.contact'].sudo().search([
                ('location_id.location_id', '=', location_id),
                ('details_fetched', '=', False)
            ], limit=50)  # Process in batches

            if not contacts_needing_details:
                _logger.info(f"No contacts need detailed data for location {location_id}")
                return {
                    'success': True,
                    'message': 'No contacts need detailed data',
                    'processed': 0
                }

            _logger.info(
                f"Syncing detailed data for {len(contacts_needing_details)} contacts in location {location_id}")

            # Get location token
            from .ghl_api_utils import get_location_token
            location_token = get_location_token(app_access_token, company_id, location_id)
            if not location_token:
                return {
                    'success': False,
                    'error': 'Failed to get location access token'
                }

            processed_count = 0

            for contact in contacts_needing_details:
                try:
                    # Sync tasks for this contact
                    task_result = self.env['ghl.contact.task'].sudo().sync_contact_tasks_from_ghl(
                        contact.id, location_token, contact.location_id.location_id, 'Ipg8nKDPLYKsbtodR6LN'
                    )

                    # Sync conversations for this contact
                    conversation_result = self.env['ghl.contact.conversation'].sudo().sync_conversations_for_contact(
                        location_token, contact.external_id, contact.id
                    )

                    # Mark contact as having details fetched
                    contact.write({'details_fetched': True})
                    processed_count += 1

                    _logger.info(
                        f"Synced details for contact {contact.external_id}: tasks={task_result.get('success', False)}, conversations={conversation_result.get('success', False)}")

                except Exception as e:
                    _logger.error(f"Error syncing details for contact {contact.external_id}: {str(e)}")
                    continue

            return {
                'success': True,
                'message': f'Processed {processed_count} contacts',
                'processed': processed_count
            }

        except Exception as e:
            _logger.error(f"Error in sync_contact_details_background: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    def fetch_location_token(self, agency_token, company_id):
        """
        Fetch a location access token from GHL using the agency token, companyId, and locationId.
        Returns the access_token string, or None if not found.
        """
        import requests
        _logger = logging.getLogger(__name__)
        url = 'https://services.leadconnectorhq.com/oauth/locationToken'
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Version': '2021-07-28',
            'Authorization': f'Bearer {agency_token}',
        }
        data = {
            'companyId': company_id,
            'locationId': self.location_id,
        }
        try:
            resp = requests.post(url, headers=headers, data=data)
            _logger.info(f"[CyclSalesApplication] fetch_location_token response: {resp.status_code} {resp.text}")
            if resp.status_code not in [200, 201]:
                _logger.error(f"Failed to fetch location token: {resp.text}")
                return None
            token_data = resp.json()
            return token_data.get('access_token')
        except Exception as e:
            _logger.error(f"Error fetching location token: {e}")
            return None
