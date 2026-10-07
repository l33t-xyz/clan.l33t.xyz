import os

bind = "127.0.0.1:" + os.environ.get("CLAN_PORT", "18461")
workers = 2
timeout = 45
max_requests = 1000
max_requests_jitter = 100
accesslog = None  # Avoid OAuth codes or future capabilities in query-string logs.
errorlog = "-"
capture_output = True
