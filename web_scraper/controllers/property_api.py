from odoo import http
from odoo.http import request, Response
import json
import logging
from .cors_utils import get_cors_headers
import requests

_logger = logging.getLogger(__name__)


class ZillowPropertyAPI(http.Controller):
    @http.route('/api/zillow/property/<string:zpid>', type='http', auth='none')
    def get_property_detail(self, zpid):
        try:
            detail = request.env['zillow.property.detail'].sudo().search([('zpid', '=', zpid)], limit=1)
            if not detail:
                response = {'success': False, 'error': 'Property detail not found'}
            else:
                property_obj = detail.property_id
                images = []
                if detail.hi_res_image_link:
                    images.append(detail.hi_res_image_link)
                if getattr(detail, 'desktop_web_hdp_image_link', None):
                    images.append(detail.desktop_web_hdp_image_link)
                images += [photo.url for photo in getattr(detail, 'mini_card_photo_ids', [])]
                tax_history = []
                for tax in getattr(detail, 'tax_history_ids', []):
                    tax_history.append({
                        'year': tax.time.year if tax.time else None,
                        'tax_paid': tax.tax_paid,
                        'value': tax.value,
                    })
                response = {
                    'success': True,
                    'zpid': detail.zpid,
                    'address': property_obj.street_address,
                    'city': property_obj.city,
                    'state': property_obj.state,
                    'zipcode': property_obj.zipcode,
                    'price': property_obj.price,
                    'beds': property_obj.bedrooms,
                    'baths': property_obj.bathrooms,
                    'living_area': property_obj.living_area,
                    'year_built': detail.year_built,
                    'lot_area_value': detail.lot_area_value,
                    'lot_area_units': detail.lot_area_units,
                    'home_type': property_obj.home_type.replace('_', ' ').title() if property_obj.home_type else '',
                    'home_status': property_obj.home_status,
                    'description': detail.description or '',
                    'images': images,
                    'tax_history': tax_history,
                    'hdp_url': detail.hdp_url or '',
                    'hi_res_image_link': detail.hi_res_image_link or '',
                    'latitude': detail.latitude,
                    'longitude': detail.longitude,
                    'provider_listing_id': detail.provider_listing_id or '',
                    'country': detail.country or '',
                    'county': detail.county or '',
                    'days_on_zillow': detail.days_on_zillow,
                    'parent_region_name': detail.parent_region_name or '',
                    'neighborhood_region_name': detail.neighborhood_region_name or '',
                    'virtual_tour_url': detail.virtual_tour_url or '',
                    'zestimate': detail.zestimate,
                    'listingAgent': None,
                }
                if detail.listing_agent_id:
                    agent = detail.listing_agent_id
                    agent_name = agent.member_full_name
                    if not agent_name:
                        agent_name = detail.agent_name
                    response['listingAgent'] = {
                        'id': agent.id,
                        'property_id': agent.property_id.id,
                        'name': agent_name or '',
                        'business_name': agent.business_name or '',
                        'phone': detail.agent_phone_number,
                        'profile_url': agent.profile_url or '',
                        'email': agent.email or '',
                        'license_number': agent.license_number or '',
                        'license_state': agent.license_state or '',
                        'badge_type': agent.badge_type or '',
                        'encoded_zuid': agent.encoded_zuid or '',
                        'first_name': agent.first_name or '',
                        'image_url': agent.image_url or '',
                        'image_height': agent.image_height,
                        'image_width': agent.image_width,
                        'rating_average': agent.rating_average,
                        'recent_sales': agent.recent_sales,
                        'review_count': agent.review_count,
                        'reviews_url': agent.reviews_url or '',
                        'services_offered': agent.services_offered or '',
                        'username': agent.username or '',
                        'write_review_url': agent.write_review_url or '',
                        'is_zpro': agent.is_zpro,
                    }
                print(response)
            return http.Response(json.dumps(response), content_type='application/json',
                                 headers=get_cors_headers(request))
        except Exception as e:
            _logger.error(f"Error in get_property_detail for zpid={zpid}: {str(e)}", exc_info=True)
            response = {'success': False, 'error': f'Internal server error: {str(e)}'}
            return http.Response(json.dumps(response), content_type='application/json', status=500,
                                 headers=get_cors_headers(request))


class ContactDetailsAPI(http.Controller):
    @http.route('/api/contact-details', type='json', auth='user', methods=['POST'], csrf=False)
    def get_contact_details(self, **kwargs):
        contact_id = kwargs.get('contact_id')
        if not contact_id:
            return {'success': False, 'error': 'contact_id is required'}
        
        try:
            contact = request.env['ghl.location.contact'].sudo().browse(int(contact_id))
            if not contact:
                return {'success': False, 'error': 'Contact not found'}
            
            if contact.details_fetched:
                # Already fetched, return details with related data
                contact_data = contact.read()[0]
                contact_data['tasks'] = contact.task_ids.read()
                contact_data['conversations'] = contact.conversation_ids.read()
                contact_data['opportunities'] = contact.opportunity_ids.read()
                return {'success': True, 'contact': contact_data}
            
            # Get the access token from the associated application
            app = request.env['cyclsales.application'].sudo().search([
                ('app_id', '=', contact.location_id.app_id),
                ('is_active', '=', True)
            ], limit=1)
            
            if not app or not app.access_token:
                return {'success': False, 'error': 'No valid access token found'}
            
            # Fetch details from GHL API
            success = self._fetch_contact_details_from_ghl(contact, app.access_token)
            
            if success:
                contact.details_fetched = True
                # Return details with related data
                contact_data = contact.read()[0]
                contact_data['tasks'] = contact.task_ids.read()
                contact_data['conversations'] = contact.conversation_ids.read()
                contact_data['opportunities'] = contact.opportunity_ids.read()
                return {'success': True, 'contact': contact_data}
            else:
                return {'success': False, 'error': 'Failed to fetch contact details from GHL API'}
                
        except Exception as e:
            _logger.error(f"Error fetching contact details: {str(e)}", exc_info=True)
            return {'success': False, 'error': f'Internal server error: {str(e)}'}

    @http.route('/api/load-more-contacts', type='json', auth='user', methods=['POST'], csrf=False)
    def load_more_contacts(self, **kwargs):
        """Load additional contacts from database with pagination"""
        location_id = kwargs.get('location_id')
        page = kwargs.get('page', 1)
        page_size = kwargs.get('page_size', 100)
        
        if not location_id:
            return {'success': False, 'error': 'location_id is required'}
        
        try:
            # Find the installed location
            installed_location = request.env['installed.location'].sudo().search([
                ('location_id', '=', location_id)
            ], limit=1)
            
            if not installed_location:
                return {'success': False, 'error': 'Location not found'}
            
            # Calculate offset for pagination
            offset = (page - 1) * page_size
            
            # Fetch contacts from database with pagination
            contacts = request.env['ghl.location.contact'].sudo().search([
                ('location_id', '=', installed_location.id)
            ], limit=page_size, offset=offset, order='date_added desc')
            
            # Convert to list of dictionaries for JSON response
            contacts_data = []
            for contact in contacts:
                contact_dict = contact.read()[0]
                # Add computed fields that might not be in read()
                contact_dict['name'] = contact.name
                contact_dict['tag_list'] = contact.tag_list
                contact_dict['assigned_user_name'] = contact.assigned_user_name
                contacts_data.append(contact_dict)
            
            # Check if there are more contacts
            total_contacts = request.env['ghl.location.contact'].sudo().search_count([
                ('location_id', '=', installed_location.id)
            ])
            
            has_more = (offset + page_size) < total_contacts
            
            return {
                'success': True,
                'contacts': contacts_data,
                'page': page,
                'page_size': page_size,
                'total_contacts': total_contacts,
                'has_more': has_more,
                'offset': offset
            }
            
        except Exception as e:
            _logger.error(f"Error loading more contacts: {str(e)}", exc_info=True)
            return {'success': False, 'error': f'Internal server error: {str(e)}'}

    def _process_contact_data(self, contact_data, installed_location):
        """Process a single contact data and create/update the record"""
        try:
            import json
            from datetime import datetime
            
            external_id = contact_data.get('id')
            
            # Check if contact already exists
            existing_contact = request.env['ghl.location.contact'].sudo().search([
                ('external_id', '=', external_id),
                ('location_id', '=', installed_location.id)
            ], limit=1)
            
            if existing_contact:
                return False  # Already exists, skip
            
            # Extract and process contact data (same logic as in fetch_location_contacts)
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

            # Parse date
            date_added = False
            if date_added_str:
                try:
                    date_added = datetime.strptime(date_added_str.replace('Z', ''), '%Y-%m-%dT%H:%M:%S.%f')
                except:
                    try:
                        date_added = datetime.strptime(date_added_str.replace('Z', ''), '%Y-%m-%dT%H:%M:%S')
                    except:
                        pass

            # Prepare contact values
            contact_name = contact_data.get('contactName', '')
            first_name = contact_data.get('firstName', '')
            last_name = contact_data.get('lastName', '')
            
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
                'details_fetched': False,
            }
            
            # Create the contact
            request.env['ghl.location.contact'].sudo().create(contact_vals)
            return True
            
        except Exception as e:
            _logger.error(f"Error processing contact data: {str(e)}")
            return False

    def _fetch_contact_details_from_ghl(self, contact, access_token):
        """Fetch tasks, conversations, and opportunities for a contact from GHL API"""
        try:
            # Fetch tasks
            self._fetch_contact_tasks(contact, access_token)
            
            # Fetch conversations
            self._fetch_contact_conversations(contact, access_token)
            
            # Fetch opportunities
            self._fetch_contact_opportunities(contact, access_token)
            
            return True
            
        except Exception as e:
            _logger.error(f"Error fetching contact details from GHL: {str(e)}", exc_info=True)
            return False
    
    def _fetch_contact_tasks(self, contact, access_token):
        """Fetch tasks for a contact from GHL API"""
        try:
            url = f"https://services.leadconnectorhq.com/contacts/{contact.external_id}/tasks"
            headers = {
                'Accept': 'application/json',
                'Authorization': f'Bearer {access_token}',
                'Version': '2021-07-28',
            }
            
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                tasks_data = response.json().get('tasks', [])
                
                for task_data in tasks_data:
                    # Check if task already exists
                    existing_task = request.env['ghl.contact.task'].sudo().search([
                        ('external_id', '=', task_data.get('id')),
                        ('contact_id', '=', contact.id)
                    ], limit=1)
                    
                    if not existing_task:
                        # Create new task
                        task_vals = {
                            'contact_id': contact.id,
                            'external_id': task_data.get('id'),
                            'title': task_data.get('title'),
                            'description': task_data.get('description'),
                            'status': task_data.get('status'),
                            'priority': task_data.get('priority'),
                            'due_date': task_data.get('dueDate'),
                            'assigned_to': task_data.get('assignedTo'),
                            'created_by': task_data.get('createdBy'),
                            'date_created': task_data.get('dateCreated'),
                            'date_modified': task_data.get('dateModified'),
                        }
                        request.env['ghl.contact.task'].sudo().create(task_vals)
                        
        except Exception as e:
            _logger.error(f"Error fetching tasks for contact {contact.external_id}: {str(e)}")
    
    def _fetch_contact_conversations(self, contact, access_token):
        """Fetch conversations for a contact from GHL API"""
        try:
            url = f"https://services.leadconnectorhq.com/contacts/{contact.external_id}/conversations"
            headers = {
                'Accept': 'application/json',
                'Authorization': f'Bearer {access_token}',
                'Version': '2021-07-28',
            }
            
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                conversations_data = response.json().get('conversations', [])
                
                for conv_data in conversations_data:
                    # Check if conversation already exists
                    existing_conv = request.env['ghl.contact.conversation'].sudo().search([
                        ('ghl_id', '=', conv_data.get('id')),
                        ('contact_id', '=', contact.id)
                    ], limit=1)
                    
                    if not existing_conv:
                        # Create new conversation
                        conv_vals = {
                            'contact_id': contact.id,
                            'ghl_id': conv_data.get('id'),
                            'location_id': contact.location_id.id,
                            'channel': conv_data.get('channel'),
                            'status': conv_data.get('status'),
                            'subject': conv_data.get('subject'),
                            'last_message': conv_data.get('lastMessage'),
                            'date_created': conv_data.get('dateCreated'),
                            'date_modified': conv_data.get('dateModified'),
                        }
                        request.env['ghl.contact.conversation'].sudo().create(conv_vals)
                        
        except Exception as e:
            _logger.error(f"Error fetching conversations for contact {contact.external_id}: {str(e)}")
    
    def _fetch_contact_opportunities(self, contact, access_token):
        """Fetch opportunities for a contact from GHL API"""
        try:
            url = f"https://services.leadconnectorhq.com/contacts/{contact.external_id}/opportunities"
            headers = {
                'Accept': 'application/json',
                'Authorization': f'Bearer {access_token}',
                'Version': '2021-07-28',
            }
            
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                opportunities_data = response.json().get('opportunities', [])
                
                for opp_data in opportunities_data:
                    # Check if opportunity already exists
                    existing_opp = request.env['ghl.contact.opportunity'].sudo().search([
                        ('external_id', '=', opp_data.get('id')),
                        ('contact_id', '=', contact.id)
                    ], limit=1)
                    
                    if not existing_opp:
                        # Create new opportunity
                        opp_vals = {
                            'contact_id': contact.id,
                            'external_id': opp_data.get('id'),
                            'name': opp_data.get('title'),
                            'location_id': contact.location_id.id,
                            'description': opp_data.get('description'),
                            'status': opp_data.get('status'),
                            'stage': opp_data.get('stage'),
                            'monetary_value': opp_data.get('monetaryValue'),
                            'assigned_to_external': opp_data.get('assignedTo'),
                            'date_created': opp_data.get('dateCreated'),
                            'date_modified': opp_data.get('dateModified'),
                            'expected_close_date': opp_data.get('expectedCloseDate'),
                        }
                        request.env['ghl.contact.opportunity'].sudo().create(opp_vals)
                        
        except Exception as e:
            _logger.error(f"Error fetching opportunities for contact {contact.external_id}: {str(e)}")
