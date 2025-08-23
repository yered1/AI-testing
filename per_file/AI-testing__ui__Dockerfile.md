# File: AI-testing/ui/Dockerfile

- Size: 294 bytes
- Kind: text
- SHA256: 608b65f7564ea514ea4cbb17f18737e2e3462336a115900e4e0e1b2071e45eb0

## Head (first 60 lines)

```

# Build stage
FROM node:20-bookworm as build
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm install --no-audit --no-fund
COPY . .
RUN npm run build

# Serve stage
FROM nginx:1.25-alpine
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx","-g","daemon off;"]
```

