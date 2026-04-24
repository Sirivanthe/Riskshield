# RiskShield - Local Development Setup Guide

Complete guide to run RiskShield on your local PC (Windows, Mac, Linux)

---

## 📋 Prerequisites

### Required Software

1. **Python 3.11+**
   - Windows: Download from [python.org](https://www.python.org/downloads/)
   - Mac: `brew install python@3.11`
   - Linux: `sudo apt install python3.11 python3.11-venv`

2. **Node.js 18+** and **Yarn**
   - Windows/Mac: Download from [nodejs.org](https://nodejs.org/)
   - Linux: `sudo apt install nodejs npm`
   - Install Yarn: `npm install -g yarn`

3. **MongoDB 7+**
   - Windows: Download from [mongodb.com](https://www.mongodb.com/try/download/community)
   - Mac: `brew tap mongodb/brew && brew install mongodb-community@7.0`
   - Linux: Follow [MongoDB Ubuntu guide](https://www.mongodb.com/docs/manual/tutorial/install-mongodb-on-ubuntu/)

4. **Git**
   - Download from [git-scm.com](https://git-scm.com/downloads)

### Recommended (Optional)
- **VS Code** or **PyCharm** for development
- **MongoDB Compass** for database visualization
- **Postman** for API testing

---

## 🚀 Quick Start (5 Minutes)

### Step 1: Clone/Download the Project

```bash
# If you have the code:
cd /path/to/riskshield

# Or clone from repository:
git clone <repository-url>
cd riskshield
```

### Step 2: Start MongoDB

**Windows:**
```cmd
# Start MongoDB service
net start MongoDB

# Or run directly:
"C:\Program Files\MongoDB\Server\7.0\bin\mongod.exe" --dbpath="C:\data\db"
```

**Mac:**
```bash
# Start MongoDB service
brew services start mongodb-community@7.0

# Or run directly:
mongod --config /usr/local/etc/mongod.conf
```

**Linux:**
```bash
# Start MongoDB service
sudo systemctl start mongod

# Check status
sudo systemctl status mongod
```

### Step 3: Setup Backend

```bash
cd backend

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Verify .env file exists
cat .env  # Should show MONGO_URL, JWT_SECRET, etc.

# Run backend
uvicorn server:app --reload --host 0.0.0.0 --port 8001
```

**Expected Output:**
```
INFO:     Will watch for changes in these directories: ['/path/to/backend']
INFO:     Uvicorn running on http://0.0.0.0:8001 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Application startup complete.
```

### Step 4: Setup Frontend (New Terminal)

```bash
cd frontend

# Install dependencies
yarn install

# Verify .env file
cat .env  # Should show REACT_APP_BACKEND_URL

# Start frontend
yarn start
```

**Expected Output:**
```
Compiled successfully!

You can now view frontend in the browser.

  Local:            http://localhost:3000
  On Your Network:  http://192.168.1.x:3000
```

### Step 5: Access the Application

**Frontend:** http://localhost:3000  
**Backend API:** http://localhost:8001  
**API Docs:** http://localhost:8001/docs  

**Demo Login:**
- LOD1: lod1@bank.com / password123
- LOD2: lod2@bank.com / password123

---

## 🔧 Detailed Setup Instructions

### Backend Configuration

#### 1. Environment Variables

Edit `backend/.env`:

```bash
# Database
MONGO_URL="mongodb://localhost:27017"
DB_NAME="riskshield_local"

# Security
JWT_SECRET="your-generated-secret-key-min-32-chars"
JWT_ALGORITHM="HS256"

# CORS (for local development)
CORS_ORIGINS="http://localhost:3000,http://127.0.0.1:3000"

# Environment
ENVIRONMENT="development"
```

**Generate JWT Secret:**
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

#### 2. Install Python Dependencies

```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

pip install --upgrade pip
pip install -r requirements.txt
```

**Common Issues:**

❌ **Error: `pip: command not found`**
```bash
# Use pip3 instead
pip3 install -r requirements.txt
```

❌ **Error: `Permission denied`**
```bash
# Use --user flag
pip install --user -r requirements.txt
```

❌ **Error: `Microsoft Visual C++ required` (Windows)**
- Download and install: [Microsoft C++ Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/)

#### 3. Database Initialization

The database auto-initializes on first run with:
- Demo users (lod1@bank.com, lod2@bank.com)
- Database indexes
- Sample workflow

**Manual Database Setup (if needed):**

```bash
# Connect to MongoDB
mongo

# Create database
use riskshield_local

# Create indexes manually
db.users.createIndex({"email": 1}, {unique: true})
db.assessments.createIndex({"created_by": 1})
db.assessments.createIndex({"status": 1})
db.assessments.createIndex({"created_at": -1})
```

#### 4. Run Backend

```bash
# Development mode (hot reload)
uvicorn server:app --reload --host 0.0.0.0 --port 8001

# Production mode
uvicorn server:app --host 0.0.0.0 --port 8001 --workers 4

# With logging
uvicorn server:app --reload --log-level debug
```

**Test Backend:**
```bash
curl http://localhost:8001/api/
# Should return: {"message":"Hello World"} or {"detail":"Not Found"}
```

### Frontend Configuration

#### 1. Environment Variables

Edit `frontend/.env`:

```bash
# Backend API URL
REACT_APP_BACKEND_URL=http://localhost:8001

# Development settings
WDS_SOCKET_PORT=3000
REACT_APP_ENABLE_VISUAL_EDITS=false
ENABLE_HEALTH_CHECK=false
```

#### 2. Install Node Dependencies

```bash
cd frontend

# Install yarn if not installed
npm install -g yarn

# Install dependencies
yarn install
```

**Common Issues:**

❌ **Error: `yarn: command not found`**
```bash
npm install -g yarn
# Or use npm instead:
npm install
npm start
```

❌ **Error: `EACCES: permission denied`**
```bash
# Mac/Linux:
sudo npm install -g yarn
# Or use nvm to manage Node versions
```

❌ **Error: `Node version too old`**
```bash
# Update Node.js to 18+
# Using nvm (recommended):
nvm install 18
nvm use 18
```

#### 3. Run Frontend

```bash
# Development mode
yarn start

# Production build
yarn build

# Serve production build
npx serve -s build -p 3000
```

**Test Frontend:**

Open browser: http://localhost:3000

---

## 🔍 Verification & Testing

### 1. Check All Services

```bash
# Backend health
curl http://localhost:8001/api/

# Frontend
curl http://localhost:3000

# MongoDB
mongo --eval "db.serverStatus()"
```

### 2. Test Login

```bash
curl -X POST http://localhost:8001/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"lod1@bank.com","password":"password123"}'
```

**Expected:** Returns JWT token

### 3. Test Assessment Creation

1. Open http://localhost:3000
2. Login as LOD1
3. Navigate to Assessments
4. Click "New Assessment"
5. Complete 3-step wizard
6. Verify assessment created

---

## 🐛 Troubleshooting

### Backend Issues

#### Port 8001 Already in Use

```bash
# Find process using port
# Mac/Linux:
lsof -i :8001
kill -9 <PID>

# Windows:
netstat -ano | findstr :8001
taskkill /PID <PID> /F

# Or use different port:
uvicorn server:app --reload --port 8002
```

#### MongoDB Connection Failed

```bash
# Check if MongoDB is running
# Mac/Linux:
sudo systemctl status mongod
ps aux | grep mongod

# Windows:
sc query MongoDB

# Check connection
mongo --eval "db.serverStatus()"

# If not running, start it:
# Mac: brew services start mongodb-community
# Linux: sudo systemctl start mongod
# Windows: net start MongoDB
```

#### Import Errors

```bash
# Reinstall dependencies
pip install --upgrade -r requirements.txt

# Check Python version
python --version  # Should be 3.11+

# Verify virtual environment is activated
which python  # Should point to venv/bin/python
```

### Frontend Issues

#### Port 3000 Already in Use

```bash
# Kill process on port 3000
# Mac/Linux:
lsof -i :3000
kill -9 <PID>

# Windows:
netstat -ano | findstr :3000
taskkill /PID <PID> /F

# Or set different port:
PORT=3001 yarn start
```

#### CORS Errors

**Error:** `Access to XMLHttpRequest blocked by CORS policy`

**Fix:** Update `backend/.env`:
```bash
CORS_ORIGINS="http://localhost:3000,http://localhost:3001,http://127.0.0.1:3000"
```

Restart backend after changing.

#### Module Not Found

```bash
# Clear cache and reinstall
rm -rf node_modules package-lock.json yarn.lock
yarn install

# Or use npm
rm -rf node_modules package-lock.json
npm install
```

#### Build Failures

```bash
# Increase Node memory
export NODE_OPTIONS="--max-old-space-size=4096"
yarn build

# Windows:
set NODE_OPTIONS=--max-old-space-size=4096
yarn build
```

### Database Issues

#### Database Empty / No Demo Users

```bash
# Access MongoDB
mongo

# Switch to database
use riskshield_local

# Check users
db.users.find()

# If empty, restart backend (auto-creates demo users)
```

#### Reset Database

```bash
mongo
use riskshield_local
db.dropDatabase()
# Restart backend to reinitialize
```

---

## 📊 Development Tools

### MongoDB Compass

**Connection String:**
```
mongodb://localhost:27017
```

**Navigate to:**
- Database: `riskshield_local`
- Collections: users, assessments, workflows, issues, etc.

### API Testing with Postman

**Import Collection:**

1. Open Postman
2. Import → Link → `http://localhost:8001/openapi.json`
3. Set base URL: `http://localhost:8001`

**Authentication:**

1. Login request:
   - POST `/api/auth/login`
   - Body: `{"email":"lod1@bank.com","password":"password123"}`
   - Save `access_token` from response

2. Add to requests:
   - Header: `Authorization: Bearer <token>`

### VS Code Setup

**Recommended Extensions:**
- Python
- Pylance
- ES7+ React/Redux/React-Native snippets
- ESLint
- Prettier
- MongoDB for VS Code

**Workspace Settings (`.vscode/settings.json`):**
```json
{
  "python.defaultInterpreterPath": "${workspaceFolder}/backend/venv/bin/python",
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": true,
  "python.formatting.provider": "black",
  "editor.formatOnSave": true,
  "[javascript]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  }
}
```

---

## 🔄 Common Development Workflows

### Adding a New Backend Endpoint

1. Add model to `server.py` (if needed)
2. Add endpoint function with `@api_router` decorator
3. Test with curl or Postman
4. Restart backend (auto-reloads in dev mode)

**Example:**
```python
@api_router.get("/test")
async def test_endpoint():
    return {"message": "Test successful"}
```

### Adding a New Frontend Page

1. Create file: `frontend/src/pages/NewPage.js`
2. Add route in `frontend/src/App.js`:
   ```javascript
   <Route path="/newpage" element={<NewPage />} />
   ```
3. Add navigation in `frontend/src/components/Layout.js`
4. Hot reload automatically updates

### Database Migrations

**Add New Collection:**

1. Define model in `server.py`
2. Add endpoint to create/read
3. Database auto-creates collection on first insert

**Add Index:**

```python
# In startup event
await db.new_collection.create_index("field_name")
```

---

## 📝 Useful Commands

### Backend

```bash
# Check Python version
python --version

# List installed packages
pip list

# Update requirements.txt
pip freeze > requirements.txt

# Run linting
pylint server.py

# Run formatting
black server.py

# Check for security issues
pip-audit
```

### Frontend

```bash
# Check Node/Yarn versions
node --version
yarn --version

# List installed packages
yarn list --depth=0

# Update packages
yarn upgrade-interactive

# Run linting
yarn lint

# Build for production
yarn build

# Analyze bundle size
yarn build && npx source-map-explorer 'build/static/js/*.js'
```

### Database

```bash
# Backup database
mongodump --db riskshield_local --out ./backup

# Restore database
mongorestore --db riskshield_local ./backup/riskshield_local

# Export collection to JSON
mongoexport --db riskshield_local --collection assessments --out assessments.json

# Import collection from JSON
mongoimport --db riskshield_local --collection assessments --file assessments.json

# MongoDB shell
mongo
use riskshield_local
db.users.find().pretty()
db.assessments.countDocuments()
```

---

## 🎯 Next Steps

### For Development

1. **Read the Code:**
   - Backend: `backend/server.py` (main application)
   - Frontend: `frontend/src/App.js` (main component)
   - Models: Check Pydantic models in server.py

2. **Explore API Docs:**
   - Open http://localhost:8001/docs
   - Interactive API testing with Swagger UI

3. **Review Documentation:**
   - `COMPREHENSIVE_FEATURE_SUMMARY.md` - Feature list
   - `COMPLETE_LIFECYCLE_FEATURES.md` - Full capabilities
   - `DEPLOYMENT_READINESS_REPORT.md` - Production checklist

### For Production Deployment

1. **Review VM Setup Guide:** `VM_DEPLOYMENT_GUIDE.md`
2. **Docker Deployment:** See `deploy/README.md`
3. **Kubernetes:** See `deploy/k8s-*.yaml` files

---

## 💡 Tips & Best Practices

### Development

- ✅ Always activate virtual environment before running backend
- ✅ Use separate terminal windows for backend and frontend
- ✅ Check backend logs for errors
- ✅ Use browser DevTools Network tab to debug API calls
- ✅ Keep MongoDB running in background

### Code Quality

- ✅ Follow PEP 8 for Python code
- ✅ Use ESLint recommendations for JavaScript
- ✅ Add type hints to Python functions
- ✅ Add PropTypes or TypeScript to React components
- ✅ Write meaningful commit messages

### Performance

- ✅ Use database indexes for frequently queried fields
- ✅ Paginate large result sets
- ✅ Cache API responses when appropriate
- ✅ Optimize frontend bundle size
- ✅ Use lazy loading for heavy components

---

## 📞 Support

### Getting Help

1. **Check Logs:**
   - Backend: Terminal output
   - Frontend: Browser console (F12)
   - MongoDB: Check mongod logs

2. **Common Issues:**
   - Review "Troubleshooting" section above
   - Check GitHub issues (if available)
   - Review deployment documentation

3. **Documentation:**
   - API Docs: http://localhost:8001/docs
   - ReDoc: http://localhost:8001/redoc
   - Feature docs: `COMPREHENSIVE_FEATURE_SUMMARY.md`

### Useful Resources

- **FastAPI:** https://fastapi.tiangolo.com/
- **React:** https://react.dev/
- **MongoDB:** https://docs.mongodb.com/
- **Pydantic:** https://docs.pydantic.dev/
- **Tailwind CSS:** https://tailwindcss.com/docs

---

## ✅ Checklist

Before starting development:

- [ ] Python 3.11+ installed
- [ ] Node.js 18+ and Yarn installed
- [ ] MongoDB 7+ installed and running
- [ ] Git installed
- [ ] Code editor (VS Code/PyCharm) installed
- [ ] Backend virtual environment created
- [ ] Backend dependencies installed
- [ ] Backend `.env` configured
- [ ] Frontend dependencies installed
- [ ] Frontend `.env` configured
- [ ] MongoDB running
- [ ] Backend running on port 8001
- [ ] Frontend running on port 3000
- [ ] Can login with demo credentials
- [ ] Can create an assessment

---

**Setup Time:** 15-30 minutes  
**Difficulty:** Beginner-Intermediate  
**Support:** Review troubleshooting section for common issues  

**Happy Coding! 🚀**
