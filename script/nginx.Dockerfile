FROM nginx:1.21
ARG NGINX_CONF="beevenue.conf"

RUN rm /etc/nginx/conf.d/default.conf
COPY ./script/${NGINX_CONF} /etc/nginx/conf.d/beevenue.conf
