# Session-Based Authentication Setup

The inference gateway now supports authentication via themultiverse.school session cookies in addition to API keys.

## How It Works

When a user is logged into themultiverse.school and visits inference.themultiverse.school:
1. The gateway reads the Flask session cookie (`session`)
2. Validates it against the Firestore session store
3. Checks if the user has admin privileges in the students table
4. Grants access to admin endpoints without requiring an API key

## Prerequisites

### 1. Google Cloud Credentials

The gateway needs access to Firestore to read session data. On GCE, this works automatically via the service account. For local development:

```bash
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account-key.json"
```

### 2. PostgreSQL Connection String

Add to your `.env` file:

```bash
# PostgreSQL connection for user verification
POSTGRES_CONNECTION_STRING="postgresql://user:password@host:port/database"
```

This is used to query the `students` table to verify admin status.

### 3. Install Dependencies

```bash
pip install google-cloud-firestore==2.14.0 psycopg2-binary==2.9.9
```

## Configuration

The session authenticator connects to:
- **Firestore Project**: `multiverseschool`
- **Firestore Database**: `multiverse-sessions`
- **Collection**: `sessions`
- **Session Cookie Name**: `session` (Flask default)
- **Cookie Domain**: `.themultiverse.school`

## Authentication Flow

### For Admin Endpoints (`/admin/*`)

The gateway tries authentication in this order:

1. **Session Auth** (if logged into themultiverse.school)
   - Read `session` cookie
   - Validate against Firestore
   - Check user's `admin` field in students table
   - ✅ Grant access if user is admin

2. **API Key Auth** (fallback)
   - Check `X-API-Key` header
   - Compare with `ADMIN_API_KEY` from .env
   - ✅ Grant access if key matches

### For Client Endpoints (`/v1/*`)

No change - these remain open or use client API keys as configured.

## Benefits

- **Seamless UX**: Admins logged into themultiverse.school don't need to manually enter API keys
- **Centralized Auth**: Single authentication system across all multiverse school services
- **Backward Compatible**: Existing API key authentication still works
- **Secure**: Sessions are validated and expired sessions are rejected

## Testing

### Test Session Auth

1. Log into https://themultiverse.school (as an admin user)
2. Visit https://inference.themultiverse.school/dashboard
3. Should see server list without needing to enter API key

### Test API Key Auth

1. Open incognito/private browser window
2. Visit https://inference.themultiverse.school/dashboard  
3. Click "Set API Key" and enter admin key
4. Should see server list after providing key

## Troubleshooting

### Session auth not working

Check logs for:
```
Session auth not available: <error>
```

Common issues:
- POSTGRES_CONNECTION_STRING not set
- Google Cloud credentials not available
- User doesn't have admin=true in students table

### Users need admin privileges

To grant admin access, update the students table:

```sql
UPDATE students SET admin = true WHERE email = 'user@example.com';
```

## Security Notes

- Sessions are validated for expiration (default: 1 day)
- Only users with `admin=true` can access admin endpoints via session auth
- API key auth remains available as a fallback
- Session cookies use secure, httponly, and samesite flags

## Production Deployment

For GCE deployment:

1. Ensure the service account has Firestore access
2. Add POSTGRES_CONNECTION_STRING to production .env:
   ```bash
   ssh into GCE instance
   sudo nano /opt/multiverse-gateway/.env
   # Add POSTGRES_CONNECTION_STRING=...
   ```
3. Restart the service:
   ```bash
   sudo systemctl restart multiverse-gateway
   ```

## Local Development

For local testing:

1. Get service account key with Firestore access
2. Set up environment:
   ```bash
   export GOOGLE_APPLICATION_CREDENTIALS="path/to/key.json"
   export POSTGRES_CONNECTION_STRING="postgresql://..."
   ```
3. Run locally:
   ```bash
   ./start.sh
   ```

## Files Modified

- `app/utils/session_auth.py` - New session authentication module
- `app/utils/auth.py` - Added `verify_admin_auth()` function
- `app/routers/admin.py` - Changed to use dual authentication
- `requirements.txt` - Added Firestore and psycopg2 dependencies

