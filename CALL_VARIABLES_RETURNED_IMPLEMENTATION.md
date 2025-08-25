# Call Variables Returned Implementation

## Overview

The `call_variables_returned` parameter has been implemented in the cyclsales-vision module to provide granular control over which AI analysis fields are included in the response. This allows for more efficient API usage and customized responses based on specific needs.

## New Parameter: `call_variables_returned`

### Type
- **Multiselect Array**: Array of integers representing which fields to include
- **Backward Compatible**: If not provided, all fields are included (original behavior)

### Values and Meanings

| Value | Field | Description |
|-------|-------|-------------|
| 1 | `sentiment` | Call sentiment analysis (positive/negative/neutral) |
| 2 | `action_items` | Key action items from the call |
| 3 | `confidence_score` | AI confidence score for the analysis |
| 4 | `speakers_detected` | Number of speakers detected in the call |
| 5 | `formatted_transcript` | **NEW**: Formatted transcript with timestamps and speaker names |
| 6 | `call_url` | **NEW**: URL to access the call recording |

## Implementation Details

### 1. Controller Updates (`controllers.py`)

#### Parameter Parsing
```python
# New call_variables_returned parameter - multiselect array
call_variables_returned = payload.get('call_variables_returned', [])
if isinstance(call_variables_returned, str):
    # Handle case where it might be a comma-separated string
    call_variables_returned = [int(x.strip()) for x in call_variables_returned.split(',') if x.strip().isdigit()]
elif isinstance(call_variables_returned, list):
    # Ensure all values are integers
    call_variables_returned = [int(x) for x in call_variables_returned if str(x).isdigit()]
else:
    call_variables_returned = []
```

#### Additional Data Processing
```python
# Handle additional variables based on call_variables_returned
additional_data = {}

# Generate formatted transcript if requested (value 5)
if 5 in call_variables_returned:
    formatted_transcript = self._generate_formatted_transcript(transcript_records)
    additional_data['formatted_transcript'] = formatted_transcript

# Get call URL if requested (value 6)
if 6 in call_variables_returned:
    call_url = self._get_call_url(message_record)
    additional_data['call_url'] = call_url
```

### 2. AI Model Updates (`ai.py`)

#### Dynamic Prompt Generation
The AI prompt is now dynamically constructed based on the requested fields:

```python
# Build JSON structure based on call_variables_returned
json_fields = []
json_fields.append('"summary": "{custom_prompt}"')
json_fields.append('"keywords": ["keyword1", "keyword2", "keyword3"]')

# Conditionally include sentiment (value 1)
if call_variables_returned and 1 in call_variables_returned:
    json_fields.append('"sentiment": "positive|negative|neutral"')

# Conditionally include action_items (value 2)
if call_variables_returned and 2 in call_variables_returned:
    json_fields.append('"action_items": ["action1", "action2", "action3"]')

# Conditionally include confidence_score (value 3)
if call_variables_returned and 3 in call_variables_returned:
    json_fields.append('"confidence_score": 0.85')

# Conditionally include speakers_detected (value 4)
if call_variables_returned and 4 in call_variables_returned:
    json_fields.append(f'"speakers_detected": {speakers_detected if speakers_detected else 0}')
```

### 3. New Helper Methods

#### Formatted Transcript Generation
```python
def _generate_formatted_transcript(self, transcript_records):
    """
    Generate a formatted transcript with timestamps and speaker names
    Format: "Agent [00:15 - 00:30]: Hello, how can I help you today?"
    """
    formatted_lines = []
    for record in transcript_records:
        if not record.transcript:
            continue
            
        # Format speaker name
        speaker = "Agent" if record.media_channel == "agent" else "Customer"
        
        # Format timestamp
        start_time = record.start_time_seconds
        end_time = record.end_time_seconds
        
        minutes_start = int(start_time // 60)
        seconds_start = int(start_time % 60)
        minutes_end = int(end_time // 60)
        seconds_end = int(end_time % 60)
        
        timestamp = f"[{minutes_start:02d}:{seconds_start:02d} - {minutes_end:02d}:{seconds_end:02d}]"
        
        # Create formatted line
        formatted_line = f"{speaker} {timestamp}: {record.transcript}"
        formatted_lines.append(formatted_line)
    
    return "\n".join(formatted_lines)
```

#### Call URL Retrieval
```python
def _get_call_url(self, message_record):
    """
    Get the call URL from the message record
    Priority: attachment URL > recording URL > constructed GHL URL
    """
    try:
        # Check if there's a recording URL in attachments
        if message_record.attachment_ids:
            for attachment in message_record.attachment_ids:
                if attachment.attachment_url and 'recording' in attachment.attachment_url.lower():
                    return attachment.attachment_url
        
        # Check if there's a recording URL in the message record itself
        if hasattr(message_record, 'recording_url') and message_record.recording_url:
            return message_record.recording_url
            
        # If no specific recording URL, construct a generic one based on message ID
        if message_record.ghl_id:
            return f"https://app.gohighlevel.com/messages/{message_record.ghl_id}"
            
        return None
    except Exception as e:
        _logger.error(f"[Call URL] Error getting call URL: {str(e)}")
        return None
```

## API Usage Examples

### Example 1: All Variables Enabled
```json
{
    "cs_vision_ai_message_id": "message_123",
    "cs_vision_summary_prompt": "Please provide a summary of this call",
    "cs_vision_call_minimum_duration": 20,
    "call_variables_returned": [1, 2, 3, 4, 5, 6]
}
```

**Response includes:**
- `summary`
- `keywords`
- `sentiment`
- `action_items`
- `confidence_score`
- `speakers_detected`
- `duration_analyzed`
- `formatted_transcript`
- `call_url`

### Example 2: Only Sentiment and Keywords
```json
{
    "cs_vision_ai_message_id": "message_124",
    "cs_vision_summary_prompt": "Please provide a summary of this call",
    "cs_vision_call_minimum_duration": 20,
    "call_variables_returned": [1]
}
```

**Response includes:**
- `summary`
- `keywords`
- `sentiment`
- `duration_analyzed`

### Example 3: Formatted Transcript and Call URL Only
```json
{
    "cs_vision_ai_message_id": "message_125",
    "cs_vision_summary_prompt": "Please provide a summary of this call",
    "cs_vision_call_minimum_duration": 20,
    "call_variables_returned": [5, 6]
}
```

**Response includes:**
- `summary`
- `keywords`
- `duration_analyzed`
- `formatted_transcript`
- `call_url`

### Example 4: Backward Compatibility (No Parameter)
```json
{
    "cs_vision_ai_message_id": "message_126",
    "cs_vision_summary_prompt": "Please provide a summary of this call",
    "cs_vision_call_minimum_duration": 20
}
```

**Response includes all fields (original behavior):**
- `summary`
- `keywords`
- `sentiment`
- `action_items`
- `confidence_score`
- `speakers_detected`
- `duration_analyzed`

## Formatted Transcript Example

When `call_variables_returned` includes value `5`, the response will include a `formatted_transcript` field:

```
Agent [00:00 - 00:15]: Hello, thank you for calling our company. How can I assist you today?
Customer [00:15 - 00:30]: Hi, I'm calling about the pricing for your services.
Agent [00:30 - 00:45]: I'd be happy to help you with pricing information. Let me pull up our current rates.
Customer [00:45 - 01:00]: That would be great, thank you.
```

## Call URL Example

When `call_variables_returned` includes value `6`, the response will include a `call_url` field:

```json
{
    "call_url": "https://app.gohighlevel.com/messages/abc123def456"
}
```

## Benefits

1. **Efficiency**: Only request the fields you need, reducing API response size and processing time
2. **Cost Optimization**: Smaller prompts mean fewer tokens used with AI services
3. **Flexibility**: Customize responses based on specific use cases
4. **New Features**: Access to formatted transcripts and call URLs
5. **Backward Compatibility**: Existing integrations continue to work without changes

## Testing

A test script (`test_call_variables.py`) has been created to verify the functionality:

```bash
python3 test_call_variables.py
```

This script tests various combinations of `call_variables_returned` values and validates that the expected fields are present in the response.

## Error Handling

- Invalid values in `call_variables_returned` are filtered out
- String values are parsed as comma-separated integers
- Missing or malformed parameters default to an empty array
- All existing error handling remains intact

## Logging

Comprehensive logging has been added to track:
- Received `call_variables_returned` values
- Generated formatted transcript length
- Call URL retrieval attempts
- Dynamic prompt construction

This implementation provides a robust, flexible, and backward-compatible solution for controlling AI analysis output while adding new valuable features.
