# OpenAI API Usage Logging Guide

## Overview

This guide explains how to ensure **ALL** OpenAI API calls in the web_scraper project are properly logged through the `cyclsales.vision.ai.usage.log` model for comprehensive tracking, billing, and analytics.

## Current Status

### ✅ Already Using Usage Logging:
1. **`cyclsales.vision.ai` model** - All calls through this model are automatically logged
2. **Call Summary Controller** - Updated to use AI service model with logging
3. **Vision AI Controller** - Updated to use AI service model with logging
4. **API Key Validation** - Updated to use AI service model with logging

### ❌ Previously NOT Using Usage Logging:
- Direct API calls in controllers (now fixed)
- API key validation calls (now fixed)

## Usage Logging System Components

### 1. AI Service Model (`cyclsales.vision.ai`)
- **Purpose**: Centralized AI service configuration and usage tracking
- **Location**: `custom/web_scraper/common/cyclsales-vision/models/ai.py`
- **Key Features**:
  - Usage count tracking
  - Error count tracking
  - Last used timestamp
  - Cost per token configuration

### 2. Usage Log Model (`cyclsales.vision.ai.usage.log`)
- **Purpose**: Detailed logging of every AI API call
- **Location**: `custom/web_scraper/common/cyclsales-vision/models/ai_usage_log.py`
- **Key Features**:
  - Token usage tracking (input/output/total)
  - Cost calculation
  - Request/response timing
  - Error tracking
  - Location and user association

## How to Ensure All API Calls Are Logged

### Method 1: Use the AI Service Model (Recommended)

For any new OpenAI API calls, use the existing AI service model:

```python
# Get the AI service
ai_service = request.env['cyclsales.vision.ai'].sudo().search([('is_active', '=', True)], limit=1)

# Use the generate_summary method (for text-based calls)
result = ai_service.generate_summary(
    message_id='your_message_id',
    contact_id='your_contact_id',
    transcript='your_text_content',
    custom_prompt='your_custom_prompt',
    custom_api_key='optional_custom_key',
    location_id='your_location_id'
)
```

### Method 2: Use the Utility Methods

For custom API calls that don't fit the standard pattern, use the utility methods:

```python
# For any OpenAI API call
ai_service_model = request.env['cyclsales.vision.ai'].sudo()

# Method 1: Use the wrapper function
def my_api_call():
    # Your OpenAI API call logic here
    response = requests.post('https://api.openai.com/v1/chat/completions', ...)
    return response.json()

result = ai_service_model.ensure_usage_logging(
    my_api_call,
    location_id='your_location_id',
    message_id='your_message_id',
    contact_id='your_contact_id',
    conversation_id='your_conversation_id',
    request_type='custom_call',
    custom_api_key='optional_custom_key'
)

# Method 2: Use the built-in API call method
result = ai_service_model.make_openai_api_call(
    endpoint='/chat/completions',
    method='POST',
    data={
        'model': 'gpt-4o',
        'messages': [{'role': 'user', 'content': 'Hello'}],
        'max_tokens': 100
    },
    location_id='your_location_id',
    message_id='your_message_id',
    contact_id='your_contact_id',
    conversation_id='your_conversation_id',
    request_type='custom_call',
    custom_api_key='optional_custom_key'
)
```

### Method 3: Manual Usage Log Creation

For edge cases where you need full control:

```python
# Create usage log entry
usage_log = request.env['cyclsales.vision.ai.usage.log'].sudo().create_usage_log(
    location_id='your_location_id',
    ai_service_id=ai_service.id,
    request_type='your_request_type',
    message_id='your_message_id',
    contact_id='your_contact_id',
    conversation_id='your_conversation_id'
)

# Update status to processing
usage_log.write({'status': 'processing'})

try:
    # Make your OpenAI API call
    response = requests.post('https://api.openai.com/v1/chat/completions', ...)
    result = response.json()
    
    # Update usage log with success
    if 'usage' in result:
        usage = result['usage']
        usage_log.write({
            'input_tokens': usage.get('prompt_tokens', 0),
            'output_tokens': usage.get('completion_tokens', 0),
            'response_length': len(result['choices'][0]['message']['content'])
        })
    
    usage_log.update_success(result)
    
except Exception as e:
    # Update usage log with failure
    usage_log.update_failure(str(e), "EXCEPTION")
    raise
```

## Request Types for Logging

Use these standardized request types when creating usage logs:

- `call_summary` - Call transcript analysis
- `transcript_analysis` - General transcript analysis
- `contact_analysis` - Contact-related analysis
- `custom_prompt` - Custom prompt requests
- `test_connection` - API key validation
- `vision_analysis` - Image/PDF analysis
- `other` - Any other type

## Best Practices

### 1. Always Include Location ID
```python
location_id = data.get('location_id', 'unknown')
```

### 2. Use Meaningful Message IDs
```python
message_id = f"call_summary_{contact_id}_{timestamp}"
```

### 3. Handle Errors Gracefully
```python
try:
    result = ai_service.generate_summary(...)
except Exception as e:
    _logger.error(f"AI call failed: {str(e)}")
    # Return fallback response
```

### 4. Monitor Usage Logs
Regularly check the usage logs for:
- Failed requests
- High token usage
- Cost anomalies
- Performance issues

## Monitoring and Analytics

### View Usage Logs
- **Menu**: CyclSales Vision → AI Usage Logs
- **Filters**: By location, date, status, request type
- **Reports**: Cost analysis, usage trends, error rates

### Key Metrics to Track
- Total API calls per day/week/month
- Success/failure rates
- Average token usage per call
- Cost per location/user
- Response times

### Alerts to Set Up
- High error rates (>5%)
- Unusual token usage spikes
- API key validation failures
- Cost threshold exceeded

## Troubleshooting

### Common Issues

1. **Usage Log Creation Fails**
   - Check if AI service exists and is active
   - Verify location_id is valid
   - Ensure proper permissions

2. **Token Count Mismatch**
   - Verify OpenAI API response includes usage data
   - Check if response parsing is correct
   - Validate token calculation logic

3. **Cost Calculation Errors**
   - Verify cost_per_1k_tokens is set correctly
   - Check if total_tokens is calculated properly
   - Validate decimal precision

### Debug Mode
Enable debug logging to see detailed usage tracking:

```python
_logger.setLevel(logging.DEBUG)
```

## Migration Checklist

For existing code that makes direct OpenAI API calls:

- [ ] Identify all direct `requests.post()` calls to OpenAI endpoints
- [ ] Replace with AI service model calls or utility methods
- [ ] Add proper error handling and logging
- [ ] Test with usage logging enabled
- [ ] Verify cost tracking is accurate
- [ ] Update documentation

## Example Migration

### Before (Direct API Call):
```python
response = requests.post(
    'https://api.openai.com/v1/chat/completions',
    headers={'Authorization': f'Bearer {api_key}'},
    json={'model': 'gpt-4o', 'messages': [...]}
)
```

### After (With Usage Logging):
```python
ai_service = request.env['cyclsales.vision.ai'].sudo().search([('is_active', '=', True)], limit=1)
result = ai_service.generate_summary(
    message_id=message_id,
    contact_id=contact_id,
    transcript=transcript_text,
    location_id=location_id
)
```

## Conclusion

By following this guide and using the provided utility methods, you can ensure that **every single OpenAI API call** in the web_scraper project is properly logged, tracked, and billed. This provides comprehensive visibility into AI usage patterns, costs, and performance across all locations and users.
