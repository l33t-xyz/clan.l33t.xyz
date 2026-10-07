from django.conf import settings

from .models import Membership


def site_context(request):
    site = (
        getattr(request, "resolver_match", None).kwargs.get("handle")
        if getattr(request, "resolver_match", None)
        else None
    )
    owner = bool(
        site
        and request.user.is_authenticated
        and Membership.objects.filter(
            site__slug=site, user=request.user, role="owner"
        ).exists()
    )
    return {
        "discord_ready": settings.DISCORD_READY,
        "preview_mode": settings.MODE != "production",
        "central_origin": settings.PUBLIC_ORIGIN,
        "site_owner": owner,
    }
