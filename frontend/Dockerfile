# Stage 1: Build the Vue App
FROM node:26-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .

ARG VITE_API_URL
ENV VITE_API_URL=$VITE_API_URL

# This compiles everything into the /dist folder
RUN npm run build 

# Stage 2: Serve with an internal Nginx
FROM nginx:alpine
# Copy the compiled static files from the builder stage
COPY --from=builder /app/dist /usr/share/nginx/html

# Expose port 80 inside the container (which docker-compose maps to 8080 for NPM)
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]