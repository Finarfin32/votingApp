from flask import Flask, render_template, request, make_response, g, send_from_directory
from redis import Redis
import os
import socket
import random
import json
import logging
from prometheus_client import start_http_server, Counter, Summary

# Konfiguracja logowania
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Inicjalizacja metryk Prometheus
vote_counter = Counter('vote_total', 'Total number of votes', ['vote'])
REQUEST_TIME = Summary('vote_request_processing_seconds', 'Time spent processing vote requests')

option_a = os.getenv('OPTION_A', "Cats")
option_b = os.getenv('OPTION_B', "Dogs")
hostname = socket.gethostname()

app = Flask(__name__)

try:
    # Uruchomienie serwera Prometheus na osobnym porcie
    start_http_server(9091)
    logger.info("Prometheus metrics server started on port 9091")
except Exception as e:
    logger.error(f"Failed to start Prometheus metrics server: {e}")

gunicorn_error_logger = logging.getLogger('gunicorn.error')
app.logger.handlers.extend(gunicorn_error_logger.handlers)
app.logger.setLevel(logging.INFO)

# Konfiguracja serwowania plików statycznych
app.static_folder = 'static'
app.static_url_path = '/static'

# Dodajemy specjalną regułę dla plików z katalogu media
@app.route('/media/<path:filename>')
def serve_media(filename):
    return send_from_directory('/usr/local/app/media', filename)

def get_redis():
    if not hasattr(g, 'redis'):
        try:
            g.redis = Redis(host="redis", db=0, socket_timeout=5)
            logger.info("Connected to Redis")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise
    return g.redis

@app.route("/", methods=['POST','GET'])
@REQUEST_TIME.time()
def hello():
    try:
        voter_id = request.cookies.get('voter_id')
        if not voter_id:
            voter_id = hex(random.getrandbits(64))[2:-1]

        vote = None

        if request.method == 'POST':
            redis = get_redis()
            vote = request.form['vote']
            app.logger.info('Received vote for %s', vote)
            data = json.dumps({'voter_id': voter_id, 'vote': vote})
            redis.rpush('votes', data)
            # Zliczanie głosów w Prometheus
            vote_counter.labels(vote=vote).inc()

        resp = make_response(render_template(
            'index.html',
            option_a=option_a,
            option_b=option_b,
            hostname=hostname,
            vote=vote,
        ))
        resp.set_cookie('voter_id', voter_id)
        return resp
    except Exception as e:
        logger.error(f"Error in hello route: {e}")
        return "Internal Server Error", 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=80, debug=True, threaded=True)
