# CyclSales Application Model

## Overview

The `cyclsales.application` model is designed to manage Go High Level (GHL) marketplace applications that your company has registered. This model allows you to manually register and manage each GHL application with its associated OAuth credentials and tokens.

## Model Fields

### Required Fields
- **App Name** (`name`): The name of the GHL marketplace application
- **Client ID** (`client_id`): OAuth Client ID for the application
- **Client Secret** (`client_secret`): OAuth Client Secret for the application  
- **App ID** (`app_id`): GHL Application ID

### Optional Fields
- **Access Token** (`access_token`): Current access token for the application
- **Refresh Token** (`refresh_token`): Refresh token for token renewal
- **Token Expiry** (`token_expiry`): When the current access token expires
- **Active** (`is_active`): Whether this application is currently active
- **Notes** (`notes`): Additional notes about this application

### Computed Fields
- **Token Status** (`token_status`): Automatically computed status of the access token
  - `valid`: Token exists and is not expired
  - `expired`: Token exists but has expired
  - `missing`: No token is set

### System Fields
- **Created On** (`create_date`): When the record was created
- **Last Updated** (`write_date`): When the record was last modified

## Features

### Validation
- **Unique Constraints**: Client ID and App ID must be unique across all applications
- **Token Status**: Automatic computation of token validity status

### Actions
- **Refresh Token**: Button to refresh the access token (placeholder for future implementation)
- **Test Connection**: Button to test the application connection (placeholder for future implementation)
- **Toggle Active**: Archive/unarchive applications

### Views
- **List View**: Shows applications with color-coded decorations based on status
- **Form View**: Detailed view with grouped fields and action buttons
- **Search View**: Advanced search with filters for active status and token status

## Usage

### Creating a New Application
1. Navigate to **Zillow Properties > Configurations > GHL Applications**
2. Click **Create** button
3. Fill in the required fields:
   - App Name
   - Client ID
   - Client Secret
   - App ID
4. Optionally add access tokens and notes
5. Save the record

### Managing Applications
- Use the list view to see all applications with their status
- Click on an application to view/edit details
- Use the action buttons to refresh tokens or test connections
- Archive inactive applications using the toggle button

### Security
- Regular users can only read application records
- System administrators can create, edit, and delete applications
- Sensitive fields (client secret, access token, refresh token) are masked in the UI

## Integration

This model is designed to work with the existing GHL integration in your web_scraper module. It can be extended to:

- Automatically refresh tokens when they expire
- Test connections to GHL APIs
- Store and manage multiple application credentials
- Integrate with OAuth flows for different applications

## Sample Data

The module includes sample data for testing:
- CyclSales Dashboard
- CyclSales Web Scraper  
- CyclSales Analytics (inactive)

## Future Enhancements

Potential improvements for this model:
- Automatic token refresh functionality
- API connection testing
- Integration with GHL webhook handling
- Token encryption for enhanced security
- Audit logging for credential changes 