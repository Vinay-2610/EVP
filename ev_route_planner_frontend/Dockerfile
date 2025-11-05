# Use Node 20
FROM node:20-alpine

# Set working directory
WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy all files
COPY . .

# Build arguments for environment variables
ARG VITE_GOOGLE_MAPS_KEY
ARG VITE_API_URL

# Set environment variables for build
ENV VITE_GOOGLE_MAPS_KEY=$VITE_GOOGLE_MAPS_KEY
ENV VITE_API_URL=$VITE_API_URL

# Build the app
RUN npm run build

# Expose port
EXPOSE 3000

# Start the app
CMD ["npm", "start"]
