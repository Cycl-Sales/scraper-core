import requests
import logging
import time
from datetime import datetime
from typing import Dict, List, Optional, Any, Generator

_logger = logging.getLogger(__name__)

class GHLAPIPaginator:
    """
    Utility class for handling paginated GHL API calls with proper error handling,
    rate limiting, and retry logic.
    """
    
    def __init__(self, location_token: str, base_url: str = "https://services.leadconnectorhq.com"):
        self.location_token = location_token
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'Accept': 'application/json',
            'Authorization': f'Bearer {location_token}',
            'Version': '2021-07-28',
            'Content-Type': 'application/json',
        })
    
    def fetch_paginated_data(self, endpoint: str, params: Optional[Dict] = None, 
                           max_pages: Optional[int] = None, delay_between_requests: float = 0.1) -> Generator[Dict, None, None]:
        """
        Fetch all pages of data from a GHL API endpoint.
        
        Args:
            endpoint (str): API endpoint (e.g., '/contacts/', '/opportunities/search')
            params (dict): Query parameters (will be updated with pagination params)
            max_pages (int): Maximum number of pages to fetch (None for unlimited)
            delay_between_requests (float): Delay between API requests in seconds
            
        Yields:
            dict: Each page of data as it's fetched
        """
        if params is None:
            params = {}
        
        # Ensure we have a limit parameter (GHL default is 100)
        if 'limit' not in params:
            params['limit'] = 100
        
        page = 1
        total_fetched = 0
        
        while True:
            if max_pages and page > max_pages:
                _logger.info(f"Reached maximum pages limit ({max_pages})")
                break
            
            # Add pagination parameters
            current_params = params.copy()
            current_params['skip'] = total_fetched
            
            try:
                url = f"{self.base_url}{endpoint}"
                _logger.info(f"Fetching page {page} from {url} with params: {current_params}")
                
                response = self.session.get(url, params=current_params, timeout=30)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Handle different response formats
                    if isinstance(data, dict):
                        # Standard GHL response format
                        items = data.get('contacts', data.get('opportunities', data.get('conversations', [])))
                        meta = data.get('meta', {})
                        total_count = meta.get('total', 0)
                        current_count = len(items) if items else 0
                        
                        _logger.info(f"Page {page}: Got {current_count} items, total available: {total_count}")
                        
                        if not items:
                            _logger.info("No more items to fetch")
                            break
                        
                        yield {
                            'page': page,
                            'items': items,
                            'meta': meta,
                            'total_count': total_count,
                            'current_count': current_count
                        }
                        
                        total_fetched += current_count
                        
                        # Check if we've fetched all available items
                        if total_count and total_fetched >= total_count:
                            _logger.info(f"Fetched all {total_count} items")
                            break
                        
                        # If we got fewer items than requested, we're done
                        if current_count < params['limit']:
                            _logger.info(f"Got fewer items ({current_count}) than limit ({params['limit']}), assuming end of data")
                            break
                    
                    elif isinstance(data, list):
                        # Direct list response
                        current_count = len(data)
                        _logger.info(f"Page {page}: Got {current_count} items (list response)")
                        
                        if not data:
                            _logger.info("No more items to fetch")
                            break
                        
                        yield {
                            'page': page,
                            'items': data,
                            'meta': {},
                            'total_count': None,
                            'current_count': current_count
                        }
                        
                        total_fetched += current_count
                        
                        # If we got fewer items than requested, we're done
                        if current_count < params['limit']:
                            _logger.info(f"Got fewer items ({current_count}) than limit ({params['limit']}), assuming end of data")
                            break
                    
                    else:
                        _logger.warning(f"Unexpected response format: {type(data)}")
                        break
                
                elif response.status_code == 404:
                    _logger.info("Endpoint returned 404, no data available")
                    break
                
                elif response.status_code == 429:
                    # Rate limit hit, wait and retry
                    retry_after = int(response.headers.get('Retry-After', 60))
                    _logger.warning(f"Rate limit hit, waiting {retry_after} seconds")
                    time.sleep(retry_after)
                    continue
                
                else:
                    _logger.error(f"API request failed: {response.status_code} {response.text}")
                    break
                
                # Delay between requests to be respectful to the API
                if delay_between_requests > 0:
                    time.sleep(delay_between_requests)
                
                page += 1
                
            except requests.exceptions.RequestException as e:
                _logger.error(f"Request error on page {page}: {str(e)}")
                break
            except Exception as e:
                _logger.error(f"Unexpected error on page {page}: {str(e)}")
                break
    
    def fetch_all_data(self, endpoint: str, params: Optional[Dict] = None, 
                      max_pages: Optional[int] = None, delay_between_requests: float = 0.1) -> Dict[str, Any]:
        """
        Fetch all pages and return combined results.
        
        Args:
            endpoint (str): API endpoint
            params (dict): Query parameters
            max_pages (int): Maximum number of pages to fetch
            delay_between_requests (float): Delay between requests
            
        Returns:
            dict: Combined results with all items and metadata
        """
        all_items = []
        total_pages = 0
        total_count = 0
        
        for page_data in self.fetch_paginated_data(endpoint, params, max_pages, delay_between_requests):
            all_items.extend(page_data['items'])
            total_pages = page_data['page']
            if page_data['total_count']:
                total_count = page_data['total_count']
        
        return {
            'success': True,
            'items': all_items,
            'total_items': len(all_items),
            'total_pages': total_pages,
            'total_count': total_count,
            'endpoint': endpoint
        }

    def fetch_contacts_with_pagination(self, location_id: str, max_pages: Optional[int] = None, page_limit: int = 100, delay_between_requests: float = 0.1) -> Dict[str, Any]:
        """
        Fetch all contacts for a location using POST /contacts/search with standard pagination.
        Args:
            location_id (str): GHL location ID
            max_pages (int): Maximum number of pages to fetch (None for unlimited)
            page_limit (int): Number of records per page (max 100)
            delay_between_requests (float): Delay between requests
        Returns:
            dict: All contacts data
        """
        all_contacts = []
        total = None
        page = 1
        pages_fetched = 0
        while True:
            if max_pages and page > max_pages:
                _logger.info(f"Reached maximum pages limit ({max_pages})")
                break
            body = {
                "locationId": location_id,
                "page": page,
                "pageLimit": page_limit,
                "sort": [
                    {
                        "field": "dateUpdated",
                        "direction": "desc"
                    }
                ]
            }
            url = f"{self.base_url}/contacts/search"
            try:
                _logger.info(f"Fetching contacts page {page} for location {location_id} via POST {url}")
                response = self.session.post(url, json=body, timeout=30)
                if response.status_code == 200:
                    data = response.json()
                    contacts = data.get('contacts', [])
                    total = data.get('total', None)
                    _logger.info(f"Fetched {len(contacts)} contacts on page {page} (total: {total})")
                    all_contacts.extend(contacts)
                    pages_fetched += 1
                    if len(contacts) < page_limit:
                        _logger.info("Last page reached (fewer contacts than pageLimit)")
                        break
                    if total is not None and len(all_contacts) >= total:
                        _logger.info("Fetched all available contacts")
                        break
                    page += 1
                    time.sleep(delay_between_requests)
                else:
                    _logger.error(f"Contacts API request failed: {response.status_code} {response.text}")
                    break
            except Exception as e:
                _logger.error(f"Request error on contacts page {page}: {str(e)}")
                break
        return {
            'success': True,
            'items': all_contacts,
            'total_items': len(all_contacts),
            'total_pages': pages_fetched,
            'total_count': total,
            'endpoint': '/contacts/search'
        }


def get_location_token(app_access_token: str, company_id: str, location_id: str) -> Optional[str]:
    """
    Get location access token from GHL API.
    
    Args:
        app_access_token (str): GHL agency access token
        company_id (str): GHL company ID
        location_id (str): GHL location ID
        
    Returns:
        str: Location access token or None if failed
    """
    try:
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
        
        response = requests.post(token_url, headers=headers, data=data, timeout=30)
        _logger.info(f"Location token response: {response.status_code}")
        
        if response.status_code in (200, 201):
            token_json = response.json()
            location_token = token_json.get('access_token')
            if location_token:
                # _logger.info("Successfully obtained location token")  # Reduced logging for production
                return location_token
            else:
                _logger.error(f"No access_token in location token response: {token_json}")
        else:
            _logger.error(f"Failed to get location token: {response.status_code} {response.text}")
        
        return None
        
    except Exception as e:
        _logger.error(f"Error getting location token: {str(e)}")
        return None


def fetch_contacts_with_pagination(location_token: str, location_id: str, max_pages: Optional[int] = None) -> Dict[str, Any]:
    paginator = GHLAPIPaginator(location_token)
    return paginator.fetch_contacts_with_pagination(location_id, max_pages=max_pages, page_limit=100, delay_between_requests=0.1)


def fetch_opportunities_with_pagination(location_token: str, location_id: str,
                                      max_pages: Optional[int] = None, contact_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Fetch all opportunities for a location (optionally filtered by contact) using pagination.
    Args:
        location_token (str): Location access token
        location_id (str): GHL location ID
        max_pages (int): Maximum pages to fetch
        contact_id (str, optional): GHL contact external ID to filter opportunities
    Returns:
        dict: All opportunities data
    """
    import requests
    import logging
    _logger = logging.getLogger(__name__)
    session = requests.Session()
    session.headers.update({
        'Accept': 'application/json',
        'Authorization': f'Bearer {location_token}',
        'Version': '2021-07-28',
        'Content-Type': 'application/json',
    })
    all_items = []
    page = 1
    total_pages = 0
    total_count = 0
    while True:
        if max_pages and page > max_pages:
            _logger.info(f"Reached maximum pages limit ({max_pages}) for opportunities/search")
            break
        params = {'location_id': location_id, 'limit': 100, 'page': page}
        if contact_id:
            params['contact_id'] = contact_id
        url = f"https://services.leadconnectorhq.com/opportunities/search"
        _logger.info(f"Fetching opportunities page {page} from {url} with params: {params}")
        response = session.get(url, params=params, timeout=30)
        if response.status_code == 200:
            data = response.json()
            items = data.get('opportunities', [])
            meta = data.get('meta', {})
            total_count = meta.get('total', 0)
            current_count = len(items)
            _logger.info(f"Page {page}: Got {current_count} opportunities, total available: {total_count}")
            if not items:
                _logger.info("No more opportunities to fetch")
                break
            all_items.extend(items)
            total_pages = page
            # If we got fewer items than requested, we're done
            if current_count < params['limit']:
                _logger.info(f"Got fewer items ({current_count}) than limit ({params['limit']}), assuming end of data")
                break
            # If we've fetched all available items
            if total_count and len(all_items) >= total_count:
                _logger.info(f"Fetched all {total_count} opportunities")
                break
            page += 1
        elif response.status_code == 422:
            _logger.error(f"API request failed: {response.status_code} {response.text}")
            break
        elif response.status_code == 429:
            retry_after = int(response.headers.get('Retry-After', 60))
            _logger.warning(f"Rate limit hit, waiting {retry_after} seconds")
            import time
            time.sleep(retry_after)
            continue
        else:
            _logger.error(f"API request failed: {response.status_code} {response.text}")
            break
    return {
        'success': True,
        'items': all_items,
        'total_items': len(all_items),
        'total_pages': total_pages,
        'total_count': total_count,
        'endpoint': '/opportunities/search'
    }


def fetch_conversations_with_pagination(location_token: str, location_id: str,
                                      max_pages: Optional[int] = None) -> Dict[str, Any]:
    """
    Fetch all conversations for a location using pagination.
    
    Args:
        location_token (str): Location access token
        location_id (str): GHL location ID
        max_pages (int): Maximum pages to fetch
        
    Returns:
        dict: All conversations data
    """
    paginator = GHLAPIPaginator(location_token)
    return paginator.fetch_all_data(
        endpoint='/conversations/search',
        params={'locationId': location_id, 'limit': 100},
        max_pages=max_pages,
        delay_between_requests=0.1
    )


def fetch_contact_tasks_with_pagination(location_token: str, contact_external_id: str,
                                      max_pages: Optional[int] = None) -> Dict[str, Any]:
    """
    Fetch all tasks for a specific contact using pagination.
    
    Args:
        location_token (str): Location access token
        contact_external_id (str): Contact external ID
        max_pages (int): Maximum pages to fetch
        
    Returns:
        dict: All tasks data for the contact
    """
    paginator = GHLAPIPaginator(location_token)
    return paginator.fetch_all_data(
        endpoint=f'/contacts/{contact_external_id}/tasks',
        params={'limit': 100},
        max_pages=max_pages,
        delay_between_requests=0.1
    ) 