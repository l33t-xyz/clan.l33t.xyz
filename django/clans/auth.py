from allauth.core.exceptions import ImmediateHttpResponse
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.http import HttpResponseForbidden


class DiscordAdapter(DefaultSocialAccountAdapter):
    def pre_social_login(self, request, sociallogin):
        if sociallogin.account.provider != "discord":
            raise ImmediateHttpResponse(
                HttpResponseForbidden("Discord sign-in required.")
            )

    def populate_user(self, request, sociallogin, data):
        user = super().populate_user(request, sociallogin, data)
        # Identity is Discord's immutable subject, never display name/email.
        user.username = "discord_" + sociallogin.account.uid
        user.first_name = str(
            sociallogin.account.extra_data.get("global_name")
            or data.get("username", "")
        )[:150]
        return user
