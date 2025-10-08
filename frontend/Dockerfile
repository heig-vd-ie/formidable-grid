FROM node:20-alpine

WORKDIR /app
COPY package*.json ./
RUN npm install

COPY . .

EXPOSE ${VITE_FRONTEND_PORT}
CMD ["npm", "run", "dev", "--", "--host"]
