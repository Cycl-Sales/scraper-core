from odoo import models, fields, api


class ZillowPropertyAddress(models.Model):
    _name = 'zillow.property.address'
    _description = 'Zillow Property Address'

    property_id = fields.Many2one('zillow.property.detail', string='Property', ondelete='cascade')
    city = fields.Char(string='City')
    community = fields.Char(string='Community')
    neighborhood = fields.Char(string='Neighborhood')
    state = fields.Char(string='State')
    street_address = fields.Char(string='Street Address')
    subdivision = fields.Char(string='Subdivision')
    zipcode = fields.Char(string='Zipcode')


class ZillowPropertyAgent(models.Model):
    _name = 'zillow.property.agent'
    _description = 'Zillow Property Agent'

    property_id = fields.Many2one('zillow.property.detail', string='Property', ondelete='cascade')
    associated_agent_type = fields.Char(string='Agent Type')
    member_full_name = fields.Char(string='Full Name')
    member_state_license = fields.Char(string='State License')


class ZillowPropertyOffice(models.Model):
    _name = 'zillow.property.office'
    _description = 'Zillow Property Office'

    property_id = fields.Many2one('zillow.property.detail', string='Property', ondelete='cascade')
    associated_office_type = fields.Selection([
        ('listOffice', 'Listing Office'),
        ('buyerOffice', 'Buyer Office')
    ], string='Office Type')
    office_name = fields.Char(string='Office Name')


class ZillowPropertyListingSubType(models.Model):
    _name = 'zillow.property.listing.subtype'
    _description = 'Zillow Property Listing Sub Type'

    property_id = fields.Many2one('zillow.property.detail', string='Property', ondelete='cascade')
    is_fsba = fields.Boolean(string='For Sale by Agent')
    is_fsbo = fields.Boolean(string='For Sale by Owner')
    is_bank_owned = fields.Boolean(string='Bank Owned')
    is_coming_soon = fields.Boolean(string='Coming Soon')
    is_for_auction = fields.Boolean(string='For Auction')
    is_foreclosure = fields.Boolean(string='Foreclosure')
    is_new_home = fields.Boolean(string='New Home')


class ZillowPropertyInsight(models.Model):
    _name = 'zillow.property.insight'
    _description = 'Zillow Property Insight'

    property_id = fields.Many2one('zillow.property.detail', string='Property')
    model_id = fields.Char(string='Model ID')
    treatment_id = fields.Char(string='Treatment ID')
    phrases = fields.Text(string='Phrases')


class ZillowPropertyListingAgent(models.Model):
    _name = 'zillow.property.listing.agent'
    _description = 'Zillow Property Listing Agent'

    property_id = fields.Many2one('zillow.property.detail', string='Property', required=True, ondelete='cascade')
    agent_reason = fields.Integer(string='Agent Reason')
    badge_type = fields.Char(string='Badge Type')
    business_name = fields.Char(string='Business Name')
    display_name = fields.Char(string='Display Name')
    encoded_zuid = fields.Char(string='Encoded ZUID')
    first_name = fields.Char(string='First Name')
    image_url = fields.Char(string='Image URL')
    image_height = fields.Integer(string='Image Height')
    image_width = fields.Integer(string='Image Width')
    phone_area_code = fields.Char(string='Phone Area Code')
    phone_prefix = fields.Char(string='Phone Prefix')
    phone_number = fields.Char(string='Phone Number')
    profile_url = fields.Char(string='Profile URL')
    rating_average = fields.Float(string='Rating Average')
    recent_sales = fields.Integer(string='Recent Sales')
    review_count = fields.Integer(string='Review Count')
    reviews_url = fields.Char(string='Reviews URL')
    services_offered = fields.Char(string='Services Offered')
    username = fields.Char(string='Username')
    write_review_url = fields.Char(string='Write Review URL')
    is_zpro = fields.Boolean(string='Is ZPRO')
    email = fields.Char(string='Email')
    license_number = fields.Char(string='License Number')
    license_state = fields.Char(string='License State')


class ZillowPropertyNearbyCity(models.Model):
    _name = 'zillow.property.nearby.city'
    _description = 'Zillow Property Nearby City'

    property_id = fields.Many2one('zillow.property.detail', string='Property')
    name = fields.Char(string='City Name')
    region_url = fields.Char(string='Region URL')


class ZillowPropertyMiniCardPhoto(models.Model):
    _name = 'zillow.property.mini.card.photo'
    _description = 'Zillow Property Mini Card Photo'

    property_id = fields.Many2one('zillow.property.detail', string='Property')
    url = fields.Char(string='Photo URL')


class ZillowPropertyNearbyRegion(models.Model):
    _name = 'zillow.property.nearby.region'
    _description = 'Zillow Property Nearby Region'

    property_id = fields.Many2one('zillow.property.detail', string='Property')
    name = fields.Char(string='Region Name')
    body = fields.Text(string='Body')
    region_url_path = fields.Char(string='Region URL Path')
    region_type = fields.Selection([
        ('neighborhood', 'Neighborhood'),
        ('zipcode', 'Zipcode')
    ], string='Region Type')


class ZillowPropertyOnsiteMessage(models.Model):
    _name = 'zillow.property.onsite.message'
    _description = 'Zillow Property Onsite Message'

    property_id = fields.Many2one('zillow.property.detail', string='Property')
    event_id = fields.Char(string='Event ID')
    bucket = fields.Char(string='Bucket')
    decision_context = fields.Text(string='Decision Context')
    is_global_holdout = fields.Boolean(string='Is Global Holdout')
    is_placement_holdout = fields.Boolean(string='Is Placement Holdout')
    last_modified = fields.Datetime(string='Last Modified')
    pass_throttle = fields.Boolean(string='Pass Throttle')
    placement_id = fields.Integer(string='Placement ID')
    placement_name = fields.Char(string='Placement Name')
    qualified_treatments = fields.Text(string='Qualified Treatments')


class ZillowPropertyTaxHistory(models.Model):
    _name = 'zillow.property.tax.history'
    _description = 'Zillow Property Tax History'

    property_id = fields.Many2one('zillow.property.detail', string='Property')
    tax_increase_rate = fields.Float(string='Tax Increase Rate')
    tax_paid = fields.Float(string='Tax Paid')
    time = fields.Datetime(string='Time')
    value = fields.Float(string='Value')
    value_increase_rate = fields.Float(string='Value Increase Rate')


class ZillowPropertyVirtualTour(models.Model):
    _name = 'zillow.property.virtual.tour'
    _description = 'Zillow Property Virtual Tour'

    property_id = fields.Many2one('zillow.property.detail', string='Property')
    approved = fields.Boolean(string='Approved')
    external_url = fields.Char(string='External URL')
    lightbox_url = fields.Char(string='Lightbox URL')
    provider_key = fields.Char(string='Provider Key')
    static_url = fields.Char(string='Static URL')


class ZillowPropertyTourEligibility(models.Model):
    _name = 'zillow.property.tour.eligibility'
    _description = 'Zillow Property Tour Eligibility'

    property_id = fields.Many2one('zillow.property.detail', string='Property')
    is_property_tour_eligible = fields.Boolean(string='Is Property Tour Eligible')
    is_final = fields.Boolean(string='Is Final')
    tour_type = fields.Selection([
        ('NONE', 'None'),
        ('VIRTUAL', 'Virtual'),
        ('IN_PERSON', 'In Person')
    ], string='Tour Type')


class ZillowPropertyDetail(models.Model):
    _name = 'zillow.property.detail'
    _description = 'Zillow Property Details'

    # Basic Information
    zpid = fields.Char(string='ZPID', required=True, index=True)
    property_id = fields.Many2one('zillow.property', string='Property', required=True, ondelete='cascade')

    # Address Information
    abbreviated_address = fields.Char(string='Abbreviated Address')
    address_ids = fields.One2many('zillow.property.address', 'property_id', string='Addresses')

    # Rental Information
    apartments_for_rent_path = fields.Char(string='Apartments for Rent Path')

    # Attribution Information
    agent_email = fields.Char(string='Agent Email')
    agent_license_number = fields.Char(string='Agent License Number')
    agent_name = fields.Char(string='Agent Name')
    agent_phone_number = fields.Char(string='Agent Phone Number')
    attribution_title = fields.Char(string='Attribution Title')
    broker_name = fields.Char(string='Broker Name')
    broker_phone_number = fields.Char(string='Broker Phone Number')
    buyer_agent_member_state_license = fields.Char(string='Buyer Agent State License')
    buyer_agent_name = fields.Char(string='Buyer Agent Name')
    buyer_brokerage_name = fields.Char(string='Buyer Brokerage Name')
    co_agent_license_number = fields.Char(string='Co-Agent License Number')
    co_agent_name = fields.Char(string='Co-Agent Name')
    co_agent_number = fields.Char(string='Co-Agent Number')

    # MLS Information
    mls_id = fields.Char(string='MLS ID')
    mls_name = fields.Char(string='MLS Name')
    mls_disclaimer = fields.Text(string='MLS Disclaimer')
    provider_logo = fields.Char(string='Provider Logo')
    true_status = fields.Char(string='True Status')

    # Listing Information
    last_checked = fields.Datetime(string='Last Checked')
    last_updated = fields.Datetime(string='Last Updated')

    # Property Details
    bathrooms = fields.Float(string='Bathrooms')
    bedrooms = fields.Integer(string='Bedrooms')

    # Agent and Office Relationships
    agent_ids = fields.One2many('zillow.property.agent', 'property_id', string='Agents')
    office_ids = fields.One2many('zillow.property.office', 'property_id', string='Offices')
    listing_sub_type_ids = fields.One2many('zillow.property.listing.subtype', 'property_id', string='Listing Sub Types')

    # Additional Information
    info_string_3 = fields.Char(string='Info String 3')
    info_string_5 = fields.Char(string='Info String 5')
    info_string_10 = fields.Text(string='Info String 10')
    info_string_16 = fields.Char(string='Info String 16')

    # New Fields from API Response
    hdp_type_dimension = fields.Selection([
        ('ForSale', 'For Sale'),
        ('ForRent', 'For Rent'),
        ('Sold', 'Sold'),
        ('RecentlySold', 'Recently Sold'),
        ('Zestimate', 'Zestimate'),
        ('Pending', 'Pending')
    ], string='HDP Type')
    hdp_url = fields.Char(string='HDP URL')
    home_status = fields.Selection([
        ('FOR_SALE', 'For Sale'),
        ('SOLD', 'Sold'),
        ('PENDING', 'Pending'),
        ('OFF_MARKET', 'Off Market'),
        ('OTHER', 'Other'),
        ('RECENTLY_SOLD', 'Recently Sold')
    ], string='Home Status')
    home_type = fields.Selection([
        ('SINGLE_FAMILY', 'Single Family'),
        ('MULTI_FAMILY', 'Multi Family'),
        ('CONDO', 'Condo'),
        ('TOWNHOUSE', 'Townhouse'),
        ('LAND', 'Land'),
        ('MANUFACTURED', 'Manufactured')
    ], string='Home Type')
    is_premier_builder = fields.Boolean(string='Is Premier Builder')
    is_showcase_listing = fields.Boolean(string='Is Showcase Listing')
    latitude = fields.Float(string='Latitude', digits=(16, 8))
    longitude = fields.Float(string='Longitude', digits=(16, 8))
    listing_type_dimension = fields.Char(string='Listing Type')
    living_area = fields.Float(string='Living Area')
    living_area_units = fields.Char(string='Living Area Units')
    living_area_units_short = fields.Char(string='Living Area Units Short')
    living_area_value = fields.Float(string='Living Area Value')
    lot_area_units = fields.Char(string='Lot Area Units')
    lot_area_value = fields.Float(string='Lot Area Value')
    lot_size = fields.Float(string='Lot Size')
    price = fields.Float(string='Price')
    currency = fields.Char(string='Currency', default='USD')
    property_type_dimension = fields.Char(string='Property Type')
    provider_listing_id = fields.Char(string='Provider Listing ID')
    state = fields.Char(string='State')
    parent_region_name = fields.Char(string='Parent Region Name')
    new_construction_type = fields.Char(string='New Construction Type')
    formatted_chip_location = fields.Text(string='Formatted Chip Location')

    # Additional Fields from New Data
    country = fields.Char(string='Country', default='USA')
    county = fields.Char(string='County')
    county_fips = fields.Char(string='County FIPS')
    county_id = fields.Integer(string='County ID')
    date_posted_string = fields.Date(string='Date Posted')
    days_on_zillow = fields.Integer(string='Days on Zillow')
    description = fields.Text(string='Description')
    desktop_web_hdp_image_link = fields.Char(string='Desktop Web HDP Image Link')
    hi_res_image_link = fields.Char(string='High Resolution Image Link')
    last_sold_price = fields.Float(string='Last Sold Price')
    list_price_low = fields.Float(string='List Price Low')
    keystone_home_status = fields.Char(string='Keystone Home Status')
    is_current_signed_in_agent_responsible = fields.Boolean(string='Is Current Agent Responsible')
    is_current_signed_in_user_verified_owner = fields.Boolean(string='Is Current User Verified Owner')
    is_featured = fields.Boolean(string='Is Featured')
    is_housing_connector = fields.Boolean(string='Is Housing Connector')
    is_income_restricted = fields.Boolean(string='Is Income Restricted')
    is_listing_claimed_by_current_signed_in_user = fields.Boolean(string='Is Listing Claimed by Current User')
    is_non_owner_occupied = fields.Boolean(string='Is Non Owner Occupied')
    is_paid_multi_family_broker_id = fields.Boolean(string='Is Paid Multi Family Broker')
    is_recent_status_change = fields.Boolean(string='Is Recent Status Change')
    is_rental_listing_off_market = fields.Boolean(string='Is Rental Listing Off Market')
    is_rentals_lead_cap_met = fields.Boolean(string='Is Rentals Lead Cap Met')
    is_undisclosed_address = fields.Boolean(string='Is Undisclosed Address')
    is_zillow_owned = fields.Boolean(string='Is Zillow Owned')
    has_approved_third_party_virtual_tour_url = fields.Boolean(string='Has Approved Virtual Tour')
    has_bad_geocode = fields.Boolean(string='Has Bad Geocode')
    has_public_video = fields.Boolean(string='Has Public Video')
    interactive_floor_plan_url = fields.Char(string='Interactive Floor Plan URL')
    favorite_count = fields.Integer(string='Favorite Count')
    featured_listing_type_dimension = fields.Char(string='Featured Listing Type')

    # Property Insights
    insight_ids = fields.One2many('zillow.property.insight', 'property_id', string='Property Insights')

    # Foreclosure Information
    foreclosure_amount = fields.Float(string='Foreclosure Amount')
    foreclosure_auction_city = fields.Char(string='Foreclosure Auction City')
    foreclosure_auction_description = fields.Text(string='Foreclosure Auction Description')
    foreclosure_auction_filing_date = fields.Date(string='Foreclosure Auction Filing Date')
    foreclosure_auction_location = fields.Char(string='Foreclosure Auction Location')
    foreclosure_auction_time = fields.Datetime(string='Foreclosure Auction Time')
    foreclosure_balance_reporting_date = fields.Date(string='Foreclosure Balance Reporting Date')
    foreclosure_date = fields.Date(string='Foreclosure Date')
    foreclosure_default_description = fields.Text(string='Foreclosure Default Description')
    foreclosure_default_filing_date = fields.Date(string='Foreclosure Default Filing Date')
    foreclosure_judicial_type = fields.Char(string='Foreclosure Judicial Type')
    foreclosure_loan_amount = fields.Float(string='Foreclosure Loan Amount')
    foreclosure_loan_date = fields.Date(string='Foreclosure Loan Date')
    foreclosure_loan_originator = fields.Char(string='Foreclosure Loan Originator')
    foreclosure_more_info = fields.Text(string='Foreclosure More Info')
    foreclosure_past_due_balance = fields.Float(string='Foreclosure Past Due Balance')
    foreclosure_prior_sale_amount = fields.Float(string='Foreclosure Prior Sale Amount')
    foreclosure_prior_sale_date = fields.Date(string='Foreclosure Prior Sale Date')
    foreclosure_unpaid_balance = fields.Float(string='Foreclosure Unpaid Balance')

    # New Fields from Latest Data
    listing_account_user_id = fields.Char(string='Listing Account User ID')
    listing_data_source = fields.Char(string='Listing Data Source')
    listing_feed_id = fields.Char(string='Listing Feed ID')
    marketing_name = fields.Char(string='Marketing Name')
    mlsid = fields.Char(string='MLS ID')
    monthly_hoa_fee = fields.Float(string='Monthly HOA Fee')
    lot_premium = fields.Float(string='Lot Premium')
    move_home_map_location_link = fields.Char(string='Move Home Map Location Link')

    # Mortgage Rates
    mortgage_arm5_rate = fields.Float(string='5-Year ARM Rate')
    mortgage_arm5_last_updated = fields.Datetime(string='5-Year ARM Last Updated')
    mortgage_arm5_rate_source = fields.Char(string='5-Year ARM Rate Source')
    mortgage_15yr_fixed_rate = fields.Float(string='15-Year Fixed Rate')
    mortgage_15yr_fixed_last_updated = fields.Datetime(string='15-Year Fixed Last Updated')
    mortgage_15yr_fixed_rate_source = fields.Char(string='15-Year Fixed Rate Source')
    mortgage_30yr_fixed_rate = fields.Float(string='30-Year Fixed Rate')
    mortgage_30yr_fixed_last_updated = fields.Datetime(string='30-Year Fixed Last Updated')
    mortgage_30yr_fixed_rate_source = fields.Char(string='30-Year Fixed Rate Source')

    # Relationships
    listing_agent_id = fields.Many2one('zillow.property.listing.agent', string='Listing Agent')
    nearby_city_ids = fields.One2many('zillow.property.nearby.city', 'property_id', string='Nearby Cities')

    # New Fields from Latest Data
    listed_by = fields.Text(string='Listed By')
    listing_account = fields.Char(string='Listing Account')
    listing_metadata = fields.Text(string='Listing Metadata')
    listing_provider = fields.Char(string='Listing Provider')
    contingent_listing_type = fields.Char(string='Contingent Listing Type')
    community_url = fields.Char(string='Community URL')
    down_payment_assistance = fields.Text(string='Down Payment Assistance')
    edit_property_history_link = fields.Char(string='Edit Property History Link')
    foreclosing_bank = fields.Char(string='Foreclosing Bank')
    foreclosure_types = fields.Text(string='Foreclosure Types')
    houses_for_rent_in_zipcode_search_url = fields.Char(string='Houses for Rent in Zipcode Search URL')
    home_insights = fields.Text(string='Home Insights')
    home_values = fields.Text(string='Home Values')
    keystone_home_status = fields.Char(string='Keystone Home Status')

    # New Relationships
    mini_card_photo_ids = fields.One2many('zillow.property.mini.card.photo', 'property_id', string='Mini Card Photos')
    nearby_region_ids = fields.One2many('zillow.property.nearby.region', 'property_id', string='Nearby Regions')
    onsite_message_ids = fields.One2many('zillow.property.onsite.message', 'property_id', string='Onsite Messages')
    tax_history_ids = fields.One2many('zillow.property.tax.history', 'property_id', string='Tax History')
    virtual_tour_id = fields.Many2one('zillow.property.virtual.tour', string='Virtual Tour')
    tour_eligibility_id = fields.Many2one('zillow.property.tour.eligibility', string='Tour Eligibility')

    # Additional Fields
    neighborhood_id = fields.Integer(string='Neighborhood ID')
    neighborhood_map_thumb_url = fields.Char(string='Neighborhood Map Thumbnail URL')
    neighborhood_region_name = fields.Char(string='Neighborhood Region Name')
    neighborhood_search_url_path = fields.Char(string='Neighborhood Search URL Path')
    time_on_zillow = fields.Char(string='Time on Zillow')
    time_zone = fields.Char(string='Time Zone')
    tour_view_count = fields.Integer(string='Tour View Count')
    virtual_tour_url = fields.Char(string='Virtual Tour URL')
    what_i_love = fields.Text(string='What I Love')
    year_built = fields.Integer(string='Year Built')
    zestimate = fields.Float(string='Zestimate')
    zestimate_high_percent = fields.Char(string='Zestimate High Percent')
    zestimate_low_percent = fields.Char(string='Zestimate Low Percent')
    zipcode = fields.Char(string='Zipcode')
    zipcode_id = fields.Integer(string='Zipcode ID')
    zipcode_search_url_path = fields.Char(string='Zipcode Search URL Path')

    _sql_constraints = [
        ('zpid_uniq', 'unique(zpid)', 'ZPID must be unique!')
    ]
