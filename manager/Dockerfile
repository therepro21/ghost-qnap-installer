FROM docker:28-cli
RUN apk add --no-cache python3 py3-flask
WORKDIR /app
COPY app.py .
COPY qnap_app.py start.sh ./
EXPOSE 2380
CMD ["/bin/sh", "/app/start.sh"]
