#!/bin/bash

# Quick start script for PDF Transcriber
# Starts both backend and frontend in parallel

set -e

echo "Starting PDF Transcriber..."
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Virtual environment not found. Please run ./setup.sh first."
    exit 1
fi

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "Shutting down..."
    kill $(jobs -p) 2>/dev/null
    exit
}

trap cleanup SIGINT SIGTERM

# Start backend
echo "Starting backend server..."
source venv/bin/activate
python backend/main.py &
BACKEND_PID=$!

# Wait a bit for backend to start
sleep 3

# Start frontend
echo "Starting Electron app..."
cd frontend
npm run electron:dev &
FRONTEND_PID=$!

cd ..

echo ""
echo "PDF Transcriber is running!"
echo "Backend PID: $BACKEND_PID"
echo "Frontend PID: $FRONTEND_PID"
echo ""
echo "Press Ctrl+C to stop all services"

# Wait for processes
wait
