# CyclSales Vision AI Integration Module

## Overview

The CyclSales Vision AI Integration module is an Odoo 18-compliant system that provides AI-powered call summarization and workflow automation for Go High Level (GHL) integration. This module enables intelligent processing of phone calls, automatic transcription analysis, and customizable AI responses.

## Table of Contents

1. [Module Structure](#module-structure)
2. [Core Features](#core-features)
3. [Installation & Setup](#installation--setup)
4. [Configuration](#configuration)
5. [API Endpoints](#api-endpoints)
6. [Models & Data Structure](#models--data-structure)
7. [Usage Examples](#usage-examples)
8. [Troubleshooting](#troubleshooting)
9. [Development Guide](#development-guide)

## Module Structure

```
cyclsales-vision/
├── __init__.py                 # Module initialization
├── __manifest__.py            # Module manifest and dependencies
├── controllers/               # API endpoints and web controllers
│   ├── __init__.py
│   ├── controllers.py         # Main API endpoints
│   ├── oauth_controller.py    # OAuth handling
│   ├── sample_controller.py   # Sample endpoints
│   └── trigger_controller.py  # Workflow trigger handling
├── models/                    # Data models and business logic
│   ├── __init__.py
│   ├── ai.py                  # AI service configuration
│   ├── ai_usage_log.py        # Usage tracking and analytics
│   ├── models.py              # Base models (placeholder)
│   └── trigger.py             # GHL workflow triggers
├── views/                     # Odoo UI views
│   ├── ai_views.xml           # AI service management UI
│   ├── ai_usage_log_views.xml # Usage analytics UI
│   ├── trigger_views.xml      # Trigger management UI
│   ├── templates.xml          # Web templates
│   └── views.xml              # Base views
├── data/                      # Initial data and configurations
│   └── ai_service_data.xml    # Default AI service configuration
├── security/                  # Access control and permissions
│   └── ir.model.access.csv    # Model access rights
└── static/                    # Static assets (if any)
```

## Core Features

### 🤖 AI-Powered Call Analysis
- **Multi-Provider Support**: OpenAI GPT-4o, GPT-4, GPT-3.5, Claude 3
- **Custom Prompts**: Configurable prompt templates for different use cases
- **Conditional Fields**: Granular control over AI response fields
- **Cost Tracking**: Per-token billing and usage analytics

### 🔗 GHL Integration
- **Webhook Processing**: Receives and processes GHL call-completed events
- **Workflow Actions**: Custom actions for GHL workflows
- **Multi-Location Support**: Tenant-aware processing
- **Trigger Management**: Dynamic workflow trigger configuration

### 📞 Call Processing
- **Duration Validation**: Minimum call duration thresholds
- **Transcript Analysis**: AI-powered call summarization
- **Formatted Transcripts**: Human-readable transcripts with timestamps
- **Call URL Retrieval**: Direct access to call recordings

### 📊 Analytics & Monitoring
- **Usage Logging**: Comprehensive request tracking
- **Performance Metrics**: Response times and success rates
- **Error Tracking**: Detailed error logging and monitoring
- **Cost Analytics**: Token usage and billing information

## Installation & Setup

### Prerequisites
- Odoo 18.0 or higher
- `web_scraper` module installed
- `cs-dashboard-backend` module installed
- Valid OpenAI API key (or other AI provider)

### Installation Steps

1. **Install the Module**
   ```bash
   # Copy the module to your Odoo addons directory
   cp -r cyclsales-vision /path/to/odoo/addons/
   
   # Update the addons list in Odoo
   # Go to Apps > Update Apps List
   ```

2. **Install via Odoo Interface**
   - Navigate to **Apps** in Odoo
   - Search for "CyclSales Vision AI Integration"
   - Click **Install**

3. **Configure AI Service**
   - Go to **CyclSales Vision > AI Services**
   - Create or edit the default AI service
   - Enter your API key and configuration

### Initial Configuration

1. **AI Service Setup**
   ```
   Navigation: CyclSales Vision > AI Services
   
   Required Fields:
   - Name: Service identifier
   - Model Type: Choose AI provider (GPT-4o recommended)
   - API Key: Your OpenAI API key
   - Base URL: https://api.openai.com/v1 (default)
   - Max Tokens: 500 (default)
   - Temperature: 0.3 (default)
   ```

2. **Access Rights**
   - The module automatically sets up access rights
   - System administrators have full access
   - Regular users have read/write access to usage logs
   - Portal users have read-only access

## Configuration

### AI Service Configuration

#### Supported Models
- **GPT-4o**: Latest OpenAI model (recommended)
- **GPT-4**: High-performance model
- **GPT-3.5 Turbo**: Cost-effective option
- **Claude 3**: Anthropic's model
- **Custom**: Custom model endpoints

#### Configuration Parameters
- **API Key**: Authentication token for AI service
- **Base URL**: API endpoint URL
- **Max Tokens**: Maximum response length
- **Temperature**: Creativity level (0.0-1.0)
- **Cost per 1K Tokens**: For billing calculations

#### Prompt Templates
Customize the AI prompt template for different use cases:

```json
{
    "summary": "<custom prompt text>",
    "keywords": ["keyword1", "keyword2", "keyword3"],
    "sentiment": "positive|negative|neutral",
    "action_items": ["action1", "action2", "action3"],
    "confidence_score": 0.85,
    "duration_analyzed": "calculated from transcript",
    "speakers_detected": "count from transcript"
}
```

### GHL Integration Setup

1. **Webhook Configuration**
   - Configure GHL webhooks to point to your Odoo instance
   - Endpoint: `/cs-vision-ai/call-summary`
   - Method: POST
   - Content-Type: application/json

2. **Workflow Triggers**
   - Set up GHL workflow triggers for call events
   - Configure custom actions to call `/cs-vision/action-transcribe-call`
   - Include required parameters in workflow actions

## API Endpoints

### 1. Call Summary Webhook
**Endpoint**: `/cs-vision-ai/call-summary`
**Method**: POST
**Purpose**: Receives GHL call-completed webhooks

**Request Format**:
```json
{
    "messageType": "CALL",
    "messageId": "msg_123456",
    "contactId": "contact_789",
    "direction": "inbound",
    "callDuration": 120,
    "locationId": "loc_456",
    "attachments": ["recording_url"]
}
```

**Response**:
```json
{
    "status": "processed",
    "message": "Call processed successfully"
}
```

### 2. Call Transcription Action
**Endpoint**: `/cs-vision/action-transcribe-call`
**Method**: POST
**Purpose**: Processes call transcription with AI analysis

**Request Format**:
```json
{
    "cs_vision_ai_message_id": "msg_123456",
    "cs_vision_summary_prompt": "Please provide a summary of this call",
    "cs_vision_call_minimum_duration": 20,
    "call_variables_returned": [1, 2, 3, 4, 5, 6],
    "cs_vision_openai_api_key": "optional_custom_key"
}
```

**Response**:
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

### 3. AI Call Summary
**Endpoint**: `/cs-vision/action-ai-call-summary`
**Method**: POST
**Purpose**: Direct AI summary generation

**Request Format**:
```json
{
    "message_id": "msg_123456",
    "contact_id": "contact_789",
    "conversation_id": "conv_123",
    "location_id": "loc_456",
    "cs_vision_openai_api_key": "optional_custom_key"
}
```

### 4. Trigger Webhook
**Endpoint**: `/cs-vision/trigger-webhook`
**Method**: POST
**Purpose**: Manages GHL workflow triggers

## Models & Data Structure

### CyclSales Vision AI (`cyclsales.vision.ai`)

**Purpose**: Manages AI service configurations

**Key Fields**:
- `name`: Service identifier
- `model_type`: AI model selection
- `api_key`: Authentication token
- `base_url`: API endpoint
- `max_tokens`: Response length limit
- `temperature`: Creativity setting
- `is_active`: Service status
- `usage_count`: Total requests
- `error_count`: Error tracking
- `default_prompt_template`: Custom prompt template

### AI Usage Log (`cyclsales.vision.ai.usage.log`)

**Purpose**: Tracks all AI requests and performance

**Key Fields**:
- `location_id`: Associated location
- `ai_service_id`: AI service used
- `request_type`: Type of request
- `status`: Request status
- `input_tokens`: Tokens consumed
- `output_tokens`: Tokens generated
- `total_cost`: Cost calculation
- `processing_duration`: Response time
- `error_message`: Error details

### GHL Workflow Trigger (`cyclsales.vision.trigger`)

**Purpose**: Manages GHL workflow triggers

**Key Fields**:
- `external_id`: GHL trigger ID
- `location_id`: Associated location
- `status`: Trigger status
- `event_type`: Trigger event type
- `target_url`: Webhook URL
- `trigger_count`: Usage tracking

## Usage Examples

### Basic Call Processing

1. **GHL sends webhook** when call completes
2. **Module validates** call duration and location
3. **Workflow triggers** custom action
4. **AI processes** transcript and generates summary
5. **Results returned** to GHL workflow

### Custom Field Selection

Use `call_variables_returned` to control response fields:

```json
// Request only sentiment and keywords
{
    "call_variables_returned": [1]
}

// Request formatted transcript and call URL
{
    "call_variables_returned": [5, 6]
}

// Request all fields
{
    "call_variables_returned": [1, 2, 3, 4, 5, 6]
}
```

### Custom Prompts

Configure different prompts for different use cases:

```json
{
    "cs_vision_summary_prompt": "Focus on pricing discussions and customer objections"
}
```

### Multi-Location Support

Each location can have its own:
- AI service configuration
- Usage tracking
- Workflow triggers
- Custom prompts

## Troubleshooting

### Common Issues

#### 1. AI Service Not Responding
**Symptoms**: 500 errors, timeout responses
**Solutions**:
- Check API key validity
- Verify base URL configuration
- Check network connectivity
- Review error logs in AI Usage Log

#### 2. Missing Transcript Data
**Symptoms**: "No transcript available" errors
**Solutions**:
- Verify GHL transcript settings
- Check message ID validity
- Ensure call duration meets minimum threshold
- Review transcript record creation

#### 3. Workflow Triggers Not Firing
**Symptoms**: No AI processing for calls
**Solutions**:
- Verify trigger status is "active"
- Check location association
- Review webhook configuration
- Validate trigger permissions

#### 4. High Token Usage
**Symptoms**: Unexpected costs
**Solutions**:
- Reduce max_tokens setting
- Optimize prompt templates
- Use conditional fields
- Monitor usage analytics

### Debugging Steps

1. **Check Logs**
   ```
   Navigation: CyclSales Vision > AI Usage Log
   Filter by: Status = Failed
   Review: Error messages and request details
   ```

2. **Test AI Service**
   ```
   Navigation: CyclSales Vision > AI Services
   Action: Test Connection
   Verify: API response and configuration
   ```

3. **Monitor Performance**
   ```
   Navigation: CyclSales Vision > AI Usage Log
   Analyze: Processing duration, success rates
   Identify: Performance bottlenecks
   ```

### Error Codes

| Code | Description | Solution |
|------|-------------|----------|
| `invalid_json` | Malformed request data | Check JSON syntax |
| `missing_fields` | Required fields missing | Verify request parameters |
| `message_not_found` | Message ID not found | Check GHL message ID |
| `no_transcript` | No transcript available | Verify transcript data |
| `duration_too_short` | Call below minimum duration | Adjust duration threshold |
| `ai_generation_failed` | AI service error | Check AI configuration |

## Development Guide

### Adding New AI Providers

1. **Update Model Selection**
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

2. **Update API Configuration**
   ```python
   # Add provider-specific configuration
   if self.model_type == 'new-provider':
       base_url = 'https://api.newprovider.com/v1'
       headers = {'Authorization': f'Bearer {api_key}'}
   ```

### Extending Response Fields

1. **Update Prompt Template**
   ```python
   # Add new field to JSON structure
   json_fields.append('"new_field": "field_value"')
   ```

2. **Update Response Processing**
   ```python
   # Handle new field in response
   if 'new_field' in ai_summary:
       result['new_field'] = ai_summary['new_field']
   ```

### Custom Workflow Actions

1. **Create New Controller Method**
   ```python
   @http.route('/cs-vision/custom-action', type='http', auth='none', methods=['POST'])
   def custom_action(self, **post):
       # Custom logic here
       pass
   ```

2. **Add to Trigger Processing**
   ```python
   # In trigger.py
   def execute_custom_action(self, trigger_data):
       # Custom action execution
       pass
   ```

### Testing

1. **Unit Tests**
   ```python
   # Create test files in tests/ directory
   def test_ai_service_creation(self):
       # Test AI service creation
       pass
   ```

2. **Integration Tests**
   ```python
   # Test API endpoints
   def test_call_summary_endpoint(self):
       # Test webhook processing
       pass
   ```

### Deployment

1. **Production Checklist**
   - [ ] Set up proper API keys
   - [ ] Configure error monitoring
   - [ ] Set up usage alerts
   - [ ] Test all endpoints
   - [ ] Verify security settings

2. **Monitoring**
   - [ ] Set up log aggregation
   - [ ] Configure performance alerts
   - [ ] Monitor API usage
   - [ ] Track error rates

## Support & Maintenance

### Regular Maintenance Tasks

1. **Monitor Usage Logs**
   - Review error patterns
   - Track performance metrics
   - Monitor cost trends

2. **Update AI Configurations**
   - Review model performance
   - Update prompt templates
   - Optimize token usage

3. **Security Reviews**
   - Rotate API keys
   - Review access permissions
   - Audit usage patterns

### Getting Help

- **Documentation**: This README and inline code comments
- **Logs**: Check AI Usage Log for detailed error information
- **Odoo Community**: Post questions in Odoo forums
- **GitHub Issues**: Report bugs and feature requests

---

**Version**: 1.0  
**Last Updated**: 2024  
**Compatibility**: Odoo 18.0+  
**License**: LGPL-3
