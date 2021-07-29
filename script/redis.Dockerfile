FROM redis:6.2

RUN echo "vm.overcommit_memory = 1" > /etc/sysctl.conf

COPY ./script/redis.conf /usr/local/etc/redis/redis.conf
CMD [ "redis-server", "/usr/local/etc/redis/redis.conf" ]
