# Step 1: Build the Vue.js app
# Crypto hash method requires node 20.12.0 (or 21.7.0) or higher
FROM node:20.19.0 AS builder

# Disable unnecessary Vite optimizations?
ENV CI=true

WORKDIR /app
COPY package*.json ./
# Install dependencies first (new layer in image) to use Docker cache
# "npm ci" uses `package-lock.json` to guarantee consistent installs
RUN npm ci --prefer-offline --no-audit --progress=false

# Standard copy & build with Vite
COPY . .
RUN npm run build  # Outputs to /app/dist

# Step 2: Serve the built files with Nginx
FROM nginx:alpine AS production

COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
