FROM node:20-bullseye

WORKDIR /app

RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

RUN git clone https://github.com/finger563/webgme-gridlabd.git webgme

WORKDIR /app/webgme

RUN sed -i'' "s#config\.mongo\.uri = 'mongodb://127.0.0.1:27017/gridlabd';#config.mongo.uri = process.env.MONGO_URL || 'mongodb://127.0.0.1:27017/gridlabd';#g" config/config.webgme.js \
 && sed -i'' "s#config\.mongo\.uri = 'mongodb://127.0.0.1:27017/gridlabd';#config.mongo.uri = process.env.MONGO_URL || 'mongodb://127.0.0.1:27017/gridlabd';#g" config/config.test.js

RUN npm install --legacy-peer-deps

# Overwrite the start script with exec version
RUN echo '#!/bin/bash\nexec npm start' > ./start-webgme-server.sh
RUN chmod +x ./start-webgme-server.sh

# Run it as the main process
CMD ["./start-webgme-server.sh"]
