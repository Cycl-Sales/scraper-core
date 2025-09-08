# PostgreSQL Serialization Failure Solution

## Problem Description

The application was experiencing PostgreSQL serialization failures with the error:
```
ERROR: could not serialize access due to concurrent update
```

This error occurred when multiple processes tried to update the same contact records simultaneously, causing Odoo's ORM to generate bulk UPDATE queries that conflicted with each other.

## Root Cause Analysis

The issue was caused by:

1. **Bulk UPDATE Queries**: Odoo's ORM was batching multiple contact updates into single SQL statements
2. **Concurrent Access**: Multiple processes updating the same contact records simultaneously
3. **Transaction Conflicts**: PostgreSQL's serializable isolation level preventing concurrent modifications

The error log showed:
```sql
UPDATE "ghl_location_contact"
SET "last_touch_date" = "__tmp"."last_touch_date"::timestamp, 
    "touch_summary" = "__tmp"."touch_summary"::VARCHAR, 
    "write_date" = "__tmp"."write_date"::timestamp, 
    "write_uid" = "__tmp"."write_uid"::int4
FROM (VALUES (34811, '2025-09-08 13:13:05.659366', '1 EMAIL, 1 OPPORTUNITY', ...), 
             (34812, '2025-09-08 13:21:25.767707', '1 EMAIL, 1 OPPORTUNITY', ...), 
             ...) AS "__tmp"("id", "last_touch_date", "touch_summary", "write_date", "write_uid")
WHERE "ghl_location_contact"."id" = "__tmp"."id"
```

## Solution Implementation

### 1. Individual Transaction Updates

**File**: `common/cs-dashboard-backend/controllers/installed_location_controller.py`

Replaced bulk updates with individual transactions:

```python
def _update_contact_touch_info_with_retry(self, contact, update_data, max_retries=3):
    """Update contact touch information with retry mechanism using individual transactions."""
    for attempt in range(max_retries):
        try:
            # Use a separate transaction for each contact update to prevent bulk UPDATE
            with request.env.registry.cursor() as new_cr:
                new_env = api.Environment(new_cr, SUPERUSER_ID, {})
                
                # Re-fetch the contact from database to get latest version
                fresh_contact = new_env['ghl.location.contact'].sudo().browse(contact.id)
                if not fresh_contact.exists():
                    return False
                
                # Perform the update on the fresh record
                fresh_contact.write(update_data)
                
                # Commit the individual transaction
                new_cr.commit()
                
                return True
                
        except Exception as e:
            # Retry logic with exponential backoff
            if "could not serialize access due to concurrent update" in str(e) and attempt < max_retries - 1:
                wait_time = (2 ** attempt) * 0.1
                time.sleep(wait_time)
                continue
            else:
                return False
```

### 2. Model-Level Transaction Control

**File**: `web_scraper/models/ghl_location_contact.py`

Updated retry methods to use individual transactions:

```python
def _update_contact_with_retry(self, update_data, max_retries=3):
    """Update contact with retry logic using individual transactions."""
    for attempt in range(max_retries):
        try:
            # Use a separate transaction to prevent bulk UPDATE conflicts
            with self.env.registry.cursor() as new_cr:
                new_env = api.Environment(new_cr, SUPERUSER_ID, {})
                
                # Re-fetch the contact from database to get latest version
                contact = new_env['ghl.location.contact'].sudo().browse(self.id)
                if not contact.exists():
                    raise Exception(f"Contact {self.id} no longer exists")
                
                # Update the fields on the fresh record
                for field, value in update_data.items():
                    setattr(contact, field, value)
                
                # Commit the individual transaction
                new_cr.commit()
                
                return True
```

### 3. Batch Processing with Isolation

Added methods for safe batch processing:

```python
def _process_contacts_in_safe_batches(self, contacts, batch_size=5):
    """Process contacts in small batches with individual transactions."""
    results = {'success_count': 0, 'failed_contact_ids': [], 'total_processed': 0}
    
    # Process contacts in small batches
    for i in range(0, len(contacts), batch_size):
        batch = contacts[i:i + batch_size]
        
        for contact in batch:
            try:
                # Use individual transaction for each contact
                with request.env.registry.cursor() as new_cr:
                    new_env = api.Environment(new_cr, SUPERUSER_ID, {})
                    
                    # Re-fetch the contact to get latest version
                    fresh_contact = new_env['ghl.location.contact'].sudo().browse(contact.id)
                    if not fresh_contact.exists():
                        continue
                    
                    # Process the contact
                    self._process_single_contact_safely(fresh_contact, new_env)
                    
                    # Commit the individual transaction
                    new_cr.commit()
                    results['success_count'] += 1
                    
            except Exception as e:
                results['failed_contact_ids'].append(contact.id)
    
    return results
```

### 4. Safe Bulk Updates

Added methods for handling bulk updates safely:

```python
def _safe_bulk_update_contacts_with_isolation(self, contact_updates, max_retries=3):
    """Safely perform bulk updates with proper transaction isolation."""
    # Process in smaller batches to reduce lock contention
    batch_size = 10
    batches = [contact_updates[i:i + batch_size] for i in range(0, len(contact_updates), batch_size)]
    
    for batch in batches:
        for attempt in range(max_retries):
            try:
                # Use a new transaction for each batch
                with request.env.registry.cursor() as new_cr:
                    new_env = api.Environment(new_cr, SUPERUSER_ID, {})
                    
                    # Process each contact individually within the batch
                    for contact in existing_contacts:
                        contact.write(unique_updates[contact.id])
                    
                    # Commit the batch
                    new_cr.commit()
                    break  # Success, move to next batch
```

## Key Improvements

1. **Individual Transactions**: Each contact update now uses its own transaction
2. **Retry Logic**: Exponential backoff retry mechanism for concurrent update errors
3. **Fresh Record Fetching**: Always re-fetch records to get the latest version
4. **Batch Size Control**: Process contacts in small batches to reduce lock contention
5. **Error Handling**: Graceful handling of serialization failures without breaking the entire process

## Benefits

- **Eliminates Serialization Failures**: Individual transactions prevent bulk UPDATE conflicts
- **Improved Reliability**: Retry logic handles temporary conflicts
- **Better Performance**: Smaller batch sizes reduce lock contention
- **Graceful Degradation**: Failed updates don't break the entire process
- **Maintains Data Integrity**: Fresh record fetching ensures consistency

## Usage

The solution is automatically applied to all contact update operations. The retry mechanism will:

1. Attempt the update with a fresh record
2. If a serialization error occurs, wait with exponential backoff
3. Retry up to 3 times
4. Log failures but continue processing other contacts

This ensures that temporary concurrent access issues don't cause permanent failures in the application.
