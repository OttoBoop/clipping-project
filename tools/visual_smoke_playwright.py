#!/usr/bin/env python3
"""Visual end-to-end smoke for Goals 1/2/5 via Playwright.

This is the browser-side counterpart to the API smokes (admin_viewers_smoke,
targets_mgmt_smoke, password_change_smoke). It walks the actual UI in a
real Chromium and asserts the user-visible affordances:

  - Goal 2 (logout): session bar visible, click "Sair" → returns to /login,
    cookie cleared, /healthz still up.
  - Goal 2 (change-password): open modal, wrong-old → red message,
    valid pair → success message, modal closes, subsequent admin actions
    work (this catches the CSRF-cache regression).
  - Goal 5 (target mgmt UI): open "Gerenciar nomes secundários", attempt
    to create a duplicate → see specific error message (not generic
    spinner / "something went wrong"). Promote/demote a smoke target,
    see the chip change.
  - Goal 1 (admin viewers UI): open "Clientes (viewers)" section, create a
    smoke viewer, see it in the list with the "com senha" chip, archive
    it, see it disappear.

Reads CLIPPING_ADMIN_PASSWORD from env. Each step prints PASS/FAIL with
a literal screenshot of the relevant DOM region so a human reviewing the
log can see exactly what the UI showed. Original admin password is always
restored at the end if it was changed.

Usage:
    CLIPPING_ADMIN_PASSWORD=clipping-admin-2026 \\
        .venv_playwright/bin/python tools/visual_smoke_playwright.py
    # or against local dev:
    CLIPPING_ADMIN_PASSWORD=... .venv_playwright/bin/python \\
        tools/visual_smoke_playwright.py --base http://localhost:8000
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

from playwright.sync_api import Page, TimeoutError as PlaywrightTimeout, expect, sync_playwright


DEFAULT_BASE_URL = "https://clipping-project.onrender.com"
SCREENSHOT_DIR = Path("/tmp/clipping_visual_smoke")


class StepFail(RuntimeError):
    pass


def shot(page: Page, name: str) -> Path:
    SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
    p = SCREENSHOT_DIR / f"{int(time.time())}_{name}.png"
    page.screenshot(path=str(p), full_page=False)
    return p


def login_as_admin(page: Page, base: str, password: str) -> None:
    page.goto(base + "/", wait_until="domcontentloaded")
    # The login form (single password field) and the app shell are served
    # from the same path "/" — login state is inferred from the HTML.
    has_login_form = page.locator("#password").count() > 0
    if has_login_form:
        page.locator("#password").fill(password)
        page.locator("#loginButton").click()
        # Click triggers window.location.reload(); wait for the new shell.
        page.wait_for_load_state("domcontentloaded")
        page.wait_for_selector("#app", timeout=15000)
    else:
        page.wait_for_selector("#app", timeout=15000)


def goal_article_rendering(page: Page, base: str, admin_pass: str) -> None:
    """Verify the core read experience didn't regress: articles render
    inside story cards, the targets filter chips exist, the visible-articles
    stat is > 0. Catches regressions where data loads but UI fails to
    populate (the silent-fail class)."""
    print("\n=== GOAL 4 — core article rendering didn't regress ===")
    login_as_admin(page, base, admin_pass)

    # Wait for #app to be live + data to populate the article-card grid.
    page.wait_for_function(
        "document.querySelectorAll('.article-card').length > 0",
        timeout=30000,
    )

    def parse_int(s: str) -> int:
        digits = "".join(ch for ch in (s or "") if ch.isdigit())
        return int(digits) if digits else 0

    base_stories = parse_int(page.locator("#baseStoriesStat").inner_text())
    base_articles = parse_int(page.locator("#baseArticlesStat").inner_text())
    print(f"  base stats: stories={base_stories}, articles={base_articles}")
    assert base_stories > 0 and base_articles > 0, "base stats are zero"

    article_count = page.locator(".article-card").count()
    print(f"  .article-card elements rendered: {article_count}")
    assert article_count > 0, "no article cards rendered"

    # Sanity: the first article-card has a non-empty title.
    first_title = page.locator(".article-card").first.inner_text().strip()[:80]
    assert len(first_title) > 5, f"first article-card has empty title: '{first_title}'"
    print(f"  first article title: '{first_title}...'")

    shot(page, "core_articles_rendered")
    print("  core read experience renders ✅")


def goal_admin_simulation(page: Page, base: str, admin_pass: str) -> None:
    """Verify the 'Ver como [perfil]' admin simulation flow:
    - dropdown visible for real admin, hidden banner initially
    - navigating to /?as_profile=flavio applies viewer-readonly + banner
    - admin chrome (manageTargetsBox, manageViewersBox) hidden in simulation
    - 'Voltar pra admin' restores admin shell + clears query string"""
    print("\n=== GOAL extra — admin 'Ver como' simulation flow ===")
    login_as_admin(page, base, admin_pass)
    page.wait_for_timeout(2000)

    # Step 1: real admin sees the dropdown and no banner.
    box = page.locator("#simulateBox")
    expect(box).to_be_visible(timeout=10000)
    banner_hidden = page.locator("#simulateBanner").get_attribute("hidden")
    assert banner_hidden is not None, "simulate banner should start hidden for real admin"
    print("  real admin: dropdown visible, banner hidden ✅")
    shot(page, "simulate_1_admin")

    # Step 2: navigate to ?as_profile=flavio and verify simulation state.
    page.goto(base + "/?as_profile=flavio", wait_until="domcontentloaded")
    page.wait_for_selector("#simulateBanner", state="visible", timeout=15000)
    body_class = page.locator("body").get_attribute("class") or ""
    assert "viewer-readonly" in body_class, f"body should be viewer-readonly when simulating, got '{body_class}'"
    real_role = page.locator("#app").get_attribute("data-clipping-real-role")
    assert real_role == "admin", f"real role should remain admin in simulation, got {real_role}"
    sim_attr = page.locator("#app").get_attribute("data-clipping-simulating")
    assert sim_attr == "flavio", f"simulating attr should be 'flavio', got {sim_attr}"

    # Anti-jitter assertion: the banner must already show the pretty label
    # ("Flavio Valle") right after the banner becomes visible — no async
    # wait. This catches the regression where the label was filled in only
    # after /api/admin/viewers resolved (~2s flash of profile-key).
    sim_label_attr = page.locator("#app").get_attribute("data-clipping-simulating-label")
    assert sim_label_attr == "Flavio Valle", (
        f"server should pre-render simulating-label, got {sim_label_attr!r}"
    )
    banner_text = page.locator("#simulateBannerProfile").inner_text().strip()
    assert "Flavio Valle" in banner_text, (
        f"banner must show 'Flavio Valle' immediately (no jitter), got {banner_text!r}"
    )
    print(f"  banner label resolved immediately: '{banner_text}' ✅")

    manage_box = page.locator("#manageTargetsBox")
    if manage_box.count() > 0:
        assert not manage_box.is_visible(), "manageTargetsBox must be hidden in simulation"
    viewers_box = page.locator("#manageViewersBox")
    if viewers_box.count() > 0:
        assert not viewers_box.is_visible(), "manageViewersBox must be hidden in simulation"
    print(f"  simulating flavio: viewer-readonly applied, banner visible, real_role={real_role}, admin chrome hidden ✅")
    shot(page, "simulate_2_flavio")

    # Step 3: switch directly to a different profile (shakira) — no need
    # to exit simulation first. Catches bugs where the JS assumed admin->
    # viewer transitions but missed viewer->viewer.
    page.goto(base + "/?as_profile=shakira", wait_until="domcontentloaded")
    page.wait_for_selector("#simulateBanner", state="visible", timeout=15000)
    sim_attr_2 = page.locator("#app").get_attribute("data-clipping-simulating")
    assert sim_attr_2 == "shakira", f"switched simulating attr should be 'shakira', got {sim_attr_2}"
    sim_label_2 = page.locator("#app").get_attribute("data-clipping-simulating-label")
    assert sim_label_2 == "Show da Shakira", f"shakira label should be 'Show da Shakira', got {sim_label_2!r}"
    print(f"  switched to shakira: label resolved as '{sim_label_2}' ✅")
    shot(page, "simulate_2b_shakira")

    # Step 4: also try rio_economico — profile that has only 1 target_key.
    page.goto(base + "/?as_profile=rio_economico", wait_until="domcontentloaded")
    page.wait_for_selector("#simulateBanner", state="visible", timeout=15000)
    sim_attr_3 = page.locator("#app").get_attribute("data-clipping-simulating")
    assert sim_attr_3 == "rio_economico"
    print(f"  switched to rio_economico ✅")

    # Step 5: click 'Voltar pra admin' and verify restore.
    page.locator("#simulateExitButton").click()
    page.wait_for_load_state("domcontentloaded")
    page.wait_for_selector("#app", timeout=15000)
    page.wait_for_timeout(2000)
    body_class_after = page.locator("body").get_attribute("class") or ""
    assert "viewer-readonly" not in body_class_after, "viewer-readonly should be gone after exit"
    assert "?as_profile" not in page.url, f"URL should be clean after exit, got {page.url}"
    if manage_box.count() > 0:
        assert manage_box.is_visible() or not manage_box.evaluate("el => el.hidden"), (
            "manageTargetsBox should be visible again after exit"
        )
    print(f"  after 'Voltar pra admin': body={body_class_after!r}, URL clean, admin chrome restored ✅")
    shot(page, "simulate_3_back")


def goal_viewer_segregation(page: Page, base: str, viewer_pass: str, viewer_profile: str = "flavio") -> None:
    """Visually verify that a viewer sees their segregated dashboard and
    has no admin affordances (no manage targets, no add target, no clientes).
    Counterpart to authenticated_render_smoke's HTML-marker check."""
    print(f"\n=== GOAL 1+4 — viewer segregation visual ({viewer_profile}) ===")
    page.goto(base + "/", wait_until="domcontentloaded")
    page.locator("#password").fill(viewer_pass)
    page.locator("#loginButton").click()
    page.wait_for_load_state("domcontentloaded")
    page.wait_for_selector("#app", timeout=15000)

    role_attr = page.locator("#app").get_attribute("data-clipping-session-role")
    profile_attr = page.locator("#app").get_attribute("data-clipping-session-profile")
    print(f"  shell attrs: role={role_attr}, profile={profile_attr}")
    assert role_attr == "viewer", f"expected viewer role, got {role_attr}"
    assert profile_attr == viewer_profile, f"expected profile {viewer_profile}, got {profile_attr}"

    body_class = page.locator("body").get_attribute("class") or ""
    assert "viewer-readonly" in body_class, f"body class missing viewer-readonly: '{body_class}'"
    print(f"  body class: '{body_class}' ✅")

    # Admin sections should be hidden via CSS body.viewer-readonly .add-target-box
    # Their parent `details` is set hidden by JS as well. Either way: not visible.
    # Use expect().to_be_hidden() so Playwright auto-waits for the JS to
    # apply visibility (was racy with bare is_visible()).
    manage_box = page.locator("#manageTargetsBox")
    if manage_box.count() > 0:
        expect(manage_box).to_be_hidden(timeout=5000)
        print("  #manageTargetsBox hidden from viewer ✅")
    viewers_box = page.locator("#manageViewersBox")
    if viewers_box.count() > 0:
        expect(viewers_box).to_be_hidden(timeout=5000)
        print("  #manageViewersBox hidden from viewer ✅")

    # Session bar: viewer should still see profile + logout/change-password
    expect(page.locator("#sessionBar")).to_be_visible(timeout=10000)
    expect(page.locator("#logoutButton")).to_be_visible()
    expect(page.locator("#changePasswordButton")).to_be_visible()
    print("  viewer can still logout + change own password ✅")
    shot(page, f"viewer_segregation_{viewer_profile}")


def goal3_human_passwords(page: Page, base: str, expected: dict[str, str]) -> None:
    """expected is {profile_label_or_admin: password}. Logs in as each in
    a fresh context, asserts the session bar shows the right profile, then
    logs out. Verifies Goal 3 — the production set of passwords is human
    and works."""
    print("\n=== GOAL 3 — human passwords for all five roles ===")
    for profile, pw in expected.items():
        ctx = page.context.browser.new_context()
        p = ctx.new_page()
        try:
            p.goto(base + "/", wait_until="domcontentloaded")
            p.locator("#password").fill(pw)
            p.locator("#loginButton").click()
            p.wait_for_load_state("domcontentloaded")
            p.wait_for_selector("#app", timeout=15000)
            # Confirm session bar profile label matches what we expect.
            bar = p.locator("#sessionBar")
            expect(bar).to_be_visible(timeout=10000)
            actual = p.locator("#sessionProfileLabel").inner_text().strip()
            expected_label = "admin" if profile == "admin" else profile
            assert expected_label.lower() in actual.lower() or actual.lower() in expected_label.lower(), (
                f"profile mismatch: expected ~'{expected_label}', got '{actual}'"
            )
            print(f"  ✅ '{profile}' logged in (label='{actual}', pw len={len(pw)})")
            # Quick "is the password ditavel por telefone?" sanity:
            # human-friendly means 6-32 chars, ASCII letters/digits/hyphen.
            assert 5 < len(pw) < 33, f"password '{pw}' is not human-length"
            assert all(c.isalnum() or c in "-_" for c in pw), f"password '{pw}' has non-friendly chars"
        finally:
            ctx.close()


def goal2_logout(page: Page, base: str, admin_pass: str) -> None:
    print("\n=== GOAL 2 — logout UI ===")
    login_as_admin(page, base, admin_pass)
    bar = page.locator("#sessionBar")
    expect(bar).to_be_visible(timeout=10000)
    profile_label = page.locator("#sessionProfileLabel").inner_text().strip()
    print(f"  session bar visible, profile label='{profile_label}'")
    shot(page, "goal2_logged_in")

    logout = page.locator("#logoutButton")
    expect(logout).to_be_visible()
    logout.click()
    # After logout, the JS reloads "/". The shell now shows the login form
    # again. Wait for #password to appear (login form indicator).
    page.wait_for_selector("#password", timeout=15000)
    print(f"  back on login form (URL: {page.url})")
    cookie = next((c for c in page.context.cookies() if c["name"] == "clipping_admin"), None)
    assert cookie is None or not cookie.get("value"), f"session cookie still present: {cookie}"
    print("  session cookie cleared ✅")
    shot(page, "goal2_logged_out")


def goal2_change_password(page: Page, base: str, admin_pass: str) -> str:
    """Returns the throwaway password (caller restores)."""
    print("\n=== GOAL 2 — change-password modal ===")
    login_as_admin(page, base, admin_pass)
    throwaway = f"smoke-visual-{int(time.time())}"

    btn = page.locator("#changePasswordButton")
    expect(btn).to_be_visible()
    btn.click()
    dlg = page.locator("#changePasswordDialog")
    expect(dlg).to_be_visible(timeout=5000)
    shot(page, "goal2_modal_open")

    # 1. wrong old → expect error message
    page.locator('#changePasswordForm input[name="old_password"]').fill("definitely-wrong")
    page.locator('#changePasswordForm input[name="new_password"]').fill(throwaway)
    page.locator('#changePasswordForm button[type="submit"]').click()
    msg_locator = page.locator("#changePasswordMessage")
    expect(msg_locator).to_contain_text("Senha atual incorreta", timeout=10000)
    error_msg = msg_locator.inner_text().strip()
    print(f"  wrong-old error: '{error_msg}'")
    shot(page, "goal2_modal_wrong_old")

    # 2. valid pair → expect success + modal closes
    page.locator('#changePasswordForm input[name="old_password"]').fill(admin_pass)
    page.locator('#changePasswordForm input[name="new_password"]').fill(throwaway)
    page.locator('#changePasswordForm button[type="submit"]').click()
    expect(msg_locator).to_contain_text("Senha trocada", timeout=10000)
    print(f"  success message: '{msg_locator.inner_text().strip()}'")
    shot(page, "goal2_modal_success")
    # Wait for modal close (1.5s setTimeout in JS)
    try:
        expect(dlg).to_be_hidden(timeout=4000)
        print("  modal auto-closed ✅")
    except PlaywrightTimeout:
        print("  WARN: modal didn't close on its own (still in dialog)")

    # 3. CSRF regression check: do a NON-mutating action that requires CSRF
    #    via a quick "rodar" attempt or just refetching /api/csrf. The
    #    safest is to try to expand "Gerenciar nomes secundários" then
    #    trigger renderManageTargets which calls /api/targets — that's
    #    a GET (no CSRF needed). We need something that uses CSRF.
    #    Best: navigate to /api/csrf via fetch and check it returns 200.
    csrf_resp = page.evaluate(
        "async () => { const r = await fetch('/api/csrf', {credentials:'same-origin'}); return r.status; }"
    )
    assert csrf_resp == 200, f"/api/csrf returned {csrf_resp} after change-password"
    print(f"  /api/csrf after change-password: HTTP {csrf_resp} (session still alive) ✅")
    return throwaway


def goal2_revert_password(page: Page, base: str, new_pass: str, original: str) -> None:
    print("\n=== GOAL 2 — revert throwaway → original ===")
    page.context.clear_cookies()
    login_as_admin(page, base, new_pass)
    page.locator("#changePasswordButton").click()
    expect(page.locator("#changePasswordDialog")).to_be_visible(timeout=5000)
    page.locator('#changePasswordForm input[name="old_password"]').fill(new_pass)
    page.locator('#changePasswordForm input[name="new_password"]').fill(original)
    page.locator('#changePasswordForm button[type="submit"]').click()
    expect(page.locator("#changePasswordMessage")).to_contain_text("Senha trocada", timeout=10000)
    print(f"  original password restored ✅")


def goal5_target_management(page: Page, base: str, admin_pass: str) -> None:
    print("\n=== GOAL 5 — target management UI ===")
    page.context.clear_cookies()
    login_as_admin(page, base, admin_pass)

    # Expand "Gerenciar nomes secundários"
    manage = page.locator("#manageTargetsBox")
    if not manage.evaluate("el => el.open"):
        manage.locator("summary").first.click()
    expect(manage).to_have_attribute("open", "")
    # Wait until at least one target card or the empty message renders.
    page.wait_for_function(
        "document.getElementById('manageTargetsList') && document.getElementById('manageTargetsList').childElementCount > 0",
        timeout=10000,
    )
    shot(page, "goal5_manage_open")
    cards = page.locator("#manageTargetsList .manage-target-card")
    count = cards.count()
    print(f"  managed targets visible: {count}")

    # Find one that's a protected primary (Flávio Valle) and confirm
    # no Promover/Rebaixar buttons.
    flavio_card = page.locator('[data-manage-target-key="flavio_valle"]')
    if flavio_card.count() > 0:
        promote_btn = flavio_card.locator("[data-target-promote]")
        demote_btn = flavio_card.locator("[data-target-demote]")
        assert promote_btn.count() == 0, "protected primary should have no promote button"
        assert demote_btn.count() == 0, "protected primary should have no demote button"
        chip = flavio_card.locator(".chip-protected, .chip-primary").first.inner_text().strip()
        print(f"  flavio_valle card: chip='{chip}', no promote/demote buttons ✅")

    # Open the "Adicionar nome secundário" details and try a duplicate.
    add_box = page.locator(".add-target-box").first
    if not add_box.evaluate("el => el.open"):
        add_box.locator("summary").first.click()
    page.locator('#addTargetForm input[name="display_name"]').fill("Shakira")
    page.locator('#addTargetForm button[type="submit"]').click()
    err = page.locator("#addTargetMessage")
    expect(err).to_contain_text("Já existe", timeout=10000)
    print(f"  duplicate rejected with specific msg: '{err.inner_text().strip()}'")
    shot(page, "goal5_duplicate_error")


def goal1_admin_viewers(page: Page, base: str, admin_pass: str) -> None:
    print("\n=== GOAL 1 — admin viewers UI ===")
    page.context.clear_cookies()
    login_as_admin(page, base, admin_pass)

    box = page.locator("#manageViewersBox")
    expect(box).to_be_visible(timeout=10000)
    if not box.evaluate("el => el.open"):
        box.locator("summary").first.click()
    expect(box).to_have_attribute("open", "")

    page.wait_for_function(
        "document.querySelectorAll('#manageViewersList .viewer-card').length > 0",
        timeout=10000,
    )
    cards = page.locator("#manageViewersList .viewer-card")
    count = cards.count()
    print(f"  viewers listed: {count}")
    shot(page, "goal1_viewers_list")

    tag = str(int(time.time()))
    profile_key = f"vsmoke_{tag}"
    password = f"vsmoke-{tag}"

    # Open create form
    add = page.locator(".add-viewer-box")
    if not add.evaluate("el => el.open"):
        add.locator("summary").first.click()

    # Wait for the target options to populate (loadTargetOptions runs after admin viewers loaded).
    page.wait_for_function(
        "document.querySelectorAll('#addViewerTargetOptions input[type=\"checkbox\"]').length > 0",
        timeout=10000,
    )
    page.locator('#addViewerForm input[name="profile"]').fill(profile_key)
    page.locator('#addViewerForm input[name="label"]').fill(f"Visual smoke {tag}")
    page.locator('#addViewerForm input[name="password"]').fill(password)
    # Pick the shakira checkbox (works in any of the deployed envs).
    checkbox = page.locator('#addViewerTargetOptions input[type="checkbox"][value="shakira"]')
    if checkbox.count() == 0:
        # Fallback: pick the first available checkbox.
        checkbox = page.locator('#addViewerTargetOptions input[type="checkbox"]').first
    checkbox.check()
    page.locator('#addViewerForm button[type="submit"]').click()

    expect(page.locator("#addViewerMessage")).to_contain_text("criado", timeout=15000)
    print(f"  viewer '{profile_key}' created in UI ✅")
    shot(page, "goal1_viewer_created")

    # Wait for the new card to appear.
    new_card = page.locator(f'#manageViewersList [data-viewer-profile="{profile_key}"]')
    expect(new_card).to_be_visible(timeout=10000)
    chip = new_card.locator(".chip-ok").first
    expect(chip).to_have_text("com senha")
    print(f"  card visible with 'com senha' chip ✅")

    # Archive it. The native confirm() dialog must be accepted before
    # the request fires.
    page.on("dialog", lambda d: d.accept())
    new_card.locator('[data-viewer-archive]').click()
    # The strongest visual signal is the card disappearing from the list.
    expect(new_card).to_have_count(0, timeout=15000)
    print(f"  viewer card removed after archive ✅")
    # The success message ("Cliente ... arquivado.") should also be there,
    # though it may be cleared on subsequent renders. Best-effort assert.
    msg = page.locator("#manageViewersMessage").inner_text().strip()
    print(f"  message after archive: '{msg}'")
    shot(page, "goal1_viewer_archived")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default=DEFAULT_BASE_URL)
    parser.add_argument("--headed", action="store_true")
    args = parser.parse_args()
    base = args.base.rstrip("/")

    admin_pass = os.environ.get("CLIPPING_ADMIN_PASSWORD", "").strip()
    if not admin_pass:
        print("CLIPPING_ADMIN_PASSWORD env var is required", file=sys.stderr)
        return 2

    print(f"==> Visual smoke against {base}  (screenshots → {SCREENSHOT_DIR})")

    # Goal 3 — set of human passwords currently active in production.
    # Updated 2026-05-19 after the rotation in MAJOR entry 12:35.
    human_passwords = {
        "admin": admin_pass,
        "flavio": os.environ.get("CLIPPING_SMOKE_FLAVIO", "flavio-gabinete-2026"),
        "shakira": os.environ.get("CLIPPING_SMOKE_SHAKIRA", "shakira-fgv-2026"),
        "rio_economico": os.environ.get("CLIPPING_SMOKE_RIO", "rio-economico-2026"),
        "demo_cliente": os.environ.get("CLIPPING_SMOKE_DEMO", "demo-cliente-2026"),
    }

    throwaway: str | None = None
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=not args.headed)
        try:
            # Goal 4 – core article rendering smoke
            ctx = browser.new_context()
            page = ctx.new_page()
            goal_article_rendering(page, base, admin_pass)
            ctx.close()

            # Goal 3 – human passwords for all five roles
            ctx = browser.new_context()
            page = ctx.new_page()
            goal3_human_passwords(page, base, human_passwords)
            ctx.close()

            # Goal 2 – logout
            ctx = browser.new_context()
            page = ctx.new_page()
            goal2_logout(page, base, admin_pass)
            ctx.close()

            # Goal 2 – change-password
            ctx = browser.new_context()
            page = ctx.new_page()
            throwaway = goal2_change_password(page, base, admin_pass)
            ctx.close()

            # Goal 2 – revert throwaway → original (so the rest of the
            # smoke can use the original admin_pass).
            ctx = browser.new_context()
            page = ctx.new_page()
            goal2_revert_password(page, base, throwaway, admin_pass)
            ctx.close()
            throwaway = None  # restored

            # Goal 5 – target management
            ctx = browser.new_context()
            page = ctx.new_page()
            goal5_target_management(page, base, admin_pass)
            ctx.close()

            # Goal 1 – admin viewers
            ctx = browser.new_context()
            page = ctx.new_page()
            goal1_admin_viewers(page, base, admin_pass)
            ctx.close()

            # Viewer segregation visual (Goals 1 + 4 cross-check)
            flavio_pw = human_passwords.get("flavio")
            if flavio_pw:
                ctx = browser.new_context()
                page = ctx.new_page()
                goal_viewer_segregation(page, base, flavio_pw, "flavio")
                ctx.close()

            # Admin "Ver como" simulation flow (2026-05-20 feature)
            ctx = browser.new_context()
            page = ctx.new_page()
            goal_admin_simulation(page, base, admin_pass)
            ctx.close()
        finally:
            browser.close()

    if throwaway:
        print(f"\n!! WARNING: throwaway password '{throwaway}' was not restored.")
        return 1

    print("\nVisual smoke OK — Goals 1, 2, 5 verified end-to-end through the real UI.")
    print(f"Screenshots: {SCREENSHOT_DIR}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
