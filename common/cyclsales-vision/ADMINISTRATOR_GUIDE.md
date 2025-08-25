# CyclSales Vision - Administrator Guide

## Overview

This guide is designed for system administrators who need to install, configure, and maintain the CyclSales Vision AI Integration module in their Odoo environment.

## Table of Contents

1. [Installation](#installation)
2. [Initial Configuration](#initial-configuration)
3. [AI Service Management](#ai-service-management)
4. [GHL Integration Setup](#ghl-integration-setup)
5. [User Management](#user-management)
6. [Monitoring & Maintenance](#monitoring--maintenance)
7. [Troubleshooting](#troubleshooting)
8. [Security Best Practices](#security-best-practices)

## Installation

### Prerequisites

Before installing the CyclSales Vision module, ensure you have:

- **Odoo 18.0** or higher installed
- **Python 3.8+** with required dependencies
- **PostgreSQL** database
- **Valid OpenAI API key** (or other AI provider)
- **GHL account** with API access
- **SSL certificate** for production (recommended)

### Installation Steps

#### 1. Module Installation

**Option A: Manual Installation**
```bash
# Copy module to Odoo addons directory
sudo cp -r cyclsales-vision /opt/odoo/addons/

# Set proper permissions
sudo chown -R odoo:odoo /opt/odoo/addons/cyclsales-vision
sudo chmod -R 755 /opt/odoo/addons/cyclsales-vision

# Restart Odoo service
sudo systemctl restart odoo
```

**Option B: Git Installation**
```bash
# Clone the repository
git clone https://github.com/your-repo/scraper-core.git
cd scraper-core/common/cyclsales-vision

# Create symbolic link
sudo ln -s $(pwd) /opt/odoo/addons/cyclsales-vision
```

#### 2. Database Installation

1. **Access Odoo Interface**
   - Navigate to your Odoo instance
   - Go to **Apps** menu
   - Click **Update Apps List**

2. **Install Module**
   - Search for "CyclSales Vision AI Integration"
   - Click **Install**
   - Wait for installation to complete

3. **Verify Installation**
   - Check **Apps** menu for "CyclSales Vision"
   - Verify no error messages in logs

### Post-Installation Verification

```bash
# Check Odoo logs for errors
sudo tail -f /var/log/odoo/odoo.log | grep -i "cyclsales\|vision"

# Verify module is loaded
./odoo-bin shell -d your_database -c /etc/odoo/odoo.conf
>>> env['cyclsales.vision.ai'].search([])
```

## Initial Configuration

### 1. AI Service Configuration

#### Create Default AI Service

1. **Navigate to AI Services**
   ```
   Apps > CyclSales Vision > AI Services
   ```

2. **Create New Service**
   ```
   Click "Create" button
   
   Fill in required fields:
   - Name: "Default OpenAI Service"
   - Model Type: "GPT-4o" (recommended)
   - API Key: Your OpenAI API key
   - Base URL: https://api.openai.com/v1
   - Max Tokens: 500
   - Temperature: 0.3
   - Cost per 1K Tokens: 0.03
   - Active: ✓
   ```

3. **Test Connection**
   ```
   Click "Test Connection" button
   Verify successful response
   ```

#### API Key Management

**Security Best Practices:**
- Store API keys securely
- Use environment variables in production
- Rotate keys regularly
- Monitor usage for anomalies

```bash
# Set environment variable (recommended for production)
export OPENAI_API_KEY="your-api-key-here"

# Add to system environment
echo 'export OPENAI_API_KEY="your-api-key-here"' >> ~/.bashrc
source ~/.bashrc
```

### 2. Access Rights Configuration

The module automatically creates access rights, but you may need to customize them:

#### Default Access Rights
- **System Administrators**: Full access to all models
- **Regular Users**: Read/write access to usage logs
- **Portal Users**: Read-only access to usage logs

#### Customizing Access Rights

1. **Navigate to Settings**
   ```
   Settings > Users & Companies > Users
   ```

2. **Edit User Groups**
   ```
   Select user > Edit > Access Rights tab
   Add/remove CyclSales Vision permissions
   ```

3. **Create Custom Groups** (if needed)
   ```
   Settings > Users & Companies > Groups
   Create new group with specific permissions
   ```

### 3. System Parameters

#### Recommended System Parameters

```python
# Set via Odoo interface: Settings > Technical > Parameters > System Parameters

# AI Service Configuration
cyclsales.vision.default_model = gpt-4o
cyclsales.vision.max_tokens = 500
cyclsales.vision.temperature = 0.3

# Call Processing
cyclsales.vision.min_call_duration = 20
cyclsales.vision.webhook_timeout = 30

# Monitoring
cyclsales.vision.enable_detailed_logging = True
cyclsales.vision.alert_on_errors = True
```

## AI Service Management

### 1. Multiple AI Providers

#### Setting Up Multiple Services

1. **Create Additional Services**
   ```
   CyclSales Vision > AI Services > Create
   
   Service 1: OpenAI GPT-4o (Primary)
   Service 2: Claude 3 (Backup)
   Service 3: GPT-3.5 Turbo (Cost-effective)
   ```

2. **Configure Load Balancing**
   ```python
   # In production, implement service rotation
   active_services = env['cyclsales.vision.ai'].search([
       ('is_active', '=', True),
       ('status', '=', 'active')
   ])
   
   # Round-robin selection
   selected_service = active_services[request_count % len(active_services)]
   ```

#### Service Monitoring

**Key Metrics to Monitor:**
- Response times
- Success rates
- Error rates
- Token usage
- Cost per request

**Setting Up Alerts:**
```python
# Monitor error rates
error_threshold = 0.05  # 5% error rate
recent_errors = env['cyclsales.vision.ai.usage.log'].search([
    ('status', '=', 'failed'),
    ('create_date', '>=', fields.Datetime.now() - timedelta(hours=1))
])

if len(recent_errors) / total_requests > error_threshold:
    # Send alert
    send_alert_email("High error rate detected")
```

### 2. Cost Management

#### Token Usage Optimization

1. **Monitor Usage**
   ```
   CyclSales Vision > AI Usage Log
   Filter by: Date range, Location, Status
   ```

2. **Optimize Settings**
   ```
   Reduce max_tokens for shorter responses
   Use conditional fields to reduce prompt size
   Implement caching for repeated requests
   ```

3. **Set Usage Limits**
   ```python
   # Implement daily/monthly limits
   daily_limit = 1000  # requests per day
   monthly_budget = 100  # dollars per month
   
   # Check limits before processing
   if daily_requests > daily_limit:
       raise ValidationError("Daily limit exceeded")
   ```

#### Billing Configuration

1. **Cost Tracking**
   ```
   CyclSales Vision > AI Usage Log
   Group by: Location, Date, AI Service
   Export data for billing
   ```

2. **Cost Allocation**
   ```python
   # Allocate costs to locations/clients
   for usage in usage_logs:
       location = usage.location_id
       cost = usage.total_cost
       # Allocate cost to location billing
   ```

## GHL Integration Setup

### 1. Webhook Configuration

#### GHL Webhook Setup

1. **Configure GHL Webhook**
   ```
   GHL Dashboard > Settings > Webhooks
   
   Event: Call Completed
   URL: https://your-odoo-domain.com/cs-vision-ai/call-summary
   Method: POST
   Headers: Content-Type: application/json
   ```

2. **Test Webhook**
   ```bash
   # Test webhook endpoint
   curl -X POST https://your-odoo-domain.com/cs-vision-ai/call-summary \
     -H "Content-Type: application/json" \
     -d '{
       "messageType": "CALL",
       "messageId": "test_123",
       "contactId": "contact_456",
       "direction": "inbound",
       "callDuration": 120,
       "locationId": "loc_789"
     }'
   ```

#### Webhook Security

1. **Implement Authentication**
   ```python
   # Add webhook signature validation
   def validate_webhook_signature(self, payload, signature):
       expected_signature = hmac.new(
           webhook_secret.encode(),
           payload.encode(),
           hashlib.sha256
       ).hexdigest()
       return hmac.compare_digest(signature, expected_signature)
   ```

2. **Rate Limiting**
   ```python
   # Implement rate limiting
   @http.route('/cs-vision-ai/call-summary', type='json', auth='none')
   def call_summary(self, **post):
       # Check rate limit
       if self._is_rate_limited(request.remote_addr):
           return {'error': 'Rate limit exceeded'}
   ```

### 2. Workflow Configuration

#### GHL Workflow Setup

1. **Create Workflow**
   ```
   GHL Dashboard > Workflows > Create Workflow
   
   Trigger: Call Completed
   Conditions: Call Duration > 20 seconds
   ```

2. **Add Custom Action**
   ```
   Action Type: Custom Action
   URL: https://your-odoo-domain.com/cs-vision/action-transcribe-call
   Method: POST
   Headers: Content-Type: application/json
   ```

3. **Configure Action Parameters**
   ```json
   {
     "cs_vision_ai_message_id": "{{messageId}}",
     "cs_vision_summary_prompt": "Please provide a summary of this call",
     "cs_vision_call_minimum_duration": 20,
     "call_variables_returned": [1, 2, 3, 4, 5, 6]
   }
   ```

### 3. Multi-Location Setup

#### Location Configuration

1. **Create Location Records**
   ```
   CyclSales Vision > Installed Locations
   Create records for each GHL location
   ```

2. **Configure Location-Specific Settings**
   ```python
   # Each location can have:
   - Custom AI service configuration
   - Specific prompt templates
   - Usage limits and billing
   - Custom webhook endpoints
   ```

3. **Location Isolation**
   ```python
   # Ensure data isolation between locations
   def get_location_data(self, location_id):
       return self.env['cyclsales.vision.ai.usage.log'].search([
           ('location_id', '=', location_id)
       ])
   ```

## User Management

### 1. User Roles and Permissions

#### Default Roles

1. **System Administrator**
   - Full access to all features
   - Can configure AI services
   - Can manage all locations
   - Can view all usage logs

2. **Location Manager**
   - Access to specific location data
   - Can view location usage logs
   - Can configure location-specific settings
   - Cannot access other locations

3. **Regular User**
   - Read access to usage logs
   - Can view AI service status
   - Cannot modify configurations

4. **Portal User**
   - Read-only access to usage logs
   - Limited to own data

#### Creating Custom Roles

1. **Define Role Requirements**
   ```
   - What data should they access?
   - What actions can they perform?
   - What locations are they responsible for?
   ```

2. **Create Security Groups**
   ```
   Settings > Users & Companies > Groups
   Create new group with specific permissions
   ```

3. **Assign Users to Groups**
   ```
   Settings > Users & Companies > Users
   Edit user > Access Rights tab
   Add to appropriate groups
   ```

### 2. User Training

#### Training Materials

1. **User Manual**
   - How to access the module
   - How to view usage logs
   - How to interpret AI results
   - Common troubleshooting steps

2. **Video Tutorials**
   - Module overview
   - Common tasks
   - Best practices

3. **Quick Reference Cards**
   - Common actions
   - Keyboard shortcuts
   - Contact information

## Monitoring & Maintenance

### 1. System Monitoring

#### Key Metrics to Monitor

1. **Performance Metrics**
   ```
   - API response times
   - Database query performance
   - Memory usage
   - CPU utilization
   ```

2. **Business Metrics**
   ```
   - Number of calls processed
   - AI service success rate
   - Cost per call
   - User adoption rate
   ```

3. **Error Metrics**
   ```
   - Error rates by endpoint
   - Error types and frequencies
   - Failed webhook deliveries
   - AI service failures
   ```

#### Monitoring Tools

1. **Odoo Built-in Monitoring**
   ```
   Settings > Technical > Logging
   Settings > Technical > Performance
   ```

2. **External Monitoring**
   ```bash
   # Set up monitoring with tools like:
   - Prometheus + Grafana
   - New Relic
   - Datadog
   - Custom monitoring scripts
   ```

3. **Custom Monitoring Scripts**
   ```python
   # Example monitoring script
   def check_system_health():
       # Check AI service status
       ai_services = env['cyclsales.vision.ai'].search([
           ('is_active', '=', True)
       ])
       
       for service in ai_services:
           if service.status == 'error':
               send_alert(f"AI service {service.name} is in error state")
       
       # Check recent errors
       recent_errors = env['cyclsales.vision.ai.usage.log'].search([
           ('status', '=', 'failed'),
           ('create_date', '>=', fields.Datetime.now() - timedelta(hours=1))
       ])
       
       if len(recent_errors) > 10:
           send_alert("High error rate detected")
   ```

### 2. Regular Maintenance Tasks

#### Daily Tasks

1. **Check Error Logs**
   ```
   CyclSales Vision > AI Usage Log
   Filter: Status = Failed, Date = Today
   Review and address any errors
   ```

2. **Monitor Performance**
   ```
   Check average response times
   Monitor token usage
   Review cost trends
   ```

3. **Verify Webhook Health**
   ```bash
   # Check webhook endpoint
   curl -I https://your-domain.com/cs-vision-ai/call-summary
   ```

#### Weekly Tasks

1. **Review Usage Analytics**
   ```
   Export usage data
   Analyze trends
   Identify optimization opportunities
   ```

2. **Update AI Configurations**
   ```
   Review prompt templates
   Optimize settings based on usage
   Update cost configurations
   ```

3. **Security Review**
   ```
   Review access logs
   Check for suspicious activity
   Update API keys if needed
   ```

#### Monthly Tasks

1. **Performance Optimization**
   ```
   Analyze slow queries
   Optimize database indexes
   Review caching strategies
   ```

2. **Cost Analysis**
   ```
   Review monthly costs
   Identify cost optimization opportunities
   Update billing configurations
   ```

3. **Backup and Recovery**
   ```
   Test backup procedures
   Verify data integrity
   Update disaster recovery plans
   ```

### 3. Backup and Recovery

#### Database Backup

1. **Automated Backups**
   ```bash
   # Create backup script
   #!/bin/bash
   DATE=$(date +%Y%m%d_%H%M%S)
   pg_dump your_database > backup_$DATE.sql
   gzip backup_$DATE.sql
   ```

2. **Backup Schedule**
   ```
   Daily: Full database backup
   Weekly: Full backup + log backup
   Monthly: Full backup + configuration backup
   ```

3. **Backup Verification**
   ```bash
   # Test backup restoration
   createdb test_restore
   psql test_restore < backup_file.sql
   ```

#### Configuration Backup

1. **AI Service Configurations**
   ```python
   # Export AI service configurations
   ai_services = env['cyclsales.vision.ai'].search([])
   config_data = []
   
   for service in ai_services:
       config_data.append({
           'name': service.name,
           'model_type': service.model_type,
           'base_url': service.base_url,
           'max_tokens': service.max_tokens,
           'temperature': service.temperature,
           'default_prompt_template': service.default_prompt_template
       })
   
   # Save to file
   with open('ai_config_backup.json', 'w') as f:
       json.dump(config_data, f, indent=2)
   ```

2. **Access Rights Backup**
   ```python
   # Export access rights
   access_rights = env['ir.model.access'].search([
       ('model_id.model', 'like', 'cyclsales.vision%')
   ])
   
   rights_data = []
   for right in access_rights:
       rights_data.append({
           'model': right.model_id.model,
           'group': right.group_id.name,
           'perm_read': right.perm_read,
           'perm_write': right.perm_write,
           'perm_create': right.perm_create,
           'perm_unlink': right.perm_unlink
       })
   ```

## Troubleshooting

### 1. Common Issues

#### AI Service Issues

**Problem**: AI service not responding
```
Symptoms:
- 500 errors in logs
- Timeout responses
- "AI service not available" errors

Solutions:
1. Check API key validity
2. Verify base URL configuration
3. Check network connectivity
4. Review error logs in AI Usage Log
5. Test connection via Odoo interface
```

**Problem**: High token usage
```
Symptoms:
- Unexpected costs
- Slow response times
- Rate limiting errors

Solutions:
1. Reduce max_tokens setting
2. Optimize prompt templates
3. Use conditional fields
4. Implement caching
5. Monitor usage analytics
```

#### GHL Integration Issues

**Problem**: Webhooks not received
```
Symptoms:
- No call processing
- Missing usage logs
- GHL workflow not triggering

Solutions:
1. Verify webhook URL configuration
2. Check SSL certificate validity
3. Review firewall settings
4. Test webhook endpoint manually
5. Check GHL webhook logs
```

**Problem**: Workflow triggers not firing
```
Symptoms:
- No AI processing for calls
- Missing trigger records
- Workflow not executing

Solutions:
1. Verify trigger status is "active"
2. Check location association
3. Review webhook configuration
4. Validate trigger permissions
5. Check GHL workflow settings
```

### 2. Debugging Procedures

#### Step-by-Step Debugging

1. **Check Logs**
   ```bash
   # Check Odoo logs
   sudo tail -f /var/log/odoo/odoo.log | grep -i "cyclsales\|vision"
   
   # Check system logs
   sudo journalctl -u odoo -f
   ```

2. **Test API Endpoints**
   ```bash
   # Test webhook endpoint
   curl -X POST https://your-domain.com/cs-vision-ai/call-summary \
     -H "Content-Type: application/json" \
     -d '{"test": "data"}'
   
   # Test AI service endpoint
   curl -X POST https://your-domain.com/cs-vision/action-transcribe-call \
     -H "Content-Type: application/json" \
     -d '{"cs_vision_ai_message_id": "test"}'
   ```

3. **Database Queries**
   ```sql
   -- Check recent errors
   SELECT * FROM cyclsales_vision_ai_usage_log 
   WHERE status = 'failed' 
   ORDER BY create_date DESC 
   LIMIT 10;
   
   -- Check AI service status
   SELECT name, status, error_count, last_error 
   FROM cyclsales_vision_ai 
   WHERE is_active = true;
   
   -- Check webhook triggers
   SELECT * FROM cyclsales_vision_trigger 
   WHERE status = 'active';
   ```

4. **Odoo Shell Debugging**
   ```python
   # Access Odoo shell
   ./odoo-bin shell -d your_database
   
   # Test AI service
   ai_service = env['cyclsales.vision.ai'].search([('is_active', '=', True)], limit=1)
   result = ai_service.generate_summary(transcript="Test transcript")
   print(result)
   
   # Check usage logs
   logs = env['cyclsales.vision.ai.usage.log'].search([
       ('create_date', '>=', fields.Datetime.now() - timedelta(hours=1))
   ])
   for log in logs:
       print(f"{log.create_date}: {log.status} - {log.error_message}")
   ```

### 3. Performance Issues

#### Database Performance

**Problem**: Slow queries
```
Solutions:
1. Add database indexes
2. Optimize query patterns
3. Implement caching
4. Monitor query execution plans
5. Consider database partitioning
```

**Problem**: High memory usage
```
Solutions:
1. Optimize ORM queries
2. Implement pagination
3. Use lazy loading
4. Monitor memory usage
5. Consider horizontal scaling
```

#### API Performance

**Problem**: Slow API responses
```
Solutions:
1. Optimize AI service calls
2. Implement response caching
3. Use async processing
4. Monitor external API performance
5. Consider load balancing
```

## Security Best Practices

### 1. API Security

#### API Key Management

1. **Secure Storage**
   ```python
   # Use environment variables
   import os
   api_key = os.environ.get('OPENAI_API_KEY')
   
   # Or use Odoo system parameters
   api_key = env['ir.config_parameter'].sudo().get_param('cyclsales.vision.api_key')
   ```

2. **Key Rotation**
   ```python
   # Implement key rotation schedule
   def rotate_api_keys(self):
       # Generate new keys
       # Update configurations
       # Notify administrators
       # Monitor for errors during transition
   ```

3. **Access Monitoring**
   ```python
   # Monitor API key usage
   def monitor_api_usage(self):
       usage_logs = env['cyclsales.vision.ai.usage.log'].search([
           ('create_date', '>=', fields.Datetime.now() - timedelta(hours=1))
       ])
       
       # Check for unusual patterns
       # Alert on suspicious activity
   ```

#### Input Validation

1. **Request Validation**
   ```python
   def validate_request(self, data):
       # Validate required fields
       required_fields = ['message_id', 'summary_prompt']
       for field in required_fields:
           if field not in data:
               raise ValidationError(f"Missing required field: {field}")
       
       # Validate data types
       if not isinstance(data.get('call_duration'), int):
           raise ValidationError("call_duration must be an integer")
       
       # Validate data ranges
       if data.get('call_duration', 0) < 0:
           raise ValidationError("call_duration cannot be negative")
   ```

2. **SQL Injection Prevention**
   ```python
   # Use ORM methods instead of raw SQL
   # Avoid string concatenation in queries
   records = env['cyclsales.vision.ai'].search([
       ('name', '=', name),
       ('is_active', '=', True)
   ])
   ```

### 2. Network Security

#### SSL/TLS Configuration

1. **SSL Certificate**
   ```bash
   # Install SSL certificate
   sudo certbot --nginx -d your-domain.com
   
   # Configure HTTPS redirect
   # Force HTTPS for all API endpoints
   ```

2. **Security Headers**
   ```python
   # Add security headers
   response.headers.update({
       'X-Content-Type-Options': 'nosniff',
       'X-Frame-Options': 'DENY',
       'X-XSS-Protection': '1; mode=block',
       'Strict-Transport-Security': 'max-age=31536000; includeSubDomains'
   })
   ```

#### Firewall Configuration

1. **Network Access Control**
   ```bash
   # Configure firewall rules
   sudo ufw allow from GHL_IP_RANGES to any port 443
   sudo ufw deny from all to any port 80  # Redirect to HTTPS
   ```

2. **Rate Limiting**
   ```python
   # Implement rate limiting
   def check_rate_limit(self, ip_address):
       recent_requests = self._get_recent_requests(ip_address)
       if len(recent_requests) > MAX_REQUESTS_PER_MINUTE:
           raise ValidationError("Rate limit exceeded")
   ```

### 3. Data Security

#### Data Encryption

1. **Sensitive Data Encryption**
   ```python
   # Encrypt sensitive data
   from cryptography.fernet import Fernet
   
   def encrypt_api_key(self, api_key):
       key = Fernet.generate_key()
       f = Fernet(key)
       encrypted_key = f.encrypt(api_key.encode())
       return encrypted_key
   ```

2. **Database Encryption**
   ```sql
   -- Enable database encryption
   ALTER DATABASE your_database SET encryption = on;
   ```

#### Access Control

1. **Role-Based Access**
   ```python
   # Implement fine-grained access control
   def check_access_rights(self, user, location_id):
       if user.has_group('cyclsales_vision.location_manager'):
           return user.location_id.id == location_id
       return user.has_group('cyclsales_vision.system_admin')
   ```

2. **Audit Logging**
   ```python
   # Log all access attempts
   def log_access_attempt(self, user, action, resource):
       env['cyclsales.vision.access.log'].create({
           'user_id': user.id,
           'action': action,
           'resource': resource,
           'ip_address': request.httprequest.remote_addr,
           'timestamp': fields.Datetime.now()
       })
   ```

### 4. Monitoring and Alerting

#### Security Monitoring

1. **Anomaly Detection**
   ```python
   # Monitor for unusual activity
   def detect_anomalies(self):
       # Check for unusual API usage patterns
       # Monitor for failed authentication attempts
       # Alert on suspicious IP addresses
       # Track unusual data access patterns
   ```

2. **Security Alerts**
   ```python
   # Set up security alerts
   def send_security_alert(self, alert_type, details):
       # Send email alerts
       # Log security events
       # Trigger incident response procedures
   ```

---

**Administrator Guide Version**: 1.0  
**Last Updated**: 2024  
**For developer documentation**: See `DEVELOPER_QUICK_REFERENCE.md`  
**For full documentation**: See `README.md`
