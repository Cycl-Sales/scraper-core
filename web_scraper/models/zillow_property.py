from odoo import models, fields, api
import requests
import logging
import json
from datetime import datetime, timedelta
from odoo.fields import Datetime, Date

_logger = logging.getLogger(__name__)


def ms_to_odoo_date(ms):
    return Date.to_string(datetime.utcfromtimestamp(ms / 1000))


def ms_to_odoo_datetime(ms):
    return Datetime.to_string(datetime.utcfromtimestamp(ms / 1000))


class ZillowProperty(models.Model):
    _name = 'zillow.property'
    _description = 'Zillow Property'
    _rec_name = 'street_address'

    # Basic Information
    street_address = fields.Char(string='Street Address')
    city = fields.Char(string='City')
    state = fields.Char(string='State')
    zipcode = fields.Char(string='Zipcode')
    country = fields.Char(string='Country', default='USA')
    unit = fields.Char(string='Unit')

    # Property Details
    bedrooms = fields.Integer(string='Bedrooms')
    bathrooms = fields.Float(string='Bathrooms')
    living_area = fields.Float(string='Living Area (sqft)')
    lot_area_value = fields.Float(string='Lot Area Value')
    lot_area_unit = fields.Selection([
        ('sqft', 'Square Feet'),
        ('acres', 'Acres')
    ], string='Lot Area Unit')

    # Price Information
    price = fields.Float(string='Price')
    currency = fields.Char(string='Currency', default='USD')
    zestimate = fields.Float(string='Zestimate')
    rent_zestimate = fields.Float(string='Rent Zestimate')
    tax_assessed_value = fields.Float(string='Tax Assessed Value')

    # Status Information
    home_status = fields.Char(string='Home Status')
    home_type = fields.Char(string='Home Type')

    # Location
    latitude = fields.Float(string='Latitude', digits=(16, 6))
    longitude = fields.Float(string='Longitude', digits=(16, 6))

    # Additional Information
    days_on_zillow = fields.Integer(string='Days on Zillow')
    time_on_zillow = fields.Char(string='Time on Zillow')
    is_featured = fields.Boolean(string='Featured')
    is_non_owner_occupied = fields.Boolean(string='Non Owner Occupied')
    is_preforeclosure_auction = fields.Boolean(string='Preforeclosure Auction')
    is_premier_builder = fields.Boolean(string='Premier Builder')
    is_showcase_listing = fields.Boolean(string='Showcase Listing')
    is_unmappable = fields.Boolean(string='Unmappable')
    is_zillow_owned = fields.Boolean(string='Zillow Owned')

    # Listing Sub Type
    is_fsba = fields.Boolean(string='For Sale By Agent')
    is_for_auction = fields.Boolean(string='For Auction')
    is_new_home = fields.Boolean(string='New Home')
    is_open_house = fields.Boolean(string='Open House')

    # Open House Information
    open_house = fields.Char(string='Open House Schedule')
    open_house_start = fields.Datetime(string='Open House Start')
    open_house_end = fields.Datetime(string='Open House End')

    # Price Change Information
    price_change = fields.Float(string='Price Change')
    price_reduction = fields.Char(string='Price Reduction')
    date_price_changed = fields.Char(string='Date Price Changed (Timestamp)')

    # External References
    zpid = fields.Char(string='ZPID', required=True)
    provider_listing_id = fields.Char(string='Provider Listing ID')

    # Image and URL Information
    hi_res_image_link = fields.Char(string='High Resolution Image Link')
    hdp_url = fields.Char(string='HDP URL')

    map_url = fields.Char(string='Map URL', compute='_compute_map_url')
    map_html = fields.Html(string='Map', compute='_compute_map_html')

    img_src = fields.Char(string='Image URL')
    listing_sub_type = fields.Text(string='Listing Sub Type')
    price_for_hdp = fields.Float(string='Price For HDP')
    home_status_for_hdp = fields.Char(string='Home Status For HDP')
    should_highlight = fields.Boolean(string='Should Highlight')

    img_html = fields.Html(string='Image', compute='_compute_img_html')

    last_fetched = fields.Datetime(string='Last Fetched')

    # Property Details Relationship
    property_detail_ids = fields.One2many('zillow.property.detail', 'property_id', string='Property Details')

    # CyclSales Integration
    sent_to_cyclsales_by = fields.Many2many(
        'res.users',
        'zillow_property_cyclsales_rel',
        'property_id',
        'user_id',
        string='Sent to CyclSales by',
        help='Users who have sent this property to CyclSales'
    )
    sent_to_cyclsales_count = fields.Integer(
        string='Times Sent to CyclSales',
        compute='_compute_sent_to_cyclsales',
        store=True
    )
    last_sent_to_cyclsales = fields.Datetime(
        string='Last Sent to CyclSales',
        help='When this property was last sent to CyclSales'
    )

    @api.depends('sent_to_cyclsales_by')
    def _compute_sent_to_cyclsales_count(self):
        for record in self:
            record.sent_to_cyclsales_count = len(record.sent_to_cyclsales_by)

    def action_send_to_cyclsales(self, user_id):
        """Send property to CyclSales and record the user who sent it."""
        self.ensure_one()
        if user_id not in self.sent_to_cyclsales_by.ids:
            self.write({
                'sent_to_cyclsales_by': [(4, user_id)]
            })
            return True
        return False

    @api.depends('latitude', 'longitude')
    def _compute_map_html(self):
        for rec in self:
            if rec.latitude and rec.longitude:
                url = f"https://www.openstreetmap.org/?mlat={rec.latitude}&mlon={rec.longitude}#map=18/{rec.latitude}/{rec.longitude}"
                rec.map_url = url
                rec.map_html = f'<a href="{url}" target="_blank">View on Map</a>'
            else:
                rec.map_url = ''
                rec.map_html = ''

    def _compute_map_url(self):
        for rec in self:
            if rec.latitude and rec.longitude:
                rec.map_url = f"https://www.openstreetmap.org/?mlat={rec.latitude}&mlon={rec.longitude}#map=18/{rec.latitude}/{rec.longitude}"
            else:
                rec.map_url = ''

    def _compute_img_html(self):
        for rec in self:
            if rec.img_src:
                rec.img_html = f'<img src="{rec.img_src}" style="max-width:300px;max-height:200px;"/>'
            else:
                rec.img_html = ''

    def action_fetch_property_data(self, ignore_last_fetched=False):
        """Fetch property data from Zillow API and update the record."""
        self.ensure_one()

        if not ignore_last_fetched:
            if self.last_fetched and self.last_fetched > fields.Datetime.now() - timedelta(days=7):
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': 'Info',
                        'message': 'Property data is up to date (fetched within the last 7 days).',
                        'sticky': False,
                        'type': 'info',
                    }
                }

        # Get API credentials from settings
        ICPSudo = self.env['ir.config_parameter'].sudo()
        api_host = ICPSudo.get_param('web_scraper.rapidapi_host', 'zillow56.p.rapidapi.com')
        api_key = ICPSudo.get_param('web_scraper.rapidapi_key')

        if not api_host or not api_key:
            raise models.UserError('Please configure RapidAPI credentials in Settings')

        url = f"https://{api_host}/propertyV2"

        headers = {
            'x-rapidapi-host': api_host,
            'x-rapidapi-key': api_key
        }

        params = {
            'zpid': self.zpid
        }

        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()

            # Update record with API data
            if data:
                # Extract address data
                address = data.get('address', {})

                # Map API response fields to model fields for main property
                vals = {
                    'street_address': address.get('streetAddress'),
                    'city': address.get('city'),
                    'state': address.get('state'),
                    'zipcode': address.get('zipcode'),
                    'price': float(data['price']) if data.get('price') else False,
                    'bedrooms': int(data['bedrooms']) if data.get('bedrooms') else False,
                    'bathrooms': float(data['bathrooms']) if data.get('bathrooms') else False,
                    'living_area': float(data['livingArea']) if data.get('livingArea') else False,
                    'lot_area_value': float(data['lotSize']) if data.get('lotSize') else False,
                    'home_status': data.get('homeStatus'),
                    'home_type': data.get('homeType'),
                    'latitude': float(data['latitude']) if data.get('latitude') else False,
                    'longitude': float(data['longitude']) if data.get('longitude') else False,
                    'zestimate': float(data['zestimate']) if data.get('zestimate') else False,
                    'rent_zestimate': float(data['rentZestimate']) if data.get('rentZestimate') else False,
                    'tax_assessed_value': float(data['taxAssessedValue']) if data.get('taxAssessedValue') else False,
                    'time_on_zillow': data.get('timeOnZillow'),
                    'days_on_zillow': int(data['daysOnZillow']) if data.get('daysOnZillow') else False,
                    'price_change': float(data['priceChange']) if data.get('priceChange') else False,
                    'date_price_changed': data.get('datePriceChanged'),
                    'provider_listing_id': data.get('providerListingID'),
                    'last_fetched': fields.Datetime.now(),
                    'hi_res_image_link': data.get('hiResImageLink'),
                    'hdp_url': data.get('hdpUrl'),
                }

                # Boolean fields for main property
                vals.update({
                    'is_featured': data.get('isFeatured', False),
                    'is_non_owner_occupied': data.get('isNonOwnerOccupied', False),
                    'is_preforeclosure_auction': data.get('isPreforeclosureAuction', False),
                    'is_premier_builder': data.get('isPremierBuilder', False),
                    'is_showcase_listing': data.get('isShowcaseListing', False),
                    'is_unmappable': data.get('isUnmappable', False),
                    'is_zillow_owned': data.get('isZillowOwned', False),
                    'is_fsba': data.get('isFSBA', False),
                    'is_for_auction': data.get('isForAuction', False),
                    'is_new_home': data.get('isNewHome', False),
                    'is_open_house': data.get('isOpenHouse', False),
                })

                res = self.write(vals)

                if not res:
                    raise models.UserError('Failed to write data')
                # Prepare detail_vals for zillow.property.detail (only valid fields)
                attribution_info = data.get('attributionInfo', {})
                _logger.info(f"[ATTRIBUTION] Raw attribution info: {attribution_info}")

                detail_vals = {
                    'zpid': self.zpid,
                    'property_id': self.id,
                    'abbreviated_address': data.get('abbreviatedAddress'),
                    'apartments_for_rent_path': data.get('apartmentsForRentPath'),
                    # Map attributionInfo fields
                    'agent_email': attribution_info.get('agentEmail'),
                    'agent_license_number': attribution_info.get('agentLicenseNumber'),
                    'agent_name': attribution_info.get('agentName'),
                    'agent_phone_number': attribution_info.get('agentPhoneNumber'),
                    'attribution_title': attribution_info.get('attributionTitle'),
                    'broker_name': attribution_info.get('brokerName'),
                    'broker_phone_number': attribution_info.get('brokerPhoneNumber'),
                    'buyer_agent_member_state_license': attribution_info.get('buyerAgentMemberStateLicense'),
                    'buyer_agent_name': attribution_info.get('buyerAgentName'),
                    'buyer_brokerage_name': attribution_info.get('buyerBrokerageName'),
                    'co_agent_license_number': attribution_info.get('coAgentLicenseNumber'),
                    'co_agent_name': attribution_info.get('coAgentName'),
                    'co_agent_number': attribution_info.get('coAgentNumber'),
                    'mls_id': data.get('mlsId'),
                    'mls_name': data.get('mlsName'),
                    'mls_disclaimer': data.get('mlsDisclaimer'),
                    'provider_logo': data.get('providerLogo'),
                    'true_status': data.get('trueStatus'),
                    'last_checked': Datetime.now(),
                    'last_updated': fields.Datetime.now(),
                    'bathrooms': float(data['bathrooms']) if data.get('bathrooms') else False,
                    'bedrooms': int(data['bedrooms']) if data.get('bedrooms') else False,
                    'hdp_type_dimension': data.get('hdpTypeDimension'),
                    'hdp_url': data.get('hdpUrl'),
                    'home_status': data.get('homeStatus'),
                    'home_type': data.get('homeType'),
                    'is_premier_builder': data.get('isPremierBuilder', False),
                    'is_showcase_listing': data.get('isShowcaseListing', False),
                    'latitude': float(data['latitude']) if data.get('latitude') else False,
                    'longitude': float(data['longitude']) if data.get('longitude') else False,
                    'listing_type_dimension': data.get('listingTypeDimension'),
                    'living_area': float(data['livingArea']) if data.get('livingArea') else False,
                    'living_area_units': data.get('livingAreaUnits'),
                    'living_area_units_short': data.get('livingAreaUnitsShort'),
                    'living_area_value': float(data['livingAreaValue']) if data.get('livingAreaValue') else False,
                    'lot_area_units': data.get('lotAreaUnits'),
                    'lot_area_value': float(data['lotAreaValue']) if data.get('lotAreaValue') else False,
                    'lot_size': float(data['lotSize']) if data.get('lotSize') else False,
                    'price': float(data['price']) if data.get('price') else False,
                    'currency': data.get('currency', 'USD'),
                    'property_type_dimension': data.get('propertyTypeDimension'),
                    'provider_listing_id': data.get('providerListingID'),
                    'state': data.get('state'),
                    'parent_region_name': data.get('parentRegionName'),
                    'new_construction_type': data.get('newConstructionType'),
                    'formatted_chip_location': data.get('formattedChipLocation'),
                    'country': data.get('country', 'USA'),
                    'county': data.get('county'),
                    'county_fips': data.get('countyFips'),
                    'county_id': int(data['countyId']) if data.get('countyId') else False,
                    'date_posted_string': data.get('datePostedString'),
                    'days_on_zillow': int(data['daysOnZillow']) if data.get('daysOnZillow') else False,
                    'description': data.get('description'),
                    'desktop_web_hdp_image_link': data.get('desktopWebHdpImageLink'),
                    'hi_res_image_link': data.get('hiResImageLink'),
                    'last_sold_price': float(data['lastSoldPrice']) if data.get('lastSoldPrice') else False,
                    'list_price_low': float(data['listPriceLow']) if data.get('listPriceLow') else False,
                    'keystone_home_status': data.get('keystoneHomeStatus'),
                    'is_current_signed_in_agent_responsible': data.get('isCurrentSignedInAgentResponsible', False),
                    'is_current_signed_in_user_verified_owner': data.get('isCurrentSignedInUserVerifiedOwner', False),
                    'is_featured': data.get('isFeatured', False),
                    'is_housing_connector': data.get('isHousingConnector', False),
                    'is_income_restricted': data.get('isIncomeRestricted', False),
                    'is_listing_claimed_by_current_signed_in_user': data.get('isListingClaimedByCurrentSignedInUser',
                                                                             False),
                    'is_non_owner_occupied': data.get('isNonOwnerOccupied', False),
                    'is_paid_multi_family_broker_id': data.get('isPaidMultiFamilyBrokerId', False),
                    'is_recent_status_change': data.get('isRecentStatusChange', False),
                    'is_rental_listing_off_market': data.get('isRentalListingOffMarket', False),
                    'is_rentals_lead_cap_met': data.get('isRentalsLeadCapMet', False),
                    'is_undisclosed_address': data.get('isUndisclosedAddress', False),
                    'is_zillow_owned': data.get('isZillowOwned', False),
                    'has_approved_third_party_virtual_tour_url': data.get('hasApprovedThirdPartyVirtualTourUrl', False),
                    'has_bad_geocode': data.get('hasBadGeocode', False),
                    'has_public_video': data.get('hasPublicVideo', False),
                    'interactive_floor_plan_url': data.get('interactiveFloorPlanUrl'),
                    'favorite_count': int(data['favoriteCount']) if data.get('favoriteCount') else False,
                    'featured_listing_type_dimension': data.get('featuredListingTypeDimension'),
                    'foreclosure_amount': float(data['foreclosureAmount']) if data.get('foreclosureAmount') else False,
                    'foreclosure_auction_city': data.get('foreclosureAuctionCity'),
                    'foreclosure_auction_description': data.get('foreclosureAuctionDescription'),
                    'foreclosure_auction_filing_date': data.get('foreclosureAuctionFilingDate'),
                    'foreclosure_auction_location': data.get('foreclosureAuctionLocation'),
                    'foreclosure_auction_time': data.get('foreclosureAuctionTime'),
                    'foreclosure_balance_reporting_date': data.get('foreclosureBalanceReportingDate'),
                    'foreclosure_date': data.get('foreclosureDate'),
                    'foreclosure_default_description': data.get('foreclosureDefaultDescription'),
                    'foreclosure_default_filing_date': data.get('foreclosureDefaultFilingDate'),
                    'foreclosure_judicial_type': data.get('foreclosureJudicialType'),
                    'foreclosure_loan_amount': float(data['foreclosureLoanAmount']) if data.get(
                        'foreclosureLoanAmount') else False,
                    'foreclosure_loan_date': ms_to_odoo_date(data['foreclosureLoanDate']) if data.get(
                        'foreclosureLoanDate') else False,
                    'foreclosure_loan_originator': data.get('foreclosureLoanOriginator'),
                    'foreclosure_more_info': data.get('foreclosureMoreInfo'),
                    'foreclosure_past_due_balance': float(data['foreclosurePastDueBalance']) if data.get(
                        'foreclosurePastDueBalance') else False,
                    'foreclosure_prior_sale_amount': float(data['foreclosurePriorSaleAmount']) if data.get(
                        'foreclosurePriorSaleAmount') else False,
                    'foreclosure_prior_sale_date': ms_to_odoo_date(data['foreclosurePriorSaleDate']) if data.get(
                        'foreclosurePriorSaleDate') else False,
                    'foreclosure_unpaid_balance': float(data['foreclosureUnpaidBalance']) if data.get(
                        'foreclosureUnpaidBalance') else False,
                    'listing_account_user_id': data.get('listingAccountUserId'),
                    'listing_data_source': data.get('listingDataSource'),
                    'listing_feed_id': data.get('listingFeedId'),
                    'marketing_name': data.get('marketingName'),
                    'mlsid': data.get('mlsid'),
                    'monthly_hoa_fee': float(data['monthlyHoaFee']) if data.get('monthlyHoaFee') else False,
                    'lot_premium': float(data['lotPremium']) if data.get('lotPremium') else False,
                    'move_home_map_location_link': data.get('moveHomeMapLocationLink'),
                    'mortgage_arm5_rate': float(data['mortgageArm5Rate']) if data.get('mortgageArm5Rate') else False,
                    'mortgage_arm5_last_updated': data.get('mortgageArm5LastUpdated'),
                    'mortgage_arm5_rate_source': data.get('mortgageArm5RateSource'),
                    'mortgage_15yr_fixed_rate': float(data['mortgage15yrFixedRate']) if data.get(
                        'mortgage15yrFixedRate') else False,
                    'mortgage_15yr_fixed_last_updated': data.get('mortgage15yrFixedLastUpdated'),
                    'mortgage_15yr_fixed_rate_source': data.get('mortgage15yrFixedRateSource'),
                    'mortgage_30yr_fixed_rate': float(data['mortgage30yrFixedRate']) if data.get(
                        'mortgage30yrFixedRate') else False,
                    'mortgage_30yr_fixed_last_updated': data.get('mortgage30yrFixedLastUpdated'),
                    'mortgage_30yr_fixed_rate_source': data.get('mortgage30yrFixedRateSource'),
                    'listed_by': data.get('listedBy'),
                    'listing_account': data.get('listingAccount'),
                    'listing_metadata': data.get('listingMetadata'),
                    'listing_provider': data.get('listingProvider'),
                    'contingent_listing_type': data.get('contingentListingType'),
                    'community_url': data.get('communityUrl'),
                    'down_payment_assistance': data.get('downPaymentAssistance'),
                    'edit_property_history_link': data.get('editPropertyHistoryLink'),
                    'foreclosing_bank': data.get('foreclosingBank'),
                    'foreclosure_types': data.get('foreclosureTypes'),
                    'houses_for_rent_in_zipcode_search_url': data.get('housesForRentInZipcodeSearchUrl'),
                    'home_insights': data.get('homeInsights'),
                    'home_values': data.get('homeValues'),
                    'neighborhood_id': int(data['neighborhoodId']) if data.get('neighborhoodId') else False,
                    'neighborhood_map_thumb_url': data.get('neighborhoodMapThumbUrl'),
                    'neighborhood_region_name': data.get('neighborhoodRegionName'),
                    'neighborhood_search_url_path': data.get('neighborhoodSearchUrlPath'),
                    'time_on_zillow': data.get('timeOnZillow'),
                    'time_zone': data.get('timeZone'),
                    'tour_view_count': int(data['tourViewCount']) if data.get('tourViewCount') else False,
                    'virtual_tour_url': data.get('virtualTourUrl'),
                    'what_i_love': data.get('whatILove'),
                    'year_built': int(data['yearBuilt']) if data.get('yearBuilt') else False,
                    'zestimate': float(data['zestimate']) if data.get('zestimate') else False,
                    'zestimate_high_percent': data.get('zestimateHighPercent'),
                    'zestimate_low_percent': data.get('zestimateLowPercent'),
                    'zipcode': data.get('zipcode'),
                    'zipcode_id': int(data['zipcodeId']) if data.get('zipcodeId') else False,
                    'zipcode_search_url_path': data.get('zipcodeSearchUrlPath'),
                }

                # _logger.info(f"[ATTRIBUTION] Mapped attribution fields: {detail_vals}")

                # Create or update property detail record
                property_detail = self.env['zillow.property.detail'].search([('zpid', '=', self.zpid)], limit=1)
                if not property_detail:
                    property_detail = self.env['zillow.property.detail'].search([('property_id', '=', self.id)],
                                                                                limit=1)
                # print(f"Creating/updating property detail for property {self.id} with vals: {detail_vals}")
                if property_detail:
                    try:
                        property_detail.write(detail_vals)
                    except Exception as e:
                        _logger.error(f"Failed to write property_detail: {e}")
                        raise
                else:
                    property_detail = self.env['zillow.property.detail'].create([detail_vals])
                # Handle listingAgents array (under attributionInfo)
                listing_agents = data.get('attributionInfo', {}).get('listingAgents', [])
                # Remove old agents for this property detail
                property_detail.agent_ids.unlink()
                for agent in listing_agents:
                    _logger.info(f"Creating agent for property_detail {property_detail.id}: {agent}")
                    self.env['zillow.property.agent'].create([{
                        'property_id': property_detail.id,
                        'associated_agent_type': agent.get('associatedAgentType'),
                        'member_full_name': agent.get('memberFullName'),
                        'member_state_license': agent.get('memberStateLicense'),
                    }])
                self.env.cr.commit()  # Force commit to ensure property_detail is saved

                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': 'Success',
                        'message': 'Property data updated successfully',
                        'sticky': False,
                        'type': 'success',
                    }
                }
            else:
                raise models.UserError('Invalid data received from API')

        except requests.exceptions.RequestException as e:
            _logger.error('Error fetching property data: %s', str(e))
            raise models.UserError(f'Error fetching property data: {str(e)}')

    def action_open_search_wizard(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Search Property',
            'res_model': 'zillow.property.search.wizard',
            'view_mode': 'form',
            'target': 'new',
        }

    @api.model
    def cron_update_all_properties(self):
        properties = self.search([])
        for prop in properties:
            try:
                prop.action_fetch_property_data()
            except Exception as e:
                _logger.error(f"Failed to update property {prop.zpid}: {e}")

    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        user = self.env.user
        _logger.info(f"[ZillowProperty.search] Called by user: {user.id} ({user.name})")
        market_location = user.market_location_id
        if not market_location:
            _logger.warning(f"[ZillowProperty.search] No market_location_id set for user {user.id}")
        else:
            _logger.info(f"[ZillowProperty.search] market_location_id: {market_location.id} ({market_location.name})")
            if not market_location.zipcode_ids:
                _logger.warning(
                    f"[ZillowProperty.search] No zipcode_ids set for market_location_id {market_location.id}")
            else:
                zipcodes = market_location.zipcode_ids.mapped('zip_code')
                _logger.info(f"[ZillowProperty.search] zipcodes for user {user.id}: {zipcodes}")
                if not any(arg[0] == 'zipcode' for arg in args):
                    args = args + [('zipcode', 'in', zipcodes)]
                    _logger.info(f"[ZillowProperty.search] Domain args updated: {args}")

        # Call super with only the parameters it expects
        return super(ZillowProperty, self).search(args, offset=offset, limit=limit, order=order)

    def update_zero_price_properties(self):
        """
        Update all Zillow Property records where price is 0 by fetching fresh data.
        """
        zero_price_props = self.env['zillow.property'].search([('price', '<', 1)])
        print(f"Records: {zero_price_props}")
        for prop in zero_price_props:
            try:
                prop.action_fetch_property_data()
            except Exception as e:
                _logger.error(f"Failed to update property {prop.zpid}: {e}")

    def fetch_details_for_missing_properties(self):
        _logger.info(">>> fetch_details_for_missing_properties CALLED on ids: %s", self.ids)
        _logger.info(f"Found {len(self)} properties to process.")
        props_without_details = self
        count = 0
        for prop in props_without_details:
            try:
                _logger.info(f"Fetching details for property zpid={prop.zpid}, id={prop.id}")
                prop.action_fetch_property_data(ignore_last_fetched=True)
                count += 1
            except Exception as e:
                _logger.error(f"Failed to fetch details for property {prop.zpid}: {e}")
        msg = f"Fetched details for {count} properties." if count else "No properties needed details."
        _logger.info(msg)
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Fetch Details',
                'message': msg,
                'sticky': False,
                'type': 'success' if count else 'warning',
            }
        }

    def action_fetch_details_for_selected(self):
        _logger.info(">>> action_fetch_details_for_selected CALLED on ids: %s", self.ids)
        return self.fetch_details_for_missing_properties()

    def send_to_ghl_webhook(self):
        import requests
        import logging
        _logger = logging.getLogger(__name__)
        webhook_url = "https://services.leadconnectorhq.com/hooks/N1D3b2rc7RAqs4k7qdFY/webhook-trigger/47dabb25-a458-43ec-a0e6-8832251239a5"
        for rec in self:
            agent = rec.listing_agent_id
            payload = {
                "listing_agent": agent.display_name if agent else '',
                "baths": rec.bathrooms,
                "beds": rec.bedrooms,
                "sqft": rec.living_area,
                "lot_size": rec.lot_size,
                "year_built": rec.year_built,
                "address": rec.street_address,
                "property_type": rec.home_type,
                "asking_price": rec.list_price,
                "realtor": agent.display_name if agent else '',
                "realtor_email": agent.email if agent else '',
                "realtor_phone": agent.phone_number if agent else '',
                "description": rec.description,
            }
            _logger.info(f"[GHL TEST] Sending payload to GHL webhook: {payload}")
            try:
                resp = requests.post(webhook_url, json=payload, timeout=10)
                _logger.info(f"[GHL TEST] Webhook response: {resp.status_code} {resp.text}")
            except Exception as e:
                _logger.error(f"[GHL TEST] Webhook error: {e}")

    @api.model_create_multi
    def create(self, vals_list):
        # Ensure vals_list is always a list
        if isinstance(vals_list, dict):
            vals_list = [vals_list]
        records = super(ZillowProperty, self).create(vals_list)
        for record in records:
            record.action_fetch_property_data(ignore_last_fetched=True)
        return records


class ZillowHomeType(models.Model):
    _name = 'zillow.home.type'
    _description = 'Zillow Home Type'

    name = fields.Char(string='Name', required=True)


class ZillowPropertySearchWizard(models.TransientModel):
    _name = 'zillow.property.search.wizard'
    _description = 'Zillow Property Search Wizard'

    address = fields.Char(string='Address', required=True)

    # --- Advanced Search Fields ---
    status = fields.Selection([
        ('for_sale', 'For Sale'),
        ('sold', 'Sold')
    ], string='Status', default='for_sale')

    price_min = fields.Selection(
        [(str(x), '${:,.0f}'.format(x)) for x in range(0, 2000001, 50000)],
        string='Min Price', default='0')
    price_max = fields.Selection(
        [(str(x), '${:,.0f}'.format(x)) for x in range(0, 2000001, 50000)],
        string='Max Price', default='2000000')

    bedrooms = fields.Selection([
        ('', 'Any'),
        ('1', '1'),
        ('2', '2'),
        ('3', '3'),
        ('4', '4'),
        ('5', '5+'),
    ], string='Bedrooms', default='')
    bathrooms = fields.Selection([
        ('', 'Any'),
        ('1', '1'),
        ('2', '2'),
        ('3', '3'),
        ('4', '4'),
        ('5', '5+'),
    ], string='Bathrooms', default='')

    home_type_multi = fields.Many2many('zillow.home.type', string='Home Types')

    sqft_min = fields.Selection(
        [('-1', 'No Min')] + [(str(x), '{:,}'.format(x)) for x in range(500, 7501, 250)],
        string='Min Sqft', default='-1')
    sqft_max = fields.Selection(
        [('-1', 'No Max')] + [(str(x), '{:,}'.format(x)) for x in range(500, 7501, 250)],
        string='Max Sqft', default='-1')

    lot_size_min = fields.Selection([
        ('-1', 'No Min'),
        ('1000', '1,000 sqft'),
        ('2000', '2,000 sqft'),
        ('3000', '3,000 sqft'),
        ('4000', '4,000 sqft'),
        ('5000', '5,000 sqft'),
        ('7500', '7,500 sqft'),
        ('10890', '1/4 acre/10,890 sqft'),
        ('21780', '1/2 acre'),
        ('43560', '1 acre'),
        ('87120', '2 acres'),
        ('217800', '5 acres'),
        ('435600', '10 acres'),
        ('871200', '20 acres'),
        ('2178000', '50 acres'),
        ('4356000', '100 acres'),
    ], string='Min Lot Size', default='-1')
    lot_size_max = fields.Selection([
        ('-1', 'No Max'),
        ('1000', '1,000 sqft'),
        ('2000', '2,000 sqft'),
        ('3000', '3,000 sqft'),
        ('4000', '4,000 sqft'),
        ('5000', '5,000 sqft'),
        ('7500', '7,500 sqft'),
        ('10890', '1/4 acre/10,890 sqft'),
        ('21780', '1/2 acre'),
        ('43560', '1 acre'),
        ('87120', '2 acres'),
        ('217800', '5 acres'),
        ('435600', '10 acres'),
        ('871200', '20 acres'),
        ('2178000', '50 acres'),
        ('4356000', '100 acres'),
    ], string='Max Lot Size', default='-1')

    year_built_min = fields.Char(string='Year Built (Min)')
    year_built_max = fields.Char(string='Year Built (Max)')

    amenities = fields.Selection([
        ('ac', 'Must Have A/C'),
        ('pool', 'Must Have Pool'),
        ('waterfront', 'Waterfront'),
    ], string='Amenities', required=False)

    view = fields.Selection([
        ('city', 'City'),
        ('mountain', 'Mountain'),
        ('park', 'Park'),
        ('water', 'Water'),
    ], string='View', required=False)

    def action_search_property(self):
        ICPSudo = self.env['ir.config_parameter'].sudo()
        api_host = ICPSudo.get_param('web_scraper.rapidapi_host', 'zillow56.p.rapidapi.com')
        api_key = ICPSudo.get_param('web_scraper.rapidapi_key')
        if not api_host or not api_key:
            raise models.UserError('Please configure RapidAPI credentials in Settings')
        url = f"https://{api_host}/search_address"
        headers = {
            'x-rapidapi-host': api_host,
            'x-rapidapi-key': api_key
        }
        params = {'address': self.address}
        try:
            response = requests.get(url, headers=headers, params=params)
            _logger.info(f"Search address response: {response.status_code} {response.text}")
            response.raise_for_status()
            data = response.json()
            if not data or not data.get('zpid'):
                raise models.UserError('No property found for this address.')
            zpid = data['zpid']
            property_obj = self.env['zillow.property'].search([('zpid', '=', zpid)], limit=1)
            vals = {
                'street_address': data.get('address', {}).get('streetAddress'),
                'city': data.get('address', {}).get('city'),
                'state': data.get('address', {}).get('state'),
                'zipcode': data.get('address', {}).get('zipcode'),
                'price': float(data['price']) if data.get('price') else False,
                'bedrooms': int(data['bedrooms']) if data.get('bedrooms') else False,
                'bathrooms': float(data['bathrooms']) if data.get('bathrooms') else False,
                'living_area': float(data['livingArea']) if data.get('livingArea') else False,
                'lot_area_value': float(data['lotSize']) if data.get('lotSize') else False,
                'home_status': data.get('homeStatus'),
                'home_type': data.get('homeType'),
                'latitude': float(data['latitude']) if data.get('latitude') else False,
                'longitude': float(data['longitude']) if data.get('longitude') else False,
                'zestimate': float(data['zestimate']) if data.get('zestimate') else False,
                'rent_zestimate': float(data['rentZestimate']) if data.get('rentZestimate') else False,
                'tax_assessed_value': float(data['taxAssessedValue']) if data.get('taxAssessedValue') else False,
                'time_on_zillow': data.get('timeOnZillow'),
                'days_on_zillow': int(data['daysOnZillow']) if data.get('daysOnZillow') else False,
                'price_change': float(data['priceChange']) if data.get('priceChange') else False,
                'date_price_changed': data.get('datePriceChanged'),
                'provider_listing_id': data.get('providerListingID'),
                'zpid': zpid,
            }
            vals.update({
                'is_featured': data.get('isFeatured', False),
                'is_non_owner_occupied': data.get('isNonOwnerOccupied', False),
                'is_preforeclosure_auction': data.get('isPreforeclosureAuction', False),
                'is_premier_builder': data.get('isPremierBuilder', False),
                'is_showcase_listing': data.get('isShowcaseListing', False),
                'is_unmappable': data.get('isUnmappable', False),
                'is_zillow_owned': data.get('isZillowOwned', False),
                'is_fsba': data.get('isFSBA', False),
                'is_for_auction': data.get('isForAuction', False),
                'is_new_home': data.get('isNewHome', False),
                'is_open_house': data.get('isOpenHouse', False),
            })
            if property_obj:
                property_obj.write(vals)
            else:
                self.env['zillow.property'].create(vals)
            return {'type': 'ir.actions.client', 'tag': 'display_notification',
                    'params': {'title': 'Success', 'message': 'Property data imported/updated successfully',
                               'sticky': False, 'type': 'success'}}
        except requests.exceptions.RequestException as e:
            _logger.error('Error searching property: %s', str(e))
            raise models.UserError(f'Error searching property: {str(e)}')
