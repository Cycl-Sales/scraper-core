from odoo import http
from odoo.http import request
import json
import logging

_logger = logging.getLogger(__name__)

class ZillowPropertyAPI(http.Controller):
    @http.route('/api/zillow/property/<string:zpid>', type='http', auth='public', cors='*')
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
                    response['listingAgent'] = {
                        'id': agent.id,
                        'property_id': agent.property_id.id,
                        'name': agent.display_name or '',
                        'business_name': agent.business_name or '',
                        'phone': f"{agent.phone_area_code or ''}-{agent.phone_prefix or ''}-{agent.phone_number or ''}",
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
            return http.Response(json.dumps(response), content_type='application/json')
        except Exception as e:
            _logger.error(f"Error in get_property_detail for zpid={zpid}: {str(e)}", exc_info=True)
            response = {'success': False, 'error': f'Internal server error: {str(e)}'}
            return http.Response(json.dumps(response), content_type='application/json', status=500) 