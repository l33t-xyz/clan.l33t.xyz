"""Synthetic, local-mode acceptance; never run this against production."""

import argparse
import json
from io import BytesIO
from pathlib import Path

from PIL import Image
from playwright.sync_api import sync_playwright

parser = argparse.ArgumentParser()
parser.add_argument("--base-url", default="http://127.0.0.1:18461")
parser.add_argument("--output", default="/tmp/clan-browser-acceptance")
args = parser.parse_args()
base = args.base_url.rstrip("/")
out = Path(args.output)
out.mkdir(parents=True, exist_ok=True)
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(viewport={"width": 1440, "height": 1050})
    page = context.new_page()
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    assert page.goto(base).status == 200
    page.screenshot(path=str(out / "landing-desktop.png"), full_page=True)
    page.get_by_role("button", name="Try the editor").click()
    page.wait_for_url("**/studio/night-owls-*/")
    handle = page.url.split("/studio/")[1].split("/")[0]
    page.screenshot(path=str(out / "studio-desktop.png"), full_page=True)
    page.get_by_role("link", name="Edit page").first.click()
    page.locator(".ql-editor").wait_for()
    edit_url = page.url
    page.locator("#id_title").fill("Our next adventure")
    page.locator(".ql-editor").fill("Bring a friend. Our next adventure starts Friday.")
    assert page.get_by_role("button", name="Publish saved draft").is_disabled()
    img = BytesIO()
    Image.new("RGB", (240, 120), (65, 105, 70)).save(img, "PNG")
    page.locator("#image-upload").set_input_files(
        {"name": "camp.png", "mimeType": "image/png", "buffer": img.getvalue()}
    )
    page.get_by_text("Image added. Save your draft", exact=False).wait_for()
    page.get_by_role("button", name="Save draft", exact=True).click()
    page.wait_for_load_state()
    page.get_by_text("Draft saved.", exact=False).wait_for()
    public = context.new_page()
    public.goto(base + "/s/" + handle + "/")
    assert (
        public.get_by_text("Our next adventure starts Friday.", exact=False).count()
        == 0
    )
    page.get_by_role("button", name="Publish saved draft").click()
    page.wait_for_load_state()
    public.reload()
    assert public.get_by_text(
        "Our next adventure starts Friday.", exact=False
    ).is_visible()
    assert public.locator(".prose img").evaluate(
        "(img)=>img.complete && img.naturalWidth>0"
    )
    public.screenshot(path=str(out / "public-desktop.png"), full_page=True)
    page.screenshot(path=str(out / "editor-desktop.png"), full_page=True)
    # Changing a theme/cover must preserve page content and load its MySQL image.
    page.goto(base + "/studio/" + handle + "/settings/")
    page.locator("[name=theme][value=amethyst]").check()
    page.locator("[name=hero]").select_option(index=1)
    page.get_by_role("button", name="Save website settings").click()
    public.reload()
    assert public.locator(".public-site").evaluate(
        '(e)=>e.classList.contains("theme-amethyst")'
    )
    assert public.locator(".cover-image").evaluate(
        "(img)=>img.complete && img.naturalWidth>0"
    )
    # Restore version one as a draft; public snapshot remains unchanged.
    page.goto(edit_url)
    page.get_by_text("Earlier versions", exact=False).click()
    page.get_by_role("button", name="Restore draft").last.click()
    page.wait_for_load_state()
    public.reload()
    assert public.get_by_text(
        "Our next adventure starts Friday.", exact=False
    ).is_visible()
    paths = [
        ("/", "landing"),
        ("/studio/" + handle + "/", "studio"),
        ("/studio/" + handle + "/images/", "library"),
        ("/studio/" + handle + "/settings/", "settings"),
        ("/studio/" + handle + "/team/", "team"),
        ("/studio/" + handle + "/builder/", "builder"),
        (edit_url.removeprefix(base), "editor"),
        ("/s/" + handle + "/", "public"),
    ]
    for width in [1440, 390]:
        page.set_viewport_size({"width": width, "height": 900})
        for path, label in paths:
            response = page.goto(base + path)
            assert response.status == 200, (path, response.status)
            assert page.evaluate(
                "document.documentElement.scrollWidth <= innerWidth"
            ), (label, width, "overflow")
            if label == "editor":
                page.locator(".ql-editor").wait_for()
            page.screenshot(path=str(out / f"{label}-{width}.png"), full_page=True)
    assert errors == [], errors
    # A fresh session must not see the sample tenant's studio or private preview.
    anonymous = browser.new_context()
    anon = anonymous.new_page()
    r = anon.goto(edit_url)
    assert "/login/" in anon.url
    print(
        json.dumps(
            {
                "result": "pass",
                "responsive_pages": len(paths) * 2,
                "journey": "image upload, draft, publish, cover/theme, restore, anonymous isolation",
                "browser_errors": errors,
            }
        )
    )
    browser.close()
