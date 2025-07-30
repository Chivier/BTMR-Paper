#!/bin/bash

# Start up the backend server in background
echo "Starting backend server..."
uvicorn src.api.main:app --host 0.0.0.0 --port 8000 &

# Start up the frontend web server in foreground
echo "Starting frontend web server..."
cd frontend
npm install
npm run dev -- --host 0.0.0.0 --port 3000
