FROM drone/drone-runner-docker:1
COPY agent.sh /agent.sh
COPY vendor/ssm_get_parameter /bin/
ADD vendor/busybox.tar.xz /
RUN chmod +x /bin/ssm_get_parameter
RUN chmod +x /agent.sh
ENTRYPOINT ["/agent.sh"]
