FROM nginx:1.21

RUN rm /etc/nginx/conf.d/default.conf
COPY ./script/beevenue.conf /etc/nginx/conf.d/
