# =============================================================================
# UniWebsite - Gunicorn Production Configuration
# =============================================================================
# Optimized for HIGH CONCURRENCY (thousands daily, hundreds simultaneous)
# Uses gevent async workers - each worker handles 1000+ connections
# =============================================================================

import os

# ===== BINDING =====
bind = "0.0.0.0:" + os.environ.get("PORT", "5006")

# ===== WORKER CLASS =====
# gevent async workers: each worker handles THOUSANDS of concurrent connections
# Unlike sync workers (1 request per worker), gevent uses green threads
# to handle many requests concurrently — essential for AI API calls (I/O-bound)
worker_class = "gevent"

# ===== NUMBER OF WORKERS =====
# With gevent, fewer workers are needed because each handles many connections.
# Server: 3 CPU cores, ~1 GB available RAM
# 3 workers × 1000 connections each = 3000 concurrent connections capacity
workers = 3

# ===== CONNECTIONS PER WORKER =====
# Each gevent worker can handle this many simultaneous connections
worker_connections = 1000

# ===== TIMEOUTS =====
# AI chatbot calls (Gemini/OpenRouter/Groq) can take significant time
timeout = 120
graceful_timeout = 30
keepalive = 5

# ===== REQUEST LIMITS =====
# Max requests before worker restart (prevents memory leaks)
max_requests = 2000
max_requests_jitter = 200

# ===== LOGGING =====
accesslog = "-"  # stdout (captured by PM2)
errorlog = "-"   # stderr (captured by PM2)
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" in %(D)sμs'

# ===== PROCESS NAMING =====
proc_name = "uniwebsite"

# ===== PRELOADING =====
# Preload app to share memory across workers and detect errors early
preload_app = True

# ===== FORWARDED HEADERS =====
# Trust proxy headers (behind Nginx/Caddy reverse proxy)
forwarded_allow_ips = "*"

# ===== SERVER HOOKS =====
def on_starting(server):
    """Called just before the master process is initialized."""
    print("=" * 60)
    print("  🎓 UniWebsite - Starting Production Server")
    print(f"  Workers: {workers} × gevent (async)")
    print(f"  Connections/worker: {worker_connections}")
    print(f"  Total capacity: ~{workers * worker_connections} concurrent connections")
    print("=" * 60)

def post_fork(server, worker):
    """Called just after a worker has been forked."""
    server.log.info(f"Worker spawned (pid: {worker.pid})")

def when_ready(server):
    """Called just after the server is started."""
    server.log.info("Server is ready. Spawning workers")

def worker_abort(worker):
    """Called when a worker receives the SIGABRT signal (timeout)."""
    worker.log.info(f"Worker received SIGABRT signal (pid: {worker.pid})")
