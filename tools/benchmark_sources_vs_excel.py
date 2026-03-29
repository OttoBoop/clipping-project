    FLAVIO_QUERY_VARIANTS,
        raw_candidates = source_module.collect(start_date, end_date, max_candidates)
        raw_urls = {normalize_url(candidate.url) for candidate in raw_candidates if normalize_url(candidate.url)}
        raw_urls = {url for url in raw_urls if host_of(url) == source_module.host}
        raw = str(url or \"\").strip()
 \�uRvbHslXDpqcD-etTsZAQJ0akGpfB1FLb2B_r6HmhQ9vU-a0wSuomsfeOjd0mY6tcy1zaTFj-OF_HMgu3GI_4q3Mt8MZg6orUC4GQYrH9T3amvxmHj3r5S5cU8hy5izvG538SnvnIo23AHXl6Jh5XLNspsfvWP0kH-S2cKgbDooh6ONMEbCqS8ewtJJK5CKctJc-wAMRQHJAsvMsZlRdkSInCtcZVx7R8ZW9N_9oUlv0IMcL9lkafh2NAPRicNUFUFEodUBN9EpYHkPP3jWrA_4iSqY0kmAQvmzZHPQ8M6cCcJt052JAjgLy5m1ULaqr0iPnilA0mPBKxNF8TdbbhXeFSldexTAvEH96jr-gkO94N8gFmusG6ZjqkeU4l5pHZOJynwmfeIaj_GSE8GlQQKTRM-Vvd9hlo0w5MyqgY79RBGRNtQwmMFVkyINR_OW3FJNXaYDnLfVQW7_8M9HTqyD9PlpHtuKllFot0ZK7iLlvkvc4Y75sbjYcJn8NKQDcZ6NqIFuW9AFeILdPgPl9i6e0foHbBLFd4qhX8RBEJoT4LAfH6O"},{"type":"function_call",
        assert source_type == \"camara_archive\"
        if progress_callback:
            progress_callback(
                \"candidate_evaluated\",
                {
                    \"status\": \"skipped\",
                    \"reason\": \"missing_published_at\",
                },
            )
        return IngestionResult(
            source_name=source_name,
            source_type=source_type,
            candidates_seen=len(raw_candidates),
            articles_inserted=0,
            mentions_inserted=0,
            stories_touched=0,
            errors=[],
        )

    monkeypatch.setattr(\"tools.benchmark_sources_vs_excel.ingest_mod.process_candidates\", fake_process_candidates)
    monkeypatch.setattr(
        \"tools.benchmark_sources_vs_excel.db_saved_urls\",
        lambda db_path, *, host: {\"https://camara.rio/comunicacao/noticias/123-exemplo\"},
    )
    result = evaluate_source_module(
        SourceModule(
            host=\"camara.rio\",
            module=\"camara_archive\",
            label=\"Camara via Archive\",
            collect=fake_collect,
            source_type=\"camara_archive\",
        ),
        excel_urls={\"https://camara.rio/comunicacao/noticias/123-exemplo\"},
        start_date=\"2025-05-01\",
        end_date=\"2025-05-31\",
        max_candidates=20,
        budget_seconds=120,
    assert result[\"excel_total\"] == 1
    assert result[\"raw_found\"] == 1
    assert result[\"raw_match\"] == 1
    assert result[\"saved_total\"] == 1
    assert result[\"saved_match\"] == 1
    assert result[\"skip_reasons\"] == {\"missing_published_at\": 1}
    assert result[\"matched_urls\"] == [\"https://camara.rio/comunicacao/noticias/123-exemplo\"]
    assert result[\"missed_urls\"] == []
                queries=list(FLAVIO_QUERY_VARIANTS),
                max_pages_per_target=48,
                max_pages=120,
        parsed = urlsplit(raw if \"://\" in raw else f\"https://{raw}\")
        host = (parsed.netloc or parsed.path or \"\").lower()
      background: var(--ai-bg);
      border-color: rgba(140, 183, 157, 0.65);
    }
    .summary-raw {
      background: var(--raw-bg);
      border-color: rgba(196, 160, 134, 0.65);
    .summary-label {
      margin-bottom: 8px;
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0.12em;
      font-weight: 700;
      color: var(--muted);
    .summary-ai .summary-label {
      color: var(--ai-ink);
    .summary-raw .summary-label {
      color: var(--raw-ink);
    .body-text {
      color: #304052;
      font-size: 15px;
      word-break: break-word;
    .body-text.full {
      margin-top: 12px;
      white-space: pre-wrap;
    .raw-details {
    .raw-details summary {
      cursor: pointer;
      color: var(--accent);
      font-weight: 600;
    .empty-state {
      margin-top: 14px;
      font-size: 14px;
    .footer-note {
      margin-top: 18px;
      font-size: 13px;
      text-align: center;
    [hidden] {
      display: none !important;
    @media (max-width: 720px) {
      main {
        width: min(100% - 16px, 100%);
        padding-top: 8px;
      }
      .hero,
      .panel {
        border-radius: 20px;
        padding-left: 18px;
        padding-right: 18px;
      .story-card {
        padding-left: 0;
        padding-right: 0;
      .story-summary-row,
      .story-meta,
      .story-blurb,
      .story-articles {
        padding-left: 16px;
        padding-right: 16px;
      .article-links {
        flex-direction: column;
        align-items: flex-start;
      .story-stats div {
        min-width: 92px;
  </style>
</head>
<body>
  <main>
    <header class=\"hero\">
      <p class=\"eyebrow\">__SCOPE_KICKER__</p>
      <h1>__SCOPE_TITLE__</h1>
      <p>__SCOPE_TEXT__</p>
      <div class=\"stats\">
        <div class=\"stat\">
          <span>Escopo do arquivo</span>
          <strong>__SCOPE_VALUE__</strong>
          <small>Sem chamadas para /api depois da geracao.</small>
        </div>
          <span>Historias visiveis</span>
          <strong id=\"visibleStoriesStat\">__VISIBLE_STORIES__ / __TOTAL_STORIES__</strong>
          <small>Historias no arquivo: __TOTAL_STORIES__</small>
          <span>Noticias visiveis</span>
          <strong id=\"visibleArticlesStat\">__VISIBLE_ARTICLES__ / __TOTAL_ARTICLES__</strong>
          <small>Somente noticias agrupadas em historias.</small>
          <span>Com resumo IA</span>
          <strong id=\"visibleAiStat\">__VISIBLE_AI__ / __TOTAL_AI__</strong>
          <small>Mostra Resumo IA quando existir.</small>
          <span>Texto bruto</span>
          <strong id=\"visibleRawStat\">__VISIBLE_RAW__ / __TOTAL_RAW__</strong>
          <small>Mostra texto bruto quando nao houver IA.</small>
      </div>
      <div class=\"meta-row\">
        <span>Gerado em: __GENERATED_AT__</span>
        <span>Banco consultado: __DB_NAME__</span>
        <span>Controles de coleta removidos: este arquivo nao dispara novas execucoes.</span>
    </header>
    <section class=\"panel\">
      <div class=\"section-head\">
        <div>
          <p class=\"eyebrow\">Filtro offline</p>
          <h2>Pessoas monitoradas</h2>
      <p class=\"filter-note\">Abre filtrado em __DEFAULT_TARGET_LABEL__. Toque para adicionar ou remover pessoas do filtro.</p>
      <div class=\"filter-row\" id=\"targetFilters\">__FILTER_BUTTONS__</div>
      <p class=\"filter-note\">Filtro ativo: <stv�6d7db69b1e4b7a7f174edb1c6c81a6ec7caa8a244825d5d73422bab1febc7c19ad97addaa7a0e7ab6dd6a18eddef0281f1acd163775b24c3c9f4e13e7e455d6c788b78f663c590bca496d0ccaf59d2cf96955de545b4123e1c5d69c99b3bbad18cac6ca1d74e7c8b897d7b3f5c25d4e8ea3211f6b779fa9b6169bd3fcb830eeccb9335356cb8aa297375c67c65bf3b876658fa36874acdc8f437363b1d3203d5427f3464575faddee9d9707db4be46dac6aac0dbb2bde5f6a23c7ad65fee930a918f566c5196c834dec09a7d5243413afbc6cdfd3cd693f5808f7a5ae4a623dbe950d667d1edc2efb79dbd0bab7815c5323bfd68fba26535f6af6f9ead5e35eb3b61077ab40d6b5e83eacf19160b975a915b9463ceeedbb4db73e7262bf7e8f5653ce89fafaa619cc5859e4cf7b5bd9ef35be3c33c26e7baad4d5a4dbe423a0937eeddebaf72bfb9b38e8c896d1b90a7373505dd6ca4b6ee6722d3b5e7594263b3f0fe69bf3413aaf8e0d5edc269d89c8b4cd71b05930ddddc88dbacdeeb4156a3764735c84bad63219af7adb0d67d2ce3f56d6fb90ed5ddab7dec8b91dc741bbd9db5436e939b8df6fee426c2cef13fedc9c572d514f375df19e5a2e7bab0c368346eb54d5a7ca7abc5d1c1bc2aab545d6d171ad9972e59e1d38d6b254adb319f1c39a53736c76a06d4699a22ce637a55256d6c7d5a97a7256e6b87f978fb6de6c55ccad713ff503e1d25ac9d73abfbd3195d9a47cdfd72f15a7daecf8925faf2c84793712fc0b3309e7fcca4f8ecb61775b9d8f33addb9f8ae5b6de198aa3537ad9863dabe29fac7163d1547bc34b6fdf0995eb70391f7a88fe47d3d976301a8fe44320aad6f4982515d94e786e57d9cecee3eb7564d8754146864550ae3ac678bdbf8d8e9c55ad06c3505b9dcabd7226b7cb9622acb8fab9536ebb3d7dd118991db67e331a7561396db391e40eebbb8535f737558fe314b93b34af3d7f5667a6bdcdd1659870d658b6ea1d4e2e2fe6ee7d754106fa64759d228f800feece5d508e6cacf6343b599b46ef128a5c5fee9c910f1798c1d063597eb7ddce84db651a77f8cb8159578fe3fe4a1d5feba738750c2d126eab83729e5b8292acc44cb5565e365337735f463b98562e9114207e6b0afdf4d06d2a7597dd5d8db9dcbeb1466c5767f5fe6dd565db07d95b8cf9b1efce27d1e69c753a482acc77db6378d6accdbd6f55fb7a3613eb93b1eb86fd8c31b6fe511f058b6a7db90a7b31ab781da737162bd9c51f8c62dd9bf482243bde47fa8a3bbbea411a653b259d37fdddaed59257563f0b94d9602b5a5d4f5aa6f6f2bee35a4a22c8a39dcb187d062948767dbcdc9dac630f1b657e2e89d5a665b3b71b773b21abf992855b891924cbfd8e0d2221f193a87937ac632824c3785cbfecf68d4dd4edd71ca7cfc9236ebb50679e94dcaaf77a979df8d5aa3b13b513effbe96abb69cfa2499dabbaf38131dccd848a34b0954e77af465ce6d439a6edf43de32e577aa7ea52d43a7e724e1a61d938f578c7380d4e8e796baec3c6ead6930226581f9d96386b57d7eb51a659c6b9769dcce461ebba443cd76dcf774298886a6fb26e74fcd9e87a3fd5d7934d35c8a6a2cd5e1869d75bcc86937b25de7acc29e96e4fd5ca34302b959a3a3e1b9b736b7db105a15c6b56f9261fd8fdac1e701327b96cc55ed51fa8fc5ed87758eeb60f36f6bc65a903efd0abfbab61127a27f7aaeb57518f1bac1e72dcb62cb7cc45ec6cba5ec73fb8cb4ebd3aaa248eda2e2bd2954b98c675caf75a7c33abb4a7a75a7fc989337f7af4f44808eb336610efd834550529b057f789c72e1a937b4b988e2fb2346dcdbb53d6e66b0a6b4f26415b908c0572cb7bbed40d66c7b8d5d01bbdd1501a9dfd59cd8be566bae9311d6e98095255f5479dc01b669343a8b1f59a1dfae6703f392ccfd97cae5adb66b2e197dd2852b554df755606bb597667995daf352f7b0579129d195b464659454d7b67ef50ab325777df41bbc3e9b7be5157fbe36ec53ecdec33df8e1a2a622db57aae5d26657fd959f6aeeb598fddae564ad4dff782866a0501d3f3e2e5657f6206a781140fcc892b6c59ffcc6c9296d00b477274beba9378cc2aa1b54ecf7dbebfbddd1b5b6d92ae57e6b1968d4eb277bf1e542bb5cdd92da876abfcb46fb29be4b09b9eeedbcc9d5bb3b9d8db1bebb58ec4d39d1d487cbd9e952fbdc16ddb1ad9fbe6859dd73bb2215b61c246e67d59b6b5754facd983e67456958d4163db431bcd4f5525dc059d79396bcd6e0a7b69cf47abfaca199bfc4ce9ba758dd5fbfe301d27999d9a3361e9b5af75e122217dc11fc761981d47ae3dd9df6ac3f5b63d1c1ee4ce61a71f564623badc92ed7c9bc6adabb5882ab5ee58cdec43ba12b8f5d499aaecd96526e36be65e24a7a10eece03a5f1d0f5d643d9c111ff3cdc9d85c8c6f73c548d2e5bd539bd7037f52edddeb9569430ec2bef9337ed03fdad5fcdddad5fca30bc57f6c178a7f14a4ffbb16a407ef9b169f7c933f039753d057b8e490a27d53a23d80424bc81010f36c4b0c0149b9094284c1180da3989a686be895772c3238144da933f572436590666299a6aab4984a5dd66b3545aa203fe1dd376fc2cd2c8f748820e33ebcf6cfbf7fa7e9ba1f82af7e8334db6721070fff11fd2de95a9c89b4ea930565f5dfe18b4f23e7628fd278a3b8ea726d4eb4ae2c18f5b1dc8531a02a135a6b4c1ea737483071f8a15694b787b22b103349e0330ed041c236bf7f47d2c5e0374a65f80b040da9006d01fedea1fd848f08ae4d1f4d08418e24f6df910fa3e7e8514ea6b82d08640b07b469c63a819b7ea5a50fb9b76f8a137ed85b9e8a68e6238de0c0bd0cbvDrong id=\"activeFilterText\">__ACTIVE_FILTER_TEXT__</strong></p>
    </section>
    <details class=\"panel\">
      <summary class=\"nav-summary\">Indice de historias visiveis (<span id=\"visibleIndexCount\">__VISIBLE_STORIES__</span>)</summary>
      <div class=\"story-index\" id=\"storyIndex\">__STORY_INDEX__</div>
      <p class=\"empty-state\" id=\"emptyState\"__EMPTY_HIDDEN__>Nenhuma historia corresponde aos filtros atuais.</p>
    </details>
    <section id=\"storyStack\">__STORY_SECTIONS__</section>
    <p class=\"footer-note\">Este snapshot foi gerado para compartilhamento em celular. As materias originais seguem com links externos; o restante funciona offline em um unico arquivo HTML.</p>
  </main>
  <script id=\"snapshot-payload\" type=\"application/json\">__PAYLOAD__</script>
  <script>
    (function () {
      const payloadEl = document.getElementById(\"snapshot-payload\");
      if (!payloadEl) return;
      const payload = JSON.parse(payloadEl.textContent || \"{}\");
      const buttons = Array.from(document.querySelectorAll(\"[data-filter-target]\"));
      const storyCards = Array.from(document.querySelectorAll(\"[data-story-id]\"));
      const storyLinks = Array.from(document.querySelectorAll(\"[data-nav-story-id]\"));
      const allTargets = Array.isArray(payload.targets) ? payload.targets.map((target) => target.key) : [];
      const selectedTargets = new Set(Array.isArray(payload.defaultTargets) ? payload.defaultTargets : []);
      const labelsByKey = {};
      (payload.targets || []).forEach((target) => {
        labelsByKey[target.key] = target.label || target.key;
      });
      if (!selectedTargets.size) {
        allTargets.forEach((key) => selectedTargets.add(key));
      function storyTargets(storyId) {
        if (!payload.storyTargets) return [];
        return payload.storyTargets[String(storyId)] || [];
      function storyVisible(targets) {
        if (!targets.length) return true;
        return targets.some((key) => selectedTargets.has(key));
      function activeLabel() {
        if (!allTargets.length || selectedTargets.size === allTargets.length) {
          return \"Todos os nomes monitorados\";
        }
        return allTargets
          .filter((key) => selectedTargets.has(key))
          .map((key) => labelsByKey[key] || key)
          .join(\" + \");
      function applyFilters() {
        let visibleStories = 0;
        let visibleArticles = 0;
        let visibleAi = 0;
        let visibleRaw = 0;
        storyCards.forEach((card) => {
          const targets = storyTargets(card.dataset.storyId);
          const visible = storyVisible(targets);
          card.hidden = !visible;
          if (!visible) return;
          visibleStories += 1;
          visibleArticles += Number(card.dataset.articleCount || 0);
          visibleAi += Number(card.dataset.aiCount || 0);
          visibleRaw += Number(card.dataset.rawCount || 0);
        });
        storyLinks.forEach((link) => {
          link.hidden = !storyVisible(storyTargets(link.dataset.navStoryId));
        buttons.forEach((button) => {
          button.classList.toggle(\"active\", selectedTargets.has(button.dataset.filterTarget));
        const storiesText = visibleStories + \" / \" + storyCards.length;
        const articlesText = visibleArticles + \" / __TOTAL_ARTICLES__\";
        const aiText = visibleAi + \" / __TOTAL_AI__\";
        const rawText = visibleRaw + \" / __TOTAL_RAW__\";
        document.getElementById(\"visibleStoriesStat\").textContent = storiesText;
        document.getElementById(\"visibleArticlesStat\").textContent = articlesText;
        document.getElementById(\"visibleAiStat\").textContent = aiText;
        document.getElementById(\"visibleRawStat\").textContent = rawText;
        document.getElementById(\"visibleIndexCount\").textContent = StringvE(visibleStories);
        document.getElementById(\"activeFilterText\").textContent = activeLabel();
        document.getElementById(\"emptyState\").hidden = visibleStories > 0;
      document.addEventListener(\"click\", (event) => {
        const button = event.target.closest(\"[data-filter-target]\");
        if (!button) return;
        const key = button.dataset.filterTarget;
        if (!key) return;
        if (selectedTargets.has(key)) selectedTargets.delete(key);
        else selectedTargets.add(key);
        if (!selectedTargets.size) {
          allTargets.forEach((item) => selectedTargets.add(item));
        applyFilters();
      applyFilters();
    })();
  </script>
</body>
</html>
\"\"\"
    return (
        template.replace(\"__PAGE_TITLE__\", html.escape(scope_title))
        .replace(\"__SCOPE_KICKER__\", html.escape(scope_kicker))
        .replace(\"__SCOPE_TITLE__\", html.escape(scope_title))
        .replace(\"__SCOPE_TEXT__\", html.escape(scope_text))
        .replace(\"__SCOPE_VALUE__\", html.escape(scope_value))
        .replace(\"__VISIBLE_STORIES__\", str(int(initial_stats[\"storyCount\"])))
        .replace(\"__TOTAL_STORIES__\", str(total_story_count))
        .replace(\"__VISIBLE_ARTICLES__\", str(int(initial_stats[\"articleCount\"])))
        .replace(\"__TOTAL_ARTICLES__\", str(total_article_count))
        .replace(\"__VISIBLE_AI__\", str(int(initial_stats[\"aiCount\"])))
        .replace(\"__TOTAL_AI__\", str(total_ai_count))
        .replace(\"__VISIBLE_RAW__\", str(int(initial_stats[\"rawCount\"])))
        .replace(\"__TOTAL_RAW__\", str(total_raw_count))
        .replace(\"__GENERATED_AT__\", html.escape(generated_at))
        .replace(\"__DB_NAME__\", html.escape(DB_PATH.name))
        .replace(\"__DEFAULT_TARGET_LABEL__\", html.escape(default_target_label))
        .replace(\"__FILTER_BUTTONS__\", filter_buttons)
        .replace(\"__ACTIVE_FILTER_TEXT__\", html.escape(active_filter_text))
        .replace(\"__STORY_INDEX__\", story_index)
        .replace(\"__EMPTY_HIDDEN__\", empty_hidden)
        .replace(\"__STORY_SECTIONS__\", story_sections)
        .replace(\"__PAYLOAD__\", json_for_script(payload))
def main() -> int:
    args = parse_args()
    output_path = output_path_for_args(args)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    db = ClippingDB(DB_PATH)
    base_targets = load_targets()
    detailed_articles = load_scope_articles(db, args)
    article_map = {int(row[\"article_id\"]): row for row in detailed_articles}
    stories = decorate_stories(db.story_with_articles(), article_map)
    target_rows = build_target_rows(base_targets, stories)
    initial_targets = resolve_initial_targets(target_rows, args.default_target)
    html_doc = build_html(
        args=args,
        stories=stories,
        target_rows=target_rows,
        initial_targets=initial_targets,
        article_map=article_map,
    output_path.write_text(html_doc, encoding=\"utf-8\")
    print(output_path)
    print(
        \"stories=%s visible_initial=%s grouped_articles=%s targets=%s\"
        % (
            len(stories),
            visibility_stats(stories, initial_targets)[\"storyCount\"],
            sum(int(story.get(\"articleCount\") or 0) for story in stories),
            len(target_rows),
    return 0
if __name__ == \"__main__\":
    raise SystemExit(main())
        assert end_date == \"2025-05-31\"
        assert max_candidates == 20
        return candidates
    def fake_process_candidates(source_name: str, source_type: str, raw_candidates, *, options=None, progress_callback=None):
        raw_urls = {url for url in raw_urls if host_of(url) == ~kC:\\\\Users\\\\Admin\\\\.vscode\\\\docs\\\\The Clipping project\\\\data\\\\reports\\\\clipping_mobile_snapshot_2026-03-12_2026-03-13.html')\
    try:
        day_candidates = col�O���
QIQQgi� ���,TRACEcodex_app_server::outgoing_messageapp-server event: item/startedcodex_app_server::outgoing_messageapp-server\src\outgoing_message.rs�pid:2916:2b2c31c9-a957-4a90-a018-52189e21fc05�;��
_k__gi� ��?�TRACEcodex_app_server::codex_message_processorapp-server event: codex/event/patch_apply_begincodex_app_server::codex_message_processorapp-server\src\codex_message_processor.rs�pid:2916:2b2c31c9-a957-4a90-a018-52189e21fc05��I���
3WUUgi� ����INFOcodex_otel.log_onlycodex_otel::events::session_telemetryotel\src\events\session_telemetry.rs�019cafa6-f9bb-7f02-b05f-7d5fc60ed10dpid:2916:2b2c31c9-a957-4a90-a018-52189e21fc05`��
QeQQgi� ��'�TRACEcodex_app_server::outgoing_messageapp-server event: account/rateLimits/updatedcodex_app_server::outgoing_messageapp-server\src\outgoing_message.rs�pid:2916:2b2c31c9-a957-4a90-a018-52189e21fc05���
QcQQgi� ���0TRACEcodex_app_server::outgoing_messageapp-server event: thread/tokenUsage/updatedcodex_app_server::outgoing_messageapp-server\src\outgoing_message.rs�pid:2916:2b2c31c9-a957-4a90-a018-52189e21fc05�
�*[
O\���\��&J��'���R
7WUgi�R*�XI�I��V���l
K#KKUgi�\4��DEBUGcodex_core::stream_events_utilsOutput itemcodex_core::stream_events_utilscore\src\stream_events_utils.rs!019ceeff-2c13-7e60-ac0a-09bc9b460021pid:2916:2b2c31c9-a957-4a90-a018-52189e21fc05m�V���e
K#KKUgi�W+/$hDEBUGcodex_core::stream_events_utilsOutput itemcodex_core::stream_events_utilscore\src\stream_events_utils.rs!019ceeff-2c13-7e60-ac0a-09bc9b460021pid:2916:2b2c31c9-a957-4a90-a018-52189e21fc05m�V���c
K#KKUgi�W+,;|DEBUGcodex_core::stream_events_utilsOutput itemcodex_core::stream_events_utilscore\src\stream_events_utils.rs!019ceeff-2c13-7e60-ac0a-09bc9b460021pid:2916:2b2c31c9-a957-4a90-a018-52189e21fc05m�V���m
K#KKUgi�R7:\PDEBUGcodex_core::stream_events_utilsOutput itemcodex_core::stream_events_utilscore\src\stream_events_utils.rs!019ceeff-2c13-7e60-ac0a-09bc9b460021pid:2916:2b2c31c9-a957-4a90-a018-52189e21fc05m����
'//Ugi�R��INFOfeedback_tagscodex_core::codexcore\src\codex.rs	019ceeff-2c13-7e60-ac0a-09bc9b460021pid:2916:2b2c31c9-a957-4a90-a018-52189e21fc053�:���
/?//Ugi�R���TRACEcodex_core::codexpost sampling token usagecodex_core::codexcore\src\codex.rs/019ceeff-2c13-7e60-ac0a-09bc9b460021pid:2916:2b2c31c9-a957-4a90-a018-52189e21fc05Q�K���y
7WUUgi�P�
�INFOcodex_otel.trace_safecodex_otel::events::session_telemetryotel\src\events\session_telemetry.rs(019ceeff-2c13-7e60-ac0a-09bc9b460021pid:2916:2b2c31c9-a957-4a90-a018-52189e21fc05b�I���x
3WUUgi�P��8INFOcodex_otel.log_onlycodex_otel::events::session_telemetryotel\src\events\session_telemetry.rs019ceeff-2c13-7e60-ac0a-09bc9b460021pid:2916:2b2c31c9-a957-4a90-a018-52189e21fc05`�K���w
7WUUgi�P��|INFOcodex_otel.trace_safecodex_otel::events::session_telemetryotel\src\events\session_telemetry.rs(019ceeff-2c13-7e60-ac0a-09bc9b460021pid:2916:2b2c31c9-a957-4a90-a018-52189e21fc05b�I���v
3WUUgi�P�?�INFOcodex_otel.log_onlycodex_otel::events::session_telemetryotel\src\events\session_telemetry.rs019ceeff-2c13-7e60-ac0a-09bc9b460021pid:2916:2b2c31c9-a957-4a90-a018-52189e21fc05`����o/�O//Ugi�N�" TRACEcodex_core::spawnspawn_child_async: "C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" ["-Command", "[Console]::OutputEncoding=[System.Text.Encoding]::UTF8;
        day_candidates = collect_cbn_day_candidates(source_module, day_str=day_str, day_limit=int(options.cbn_day_limit))
    except RuntimeError as exc:
        message = str(exc)
        if message.startswith(\"possible_truncation:\"):
            raise
        if message.startswith(\"sitemap_fetch_error:\"):
            return {
                \"date\": day_str,
                \"raw_urls\": [],
                \"positive_candidates\": [],
                \"excel_matches_discovered\": [],
                \"excel_matches_prescreen\": [],
                \"fetch_errors\": [{\"url\": \"\", \"error\": message}],
                \"runtime_seconds\": round(time.monotonic() - day_started_at, 3),
            }
        raise
DEFAULT_START_DATE = \"2025-05-01\"
DEFAULT_END_DATE = \"2025-07-31\"
def build_cbn_run_dir(run_id: str, source_module: SourceModule) -> Path:
    source_key = f\"{source_module.host}_{source_module.module}\".replace(\"/\", \"_\")
    return PROJECT_ROOT / \"data\" / \"experiments\" / \"sitemap_benchmark_runs\" / run_id / source_key
def source_uses_sitemap_fast_path(source_module: SourceModule, *, cbn_fast_path: str = \"auto\") -> bool:
    mode = str(cbn_fast_path or \"auto\").strip().lower()
    if mode == \"off\":
        return False
    if source_module.module != \"sitemap_daily\" or source_module.source_type != \"sitemap_daily\":
        source = get_sitemap_source(source_module.host)
    except RuntimeError:
    return str(source.get(\"benchmark_fast_path\") or \"\").strip().lower() == \"sitemap_body_prescreen\"
    if source_uses_sitemap_fast_path(source_module, cbn_fast_path=cbn_fast_path):
    run_dir = build_cbn_run_dir(run_id, source_module)
    effective_day_limit = max(1, int(source.get(\"benchmark_day_limit\") or day_limit))
        \"desktop\": str(desktop_path.resolve()),
        \"mobile\": str(mobile_path.resolve()),
def prepare_snapshot(args: argparse.Namespace) -> dict[str, Any]:
    prepared_at = datetime.now(timezone.utc)
    prepared_token = prepared_at.strftime(\"%Y%m%dT%H%M%SZ\")
    canonical_output = export_mobile_snapshot.output_path_for_args(args)
    current_output = Path(args.current_output).expanduser().resolve()
    archive_dir = Path(args.archive_dir).expanduser().resolve()
    review_root = Path(args.review_dir).expanduser().resolve()
    artifact = export_mobile_snapshot.build_snapshot_artifact(args)
    stories = artifact[\"stories\"]
    target_rows = artifact[\"target_rows\"]
    initial_targets = artifact[\"initial_targets\"]
    initial_stats = artifact[\"initial_stats\"]
    html_doc = artifact[\"html_doc\"]
    validation = validate_snapshot_html(html_doc)
    if not validation[\"ok\"]:
        raise RuntimeError(
            \"Snapshot HTML invalido para o fluxo do Wix: \"
            + \", \".join(validation[\"missing_markers\"])
    canonical_output.parent.mkdir(parents=True, exist_ok=True)
    current_output.parent.mkdir(parents=True, exist_ok=True)
    archive_dir.mkdir(parents=True, exist_ok=True)
    review_bundle_dir = review_root / f\"{scope_token(args)}_{prepared_token}\"
    review_bundle_dir.mkdir(parents=True, exist_ok=True)
    canonical_output.write_text(html_doc, encoding=\"utf-8\")
    shutil.copy2(canonical_output, current_output)
    archive_html = archive_dir / f\"clipping_mobile_snapshot_wix_{scope_token(args)}_{prepared_token}.html\"
    shutil.copy2(current_output, archive_html)
    screenshots = render_review_screenshots(current_output, review_bundle_dir)
    metadata = {
        \"preparedAt\": prepared_at.isoformat(),
        \"scopeToken\": scope_token(args),
        \"allStories\": bool(args.all_stories),
        \"dateFrom\": args.date_from,
        \"dateTo\": args.date_to,
        \"defaultTarget\": args.default_target,
        \"canonicalOutputPath\": str(canonical_output.resolve()),
        \"currentOutputPath\": str(current_output),
        \"archiveHtmlPath\": str(archive_html),
        \"reviewDirectory\": str(review_bundle_dir),
        \"desktopScreenshotPath\": screenshots[\"desktop\"],
        \"mobileScreenshotPath\": screenshots[\"mobile\"],
        \"fileSizeBytes\": current_output.stat().st_size,
        \"storyCount\": len(stories),
        \"groupedArticleCount\": sum(int(story.get(\"articleCount\") or 0) for story in stories),
        \"initialVisibleStoryCount\": int(initial_stats[\"storyCount\"]),
        \"initialVisibleArticleCount\": int(initial_stats[\"articleCount\"]),
        \"targetCount\": len(target_rows),
        \"validation\": validation,
        \"requiredMarkers\": list(REQUIRED_MARKERS),
    archive_metadata = archive_dir / f\"clipping_mobile_snapshot_wix_{scope_token(args)}_{prepared_token}.json\"
    archive_metadata.write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2),
        encoding=\"utf-8\",
    CURRENT_METADATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    CURRENT_METADATA_PATH.write_text(
    metadata[\"archiveMetadataPath\"] = str(archive_metadata.resolve())
    metadata[\"currentMetadataPath\"] = str(CURRENT_METADATA_PATH.resolve())
    return metadata
    metadata = prepare_snapshot(args)
    if args.json:
        print(json.dumps(metadata, ensure_ascii=False))
    else:
        print(metadata[\"c
�r
    excel_days_only: bool = False
    excel_days: set[str] | None = None,
    if options.excel_days_only and excel_days:
        days = sorted(day for day in excel_days if day)
        days = iter_window_days(options.start_date, options.end_date)
        \"excel_days_only\": bool(options.excel_days_only),
    excel_days: set[str] | None,
    excel_days_only: bool = False,
        excel_days_only=bool(excel_days_only),
        excel_days=excel_days,
        \"excel_days_only\",
                    \"excel_days_only\": row.get(\"excel_days_only\", \"\"),
    parser.add_argument(\"--excel-days-only\", action=\"store_true\", help=\"For fast-path sitemap benchmarks, scan only days present in the Excel rows for that host\")
    excel_days_by_host: dict[str, set[str]] = {}
        day_str = str(row.get(\"date\") or \"\")[:10]
        if day_str:
            excel_days_by_host.setdefault(row[\"host\"], set()).add(day_str)
            excel_days=excel_days_by_host.get(source_module.host, set()),
            excel_days_only=bool(args.excel_days_only),
    excel_day_padding: int = 0
def expand_excel_days(days: set[OT NULL,\r
def expand_excel_days(days: set[str], *, start_date: str, end_date: str, padding: int) -> set[str]:
    if not days:
        return set()
    if int(padding) <= 0:
        return {str(day) for day in days if str(day)}
    start = datetime.strptime(start_date, \"%Y-%m-%d\").date()
    end = datetime.strptime(end_date, \"%Y-%m-%d\").date()
    expanded: set[str] = set()
    for day_str in days:
        raw = str(day_str or \"\").strip()
        if not raw:
            continue
        base_day = datetime.strptime(raw, \"%Y-%m-%d\").date()
        for offset in range(-int(padding), int(padding) + 1):
            current = base_day + timedelta(days=offset)
            if current < start or current > end:
                continue
            expanded.add(current.isoformat())
    return expanded
        \"excel_day_padding\": int(options.excel_day_padding),
    excel_day_padding: int = 0,
        excel_day_padding=max(0, int(excel_day_padding)),
        \"excel_day_padding\",
        days = sorted(day for day in 0m-UzWK9p630hlcVgj0hQavN8r9KjDx0NcAzvtX2sqdZI-auAVI1zYc5_imu2ilMPJ8VHI0NN2sosdWShwfsvMpJehywZb-FxiZhRk0v1grfawRccxuG7j_wsWCTek1KyPoKZgOMHMEbiV23kghT5eKoBmCq0rI3pT3zQ_r8qeSRLuNc_MIQ43S1WrYQovT95M2p5aZ3d-mMShl679HuHnEF0aY5lnxxm_w6w2xkSV3BjIRcqzCuL1JEKjLjQ0YxwSI1dFSaP8DGpWvAe6066XbP2ADhkxJOJ8RB78zfOIQZpxzYEmZjzpogu9gQ0ypNRwqJ7CMwnDFfaUpD-62s4pZ8Jj-F56BqqgnPJ1y2zgoi3jE18Zd9ec3HpFdfqyE"},{"type":"function_call",
def _clean_embedded_text(value: str) -> str:
    cleaned = html.unescape(str(value or \"\"))
    cleaned = WS_RE.sub(\" \", cleaned).strip()
    return cleaned
def _json_string_to_text(value: str) -> str:
    raw = str(value or \"\")
    if not raw:
        return \"\"
        decoded = json.loads(f'\"{raw}\"')
    except Exception:
        decoded = raw.encode(\"utf-8\", errors=\"ignore\").decode(\"unicode_escape\", errors=\"ignore\")
    return _clean_embedded_text(decoded)
def _collect_text_values(node) -> list[str]:
    hits: list[str] = []
    if isinstance(node, dict):
        for key, value in node.items():
            key_name = str(key or \"\").strip().lower()
            if key_name in {\"articlebody\", \"body\", \"content\", \"description\", \"text\"} and isinstance(value, str):
                cleaned = _clean_embedded_text(value)
                if len(cleaned.split()) >= 20:
                    hits.append(cleaned)
            hits.extend(_collect_text_values(value))
    elif isinstance(node, list):
        for item in node:
            hits.extend(_collect_text_values(item))
    return hits
def extract_embedded_article_text(raw_html: str) -> str:
    html_body = raw_html or \"\"
    candidates: list[str] = []
    for match in LDJSON_BLOCK_RE.finditer(html_body):
        script_body = str(match.group(1) or \"\").strip()
        if not script_body:
        try:
            parsed = json.loads(script_body)
        except Exception:
        candidates.extend(_collect_text_values(parsed))
    for match in SCRIPT_BLOCK_RE.finditer(html_body):
        script_body = str(match.group(1) or \"\")
        for value_match in JSON_TEXT_VALUE_RE.finditer(script_body):
            cleaned = _json_string_to_text(value_match.group(1))
            if len(cleaned.split()) >= 20:
                candidates.append(cleaned)
    if not candidates:
    return max(candidates, key=lambda chunk: len(chunk))
    article_text = html_to_text(best)
    if len(article_text.split()) >= 80:
        return article_text
    embedded_text = extract_embedded_article_text(raw_html)
    if len(embedded_text.split()) > len(article_text.split()):
        return embedded_text
    return article_text
    return PROJECT_ROOT / \"data\" / \"expe�M6wv5Rk4WHhuOyYHiXqXsmTzT46Vdgs8azAnAN8a84zFGAzjIPbs3FeBjQaHWLJ46_sQf91GkqcviMBwnb36OC5r1PHRd0YmbCz0eFL2U-kxeYx3qKkad1s4yok8zvzizAzOi9HFm2kga7W_mm866-8csLRWwQwU6gCpWC_xTUWQuR2ygRxdOhhbNWxbzTT6UDxdQHXQrCQyJa1vEoCsI7_x4vTyfeOAFAEifkZP0VdIP8yVfXhf-2rBIPsh4UWZzd0ALMibnUUmisOkhS9KSC5_te4pe9fGuOt7Lo9RpD7EPAysBmOAHOS8uZCW3NAQf5uHmxZhgWwBz4dC6xmBCjRQcaWQ3xFbZJLjvQcAAzDoX9GBFpnkb54JSxX_1EEezpmgY3JfBR5q6-E1o2dW7tGdQ94GCmGQTAh0KEcdySZLru7XMJ2AudJS0iawFtECPkaYAbf5KnkYCigP21Jq5fq-yTRxbUHsazeTDIJZLjnoKX7d9-NxLUFf8AJuIt1DFc7IQPfLuYpI6_QNHOykkt1SNkji1El4kaG_6ek_JHmPCn7itAbmGuNdyoYw5P2bUs7o46OjRz6ww9T6HzBrxg2HcNg1bx2nJ-fbSvNzYhuh1goID2kObGeooriy3mGe-7KCIpUdMZuyyeeaU2axcpmqXHRbB3CWEUNLDnNZiVJ_lptdT8TBZq3U7jX22BxaaWNU-oIKMXWLV3o14kRSgeK3GfzqKh11K3ihAjZWeD35HruN_Q-qCdhwfCZxvdvvpt1nKCEI4TprV49raZH70CczOLltl-GSA07U3HvMPTN3_V5XTM_fesaiGXlVjLVb3S-1MfDf_0hCHmFfKhblFBxRE2O247PwbSvyaZedJ_wPjSlVEMEFRlCvV0lIYEZqicqT2nxWgjlHKmALIp4u__1oZzifUpGD-Vhu0CgzprhsOzCvat15EvFOf4MG8kiMy_fiWva_bjAapAWPfwzn0YZ8Vs_7YiflaJllUruDZoh0VshvMfH25B93cuOsJuB0-0UvuliXOr1aGyY52XY9y-KajJxG1BcTZEcYDI2ZD18nmcr32s5CTt_L_Slz6g-F-zddZRdzGJycfSDCw9xio_zwk1aATO7-Ro8iJPCGWwCKVW9d4qsJkUVPfUP-aM4NqmJVfukjeFi3MxqOxUmcy_KZLxSZz1nPdPu3bk5EKl-2MLK53QMDTo-h5WRoKP-YuKT2g5ItWFaVpOAsDtD8AcwJWfa8WYhOH78V0Krdbstti0OQ6aZ8iROGQ-FI2lLznLbklk1342h6QDueYWZdlMJ_3s84JWn8FbVELKwrN0_6emiDc_Z5EqB6Ns2b6BQ1nZz5yggyf2mpPvpr2NRZ_n8aocIrqpNUQx0sPoUhXoz-OQT2LY-izEAvK5kTk1zxj8vOYO5rNu5fv-0kq7JHLuZZvkvfKmZZZwXYZzZkKL6CyZYye_c9N2aED-B5mT2jqhUDES2jeX36wjvPW18IeOETR2Y84sLQL1-AHAYNlkEaZv-8GAUN1Z0aDi3ks2gWXTmpJGiJb1vtTbbG8WDIO5mtkwYCgUXCGtwHWDmIz82jYFEq1Sut0Z_QVu_1xuFlxhcy1svft7iD8J5qHCLRswYYpHlAe3r9e4kM5bcgLudDj5DPohZN-0QrNTOJ2P-uXwAAezIO4MGxZgnAB2bViOg9uqzT7Kc1SZE-FxZl7Qvmlf4EsyBfkGZTG6oG1SKHXX311-cc8q3Cg6NsVcH3Bt-3mtM4Avr3TdhBXnQszNhczFpKw1slFRD8twY1hjppsS6El5PtDcXTuaAf9aveb3M078aqAcal4aEX29QW8JA1SU4gkWOZ2TbuKWbW7o6XZqRyV4kr-faEH3-p0rwts8Y-D3G-2zZ0CtrllbBH5rSF6TCw9jWAFQit3-P_XikQPe8QnwTAoDF0zs8JOUK99L9d3fP-94V_F5ClNbK8lCQif50t0QhaqXIkLERJWcbe4iq3XOUwQ7xEAUBpFHrv0rOWT378YliJIpen-nGXA10pzY55KlY9Txe_zoXePBCiLdQCz6bUlXQDTr0ehU2kiCO71HUWKJEwVZJ8pXjaO8A4T__uvj9TD3bMw7QJvLb5tcmHxoUcmOHTrRngy3wmNPy3swjZh3gt3bS8RHVLy4FjLk7XF5bhdsf2sr2cJrXzmhsQdAKQ6DkL-ehPZwA7eVsF6I_-DAEI5TPJNYSTzTInMcUvjrMEA-eiLxBK5C8qxUSYumt4qKYDp_Yuu5ds0Y-J-9BdcHXC1OdtIZeHA6fDyBKQCmzwsjHT7RA0VH8SLv2ocSYQqL62DdPRgpcwwWAR3dmE0q-Ozh7LyramE4TiUe_w_MArFdKJP-dAhGp7QDEhzyGNbENuILN_PpxdCW3EJ5jG53R8CeNbafrzv6WvgDCbUtTm1ziRcRoCbHOD9dGZZBEIFGtC-aOjLkCWmnXaNcCAT9Q9ZgeLylsJA4WLWQGa850an1w8WLAfv_XksUKrSR5i4c1PO41fI8wPfz32cfRI0sArQEY4noy60G6P0ARmsGooWmQ6tuGTwffYs3yOvbImbH1oX9Vjyt4LCDay50rTuA68F8CF48mL8tBx432-sRGVhYapRqHuOXoDcWLQrJ8-f5loP_H-iBdr5GDpr-NK1nwEBh9VaJpHjR7BkgsUsWenY-5cc2s8iWMZJcoc2Yv7_6RkarCSUC9eEaux3zheFGO-Rz7YZorP7rdlmvE92XnCEDvjQDsz2CGUcewsGCrIYuH-ScnnlZ7ziLy2PAYfnr3s7mwn8kDUxox1tML24wpsWktKXcuGIr6t021MYoqitOC0IcClP8nUH8uE1VIDcRGSa3JBT3O5CQHPY2SyUXMVv_0fAPEjNRWwruqdaaQocGWSrgmsVamvwx0c4d56SKkSpJfalV8D0eUg_GlPbMNTthvepHN4k0L2HR6XBRfXKiH1hkiZ_c7Nw3bjlmMeavVGXWTdk7_PSZZ9EcEWcz1saW-pA1icktIYKXS69C2vclz0efvX9AV1ycbDGNwOErDU4AgO-CeGGYBkG5_V8QswgdSq7Jrzh9XO3C-1_C8JkOlgV6F0jr4w561NT_DqcR5N3Vodq3M-W__7zsGyto72ruDwE_Vbi_NX4-M7J2StA6KkWxuYCC7rBelgZ7GXoJs1nwtf0E-wbLBKjWSMlRceadUWVnlmGkIZZ7dFsLplLuvYtcp8aCn2FboaUGhg2Lh8N-e_pOOOgKbiKlDi5t2cv_ld7GhhulTwmJNJMmOgfle4uWA0t2HYtHWVbXRtZsutRXMrhkB6PXUVPRF5VjAwL63rDu4F4UcflnIV8YnQMrK8Rp_RJ2augWkCKMnaJWck-tHEsClUrqmZ99GK2aSOp91En9JEYCwkYD1kSqe9WQJFoWceMg70p3UFKrz-ptladDtTxqyXx4VBmeyxZvg-Yt9wwW2PnFAJfgZ-IQflwOCO04j8qZlvapq41nXNxzmqzp5i5wRxl0UwPn9p5kI3teNE6dB2OtpbYacEZ7vJBE4F6HTg9-xv0sFQ58kdRScrkiicF6DqtPLGnDuWZ47Gw1e8DQ7G6QsoBUGH9S0Uk5ScUchvuPhDrCw8JgCeoWF3KQ0Nk2KqST1lFaM6wEF0c2KHzF4ichvnamrWT43uMsvtkwDxMwgXkyyIOYub1Y_pvGd8pQ9T0041u1a_W1DBBtVNhAMSbd-Yu_bO-GofN4dBYKew4cfBj6rW75bKcTTW24sW6SNAzgPqi7fI20Mykv_7BEswnTcrVANOVtad7YjFApR-ykW09qHapspCltKQz_amQPJ1LAZVujGiRM_1m7K4C2BanalHlPT8aTiaVin5PPombrvXb3L3He2bZRNUi6uKO_vnFc4C-YQsLYE4wqECxEGeqMbjb_ap8VTEzAFtFipvwIU53XDu9Heuq5nRmH7QHY8l8lmoBTmRmC1TR6mwExDTcFHVe5alhVZu9F7tZv9MNIq35h639AnjFP5ze_SYggDClbyODUY1-MiCBtBaKp5OigK5Qp9Fg1kz-YG99CRW_DNp2Uq21bDVAuWxD7VOHJQQMtcAEg-qBeCCgB3ldC8x
�]���B�eUgi�:�DTRACElogSending ClientHello Message {
    version: TLSv1_0,
    payload: Handshake {
        parsed: HandshakeMessagePayload(
            ClientHello(
                ClientHelloPayload {
                    client_version: TLSv1_2,
                    random: d5cfbf00da6d40c99dbcb89e28a6799644b6ec0e6ab9dbe0c5642c4a8b10c1cd,
                    session_id: 9f722954ec18986ba66c1dc8e3603a71748c067379218e7c7b477f2d6b04d46d,
                    cipher_suites: [
                        TLS13_AES_256_GCM_SHA384,
                        TLS13_AES_128_GCM_SHA256,
                        TLS13_CHACHA20_POLY1305_SHA256,
                        TLS_ECDHE_ECDSA_WITH_AES_256_GCM_SHA384,
                        TLS_ECDHE_ECDSA_WITH_AES_128_GCM_SHA256,
                        TLS_ECDHE_ECDSA_WITH_CHACHA20_POLY1305_SHA256,
                        TLS_ECDHE_RSA_WITH_AES_256_GCM_SHA384,
                        TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256,
                        TLS_ECDHE_RSA_WITH_CHACHA20_POLY1305_SHA256,
                        TLS_EMPTY_RENEGOTIATION_INFO_SCSV,
                    ],
                    compression_methods: [
                        Null,
                    ],
                    extensions: ClientExtensions {
                        server_name: SingleDnsName(
                            DnsName(
                                "chatgpt.com",
                            ),
                        ),
                        certificate_status_request: Ocsp(
                            OcspCertificateStatusRequest {
                                responder_ids: [],
                                extensions: ,
                            },
                        ),
                        named_groups: [
                            X25519,
                            secp256r1,
                            secp384r1,
                        ],
                        ec_point_formats: SupportedEcPointFormats {
                            uncompressed: true,
                        },
                        signature_schemes: [
                            ECDSA_NISTP384_SHA384,
                            ECDSA_NISTP256_SHA256,
                            ED25519,
                            RSA_PSS_SHA512,
                            RSA_PSS_SHA384,
                            RSA_PSS_SHA256,
                            RSA_PKCS1_SHA512,
                            RSA_PKCS1_SHA384,
                            RSA_PKCS1_SHA256,
                        ],
                        extended_master_secret_request: (),
                        session_ticket: Request,
                        supported_versions: SupportedProtocolVersions {
                            tls13: true,
                            tls12: true,
                        },
                        preshared_key_modes: PskKeyExchangeModes {
                            psk_dhe: true,
                            psk: false,
                        },
                        key_shares: [
                            KeyShareEntry {
                                group: X25519,
                                payload: bfc039629194d3d32acc29b50004229004ae1362820c96e37947cc648909cd06,
                            },
                        ],
                        order_seed: 6095,
                        contiguous_extensions: [],
                        ..
                    },
                },
            ),
        ),
        encoded: 010000e50303d5cfbf00da6d40c99dbcb89e28a6799644b6ec0e6ab9dbe0c5642c4a8b10c1cd209f722954ec18986ba66c1dc8e3603a71748c067379218e7c7b477f2d6b04d46d0014130213011303c02cc02bcca9c030c02fcca800ff01000088000d00140012050304030807080608050804060105010401002d0002010100050005010000000000000010000e00000b636861746770742e636f6d0017000000230000000a00080006001d00170018003300260024001d0020bfc039629194d3d32acc29b50004229004ae1362820c96e37947cc648909cd06000b00020100002b00050403040303,
    },
}019ccec6-627d-7f70-8dc9-36bf55ca3683pid:2916:2b2c31c9-a957-4a90-a018-52189e21fc05t�EtFt7M2t4EuciHAMIbcXIbnF7M7NomvJGf0_hDWbvhj4CkgkW5Gt2YAhuW2wd_iBncDMzdlLzAzTcg5iQtqMagtG-81a8VjUqXWlvfz6_oVUUNQYyGwHt3GBnlM997XWuU0hXQqVpsQTBGeyMIXeENErjqv0U0dQ4NnbVfDwz9-8RWdT0vMfAHSOYVAsJsoOqXIXitxbrhxoCU8dQ764UPsElXQ5Q9UMcuAFqrYV7HSTpBzBrAMVyElGrgcErkiz3lh2fo4aE_CgiczOzcKJXduoCAe_hnNbO418lmyLxPBaqt9Af9gT4r4s2fDvhcsVZUH499HCZslMPhcZfgqkqtlIvqUB0mu0XixFEJFgkaOXEPdSWU-b4wFVV3NqHmAktTq3OvRT1taJTMMzhFTa7BVHm11DwUaRAramHqoejXViAlpy-4pKC1HGRMYOiRC-Ns37zY="},{"type":"message","role":"assistant","content":[{"type":"output_text","text":"Já tenho o ponto exato onde o benchmark zera a família Globo. Agora vou abrir os trechos de `collect_sitemap_daily`, `fetch_full_article_text` e `html_to_article_text` para encaixar o diagnóstico sem duplicar lógica."}],"phase":"commentary"},{"type":"function_call",
    if options.ex�cel_days_only and excel_days:
                    \"excel_day_padding\": row.get(\"excel_day_padding\", \"\"),
    parser.add_argument(\"--excel-day-padding\", type=int, default=0, help=\"Extra days to scan around each Excel date when --excel-days-only is enabled\")
            excel_days=expand_excel_days(
                excel_days_by_host.get(source_module.host, set()),
                start_date=args.start_date,
                end_date=args.end_date,
                padding=max(0, int(args.excel_day_padding)),
            ),
            excel_day_padding=max(0, int(args.excel_day_padding)),
    return str(source.get(\"benchmarkU_fast_path\") or \"\").strip().lower() == \"sitemap_body_prescreen\"
                    \"query_prefilter_applied\": bool(source.get(\"prefilter_queries\", False)),
                    \"window_by_sitemap_day\": bool(source.get(\"window_by_sitemap_day\")),
        if len(candidates) >= effective_day_limit:
    if mode == \"off\"

]�
���
�	����~nm]M=�
���W/
c�ii�u`3zLDEBUGopentelemetry_sdkopentelemetry_sdk::metrics::periodic_readerC:\Users\runneradmin\.cargo\registry\src\index.crates.io-1949cf8c6b5b557f\opentelemetry_sdk-0.31.0\src\metrics\periodic_reader.rs�pid:15240:1593c4df-26fc-4cbc-9fae-07584203ed31
���V/
c�ii�u`3y�DDEBUGopentelemetry_sdkopentelemetry_sdk::metrics::periodic_readerC:\Users\runneradmin\.cargo\registry\src\index.crates.io-1949cf8c6b5b557f\opentelemetry_sdk-0.31.0\src\metrics\periodic_reader.rs pid:15240:1593c4df-26fc-4cbc-9fae-07584203ed31
���U/
c�ii�u`3y͔DEBUGopentelemetry_sdkopentelemetry_sdk::metrics::periodic_readerC:\Users\runneradmin\.cargo\registry\src\index.crates.io-1949cf8c6b5b557f\opentelemetry_sdk-0.31.0\src\metrics\periodic_reader.rs�pid:15240:1593c4df-26fc-4cbc-9fae-07584203ed31{���T/
U�ii�u`3y��DEBUGopentelemetry_sdkopentelemetry_sdk::metrics::pipelineC:\Users\runneradmin\.cargo\registry\src\index.crates.io-1949cf8c6b5b557f\opentelemetry_sdk-0.31.0\src\metrics\pipeline.rslpid:15240:1593c4df-26fc-4cbc-9fae-07584203ed31��
���S/
c�ii�u`3x�(DEBUGopentelemetry_sdkopentelemetry_sdk::metrics::periodic_readerC:\Users\runneradmin\.cargo\registry\src\index.crates.io-1949cf8c6b5b557f\opentelemetry_sdk-0.31.0\src\metrics\periodic_reader.rspid:15240:1593c4df-26fc-4cbc-9fae-07584203ed31
���R/
c�ii�u$2�#PDEBUGopentelemetry_sdkopentelemetry_sdk::metrics::periodic_readerC:\Users\runneradmin\.cargo\registry\src\index.crates.io-1949cf8c6b5b557f\opentelemetry_sdk-0.31.0\src\metrics\periodic_reader.rs�pid:15240:1593c4df-26fc-4cbc-9fae-07584203ed31
���Q/
c�ii�u$2���DEBUGopentelemetry_sdkopentelemetry_sdk::metrics::periodic_readerC:\Users\runneradmin\.cargo\registry\src\index.crates.io-1949cf8c6b5b557f\opentelemetry_sdk-0.31.0\src\metrics\periodic_reader.rs pid:15240:1593c4df-26fc-4cbc-9fae-07584203ed31
���P/
c�ii�u$2��hDEBUGopentelemetry_sdkopentelemetry_sdk::metrics::periodic_readerC:\Users\runneradmin\.cargo\registry\src\index.crates.io-1949cf8c6b5b557f\opentelemetry_sdk-0.31.0\src\metrics\periodic_reader.rs�pid:15240:1593c4df-26fc-4cbc-9fae-07584203ed31{���O/
U�ii�u$2���DEBUGopentelemetry_sdkopentelemetry_sdk::metrics::pipelineC:\Users\runneradmin\.cargo\registry\src\index.crates.io-1949cf8c6b5b557f\opentelemetry_sdk-0.31.0\src\metrics\pipeline.rslpid:15240:1593c4df-26fc-4cbc-9fae-07584203ed31��
���N/
c�ii�u$2� �DEBUGopentelemetry_sdkopentelemetry_sdk::metrics::periodic_readerC:\Users\runneradmin\.cargo\registry\src\index.crates.io-1949cf8c6b5b557f\opentelemetry_sdk-0.31.0\src\metrics\periodic_reader.rspid:15240:1593c4df-26fc-4cbc-9fae-07584203ed31
���M/
c�ii�t�2g�,DEBUGopentelemetry_sdkopentelemetry_sdk::metrics::periodic_readerC:\Users\runneradmin\.cargo\registry\src\index.crates.io-1949cf8c6b5b557f\opentelemetry_sdk-0.31.0\src\metrics\periodic_reader.rs�pid:15240:1593c4df-26fc-4cbc-9fae-07584203ed31
���L/
c�ii�t�2g��DEBUGopentelemetry_sdkopentelemetry_sdk::metrics::periodic_readerC:\Users\runneradmin\.cargo\registry\src\index.crates.io-1949cf8c6b5b557f\opentelemetry_sdk-0.31.0\src\metrics\periodic_reader.rs pid:15240:1593c4df-26fc-4cbc-9fae-07584203ed31
���K/
c�ii�t�2g�8DEBUGopentelemetry_sdkopentelemetry_sdk::metrics::periodic_readerC:\Users\runneradmin\.cargo\registry\src\index.crates.io-1949cf8c6b5b557f\opentelemetry_sdk-0.31.0\src\metrics\periodic_reader.rs�pid:15240:1593c4df-26fc-4cbc-9fae-07584203ed31{���J/
U�ii�t�2gz<DEBUGopentelemetry_sdkopentelemetry_sdk::metrics::pipelineC:\Users\runneradmin\.cargo\registry\src\index.crates.io-1949cf8c6b5b557f\opentelemetry_sdk-0.31.0\src\metrics\pipeline.rslpid:15240:1593c4df-26fc-4cbc-9fae-07584203ed31��
���I/
c�ii�t�2g�DEBUGopentelemetry_sdkopentelemetry_sdk::metrics::periodic_readerC:\Users\runneradmin\.cargo\registry\src\index.crates.io-1949cf8c6b5b557f\opentelemetry_sdk-0.31.0\src\metrics\periodic_reader.rspid:15240:1593c4df-26fc-4cbc-9fae-07584203ed31�(��(&%���(�(�(?���_��gh����������������	(r(���$�$�'!�(m'�((�( (h!�!�!�!�!�!�!}(�(!""" "#"*";"H"K"O"Q"S"U"W"Y"["`"a"b"h"f"e"d"c"q"i"j"k"l"m"n"o"p"|"�"�"�"�"�"�"�"�"�"�"�"�"�"�"�"�########�#�#�#�#�#�#�#�#�#�#�#�#�#�#�#�#�#�#�#�#�#�#�#�#�#�#�#�$n$�$�$�$�$�%%%&%/%8%B%J%T%`%h%p%�&$�(;(c(�(�(��5���� 	    $ ' + , - . / 0 1 2 3 4 5 6 7 8 9 : ;F�"!!�!�!�(� %)*+,-3�������������������������������������"$%&'()*���������������������{���06gmHKa����������� = > ? @ A B C D E F G I t ~ � � � � � � � � � � � � � � � � � � � � � � � � � � �!!!Y'y(�(�(�e'w(f��(�'~"(�!�!�'*$�%S(j(��'�(d�'n'p(�%6�(�(�u'+$�(l'%4''(;%%9$�'-(g%U(�(�'�$�$�%V'#!�(�'x(�&�������(�'�'$(\(b(�'�!�'j!�(�!�'O(a"$(w����������  %r"�"�"N"E"="5"4"3"0"/"-",%{%�%L(�!��%�%[''''' '"''''"'#�$��"G� * G""%�(A$#�#�(�%W �#��$%Y"%Q$�"��#��#�#�$$A$!�#�#�#��%�$$	�#�"D$"#��(�$�(D("(��"g$$(2#�#�%Z#�(G#�$O#��#�"�$
�#�#�$�#"�"�"w"�(F(M(C$Y"�$I(5(<"�%m(H$N$R"�$
(B(J��(7$V$�(0��$"�S(L�% $L"�"�$+�+�+�+�+�+�+�+�+��+�+�'�+�+�+�+�+�+�+�+�+�+�+�7+�%�+�+�+�+�+�+�'�+�+�+�G+�+�+�+�*�*�*�*�*�*�*�*�*�*�*�*�*�*�*�*�*�*�*�*�*�*�*�*�*�*�*�*�*�*�*�*�*�*�*�*�*�*�*�*�*�*�*�*�*�*�*�*�*�*�*�*�*�*�*�*�*�*�*�*�*�*�*�*�*�*�*�*�*�*�*�*�*�*�*�*�*�*�*�*�*�*�*�*�*�*�*�*�*�*�*�*�*�*�*�*�*�*�*�*�*�*�*�*�*�*�*�*�*�*�*�*�*�*�*�*�*�*�*�*�*�++++++++++	+
+++
+++++++++++++++++++ +!+"+#+$+%+&+'+(+)+*+++,+-+.+/+0+1+2+3+4+5+6+7+8+9+:+;+<+=+>+?+@+A+B+C+D+E+F+G+H+I+J+K+L+M+N+O+P+Q+R+S+T+U+V+W+X+Y+Z+[+\+]+^+_+`+a+b+c+d+e+f+g+h+i+j+k+l+m+n+o+p+q+r+s+t+u+v+w+x+y+z+{+|+}+~++�+�+�+�+�+�+�+�+�+�+�+�+�+�+�+�+�+�+�+�+�+�+�+�+�+�+�+�+�+�+�+�+�+�+�+�*�*��*�*�*�*�%�*�'�**}*~*|�*y*{*z*x*t*u*w*s*v*r'�*p*o�*q*k*l*i*m*n*j*e*f*h*d*g%��*`*a*c*_'�*b*^*[*\*Y*]*Z*U*V*X*TV*W)7)8)9):);)<)=)>)?)@)A)B)C)D)E)F)G)H)I)J)K)L)M)N)O)P)Q)R)S)T)UnNy3pCm7E1Ucd0EFlTYtYPp8*4UDvWekd01k9E-c48RL08bAzVuOocBoUVbvfqusx12IHO3oS-DYxn94QzLvwwxKu1ZKPlEpSo0X2sI7nEbqF6WWAATn38aAY5SOoTpcwg0RE-RKxpE7sLGKuFQ2wQPnWepJYE8aA1W3ISq8fR9uHyd57PnemN2RN1GL0vRqw2VxSDuN9wMJ8nwMmr2u_Q1YzjpZIuEF3zY1fKE-DQDeadz7Jh66XNwpE_2d4ZodmSbHgULsETj18iBj7fJyl38mPmQY0pC1FCcPAi-geowORXjAV3F4LDV_mnVCEvccQflMz49bjl3HmMuv-BadTS7rHK1qHetoQk1vBRlLtG4phTVnNanbYd5oNNuw12kpcDIYQT8IfcTshv8Jh1LNG05FUvVZ2Tf4PjixgyDh8_n27Y0oD4XkoOUEYChk9A0PLtmNOEveY_JHbcvbTiKQfaz-VumFPUpkNNFGYXMGFy66EmG5zIyf26TCWmLZ82QJz2Qxb_H1wNZAbBN5Ku1yd5_xRo_7aYYBGK2RZAf8lZ0KPvzImJf-RsgZ5-bJTo02TPGuidfVXlJW5g9Fsun7lWdZu0BJsxQKeL2IAuEJBeLqDbubbVPOH9VOg_pCZRJIgnydFIZQmv0E2F6cVRp70sTf69DXii4SPF1qto_Nuw3ojojZhF02TOKGiRptDIj0UYvXopWt-w3lDf7MVjaLQjiVdRO9TNbs_4PzgD4grs7eOB1VpFQfAntMcCgiUB35IphO18rfjTdTl69iw3QHbZxQ5e6AppbOu8Kvfa1GtbzH61ujUM7N5PLxhoB69_cTb7fcr-cJJumteZeEQz8Z6nBtqa5_SvP9Yn9Y1FvqgzvIKMXVx_Uij9D0ixpWEv1qKw6JrSMH4F2jqUL-oAXYl6tVw5rNoTfJtKQYzRHK6KhPbtu2vli3ilBZTyN2owpkelFw-Ke0zcKdGKCiEcrcTyFRUlzHI-xkrQ7TfxWMBW7UM5PTQVqtbd-m1EQgX5yXb-rKeoGpTDN1w7plOs1kV5NGffceMc6C6tYu16qwNctmTG0irLYmjAfvKm2upihKkXtN_DaoXz0IbmhfyhjHm2PQxICrjC3uZUTCODJ4oKVntS1ja-nSDVqL9wQ9-anoBO2o25omYn6c0dIaOUcRueWoxqMzB-2OUj36y_FUbAyjSYxTmYFJFY6LStG5jQZ_7FNX1gcQXrLqH2-Ii9xzm177yAWyiEI5XQnrWc5l_U6QXbkPTXN0vqFMusDSSt66dMUYSyy8Liq8UgYHW9UgSPLoO5LN2OR1SzrBZKH4ZOdTjtCY2-5qvWFc2v3IwyNpsm58thEKBuDbzBIlCGrGMvV4McR9QXOHCIzIhiKy3kksG2jruo1qWnX242W25buOIKN9o5bJCrgXaxbFr_9SB4EYYEnBlVzf-lhln29Ckc4wKI09mHATfqCVdpmwxnZM200PAZXkKjWQooeLpDgsjZOEGeOLAmJDjzIHF41A0mA-gKA9Jepmnry3ghe4y5XUzLSppvhTxOwD6WyizKgWSnfWVTAanu_EinLkKdExoVnIgIJY8H1qxPtTHwvAwHxpXIak6ib_h7irryk06SGUj2BZ-fmwVK2TWz7koNG1_P7xY53Yu-2SHvjJ24jkYwZu9FPpE-OfjN9GiXFcQENJbVIEUSrU1udOmWmgYmzVdzHNOmSQI08Em3Tv1X6LNTU0WUif0P5xGKJ26lWT66WNXWm4nRD5IeoZmjTbel3PDa8H9cpQGRuNeav73AeSsjN7JyE5eCovpva8F9q0PK3T4KJDMXuKgr1W4TIREKn9yHWIWQqFVdaIH3oQl1BDGKkAecaFkxCiRYgb_SQM0sbCKv_Y3rXxNzhEIMp-P1B4wS8FBMVwWPpqMdSQMo-SKHlKzF0mq8bHwBUQnmE5pzG9A7D4Es2mxGfSMtXIMjBXTIeXdGQCxBpI-EQA5iD201xODaffGAuB6rRbx99y1jcnUSzsj0Fl57rulSXU8qiWuri_Cimvm5-OzJ50qpD-Gw12Vopld3iBnDA8lqBJ5_EG0qpW_lGX91L0S-Ah95Mxfu_eDIof3zuPbvCmSJTm5RkJwup3VWAeMEHTCMiRdgNLvCZ4qpUde9mEJWbT3GbHQbZU63HpBUh99IMCJLwrbyK_XRCSHODCjjIvoID-gATZeTDIgiTcIE4hgdYfhSnvs7TkX-j2A5O90zULSrFJX277nif0MSfPs3xYwvx-TviBptRV4ymejS8zRMGLK1-i0TwvXIbVdYQ4mTXIemjYkpN0neAJ-_OD0SDHGZ9DV-ElRng4zLhVrakss5I6jmu_yM9YSQTIikHABaMmsfw7nrKkjieVSIL02ILbhY6xZgmU6_ECLHUwU9PKtMOZJCM2q962cBpYhoLhMoLBz0ERS1WjaRNl4A5DJ32yUFriTj7csxIIzDK90-8wqbsiPnKtOZfAV81QzJAyALjiXEaOKwdX6IbBnCixk25J5cx3r_yTl2Er5zEp-aOqDmCIOHgceu-q3sT4TuaWD0xjiROR2Wf6uWL_7cbEj47ysX8EEi94MSRZpi1hc-mG7I5E-IF2js16PAHxvZehIViNAmJKrCQa0bCD_Fyeel7I6GZzlzjxmLYePWYr-GneICuEYL5XLuMfhcsCEA1vvtecmSHtqWvRaANAWJ0Z_cfSL-FWk885J_h4vHapIllAZv_-wxFJHT1774TOni5gxjksMA7d_0jQsgNO2R_fRDn-OrRxNnQnDViuBR11a3NSvFSr6VAHaHbo4CtUcZUp9M1-bdVNvzyUgO0yMUnD9McfFZd8m1QvL6u4UkuBmflv6WZ1XLAyOwfENqQc13HugTNQFNvW_dUJv2YVrHMvzue_kwa2KVb1PatBBgTy6O5YdOJpsTzpyOC-OneXSP6GQcH4PfJooaVNOLiigqYTf8G1K8qZHNuaOIhmHBjaTZEHgBL72yeKrmRAq3VX2oiMNsAyJb7kJqLH7YLLPmCd2ujaptsStAffqaZxA3YN0mWDmj8p4VypVdsZlYpidKn-nmkj0rA1k8odOXGzax7waa9yvhNqMB8t9sYDv-gf1FtNfjvtgPbiEQq_jtJGG0b1NiIn5U6hP5n1IE7In1tWWF5sUlMf2AL71_w5G0jyixbrQiP6t2AF_IGbb3EkDvpaLz4Io91x1k6dMpNucVhlhukKWRmHlo8srPlM0bJSSC0FyCsN9ax-pu-kXgIfaVKq6Ar2A8hfyBg3ZK1B_10li5lEXDKwo_nKJVL5gcu4bZYUQjvBqQ_rjGBli44kYNyPTJHKDHU1rrgYEjuKb9L-ifkq-AT5n9CJUeLVBh1xNGDoXx5Ok971cZWRV_kX9zK7CwUyO5brG0X7x06h2fFSDm7697qsRpDE-7DiuXGBCnU8alC9sEYem0LIwX89r3R6Wrs0pznKhJ3V516E93D1qr8HzQDB0GT6g8-jPbSGAAxuGnJ8qqWZ5eYFThc5Ciy_NpMFuFU5ixWsru6mTuIriaABYw1B-Tq9BeeAD83vSXbhY03Hrk3MmI4fig3VCyIVNyqClhg2z5EbDnPr0ct6zaES1-kIK9Ynj-oFjXm8CoSkEKuGnvzoV3ae488Ap_trp_Rq9Vydebzs7UF4REm8-UhSFXNceM1IC0-wbQr5ri4NZor2XqdDqYZEvvKefylQyyAdSNM9dmaE9j5fP-d7yrgMPFPv8u3EC764A6mCGqjd3LHNAKnBPvs8WapM6GxXgMoyCcXYQaxce6OU8xy7qO9Cjhvgng-UVDaPkyNMZYEsI58q4GCdZBPfjR5q6U93wS8W3GNlyDn12yU0LfXAoHvQR4xYzzcr8OAfaBJVHk2512S9knEi1iNPE3Q9w5QtPseNvr-lT3VZi9WGKdLXYnNzsRhQoUa0yL5EO05WBcLkZxwgILy1Y0nb8arklUQpSX2Bj2dw3KJUhTFSwf4STEUdmu0Xz3lcSnphcIzHp7Xdt3TrDZm9UeTc2OS6KnTAq1HI8AUB9kIF6dVVO1aQuilF_UzTOhrAv7yMompilCjn5A60NTawpdQRELZ2RP2sx0bsUeKCfJ6p4t9ksUZrWlPbGQgT7lW8A+WIFjOQgq6OEmV-MK7zRlnLtYM_sOWZIBeQjEyRc1IRCkyVoIGB_opNGwPqOj9V0fXN4RPP47pB0E5XoF1pPd9Y3YUAT8ohFtM1NgKwWJTRrLF-IlNkER5xMskZNEI1-z7Rc7eFoujS0AOdbbgfTEq3nNHPMfpBmvE3WF_BCbWP9X2xG5dKBW7rzCWYPAjMaVVhDGnz8ZNOWEV1V3Dqka-pf2Hl_Wu9-tUjWwYmoVaL3SQVzOB8rOrYE7w0Y68J8XNFVdQIbr7DBTle-xZ4cecq2DBFv3JXrTnr-XTgTwuxSxL0ui8yKa73-lcrEJraxCThfc49isIMFnpHHtcRegC1L4Q2_-tEcM-4Oo5IbU4yz0RhpkgwWFTYCAU7uStFcUiaEAZ-ChOdZ6HQwhoXzzH7nWSMdg6mfYwtnsNftwRiwWujry0GCGs2RPn1CCplVNkVMHTpOMqGZ3mday-TdkXMWg_L95rjAf9cB8ro9c5OxpfsKWWdrTe_wX_egTMoMWhVZoJpWwztrGa6Kjn-tCPlp8LhTObcJLe_K6ZYh_vBN6ocpMIRzLD8Hke5eQWbtjiH28qFl-2Qxuo0-dpooG42NlrrJoGZID8Vopg_PeWGi0yZx2scRXKLXy4eCiCXYkO99p3Y191Vw_y0VvcZ7sCLw72rQfz4onVPjoPTse2nQgD0TF4GfpwX1c5T8R_t4KgLQJNjE4CgYDa7I0qNMbEp87gJh6SqzilWVMt1F0YG6lP3C1OQl2CdCnrJBrdX8mXbPF5dGbBMBRv3YKW5GRbhXnm9pFp4D5FbFPlKb0rc_XGDFHpfcDaJBMIUZW8rJnT1_TH0lgcawmnw883C4pjPdU_GfQk59sz5CfBKZv93whD56zleYjGtKbSfDg-SgK0kxkDUaL4Vh2uCkQJfCsG1q7C_WXislzviivPmnEtxtl8LHjMl3e16phzvPu2dG4ZTJCKDYm3StnwXKIb7SdTSnlfIC4e1f6rgaZk06gtGcD9EF_hUf8x8ZXXEdmyvSb5bUNMbqKMjdxpkoqXcG1KPHurzgjKtD1aH1sIDW8ZH_fO3mws09rQtC0G2S8BQggZIxveXP2lyR0r0oV6yjLjMh2Z0UKzKAhm0TZfA_ihvE-1iQs-DeyZyUHXQfv2sifN6rPa6hCuOTgeNVUL0t_cXB8dyLbPYsxUFVLjwq8nRtVV6kIvKXRcgI8KijsoJTvmtq_4u0b4PHNYXZdLySK0drbeHoRjDLN1eQALYVol7Pkn5yYs6mscR-8bDQCQ1KM7-O76FxtGV8XNf15vU6vbXO06WIFX6rS5qICavP3umjJG1G-fAxj-RBMrysT6mTnfkaj2eABNKpkg3tfUUeJLSH_lfOmhXAu8bmxG9QvxkFLSBEqqTWGhWsm86qnVeg0A707uQBni1UxNlA3_PuMbZa8JFh7QXlH-pSfCExqsxTceTeUTMyc-5PsdEp21fhhZ6A-Rq25JrBpyP7clRdEMazpshKL_mZX-bffJOpTyx1OO0xFEXCLUjNKJP9Zqd0F-t_V_yDVaj1NHP1x-QEeiyN1fZ1Gmw6ywGNmj_mYf8s3y2BdxfmODADkDaRuAmQAGKxQyMjae3xv1ReHFOowba6JNgxXKi99uHhAh4VGcU2XOwUnuu69kyqVEH3GmKa884DEzjmuhtplgfWs4L2j8kSZ4KZHFVA8jyJO4UEBIhuT7P7hUuKpoEU9LK8u6GlmAfikvojHuMzTazT14x8rHH-VC8iyk8JmamVtds0sEI1qmDHRP4-gyUU0itVtDACOzvDxaQn9FEoCeaqjvnXG7mw5HhHUpa2jm4J4OKxbl8GINsWB5Lb0uLx-l7y_KR_zG38hut1y5tskiLKmlXbStQ0Kz11WLsFRhdqShWclV1xsCPg5Zdhbnng0_hhde-qmZtV2lVUA9wSBbxNHgF_1GBEL-ozE97K47CihJ8E2vMniYI-gEfWXx_EnKHbEnQRn6c6CiwT6tkzhPxQ2slmO6y9gnfyoDQ0lhH-ZWRtQx5FN6tdA9dIiV4I5xDpQMGUxKJbyTYQp4i8pnKUsbiJfwCwyTAVCKnsB8ikAYzjAU0xr48_B8oQR816Jnxlqys61ogSml73W-K6cJgTXp0bZvAy59eHmabHDqXOKHJire-82c53-FmXoEeTydpJq4eX1SS-O0dYo_7h0fhzuBJQm2W6Wko0MZCUcreNRszA4aZCYLPAuZdeoCpZui6nkj0XxAqtM6CBLnptCO2trwCUXiYFYFz1ElNR_IUEW5gCwBE5aU58n12Uut2JpRSbFftQruG7GVPtcLyZ4PLG74eTOp_RreN6pAC36zPcGzQoUaIPG7Ckak9mmRPt6ZikYmagGVqKDqEcTtQaol0le0ZIem2iD7IAM3CQlK55lbkZjq5P-wI5xrFzB7NciNrM_SW4iyL_sDwwkf7z7duLmKhz4B50oGMFBago8nf6fw7JDcjWJYNSKxIYfZsZ_yqjxcHX4jP5VGFTc2ZWI-qvbUqpzIr1DWvXJm5srYWNiZvQtY_8LL7cZB2RXWeuEcOX8ONhyQSx4FHvizKYjI5o_NeUeryTNBoyFBNU2Bk6B3HGuvapVkv8ffTwmmvsSXi2m4VWqNtblpab0DuqXV3QBa76JvF6aeZRBB_NcNrNG7jOpVpS70v4-lo41sfJheOJ7J595-ABw9mvWPaAVafSjkQgfsI4vSILEpIai5-JbnY04Vn6jxpFXFNSOTeRDcwKmYthfkNYGgtY7GG4FsMY-wKE81JrzwFRunx7KkV6olHALHmAYPX9cPiUYB73jqd3ZG-u445pp5Ax6RI5yJwB6AilnMxMbR6QGvN89jRIT0f-QQwBGKf2sPTMWfXVRIxbnoZYQvSyyINyBKSp9sYzlGmUyJPL5nBWwBwz-HIbLuOf5TDupj8A0FpO8veOfi03mRn3-LgzoiulkWjyqrcNT5P4TFH1rp2DTgKqfCBOXWrpRr1OqEwqpkEzKIrLnuUR7fvMnvpkEPqVLTEqeJrUOk2kCrc5X_nLo8BlxQfzrk56d6OWHFW1Nnm_WyN-p_vdpL7bZyaMgD8_A9UiUAnglaXi0WyvhneV3efjqZ1UYD2H-4z-7Umu2JA6aiOUNwcU6qSzC2RmhHeGrFRBKv3d1HX_0HLwbkcYrMdHGEUHC99Ps65mV8ohqzN084OJaA_9H1J7jvsEsCVOqQgH48Fhi-Cy0F-EmpTot8TFFNOed5RhJdwk6VNhkX1wcYbgG5DpBLPFRNjDRFJ-uB2TaNqwI1h4nQAOmcIIFq_nOcud65B2GgLkAQRPOnxQyTRsItPODfN9I-0X1k85eoj1VT5JV6Fq8DtDiCYwc2v5lNmeSOD8YHLTUUqFro5ePAHQ-4WzSTjdxz_uNUyxz-hDIA9pHgZSMYT-KiaPZS9Vib2dqly1D4ZYhKjlIItQs_Xlo73iPaePoni9rpgQzXoEwyaAju5Qg5CWrRlBWZEQ54O_p4i-R5wwSMQwJXxUtDsf0lKZPOFJa9HqcGmzKmxjhX_9F2w6GyFWCW_ABTa1th2zxoTN4l6CTIB6PumYGyY9d6jIBcdZNmotIjvgTpysyh1tqa35KaLJuR0r5dmaZrqJIOP2MuNcTANph62Z9ySvfsRYIk0YZBaZGyneby-kKmn2GBurY2xVzJMAqIhZJFEVuTV2SIr2ocG1WyI9Rb4GAW6Sq4hpTnNrP8poZk5mCzQPj-0VmcqgtWniWhfkqhXX3wlXkhI1bJFQVp8Rzs7Jim74Q798i2FnoUcJQ9zyEV9Qk95TEQVeRVP7CHqSHksa2XdWt1ybKJCHd3NVey_HQW5-FleZLQKdx7A0_aJHGc90TI3FbOzpVcsN_EbmKLfg5b0l9c67cy_uaarjFp2cjH_mUjDz7TWtcex6NAg3Ka_0tAhn9bw-ueEOUyF5CElU0YURCGI3VtZ4Rer3xlLN-Wc97strsmpo9JaNSEZ1tczibTZG_lL7CHQnbfc0sG651KPX1EvG391P2HvIv-_qHBAajIcmneewMLR6BFGTNuxXsqYHrf57tN43BREAOMaHST2mSei79rKbP5v9xkB_H7Etg,lQqrZc8-OUQfx5l8nwuRZ2e98qqtgdXFCUGldKvgYX-zgihVbxWbrHanJJRFS1Rz_7y6HPnaoGeZJElJ_MlVL6KlurWyYvSdTzVV8ICyzXnRCJAj0fYrb-NNkNC9jnb5x4uV5pwXRIX_1vSt6D5ZA7O8UQzSunp42fhK4wVL-NbS-AA0P-wcYcD6UGDqdo4rGzoakKgg_JHyzCNTx34p2iM6ZAd7tmEcPjHg1u_SfGZNGL4pwJjA5MvkJVAANkH2XIC0lalgT7Y9BeE8PNw3q2eciTwp2vjG7aISAsg4D1JPqYfc_o0PCQVvyZmlDc9i7bVs-cxQSgLkbuZBZfepA9BMBu6bFWBOr4TsxEr4HgXTcmV6itABsa4xW544KCijBsXr122dw8QvNX69ZRlnDxe3OxWAxBvgCW_-WccZ3Hni7gVDXMJ6BDJIkWKSqhjPQDCEYZtzDqXJsU3spoXBmKUHmZI59H9MJkay9L7PqCEA3wGV1tBOeqsPK0bnO7cg0NMnlVWMw7mM_TiXXVQoGiY33616fBjPUhU6OhFeQ0272tlP4yXF3X2lWeqzvgpb_LTrMw_-E9SJQrPgxvqxPYQny6fQ-pI4Nu16GF9vwim_NDVcxveVEI6GdPn0Nh7_zsxE823avTInRzjduL3JlB5TYnzKW-c9TwqvyCxlP8WBmS6R9veTdf2k6hDk9okb7ie_GtVN5dUyoDlvUmdEneHd9sifR-dzE2E8-me9OUWdyy81-TIGMKI5vJN7Lf5lvdrnCkwnwR6ZKhVIAg6aNbntX2Jl-aShE3ykmlHOIpi9MMhlYadhIJrrpXZ5npMjOhvalgXBSOHm1UUpXuzPHck_2wbhKUvCU4GyWdwY9j8z2yAwuyLGM4g-QoZMnPAv2N2rLayOXF-ejb_I631rhEGiHbS8dRSOu4V70x4vcYKSq8nuH4yePFORtoveJ-bx3r9BAE42iu_S9XiznyV1rWirqQIYfAQhOfIXO-r9BP-bt1R3TjR36WD8PWKiLydhbYX9SWeewJAFmSZyYCjZ7aFp3UnMD87hcxartIt6RrzxiuFo3mS8xLm-wwEqs5ht9V-0hm0w8B-lCB7_BDE3GkVLmhZX1wYFxTM5PA7ORCl76F4IMFeeRNRAKrQ1__tjJbflGc_oyQq2jzPvFWqQlpmohChv1liw9yoR7ev9XLQEISY1tgDreMy-aq72MS8jpj-sjPXgibinBBN2un8wrDwpSSwoEJm6fZHz5e0_T3ZIjOH1EseFzcEoR6SboxAF_UH6-VMFR26F2EkJZ94K3Qu8FR9_AvxSTGNTFKJ3KFuVgnpZtAKaIZqD-sq6YqozLvwneTXthlikOGfF91b2NXTEDRwWaOpav0hnMi2eM_4RHGpFGGse-0kPzI_MtdojcWwKkgH2UswBiboA28r3bz3wYZfu_fi-FbSiYXR0rURJAiJyA4NBKi15q08mdBPMn8wafeJvErjylGCIb0sf1qeK3VHUzLV8dsA0wnW2uAVHXrDio4v8-H-gYQz5zQmDccvv9t6qKyq2P3b9-inMZo7LDZDNH54hL1xxHfmoiB5kDM1bc8ojU_bzdiXR_sYgZEX1GtNKjqfqDg2S8CcuGO0tPfwdnVMLNPVZEEcbymn23VXcwlUL-g9SCHUYd1DXwbvyVBxFF_Z9xAPnSmUImB9fpku45ZOIwgeUryS4Ss79N6VtVnLEDWWGSBhy--yMGpjrPJmF_SVKjLROTW-FPUesYcWmKhygvitHca4ufc4vZ9Jnwg863gP_acd41a4cwokGUs2ig6kglosUQrgGwmqP0jHf8piSdNCX1b_5rMNFSgLIgZGD2hhEsFW-EviSmTWyTC-v1d11I2BGXunA16Cz4od0DabSmD7xZFkmA8rPGB5q7f-vPUKjxfY8UjxXnmBGRZrP32Ydn1YaMYi5X3lSWrUScEqAV1k83o8mWZbeg6OqnLR0tjchAxmf-gXuEMeCfQv94SSghp6i8nKO8P0l6hYpAFbUOGY5GCnY8uRKzws-kJwaeReonP8nqJaVaA7h6DDyhRU_XGK7Qa_uV-Z_pcZxeqlNkYl0JISypAJlGOlhEmW8b-UzcHfD2DXtE2o07QYJzoMd8U8d9IDoi-dc47l7Ws_f281xeheivJMJDD8Ijb_Qd2lzjZJKfrLzuPDojfXp4orMMzlNOWw5upPlbni931sHsLYduivH_EFYGhfoh97w-sA41oJm2ewKQM416mowOv11tE60qldba1xCprM54KM_3QnIKjArRzBpSpS2uP6R_DJXXadvDQANOy-MYQ4p375S0y7t3jopAnQ8v_gHLVHqFl9KIh4nBrHzzMJKklJxva5EqcOxVu2b-v_hAE_pNnC5ihmdZm_gENTbmfm7iAwngl49fG7BReukfvmfwr_9kRKSLu9rkdQthW7AXeSwNRjAcRvlAJZoAQaTsJc4ukeEuGfKAyl0h9uedPmHfOehwRwAj9pTFH_UFLrYaZmeKQz_U0MHKwfUhQb1sR9pqb1TA6LzB2LX6ilsk2lidzOOz_W8N4of8egOkD1CbfiktTEoNS236fkWqNFQtEH1XoImoTFo1bWN2VTnKvQI9qY4FkkW9vkayEc-m1bo2QmyPAiolHc8PgdANAyj7y-CqztQbyv098g0kIIEnapxvi5YbcvPdC600_jmJoN1HLllDqceJvmUezcXjepwt84leU1Cm0sPEu4Bp2qVY7vzrhP3x6fd0M4ISabzs5pZdqBoZOLk7UjjEmBqq6porBRo3AX1huILUQwRxms7NyZWg4uuSSQxdMkqCH1vwvfPXgYTbQiimi5bpxoNr-z2V7VdXvSH1YvYAYk9HEAWa4ApVJwPK9IKhr4oPbK3tFDoErvmhzJzYqwsJUFRj-EiXr7OjGc2P3gaSKPpJDjKdh7p7augZSJYR5JFvtc57IewWk3NKDd-TU8EMN67Ctx2C0UQrA37QKkfjrOaBvvQ83Vg_2T2hIugOFYV67S1sLOTyPepRbqUIGdA4KziK9uNgAnKSDZlU9H_qslg8HtuiST7cjsHlUdkYJSZAVpV94deTbh30_cBaXJ1t-Ht9yWoTKFd1eazM_ugaWojGqYijcU7FNQXt-btt_FzvWTwb7gz23D2eeMimbB7l8Ei-if5fhQ2z-pkS6a43xZra7dBSC9IKSKIhBYxKKdNZwNtJDKl_WvnDqemJezUOYhqBNs2H5CWr5Gnc69cJlihnNpOrpjKZV2yz5L_ObDcsBgkR9nghKMWi6pGYz8kOS1875hoylAA_7WJeYRol7fdxzPsro3GjME4IN_RKvw7o2Hx7VnOcnT9M3XbZalZRRZSFHr4Ews6dd3C-Mwvp4eCLjIemgf11Z8LacziEcwkeMahpAXj2_8iMFk98i7XZgpTJfn5VWxEYBxREKoKANv5Q2h4XytWvdbL_XBzffENzhSd01QDwfsEzDSXdaLqhbKVH6dwawj4KzQbdYRMmQRBq1eitmD7IPD6Nk-FBRpqPdHXOZZqk5w_56YbBlBVbfK2sxgFRB71EVkaocShwKuGLyPBkvdTwDSfeU2iWWXeUGCifIapSuNvFu1i8Ww1TfMhB2vr9p-_zoDQwHHkmqHQnP76ZDG4BQ6XdZXThO4_98sATmhMOEg_ImYbz_XkMsDLlcLrZUA1DfTkSOP_mu8PONRBe3FFgIBfpiIiS7fU8XEcl9UNJGuDsheCVT15LOKiGhKRqzeLaljnDPC8SuEwWbRJYHf9lB2abZYF-VY_9K0FQC7dDidokNFsF_qaNvKlYlWjkATV30UEyU8xWA4itlk2dKXmG50rGt41CKpe0EMKzWnq3CrGVWo2IDgMK2KuQjUuq5d8F33luB_-ksyrQc22XI2dpWOn6VpXWh87E176FMBx31xPk12zBU-gHz1Wg_5v-Nk3Z_gz3ObS_AGr0KTkk-teIiQmKKAIR-ohMCDBhY48MkHJLPjp36MH6fzaCOuSuKP7AmoNmrzG3ojb03RgqaxuX35EO7vDcqWZ0YF5uZBJfNcA8z_OYVswhXQjhOUk6PtT_srvSXskKtLYoEkdA-488WuQstcep6z_-ded)
        day_str = str(row.get(\"da They are the highest-leverage changes."}],"phase":"final_answer"},{"type":"message","role":"user","content":[{"type":"input_text","text":"THat was very good! Let's implement fixes 1 through 5. Then, we can try fix 3. Fix 4, however, is still a work in.  progress, let's leave it for the future rn. We can begin planning these changes!
                    \"excel_day_padding\": row.get(\"excel_day_padding\", \"R  <urlset xmlns=\"http://www.sitemaps.org/schemas/sitemap/0.9\">
      <url>
        <loc>https://noticias.r7.com/rio-de-janeiro/evento-no-rio-28012025</loc>
        <lastmod>2025-01-28T14:30:00Z</lastmod>
      </url>
    </urlset>
    \"\"\"
    def fake_fetch_url(url: str, timeout: int = 10):
        calls.append(url)
        mapping = {
            \"https://noticias.r7.com/arc/outboundfeeds/sitemap-index-byday/\": day_index_xml,
            \"https://noticias.r7.com/arc/outboundfeeds/sitemap/2025-01-27/\": day_child_xml,
            \"https://noticias.r7.com/arc/outboundfeeds/sitemap-news-index/\": news_index_xml,
            \"https://noticias.r7.com/arc/outboundfeeds/sitemap-news/?outputType=xml\": news_child_xml,
            \"https://noticias.r7.com/arc/outboundfeeds/sitemap-section-index/\": section_index_xml,
            \"https://noticias.r7.com/arc/outboundfeeds/sitemap/category/rio-de-janeiro/?outputType=xml\": section_child_xml,
        if url not in mapping:
            raise AssertionError(f\"unexpected url {url}\")
        return url, mapping[url]
    monkeypatch.setattr(collectors, \"fetch_url\", fake_fetch_url)
    items = collectors.collect_r7_site(
        date_from=\"2025-01-27\",
        date_to=\"2025-01-28\",
        limit_total=10,
        request_timeout=3,
    assert \"https://noticias.r7.com/arc/outboundfeeds/sitemap/category/esportes/?outputType=xml\" not in calls
    assert [item.url for item in items] == [
        \"https://noticias.r7.com/cidades/e-preciso-denunciar-apologias-ao-nazismo-27012025\",
        \"https://noticias.r7.com/jr-na-tv/video/governo-estuda-forma-de-trazer-brasileiros-14062025\",
        \"https://noticias.r7.com/rio-de-janeiro/evento-no-rio-28012025\",
    ]
    assert all(item.source_type == \"r7_site\" for item in items)
    assert all(item.metadata[\"exact_body_only\"] for item in items)
    parser.add_argument(\"--excel-day-padding\
LT�T)���}	�	s	H	���qoD���mB���k@���i>�Fe��g<�������!
��:
Jc�
8	�
	��NR'
�
�
�
{
P
%���y
�
�
u#���wL��*U019cafa6-f9bb-7f02-b05f-7d5fc60ed10d*+�*U019cafa6-f9bb-7f02-b05f-7d5fc60ed10d*+�*U019cafa6-f9bb-7f02-b05f-7d5fc60ed10d*+�*U019cafa6-f9bb-7f02-b05f-7d5fc60ed10d*+�*U019cafa6-f9bb-7f02-b05f-7d5fc60ed10d*+�*U019cafa6-f9bb-7f02-b05f-7d5fc60ed10d*+�*U019cafa6-f9bb-7f02-b05f-7d5fc60ed10d*+�*U019cafa6-f9bb-7f02-b05f-7d5fc60ed10d*+�*U019cafa6-f9bb-7f02-b05f-7d5fc60ed10d*+�*U019cafa6-f9bb-7f02-b05f-7d5fc60ed10d**�*U019cafa6-f9bb-7f02-b05f-7d5fc60ed10d*+�*U019cafa6-f9bb-7f02-b05f-7d5fc60ed10d*+�*U019cafa6-f9bb-7f02-b05f-7d5fc60ed10d*+�*U019cafa6-f9bb-7f02-b05f-7d5fc60ed10d**�*U019cafa6-f9bb-7f02-b05f-7d5fc60ed10d*+�*U019cafa6-f9bb-7f02-b05f-7d5fc60ed10d**�*U019cafa6-f9bb-7f02-b05f-7d5fc60ed10d**�*U019cafa6-f9bb-7f02-b05f-7d5fc60ed10d**�*U019cafa6-f9bb-7f02-b05f-7d5fc60ed10d**�*U019cafa6-f9bb-7f02-b05f-7d5fc60ed10d**�*U019cafa6-f9bb-7f02-b05f-7d5fc60ed10d**�*U019cafa6-f9bb-7f02-b05f-7d5fc60ed10d**�*U019cafa6-f9bb-7f02-b05f-7d5fc60ed10d**�*U019cafa6-f9bb-7f02-b05f-7d5fc60ed10d**�*U019cafa6-f9bb-7f02-b05f-7d5fc60ed10d**�*U019cafa6-f9bb-7f02-b05f-7d5fc60ed10d*+�*U019cafa6-f9bb-7f02-b05f-7d5fc60ed10d**�*U019cafa6-f9bb-7f02-b05f-7d5fc60ed10d**�*U019cafa6-f9bb-7f02-b05f-7d5fc60ed10d**�*U019cafa6-f9bb-7f02-b05f-7d5fc60ed10d**�*U019cafa6-f9bb-7f02-b05f-7d5fc60ed10d**�*U019cafa6-f9bb-7f02-b05f-7d5fc60ed10d**�*U019cafa6-f9bb-7f02-b05f-7d5fc60ed10d**�*U019cafa6-f9bb-7f02-b05f-7d5fc60ed10d**�*U019cafa6-f9bb-7f02-b05f-7d5fc60ed10d**�*U019cafa6-f9bb-7f02-b05f-7d5fc60ed10d**�*U019cafa6-f9bb-7f02-b05f-7d5fc60ed10d**�*U019cafa6-f9bb-7f02-b05f-7d5fc60ed10d**�*U019cafa6-f9bb-7f02-b05f-7d5fc60ed10d**�*U019cafa6-f9bb-7f02-b05f-7d5fc60ed10d**�*U019cafa6-f9bb-7f02-b05f-7d5fc60ed10d*+�*U019cafa6-f9bb-7f02-b05f-7d5fc60ed10d*+�*U019cafa6-f9bb-7f02-b05f-7d5fc60ed10d*+�*U019cafa6-f9bb-7f02-b05f-7d5fc60ed10d**�*U019cafa6-f9bb-7f02-b05f-7d5fc60ed10d**�*U019cafa6-f9bb-7f02-b05f-7d5fc60ed10d**�*U019cafa6-f9bb-7f02-b05f-7d5fc60ed10d*
=*U019cafa6-f9bb-7f02-b05f-7d5fc60ed10d*
2*U019cafa6-f9bb-7f02-b05f-7d5fc60ed10d*	u*U019cafa6-f9bb-7f02-b05f-7d5fc60ed10d*	t*U019cafa6-f9bb-7f02-b05f-7d5fc60ed10d*	m*U019cafa6-f9bb-7f02-b05f-7d5fc60ed10d*	b*U019cafa6-f9bb-7f02-b05f-7d5fc60ed10d*	a*U019cafa6-f9bb-7f02-b05f-7d5fc60ed10d*+�*U019cafa6-f9bb-7f02-b05f-7d5fc60ed10d*+�*U019cafa6-f9bb-7f02-b05f-7d5fc60ed10d*+�*U019cafa6-f9bb-7f02-b05f-7d5fc60ed10d*+�*U019cafa6-f9bb-7f02-b05f-7d5fc60ed10d*-�*U019cafa6-f9bb-7f02-b05f-7d5fc60ed10d*-�*U019cafa6-f9bb-7f02-b05f-7d5fc60ed10d*+�*U019cafa6-f9bb-7f02-b05f-7d5fc60ed10d*+�*U019cafa6-f9bb-7f02-b05f-7d5fc60ed10d*+��019cafa6-f9bb-7f02-b05f-7d5fc60ed10d*-�*U019cafa6-f9bb-7f02-b05f-7d5fc60ed10d*-�*U019cafa6-f9bb-7f02-b05f-7d5fc60ed10d*-�*U019cafa6-f9bb-7f02-b05f-7d5fc60ed10d*-�*U019cafa6-f9bb-7f02-b05f-7d5fc60ed10d*-�*U019cafa6-f9bb-7f02-b05f-7d5fc60ed10d*-�*U019cafa6-f9bb-7f02-b05f-7d5fc60ed10d*+�*U019cafa6-f9bb-7f02-b05f-7d5fc60ed10d*+�*U019cafa6-f9bb-7f02-b05f-7d5fc60ed10d*+�*U019cafa6-f9bb-7f02-b05f-7d5fc60ed10d*+�*U019cafa6-f9bb-7f02-b05f-7d5fc60ed10d*+�*U019cafa6-f9bb-7f02-b05f-7d5fc60ed10d*+�*U019cafa6-f9bb-7f02-b05f-7d5fc60ed10d*+�*U019cafa6-f9bb-7f02-b05f-7d5fc60ed10d*+�*U019cafa6-f9bb-7f02-b05f-7d5fc60ed10d*+�*U019cafa6-f9bb-7f02-b05f-7d5fc60ed10d*+�*U019cafa6-f9bb-7f02-b05f-7d5fc60ed10d*+�*U019cafa6-f9bb-7f02-b05f-7d5fc60ed10d*+�*U019cafa6-f9bb-7f02-b05f-7d5fc60ed10d*+�*U019cafa6-f9bb-7f02-b05f-7d5fc60ed10d*	`*U019cafa6-f9bb-7f02-b05f-7d5fc60ed10d*	_*U019cafa6-f9bb-7f02-b05f-7d5fc60ed10d*	^*U019cafa6-f9bb-7f02-b05f-7d5fc60ed10d*	]*U019cafa6-f9bb-7f02-b05f-7d5fc60ed10d*	\*U019cafa6-f9bb-7f02-b05f-7d5fc60ed10d*	[�019cafa6-f9bb-7f02-b05f-7d5fc60ed10d*.*U019cafa6-f9bb-7f02-b05f-7d5fc60ed10d*.*U019cafa6-f9bb-7f02-b05f-7d5fc60ed10d*.�Wzc3xs6RzjBfQhsuEbvYPEpYz_iXKU55g654v717DMZdsOQs7CLjKac-OZKAHhDXZ9oI8-SPWtgMbVEteSgw5T7G5Q8WBU4YyqqBDYywOOSmdWGUwB3pAaEyH7_i-OahjjawRybiO4m5gTkYHapDoZk6Em5eTzF5-6NAkz9OxrskhDu50nGhu6yn3flnQ_FdGofM1jOsUo51lfUp4yZFKRKJ8GDLdX8X0QPkzPe3uWzV24dRdxIRh8QS1AMIWQy7iwUIJJ9locOs3gKtRSkhb7UmJCemADGo0wDgeP56y5Z7zDks2jCLu4G69dnZL-3_QdjyGYPS0jskHPFyssn85EOvLtsYLnNs7hKbTVT7DN3iH_xTTE1UE-naIgBZfU-PKmValnz5aW4ZE5hWqdTk7KCi2Cu1XD20dI5cdLV4c3XewHp8ZxvgCwklJsqoAcwSQmvdYc3XpLby-XWDhiOm1jMdaz13KoFC4Oa5Z4GkI4la6_nihM2GZFikoLBFp6I-sKdu8hPBtVBV8MkRzygRX0ZajlKlW-WmEAiRCAYmR4vHHzDSRP-tM01Elm8bYVbEMjOVg1xXEU3wDasAJR8Kq_uKqmSJUxk55r7We3yeevVA0V6QdxgLhAj8PHIhcZVQZVZIo4trocvabxkUYdMDpCYuK3SiwkEcUyxVsO1v24Pj4DzpTDN42aPMK0uIng9phovawFa7sy6OMbdnBisy7tTZf8DcE67kFDLFt1tbmlMYuANGplxY0JpidI6VGCVg--Bo8SrxFoTeT0lVBXLhNuO8yAeVZZIZwV6mvj8QBcsJOXS-tITWf-KhbAJXDFCUUYwyoZbuTDz5RMuNAfdyq3l4YM2Xvbj-foLM6qgAnMLK2ntdRbjyOW1258VAnlO06rArXdMHwPUn0zjI1CSzNeNNXJF9PBVRQoDc6pTHXna7yF7XSgGJyS-nViKyMY32-F4UAxttguaq-4Uz_TLheDldXF0JDRqbG8AZE01B7SKFnF6Jd7VPsl3R6FNsiE31GeZNVtvd9ry1YQw7EyHUZ1rbXYoVQSvwuN8Tw-mEERYE8PX90D4rr_upzk9KQr_p8KjEcG4F26S-V9D7-dOwzXAa5cpGSEDkXxgA9ieuqZKKJ_wZcjcrhwiOZ054mHaFSnRyD-RWZAuoodX5cfpKeHjLOZvt3MGmBi9PejgvpG6TG6Fzq0oTdHh3A8aJzCi0ZgbT0AQPqoK6ZfNgczhhEGXfjr8ZAccYRByjpwpcS9-dXcgnaBviNSLDYHfcF_94K3fGj9bg175pjHJHvsrAWZj8aKcQIMVEqPzqrs_lbfoyYQwZwwzltr5NbkfqoTzdfOxes9o9t1Tvn5-eZyQcUIeSnE8RloMfmunzuKIwyD8gNB-zD8XXsghnH-yVJWOm9yyizw6WJ0-pYiywmuTVXuVIlxebA1-SiQpIJc6KvUI3NL1lg954x56f0iP579dhHyByyTss5Fr5k8a9RxDfSwWpqQGEm1PRyZ4Frzxx_Fil1Lx7U8z_b6rYoMF3mmbygKDaSWupUtpJpjyi8DvILF-TR-vX9xd9BBzLrSrtu5YWyAs="},{"type":"function_call",
    if mode == \"off\"HN:
    parser.add_argument(\"--excel-day-padding\Hi", type=int, default=0, help=\"Extra days to scan around each Excel date when --excel-days-only is enabled\")
    effective_day_limitI~ = max(1, int(source.get(\"benchmark_day_limit\") or day_limit))
    effective_day_limit @ = max(1, int(source.get(\"benchmark_day_limit\") or day_limit))
DEFAULT_END_DATE = \"2025-"�tLY0vqhY0OTDeV6XYl4mybqtW7nq8toRPhhQYP0HgVg_MeX363Dqd77DM_OfIzKM2BoKU4E6QAfbMp5yQ2mOT8CpNwZPH6LyzWs-cWcGHLMeZafQR_DlT-LU7O3cYoTRkLAYWG_3JSMDKPNTS9y3Zi_JN42Q8oFjmPwHdW8Fk1NOyDSku8YProICi-zUn9ByioYUiuJB7mw5EgdEHL7nXMHkOdSInVZoxA6XkVfzi6zd-ywk0E3R2sHdYPe5ppBE57_n3w475ytiXSumO0jKVuPQkhZ-Fg84K1OcSCnBGmLp0jMDVQUIZDmcW5SNZpgki766PwJ-TZq1HLiQH4kqFCp7UkUx3vK01ruNwHCxd4KrHrDYDSg1GSjXCY1KTu6Otvx_DCX7oe6biUnZxmULdvaRTUlplIG71PJrebrhQo-RdpmiQd4TTzxZHg9qG7pf8pssRtXq67Quuqh2sDsSFCMVLVFzSxsjh9wInY0d7TM3SGf1aUmVIJs_DoktYwyvyCAwZ-Ua1InfwVZVrGJU7AhOd-4f1RA_RJ20-R_29HcFdKVWFn-3jGkJ1I-w23MyBgiR1w8TnaJdkHm6hCeACv_LmXbzHp54Opfqh17jf-gPV9PQTnSMCg7OK44UPF5E6fgfmGw3bRBffk8qqFldoCjTPYEIplzzgGK8KT_lu7GGH9dEvZz8_2h59cgeofIjPkdeUseMDogBPqq7QG_QGEiqWYLfRVx58VoeUile-g7uiqjNP57ep83QD91oYUIVTkU0Qao1iKqurAhiu8aCdWNVvPd6RStlggAG3Eb6Wtt0ltLejX6zP-xuD5Zuo5fj6Y3aAsVkiw0EGut1wQDm7Q80NfZ2oQhAvwn1o_utsxpzYKFQ8huM87MXSW7Kjg-3VKjtrhY1OIQaRndGC09s9qM3PEzT1nmhBf_KojM5Oq4x8gQ6lNgowOQWHBXot1FSpVFm34Untrro1Lsl9OWT9d4j0aqWSFt3HlQijTDkbeqsB5uZRE2D_-bUAa1Rbxbpu0kKbzmVh5P2Iz7F_2ua4JvPqQ5KqQyw_z0jhK-95nNy3pCm7E1Ucd0EFlTYtYPp8DXPWTQ21uVS_CAjFA90RjVN_czpPn8bTIc_cNPY81ZjO8Ju7Dxkh6QjskEJnnM09X46eMhDstabFY0LfcqfniHd8eZosHaAGzsrnlVvHXxHgNGtTfavaWGl-Me4nKODJ8LCAw_pqb3JWhNaO-zqnvwygIf_MaoiQj2lsFDPP8RG4HIia5DogALP53oNXOGBTI6fsgEWt5nMX0xXvYwBVlydeTE3JaCYQdaCN_jGtec5ZEO4MKpiFlQU5YxFXzbPTvVeiF-sezZT63AnYVPmQthSs5deYjv5hK3dYogDcbhupC8pjn4Uy2EO_UKfaowJ4rfEUqzSFO0fK2f4Lfe_9PUdHVDZNLIUvRrjrZC4aQ7Yg_Iw3WiHTmi5KN3BObIEROUngW-dHa9kkSXtX02x4y-frJmKQG-_Psoo0mKrqNi81PPfXO84kIyXSnFwKNL1dzaN9tlnHfNGHnniqjooAF9c-S2UT149K-PNZq12z8kx1pFknjgqMnaOJRa-zzsOvoe4lKF_YJzTw27FF2TIiPFrK4wiVToSctIJmDiT60wLvBSsAyK44xM3j9k9S7QOJkpwcJ1eCQerBxTS6nPKHj9HwvWb6fnrVZNOdjgk4UjqgJy-m2qJ6-WI4EwErwO98Gw3o7c402XHa4X54K5Bo9wim14Ze71MiqzF0Dk5D-cSab771KEBeRsepkaSMipYuyubsQPDfs9u-enYYXW6LL_TXhz6MXFUH2w2aa8iInBSoWBTG2q5SXgKUOSHMruwFW45lHBr-5CiReTEs4Bi4EMwiF3ndhZj46atW7SmEYBzTDjGYu6QW7JR4kVCkZohKIMxzf9ady4W0z8KeGgg5b_pBgWMimYqyZZEbND0xuLzf1jYKD_ekZfPF4rzUdXlpLd4VS8F-LxfOhRAm4D9RmKnjlPjeLD7SC_q68yS6FFhbBs2XJ3EUMuHfl09OqcpiwIyqax61QujXaga43i6xCYBIBEejX2XcZ1WiqoaF6RzPgDnazKUdCFSb8i_Nf_7Aipy8edOnER4S9phaZN03YIWsLbEqGt-vyy-mnpCmzkXfYOE-HcFV8QwyK8kJsHhNLmTx_X4mbP1r3bnCJX__L1WfeBHa-YLkd_e_eK0BVieEA2iM9TbEpLFeXLRFc1cQiVt1coLzQaJ2MFH0YUfBTxeVcIUTf6gGIhN2HtjXpe_5-TpS3U_p0h6YJvfLUH6-P4OP6Rv9teJWfO_pjhRZF8fEoH6BQXmv-KyxAMvSCE9fpjF2KZggC3rbix0tTMyE4SxE0PhYjBFzd6ZSrICj6EBL-JJzAyUFYH98gPwg6rD0SEKNM5w0IzG_8YNwp4BLXWPfgmuDCswXQgzZY5T2Ife7eDJSP_vZddG15l7nUaFNk3Uwg9FQTTTJPLTmE3sO6DzL_XKL2GG_JBRe_A3JN0xQeHX82ZvMl2CNFytEtraluZ9owE1SGXBQz874BSSZ0zF4sJti88qHvZajUt0T5uRVEclRoVd58BBM5_I4I7VtSSFTYmQfLnPz9XoB4BpB5fBAUdhMzar_qtpevnEaZe_nVC84IP1uyQN3KkuosMedg5uN040nHq61TQqcfFMu5dNZ1FgU-7QRLI54b2z8ktwgKb8XSyWNnAte5caV9sJGgkUoVu1PecVAth6ebxL4RVYxnDVFLkeqJb90qJqouBNDpWJvA_xNuJHW8u8aLZUp9i0ydQM8GiXhZ32figkFLYEXHGXq0IAUQ243WOZCVtzq0ZE7R9OBBAwaOEeteNKew2d1NujDy95YOuOOfA-26bbG-rxVXqqMH-5iXoUy4AyiJ2vSxuiL13pHPTxg38qB4DW4Vgt9lIu0NcfDsBGuHz8FID-Rn7hePy7RlTCX4wRhCiIYyz673TaMRQVvEWSehlOpTFNQozQ14Uqfbo2KGXK9HT5Q30kFBPHgeqa2oHBYrFBpYPGP0mt68FqhlkQ1zcTElw9DOf0AZIoHk5yjb7QoHCC1E1QMJUOcYbJC6e4oAkShiI3VWGJcyRTe9okB-t3sgxIqOEyCsH4uHsMkQlAUVMnXxuBd4iT2nuO9QWycu4BLSipC2YCldV08GLzgdzYfVAQ7mnm9RreOkVGFL-cQQ3dB--dl4YQTvOZyVNMvDIcJbp3lpX2C2m3EelO-uTqxO0oK-ySzIdAe1QyF3Uu5Ftk9JkJh_uNGdeqXTUImR9nHvhyAkIdFMHxotXRzbbyEV8peaYdqql5mO_9UG_feehavgrw7p_qWdn3AUr0Hh_IY3YfA9zirBArDCXhM--MXarG97-lwKZ14PrJy9zp1Nu4I2Lc1fYJLgZnpbgwYZAWBGjWnEIiUHDoN9O20YkRt5zIVDo7wPpV7zwzHC_L7sd6BeOc1ARd8oFJfdQWXPO8SgDxICXaWKHJL45qToSRJjI-A-tXGy_701-LtC2V_edpKwThldk9S5-adIXvUzHMvlOe5_eaNuhzHNpKz-WppJG4emstmgMCDBXs3PzuHN7dhAy2Bd1UH860tLDh4U7Uuu_t4YGkrNRbc03eS1fxTwGQq5mmeBnUPwLP0I419uOknMZ2d1nFgnFE9m0KquUxCmoZUuWaWQD8ak3a_3f0flps8NookWHjnfCTerQeuLrMW8JWN5_e4q0cAbJic7okt-IMimqA6OXEENkK-4O9yod_HE5znuTopf73kcPPdUAXjknhsFwnszjkSubdlh8kDY1rcKtlV6qXKUcX-gqLdEkuxVG_zk-3R_2qNGZk0UsUOuGvuStVsm37tB5gJ7Gssfs1SO4T08u-2wJ1-nwHNJG_EffnB0niB4xbaehnPKSlEcLn4WTjTxpe6NTap3fDHNzO8i-1HB7r1uZFDsS7MCzpkew8MQFz3FfurnNm8qP9QqYq0IJjn303yYprtmHPtxMtInadcjxwgUTa8RrK713MoExD-YquxE5FMqtuQx3IiX545bH4bpqPDwybx7xes4G3Sl_jewSCLQtbnr4XF6AhbOYxzWxR"�qaZxA3YN0mWDmj8p4VypVdsZlYpidKn-nmkj0rA1k8odOXGzax7waa9yvhNqMB8t9sYDv-gf1FtNfjvtgPbiEQq_jtJGG0b1NiIn5U6hP5n1IE7In1tWWF5sUlMf2AL71_w5G0jyixbrQiP6t2AF_IGbb3EkDvpaLz4Io91x1k6dMpNucVhlhukKWRmHlo8srPlM0bJSSC0FyCsN9ax-pu-kXgIfaVKq6Ar2A8hfyBg3ZK1B_10li5lEXDKwo_nKJVL5gcu4bZYUQjvBqQ_rjGBli44kYNyPTJHKDHU1rrgYEjuKb9L-ifkq-AT5n9CJUeLVBh1xNGDoXx5Ok971cZWRV_kX9zK7CwUyO5brG0X7x06h2fFSDm7697qsRpDE-7DiuXGBCnU8alC9sEYem0LIwX89r3R6Wrs0pznKhJ3V516E93D1qr8HzQDB0GT6g8-jPbSGAAxuGnJ8qqWZ5eYFThc5Ciy_NpMFuFU5ixWsru6mTuIriaABYw1B-Tq9BeeAD83vSXbhY03Hrk3MmI4fig3VCyIVNyqClhg2z5EbDnPr0ct6zaES1-kIK9Ynj-oFjXm8CoSkEKuGnvzoV3ae488Ap_trp_Rq9Vydebzs7UF4REm8-UhSFXNceM1IC0-wbQr5ri4NZor2XqdDqYZEvvKefylQyyAdSNM9dmaE9j5fP-d7yrgMPFPv8u3EC764A6mCGqjd3LHNAKnBPvs8WapM6GxXgMoyCcXYQaxce6OU8xy7qO9Cjhvgng-UVDaPkyNMZYEsI58q4GCdZBPfjR5q6U93wS8W3GNlyDn12yU0LfXAoHvQR4xYzzcr8OAfaBJVHk2512S9knEi1iNPE3Q9w5QtPseNvr-lT3VZi9WGKdLXYnNzsRhQoUa0yL5EO05WBcLkZxwgILy1Y0nb8arklUQpSX2Bj2dw3KJUhTFSwf4STEUdmu0Xz3lcSnphcIzHp7Xdt3TrDZm9UeTc2OS6KnTAq1HI8AUB9kIF6dVVO1aQuilF_UzTOhrAv7yMompilCjn5A60NTawpdQRELZ2RP2sx0bsUeKCfJ6p4t9ksUZrWlPbGQgT7lW8A87ifE67tEAhj3A9JTBQHBNeyN6vcRav86VvfMP0jHHcy6uuYv826nDUS_RdyzFjZZMn7QI4wKLLEkjFOgTNCPRZ2FiyLRFdG00WcjPNjGIzk7IZ0380UJo3SnwxfYc6yNIIGD4ouvJ9f6b16OgesNTI1ad643VB44c2HFKOCtpz5ae4yfrV0u3U0ChvFQASSt6kPRv8B3_uTaLQRadu8zaAUonAa08A6n6_vE9Eg3ZGEyDp6BiTpm9urjCXYhjsTb8YqhJZyZL_-r5ICjlSwB6my3UH6N2yt8vOWdgA0StjsngqNrJZ70g818yEP46qcnjRxfM-jW5X6MmuxEmz-xYYqjskkivCBobi2WhEQ8RRTeLK-xKyGgbU2xccU3yozdhpXdTp63zC-ynOs7RO_huZK9x9WQ-z-vTgqwPUuQ6Sako9eHPH2XErGvJDG_9eqNfpjgR7UU1CXTzzwZatFEatwlLG--UeQf-ICNl0qNq38NWctE-Oqzg88yFetfBleM56Asbnlbjkw9DjaQ5yLVjdT6LWG2fM9hZhPb814uWdKK_W9GhLjHJZqLjgrr7U5iD_0ArK5lGwWvi9CnG-m-yJ1V3v4uq3NT-inFObraMmN2sArPl9ky6BrEsP9mqTR4qUzc_aujOmP7fzoWqDuxzpSRcXGqwaDJZHkIl3HgOoDAQR-_aWd2QiNQKQls05V5APX9-3kycZIXCAWGiRsRNmFcMsgUkGM-OsKnvqtW7Yyv36xoB3_4zwk_GfIsd2ZN_YD63wzsgAnlMSgSVfXL_Z4Zyh6XocyAq4Qn6WboJHSDVu-yOZZi5tsNTeqoBQtJQr9bGMjL_01BdwuCWB0nz2sRpsiDHmitUmuRrc5nLMyyyAv342qUuED1DzDTgDTB34nJl7HRFtD_9RZjg6UTSPKGb8Mr5vcNoBtKtPNbBwfSKZT8BPs47L95f3Ty48er5kpM6Jdd1JomjmKEy1L934-74KDczvelOrWbbECV-lW9vjhPN5vkVYSAw8Z1Ks5TdqNO8cnEKy3pFrv1LRefxyfAXcUZPENoHdCf12Q28Y7__JItkUkb5a7F-v4bndjOs8nAhIqPXpDflIFh0KD9iKOYkfBy9VvVVX-pWcoIzjo6HZSvrC8k4O9jk5QNJOccdILXNCYJpfFDa56bRpa2gQQEKUX6ScKaPQNdz65g-_6cvVhTqLoCtFJn9MDEGJmEq5IUn2Te8zm5JyY1h3fkQ8jLZKBd-GE4Yfo1hKRRSMc7ukmRwvp2dT3OW9uvPFGm7kIJHNY83Dp0Hc3vs1_z2JzZiVPztf6rG9WE1mk-PdDdLQPSObwVoCvi-BFiZuJOD4f7e7eZMy9iSU9c9YabGPqQPFnid8rUzQvMkvcp9-kvhlEhsVeT8EZ8IAciQfZyEONXCLKui5tTm0aL4FETmTLD_S_fqWP4s9y5OHLvq-GVujo0hUXFoCH8S5lrrfhkRx87i7L3HdF9a_yC8f6h-OHkwhpIWpB5ewuS4mXvt0HR_rx8uX7DG1Ez5onyGL_hZCmVCO-2vI0cXHXa1JIM3FbDtkZJ83cU8NycA2rUwJ8g5hM8HeLNflY873GNO0A44VGh7TfD3WrXr8awO_EYB55AZp9xl8ZMs7ddVVb86bLy69d5cHTeXGDw05ciwiEHtaNHW-jhf6VgwytN-_dDHSDJIQzCdqYrLMOt7x5N-wkP4a9tueA2mq9utJhuh1ul65_-86skr5pCG14lPHSxTd1p2NLkwHdYRbxc9C0oDXV6Za0o2X88GCFnq8akZ6KgSwmHYzPToq3F-qLleqxPelEXT7E2nP3WuYvW0tfq2tSEgerc_935g9WR1cqiBjjLxQBmQCxTRuG4oLLI34gFXnjcsdpzhPzTRI5f9K-yre-Rrcj8rpnvLwEy9A7qrA3mQ7ZXpnVzvojYjs20Hb3_kxc8AHZKRWrxvhC07XI6Zegkaz8nS0EYYENr7RxxguK5n3GUJJevj2IjhLWhIeIvswRo-7MK2kGDnLkgV4wcyaxKI7Oh0jn9SvnnuSelEZ_YdGC1qdW2vGHkL7WmzpG_A8yXMgx-eZUp1I7z4oR-BTzMcISmNJc6lx1mFzQbirPNDrOkMEZ8TlmIRhlNio3xj3TiP4RLLrv_qAukdfxH5D4Y9bGWPgWk1PylanbkFrjwaSbdRpesz3jnu4HshbYcozrL6F7XVsOU8ERPshv_nq10fVDWhWcg5YIZbuDWbDnSOc7SgnvNovpyQAohZqRwA6R_YUNRNrOXbIFZr6G2647u4ADg8t9d8lMXx9wakgYZw8VzOZEgtlpOIVNZTwSlCD-l7emND2kuOserHwKFcghbI5yKACA8ZnjI7MDIffqsu9CrvVs-Rbg-N6yINJ6JAzMaeu_Nwp85H9PsldrEhUWI0dGOIOdtMGVRxPORvsmpg763U9dpq1s919-bAR78R45rRSdfqwqcQXU40f7JP34DNofM2SLnUMQBdJ-bHMrCXuVcssn8QUjjt3dHXrQMEg-l67V9EQz5ZIdlpJ_MzuDfLbFYnEsiMgILYUBi3atZDzOtDp5FwVSznVi4Z8YxpTHqpyhJ2fgK3YEeGBwuwlOxd18i3KjK_DkVBHTnEdeW0Aujb5pSo8TaNmMlyQg4N-24f8yljfGVlP432OGMEtX9bagySe240gjNBapKe3xipbTtXjfSesog5fvyhqBvKFjTofjgfGIVCRCHh8T9CDnKt-dLp7EpHhNavi1xqUbLBlpn_IABj8iHjIt4jndMRBFkNxs7iBEP7OOSNfCYB_rds-KmLHH_BQYAaH4IwLUNG0Fm9vS5pU-rJdIgq0EsDvyrES0FypFwACZmc14tRZcXzO0yuyT3P92r3snnS14lIYVTON9Uf75sNdvXhN5K9zmOluTm2m6zHX6_HYeVcwUL8biuwrd04lHNvMCbi-9xz2hzcabOfeNdt580FdQntnBNR_0h_AXDVxoeM7FNmel99kXd4ytygK1hrY"�7fvMnvpkEPqVLTEqeJrUOk2kCrc5X_nLo8BlxQfzrk56d6OWHFW1Nnm_WyN-p_vdpL7bZyaMgD8_A9UiUAnglaXi0WyvhneV3efjqZ1UYD2H-4z-7Umu2JA6aiOUNwcU6qSzC2RmhHeGrFRBKv3d1HX_0HLwbkcYrMdHGEUHC99Ps65mV8ohqzN084OJaA_9H1J7jvsEsCVOqQgH48Fhi-Cy0F-EmpTot8TFFNOed5RhJdwk6VNhkX1wcYbgG5DpBLPFRNjDRFJ-uB2TaNqwI1h4nQAOmcIIFq_nOcud65B2GgLkAQRPOnxQyTRsItPODfN9I-0X1k85eoj1VT5JV6Fq8DtDiCYwc2v5lNmeSOD8YHLTUUqFro5ePAHQ-4WzSTjdxz_uNUyxz-hDIA9pHgZSMYT-KiaPZS9Vib2dqly1D4ZYhKjlIItQs_Xlo73iPaePoni9rpgQzXoEwyaAju5Qg5CWrRlBWZEQ54O_p4i-R5wwSMQwJXxUtDsf0lKZPOFJa9HqcGmzKmxjhX_9F2w6GyFWCW_ABTa1th2zxoTN4l6CTIB6PumYGyY9d6jIBcdZNmotIjvgTpysyh1tqa35KaLJuR0r5dmaZrqJIOP2MuNcTANph62Z9ySvfsRYIk0YZBaZGyneby-kKmn2GBurY2xVzJMAqIhZJFEVuTV2SIr2ocG1WyI9Rb4GAW6Sq4hpTnNrP8poZk5mCzQPj-0VmcqgtWniWhfkqhXX3wlXkhI1bJFQVp8Rzs7Jim74Q798i2FnoUcJQ9zyEV9Qk95TEQVeRVP7CHqSHksa2XdWt1ybKJCHd3NVey_HQW5-FleZLQKdx7A0_aJHGc90TI3FbOzpVcsN_EbmKLfg5b0l9c67cy_uaarjFp2cjH_mUjDz7TWtcex6NAg3Ka_0tAhn9bw-ueEOUyF5CElU0YURCGI3VtZ4Rer3xlLN-Wc97strsmpo9JaNSEZ1tczibTZG_lL7CHQnbfc0sG651KPX1EvG391P2HvIv-_qHBAajIcmneewMLR6BFGTNuxXsqYHrf57tN43BREAOMaHST2mSei79rKbP5v9xkB_H7Etg4UDvWekd01k9E-c48RL08bAzVuOocBoUVbvfqusx12IHO3oS-DYxn94QzLvwwxKu1ZKPlEpSo0X2sI7nEbqF6WWAATn38aAY5SOoTpcwg0RE-RKxpE7sLGKuFQ2wQPnWepJYE8aA1W3ISq8fR9uHyd57PnemN2RN1GL0vRqw2VxSDuN9wMJ8nwMmr2u_Q1YzjpZIuEF3zY1fKE-DQDeadz7Jh66XNwpE_2d4ZodmSbHgULsETj18iBj7fJyl38mPmQY0pC1FCcPAi-geowORXjAV3F4LDV_mnVCEvccQflMz49bjl3HmMuv-BadTS7rHK1qHetoQk1vBRlLtG4phTVnNanbYd5oNNuw12kpcDIYQT8IfcTshv8Jh1LNG05FUvVZ2Tf4PjixgyDh8_n27Y0oD4XkoOUEYChk9A0PLtmNOEveY_JHbcvbTiKQfaz-VumFPUpkNNFGYXMGFy66EmG5zIyf26TCWmLZ82QJz2Qxb_H1wNZAbBN5Ku1yd5_xRo_7aYYBGK2RZAf8lZ0KPvzImJf-RsgZ5-bJTo02TPGuidfVXlJW5g9Fsun7lWdZu0BJsxQKeL2IAuEJBeLqDbubbVPOH9VOg_pCZRJIgnydFIZQmv0E2F6cVRp70sTf69DXii4SPF1qto_Nuw3ojojZhF02TOKGiRptDIj0UYvXopWt-w3lDf7MVjaLQjiVdRO9TNbs_4PzgD4grs7eOB1VpFQfAntMcCgiUB35IphO18rfjTdTl69iw3QHbZxQ5e6AppbOu8Kvfa1GtbzH61ujUM7N5PLxhoB69_cTb7fcr-cJJumteZeEQz8Z6nBtqa5_SvP9Yn9Y1FvqgzvIKMXVx_Uij9D0ixpWEv1qKw6JrSMH4F2jqUL-oAXYl6tVw5rNoTfJtKQYzRHK6KhPbtu2vli3ilBZTyN2owpkelFw-Ke0zcKdGKCiEcrcTyFRUlzHI-xkrQ7TfxWMBW7UM5PTQVqtbd-m1EQgX5yXb-rKeoGpTDN1w7plOs1kV5NGffceMc6C6tYu16qwNctmTG0irLYmjAfvKm2upihKkXtN_DaoXz0IbmhfyhjHm2PQxICrjC3uZUTCODJ4oKVntS1ja-nSDVqL9wQ9-anoBO2o25omYn6c0dIaOUcRueWoxqMzB-2OUj36y_FUbAyjSYxTmYFJFY6LStG5jQZ_7FNX1gcQXrLqH2-Ii9xzm177yAWyiEI5XQnrWc5l_U6QXbkPTXN0vqFMusDSSt66dMUYSyy8Liq8UgYHW9UgSPLoO5LN2OR1SzrBZKH4ZOdTjtCY2-5qvWFc2v3IwyNpsm58thEKBuDbzBIlCGrGMvV4McR9QXOHCIzIhiKy3kksG2jruo1qWnX242W25buOIKN9o5bJCrgXaxbFr_9SB4EYYEnBlVzf-lhln29Ckc4wKI09mHATfqCVdpmwxnZM200PAZXkKjWQooeLpDgsjZOEGeOLAmJDjzIHF41A0mA-gKA9Jepmnry3ghe4y5XUzLSppvhTxOwD6WyizKgWSnfWVTAanu_EinLkKdExoVnIgIJY8H1qxPtTHwvAwHxpXIak6ib_h7irryk06SGUj2BZ-fmwVK2TWz7koNG1_P7xY53Yu-2SHvjJ24jkYwZu9FPpE-OfjN9GiXFcQENJbVIEUSrU1udOmWmgYmzVdzHNOmSQI08Em3Tv1X6LNTU0WUif0P5xGKJ26lWT66WNXWm4nRD5IeoZmjTbel3PDa8H9cpQGRuNeav73AeSsjN7JyE5eCovpva8F9q0PK3T4KJDMXuKgr1W4TIREKn9yHWIWQqFVdaIH3oQl1BDGKkAecaFkxCiRYgb_SQM0sbCKv_Y3rXxNzhEIMp-P1B4wS8FBMVwWPpqMdSQMo-SKHlKzF0mq8bHwBUQnmE5pzG9A7D4Es2mxGfSMtXIMjBXTIeXdGQCxBpI-EQA5iD201xODaffGAuB6rRbx99y1jcnUSzsj0Fl57rulSXU8qiWuri_Cimvm5-OzJ50qpD-Gw12Vopld3iBnDA8lqBJ5_EG0qpW_lGX91L0S-Ah95Mxfu_eDIof3zuPbvCmSJTm5RkJwup3VWAeMEHTCMiRdgNLvCZ4qpUde9mEJWbT3GbHQbZU63HpBUh99IMCJLwrbyK_XRCSHODCjjIvoID-gATZeTDIgiTcIE4hgdYfhSnvs7TkX-j2A5O90zULSrFJX277nif0MSfPs3xYwvx-TviBptRV4ymejS8zRMGLK1-i0TwvXIbVdYQ4mTXIemjYkpN0neAJ-_OD0SDHGZ9DV-ElRng4zLhVrakss5I6jmu_yM9YSQTIikHABaMmsfw7nrKkjieVSIL02ILbhY6xZgmU6_ECLHUwU9PKtMOZJCM2q962cBpYhoLhMoLBz0ERS1WjaRNl4A5DJ32yUFriTj7csxIIzDK90-8wqbsiPnKtOZfAV81QzJAyALjiXEaOKwdX6IbBnCixk25J5cx3r_yTl2Er5zEp-aOqDmCIOHgceu-q3sT4TuaWD0xjiROR2Wf6uWL_7cbEj47ysX8EEi94MSRZpi1hc-mG7I5E-IF2js16PAHxvZehIViNAmJKrCQa0bCD_Fyeel7I6GZzlzjxmLYePWYr-GneICuEYL5XLuMfhcsCEA1vvtecmSHtqWvRaANAWJ0Z_cfSL-FWk885J_h4vHapIllAZv_-wxFJHT1774TOni5gxjksMA7d_0jQsgNO2R_fRDn-OrRxNnQnDViuBR11a3NSvFSr6VAHaHbo4CtUcZUp9M1-bdVNvzyUgO0yMUnD9McfFZd8m1QvL6u4UkuBmflv6WZ1XLAyOwfENqQc13HugTNQFNvW_dUJv2YVrHMvzue_kwa2KVb1PatBBgTy6O5YdOJpsTzpyOC-OneXSP6GQcH4PfJooaVNOLiigqYTf8G1K8qZHNuaOIhmHBjaTZEHgBL72yeKrmRAq3VX2oiMNsAyJb7kJqLH7YLLPmCd2ujaptsStAff"�V67S1sLOTyPepRbqUIGdA4KziK9uNgAnKSDZlU9H_qslg8HtuiST7cjsHlUdkYJSZAVpV94deTbh30_cBaXJ1t-Ht9yWoTKFd1eazM_ugaWojGqYijcU7FNQXt-btt_FzvWTwb7gz23D2eeMimbB7l8Ei-if5fhQ2z-pkS6a43xZra7dBSC9IKSKIhBYxKKdNZwNtJDKl_WvnDqemJezUOYhqBNs2H5CWr5Gnc69cJlihnNpOrpjKZV2yz5L_ObDcsBgkR9nghKMWi6pGYz8kOS1875hoylAA_7WJeYRol7fdxzPsro3GjME4IN_RKvw7o2Hx7VnOcnT9M3XbZalZRRZSFHr4Ews6dd3C-Mwvp4eCLjIemgf11Z8LacziEcwkeMahpAXj2_8iMFk98i7XZgpTJfn5VWxEYBxREKoKANv5Q2h4XytWvdbL_XBzffENzhSd01QDwfsEzDSXdaLqhbKVH6dwawj4KzQbdYRMmQRBq1eitmD7IPD6Nk-FBRpqPdHXOZZqk5w_56YbBlBVbfK2sxgFRB71EVkaocShwKuGLyPBkvdTwDSfeU2iWWXeUGCifIapSuNvFu1i8Ww1TfMhB2vr9p-_zoDQwHHkmqHQnP76ZDG4BQ6XdZXThO4_98sATmhMOEg_ImYbz_XkMsDLlcLrZUA1DfTkSOP_mu8PONRBe3FFgIBfpiIiS7fU8XEcl9UNJGuDsheCVT15LOKiGhKRqzeLaljnDPC8SuEwWbRJYHf9lB2abZYF-VY_9K0FQC7dDidokNFsF_qaNvKlYlWjkATV30UEyU8xWA4itlk2dKXmG50rGt41CKpe0EMKzWnq3CrGVWo2IDgMK2KuQjUuq5d8F33luB_-ksyrQc22XI2dpWOn6VpXWh87E176FMBx31xPk12zBU-gHz1Wg_5v-Nk3Z_gz3ObS_AGr0KTkk-teIiQmKKAIR-ohMCDBhY48MkHJLPjp36MH6fzaCOuSuKP7AmoNmrzG3ojb03RgqaxuX35EO7vDcqWZ0YF5uZBJfNcA8z_OYVswhXQjhOUk6PtT_srvSXskKtLYoEkdA-488WuQstcep6z_WIFjOQgq6OEmV-MK7zRlnLtYM_sOWZIBeQjEyRc1IRCkyVoIGB_opNGwPqOj9V0fXN4RPP47pB0E5XoF1pPd9Y3YUAT8ohFtM1NgKwWJTRrLF-IlNkER5xMskZNEI1-z7Rc7eFoujS0AOdbbgfTEq3nNHPMfpBmvE3WF_BCbWP9X2xG5dKBW7rzCWYPAjMaVVhDGnz8ZNOWEV1V3Dqka-pf2Hl_Wu9-tUjWwYmoVaL3SQVzOB8rOrYE7w0Y68J8XNFVdQIbr7DBTle-xZ4cecq2DBFv3JXrTnr-XTgTwuxSxL0ui8yKa73-lcrEJraxCThfc49isIMFnpHHtcRegC1L4Q2_-tEcM-4Oo5IbU4yz0RhpkgwWFTYCAU7uStFcUiaEAZ-ChOdZ6HQwhoXzzH7nWSMdg6mfYwtnsNftwRiwWujry0GCGs2RPn1CCplVNkVMHTpOMqGZ3mday-TdkXMWg_L95rjAf9cB8ro9c5OxpfsKWWdrTe_wX_egTMoMWhVZoJpWwztrGa6Kjn-tCPlp8LhTObcJLe_K6ZYh_vBN6ocpMIRzLD8Hke5eQWbtjiH28qFl-2Qxuo0-dpooG42NlrrJoGZID8Vopg_PeWGi0yZx2scRXKLXy4eCiCXYkO99p3Y191Vw_y0VvcZ7sCLw72rQfz4onVPjoPTse2nQgD0TF4GfpwX1c5T8R_t4KgLQJNjE4CgYDa7I0qNMbEp87gJh6SqzilWVMt1F0YG6lP3C1OQl2CdCnrJBrdX8mXbPF5dGbBMBRv3YKW5GRbhXnm9pFp4D5FbFPlKb0rc_XGDFHpfcDaJBMIUZW8rJnT1_TH0lgcawmnw883C4pjPdU_GfQk59sz5CfBKZv93whD56zleYjGtKbSfDg-SgK0kxkDUaL4Vh2uCkQJfCsG1q7C_WXislzviivPmnEtxtl8LHjMl3e16phzvPu2dG4ZTJCKDYm3StnwXKIb7SdTSnlfIC4e1f6rgaZk06gtGcD9EF_hUf8x8ZXXEdmyvSb5bUNMbqKMjdxpkoqXcG1KPHurzgjKtD1aH1sIDW8ZH_fO3mws09rQtC0G2S8BQggZIxveXP2lyR0r0oV6yjLjMh2Z0UKzKAhm0TZfA_ihvE-1iQs-DeyZyUHXQfv2sifN6rPa6hCuOTgeNVUL0t_cXB8dyLbPYsxUFVLjwq8nRtVV6kIvKXRcgI8KijsoJTvmtq_4u0b4PHNYXZdLySK0drbeHoRjDLN1eQALYVol7Pkn5yYs6mscR-8bDQCQ1KM7-O76FxtGV8XNf15vU6vbXO06WIFX6rS5qICavP3umjJG1G-fAxj-RBMrysT6mTnfkaj2eABNKpkg3tfUUeJLSH_lfOmhXAu8bmxG9QvxkFLSBEqqTWGhWsm86qnVeg0A707uQBni1UxNlA3_PuMbZa8JFh7QXlH-pSfCExqsxTceTeUTMyc-5PsdEp21fhhZ6A-Rq25JrBpyP7clRdEMazpshKL_mZX-bffJOpTyx1OO0xFEXCLUjNKJP9Zqd0F-t_V_yDVaj1NHP1x-QEeiyN1fZ1Gmw6ywGNmj_mYf8s3y2BdxfmODADkDaRuAmQAGKxQyMjae3xv1ReHFOowba6JNgxXKi99uHhAh4VGcU2XOwUnuu69kyqVEH3GmKa884DEzjmuhtplgfWs4L2j8kSZ4KZHFVA8jyJO4UEBIhuT7P7hUuKpoEU9LK8u6GlmAfikvojHuMzTazT14x8rHH-VC8iyk8JmamVtds0sEI1qmDHRP4-gyUU0itVtDACOzvDxaQn9FEoCeaqjvnXG7mw5HhHUpa2jm4J4OKxbl8GINsWB5Lb0uLx-l7y_KR_zG38hut1y5tskiLKmlXbStQ0Kz11WLsFRhdqShWclV1xsCPg5Zdhbnng0_hhde-qmZtV2lVUA9wSBbxNHgF_1GBEL-ozE97K47CihJ8E2vMniYI-gEfWXx_EnKHbEnQRn6c6CiwT6tkzhPxQ2slmO6y9gnfyoDQ0lhH-ZWRtQx5FN6tdA9dIiV4I5xDpQMGUxKJbyTYQp4i8pnKUsbiJfwCwyTAVCKnsB8ikAYzjAU0xr48_B8oQR816Jnxlqys61ogSml73W-K6cJgTXp0bZvAy59eHmabHDqXOKHJire-82c53-FmXoEeTydpJq4eX1SS-O0dYo_7h0fhzuBJQm2W6Wko0MZCUcreNRszA4aZCYLPAuZdeoCpZui6nkj0XxAqtM6CBLnptCO2trwCUXiYFYFz1ElNR_IUEW5gCwBE5aU58n12Uut2JpRSbFftQruG7GVPtcLyZ4PLG74eTOp_RreN6pAC36zPcGzQoUaIPG7Ckak9mmRPt6ZikYmagGVqKDqEcTtQaol0le0ZIem2iD7IAM3CQlK55lbkZjq5P-wI5xrFzB7NciNrM_SW4iyL_sDwwkf7z7duLmKhz4B50oGMFBago8nf6fw7JDcjWJYNSKxIYfZsZ_yqjxcHX4jP5VGFTc2ZWI-qvbUqpzIr1DWvXJm5srYWNiZvQtY_8LL7cZB2RXWeuEcOX8ONhyQSx4FHvizKYjI5o_NeUeryTNBoyFBNU2Bk6B3HGuvapVkv8ffTwmmvsSXi2m4VWqNtblpab0DuqXV3QBa76JvF6aeZRBB_NcNrNG7jOpVpS70v4-lo41sfJheOJ7J595-ABw9mvWPaAVafSjkQgfsI4vSILEpIai5-JbnY04Vn6jxpFXFNSOTeRDcwKmYthfkNYGgtY7GG4FsMY-wKE81JrzwFRunx7KkV6olHALHmAYPX9cPiUYB73jqd3ZG-u445pp5Ax6RI5yJwB6AilnMxMbR6QGvN89jRIT0f-QQwBGKf2sPTMWfXVRIxbnoZYQvSyyINyBKSp9sYzlGmUyJPL5nBWwBwz-HIbLuOf5TDupj8A0FpO8veOfi03mRn3-LgzoiulkWjyqrcNT5P4TFH1rp2DTgKqfCBOXWrpRr1OqEwqpkEzKIrLnuUR"�orRBI763_BdyNuFM5dBVlirePCl-AiFfXbNIwaHcQCZSyYz81LYWEJRCuE0eu4ZeShmq7qBzGRWXq4qjXFSM1JIif_Czzcom2GEXoEyaN9foryQgz-nQ57Iz5l-dVGg9vI178ohJnDSPLlJAZTTiwcD0RBp7gJLM-g-Jw2r9HVhSfAV020NctrfQnNSJvlxnfmYVPQS_MBl5eQfVeHUfINRUoLYq8hBKbtCXqzJYGrJEhnet8DEPymMlm8eoezaNOIFDdCk1fURTZ-g6QERqLLnhhw9RlRPG7tOwOCMUpPHB1ty7vSytwKdAE6SivOGMSPUTYuyIc--1LDEOY-OlluvZdX640R0bIeStn5lEWkr5eQynX7-TtfLMW9rXjf3jGX1sjDgkmHEAXfP4Nsg9C89U0K8xap4ejLMVO0vvr-6ubaGJAm_mKn4mjUp8ASH7k-KcYr_jsLd4XTTM_t9dfGtn-FvaDo6-o7eX2WF9CgyYbfKuDBme8fJDqMZEAvLAYQSaNVuLT6DL2ebOA_Xx4O1akTpw-quIkCwnaFG4ul7MlFTfLz350IR83FbOJfnffPOttBdjyreN0U2ZmoV_JAnLhjr-8472gOPMOsCpRtbX6nuHpwfGPPGwfZPFOZC5yrWM41KThIAaOX8vO74ceepaKrA81RPjv9BHS_4cB4SK1WrUoHXjOUstnb6a1f-w28N2fVaG3xF8vat0uCI27LVO2Fd4DZUMZPClioCWZ6aIWyAFq3ht0Jdv_K50VFuMAG9sbCl1qy1Lo0m4XY1zAHiiHiD0otdzb_WyZo2fEMCdAtHNhCasQkYUt-SrWt4zpCcYV0Li-yMyezskJAvxhRlNDA8ux90icc_ZDS7ZcmchL3cxm8_VtiVWyd3E17G3HIUw6XYvoeNZs3zgs9ZyofoTurt42tuBY15yQ5UeNXyF9tWruGUZ8v0QrcWvgONCeSecSxrHweKtUf19a3ST1V1TDaMGvZXJSnfSd0L1IrPirQxVPSg8qq9T7hR3TEpsa9jK8mwnNknbfxfDt4wi12x7HXWEbADBDlugvtEYOkYFQhbKQE8JPHoVS_Gi4LzXilQqrZc8-OUQfx5l8nwuRZ2e98qqtgdXFCUGldKvgYX-zgihVbxWbrHanJJRFS1Rz_7y6HPnaoGeZJElJ_MlVL6KlurWyYvSdTzVV8ICyzXnRCJAj0fYrb-NNkNC9jnb5x4uV5pwXRIX_1vSt6D5ZA7O8UQzSunp42fhK4wVL-NbS-AA0P-wcYcD6UGDqdo4rGzoakKgg_JHyzCNTx34p2iM6ZAd7tmEcPjHg1u_SfGZNGL4pwJjA5MvkJVAANkH2XIC0lalgT7Y9BeE8PNw3q2eciTwp2vjG7aISAsg4D1JPqYfc_o0PCQVvyZmlDc9i7bVs-cxQSgLkbuZBZfepA9BMBu6bFWBOr4TsxEr4HgXTcmV6itABsa4xW544KCijBsXr122dw8QvNX69ZRlnDxe3OxWAxBvgCW_-WccZ3Hni7gVDXMJ6BDJIkWKSqhjPQDCEYZtzDqXJsU3spoXBmKUHmZI59H9MJkay9L7PqCEA3wGV1tBOeqsPK0bnO7cg0NMnlVWMw7mM_TiXXVQoGiY33616fBjPUhU6OhFeQ0272tlP4yXF3X2lWeqzvgpb_LTrMw_-E9SJQrPgxvqxPYQny6fQ-pI4Nu16GF9vwim_NDVcxveVEI6GdPn0Nh7_zsxE823avTInRzjduL3JlB5TYnzKW-c9TwqvyCxlP8WBmS6R9veTdf2k6hDk9okb7ie_GtVN5dUyoDlvUmdEneHd9sifR-dzE2E8-me9OUWdyy81-TIGMKI5vJN7Lf5lvdrnCkwnwR6ZKhVIAg6aNbntX2Jl-aShE3ykmlHOIpi9MMhlYadhIJrrpXZ5npMjOhvalgXBSOHm1UUpXuzPHck_2wbhKUvCU4GyWdwY9j8z2yAwuyLGM4g-QoZMnPAv2N2rLayOXF-ejb_I631rhEGiHbS8dRSOu4V70x4vcYKSq8nuH4yePFORtoveJ-bx3r9BAE42iu_S9XiznyV1rWirqQIYfAQhOfIXO-r9BP-bt1R3TjR36WD8PWKiLydhbYX9SWeewJAFmSZyYCjZ7aFp3UnMD87hcxartIt6RrzxiuFo3mS8xLm-wwEqs5ht9V-0hm0w8B-lCB7_BDE3GkVLmhZX1wYFxTM5PA7ORCl76F4IMFeeRNRAKrQ1__tjJbflGc_oyQq2jzPvFWqQlpmohChv1liw9yoR7ev9XLQEISY1tgDreMy-aq72MS8jpj-sjPXgibinBBN2un8wrDwpSSwoEJm6fZHz5e0_T3ZIjOH1EseFzcEoR6SboxAF_UH6-VMFR26F2EkJZ94K3Qu8FR9_AvxSTGNTFKJ3KFuVgnpZtAKaIZqD-sq6YqozLvwneTXthlikOGfF91b2NXTEDRwWaOpav0hnMi2eM_4RHGpFGGse-0kPzI_MtdojcWwKkgH2UswBiboA28r3bz3wYZfu_fi-FbSiYXR0rURJAiJyA4NBKi15q08mdBPMn8wafeJvErjylGCIb0sf1qeK3VHUzLV8dsA0wnW2uAVHXrDio4v8-H-gYQz5zQmDccvv9t6qKyq2P3b9-inMZo7LDZDNH54hL1xxHfmoiB5kDM1bc8ojU_bzdiXR_sYgZEX1GtNKjqfqDg2S8CcuGO0tPfwdnVMLNPVZEEcbymn23VXcwlUL-g9SCHUYd1DXwbvyVBxFF_Z9xAPnSmUImB9fpku45ZOIwgeUryS4Ss79N6VtVnLEDWWGSBhy--yMGpjrPJmF_SVKjLROTW-FPUesYcWmKhygvitHca4ufc4vZ9Jnwg863gP_acd41a4cwokGUs2ig6kglosUQrgGwmqP0jHf8piSdNCX1b_5rMNFSgLIgZGD2hhEsFW-EviSmTWyTC-v1d11I2BGXunA16Cz4od0DabSmD7xZFkmA8rPGB5q7f-vPUKjxfY8UjxXnmBGRZrP32Ydn1YaMYi5X3lSWrUScEqAV1k83o8mWZbeg6OqnLR0tjchAxmf-gXuEMeCfQv94SSghp6i8nKO8P0l6hYpAFbUOGY5GCnY8uRKzws-kJwaeReonP8nqJaVaA7h6DDyhRU_XGK7Qa_uV-Z_pcZxeqlNkYl0JISypAJlGOlhEmW8b-UzcHfD2DXtE2o07QYJzoMd8U8d9IDoi-dc47l7Ws_f281xeheivJMJDD8Ijb_Qd2lzjZJKfrLzuPDojfXp4orMMzlNOWw5upPlbni931sHsLYduivH_EFYGhfoh97w-sA41oJm2ewKQM416mowOv11tE60qldba1xCprM54KM_3QnIKjArRzBpSpS2uP6R_DJXXadvDQANOy-MYQ4p375S0y7t3jopAnQ8v_gHLVHqFl9KIh4nBrHzzMJKklJxva5EqcOxVu2b-v_hAE_pNnC5ihmdZm_gENTbmfm7iAwngl49fG7BReukfvmfwr_9kRKSLu9rkdQthW7AXeSwNRjAcRvlAJZoAQaTsJc4ukeEuGfKAyl0h9uedPmHfOehwRwAj9pTFH_UFLrYaZmeKQz_U0MHKwfUhQb1sR9pqb1TA6LzB2LX6ilsk2lidzOOz_W8N4of8egOkD1CbfiktTEoNS236fkWqNFQtEH1XoImoTFo1bWN2VTnKvQI9qY4FkkW9vkayEc-m1bo2QmyPAiolHc8PgdANAyj7y-CqztQbyv098g0kIIEnapxvi5YbcvPdC600_jmJoN1HLllDqceJvmUezcXjepwt84leU1Cm0sPEu4Bp2qVY7vzrhP3x6fd0M4ISabzs5pZdqBoZOLk7UjjEmBqq6porBRo3AX1huILUQwRxms7NyZWg4uuSSQxdMkqCH1vwvfPXgYTbQiimi5bpxoNr-z2V7VdXvSH1YvYAYk9HEAWa4ApVJwPK9IKhr4oPbK3tFDoErvmhzJzYqwsJUFRj-EiXr7OjGc2P3gaSKPpJDjKdh7p7augZSJYR5JFvtc57IewWk3NKDd-TU8EMN67Ctx2C0UQrA37QKkfjrOaBvvQ83Vg_2T2hIugOFY"�>]*>(.*?)</script>')
JSON_TEXT_VALUE_RE = re.compile(
    r'\"(?:articleBody|body|content|description|text)\"\\s*:\\s*\"((?:[^\"\\\\]|\\\\.){40,})\"',
)
    if source_module.module != \"sitemap_daily\" or source_module.source_type != \"sitemap_daily\":\&�J8LCAw_pqb3JWhNaO-zqnvwygIf_MaoiQj2lsFDPP8RG4HIia5DogALP53oNXOGBTI6fsgEWt5nMX0xXvYwBVlydeTE3JaCYQdaCN_jGtec5ZEO4MKpiFlQU5YxFXzbPTvVeiF-sezZT63AnYVPmQthSs5deYjv5hK3dYogDcbhupC8pjn4Uy2EO_UKfaowJ4rfEUqzSFO0fK2f4Lfe_9PUdHVDZNLIUvRrjrZC4aQ7Yg_Iw3WiHTmi5KN3BObIEROUngW-dHa9kkSXtX02x4y-frJmKQG-_Psoo0mKrqNi81PPfXO84kIyXSnFwKNL1dzaN9tlnHfNGHnniqjooAF9c-S2UT149K-PNZq12z8kx1pFknjgqMnaOJRa-zzsOvoe4lKF_YJzTw27FF2TIiPFrK4wiVToSctIJmDiT60wLvBSsAyK44xM3j9k9S7QOJkpwcJ1eCQerBxTS6nPKHj9HwvWb6fnrVZNOdjgk4UjqgJy-m2qJ6-WI4EwErwO98Gw3o7c402XHa4X54K5Bo9wim14Ze71MiqzF0Dk5D-cSab771KEBeRsepkaSMipYuyubsQPDfs9u-enYYXW6LL_TXhz6MXFUH2w2aa8iInBSoWBTG2q5SXgKUOSHMruwFW45lHBr-5CiReTEs4Bi4EMwiF3ndhZj46atW7SmEYBzTDjGYu6QW7JR4kVCkZohKIMxzf9ady4W0z8KeGgg5b_pBgWMimYqyZZEbND0xuLzf1jYKD_ekZfPF4rzUdXlpLd4VS8F-LxfOhRAm4D9RmKnjlPjeLD7SC_q68yS6FFhbBs2XJ3EUMuHfl09OqcpiwIyqax61QujXaga43i6xCYBIBEejX2XcZ1WiqoaF6RzPgDnazKUdCFSb8i_Nf_7Aipy8edOnER4S9phaZN03YIWsLbEqGt-vyy-mnpCmzkXfYOE-HcFV8QwyK8kJsHhNLmTx_X4mbP1r3bnCJX__L1WfeBHa-YLkd_e_eK0BVieEA2iM9TbEpLFeXLRFc1cQiVt1coLzQaJ2MFH0YUfBTxeVcIUTf6gGIhN2HtjXpe_5-TpS3U_p0h6YJvfLUH6-P4OP6Rv9teJWfO_pjhRZF8fEoH6BQXmv-KyxAMvSCE9fpjF2KZggC3rbix0tTMyE4SxE0PhYjBFzd6ZSrICj6EBL-JJzAyUFYH98gPwg6rD0SEKNM5w0IzG_8YNwp4BLXWPfgmuDCswXQgzZY5T2Ife7eDJSP_vZddG15l7nUaFNk3Uwg9FQTTTJPLTmE3sO6DzL_XKL2GG_JBRe_A3JN0xQeHX82ZvMl2CNFytEtraluZ9owE1SGXBQz874BSSZ0zF4sJti88qHvZajUt0T5uRVEclRoVd58BBM5_I4I7VtSSFTYmQfLnPz9XoB4BpB5fBAUdhMzar_qtpevnEaZe_nVC84IP1uyQN3KkuosMedg5uN040nHq61TQqcfFMu5dNZ1FgU-7QRLI54b2z8ktwgKb8XSyWNnAte5caV9sJGgkUoVu1PecVAth6ebxL4RVYxnDVFLkeqJb90qJqouBNDpWJvA_xNuJHW8u8aLZUp9i0ydQM8GiXhZ32figkFLYEXHGXq0IAUQ243WOZCVtzq0ZE7R9OBBAwaOEeteNKew2d1NujDy95YOuOOfA-26bbG-rxVXqqMH-5iXoUy4AyiJ2vSxuiL13pHPTxg38qB4DW4Vgt9lIu0NcfDsBGuHz8FID-Rn7hePy7RlTCX4wRhCiIYyz673TaMRQVvEWSehlOpTFNQozQ14Uqfbo2KGXK9HT5Q30kFBPHgeqa2oHBYrFBpYPGP0mt68FqhlkQ1zcTElw9DOf0AZIoHk5yjb7QoHCC1E1QMJUOcYbJC6e4oAkShiI3VWGJcyRTe9okB-t3sgxIqOEyCsH4uHsMkQlAUVMnXxuBd4iT2nuO9QWycu4BLSipC2YCldV08GLzgdzYfVAQ7mnm9RreOkVGFL-cQQ3dB--dl4YQTvOZyVNMvDIcJbp3lpX2C2m3EelO-uTqxO0oK-ySzIdAe1QyF3Uu5Ftk9JkJh_uNGdeqXTUImR9nHvhyAkIdFMHxotXRzbbyEV8peaYdqql5mO_9UG_feehavgrw7p_qWdn3AUr0Hh_IY3YfA9zirBArDCXhM--MXarG97-lwKZ14PrJy9zp1Nu4I2Lc1fYJLgZnpbgwYZAWBGjWnEIiUHDoN9O20YkRt5zIVDo7wPpV7zwzHC_L7sd6BeOc1ARd8oFJfdQWXPO8SgDxICXaWKHJL45qToSRJjI-A-tXGy_701-LtC2V_edpKwThldk9S5-adIXvUzHMvlOe5_eaNuhzHNpKz-WppJG4emstmgMCDBXs3PzuHN7dhAy2Bd1UH860tLDh4U7Uuu_t4YGkrNRbc03eS1fxTwGQq5mmeBnUPwLP0I419uOknMZ2d1nFgnFE9m0KquUxCmoZUuWaWQD8ak3a_3f0flps8NookWHjnfCTerQeuLrMW8JWN5_e4q0cAbJic7okt-IMimqA6OXEENkK-4O9yod_HE5znuTopf73kcPPdUAXjknhsFwnszjkSubdlh8kDY1rcKtlV6qXKUcX-gqLdEkuxVG_zk-3R_2qNGZk0UsUOuGvuStVsm37tB5gJ7Gssfs1SO4T08u-2wJ1-nwHNJG_EffnB0niB4xbaehnPKSlEcLn4WTjTxpe6NTap3fDHNzO8i-1HB7r1uZFDsS7MCzpkew8MQFz3FfurnNm8qP9QqYq0IJjn303yYprtmHPtxMtInadcjxwgUTa8RrK713MoExD-YquxE5FMqtuQx3IiX545bH4bpqPDwybx7xes4G3Sl_jewSCLQtbnr4XF6AhbOYxzWxRGdzU7wOS01LEkzqZ-Yg847Kn9RANnmhNAMRj3_6gbiQLkD-YuJ20FVYGFjENwml6vpQ-Mrmg1qwcNeyYNF6KmfVBexxah6sQzV921a6Q13bUksUWeLjCIjuXJAsVFG-g_nrf7nevuxN7iZsvX4aGs6txWPh8K43HSf2TuVtydNC9fcmge951xI-hBNRHDqMaTLsBX7F-D7gZgYzX6-1xGH7vlvbHyPnukFRh0YaodLg80PCp63uraxrx9myaUyBlZ9LyUupalYh0z_4ftV8jcukxlKPa8bgEd0UkLGnds3xi5GNUtv2Pu6LG4dAhUityuAy1S8hpcsUxs8gPDvbx8jlYXhNKsw7X1A5KP7duc5edHcWKfLt05yNHLkkg4otPfdpdZKOAxjv9O9yFEptyU_AeKBXhghtRXaQkjezbm1nc0R7dDvbTUuNe0WVaMfns0d7HQuV9WwEdCkVPwXfnbXceIJLdkECodRKuUfKDC2O90WNSLum52okdIHDKoi1idz3O7rgy1xaaFaV3JGZiyA1qCG2_yUvj6WrvR7ZQXm-Rh5JWojWdUi5UvzrtYA9uZHnnqvJOZufHIR7VL5pFb_9u8tP6h6I7nLyiv4kflAu-YvPUXtbtYZfzaxyUeInsZNqwXsNepjO4zq2lRBguoonfWvsfgvpHL6vPlcJW_0iIXvhT9gutOBJLfxxJyhdOzMKmc54k8yLmHKjRfYaaqUjCGOiiiVbQsKEXEKso6NWC4D32_Xy2hmw8cr87WLTQZT2EBtxQTxAS6GMPqYFIVpKvlp6H9IVZ5iSuGIwZSO5RDgCzD-k3_u51TvfqvOE4n-yLgCgjmV8Afm-J9sC7k3VTf-7o2mGlQgmqXvrH0QV-7O4VwwUQ8QunRlOIwh4o6JdN0TmHgT6ac50tBU2zsegfgNu227LalQ2LaoONxZOKbhsRqPjJGPujNhFnNmJdaBN2aW-vjMp_W_avG9rGlPyATdsbjOfMHJXmD7ob1vFXqoQ4RuAveHI0HCAMRwfJrCTonq3X2x3ZiBIJvWdOb-QdqIZZKbqus4gFfLdXG4oRTd2BR_cyVCMOd5i0AZM94kqJz_sppaSDfVC73FiZnCVKOFXAeyK6U2lmF5EjyLDWrM1YsE7MEs6pYitDnbo1bBky4aFD-3RLQMDr3B6IHw_EuTXYaslDLpR0uzpcJEpqdknJcSJ7eNdUozkcwiuB&�yNIIGD4ouvJ9f6b16OgesNTI1ad643VB44c2HFKOCtpz5ae4yfrV0u3U0ChvFQASSt6kPRv8B3_uTaLQRadu8zaAUonAa08A6n6_vE9Eg3ZGEyDp6BiTpm9urjCXYhjsTb8YqhJZyZL_-r5ICjlSwB6my3UH6N2yt8vOWdgA0StjsngqNrJZ70g818yEP46qcnjRxfM-jW5X6MmuxEmz-xYYqjskkivCBobi2WhEQ8RRTeLK-xKyGgbU2xccU3yozdhpXdTp63zC-ynOs7RO_huZK9x9WQ-z-vTgqwPUuQ6Sako9eHPH2XErGvJDG_9eqNfpjgR7UU1CXTzzwZatFEatwlLG--UeQf-ICNl0qNq38NWctE-Oqzg88yFetfBleM56Asbnlbjkw9DjaQ5yLVjdT6LWG2fM9hZhPb814uWdKK_W9GhLjHJZqLjgrr7U5iD_0ArK5lGwWvi9CnG-m-yJ1V3v4uq3NT-inFObraMmN2sArPl9ky6BrEsP9mqTR4qUzc_aujOmP7fzoWqDuxzpSRcXGqwaDJZHkIl3HgOoDAQR-_aWd2QiNQKQls05V5APX9-3kycZIXCAWGiRsRNmFcMsgUkGM-OsKnvqtW7Yyv36xoB3_4zwk_GfIsd2ZN_YD63wzsgAnlMSgSVfXL_Z4Zyh6XocyAq4Qn6WboJHSDVu-yOZZi5tsNTeqoBQtJQr9bGMjL_01BdwuCWB0nz2sRpsiDHmitUmuRrc5nLMyyyAv342qUuED1DzDTgDTB34nJl7HRFtD_9RZjg6UTSPKGb8Mr5vcNoBtKtPNbBwfSKZT8BPs47L95f3Ty48er5kpM6Jdd1JomjmKEy1L934-74KDczvelOrWbbECV-lW9vjhPN5vkVYSAw8Z1Ks5TdqNO8cnEKy3pFrv1LRefxyfAXcUZPENoHdCf12Q28Y7__JItkUkb5a7F-v4bndjOs8nAhIqPXpDflIFh0KD9iKOYkfBy9VvVVX-pWcoIzjo6HZSvrC8k4O9jk5QNJOccdILXNCYJpfFDa56bRpa2gQQEKUX6ScKaPQNdz65g-_6cvVhTqLoCtFJn9MDEGJmEq5IUn2Te8zm5JyY1h3fkQ8jLZKBd-GE4Yfo1hKRRSMc7ukmRwvp2dT3OW9uvPFGm7kIJHNY83Dp0Hc3vs1_z2JzZiVPztf6rG9WE1mk-PdDdLQPSObwVoCvi-BFiZuJOD4f7e7eZMy9iSU9c9YabGPqQPFnid8rUzQvMkvcp9-kvhlEhsVeT8EZ8IAciQfZyEONXCLKui5tTm0aL4FETmTLD_S_fqWP4s9y5OHLvq-GVujo0hUXFoCH8S5lrrfhkRx87i7L3HdF9a_yC8f6h-OHkwhpIWpB5ewuS4mXvt0HR_rx8uX7DG1Ez5onyGL_hZCmVCO-2vI0cXHXa1JIM3FbDtkZJ83cU8NycA2rUwJ8g5hM8HeLNflY873GNO0A44VGh7TfD3WrXr8awO_EYB55AZp9xl8ZMs7ddVVb86bLy69d5cHTeXGDw05ciwiEHtaNHW-jhf6VgwytN-_dDHSDJIQzCdqYrLMOt7x5N-wkP4a9tueA2mq9utJhuh1ul65_-86skr5pCG14lPHSxTd1p2NLkwHdYRbxc9C0oDXV6Za0o2X88GCFnq8akZ6KgSwmHYzPToq3F-qLleqxPelEXT7E2nP3WuYvW0tfq2tSEgerc_935g9WR1cqiBjjLxQBmQCxTRuG4oLLI34gFXnjcsdpzhPzTRI5f9K-yre-Rrcj8rpnvLwEy9A7qrA3mQ7ZXpnVzvojYjs20Hb3_kxc8AHZKRWrxvhC07XI6Zegkaz8nS0EYYENr7RxxguK5n3GUJJevj2IjhLWhIeIvswRo-7MK2kGDnLkgV4wcyaxKI7Oh0jn9SvnnuSelEZ_YdGC1qdW2vGHkL7WmzpG_A8yXMgx-eZUp1I7z4oR-BTzMcISmNJc6lx1mFzQbirPNDrOkMEZ8TlmIRhlNio3xj3TiP4RLLrv_qAukdfxH5D4Y9bGWPgWk1PylanbkFrjwaSbdRpesz3jnu4HshbYcozrL6F7XVsOU8ERPshv_nq10fVDWhWcg5YIZbuDWbDnSOc7SgnvNovpyQAohZqRwA6R_YUNRNrOXbIFZr6G2647u4ADg8t9d8lMXx9wakgYZw8VzOZEgtlpOIVNZTwSlCD-l7emND2kuOserHwKFcghbI5yKACA8ZnjI7MDIffqsu9CrvVs-Rbg-N6yINJ6JAzMaeu_Nwp85H9PsldrEhUWI0dGOIOdtMGVRxPORvsmpg763U9dpq1s919-bAR78R45rRSdfqwqcQXU40f7JP34DNofM2SLnUMQBdJ-bHMrCXuVcssn8QUjjt3dHXrQMEg-l67V9EQz5ZIdlpJ_MzuDfLbFYnEsiMgILYUBi3atZDzOtDp5FwVSznVi4Z8YxpTHqpyhJ2fgK3YEeGBwuwlOxd18i3KjK_DkVBHTnEdeW0Aujb5pSo8TaNmMlyQg4N-24f8yljfGVlP432OGMEtX9bagySe240gjNBapKe3xipbTtXjfSesog5fvyhqBvKFjTofjgfGIVCRCHh8T9CDnKt-dLp7EpHhNavi1xqUbLBlpn_IABj8iHjIt4jndMRBFkNxs7iBEP7OOSNfCYB_rds-KmLHH_BQYAaH4IwLUNG0Fm9vS5pU-rJdIgq0EsDvyrES0FypFwACZmc14tRZcXzO0yuyT3P92r3snnS14lIYVTON9Uf75sNdvXhN5K9zmOluTm2m6zHX6_HYeVcwUL8biuwrd04lHNvMCbi-9xz2hzcabOfeNdt580FdQntnBNR_0h_AXDVxoeM7FNmel99kXd4ytygK1hrYtLY0vqhY0OTDeV6XYl4mybqtW7nq8toRPhhQYP0HgVg_MeX363Dqd77DM_OfIzKM2BoKU4E6QAfbMp5yQ2mOT8CpNwZPH6LyzWs-cWcGHLMeZafQR_DlT-LU7O3cYoTRkLAYWG_3JSMDKPNTS9y3Zi_JN42Q8oFjmPwHdW8Fk1NOyDSku8YProICi-zUn9ByioYUiuJB7mw5EgdEHL7nXMHkOdSInVZoxA6XkVfzi6zd-ywk0E3R2sHdYPe5ppBE57_n3w475ytiXSumO0jKVuPQkhZ-Fg84K1OcSCnBGmLp0jMDVQUIZDmcW5SNZpgki766PwJ-TZq1HLiQH4kqFCp7UkUx3vK01ruNwHCxd4KrHrDYDSg1GSjXCY1KTu6Otvx_DCX7oe6biUnZxmULdvaRTUlplIG71PJrebrhQo-RdpmiQd4TTzxZHg9qG7pf8pssRtXq67Quuqh2sDsSFCMVLVFzSxsjh9wInY0d7TM3SGf1aUmVIJs_DoktYwyvyCAwZ-Ua1InfwVZVrGJU7AhOd-4f1RA_RJ20-R_29HcFdKVWFn-3jGkJ1I-w23MyBgiR1w8TnaJdkHm6hCeACv_LmXbzHp54Opfqh17jf-gPV9PQTnSMCg7OK44UPF5E6fgfmGw3bRBffk8qqFldoCjTPYEIplzzgGK8KT_lu7GGH9dEvZz8_2h59cgeofIjPkdeUseMDogBPqq7QG_QGEiqWYLfRVx58VoeUile-g7uiqjNP57ep83QD91oYUIVTkU0Qao1iKqurAhiu8aCdWNVvPd6RStlggAG3Eb6Wtt0ltLejX6zP-xuD5Zuo5fj6Y3aAsVkiw0EGut1wQDm7Q80NfZ2oQhAvwn1o_utsxpzYKFQ8huM87MXSW7Kjg-3VKjtrhY1OIQaRndGC09s9qM3PEzT1nmhBf_KojM5Oq4x8gQ6lNgowOQWHBXot1FSpVFm34Untrro1Lsl9OWT9d4j0aqWSFt3HlQijTDkbeqsB5uZRE2D_-bUAa1Rbxbpu0kKbzmVh5P2Iz7F_2ua4JvPqQ5KqQyw_z0jhK-95nNy3pCm7E1Ucd0EFlTYtYPp8DXPWTQ21uVS_CAjFA90RjVN_czpPn8bTIc_cNPY81ZjO8Ju7Dxkh6QjskEJnnM09X46eMhDstabFY0LfcqfniHd8eZosHaAGzsrnlVvHXxHgNGtTfavaWGl-Me4nKOD&�WepJYE8aA1W3ISq8fR9uHyd57PnemN2RN1GL0vRqw2VxSDuN9wMJ8nwMmr2u_Q1YzjpZIuEF3zY1fKE-DQDeadz7Jh66XNwpE_2d4ZodmSbHgULsETj18iBj7fJyl38mPmQY0pC1FCcPAi-geowORXjAV3F4LDV_mnVCEvccQflMz49bjl3HmMuv-BadTS7rHK1qHetoQk1vBRlLtG4phTVnNanbYd5oNNuw12kpcDIYQT8IfcTshv8Jh1LNG05FUvVZ2Tf4PjixgyDh8_n27Y0oD4XkoOUEYChk9A0PLtmNOEveY_JHbcvbTiKQfaz-VumFPUpkNNFGYXMGFy66EmG5zIyf26TCWmLZ82QJz2Qxb_H1wNZAbBN5Ku1yd5_xRo_7aYYBGK2RZAf8lZ0KPvzImJf-RsgZ5-bJTo02TPGuidfVXlJW5g9Fsun7lWdZu0BJsxQKeL2IAuEJBeLqDbubbVPOH9VOg_pCZRJIgnydFIZQmv0E2F6cVRp70sTf69DXii4SPF1qto_Nuw3ojojZhF02TOKGiRptDIj0UYvXopWt-w3lDf7MVjaLQjiVdRO9TNbs_4PzgD4grs7eOB1VpFQfAntMcCgiUB35IphO18rfjTdTl69iw3QHbZxQ5e6AppbOu8Kvfa1GtbzH61ujUM7N5PLxhoB69_cTb7fcr-cJJumteZeEQz8Z6nBtqa5_SvP9Yn9Y1FvqgzvIKMXVx_Uij9D0ixpWEv1qKw6JrSMH4F2jqUL-oAXYl6tVw5rNoTfJtKQYzRHK6KhPbtu2vli3ilBZTyN2owpkelFw-Ke0zcKdGKCiEcrcTyFRUlzHI-xkrQ7TfxWMBW7UM5PTQVqtbd-m1EQgX5yXb-rKeoGpTDN1w7plOs1kV5NGffceMc6C6tYu16qwNctmTG0irLYmjAfvKm2upihKkXtN_DaoXz0IbmhfyhjHm2PQxICrjC3uZUTCODJ4oKVntS1ja-nSDVqL9wQ9-anoBO2o25omYn6c0dIaOUcRueWoxqMzB-2OUj36y_FUbAyjSYxTmYFJFY6LStG5jQZ_7FNX1gcQXrLqH2-Ii9xzm177yAWyiEI5XQnrWc5l_U6QXbkPTXN0vqFMusDSSt66dMUYSyy8Liq8UgYHW9UgSPLoO5LN2OR1SzrBZKH4ZOdTjtCY2-5qvWFc2v3IwyNpsm58thEKBuDbzBIlCGrGMvV4McR9QXOHCIzIhiKy3kksG2jruo1qWnX242W25buOIKN9o5bJCrgXaxbFr_9SB4EYYEnBlVzf-lhln29Ckc4wKI09mHATfqCVdpmwxnZM200PAZXkKjWQooeLpDgsjZOEGeOLAmJDjzIHF41A0mA-gKA9Jepmnry3ghe4y5XUzLSppvhTxOwD6WyizKgWSnfWVTAanu_EinLkKdExoVnIgIJY8H1qxPtTHwvAwHxpXIak6ib_h7irryk06SGUj2BZ-fmwVK2TWz7koNG1_P7xY53Yu-2SHvjJ24jkYwZu9FPpE-OfjN9GiXFcQENJbVIEUSrU1udOmWmgYmzVdzHNOmSQI08Em3Tv1X6LNTU0WUif0P5xGKJ26lWT66WNXWm4nRD5IeoZmjTbel3PDa8H9cpQGRuNeav73AeSsjN7JyE5eCovpva8F9q0PK3T4KJDMXuKgr1W4TIREKn9yHWIWQqFVdaIH3oQl1BDGKkAecaFkxCiRYgb_SQM0sbCKv_Y3rXxNzhEIMp-P1B4wS8FBMVwWPpqMdSQMo-SKHlKzF0mq8bHwBUQnmE5pzG9A7D4Es2mxGfSMtXIMjBXTIeXdGQCxBpI-EQA5iD201xODaffGAuB6rRbx99y1jcnUSzsj0Fl57rulSXU8qiWuri_Cimvm5-OzJ50qpD-Gw12Vopld3iBnDA8lqBJ5_EG0qpW_lGX91L0S-Ah95Mxfu_eDIof3zuPbvCmSJTm5RkJwup3VWAeMEHTCMiRdgNLvCZ4qpUde9mEJWbT3GbHQbZU63HpBUh99IMCJLwrbyK_XRCSHODCjjIvoID-gATZeTDIgiTcIE4hgdYfhSnvs7TkX-j2A5O90zULSrFJX277nif0MSfPs3xYwvx-TviBptRV4ymejS8zRMGLK1-i0TwvXIbVdYQ4mTXIemjYkpN0neAJ-_OD0SDHGZ9DV-ElRng4zLhVrakss5I6jmu_yM9YSQTIikHABaMmsfw7nrKkjieVSIL02ILbhY6xZgmU6_ECLHUwU9PKtMOZJCM2q962cBpYhoLhMoLBz0ERS1WjaRNl4A5DJ32yUFriTj7csxIIzDK90-8wqbsiPnKtOZfAV81QzJAyALjiXEaOKwdX6IbBnCixk25J5cx3r_yTl2Er5zEp-aOqDmCIOHgceu-q3sT4TuaWD0xjiROR2Wf6uWL_7cbEj47ysX8EEi94MSRZpi1hc-mG7I5E-IF2js16PAHxvZehIViNAmJKrCQa0bCD_Fyeel7I6GZzlzjxmLYePWYr-GneICuEYL5XLuMfhcsCEA1vvtecmSHtqWvRaANAWJ0Z_cfSL-FWk885J_h4vHapIllAZv_-wxFJHT1774TOni5gxjksMA7d_0jQsgNO2R_fRDn-OrRxNnQnDViuBR11a3NSvFSr6VAHaHbo4CtUcZUp9M1-bdVNvzyUgO0yMUnD9McfFZd8m1QvL6u4UkuBmflv6WZ1XLAyOwfENqQc13HugTNQFNvW_dUJv2YVrHMvzue_kwa2KVb1PatBBgTy6O5YdOJpsTzpyOC-OneXSP6GQcH4PfJooaVNOLiigqYTf8G1K8qZHNuaOIhmHBjaTZEHgBL72yeKrmRAq3VX2oiMNsAyJb7kJqLH7YLLPmCd2ujaptsStAffqaZxA3YN0mWDmj8p4VypVdsZlYpidKn-nmkj0rA1k8odOXGzax7waa9yvhNqMB8t9sYDv-gf1FtNfjvtgPbiEQq_jtJGG0b1NiIn5U6hP5n1IE7In1tWWF5sUlMf2AL71_w5G0jyixbrQiP6t2AF_IGbb3EkDvpaLz4Io91x1k6dMpNucVhlhukKWRmHlo8srPlM0bJSSC0FyCsN9ax-pu-kXgIfaVKq6Ar2A8hfyBg3ZK1B_10li5lEXDKwo_nKJVL5gcu4bZYUQjvBqQ_rjGBli44kYNyPTJHKDHU1rrgYEjuKb9L-ifkq-AT5n9CJUeLVBh1xNGDoXx5Ok971cZWRV_kX9zK7CwUyO5brG0X7x06h2fFSDm7697qsRpDE-7DiuXGBCnU8alC9sEYem0LIwX89r3R6Wrs0pznKhJ3V516E93D1qr8HzQDB0GT6g8-jPbSGAAxuGnJ8qqWZ5eYFThc5Ciy_NpMFuFU5ixWsru6mTuIriaABYw1B-Tq9BeeAD83vSXbhY03Hrk3MmI4fig3VCyIVNyqClhg2z5EbDnPr0ct6zaES1-kIK9Ynj-oFjXm8CoSkEKuGnvzoV3ae488Ap_trp_Rq9Vydebzs7UF4REm8-UhSFXNceM1IC0-wbQr5ri4NZor2XqdDqYZEvvKefylQyyAdSNM9dmaE9j5fP-d7yrgMPFPv8u3EC764A6mCGqjd3LHNAKnBPvs8WapM6GxXgMoyCcXYQaxce6OU8xy7qO9Cjhvgng-UVDaPkyNMZYEsI58q4GCdZBPfjR5q6U93wS8W3GNlyDn12yU0LfXAoHvQR4xYzzcr8OAfaBJVHk2512S9knEi1iNPE3Q9w5QtPseNvr-lT3VZi9WGKdLXYnNzsRhQoUa0yL5EO05WBcLkZxwgILy1Y0nb8arklUQpSX2Bj2dw3KJUhTFSwf4STEUdmu0Xz3lcSnphcIzHp7Xdt3TrDZm9UeTc2OS6KnTAq1HI8AUB9kIF6dVVO1aQuilF_UzTOhrAv7yMompilCjn5A60NTawpdQRELZ2RP2sx0bsUeKCfJ6p4t9ksUZrWlPbGQgT7lW8A87ifE67tEAhj3A9JTBQHBNeyN6vcRav86VvfMP0jHHcy6uuYv826nDUS_RdyzFjZZMn7QI4wKLLEkjFOgTNCPRZ2FiyLRFdG00WcjPNjGIzk7IZ0380UJo3SnwxfYc6&�z7Rc7eFoujS0AOdbbgfTEq3nNHPMfpBmvE3WF_BCbWP9X2xG5dKBW7rzCWYPAjMaVVhDGnz8ZNOWEV1V3Dqka-pf2Hl_Wu9-tUjWwYmoVaL3SQVzOB8rOrYE7w0Y68J8XNFVdQIbr7DBTle-xZ4cecq2DBFv3JXrTnr-XTgTwuxSxL0ui8yKa73-lcrEJraxCThfc49isIMFnpHHtcRegC1L4Q2_-tEcM-4Oo5IbU4yz0RhpkgwWFTYCAU7uStFcUiaEAZ-ChOdZ6HQwhoXzzH7nWSMdg6mfYwtnsNftwRiwWujry0GCGs2RPn1CCplVNkVMHTpOMqGZ3mday-TdkXMWg_L95rjAf9cB8ro9c5OxpfsKWWdrTe_wX_egTMoMWhVZoJpWwztrGa6Kjn-tCPlp8LhTObcJLe_K6ZYh_vBN6ocpMIRzLD8Hke5eQWbtjiH28qFl-2Qxuo0-dpooG42NlrrJoGZID8Vopg_PeWGi0yZx2scRXKLXy4eCiCXYkO99p3Y191Vw_y0VvcZ7sCLw72rQfz4onVPjoPTse2nQgD0TF4GfpwX1c5T8R_t4KgLQJNjE4CgYDa7I0qNMbEp87gJh6SqzilWVMt1F0YG6lP3C1OQl2CdCnrJBrdX8mXbPF5dGbBMBRv3YKW5GRbhXnm9pFp4D5FbFPlKb0rc_XGDFHpfcDaJBMIUZW8rJnT1_TH0lgcawmnw883C4pjPdU_GfQk59sz5CfBKZv93whD56zleYjGtKbSfDg-SgK0kxkDUaL4Vh2uCkQJfCsG1q7C_WXislzviivPmnEtxtl8LHjMl3e16phzvPu2dG4ZTJCKDYm3StnwXKIb7SdTSnlfIC4e1f6rgaZk06gtGcD9EF_hUf8x8ZXXEdmyvSb5bUNMbqKMjdxpkoqXcG1KPHurzgjKtD1aH1sIDW8ZH_fO3mws09rQtC0G2S8BQggZIxveXP2lyR0r0oV6yjLjMh2Z0UKzKAhm0TZfA_ihvE-1iQs-DeyZyUHXQfv2sifN6rPa6hCuOTgeNVUL0t_cXB8dyLbPYsxUFVLjwq8nRtVV6kIvKXRcgI8KijsoJTvmtq_4u0b4PHNYXZdLySK0drbeHoRjDLN1eQALYVol7Pkn5yYs6mscR-8bDQCQ1KM7-O76FxtGV8XNf15vU6vbXO06WIFX6rS5qICavP3umjJG1G-fAxj-RBMrysT6mTnfkaj2eABNKpkg3tfUUeJLSH_lfOmhXAu8bmxG9QvxkFLSBEqqTWGhWsm86qnVeg0A707uQBni1UxNlA3_PuMbZa8JFh7QXlH-pSfCExqsxTceTeUTMyc-5PsdEp21fhhZ6A-Rq25JrBpyP7clRdEMazpshKL_mZX-bffJOpTyx1OO0xFEXCLUjNKJP9Zqd0F-t_V_yDVaj1NHP1x-QEeiyN1fZ1Gmw6ywGNmj_mYf8s3y2BdxfmODADkDaRuAmQAGKxQyMjae3xv1ReHFOowba6JNgxXKi99uHhAh4VGcU2XOwUnuu69kyqVEH3GmKa884DEzjmuhtplgfWs4L2j8kSZ4KZHFVA8jyJO4UEBIhuT7P7hUuKpoEU9LK8u6GlmAfikvojHuMzTazT14x8rHH-VC8iyk8JmamVtds0sEI1qmDHRP4-gyUU0itVtDACOzvDxaQn9FEoCeaqjvnXG7mw5HhHUpa2jm4J4OKxbl8GINsWB5Lb0uLx-l7y_KR_zG38hut1y5tskiLKmlXbStQ0Kz11WLsFRhdqShWclV1xsCPg5Zdhbnng0_hhde-qmZtV2lVUA9wSBbxNHgF_1GBEL-ozE97K47CihJ8E2vMniYI-gEfWXx_EnKHbEnQRn6c6CiwT6tkzhPxQ2slmO6y9gnfyoDQ0lhH-ZWRtQx5FN6tdA9dIiV4I5xDpQMGUxKJbyTYQp4i8pnKUsbiJfwCwyTAVCKnsB8ikAYzjAU0xr48_B8oQR816Jnxlqys61ogSml73W-K6cJgTXp0bZvAy59eHmabHDqXOKHJire-82c53-FmXoEeTydpJq4eX1SS-O0dYo_7h0fhzuBJQm2W6Wko0MZCUcreNRszA4aZCYLPAuZdeoCpZui6nkj0XxAqtM6CBLnptCO2trwCUXiYFYFz1ElNR_IUEW5gCwBE5aU58n12Uut2JpRSbFftQruG7GVPtcLyZ4PLG74eTOp_RreN6pAC36zPcGzQoUaIPG7Ckak9mmRPt6ZikYmagGVqKDqEcTtQaol0le0ZIem2iD7IAM3CQlK55lbkZjq5P-wI5xrFzB7NciNrM_SW4iyL_sDwwkf7z7duLmKhz4B50oGMFBago8nf6fw7JDcjWJYNSKxIYfZsZ_yqjxcHX4jP5VGFTc2ZWI-qvbUqpzIr1DWvXJm5srYWNiZvQtY_8LL7cZB2RXWeuEcOX8ONhyQSx4FHvizKYjI5o_NeUeryTNBoyFBNU2Bk6B3HGuvapVkv8ffTwmmvsSXi2m4VWqNtblpab0DuqXV3QBa76JvF6aeZRBB_NcNrNG7jOpVpS70v4-lo41sfJheOJ7J595-ABw9mvWPaAVafSjkQgfsI4vSILEpIai5-JbnY04Vn6jxpFXFNSOTeRDcwKmYthfkNYGgtY7GG4FsMY-wKE81JrzwFRunx7KkV6olHALHmAYPX9cPiUYB73jqd3ZG-u445pp5Ax6RI5yJwB6AilnMxMbR6QGvN89jRIT0f-QQwBGKf2sPTMWfXVRIxbnoZYQvSyyINyBKSp9sYzlGmUyJPL5nBWwBwz-HIbLuOf5TDupj8A0FpO8veOfi03mRn3-LgzoiulkWjyqrcNT5P4TFH1rp2DTgKqfCBOXWrpRr1OqEwqpkEzKIrLnuUR7fvMnvpkEPqVLTEqeJrUOk2kCrc5X_nLo8BlxQfzrk56d6OWHFW1Nnm_WyN-p_vdpL7bZyaMgD8_A9UiUAnglaXi0WyvhneV3efjqZ1UYD2H-4z-7Umu2JA6aiOUNwcU6qSzC2RmhHeGrFRBKv3d1HX_0HLwbkcYrMdHGEUHC99Ps65mV8ohqzN084OJaA_9H1J7jvsEsCVOqQgH48Fhi-Cy0F-EmpTot8TFFNOed5RhJdwk6VNhkX1wcYbgG5DpBLPFRNjDRFJ-uB2TaNqwI1h4nQAOmcIIFq_nOcud65B2GgLkAQRPOnxQyTRsItPODfN9I-0X1k85eoj1VT5JV6Fq8DtDiCYwc2v5lNmeSOD8YHLTUUqFro5ePAHQ-4WzSTjdxz_uNUyxz-hDIA9pHgZSMYT-KiaPZS9Vib2dqly1D4ZYhKjlIItQs_Xlo73iPaePoni9rpgQzXoEwyaAju5Qg5CWrRlBWZEQ54O_p4i-R5wwSMQwJXxUtDsf0lKZPOFJa9HqcGmzKmxjhX_9F2w6GyFWCW_ABTa1th2zxoTN4l6CTIB6PumYGyY9d6jIBcdZNmotIjvgTpysyh1tqa35KaLJuR0r5dmaZrqJIOP2MuNcTANph62Z9ySvfsRYIk0YZBaZGyneby-kKmn2GBurY2xVzJMAqIhZJFEVuTV2SIr2ocG1WyI9Rb4GAW6Sq4hpTnNrP8poZk5mCzQPj-0VmcqgtWniWhfkqhXX3wlXkhI1bJFQVp8Rzs7Jim74Q798i2FnoUcJQ9zyEV9Qk95TEQVeRVP7CHqSHksa2XdWt1ybKJCHd3NVey_HQW5-FleZLQKdx7A0_aJHGc90TI3FbOzpVcsN_EbmKLfg5b0l9c67cy_uaarjFp2cjH_mUjDz7TWtcex6NAg3Ka_0tAhn9bw-ueEOUyF5CElU0YURCGI3VtZ4Rer3xlLN-Wc97strsmpo9JaNSEZ1tczibTZG_lL7CHQnbfc0sG651KPX1EvG391P2HvIv-_qHBAajIcmneewMLR6BFGTNuxXsqYHrf57tN43BREAOMaHST2mSei79rKbP5v9xkB_H7Etg4UDvWekd01k9E-c48RL08bAzVuOocBoUVbvfqusx12IHO3oS-DYxn94QzLvwwxKu1ZKPlEpSo0X2sI7nEbqF6WWAATn38aAY5SOoTpcwg0RE-RKxpE7sLGKuFQ2wQPn&�5x4uV5pwXRIX_1vSt6D5ZA7O8UQzSunp42fhK4wVL-NbS-AA0P-wcYcD6UGDqdo4rGzoakKgg_JHyzCNTx34p2iM6ZAd7tmEcPjHg1u_SfGZNGL4pwJjA5MvkJVAANkH2XIC0lalgT7Y9BeE8PNw3q2eciTwp2vjG7aISAsg4D1JPqYfc_o0PCQVvyZmlDc9i7bVs-cxQSgLkbuZBZfepA9BMBu6bFWBOr4TsxEr4HgXTcmV6itABsa4xW544KCijBsXr122dw8QvNX69ZRlnDxe3OxWAxBvgCW_-WccZ3Hni7gVDXMJ6BDJIkWKSqhjPQDCEYZtzDqXJsU3spoXBmKUHmZI59H9MJkay9L7PqCEA3wGV1tBOeqsPK0bnO7cg0NMnlVWMw7mM_TiXXVQoGiY33616fBjPUhU6OhFeQ0272tlP4yXF3X2lWeqzvgpb_LTrMw_-E9SJQrPgxvqxPYQny6fQ-pI4Nu16GF9vwim_NDVcxveVEI6GdPn0Nh7_zsxE823avTInRzjduL3JlB5TYnzKW-c9TwqvyCxlP8WBmS6R9veTdf2k6hDk9okb7ie_GtVN5dUyoDlvUmdEneHd9sifR-dzE2E8-me9OUWdyy81-TIGMKI5vJN7Lf5lvdrnCkwnwR6ZKhVIAg6aNbntX2Jl-aShE3ykmlHOIpi9MMhlYadhIJrrpXZ5npMjOhvalgXBSOHm1UUpXuzPHck_2wbhKUvCU4GyWdwY9j8z2yAwuyLGM4g-QoZMnPAv2N2rLayOXF-ejb_I631rhEGiHbS8dRSOu4V70x4vcYKSq8nuH4yePFORtoveJ-bx3r9BAE42iu_S9XiznyV1rWirqQIYfAQhOfIXO-r9BP-bt1R3TjR36WD8PWKiLydhbYX9SWeewJAFmSZyYCjZ7aFp3UnMD87hcxartIt6RrzxiuFo3mS8xLm-wwEqs5ht9V-0hm0w8B-lCB7_BDE3GkVLmhZX1wYFxTM5PA7ORCl76F4IMFeeRNRAKrQ1__tjJbflGc_oyQq2jzPvFWqQlpmohChv1liw9yoR7ev9XLQEISY1tgDreMy-aq72MS8jpj-sjPXgibinBBN2un8wrDwpSSwoEJm6fZHz5e0_T3ZIjOH1EseFzcEoR6SboxAF_UH6-VMFR26F2EkJZ94K3Qu8FR9_AvxSTGNTFKJ3KFuVgnpZtAKaIZqD-sq6YqozLvwneTXthlikOGfF91b2NXTEDRwWaOpav0hnMi2eM_4RHGpFGGse-0kPzI_MtdojcWwKkgH2UswBiboA28r3bz3wYZfu_fi-FbSiYXR0rURJAiJyA4NBKi15q08mdBPMn8wafeJvErjylGCIb0sf1qeK3VHUzLV8dsA0wnW2uAVHXrDio4v8-H-gYQz5zQmDccvv9t6qKyq2P3b9-inMZo7LDZDNH54hL1xxHfmoiB5kDM1bc8ojU_bzdiXR_sYgZEX1GtNKjqfqDg2S8CcuGO0tPfwdnVMLNPVZEEcbymn23VXcwlUL-g9SCHUYd1DXwbvyVBxFF_Z9xAPnSmUImB9fpku45ZOIwgeUryS4Ss79N6VtVnLEDWWGSBhy--yMGpjrPJmF_SVKjLROTW-FPUesYcWmKhygvitHca4ufc4vZ9Jnwg863gP_acd41a4cwokGUs2ig6kglosUQrgGwmqP0jHf8piSdNCX1b_5rMNFSgLIgZGD2hhEsFW-EviSmTWyTC-v1d11I2BGXunA16Cz4od0DabSmD7xZFkmA8rPGB5q7f-vPUKjxfY8UjxXnmBGRZrP32Ydn1YaMYi5X3lSWrUScEqAV1k83o8mWZbeg6OqnLR0tjchAxmf-gXuEMeCfQv94SSghp6i8nKO8P0l6hYpAFbUOGY5GCnY8uRKzws-kJwaeReonP8nqJaVaA7h6DDyhRU_XGK7Qa_uV-Z_pcZxeqlNkYl0JISypAJlGOlhEmW8b-UzcHfD2DXtE2o07QYJzoMd8U8d9IDoi-dc47l7Ws_f281xeheivJMJDD8Ijb_Qd2lzjZJKfrLzuPDojfXp4orMMzlNOWw5upPlbni931sHsLYduivH_EFYGhfoh97w-sA41oJm2ewKQM416mowOv11tE60qldba1xCprM54KM_3QnIKjArRzBpSpS2uP6R_DJXXadvDQANOy-MYQ4p375S0y7t3jopAnQ8v_gHLVHqFl9KIh4nBrHzzMJKklJxva5EqcOxVu2b-v_hAE_pNnC5ihmdZm_gENTbmfm7iAwngl49fG7BReukfvmfwr_9kRKSLu9rkdQthW7AXeSwNRjAcRvlAJZoAQaTsJc4ukeEuGfKAyl0h9uedPmHfOehwRwAj9pTFH_UFLrYaZmeKQz_U0MHKwfUhQb1sR9pqb1TA6LzB2LX6ilsk2lidzOOz_W8N4of8egOkD1CbfiktTEoNS236fkWqNFQtEH1XoImoTFo1bWN2VTnKvQI9qY4FkkW9vkayEc-m1bo2QmyPAiolHc8PgdANAyj7y-CqztQbyv098g0kIIEnapxvi5YbcvPdC600_jmJoN1HLllDqceJvmUezcXjepwt84leU1Cm0sPEu4Bp2qVY7vzrhP3x6fd0M4ISabzs5pZdqBoZOLk7UjjEmBqq6porBRo3AX1huILUQwRxms7NyZWg4uuSSQxdMkqCH1vwvfPXgYTbQiimi5bpxoNr-z2V7VdXvSH1YvYAYk9HEAWa4ApVJwPK9IKhr4oPbK3tFDoErvmhzJzYqwsJUFRj-EiXr7OjGc2P3gaSKPpJDjKdh7p7augZSJYR5JFvtc57IewWk3NKDd-TU8EMN67Ctx2C0UQrA37QKkfjrOaBvvQ83Vg_2T2hIugOFYV67S1sLOTyPepRbqUIGdA4KziK9uNgAnKSDZlU9H_qslg8HtuiST7cjsHlUdkYJSZAVpV94deTbh30_cBaXJ1t-Ht9yWoTKFd1eazM_ugaWojGqYijcU7FNQXt-btt_FzvWTwb7gz23D2eeMimbB7l8Ei-if5fhQ2z-pkS6a43xZra7dBSC9IKSKIhBYxKKdNZwNtJDKl_WvnDqemJezUOYhqBNs2H5CWr5Gnc69cJlihnNpOrpjKZV2yz5L_ObDcsBgkR9nghKMWi6pGYz8kOS1875hoylAA_7WJeYRol7fdxzPsro3GjME4IN_RKvw7o2Hx7VnOcnT9M3XbZalZRRZSFHr4Ews6dd3C-Mwvp4eCLjIemgf11Z8LacziEcwkeMahpAXj2_8iMFk98i7XZgpTJfn5VWxEYBxREKoKANv5Q2h4XytWvdbL_XBzffENzhSd01QDwfsEzDSXdaLqhbKVH6dwawj4KzQbdYRMmQRBq1eitmD7IPD6Nk-FBRpqPdHXOZZqk5w_56YbBlBVbfK2sxgFRB71EVkaocShwKuGLyPBkvdTwDSfeU2iWWXeUGCifIapSuNvFu1i8Ww1TfMhB2vr9p-_zoDQwHHkmqHQnP76ZDG4BQ6XdZXThO4_98sATmhMOEg_ImYbz_XkMsDLlcLrZUA1DfTkSOP_mu8PONRBe3FFgIBfpiIiS7fU8XEcl9UNJGuDsheCVT15LOKiGhKRqzeLaljnDPC8SuEwWbRJYHf9lB2abZYF-VY_9K0FQC7dDidokNFsF_qaNvKlYlWjkATV30UEyU8xWA4itlk2dKXmG50rGt41CKpe0EMKzWnq3CrGVWo2IDgMK2KuQjUuq5d8F33luB_-ksyrQc22XI2dpWOn6VpXWh87E176FMBx31xPk12zBU-gHz1Wg_5v-Nk3Z_gz3ObS_AGr0KTkk-teIiQmKKAIR-ohMCDBhY48MkHJLPjp36MH6fzaCOuSuKP7AmoNmrzG3ojb03RgqaxuX35EO7vDcqWZ0YF5uZBJfNcA8z_OYVswhXQjhOUk6PtT_srvSXskKtLYoEkdA-488WuQstcep6z_WIFjOQgq6OEmV-MK7zRlnLtYM_sOWZIBeQjEyRc1IRCkyVoIGB_opNGwPqOj9V0fXN4RPP47pB0E5XoF1pPd9Y3YUAT8ohFtM1NgKwWJTRrLF-IlNkER5xMskZNEI1-&� for key, value in node.items():
                    \"excel_day_padding\": row.get(\"excel_day_padding\", \"G�\"),