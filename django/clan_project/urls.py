from clans import bot, views
from django.urls import include, path

urlpatterns = [
    path("", views.landing, name="landing"),
    path("login/", views.signin, name="login"),
    path("logout/", views.signout, name="logout"),
    path("accounts/", include("allauth.urls")),
    path("health/", views.health, name="health"),
    path("demo/", views.demo, name="demo"),
    path("studio/", views.studio, name="studio"),
    path("studio/new/", views.new_site, name="new_site"),
    path("studio/<slug:handle>/", views.dashboard, name="dashboard"),
    path("studio/<slug:handle>/pages/new/", views.edit, name="new_page"),
    path("studio/<slug:handle>/pages/<uuid:page_id>/", views.edit, name="edit"),
    path(
        "studio/<slug:handle>/pages/<uuid:page_id>/publish/",
        views.publish,
        name="publish",
    ),
    path(
        "studio/<slug:handle>/pages/<uuid:page_id>/restore/<int:revision_id>/",
        views.restore,
        name="restore",
    ),
    path("studio/<slug:handle>/upload/", views.upload, name="upload"),
    path("studio/<slug:handle>/images/", views.library, name="library"),
    path("studio/<slug:handle>/settings/", views.configure, name="configure"),
    path("studio/<slug:handle>/team/", views.team, name="team"),
    path("studio/<slug:handle>/builder/", views.builder, name="builder"),
    path(
        "studio/<slug:handle>/preview/<slug:page_slug>/", views.preview, name="preview"
    ),
    path("s/<slug:handle>/", views.public_site, name="site"),
    path("s/<slug:handle>/media/<uuid:asset_id>/", views.asset, name="asset"),
    path("s/<slug:handle>/<slug:page_slug>/", views.public_site, name="public_page"),
    path("api/builder/", bot.builder_api, name="builder_api"),
    path(
        "discord/interactions/", bot.discord_interactions, name="discord_interactions"
    ),
]
