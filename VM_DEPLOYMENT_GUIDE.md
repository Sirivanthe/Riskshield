# RiskShield - VM Deployment Guide

Complete guide to deploy RiskShield on a Virtual Machine (Ubuntu, CentOS, or other Linux distributions)

---

## 📋 VM Requirements

### Minimum Specifications

- **OS:** Ubuntu 20.04+ / CentOS 8+ / RHEL 8+ / Debian 11+
- **CPU:** 2 vCPUs
- **RAM:** 4 GB
- **Disk:** 20 GB
- **Network:** Public IP or accessible via VPN

### Recommended Specifications

- **OS:** Ubuntu 22.04 LTS
- **CPU:** 4 vCPUs
- **RAM:** 8 GB
- **Disk:** 50 GB SSD
- **Network:** Public IP with firewall

### Supported Platforms

- AWS EC2
- Azure VM
- Google Compute Engine
- DigitalOcean Droplets
- Linode
- On-premise VMs (VMware, VirtualBox, Hyper-V)

---

## 🚀 Quick Start (30 Minutes)

### Method 1: Automated Installation Script

```bash
# Download and run installation script
curl -fsSL https://your-repo/install.sh | bash

# Or manually:
wget https://your-repo/install.sh
chmod +x install.sh
sudo ./install.sh
```

### Method 2: Manual Installation (Below)

---

## 🔧 Manual Installation Steps

### Step 1: Prepare VM

#### SSH into VM

```bash
ssh user@your-vm-ip

# Or with key:
ssh -i your-key.pem ubuntu@your-vm-ip
```

#### Update System

```bash
sudo apt update && sudo apt upgrade -y  # Ubuntu/Debian
# OR
sudo yum update -y  # CentOS/RHEL
```

#### Install Essential Tools

```bash
sudo apt install -y curl wget git build-essential  # Ubuntu/Debian
# OR
sudo yum install -y curl wget git gcc gcc-c++ make  # CentOS/RHEL
```

### Step 2: Install Python 3.11

#### Ubuntu 22.04+

```bash
sudo apt install -y python3.11 python3.11-venv python3.11-dev python3-pip
```

#### Ubuntu 20.04

```bash
sudo apt install -y software-properties-common
sudo add-apt-repository -y ppa:deadsnakes/ppa
sudo apt update
sudo apt install -y python3.11 python3.11-venv python3.11-dev
```

#### CentOS/RHEL

```bash
sudo yum install -y gcc openssl-devel bzip2-devel libffi-devel
cd /usr/src
sudo wget https://www.python.org/ftp/python/3.11.8/Python-3.11.8.tgz
sudo tar xzf Python-3.11.8.tgz
cd Python-3.11.8
sudo ./configure --enable-optimizations
sudo make altinstall
```

**Verify:**
```bash
python3.11 --version
# Should output: Python 3.11.x
```

### Step 3: Install Node.js and Yarn

#### Ubuntu/Debian

```bash
# Install Node.js 18 LTS
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs

# Install Yarn
curl -sS https://dl.yarnpkg.com/debian/pubkey.gpg | sudo apt-key add -
echo "deb https://dl.yarnpkg.com/debian/ stable main" | sudo tee /etc/apt/sources.list.d/yarn.list
sudo apt update
sudo apt install -y yarn
```

#### CentOS/RHEL

```bash
# Install Node.js 18 LTS
curl -fsSL https://rpm.nodesource.com/setup_18.x | sudo bash -
sudo yum install -y nodejs

# Install Yarn
curl -sL https://dl.yarnpkg.com/rpm/yarn.repo | sudo tee /etc/yum.repos.d/yarn.repo
sudo yum install -y yarn
```

**Verify:**
```bash
node --version  # Should output: v18.x.x
yarn --version  # Should output: 1.x.x
```

### Step 4: Install MongoDB 7

#### Ubuntu 22.04

```bash
# Import MongoDB GPG key
curl -fsSL https://www.mongodb.org/static/pgp/server-7.0.asc | sudo gpg --dearmor -o /usr/share/keyrings/mongodb-server-7.0.gpg

# Add MongoDB repository
echo "deb [ signed-by=/usr/share/keyrings/mongodb-server-7.0.gpg ] https://repo.mongodb.org/apt/ubuntu jammy/mongodb-org/7.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-7.0.list

# Install MongoDB
sudo apt update
sudo apt install -y mongodb-org

# Start MongoDB
sudo systemctl start mongod
sudo systemctl enable mongod

# Verify
sudo systemctl status mongod
```

#### Ubuntu 20.04

```bash
curl -fsSL https://www.mongodb.org/static/pgp/server-7.0.asc | sudo gpg --dearmor -o /usr/share/keyrings/mongodb-server-7.0.gpg
echo "deb [ signed-by=/usr/share/keyrings/mongodb-server-7.0.gpg ] https://repo.mongodb.org/apt/ubuntu focal/mongodb-org/7.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-7.0.list
sudo apt update
sudo apt install -y mongodb-org
sudo systemctl start mongod
sudo systemctl enable mongod
```

#### CentOS/RHEL 8

```bash
# Create MongoDB repository file
sudo tee /etc/yum.repos.d/mongodb-org-7.0.repo << EOF
[mongodb-org-7.0]
name=MongoDB Repository
baseurl=https://repo.mongodb.org/yum/redhat/\$releasever/mongodb-org/7.0/x86_64/
gpgcheck=1
enabled=1
gpgkey=https://www.mongodb.org/static/pgp/server-7.0.asc
EOF

# Install MongoDB
sudo yum install -y mongodb-org

# Start MongoDB
sudo systemctl start mongod
sudo systemctl enable mongod
```

**Test MongoDB:**
```bash
mongosh --eval "db.serverStatus()"
```

### Step 5: Deploy Application

#### Clone/Upload Code

**Option A: Git Clone**
```bash
cd /opt
sudo git clone <your-repo-url> riskshield
sudo chown -R $USER:$USER /opt/riskshield
cd riskshield
```

**Option B: Upload via SCP**
```bash
# From your local machine:
scp -r /path/to/riskshield user@vm-ip:/opt/

# Then on VM:
sudo chown -R $USER:$USER /opt/riskshield
```

**Option C: Download Release**
```bash
cd /opt
wget https://your-repo/releases/riskshield-v1.0.tar.gz
tar -xzf riskshield-v1.0.tar.gz
cd riskshield
```

#### Setup Backend

```bash
cd /opt/riskshield/backend

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Configure environment
cp .env.example .env  # If .env doesn't exist
nano .env
```

**Edit `.env`:**
```bash
MONGO_URL="mongodb://localhost:27017"
DB_NAME="riskshield_prod"
JWT_SECRET="$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')"
JWT_ALGORITHM="HS256"
CORS_ORIGINS="http://your-domain.com,https://your-domain.com"
ENVIRONMENT="production"
```

**Test Backend:**
```bash
uvicorn server:app --host 0.0.0.0 --port 8001

# In another terminal:
curl http://localhost:8001/api/
# Should return response

# Stop with Ctrl+C
```

#### Setup Frontend

```bash
cd /opt/riskshield/frontend

# Install dependencies
yarn install

# Configure environment
nano .env
```

**Edit `.env`:**
```bash
REACT_APP_BACKEND_URL=http://your-vm-ip:8001
# OR for production with domain:
REACT_APP_BACKEND_URL=https://api.your-domain.com
```

**Build Frontend:**
```bash
yarn build

# Verify build
ls -la build/
# Should see static/, index.html, etc.
```

### Step 6: Setup Systemd Services

#### Create Backend Service

```bash
sudo nano /etc/systemd/system/riskshield-backend.service
```

**Content:**
```ini
[Unit]
Description=RiskShield Backend API
After=network.target mongod.service
Requires=mongod.service

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/opt/riskshield/backend
Environment="PATH=/opt/riskshield/backend/venv/bin"
ExecStart=/opt/riskshield/backend/venv/bin/uvicorn server:app --host 0.0.0.0 --port 8001 --workers 4
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Enable and Start:**
```bash
sudo systemctl daemon-reload
sudo systemctl enable riskshield-backend
sudo systemctl start riskshield-backend
sudo systemctl status riskshield-backend
```

#### Install and Configure Nginx

```bash
# Install Nginx
sudo apt install -y nginx  # Ubuntu/Debian
# OR
sudo yum install -y nginx  # CentOS/RHEL

# Create Nginx config
sudo nano /etc/nginx/sites-available/riskshield
```

**Content:**
```nginx
server {
    listen 80;
    server_name your-domain.com www.your-domain.com;

    # Frontend
    root /opt/riskshield/frontend/build;
    index index.html;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Frontend routes
    location / {
        try_files $uri $uri/ /index.html;
    }

    # Backend API proxy
    location /api {
        proxy_pass http://localhost:8001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }

    # API docs
    location /docs {
        proxy_pass http://localhost:8001;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
    }

    location /redoc {
        proxy_pass http://localhost:8001;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
    }

    # Static files caching
    location ~* \.(jpg|jpeg|png|gif|ico|css|js|svg|woff|woff2|ttf|eot)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

**Enable Site:**
```bash
# Ubuntu/Debian
sudo ln -s /etc/nginx/sites-available/riskshield /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default  # Remove default site

# CentOS/RHEL (if sites-available doesn't exist)
sudo mkdir -p /etc/nginx/sites-{available,enabled}
sudo ln -s /etc/nginx/sites-available/riskshield /etc/nginx/sites-enabled/
# Add to /etc/nginx/nginx.conf in http block:
# include /etc/nginx/sites-enabled/*;

# Test configuration
sudo nginx -t

# Restart Nginx
sudo systemctl restart nginx
sudo systemctl enable nginx
```

### Step 7: Configure Firewall

#### UFW (Ubuntu/Debian)

```bash
# Enable firewall
sudo ufw enable

# Allow SSH (IMPORTANT: Do this first!)
sudo ufw allow 22/tcp

# Allow HTTP/HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Check status
sudo ufw status
```

#### Firewalld (CentOS/RHEL)

```bash
# Start firewall
sudo systemctl start firewalld
sudo systemctl enable firewalld

# Allow services
sudo firewall-cmd --permanent --add-service=ssh
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https

# Reload
sudo firewall-cmd --reload

# Check status
sudo firewall-cmd --list-all
```

#### Cloud Provider Security Groups

**AWS EC2:**
- Allow port 22 (SSH) from your IP
- Allow port 80 (HTTP) from 0.0.0.0/0
- Allow port 443 (HTTPS) from 0.0.0.0/0

**Azure:**
- Add inbound rules for ports 22, 80, 443

**GCP:**
- Add firewall rules for tcp:22,80,443

### Step 8: Setup SSL/HTTPS (Recommended)

#### Using Let's Encrypt (Free)

```bash
# Install Certbot
sudo apt install -y certbot python3-certbot-nginx  # Ubuntu/Debian
# OR
sudo yum install -y certbot python3-certbot-nginx  # CentOS/RHEL

# Obtain certificate
sudo certbot --nginx -d your-domain.com -d www.your-domain.com

# Follow prompts:
# - Enter email
# - Agree to terms
# - Choose redirect (recommended)

# Auto-renewal (certbot sets this up automatically)
sudo certbot renew --dry-run
```

#### Manual Certificate

If you have your own certificate:

```bash
# Copy certificates
sudo mkdir -p /etc/nginx/ssl
sudo cp your-cert.crt /etc/nginx/ssl/
sudo cp your-key.key /etc/nginx/ssl/
sudo chmod 600 /etc/nginx/ssl/your-key.key

# Update Nginx config
sudo nano /etc/nginx/sites-available/riskshield
```

**Add to config:**
```nginx
server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /etc/nginx/ssl/your-cert.crt;
    ssl_certificate_key /etc/nginx/ssl/your-key.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # ... rest of config
}

server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}
```

### Step 9: Verify Deployment

#### Check All Services

```bash
# MongoDB
sudo systemctl status mongod

# Backend
sudo systemctl status riskshield-backend

# Nginx
sudo systemctl status nginx

# Check logs
sudo journalctl -u riskshield-backend -n 50
sudo tail -f /var/log/nginx/error.log
```

#### Test Application

```bash
# Test backend directly
curl http://localhost:8001/api/

# Test via Nginx
curl http://your-vm-ip/api/

# Test frontend
curl http://your-vm-ip/
```

#### Access Application

**Without Domain:**
- Frontend: http://your-vm-ip
- Backend: http://your-vm-ip/api
- API Docs: http://your-vm-ip/docs

**With Domain:**
- Frontend: https://your-domain.com
- Backend: https://your-domain.com/api
- API Docs: https://your-domain.com/docs

**Login:**
- LOD1: lod1@bank.com / password123
- LOD2: lod2@bank.com / password123

---

## 🔒 Security Hardening

### 1. MongoDB Security

#### Enable Authentication

```bash
# Connect to MongoDB
mongosh

# Create admin user
use admin
db.createUser({
  user: "admin",
  pwd: "StrongPassword123!",
  roles: ["userAdminAnyDatabase", "dbAdminAnyDatabase", "readWriteAnyDatabase"]
})

# Create application user
use riskshield_prod
db.createUser({
  user: "riskshield",
  pwd: "AnotherStrongPassword!",
  roles: [{role: "readWrite", db: "riskshield_prod"}]
})

exit
```

#### Configure MongoDB with Auth

```bash
sudo nano /etc/mongod.conf
```

**Add:**
```yaml
security:
  authorization: enabled

net:
  bindIp: 127.0.0.1
  port: 27017
```

**Restart:**
```bash
sudo systemctl restart mongod
```

**Update Backend `.env`:**
```bash
MONGO_URL="mongodb://riskshield:AnotherStrongPassword!@localhost:27017/riskshield_prod"
```

**Restart Backend:**
```bash
sudo systemctl restart riskshield-backend
```

### 2. SSH Hardening

```bash
sudo nano /etc/ssh/sshd_config
```

**Update:**
```bash
# Disable root login
PermitRootLogin no

# Disable password auth (use keys only)
PasswordAuthentication no

# Limit users
AllowUsers your-username

# Change default port (optional)
Port 2222
```

**Restart SSH:**
```bash
sudo systemctl restart sshd
```

### 3. Fail2Ban (Brute Force Protection)

```bash
# Install
sudo apt install -y fail2ban  # Ubuntu/Debian
# OR
sudo yum install -y fail2ban  # CentOS/RHEL

# Configure
sudo nano /etc/fail2ban/jail.local
```

**Add:**
```ini
[sshd]
enabled = true
port = ssh
logpath = /var/log/auth.log
maxretry = 3
bantime = 3600

[nginx-http-auth]
enabled = true
filter = nginx-http-auth
port = http,https
logpath = /var/log/nginx/error.log
maxretry = 5
bantime = 3600
```

**Start:**
```bash
sudo systemctl start fail2ban
sudo systemctl enable fail2ban
```

### 4. Regular Updates

```bash
# Setup automatic security updates (Ubuntu)
sudo apt install -y unattended-upgrades
sudo dpkg-reconfigure -plow unattended-upgrades

# Or manually update weekly:
sudo apt update && sudo apt upgrade -y
```

---

## 📊 Monitoring & Maintenance

### Log Locations

```bash
# Backend logs
sudo journalctl -u riskshield-backend -f

# Nginx access logs
sudo tail -f /var/log/nginx/access.log

# Nginx error logs
sudo tail -f /var/log/nginx/error.log

# MongoDB logs
sudo tail -f /var/log/mongodb/mongod.log

# System logs
sudo journalctl -xe
```

### Monitoring Commands

```bash
# System resources
htop
# OR
top

# Disk usage
df -h

# Memory usage
free -h

# Service status
sudo systemctl status riskshield-backend mongod nginx

# Active connections
ss -tulpn

# MongoDB stats
mongosh --eval "db.serverStatus()"
```

### Database Backup

#### Automated Daily Backup

```bash
# Create backup script
sudo nano /opt/backup-riskshield.sh
```

**Content:**
```bash
#!/bin/bash
DATE=$(date +%Y-%m-%d)
BACKUP_DIR="/opt/backups/riskshield"

mkdir -p $BACKUP_DIR

# Backup MongoDB
mongodump --db riskshield_prod --out $BACKUP_DIR/mongo-$DATE

# Compress
tar -czf $BACKUP_DIR/mongo-$DATE.tar.gz $BACKUP_DIR/mongo-$DATE
rm -rf $BACKUP_DIR/mongo-$DATE

# Keep only last 7 days
find $BACKUP_DIR -name "mongo-*.tar.gz" -mtime +7 -delete

echo "Backup completed: $DATE"
```

**Make executable:**
```bash
sudo chmod +x /opt/backup-riskshield.sh
```

**Add to crontab:**
```bash
sudo crontab -e

# Add line (runs daily at 2 AM):
0 2 * * * /opt/backup-riskshield.sh >> /var/log/backup-riskshield.log 2>&1
```

#### Manual Backup

```bash
# Backup
mongodump --db riskshield_prod --out /opt/backup-$(date +%Y-%m-%d)

# Restore
mongorestore --db riskshield_prod /opt/backup-2024-01-15/riskshield_prod
```

### Application Updates

```bash
# Pull latest code
cd /opt/riskshield
git pull origin main

# Update backend
cd backend
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart riskshield-backend

# Update frontend
cd ../frontend
yarn install
yarn build
sudo systemctl restart nginx

# Check status
sudo systemctl status riskshield-backend nginx
```

---

## 🐛 Troubleshooting

### Backend Won't Start

```bash
# Check logs
sudo journalctl -u riskshield-backend -n 100

# Common issues:

# 1. Port already in use
sudo lsof -i :8001
sudo kill -9 <PID>

# 2. MongoDB not running
sudo systemctl status mongod
sudo systemctl start mongod

# 3. Environment variables
cat /opt/riskshield/backend/.env
# Verify JWT_SECRET, MONGO_URL

# 4. Python errors
cd /opt/riskshield/backend
source venv/bin/activate
python -c "import server"
```

### Frontend Not Loading

```bash
# Check Nginx
sudo nginx -t
sudo systemctl status nginx

# Check build exists
ls -la /opt/riskshield/frontend/build/

# Check permissions
sudo chown -R www-data:www-data /opt/riskshield/frontend/build

# Check logs
sudo tail -f /var/log/nginx/error.log

# Rebuild frontend
cd /opt/riskshield/frontend
yarn build
sudo systemctl restart nginx
```

### Can't Connect from Browser

```bash
# Check firewall
sudo ufw status
sudo firewall-cmd --list-all

# Check if service is listening
sudo ss -tulpn | grep :80
sudo ss -tulpn | grep :8001

# Check from VM
curl http://localhost
curl http://localhost:8001/api/

# Check from outside
curl http://your-vm-ip

# Test specific port
telnet your-vm-ip 80
```

### Database Issues

```bash
# Check MongoDB status
sudo systemctl status mongod

# Check MongoDB logs
sudo tail -f /var/log/mongodb/mongod.log

# Test connection
mongosh

# If auth enabled:
mongosh -u riskshield -p AnotherStrongPassword! --authenticationDatabase riskshield_prod

# Check database
use riskshield_prod
db.users.count()
db.users.findOne()
```

### High Resource Usage

```bash
# Check resource usage
htop

# MongoDB resources
mongosh --eval "db.serverStatus().mem"

# Limit backend workers
# Edit /etc/systemd/system/riskshield-backend.service
# Change: --workers 4 to --workers 2
sudo systemctl daemon-reload
sudo systemctl restart riskshield-backend
```

---

## 📝 Useful Commands Reference

### Service Management

```bash
# Start/Stop/Restart
sudo systemctl start riskshield-backend
sudo systemctl stop riskshield-backend
sudo systemctl restart riskshield-backend

# Enable/Disable autostart
sudo systemctl enable riskshield-backend
sudo systemctl disable riskshield-backend

# View logs
sudo journalctl -u riskshield-backend -f
sudo journalctl -u riskshield-backend --since "1 hour ago"

# Check status
sudo systemctl status riskshield-backend mongod nginx
```

### Database Operations

```bash
# Connect
mongosh

# Show databases
show dbs

# Use database
use riskshield_prod

# Show collections
show collections

# Count documents
db.users.countDocuments()
db.assessments.countDocuments()

# Find documents
db.users.find().pretty()
db.assessments.find({status: "COMPLETED"})

# Backup
mongodump --db riskshield_prod --out /backup

# Restore
mongorestore --db riskshield_prod /backup/riskshield_prod
```

### Nginx Operations

```bash
# Test configuration
sudo nginx -t

# Reload configuration
sudo nginx -s reload

# Restart
sudo systemctl restart nginx

# View access logs
sudo tail -f /var/log/nginx/access.log

# View error logs
sudo tail -f /var/log/nginx/error.log

# Check configuration
sudo nginx -T
```

---

## ✅ Post-Deployment Checklist

- [ ] VM created with required specs
- [ ] System updated
- [ ] Python 3.11+ installed
- [ ] Node.js 18+ and Yarn installed
- [ ] MongoDB 7 installed and running
- [ ] Application code deployed
- [ ] Backend environment configured
- [ ] Frontend built successfully
- [ ] Systemd service created and running
- [ ] Nginx installed and configured
- [ ] Firewall configured
- [ ] SSL/HTTPS configured (if domain)
- [ ] MongoDB authentication enabled
- [ ] SSH hardened
- [ ] Fail2Ban configured
- [ ] Backup script created
- [ ] Monitoring setup
- [ ] Application accessible from browser
- [ ] Can login with demo credentials
- [ ] Can create assessment
- [ ] Documentation reviewed

---

## 🎯 Next Steps

1. **Configure Production Settings:**
   - Change all default passwords
   - Generate new JWT secret
   - Configure proper CORS origins
   - Review all environment variables

2. **Setup Monitoring:**
   - Install monitoring tools (Prometheus, Grafana)
   - Configure alerting
   - Setup log aggregation

3. **Performance Optimization:**
   - Configure MongoDB replica set
   - Setup Redis caching
   - Optimize Nginx
   - Enable compression

4. **High Availability:**
   - Deploy multiple backend instances
   - Setup load balancer
   - Configure database replication
   - Implement auto-scaling

---

**Deployment Time:** 30-60 minutes  
**Difficulty:** Intermediate  
**Support:** Review troubleshooting section for common issues  

**Your RiskShield platform is now live! 🚀**
