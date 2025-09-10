from odoo import models, fields, api
import requests
import logging

_logger = logging.getLogger(__name__)


class GHLLocationUserPermissions(models.Model):
    _name = 'ghl.location.user.permissions'
    _description = 'GHL Location User Permissions'

    campaigns_enabled = fields.Boolean()
    campaigns_read_only = fields.Boolean()
    contacts_enabled = fields.Boolean()
    workflows_enabled = fields.Boolean()
    workflows_read_only = fields.Boolean()
    triggers_enabled = fields.Boolean()
    funnels_enabled = fields.Boolean()
    websites_enabled = fields.Boolean()
    opportunities_enabled = fields.Boolean()
    dashboard_stats_enabled = fields.Boolean()
    bulk_requests_enabled = fields.Boolean()
    appointments_enabled = fields.Boolean()
    reviews_enabled = fields.Boolean()
    online_listings_enabled = fields.Boolean()
    phone_call_enabled = fields.Boolean()
    conversations_enabled = fields.Boolean()
    assigned_data_only = fields.Boolean()
    adwords_reporting_enabled = fields.Boolean()
    membership_enabled = fields.Boolean()
    facebook_ads_reporting_enabled = fields.Boolean()
    attributions_reporting_enabled = fields.Boolean()
    settings_enabled = fields.Boolean()
    tags_enabled = fields.Boolean()
    lead_value_enabled = fields.Boolean()
    marketing_enabled = fields.Boolean()
    agent_reporting_enabled = fields.Boolean()
    bot_service = fields.Boolean()
    social_planner = fields.Boolean()
    blogging_enabled = fields.Boolean()
    invoice_enabled = fields.Boolean()
    affiliate_manager_enabled = fields.Boolean()
    content_ai_enabled = fields.Boolean()
    refunds_enabled = fields.Boolean()
    record_payment_enabled = fields.Boolean()
    cancel_subscription_enabled = fields.Boolean()
    payments_enabled = fields.Boolean()
    communities_enabled = fields.Boolean()
    export_payments_enabled = fields.Boolean()


class GHLLocationUserRoles(models.Model):
    _name = 'ghl.location.user.roles'
    _description = 'GHL Location User Roles'

    type = fields.Char()
    role = fields.Char()
    restrict_sub_account = fields.Boolean()
    location_ids = fields.Many2many('installed.location', string='Locations')


class GHLLocationUserLCPhone(models.Model):
    _name = 'ghl.location.user.lcphone'
    _description = 'GHL Location User LC Phone'

    location_id = fields.Char()


class GHLLocationUser(models.Model):
    _name = 'ghl.location.user'
    _description = 'GHL Location User'

    external_id = fields.Char(string='External ID')
    location_id = fields.Char(string='Location ID', required=True, index=True)
    name = fields.Char()
    first_name = fields.Char()
    last_name = fields.Char()
    email = fields.Char()
    phone = fields.Char()
    extension = fields.Char()
    permissions_id = fields.Many2one('ghl.location.user.permissions', string='Permissions')
    scopes = fields.Char()
    roles_id = fields.Many2one('ghl.location.user.roles', string='Roles')
    deleted = fields.Boolean()
    lc_phone_id = fields.Many2one('ghl.location.user.lcphone', string='LC Phone')
    profile_photo = fields.Char(string='Profile Photo URL')
    membership_contact_id = fields.Char(string='Membership Contact ID')
    freshdesk_contact_id = fields.Char(string='Freshdesk Contact ID')
    totp_enabled = fields.Boolean(string='TOTP Enabled')

    @api.model
    def fetch_user_by_id(self, user_id, location_id, company_id, app_access_token):
        """
        Fetch a specific user by ID using the GHL API and create/update user record.
        
        Args:
            user_id (str): The user ID to fetch
            location_id (str): The location ID
            company_id (str): The company ID
            app_access_token (str): The app access token
            
        Returns:
            dict: Result with success status and operation details
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
            if token_resp.status_code not in (200, 201):
                _logger.error(f"Failed to get location token: {token_resp.text}")
                return {
                    'success': False,
                    'error': f"Failed to get location token: {token_resp.text}"
                }

            token_json = token_resp.json()
            location_token = token_json.get('access_token')
            if not location_token:
                _logger.error(f"No access_token in location token response: {token_json}")
                return {
                    'success': False,
                    'error': f"No access_token in location token response: {token_json}"
                }

            # Step 2: Fetch specific user
            user_url = f"https://services.leadconnectorhq.com/users/{user_id}"
            user_headers = {
                'Accept': 'application/json',
                'Authorization': f'Bearer {location_token}',
                'Version': '2021-07-28',
            }
            user_resp = requests.get(user_url, headers=user_headers)

            if user_resp.status_code == 200:
                user_data = user_resp.json()

                # Step 3: Process and create/update user record
                try:
                    # Extract user data
                    external_id = user_data.get('id')
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
                        operation = 'updated'
                    else:
                        self.env['ghl.location.user'].sudo().create(user_vals)
                        operation = 'created'

                    return {
                        'success': True,
                        'operation': operation,
                        'external_id': external_id,
                        'user_data': user_data
                    }

                except Exception as e:
                    _logger.error(f"Error processing user {user_id}: {e}")
                    return {
                        'success': False,
                        'error': f"Error processing user {user_id}: {e}"
                    }
            else:
                _logger.error(f"Failed to fetch user: {user_resp.text}")
                return {
                    'success': False,
                    'error': f"Failed to fetch user: {user_resp.text}"
                }
        except Exception as e:
            _logger.error(f"Error fetching user {user_id}: {e}")
            return {
                'success': False,
                'error': f"Error fetching user {user_id}: {e}"
            }
