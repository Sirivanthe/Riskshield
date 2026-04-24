#!/bin/bash

# RiskShield - Quick Start Script for Local Development
# This script sets up and runs RiskShield on your local machine

set -e  # Exit on error

echo "====================================="
echo "  RiskShield - Quick Start Setup"
echo "====================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}! $1${NC}"
}

print_info() {
    echo -e "$1"
}

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Step 1: Check Prerequisites
print_info "Step 1: Checking prerequisites..."
echo ""

if command_exists python3; then
    PYTHON_VERSION=$(python3 --version | awk '{print $2}')
    print_success "Python found: $PYTHON_VERSION"
else
    print_error "Python 3 not found. Please install Python 3.11+"
    exit 1
fi

if command_exists node; then
    NODE_VERSION=$(node --version)
    print_success "Node.js found: $NODE_VERSION"
else
    print_error "Node.js not found. Please install Node.js 18+"
    exit 1
fi

if command_exists yarn; then
    YARN_VERSION=$(yarn --version)
    print_success "Yarn found: $YARN_VERSION"
else
    print_warning "Yarn not found. Installing..."
    npm install -g yarn
fi

if command_exists mongod; then
    print_success "MongoDB found"
else
    print_error "MongoDB not found. Please install MongoDB 7+"
    print_info "Visit: https://www.mongodb.com/try/download/community"
    exit 1
fi

echo ""

# Step 2: Check if MongoDB is running
print_info "Step 2: Checking MongoDB status..."
if pgrep -x "mongod" > /dev/null; then
    print_success "MongoDB is running"
else
    print_warning "MongoDB is not running. Attempting to start..."
    
    # Try to start MongoDB based on OS
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        brew services start mongodb-community >/dev/null 2>&1 || \
        mongod --config /usr/local/etc/mongod.conf --fork >/dev/null 2>&1
    else
        # Linux
        sudo systemctl start mongod >/dev/null 2>&1 || \
        mongod --fork --logpath /var/log/mongodb/mongod.log >/dev/null 2>&1
    fi
    
    sleep 2
    
    if pgrep -x "mongod" > /dev/null; then
        print_success "MongoDB started successfully"
    else
        print_error "Failed to start MongoDB. Please start it manually."
        exit 1
    fi
fi

echo ""

# Step 3: Setup Backend
print_info "Step 3: Setting up backend..."

if [ ! -d "backend/venv" ]; then
    print_info "Creating Python virtual environment..."
    cd backend
    python3 -m venv venv
    cd ..
    print_success "Virtual environment created"
else
    print_success "Virtual environment already exists"
fi

print_info "Installing Python dependencies..."
cd backend
source venv/bin/activate
pip install -q --upgrade pip
pip install -q -r requirements.txt
cd ..
print_success "Python dependencies installed"

echo ""

# Step 4: Setup Frontend
print_info "Step 4: Setting up frontend..."

if [ ! -d "frontend/node_modules" ]; then
    print_info "Installing Node dependencies (this may take a few minutes)..."
    cd frontend
    yarn install --silent
    cd ..
    print_success "Node dependencies installed"
else
    print_success "Node dependencies already installed"
fi

echo ""

# Step 5: Check configuration
print_info "Step 5: Checking configuration..."

if [ ! -f "backend/.env" ]; then
    print_warning "Backend .env file not found. Creating from template..."
    cat > backend/.env << EOF
MONGO_URL="mongodb://localhost:27017"
DB_NAME="riskshield_local"
JWT_SECRET="$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')"
JWT_ALGORITHM="HS256"
CORS_ORIGINS="http://localhost:3000,http://127.0.0.1:3000"
ENVIRONMENT="development"
EOF
    print_success "Backend .env file created"
else
    print_success "Backend .env file exists"
fi

if [ ! -f "frontend/.env" ]; then
    print_warning "Frontend .env file not found. Creating from template..."
    cat > frontend/.env << EOF
REACT_APP_BACKEND_URL=http://localhost:8001
WDS_SOCKET_PORT=3000
REACT_APP_ENABLE_VISUAL_EDITS=false
ENABLE_HEALTH_CHECK=false
EOF
    print_success "Frontend .env file created"
else
    print_success "Frontend .env file exists"
fi

echo ""
echo "====================================="
echo "  Setup Complete!"
echo "====================================="
echo ""

print_info "To start the application, run:"
echo ""
echo "  Terminal 1 (Backend):"
echo "    cd backend"
echo "    source venv/bin/activate"
echo "    uvicorn server:app --reload --host 0.0.0.0 --port 8001"
echo ""
echo "  Terminal 2 (Frontend):"
echo "    cd frontend"
echo "    yarn start"
echo ""
print_info "Or use the start script:"
echo "  ./scripts/start.sh"
echo ""
print_info "Access the application:"
echo "  Frontend: http://localhost:3000"
echo "  Backend:  http://localhost:8001"
echo "  API Docs: http://localhost:8001/docs"
echo ""
print_info "Demo credentials:"
echo "  LOD1: lod1@bank.com / password123"
echo "  LOD2: lod2@bank.com / password123"
echo ""
print_success "Happy coding! 🚀"
