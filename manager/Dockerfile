FROM docker:28-cli
RUN apk add --no-cache python3 py3-flask
WORKDIR /app
COPY app.py .
EXPOSE 2380
CMD ["python3", "app.py"]

