FROM node:14.7

ENV NODE_ENV production
ENV APP_DIR /usr/src/app
ENV APP_PORT 80

WORKDIR $APP_DIR

COPY package*.json ./

RUN npm ci --only production

COPY . .

EXPOSE $APP_PORT

CMD ["node", "server.js"]
