FROM node:alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .

FROM nginx:alpine
COPY --from=build /app/build /usr/share/nginx/html
# fix up permissions to allow the nginx user to start nginx
RUN mkdir -p /var/cache/nginx && chown nginx:nginx /var/cache/nginx && chmod 1777 /var/run
USER nginx

EXPOSE 80
HEALTHCHECK CMD curl --fail http://localhost || exit 1
CMD ["nginx", "-g", "daemon off;"]
# CMD ["ls", "-la", "/var/cache/nginx"]
