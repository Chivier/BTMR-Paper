# Use Node.js 18 as base image
FROM node:18-slim

# Set working directory
WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy the rest of the frontend code
COPY . .

# Expose port
EXPOSE 3000

# Build the application
RUN npm run build

# Run the application with environment-based backend URL
CMD ["sh", "-c", "VITE_API_BASE_URL=${VITE_API_BASE_URL:-http://backend:8000} npm run preview -- --host 0.0.0.0 --port ${FRONTEND_PORT:-3000} --strictPort false"]
