# Sub-Account Access Testing Guide

## Quick Test Commands

### 1. Start the Development Server
```bash
cd client
npm run dev
```

### 2. Test URLs

#### Agency Mode (Full Access)
- http://localhost:3000/overview
- http://localhost:3000/analytics
- http://localhost:3000/automations

#### Sub-Account Mode (Limited Access)
- http://localhost:3000/analytics?location_id=GMCTanHIR07xDE3kvnpo
- http://localhost:3000/automations?location_id=GMCTanHIR07xDE3kvnpo
- http://localhost:3000/call-details?contact_id=34450&contact=Lori%20Barber&date=2025-08-18T19%3A21%3A06.114000&tags=name%20via%20lookup%2Csent%20quick%20message%2Cunqualified%2Cgoogle-call%2Cnew%20lead%20no%20answer%20campaign%2Cai%20follow%20up%20bot%2Cai%20off

#### Test Page
- http://localhost:3000/sub-account-test?location_id=GMCTanHIR07xDE3kvnpo

## Expected Behavior

### Agency Mode
- Full navigation with Overview, Analytics, Automations tabs
- Can access all pages
- Can switch between locations
- No authentication required

### Sub-Account Mode
- Limited navigation with only Analytics and Automations tabs
- Shows sub-account header with location info
- Cannot access Overview, Dashboard, Settings, etc.
- Data filtered by location_id
- Logout functionality available

## Testing Checklist

- [ ] Agency mode works normally
- [ ] Sub-account mode activates with location_id parameter
- [ ] Authentication validates location_id
- [ ] Sub-account navigation shows only allowed pages
- [ ] Data is filtered by location_id
- [ ] Logout clears session
- [ ] Invalid location_id shows error
- [ ] Session persists on refresh
- [ ] iFrame integration works

## Troubleshooting

### Common Issues

1. **TypeScript Errors**: Run `npm run check` to verify types
2. **API Errors**: Check that the backend API is running
3. **Authentication Fails**: Verify the location_id is valid
4. **Navigation Issues**: Clear localStorage and try again

### Debug Commands

```bash
# Check TypeScript
npm run check

# Build for production
npm run build

# Preview build
npm run preview
```
