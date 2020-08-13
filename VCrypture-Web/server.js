const path = require('path');
const http = require('http');
const express = require('express');
const session = require('express-session');
const mustacheExpress = require('mustache-express');
const redis = require('redis');
const RedisStore = require('connect-redis')(session);
const config = require('./config');
const dhimankasana = require('./routes/dhimankasana');
const naorshamir = require('./routes/naorshamir');
const taghaddoslatif = require('./routes/taghaddoslatif');

const { port, sessionConfig } = config.app;
const redisClient = redis.createClient({ host: config.redis.host, port: config.redis.port });
const app = express();

// Set session
app.use(session({
  ...sessionConfig,
  store: new RedisStore({ ...config.redis, client: redisClient })
}));

// Set template engine
app.engine('mustache', mustacheExpress());
app.set('view engine', 'mustache');
app.set('views', path.join(__dirname, 'views'));

// Routes
app.use(express.static(path.join(__dirname, 'views')));
app.get('/', (_, res) => { res.render('index'); });
app.use('/download', express.static(path.join(__dirname, 'views')));
app.use('/dhimankasana', express.static(path.join(__dirname, 'views')), dhimankasana);
app.use('/naorshamir', express.static(path.join(__dirname, 'views')), naorshamir);
app.use('/taghaddoslatif', express.static(path.join(__dirname, 'views')), taghaddoslatif);
app.get('/download/:filename', (req, res) => {
  const { apiIP, apiPort } = config.app;
  const options = {
    hostname: apiIP,
    port: apiPort,
    path: `/api/download/${req.params.filename}`
  };
  http.get(options, (resp) => {
    if (resp.statusCode === 404) {
      res.status(404).render('error', { error: 'Oops! 404 NOT FOUND' });
    } else {
      res.setHeader('content-disposition', resp.headers['content-disposition']);
      res.setHeader('content-type', resp.headers['content-type']);
      resp.pipe(res);
    }
  });
});
app.use((_, res) => { res.status(404).render('error', { error: 'Oops! 404 NOT FOUND' }); });

app.listen(port);
