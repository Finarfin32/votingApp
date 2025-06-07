var express = require('express'),
    async = require('async'),
    { Pool } = require('pg'),
    cookieParser = require('cookie-parser'),
    path = require('path'),
    app = express(),
    server = require('http').Server(app),
    io = require('socket.io')(server);

// Konfiguracja logowania
console.log('Starting application...');

// Dodajemy obsługę błędów
process.on('uncaughtException', function(err) {
    console.error('Uncaught Exception:', err);
});

process.on('unhandledRejection', function(err) {
    console.error('Unhandled Rejection:', err);
});

var port = process.env.PORT || 80;
console.log('Using port:', port);

// Konfiguracja Prometheus
try {
    const client = require('prom-client');
    const collectDefaultMetrics = client.collectDefaultMetrics;
    collectDefaultMetrics();
    console.log('Prometheus metrics initialized');
} catch (err) {
    console.error('Failed to initialize Prometheus metrics:', err);
}

io.on('connection', function (socket) {
  console.log('New client connected');
  socket.emit('message', { text : 'Welcome!' });

  socket.on('subscribe', function (data) {
    socket.join(data.channel);
  });
});

var pool = new Pool({
  connectionString: 'postgres://postgres:postgres@db/postgres'
});

console.log('Attempting to connect to database...');

async.retry(
  {times: 1000, interval: 1000},
  function(callback) {
    pool.connect(function(err, client, done) {
      if (err) {
        console.error("Waiting for db:", err);
      }
      callback(err, client);
    });
  },
  function(err, client) {
    if (err) {
      return console.error("Giving up:", err);
    }
    console.log("Connected to db");
    getVotes(client);
  }
);

function getVotes(client) {
  client.query('SELECT vote, COUNT(id) AS count FROM votes GROUP BY vote', [], function(err, result) {
    if (err) {
      console.error("Error performing query:", err);
    } else {
      var votes = collectVotesFromResult(result);
      io.sockets.emit("scores", JSON.stringify(votes));
    }

    setTimeout(function() {getVotes(client) }, 1000);
  });
}

function collectVotesFromResult(result) {
  var votes = {a: 0, b: 0};

  result.rows.forEach(function (row) {
    votes[row.vote] = parseInt(row.count);
  });

  return votes;
}

app.use(cookieParser());
app.use(express.urlencoded({ extended: true }));
app.use(express.static(__dirname + '/views'));
app.use('/media', express.static(__dirname + '/media'));

app.get('/', function (req, res) {
  res.sendFile(path.resolve(__dirname + '/views/index.html'));
});

app.get('/metrics', async (req, res) => {
  res.set('Content-Type', client.register.contentType);
  res.end(await client.register.metrics());
});

console.log('Starting server...');
server.listen(port, function () {
  console.log('App running on port ' + port);
});