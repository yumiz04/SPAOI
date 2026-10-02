# Imagen multi-etapa: Node compila, nginx sirve. El proxy /agent se resuelve dentro
# de la red de Docker, asi que el navegador siempre habla del mismo origen.
FROM node:24-alpine AS build

WORKDIR /app

# Se copian los manifiestos primero para que la cache de capas sobreviva a cambios
# en el codigo: `npm ci` solo se vuelve a ejecutar cuando cambian las dependencias.
COPY package.json package-lock.json ./
RUN npm ci

COPY . .
RUN npm run build

FROM nginx:1.29-alpine AS runtime

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80

HEALTHCHECK --interval=10s --timeout=3s --start-period=5s --retries=5 \
    CMD wget --quiet --tries=1 --spider http://localhost/ || exit 1

CMD ["nginx", "-g", "daemon off;"]