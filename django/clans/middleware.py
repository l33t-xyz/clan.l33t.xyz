from django.conf import settings
from django.http import HttpResponseNotFound


class ResponsePolicy:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            length = int(request.META.get("CONTENT_LENGTH") or 0)
        except ValueError:
            length = 0
        if length > 3 * 1024 * 1024:
            from django.http import HttpResponse

            return HttpResponse(
                "Upload is too large. Maximum request size is 3 MB.", status=413
            )
        host = request.get_host().split(":")[0]
        base = settings.CLAN_BASE_DOMAIN
        response = None
        if base and host.endswith("." + base):
            handle = host[: -(len(base) + 1)]
            path = request.path
            if path == "/":
                from .views import public_site

                response = public_site(request, handle)
            elif path.startswith("/static/") or path.startswith("/s/" + handle + "/"):
                pass
            else:
                response = HttpResponseNotFound("Not found")
        if response is None:
            response = self.get_response(request)
        response["Content-Security-Policy"] = (
            "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; font-src 'self'; object-src 'none'; base-uri 'self'; frame-ancestors 'none'; form-action 'self' https://discord.com"
        )
        response["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        if request.path.startswith(("/studio/", "/api/", "/accounts/", "/login/")):
            response["Cache-Control"] = "private, no-store"
        if settings.MODE != "production":
            response["X-Robots-Tag"] = "noindex, nofollow"
        return response
