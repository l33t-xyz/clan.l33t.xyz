import secrets

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model, login, logout
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST

from . import services
from .forms import PageForm, SiteForm
from .models import Asset, Membership, Page, Revision, Site


def scoped(request, handle, owner=False):
    site = get_object_or_404(Site, slug=handle)
    # Return same 404 for nonexistent and unauthorized sites.
    if not request.user.is_authenticated or not request.user.is_active:
        raise Http404
    q = site.memberships.filter(user=request.user)
    if owner:
        q = q.filter(role="owner")
    if not q.exists():
        raise Http404
    return site


def landing(request):
    # Only explicitly published sample, not a tenant directory.
    return render(
        request, "clans/landing.html", {"demo_available": settings.MODE == "local"}
    )


def signin(request):
    return render(request, "clans/login.html")


@require_POST
def signout(request):
    logout(request)
    return redirect("landing")


@login_required
def studio(request):
    memberships = Membership.objects.filter(user=request.user).select_related("site")
    return render(request, "clans/studio.html", {"memberships": memberships})


@login_required
def new_site(request):
    form = SiteForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            s = services.create_site(
                request.user,
                form.cleaned_data["name"],
                form.cleaned_data["slug"],
                form.cleaned_data["game"],
            )
            return redirect("dashboard", handle=s.slug)
        except ValidationError as e:
            form.add_error(None, e)
        except IntegrityError:
            form.add_error("slug", "That address is taken. Try another.")
    return render(request, "clans/new.html", {"form": form})


@login_required
def dashboard(request, handle):
    s = scoped(request, handle)
    used = services.usage(s)
    return render(
        request,
        "clans/dashboard.html",
        {
            "site": s,
            "pages": s.pages.all(),
            "used_mb": round(used / 1024 / 1024, 2),
            "limit_mb": round(s.storage_limit / 1024 / 1024),
            "used_percent": min(100, round(used / max(1, s.storage_limit) * 100)),
            "events": s.events.select_related("actor")[:8],
            "is_owner": s.memberships.filter(user=request.user, role="owner").exists(),
        },
    )


@login_required
def edit(request, handle, page_id=None):
    s = scoped(request, handle)
    p = get_object_or_404(Page, site=s, pk=page_id) if page_id else None
    form = PageForm(
        request.POST or None,
        initial={
            "title": p.title if p else "",
            "html": p.draft_html if p else "",
            "version": p.version if p else 0,
        },
    )
    status = 200
    if request.method == "POST" and form.is_valid():
        try:
            p = services.save_page(
                s,
                request.user,
                page_id,
                form.cleaned_data["title"],
                form.cleaned_data["html"],
                form.cleaned_data["version"],
            )
            messages.success(request, "Draft saved. Your live website hasn't changed.")
            return redirect("edit", handle=handle, page_id=p.pk)
        except services.Conflict as e:
            form.add_error(None, e)
            status = 409
        except ValidationError as e:
            form.add_error(None, e)
            status = 400
    return render(
        request,
        "clans/edit.html",
        {
            "site": s,
            "page": p,
            "form": form,
            "assets": s.assets.defer("contents"),
            "history": p.revisions.select_related("actor")[:10] if p else [],
        },
        status=status,
    )


@login_required
@require_POST
def publish(request, handle, page_id):
    s = scoped(request, handle)
    get_object_or_404(Page, site=s, pk=page_id)
    try:
        services.publish(
            s,
            request.user,
            page_id,
            request.POST.get("version"),
            request.POST.get("action") == "unpublish",
        )
    except services.Conflict as e:
        return HttpResponse(e.messages[0], status=409)
    except ValidationError as e:
        return HttpResponse(e.messages[0], status=400)
    messages.success(
        request,
        "Website updated."
        if request.POST.get("action") != "unpublish"
        else "Page taken offline. Your draft is safe.",
    )
    return redirect("edit", handle=handle, page_id=page_id)


@login_required
@require_POST
def restore(request, handle, page_id, revision_id):
    s = scoped(request, handle)
    p = get_object_or_404(Page, site=s, pk=page_id)
    r = get_object_or_404(Revision, page=p, pk=revision_id)
    try:
        services.save_page(
            s,
            request.user,
            p.pk,
            r.title,
            r.html,
            request.POST.get("version"),
            source="restore",
        )
    except services.Conflict as e:
        return HttpResponse(e.messages[0], status=409)
    except ValidationError as e:
        return HttpResponse(e.messages[0], status=400)
    messages.success(
        request, "Earlier version restored as a draft. Review it before publishing."
    )
    return redirect("edit", handle=handle, page_id=p.pk)


@login_required
@require_POST
def upload(request, handle):
    s = scoped(request, handle)
    if "image" not in request.FILES:
        return JsonResponse({"error": "Choose an image."}, status=400)
    try:
        a = services.upload(s, request.user, request.FILES["image"])
    except ValidationError as e:
        return JsonResponse({"error": e.messages[0]}, status=400)
    return JsonResponse({"url": a.get_absolute_url(), "id": str(a.pk), "name": a.name})


@login_required
def library(request, handle):
    s = scoped(request, handle)
    return render(
        request, "clans/library.html", {"site": s, "assets": s.assets.defer("contents")}
    )


@login_required
def configure(request, handle):
    s = scoped(request, handle, owner=True)
    error = None
    if request.method == "POST":
        try:
            s = services.configure(s, request.user, request.POST)
            messages.success(request, "Website settings saved.")
            return redirect("configure", handle=handle)
        except (ValidationError, ValueError, Asset.DoesNotExist) as e:
            error = (
                e.messages[0]
                if isinstance(e, ValidationError)
                else "Choose an image from this website."
            )
    return render(
        request,
        "clans/configure.html",
        {"site": s, "assets": s.assets.defer("contents"), "error": error},
    )


@login_required
def team(request, handle):
    s = scoped(request, handle, owner=True)
    error = None
    if request.method == "POST":
        from allauth.socialaccount.models import SocialAccount

        with transaction.atomic():
            Site.objects.select_for_update().get(pk=s.pk)
            services.membership(s, request.user, owner=True)
            if request.POST.get("remove"):
                if not request.POST["remove"].isdigit():
                    return HttpResponse("Invalid membership.", status=400)
                m = get_object_or_404(
                    Membership, site=s, pk=request.POST["remove"], role="editor"
                )
                m.delete()
                messages.success(
                    request, "Editor removed. Their builder access is no longer valid."
                )
            else:
                a = (
                    SocialAccount.objects.filter(
                        provider="discord", uid=request.POST.get("discord_id", "")
                    )
                    .select_related("user")
                    .first()
                )
                if not a:
                    error = "Ask your teammate to sign in with Discord first, then enter their Discord user ID."
                elif a.user_id == request.user.pk:
                    error = "You're already the owner."
                elif s.memberships.count() >= 20:
                    error = "This website supports up to 20 editors."
                else:
                    Membership.objects.get_or_create(
                        site=s, user=a.user, defaults={"role": "editor"}
                    )
                    messages.success(request, "Editor added.")
    return render(
        request,
        "clans/team.html",
        {"site": s, "members": s.memberships.select_related("user"), "error": error},
    )


@login_required
def builder(request, handle):
    s = scoped(request, handle)
    if request.method == "POST":
        services.membership(s, request.user, owner=True)
        import uuid

        try:
            grant_id = uuid.UUID(request.POST.get("revoke", ""))
        except (ValueError, TypeError, AttributeError):
            return HttpResponse("Invalid connection.", status=400)
        grant = get_object_or_404(s.builder_grants, pk=grant_id)
        grant.revoked_at = timezone.now()
        grant.save(update_fields=["revoked_at"])
        messages.success(request, "Builder access revoked.")
        return redirect("builder", handle=handle)
    return render(
        request,
        "clans/builder.html",
        {
            "site": s,
            "grants": s.builder_grants.all(),
            "bindings": s.discordbinding_set.all(),
            "is_owner": s.memberships.filter(user=request.user, role="owner").exists(),
        },
    )


def public_site(request, handle, page_slug=None, preview=False):
    s = get_object_or_404(Site.objects.select_related("hero"), slug=handle)
    # A tenant subdomain may never route another tenant via a path.
    host = request.get_host().split(":")[0]
    if settings.CLAN_BASE_DOMAIN and host.endswith("." + settings.CLAN_BASE_DOMAIN):
        if host[: -(len(settings.CLAN_BASE_DOMAIN) + 1)] != handle:
            raise Http404
    if preview:
        scoped(request, handle)
        pages = s.pages.all()
    else:
        pages = s.pages.filter(published_at__isnull=False)
    p = get_object_or_404(pages, slug=page_slug) if page_slug else pages.first()
    if not p:
        raise Http404
    return render(
        request,
        "clans/public.html",
        {
            "site": s,
            "page": p,
            "pages": pages,
            "draft_preview": preview,
            "content": p.draft_html if preview else p.published_html,
            "title": p.title if preview else p.published_title,
        },
    )


@login_required
def preview(request, handle, page_slug):
    return public_site(request, handle, page_slug, True)


def asset(request, handle, asset_id):
    a = get_object_or_404(
        Asset.objects.select_related("site"), site__slug=handle, pk=asset_id
    )
    permitted = (
        request.user.is_authenticated
        and request.user.is_active
        and a.site.memberships.filter(user=request.user).exists()
    )
    public = a.site.hero_id == a.pk or any(
        a.get_absolute_url() in services.image_sources(p.published_html)
        for p in a.site.pages.filter(published_at__isnull=False).only("published_html")
    )
    if not (permitted or public):
        raise Http404
    response = HttpResponse(bytes(a.contents), content_type=a.content_type)
    response["ETag"] = '"' + a.sha256 + '"'
    response["Cache-Control"] = "private, no-cache"
    response["X-Content-Type-Options"] = "nosniff"
    return response


@require_GET
def health(request):
    from django.db import connection

    with connection.cursor() as cursor:
        cursor.execute("SELECT 1")
    return JsonResponse({"status": "ok"})


@require_POST
def demo(request):
    if settings.MODE != "local":
        raise Http404
    if request.user.is_authenticated:
        return redirect("studio")
    User = get_user_model()
    if User.objects.filter(username__startswith="demo_").count() >= 30:
        return HttpResponse(
            "Preview is full. Please try again after the next reset.", status=429
        )
    suffix = secrets.token_hex(4)
    with transaction.atomic():
        u = User.objects.create_user(
            username="demo_" + suffix, first_name="Preview captain"
        )
        s = services.create_site(
            u, "The Night Owls", "night-owls-" + suffix, "Adventures after dark"
        )
        s.tagline = "Different time zones. One squad."
        s.theme = "amethyst"
        s.save()
        p = s.pages.first()
        services.publish(s, u, p.pk, p.version)
    login(request, u, backend="django.contrib.auth.backends.ModelBackend")
    return redirect("dashboard", handle=s.slug)
