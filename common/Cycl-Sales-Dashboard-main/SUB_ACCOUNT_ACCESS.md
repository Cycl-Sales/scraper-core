# Sub-Account Access Implementation

This document describes the sub-account level access implementation for the Cycl Sales Dashboard.

## Overview

The dashboard now supports two access modes:
1. **Agency Mode**: Full access to all features and locations (original functionality)
2. **Sub-Account Mode**: Limited access to specific location data only

## How It Works

### Authentication Flow

1. **URL Detection**: When a user visits a URL with `location_id` parameter, the system automatically switches to sub-account mode
2. **Validation**: The system validates the `location_id` by making an API call to verify it exists
3. **Session Management**: Valid location IDs are stored in localStorage for persistence
4. **Access Control**: Sub-accounts can only access specific pages and their own data

### Supported URLs for Sub-Accounts

Sub-accounts can access these pages with their `location_id`:

```
http://localhost:3000/analytics?location_id=GMCTanHIR07xDE3kvnpo
http://localhost:3000/automations?location_id=GMCTanHIR07xDE3kvnpo
http://localhost:3000/call-details?contact_id=34450&contact=Lori%20Barber&date=2025-08-18T19%3A21%3A06.114000&tags=name%20via%20lookup%2Csent%20quick%20message%2Cunqualified%2Cgoogle-call%2Cnew%20lead%20no%20answer%20campaign%2Cai%20follow%20up%20bot%2Cai%20off
```

### Components

#### SubAccountContext
- Manages sub-account authentication state
- Provides location ID validation
- Handles session persistence

#### SubAccountAuth
- Authentication UI for sub-accounts
- Location ID input form
- Error handling and validation feedback

#### SubAccountHeader
- Shows sub-account information with prominent "SUB-ACCOUNT" badge
- Displays location ID and account name
- Clear visual separation from agency mode
- No logout functionality (sub-accounts are embedded views)

#### SubAccountNavigation
- Limited navigation for sub-accounts
- Only shows Analytics and Automations tabs
- Automatically includes location_id in URLs

#### SubAccountLayout
- Wraps sub-account pages
- Provides consistent header and navigation
- Ensures proper layout structure

### Access Control

#### Sub-Account Restrictions
- Can only access Analytics, Automations, and Call Details pages
- All data is filtered by their specific `location_id`
- Cannot access Overview, Dashboard, Contacts, Calls, or Settings pages
- Cannot switch between different locations
- "Select Locations" dropdown is hidden and replaced with "Current Location" display
- Clear visual indicators (SUB-ACCOUNT badge) show restricted access mode

#### Agency Mode
- Full access to all features
- Can switch between locations
- Access to all pages and functionality

### Implementation Details

#### URL Parameter Handling
- `location_id` parameter triggers sub-account mode
- Parameter is validated against the API
- Invalid location IDs show authentication error

#### Data Filtering
- All API calls automatically include the sub-account's `location_id`
- Data is filtered at the API level for security
- Sub-accounts cannot access data from other locations

#### Session Persistence
- Valid location IDs are stored in localStorage
- Sessions persist across browser refreshes
- No logout functionality (sub-accounts are embedded views)

### Security Considerations

1. **API Validation**: All location IDs are validated server-side
2. **Data Isolation**: Sub-accounts can only access their own data
3. **URL Protection**: Invalid location IDs result in authentication failure
4. **Session Management**: Proper cleanup on logout

### Usage Examples

#### For Agencies (iFrame Integration)
```html
<iframe src="http://localhost:3000/analytics?location_id=GMCTanHIR07xDE3kvnpo" 
        width="100%" 
        height="600px">
</iframe>
```

#### For Sub-Account Direct Access
```
http://localhost:3000/analytics?location_id=GMCTanHIR07xDE3kvnpo
http://localhost:3000/automations?location_id=GMCTanHIR07xDE3kvnpo
```

### Configuration

The system uses the following environment variables:
- `VITE_CYCLSALES_APP_ID`: Application ID for API calls
- `VITE_API_BASE_URL`: Base URL for API endpoints

### Error Handling

- Invalid location IDs show authentication form
- Network errors display appropriate error messages
- Session expiration redirects to authentication
- API failures show user-friendly error messages
