#!/bin/bash

# BTMR Paper Service Startup Script
# This script starts the complete BTMR Paper processing service with database support

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check if a port is in use
is_port_in_use() {
    lsof -i :$1 >/dev/null 2>&1
}

# Function to kill process on port
kill_port() {
    if is_port_in_use $1; then
        print_warning "Port $1 is in use. Killing existing process..."
        lsof -ti :$1 | xargs kill -9 2>/dev/null || true
        sleep 2
    fi
}

# Function to wait for service to be ready
wait_for_service() {
    local url=$1
    local service_name=$2
    local max_attempts=30
    local attempt=1
    
    print_status "Waiting for $service_name to be ready..."
    
    while [ $attempt -le $max_attempts ]; do
        # Try multiple approaches to check if service is ready
        
        # First check if port is responding
        local port=$(echo "$url" | sed -n 's/.*:\([0-9]*\).*/\1/p')
        if [ -n "$port" ]; then
            if nc -z localhost "$port" 2>/dev/null; then
                # Port is open, now try HTTP request
                if curl -s --max-time 5 "$url" >/dev/null 2>&1; then
                    print_success "$service_name is ready!"
                    return 0
                elif curl -s --max-time 5 -I "$url" 2>/dev/null | head -n 1 | grep -q "200\|404"; then
                    # Even 404 means the server is responding
                    print_success "$service_name is ready!"
                    return 0
                fi
            fi
        else
            # Fallback to direct curl if we can't extract port
            if curl -s --max-time 5 "$url" >/dev/null 2>&1; then
                print_success "$service_name is ready!"
                return 0
            fi
        fi
        
        echo -n "."
        sleep 2
        attempt=$((attempt + 1))
    done
    
    print_error "$service_name failed to start within timeout"
    print_status "Checking what might be wrong..."
    
    # Debug information
    if [ -n "$port" ]; then
        if nc -z localhost "$port" 2>/dev/null; then
            print_warning "Port $port is open but HTTP requests are failing"
        else
            print_warning "Port $port is not accessible"
        fi
    fi
    
    # Show recent log entries if available
    if [ "$service_name" = "Backend" ] && [ -f "logs/backend.log" ]; then
        print_status "Recent backend log entries:"
        tail -n 5 logs/backend.log 2>/dev/null || echo "No log entries found"
    fi
    
    return 1
}

# Cleanup function
cleanup() {
    print_status "Shutting down services..."
    
    # Kill backend if running
    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null || true
    fi
    
    # Kill frontend if running
    kill_port 3000
    kill_port 8000
    
    print_success "Services stopped"
}

# Set up signal handlers
trap cleanup EXIT INT TERM

# Main startup sequence
main() {
    echo "=============================================="
    echo "      BTMR Paper Service Startup"
    echo "=============================================="
    echo ""
    
    # Check system requirements
    print_status "Checking system requirements..."
    
    if ! command_exists uv; then
        print_error "uv is required but not installed. Please install uv: https://docs.astral.sh/uv/getting-started/installation/"
        exit 1
    fi
    
    if ! command_exists node; then
        print_error "Node.js is required but not installed"
        exit 1
    fi
    
    if ! command_exists npm; then
        print_error "npm is required but not installed"
        exit 1
    fi
    
    print_success "System requirements check passed"
    
    # Create necessary directories
    print_status "Creating necessary directories..."
    mkdir -p output
    mkdir -p uploads
    mkdir -p logs
    
    # Install Python dependencies using uv
    print_status "Installing Python dependencies with uv..."
    if [ -f "pyproject.toml" ]; then
        uv sync --group all >/dev/null 2>&1 || {
            print_error "Failed to install Python dependencies with uv"
            exit 1
        }
    else
        print_error "pyproject.toml not found. This project requires uv and pyproject.toml"
        exit 1
    fi
    
    # Install Playwright browsers
    print_status "Installing Playwright browsers..."
    uv run playwright install chromium >/dev/null 2>&1 || {
        print_warning "Failed to install Playwright browsers, will try again..."
        # Try with more verbose output to see what's wrong
        uv run playwright install chromium || {
            print_error "Failed to install Playwright browsers"
            print_status "You may need to manually run: uv run playwright install chromium"
        }
    }
    
    # Initialize database
    print_status "Initializing database..."
    uv run python -c "
from src.database import DatabaseMetadataManager
import os

try:
    # Create metadata manager (will initialize SQLite database)
    metadata_manager = DatabaseMetadataManager()
    
    # Check if CSV file exists and migrate
    csv_path = 'output/paper_metadata.csv'
    if os.path.exists(csv_path):
        print('Found existing CSV metadata, migrating to database...')
        success = metadata_manager.migrate_from_csv(csv_path)
        if success:
            print('Migration successful!')
            # Backup the original CSV file
            os.rename(csv_path, csv_path + '.backup')
            print('Original CSV backed up as paper_metadata.csv.backup')
        else:
            print('Migration failed, but database is initialized')
    else:
        print('No existing CSV found, database initialized with empty schema')
    
    # Test database health
    health = metadata_manager.health_check()
    if health['healthy']:
        print('Database health check passed')
    else:
        print('Database health check failed')
        exit(1)
        
except Exception as e:
    print(f'Database initialization failed: {e}')
    exit(1)
" || {
        print_error "Database initialization failed"
        exit 1
    }
    
    print_success "Database initialized successfully"
    
    # Kill any existing services on the ports we need
    kill_port 8000
    kill_port 3000
    
    # Start backend server
    print_status "Starting backend server on port 8000..."
    nohup uv run uvicorn src.api.main:app --host 0.0.0.0 --port 8000 > logs/backend.log 2>&1 &
    BACKEND_PID=$!
    
    # Wait for backend to be ready
    if ! wait_for_service "http://localhost:8000/health" "Backend"; then
        print_error "Backend failed to start"
        exit 1
    fi
    
    # Install frontend dependencies
    print_status "Installing frontend dependencies..."
    cd frontend
    if [ -f "package.json" ]; then
        npm install >/dev/null 2>&1 || {
            print_error "Failed to install frontend dependencies"
            exit 1
        }
    else
        print_error "Frontend package.json not found"
        exit 1
    fi
    
    # Start frontend server
    print_status "Starting frontend server on port 3000..."
    npm run dev -- --host 0.0.0.0 --port 3000 > ../logs/frontend.log 2>&1 &
    FRONTEND_PID=$!
    
    # Wait for frontend to be ready
    if ! wait_for_service "http://localhost:3000" "Frontend"; then
        print_error "Frontend failed to start"
        exit 1
    fi
    
    echo ""
    echo "=============================================="
    print_success "BTMR Paper Service Started Successfully!"
    echo "=============================================="
    echo ""
    echo "🌐 Frontend: http://localhost:3000"
    echo "🔧 Backend API: http://localhost:8000"
    echo "📚 API Documentation: http://localhost:8000/docs"
    echo "📊 Database: SQLite (output/paper_metadata.db)"
    echo ""
    echo "📋 Logs:"
    echo "  - Backend: logs/backend.log"
    echo "  - Frontend: logs/frontend.log"
    echo ""
    echo "Press Ctrl+C to stop all services"
    echo "=============================================="
    
    # Keep the script running and monitor services
    while true; do
        # Check if backend is still running
        if ! kill -0 $BACKEND_PID 2>/dev/null; then
            print_error "Backend process died unexpectedly"
            exit 1
        fi
        
        # Check if frontend is still running
        if ! kill -0 $FRONTEND_PID 2>/dev/null; then
            print_error "Frontend process died unexpectedly"
            exit 1
        fi
        
        sleep 5
    done
}

# Check if running with arguments
case "${1:-}" in
    "stop")
        print_status "Stopping BTMR Paper services..."
        kill_port 8000
        kill_port 3000
        print_success "All services stopped"
        exit 0
        ;;
    "status")
        echo "Service Status:"
        if is_port_in_use 8000; then
            print_success "Backend: Running on port 8000"
        else
            print_error "Backend: Not running"
        fi
        
        if is_port_in_use 3000; then
            print_success "Frontend: Running on port 3000"
        else
            print_error "Frontend: Not running"
        fi
        exit 0
        ;;
    "restart")
        print_status "Restarting BTMR Paper services..."
        kill_port 8000
        kill_port 3000
        sleep 3
        exec "$0"
        ;;
    "help"|"-h"|"--help")
        echo "BTMR Paper Service Management Script"
        echo ""
        echo "Usage: $0 [COMMAND]"
        echo ""
        echo "Commands:"
        echo "  (no args)  Start all services"
        echo "  stop       Stop all services"
        echo "  restart    Restart all services"
        echo "  status     Show service status"
        echo "  help       Show this help message"
        echo ""
        exit 0
        ;;
    "")
        # Default behavior - start services
        main
        ;;
    *)
        print_error "Unknown command: $1"
        echo "Use '$0 help' for usage information"
        exit 1
        ;;
esac
