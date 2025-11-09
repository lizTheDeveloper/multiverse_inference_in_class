# GCE Deployment - Multiverse Inference Gateway

## Deployment Summary

Successfully deployed the Multiverse Inference Gateway to Google Cloud Platform.

### Instance Details

- **Instance Name**: multiverse-gateway
- **Machine Type**: e2-small (2 vCPUs, 2GB RAM)
- **Zone**: us-west1-b
- **Region**: us-west1
- **Project**: multiverseschool
- **External IP**: 136.117.2.59
- **OS**: Ubuntu 22.04 LTS
- **Disk**: 20GB standard persistent disk

### Deployed Services

1. **Multiverse Gateway Application**
   - Running on port 8000 internally
   - Managed by systemd service: `multiverse-gateway.service`
   - Auto-starts on boot
   - Logs to journald

2. **Nginx Reverse Proxy**
   - Listening on port 80 (HTTP)
   - Proxying to application on port 8000
   - Streaming support enabled
   - Access logs: `/var/log/nginx/multiverse-gateway-access.log`
   - Error logs: `/var/log/nginx/multiverse-gateway-error.log`

### Access Information

#### Web User Interface
- **Dashboard**: http://136.117.2.59/dashboard
- **Register Server**: http://136.117.2.59/register
- **View Models**: http://136.117.2.59/models
- **Test Inference**: http://136.117.2.59/test
- **Settings**: http://136.117.2.59/settings

#### API Endpoints
- **Gateway URL**: http://136.117.2.59
- **API Documentation**: http://136.117.2.59/docs
- **Health Endpoint**: http://136.117.2.59/health
- **Models Endpoint**: http://136.117.2.59/v1/models

### Admin Credentials

**IMPORTANT - Save these credentials:**

- **Admin API Key**: `6ix6iURn29_4MPybfbyXgbxoO8-dPeoKuRPRR9Sj58o`

Use this key in the `X-API-Key` header for all admin endpoints:
- POST /admin/register
- PUT /admin/register/{id}
- DELETE /admin/register/{id}
- GET /admin/servers

### Verification Tests

```bash
# Test health endpoint
curl http://136.117.2.59/health
# Response: {"status":"healthy","service":"Multiverse Inference Gateway","version":"1.0.0","database":"healthy"}

# List available models
curl http://136.117.2.59/v1/models
# Response: {"object":"list","data":[]}

# View API documentation
open http://136.117.2.59/docs
```

### Service Management

```bash
# SSH into instance
gcloud compute ssh multiverse-gateway --project=multiverseschool --zone=us-west1-b

# Check service status
sudo systemctl status multiverse-gateway

# View application logs
sudo journalctl -u multiverse-gateway -f

# Restart service
sudo systemctl restart multiverse-gateway

# Stop service
sudo systemctl stop multiverse-gateway

# Start service
sudo systemctl start multiverse-gateway
```

### File Locations

- **Application Directory**: `/opt/multiverse-gateway/`
- **Virtual Environment**: `/opt/multiverse-gateway/env/`
- **Configuration**: `/opt/multiverse-gateway/.env`
- **Database**: `/opt/multiverse-gateway/gateway.db`
- **Logs**: `/opt/multiverse-gateway/logs/`
- **systemd Service**: `/etc/systemd/system/multiverse-gateway.service`
- **Nginx Config**: `/etc/nginx/sites-available/multiverse-gateway`

### Next Steps

#### Using the Web Interface (Recommended)

1. **Access the Dashboard**
   - Open http://136.117.2.59/dashboard in your browser
   - View real-time server status and statistics

2. **Register a Server via Web Form**
   - Navigate to http://136.117.2.59/register
   - Enter your API key: `6ix6iURn29_4MPybfbyXgbxoO8-dPeoKuRPRR9Sj58o`
   - Fill in server details (model name, endpoint URL, description)
   - Click "Test Connection" to verify before registering
   - Submit the form

3. **Test Inference via Web UI**
   - Go to http://136.117.2.59/test
   - Select a model from the dropdown
   - Enter your prompt
   - Toggle streaming if desired
   - Click "Send Request"

#### Using the API (Alternative)

1. **Register a Test Server**
   ```bash
   curl -X POST http://136.117.2.59/admin/register \
     -H "X-API-Key: 6ix6iURn29_4MPybfbyXgbxoO8-dPeoKuRPRR9Sj58o" \
     -H "Content-Type: application/json" \
     -d '{
       "model_name": "gpt-3.5-turbo",
       "endpoint_url": "https://your-model-server.ngrok.io",
       "description": "Test server",
       "student_id": "test-student"
     }'
   ```

2. **Test Inference**
   ```bash
   curl -X POST http://136.117.2.59/v1/chat/completions \
     -H "Content-Type: application/json" \
     -d '{
       "model": "gpt-3.5-turbo",
       "messages": [{"role": "user", "content": "Hello!"}]
     }'
   ```

3. **Set Up SSL (Optional but Recommended)**
   - Get a domain name and point it to 136.117.2.59
   - Update nginx config with domain name
   - Run certbot to get Let's Encrypt certificate:
     ```bash
     sudo certbot --nginx -d your-domain.com
     ```

4. **Set Up Monitoring**
   - Monitor service health: `http://136.117.2.59/health`
   - Check application logs: `sudo journalctl -u multiverse-gateway -f`
   - Monitor nginx logs: `sudo tail -f /var/log/nginx/multiverse-gateway-*.log`

### Security Notes

- Admin API key is required for all admin operations
- Change the API key by editing `/opt/multiverse-gateway/.env`
- Firewall rules allow HTTP (80) and HTTPS (443) traffic
- SSH access is secured with OS Login

### Backup and Maintenance

```bash
# Create database backup
sudo su - gateway -c 'cd /opt/multiverse-gateway && bash deploy/backup.sh'

# Update application
sudo su - gateway -c 'cd /opt/multiverse-gateway && bash deploy/update.sh'

# View recent backups
ls -lh ~gateway/backups/multiverse-gateway/
```

### Troubleshooting

**Service won't start:**
```bash
sudo systemctl status multiverse-gateway
sudo journalctl -u multiverse-gateway -n 50
```

**Nginx issues:**
```bash
sudo nginx -t
sudo systemctl status nginx
sudo tail -f /var/log/nginx/error.log
```

**Database issues:**
```bash
cd /opt/multiverse-gateway
source env/bin/activate
python -c "from app.utils.database import get_db_connection; import asyncio; asyncio.run(get_db_connection())"
```

---

**Deployment Date**: October 17, 2025
**Deployed By**: Claude Code
**Instance Status**: Active and Healthy
