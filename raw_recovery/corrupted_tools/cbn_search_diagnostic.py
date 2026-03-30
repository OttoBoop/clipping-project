C:\Users\Admin\.vscode\general_scraper\general_scraper\browser_engine.py:12:from playwright.sync_api import sync_playwright
C:\Users\Admin\.vscode\general_scraper\general_scraper\browser_engine.py:55:        self.playwright = None
C:\Users\Admin\.vscode\general_scraper\general_scraper\browser_engine.py:78:        self._pw_context = sync_playwright()
C:\Users\Admin\.vscode\general_scraper\general_scraper\browser_engine.py:80:        self.playwright = pw
C:\Users\Admin\.vscode\general_scraper\profiles\gabineteonline.yaml:18:#   Camoufox manages its own Playwright — don't call sync_playwright().start() first.
C:\Users\Admin\.vscode\general_scraper\profiles\flaviovalle.yaml:58:# stealth_sync (playwright-stealth / Tarnished) makes Wix reCAPTCHA Enterprise invisible.
C:\Users\Admin\.vscode\general_scraper\profiles\flaviovalle.yaml:161:# See playwright_backend.py and PLAN_Wix_Editor_Loading_Fix.md for implementation details.
C:\Users\Admin\.vscode\general_scraper\requirements.txt:2:playwright>=1.40.0
C:\Users\Admin\.vscode\general_scraper\requirements.txt:10:# undetected-playwright
C:\Users\Admin\.vscode\general_scraper\playwright_backend.py:22:from playwright.sync_api import sync_playwright
C:\Users\Admin\.vscode\general_scraper\playwright_backend.py:28:    from undetected_playwright import Tarnished
C:\Users\Admin\.vscode\general_scraper\playwright_backend.py:34:# playwright-stealth — masks bot detection signals (navigator.webdriver, etc.)
C:\Users\Admin\.vscode\general_scraper\playwright_backend.py:39:    from playwright_stealth import Stealth as _StealthClass
C:\Users\Admin\.vscode\ge�neral_scraper\playwright_backend.py:45:        from playwright_stealth import stealth_sync
C:\Users\Admin\.vscode\general_scraper\playwright_backend.py:65:        self.playwright = None
C:\Users\Admin\.vscode\general_scraper\playwright_backend.py:94:                self.playwright = sync_playwright().start()
C:\Users\Admin\.vscode\general_scraper\playwright_backend.py:100:                self.context = self.playwright.chromium.launch_persistent_context(
C:\Users\Admin\.vscode\general_scraper\playwright_backend.py:121:                self.playwright = sync_playwright().start()
C:\Users\Admin\.vscode\general_scraper\playwright_backend.py:123:                    self.browser = self.playwright.chromium.launch(headless=headless)
C:\Users\Admin\.vscode\general_scraper\playwright_backend.py:126:                    self.browser = self.playwright.chromium.launch(headless=headless)
C:\Users\Admin\.vscode\general_scraper\playwright_backend.py:347:            if self.playwright:
C:\Users\Admin\.vscode\general_scraper\playwright_backend.py:348:                self.playwright.stop()
C:\Users\Admin\.vscode\general_scraper\playwright_backend.py:487:                "playwright": self.playwright,
C:\Users\Admin\.vscode\general_scraper\interactive_driver.py:65:from playwright.sync_api import sync_playwright
C:\Users\Admin\.vscode\general_scraper\interactive_driver.py:87:    from undetected_playwright import Tarnished
C:\Users\Admin\.vscode\general_scraper\interactive_driver.py:1798:    parser.add_argument("--backend", default="playwright",
C:\Users\Admin\.vscode\general_scraper\interactive_driver.py:1799:                        choices=["playwright", "copilot"],
C:\Users\Admin\.vscode\general_scraper\interactive_driver.py:1800:                        help="Browser backend: playwright (local browser), copilot (Copilot Browser extension)")
C:\Users\Admin\.vscode\general_scraper\interactive_driver.py:1818:                             "Requires undetected-playwright package.")
C:\Users\Admin\.vscode\general_scraper\interactive_driver.py:1822:                             "stealth-js (Tarnished/undetected-playwright), "
C:\Users\Admin\.vscode\general_scraper\interactive_driver.py:1853:        print("ERROR: stealth-js mode requires undetected-playwright. Install with:")
C:\Users\Admin\.vscode\general_scraper\interactive_driver.py:1854:        print("  pip install undetected-playwright")
C:\Users\Admin\.vscode\general_scraper\interactive_driver.py:1886:    if args.backend == "playwright":
C:\Users\Admin\.vscode\general_scraper\interactive_driver.py:1887:        from playwright_backend import PlaywrightBackend
C:\Users\Admin\.vscode\general_scraper\	ests\unit\	est_browser_engine.py:18:    @patch("general_scraper.browser_engine.sync_playwright")
C:\Users\Admin\.vscode\general_scraper\	ests\unit\	est_browser_engine.py:19:    def test_browser_engine_selects_plain_mode(self, mock_playwright):
C:\Users\Admin\.vscode\general_scraper\	ests\unit\	est_browser_engine.py:29:        mock_playwright.return_value.__enter__.return_value = mock_pw
C:\Users\Admin\.vscode\general_scraper\	ests\unit\	est_browser_engine.py:43:    @patch("general_scraper.browser_engine.sync_playwright")
C:\Users\Admin\.vscode\general_scraper\	ests\unit\	est_browser_engine.py:45:    def test_browser_engine_selects_stealth_js_mode(self, mock_tarnished, mock_playwright):
C:\Users\Admin\.vscode\general_scraper\	ests\unit\	est_browser_engine.py:55:        mock_playwright.return_value.__enter__.return_value = mock_pw
C:\Users\Admin\.vscode\general_scraper\	ests\unit\	est_browser_engine.py:71:    @patch("general_scraper.browser_engine.sync_playwright")
C:\Users\Admin\.vscode\general_scraper\	ests\unit\	est_browser_engine.py:73:    def test_browser_engine_selects_stealth_cpp_mode(self, mock_camoufox, mock_playwright):
C:\�ocs\The Clipping project\	ools\export_mobile_snapshot.py:211:
  docs\The Clipping project\	ools\export_mobile_snapshot.py:212:    rows: list[dict[str, Any]] = []
  docs\The Clipping project\	ools\export_mobile_snapshot.py:213:    seen: set[str] = set()
  docs\The Clipping project\	ools\export_mobile_snapshot.py:214:    for target in base_targets:
  docs\The Clipping project\	ools\export_mobile_snapshot.py:215:        key = str(target["key"])
  docs\The Clipping project\	ools\export_mobile_snapshot.py:216:        if int(counts.get(key, 
{}).get("storyCount", 0)) <= 0:
  docs\The Clipping project\	ools\export_mobile_snapshot.py:217:            continue
  docs\The Clipping project\	ools\export_mobile_snapshot.py:218:        rows.append(
  docs\The Clipping project\	ools\export_mobile_snapshot.py:219:            {
  docs\The Clipping project\	ools\export_mobile_snapshot.py:220:                "key": key,
  docs\The Clipping project\	ools\export_mobile_snapshot.py:221:                "label": 
str(target["label"]),
  docs\The Clipping project\	ools\export_mobile_snapshot.py:222:                "primary": 
bool(target.get("primary", False)),
  docs\The Clipping project\	ools\export_mobile_snapshot.py:223:                "storyCount": 
int(counts[key]["storyCount"]),
  docs\The Clipping project\	ools\export_mobile_snapshot.py:224:                "articleCount": 
int(counts[key]["articleCount"]),
  docs\The Clipping project\	ools\export_mobile_snapshot.py:225:            }
  docs\The Clipping project\	ools\export_mobile_snapshot.py:226:        )
  docs\The Clipping project\	ools\export_mobile_snapshot.py:227:        seen.add(key)
  docs\The Clipping project\	ools\export_mobile_snapshot.py:228:
  docs\The Clipping project\	ools\export_mobile_snapshot.py:229:    for key in sorted(counts):
> docs\The Clipping project\	ools\export_mobile_snapshot.py:244:def 
resolve_initial_targets(target_rows: list[dict[str, Any]], default_target: str) -> list[str]:
  docs\The Clipping project\	ools\export_mobile_snapshot.py:245:    keys = [str(row["key"]) for 
row in target_rows]
  docs\The Clipping project\	ools\export_mobile_snapshot.py:246:    if default_target and 
default_target in keys:
  docs\The Clipping project\	ools\export_mobile_snapshot.py:247:        return [default_target]
  docs\The Clipping project\	ools\export_mobile_snapshot.py:248:    return keys
  docs\The Clipping project\	ools\export_mobile_snapshot.py:249:
  docs\The Clipping project\	ools\export_mobile_snapshot.py:250:
> docs\The Clipping project\	ools\export_mobile_snapshot.py:251:def visibility_stats(stories: 
list[dict[str, Any]], selected_targets: list[str]) -> dict[str, Any]:
  docs\The Clipping project\	ools\export_mobile_snapshot.py:252:    selected = 
set(selected_targets)
  docs\The Clipping project\	ools\export_mobile_snapshot.py:253:    if not selected:
  docs\The Clipping project\	ools\export_mobile_snapshot.py:254:        visible = list(stories)
  docs\The Clipping project\	ools\export_mobile_snapshot.py:255:    else:
  docs\The Clipping project\	ools\export_mobile_snapshot.py:256:        visible = [story for story 
in stories if set(story.get("targetKeys", [])) & selected]
  docs\The Clipping project\	ools\export_mobile_snapshot.py:257:    return {
  docs\The Clipping project\	ools\export_mobile_snapshot.py:258:        "storyCount": len(visible),
  docs\The Clipping project\	ools\export_mobile_snapshot.py:259:        "articleCount": 
sum(int(story.get("articleCount") or 0) for story in visible),
  docs\The Clipping project\	ools\export_mobile_snapshot.py:260:        "aiCount": 
sum(int(story.get("aiCount") or 0) for story in visible),
  docs\The Clipping project\	ools\export_mobile_snapshot.py:261:        "rawCount": 
sum(int(story.get("rawCount") or 0) for sto�ry in visible),
  docs\The Clipping project\	ools\export_mobile_snapshot.py:262:        "storyIds": 
{int(story.get("storyIdInt") or 0) for story in visible},
  docs\The Clipping project\	ools\export_mobile_snapshot.py:263:    }
  docs\The Clipping project\	ools\export_mobile_snapshot.py:264:
  docs\The Clipping project\	ools\export_mobile_snapshot.py:265:
  docs\The Clipping project\	ools\export_mobile_snapshot.py:266:def 
active_filter_label(selected_targets: list[str], target_rows: list[dict[str, Any]]) -> str:
  docs\The Clipping project\	ools\export_mobile_snapshot.py:267:    all_keys = [str(row["key"]) 
for row in target_rows]
  docs\The Clipping project\	ools\export_mobile_snapshot.py:268:    if set(selected_targets) == 
set(all_keys):
  docs\The Clipping project\	ools\export_mobile_snapshot.py:269:        return "Todos os nomes 
monitorados"
  docs\The Clipping project\	ools\export_mobile_snapshot.py:270:    labels = [str(row["label"]) 
for row in target_rows if str(row["key"]) in set(selected_targets)]
  docs\The Clipping project\	ools\export_mobile_snapshot.py:271:    return " + ".join(labels) if 
labels else "Todos os nomes monitorados"
  docs\The Clipping project\	ools\export_mobile_snapshot.py:272:
  docs\The Clipping project\	ools\export_mobile_snapshot.py:273:
  docs\The Clipping project\	ools\export_mobile_snapshot.py:274:def target_badges(target_keys: 
list[str], label_by_key: dict[str, str]) -> str:
  docs\The Clipping project\	ools\export_mobile_snapshot.py:275:    return "".join(
  docs\The Clipping project\	ools\export_mobile_snapshot.py:276:        f'<span 
class="chip">{html.escape(label_by_key.get(key, key))}</span>'
> docs\The Clipping project\	ools\export_mobile_snapshot.py:377:def build_html(
  docs\The Clipping project\	ools\export_mobile_snapshot.py:378:    args: argparse.Namespace,
  docs\The Clipping project\	ools\export_mobile_snapshot.py:379:    stories: list[dict[str, Any]],
  docs\The Clipping project\	ools\export_mobile_snapshot.py:380:    target_rows: list[dict[str, 
Any]],
  docs\The Clipping project\	ools\export_mobile_snapshot.py:381:    initial_targets: list[str],
  docs\The Clipping project\	ools\export_mobile_snapshot.py:382:    article_map: dict[int, 
dict[str, Any]],
  docs\The Clipping project\	ools\export_mobile_snapshot.py:383:) -> str:
  docs\The Clipping project\	ools\export_mobile_snapshot.py:384:    label_by_key = 
{str(row["key"]): str(row["label"]) for row in target_rows}
  docs\The Clipping project\	ools\export_mobile_snapshot.py:385:    scope_kicker, scope_title, 
scope_text = scope_labels(args)
  docs\The Clipping project\	ools\export_mobile_snapshot.py:386:    generated_at = 
datetime.now(timezone.utc).strftime("%d/%m/%Y %H:%M UTC")
  docs\The Clipping project\	ools\export_mobile_snapshot.py:387:    total_stories = len(stories)
  docs\The Clipping project\	ools\export_mobile_snapshot.py:388:    total_articles = 
sum(int(story.get("articleCount") or 0) for story in stories)
  docs\The Clipping project\	ools\export_mobile_snapshot.py:389:    total_ai = 
sum(int(story.get("aiCount") or 0) for story in stories)
  docs\The Clipping project\	ools\export_mobile_snapshot.py:390:    total_raw = 
sum(int(story.get("rawCount") or 0) for story in stories)
  docs\The Clipping project\	ools\export_mobile_snapshot.py:391:    initial_stats = 
visibility_stats(stories, initial_targets)
  docs\The Clipping project\	ools\export_mobile_snapshot.py:392:    active_text = 
active_filter_label(initial_targets, target_rows)
  docs\The Clipping project\	ools\export_mobile_snapshot.py:393:    visible_story_ids = 
set(initial_stats["storyIds"])
  docs\The Clipping project\	ools\export_mobile_snapshot.py:394:    payload = {
  docs\The Clipping project\	ools\export_mobile_snapshot.py:395:        \�Users\Admin\.vscode\general_scraper\	ests\unit\	est_browser_engine.py:83:        mock_playwright.return_value.__enter__.return_value = mock_pw
C:\Users\Admin\.vscode\general_scraper\	ests\unit\	est_browser_engine.py:100:    @patch("general_scraper.browser_engine.sync_playwright")
C:\Users\Admin\.vscode\general_scraper\	ests\unit\	est_browser_engine.py:101:    def test_browser_engine_falls_back_to_plain_on_stealth_failure(self, mock_playwright):
C:\Users\Admin\.vscode\general_scraper\	ests\unit\	est_browser_engine.py:111:        mock_playwright.return_value.__enter__.return_value = mock_pw
C:\Users\Admin\.vscode\general_scraper\	ests\unit\	est_browser_engine.py:130:    @patch("general_scraper.browser_engine.sync_playwright")
C:\Users\Admin\.vscode\general_scraper\	ests\unit\	est_browser_engine.py:131:    def test_browser_engine_uses_persistent_session(self, mock_playwright):
C:\Users\Admin\.vscode\general_scraper\	ests\unit\	est_browser_engine.py:140:        mock_playwright.return_value.__enter__.return_value = mock_pw
C:\Users\Admin\.vscode\general_scraper\	ests\unit\	est_browser_engine.py:158:    @patch("general_scraper.browser_engine.sync_playwright")
C:\Users\Admin\.vscode\general_scraper\	ests\unit\	est_browser_engine.py:159:    def test_browser_engine_default_viewport(self, mock_playwright):
C:\Users\Admin\.vscode\general_scraper\	ests\unit\	est_browser_engine.py:169:        mock_playwright.return_value.__enter__.return_value = mock_pw
C:\Users\Admin\.vscode\general_scraper\	ests\unit\	est_browser_engine.py:183:    @patch("general_scraper.browser_engine.sync_playwright")
C:\Users\Admin\.vscode\general_scraper\	ests\unit\	est_browser_engine.py:184:    def test_browser_engine_custom_viewport(self, mock_playwright):
C:\Users\Admin\.vscode\general_scraper\	ests\unit\	est_browser_engine.py:194:        mock_playwright.return_value.__enter__.return_value = mock_pw
C:\Users\Admin\.vscode\general_scraper\	ests\unit\	est_browser_engine.py:211:    @patch("general_scraper.browser_engine.sync_playwright")
C:\Users\Admin\.vscode\general_scraper\	ests\unit\	est_browser_engine.py:212:    def test_browser_engine_headless_false_by_default(self, mock_playwright):
C:\Users\Admin\.vscode\general_scraper\	ests\unit\	est_browser_engine.py:222:        mock_playwright.return_value.__enter__.return_value = mock_pw
C:\Users\Admin\.vscode\general_scraper\	ests\unit\	est_browser_engine.py:239:    @patch("general_scraper.browser_engine.sync_playwright")
C:\Users\Admin\.vscode\general_scraper\	ests\unit\	est_browser_engine.py:240:    def test_browser_engine_close_cleans_up(self, mock_playwright):
C:\Users\Admin\.vscode\general_scraper\	ests\unit\	est_browser_engine.py:242:        Test that close() calls browser.close() and playwright.stop().
C:\Users\Admin\.vscode\general_scraper\	ests\unit\	est_browser_engine.py:251:        mock_playwright.return_value.__enter__.return_value = mock_pw
C:\Users\Admin\.vscode\general_scraper\	ests\unit\	est_browser_engine.py:252:        mock_playwright.return_value.__exit__ = MagicMock()
C:\Users\Admin\.vscode\general_scraper\	ests\unit\	est_browser_engine.py:263:        # Assert: Should close browser and stop playwright
C:\Users\Admin\.vscode\general_scraper\	ests\unit\	est_browser_engine.py:270:    @patch("general_scraper.browser_engine.sync_playwright")
C:\Users\Admin\.vscode\general_scraper\	ests\unit\	est_browser_engine.py:271:    def test_browser_engine_exposes_page_attribute(self, mock_playwright):
C:\Users\Admin\.vscode\general_scraper\	ests\unit\	est_browser_engine.py:281:        mock_playwright.return_value.__enter__.return_value = mock_pw
C:\Users\Admin\.vscode\general_scraper\	ests\unit\	est_browser_engine.py:300:    @patch("general_scraper.browser_engine.sync_playwright")
C:\Users\Admin\.vscode\general_scraper\	ests\unit\E = a.id
529-                      AND mt.target_key IN ({placeholders})
530-                )
531-                """
532-            )
533-            params.extend(target_keys)
534-
535-        sql = f"""
536-            SELECT
537-                a.id,
538-                a.url,
539-                a.title,
540-                a.source_name,
541-                a.source_type,
542-                COALESCE(a.published_at, a.discovered_at) AS published_at,
543-                a.snippet,
544-                a.full_text,
545-                a.summary,
546-                CASE
547-                    WHEN EXISTS (
548-                        SELECT 1
549-                        FROM mentions m2
550-                        WHERE m2.article_id = a.id
551-                          AND COALESCE(m2.sentiment_reason, '') = 'anthropic_batch'
552-                    ) THEN 1 ELSE 0
553-                END AS has_ai_summary,
554-                GROUP_CONCAT(DISTINCT m.target_key) AS target_keys,
555-                GROUP_CONCAT(DISTINCT m.target_name) AS target_names,
556-                GROUP_CONCAT(DISTINCT m.keyword_matched) AS keywords,
557-                sa.story_id
558-            FROM articles a
559-            JOIN mentions m ON m.article_id = a.id
560-            LEFT JOIN story_articles sa ON sa.article_id = a.id
561-            WHERE {" AND ".join(where)}
562-            GROUP BY a.id
563-            ORDER BY COALESCE(a.published_at, a.discovered_at) DESC
564-            LIMIT ?
565-        """
566-        params.append(max(1, int(limit)))
567-
568-        with self.connect() as conn:
569-            rows = conn.execute(sql, tuple(params)).fetchall()
570-            payload: list[dict] = []
571-            for row in rows:
572-                payload.append(
573-                    {
574-                        "article_id": int(row["id"]),
575-                        "url": row["url"] or "",
576-                        "title": row["title"] or "",
577-                        "source_name": row["source_name"] or "",
578-                        "source_type": row["source_type"] or "",
579-                        "published_at": row["published_at"] or "",
580-                        "snippet": row["snippet"] or "",
581-                        "full_text": row["full_text"] or "",
582-                        "summary": row["summary"] or "",
583-                        "has_ai_summary": bool(int(row["has_ai_summary"] or 0)),
"},{