FROM node:20-slim
ARG WORKLOAD=minimal
WORKDIR /app
COPY package.json .
RUN if [ "$WORKLOAD" = "deps" ]; then npm install --omit=dev; fi
COPY server_${WORKLOAD}.js server.js
CMD ["node", "server.js"]