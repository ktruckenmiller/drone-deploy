FROM drone/drone:1.6.4
COPY vendor/ssm_get_parameter /bin/
COPY server.sh /server.sh
ADD vendor/busybox.tar.xz /
RUN chmod +x /bin/ssm_get_parameter
RUN chmod +x /server.sh
ENV DRONE_GITHUB=true
ENV DRONE_DATABASE_DRIVER=mysql
ENV DRONE_SERVER_PROTO=https
ENTRYPOINT ["/server.sh"]
