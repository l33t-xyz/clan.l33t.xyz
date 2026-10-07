# Non-secret shape only. Populate through the host's protected credential flow.
# Never commit a populated copy or put it in chat. Mode 0640; checkout owner:service group.
CLAN_MODE = "preview"
DJANGO_SECRET_KEY = ""
MYSQL_DATABASE = "clan_builder_preview"
MYSQL_USER = "clan_builder_preview"
MYSQL_PASSWORD = ""
MYSQL_HOST = "127.0.0.1"
MYSQL_PORT = "3306"
ALLOWED_HOSTS = "clan-preview.example.test"
PUBLIC_ORIGIN = "https://clan-preview.example.test"
CSRF_TRUSTED_ORIGINS = PUBLIC_ORIGIN
CLAN_BASE_DOMAIN = ""
TRUST_PROXY_HTTPS = "1"
LEGACY_RESERVED_SLUGS = "existing-clan"
DISCORD_CLIENT_ID = ""
DISCORD_CLIENT_SECRET = ""
DISCORD_PUBLIC_KEY = ""
