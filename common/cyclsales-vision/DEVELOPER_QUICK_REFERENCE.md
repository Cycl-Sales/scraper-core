# CyclSales Vision - Developer Quick Reference

## Quick Start

### 1. Module Location
```
common/cyclsales-vision/
```

### 2. Key Files
- **Controllers**: `controllers/controllers.py` - Main API endpoints
- **AI Model**: `models/ai.py` - AI service configuration and processing
- **Usage Logging**: `models/ai_usage_log.py` - Request tracking
- **Triggers**: `models/trigger.py` - GHL workflow triggers

### 3. Main API Endpoints
```
POST /cs-vision-ai/call-summary          # GHL webhook receiver
POST /cs-vision/action-transcribe-call   # Main AI processing
POST /cs-vision/action-ai-call-summary   # Direct AI summary
POST /cs-vision/trigger-webhook          # Trigger management
```

## Core Models

### CyclSales Vision AI
```python
# Model: cyclsales.vision.ai
# Purpose: AI service configuration

# Key methods:
ai_service.generate_summary(
    transcript="call transcript text",
    custom_prompt="custom prompt",
    call_variables_returned=[1, 2, 3, 4, 5, 6],
    message_id="msg_123",
    contact_id="contact_456"
)
```

### AI Usage Log
```python
# Model: cyclsales.vision.ai.usage.log
# Purpose: Request tracking and analytics

# Key fields:
- location_id: Associated location
- ai_service_id: AI service used
- request_type: Type of request
- status: Request status
- input_tokens: Tokens consumed
- output_tokens: Tokens generated
- total_cost: Cost calculation
```

### GHL Workflow Trigger
```python
# Model: cyclsales.vision.trigger
# Purpose: GHL workflow trigger management

# Key fields:
- external_id: GHL trigger ID
- location_id: Associated location
- status: Trigger status (active/inactive)
- event_type: Trigger event type
```

## Call Variables Returned

### Values and Meanings
| Value | Field | Description |
|-------|-------|-------------|
| 1 | `sentiment` | Call sentiment analysis |
| 2 | `action_items` | Key action items |
| 3 | `confidence_score` | AI confidence score |
| 4 | `speakers_detected` | Number of speakers |
| 5 | `formatted_transcript` | Formatted transcript with timestamps |
| 6 | `call_url` | Call recording URL |

### Usage Example
```python
# Request only sentiment and formatted transcript
call_variables_returned = [1, 5]

# Request all fields
call_variables_returned = [1, 2, 3, 4, 5, 6]

# Backward compatibility (no parameter = all fields)
call_variables_returned = None
```

## API Request Examples

### Call Transcription Action
```json
{
    "cs_vision_ai_message_id": "msg_123456",
    "cs_vision_summary_prompt": "Please provide a summary of this call",
    "cs_vision_call_minimum_duration": 20,
    "call_variables_returned": [1, 2, 3, 4, 5, 6],
    "cs_vision_openai_api_key": "optional_custom_key"
}
```

### Response Format
```json
{
    "summary": "Call summary based on custom prompt",
    "keywords": ["keyword1", "keyword2", "keyword3"],
    "sentiment": "positive",
    "action_items": ["action1", "action2"],
    "confidence_score": 0.85,
    "duration_analyzed": "120 seconds",
    "speakers_detected": 2,
    "formatted_transcript": "Agent [00:00 - 00:15]: Hello...",
    "call_url": "https://app.gohighlevel.com/messages/msg_123456"
}
```

## Common Development Tasks

### 1. Add New AI Provider
```python
# In models/ai.py
model_type = fields.Selection([
    ('gpt-4o', 'GPT-4o'),
    ('gpt-4', 'GPT-4'),
    ('gpt-3.5-turbo', 'GPT-3.5 Turbo'),
    ('claude-3', 'Claude 3'),
    ('custom', 'Custom Model'),
    ('new-provider', 'New Provider')  # Add here
], string='Model Type', default='gpt-4o', required=True)
```

### 2. Add New Response Field
```python
# In controllers/controllers.py
# Add to additional_data processing
if new_field_requested:
    additional_data['new_field'] = generate_new_field()

# In models/ai.py
# Add to JSON structure
if new_field in call_variables_returned:
    json_fields.append('"new_field": "field_value"')
```

### 3. Create New API Endpoint
```python
# In controllers/controllers.py
@http.route('/cs-vision/new-endpoint', type='http', auth='none', methods=['POST'], cors='*', csrf=False)
def new_endpoint(self, **post):
    try:
        # Handle OPTIONS request for CORS
        if request.httprequest.method == 'OPTIONS':
            return Response(
                json.dumps({'status': 'ok'}),
                content_type='application/json',
                status=200,
                headers={'Access-Control-Allow-Origin': '*'}
            )
        
        # Process request
        data = json.loads(request.httprequest.data)
        
        # Your logic here
        
        return Response(
            json.dumps(result),
            content_type='application/json',
            status=200
        )
    except Exception as e:
        _logger.error(f"[New Endpoint] Error: {str(e)}", exc_info=True)
        return Response(
            json.dumps({'error': str(e)}),
            content_type='application/json',
            status=500
        )
```

### 4. Add New Model Field
```python
# In models/ai.py or other model files
new_field = fields.Char('New Field', help='Description of the field')
new_selection = fields.Selection([
    ('option1', 'Option 1'),
    ('option2', 'Option 2')
], string='New Selection', default='option1')
new_related = fields.Many2one('other.model', string='Related Record')
```

## Error Handling

### Common Error Codes
```python
# Standard error responses
{
    'error_code': 'error_type',
    'message': 'Human readable message',
    'details': 'Additional error details'
}

# Common error codes:
- 'invalid_json': Malformed request data
- 'missing_fields': Required fields missing
- 'message_not_found': Message ID not found
- 'no_transcript': No transcript available
- 'duration_too_short': Call below minimum duration
- 'ai_generation_failed': AI service error
```

### Logging Best Practices
```python
# Use structured logging
_logger.info(f"[Component] Action: {action} | Data: {data}")
_logger.warning(f"[Component] Warning: {warning_message}")
_logger.error(f"[Component] Error: {error_message}", exc_info=True)

# Log sensitive data carefully
_logger.info(f"[AI Service] API key (first 10 chars): {api_key[:10]}...")
```

## Testing

### Unit Test Example
```python
# tests/test_ai_service.py
from odoo.tests.common import TransactionCase

class TestAIService(TransactionCase):
    def setUp(self):
        super().setUp()
        self.ai_service = self.env['cyclsales.vision.ai'].create({
            'name': 'Test AI Service',
            'model_type': 'gpt-4o',
            'api_key': 'test_key',
            'is_active': True
        })
    
    def test_generate_summary(self):
        result = self.ai_service.generate_summary(
            transcript="Test transcript",
            custom_prompt="Test prompt"
        )
        self.assertIsNotNone(result)
        self.assertIn('summary', result)
```

### Integration Test Example
```python
# tests/test_controllers.py
from odoo.tests.common import HttpCase

class TestControllers(HttpCase):
    def test_call_transcription_endpoint(self):
        data = {
            "cs_vision_ai_message_id": "test_msg",
            "cs_vision_summary_prompt": "Test prompt",
            "cs_vision_call_minimum_duration": 20
        }
        
        response = self.url_open(
            '/cs-vision/action-transcribe-call',
            data=json.dumps(data),
            headers={'Content-Type': 'application/json'}
        )
        
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content)
        self.assertIn('summary', result)
```

## Performance Optimization

### 1. Token Usage Optimization
```python
# Reduce max_tokens for cost efficiency
max_tokens = 300  # Instead of 500

# Use conditional fields to reduce prompt size
if only_sentiment_needed:
    call_variables_returned = [1]  # Only sentiment
```

### 2. Caching
```python
# Consider caching for repeated requests
@tools.ormcache('message_id')
def get_cached_transcript(self, message_id):
    return self.env['ghl.contact.message.transcript'].search([
        ('message_id', '=', message_id)
    ])
```

### 3. Batch Processing
```python
# Process multiple requests in batch
def process_batch_calls(self, message_ids):
    results = []
    for message_id in message_ids:
        result = self.generate_summary(message_id=message_id)
        results.append(result)
    return results
```

## Security Considerations

### 1. API Key Management
```python
# Store API keys securely
api_key = fields.Char('API Key', password=True)  # Masked in UI

# Validate API keys
def validate_api_key(self, api_key):
    if not api_key or len(api_key) < 10:
        raise ValidationError("Invalid API key")
```

### 2. Input Validation
```python
# Validate all inputs
def validate_request_data(self, data):
    required_fields = ['message_id', 'summary_prompt']
    for field in required_fields:
        if field not in data:
            raise ValidationError(f"Missing required field: {field}")
```

### 3. Rate Limiting
```python
# Consider implementing rate limiting
def check_rate_limit(self, location_id):
    recent_requests = self.env['cyclsales.vision.ai.usage.log'].search([
        ('location_id', '=', location_id),
        ('create_date', '>=', fields.Datetime.now() - timedelta(minutes=1))
    ])
    
    if len(recent_requests) > 10:  # Max 10 requests per minute
        raise ValidationError("Rate limit exceeded")
```

## Deployment Checklist

### Pre-Deployment
- [ ] All tests passing
- [ ] API keys configured
- [ ] Error monitoring set up
- [ ] Performance benchmarks established
- [ ] Security review completed

### Post-Deployment
- [ ] Monitor error rates
- [ ] Track API usage
- [ ] Verify webhook endpoints
- [ ] Test AI service connectivity
- [ ] Check usage analytics

## Useful Commands

### Odoo Shell
```bash
# Access Odoo shell
./odoo-bin shell -d your_database

# Test AI service
ai_service = env['cyclsales.vision.ai'].search([('is_active', '=', True)], limit=1)
result = ai_service.generate_summary(transcript="Test transcript")
print(result)
```

### Database Queries
```sql
-- Check AI usage logs
SELECT 
    location_id,
    COUNT(*) as request_count,
    AVG(processing_duration) as avg_duration,
    SUM(total_cost) as total_cost
FROM cyclsales_vision_ai_usage_log 
WHERE create_date >= NOW() - INTERVAL '1 day'
GROUP BY location_id;

-- Check error rates
SELECT 
    status,
    COUNT(*) as count
FROM cyclsales_vision_ai_usage_log 
WHERE create_date >= NOW() - INTERVAL '1 hour'
GROUP BY status;
```

---

**Quick Reference Version**: 1.0  
**Last Updated**: 2024  
**For full documentation**: See `README.md`
