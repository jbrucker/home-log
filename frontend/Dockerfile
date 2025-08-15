# Step 1: Build the Vue.js app
FROM node:18 AS builder

#  Enable Web Crypto API support, needed for Vue/Vite
ENV NODE_OPTIONS="--openssl-legacy-provider"

WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
# Build with Vite
RUN npm run build  # Outputs to /app/dist

# Step 2: Serve the built files with Nginx
FROM nginx:alpine as production

COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
