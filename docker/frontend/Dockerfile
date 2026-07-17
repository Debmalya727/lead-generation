# Stage 1: Base image with Node 22 LTS
FROM node:22-alpine AS base
WORKDIR /app
COPY package*.json ./

# Stage 2: Development target (used by Docker Compose in dev environment)
FROM base AS development
ENV NODE_ENV=development
RUN npm install
COPY . .
EXPOSE 5173
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "5173"]

# Stage 3: Build production bundle
FROM base AS builder
ENV NODE_ENV=production
RUN npm ci
COPY . .
RUN npm run build

# Stage 4: Production target (Nginx serving static bundle)
FROM nginx:alpine AS production
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]