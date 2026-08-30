FROM node:22-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install --omit=dev
COPY publish.mjs ./
ENTRYPOINT ["node", "/app/publish.mjs"]
