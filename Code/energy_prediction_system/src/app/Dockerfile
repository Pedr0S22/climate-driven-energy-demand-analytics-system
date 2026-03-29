# Estágio 1: Build
FROM node:18-alpine AS build-stage
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

# Estágio 2: Produção (Servir os ficheiros)
FROM nginx:stable-alpine
# Copiar o build do estágio anterior para o Nginx
COPY --from=build-stage /app/dist /usr/share/nginx/html
# Copiar configuração customizada do Nginx se necessário
# COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]