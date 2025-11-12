#!/bin/bash

# PDF Transcriber Setup Script
# This script sets up the entire application including backend and frontend

set -e  # Exit on error

echo "========================================="
echo "PDF Transcriber Setup"
echo "========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

# Check if Python 3 is installed
echo "Checking dependencies..."
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi
print_status "Python 3 found: $(python3 --version)"

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    print_error "Node.js is not installed. Please install Node.js 16 or higher."
    exit 1
fi
print_status "Node.js found: $(node --version)"

# Check if npm is installed
if ! command -v npm &> /dev/null; then
    print_error "npm is not installed. Please install npm."
    exit 1
fi
print_status "npm found: $(npm --version)"

echo ""
echo "========================================="
echo "Setting up Backend..."
echo "========================================="

# Create Python virtual environment
echo "Creating Python virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    print_status "Virtual environment created"
else
    print_warning "Virtual environment already exists"
fi

# Activate virtual environment
source venv/bin/activate
print_status "Virtual environment activated"

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip > /dev/null 2>&1
print_status "pip upgraded"

# Install Python dependencies
echo "Installing Python dependencies (this may take a while)..."
pip install -r backend/requirements.txt
print_status "Python dependencies installed"

# Create necessary directories
echo "Creating required directories..."
mkdir -p backend/uploads
mkdir -p backend/temp
mkdir -p backend/output
mkdir -p logs
print_status "Directories created"

echo ""
echo "========================================="
echo "Setting up Frontend..."
echo "========================================="

# Install Node.js dependencies
cd frontend
echo "Installing Node.js dependencies (this may take a while)..."
npm install
print_status "Node.js dependencies installed"
cd ..

echo ""
echo "========================================="
echo "Checking Optional Dependencies..."
echo "========================================="

# Check for Ollama
if command -v ollama &> /dev/null; then
    print_status "Ollama found: $(ollama --version 2>&1 | head -n 1)"
    echo ""
    echo "Checking available Ollama models..."
    if ollama list &> /dev/null; then
        echo "Available models:"
        ollama list
    else
        print_warning "Could not list Ollama models"
    fi
    echo ""
    print_warning "If you want to use Ollama for markdown cleanup, make sure you have a model pulled."
    echo "  Suggested: ollama pull llama2:7b"
    echo "  Or: ollama pull mistral:7b"
else
    print_warning "Ollama not found. Install from https://ollama.ai for markdown cleanup features."
fi

echo ""
echo "========================================="
echo "Setup Complete!"
echo "========================================="
echo ""
echo "To start the application:"
echo ""
echo "1. Start the backend server:"
echo "   ${GREEN}source venv/bin/activate${NC}"
echo "   ${GREEN}python backend/main.py${NC}"
echo ""
echo "2. In a new terminal, start the Electron app:"
echo "   ${GREEN}cd frontend${NC}"
echo "   ${GREEN}npm run electron:dev${NC}"
echo ""
echo "Or run both with the quick start script:"
echo "   ${GREEN}./start.sh${NC}"
echo ""
echo "For production build:"
echo "   ${GREEN}cd frontend && npm run electron:build${NC}"
echo ""
echo "Configuration can be modified in:"
echo "   ${YELLOW}config/default_config.yaml${NC}"
echo ""
print_status "Happy transcribing!"
