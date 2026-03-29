    FLAVIO_INTERNAL_SEARCH_TARGETS,
def select_targets(targets: list, target_keys: list[str] | None) -> list:
    requested = ordered_unique(target_keys or [])
    if not requested:
        return list(targets)
    target_map = {str(target.key): target for target in targets}
    missing = [key for key in requested if key not in target_map]
    if missing:
        raise ValueError(f\"unknown_target_keys:{','.join(missing)}\")
    return [target_map[key] for key in requested]

    targets = select_targets(get_active_targets(), options.target_keys)
    if not targets:
        return IngestionResult(
            source_name=source_name,
            source_type=source_type,
            candidates_seen=0,
            articles_inserted=0,
            mentions_inserted=0,
            stories_touched=0,
            errors=[],
        )
        candidate_metadata = dict(candidate.metadata or {})
        force_full_fetch = bool(candidate_metadata.get(\"force_full_fetch\"))
        exact_body_only = bool(candidate_metadata.get(\"exact_body_only\"))
        require_published_extraction = bool(candidate_metadata.get(\"require_published_extraction\"))
        needs_published_extraction = bool(
            require_published_extraction
            or (strict_window and candidate_source_type == \"scrape\")
            or (strict_window and candidate_source_type == \"internal_search\" and not candidate.published_at)
          <summary class=\"story-summary-row\">
            <div class=\"story-heading\">
              <span class=\"story-toggle\" aria-hidden=\"true\"></span>
              <div>
                <p class=\"eyebrow\">Historia principal __SID__</p>
                <h2>__TITLE__</h2>
                <div class=\"chips\">__TARGET_BADGES__</div>
              </div>
            </div>
            <div class=\"story-stats\">
              <div><strong>__ARTICLE_COUNT__</strong><span>noticias</span></div>
              <div><strong>__TEMP__</strong><span>temperatura</span></div>
          </summary>
          <div class=\"story-meta\">
            <span>Primeira publicacao: __FIRST_PUBLISHED__</span>
            <span>Ultima publicacao: __LAST_PUBLISHED__</span>
          </div>
          <div class=\"story-blurb\">
            <div class=\"summary-label\">__SUMMARY_LABEL__</div>
            <p>__SUMMARY_TEXT__</p>
          <div class=\"story-articles\">__ARTICLE_CARDS__</div>
        </details>
        \"\"\"
        .replace(\"__SID__\", str(sid))
        .replace(\"__ARTICLE_COUNT__\", str(int(story.get(\"articleCount\") or 0)))
        .replace(\"__AI_COUNT__\", str(int(story.get(\"aiCount\") or 0)))
        .replace(\"__RAW_COUNT__\", str(int(story.get(\"rawCount\") or 0)))
        .replace(\"__TARGETS__\", html.escape(\",\".join(str(key) for key in story.get(\"targetKeys\", []))))
        .replace(\"__HIDDEN__\", hidden_attr)
        .replace(\"__TITLE__\", html.escape(str(story.get(\"title\") or \"Sem titulo\")))
        .replace(\"__TARGET_BADGES__\", target_badges(list(story.get(\"targetKeys\") or []), label_by_key))
        .replace(\"__TEMP__\", str(int(round(float(story.get(\"temperature\") or 0.0)))))
        .replace(\"__FIRST_PUBLISHED__\", html.escape(fmt_dt(str(story.get(\"firstPublishedAt\") or \"\"))))
        .replace(\"__LAST_PUBLISHED__\", html.escape(fmt_dt(str(story.get(\"lastPublishedAt\") or \"\"))))
        .replace(\"__SUMMARY_LABEL__\", html.escape(summary_label))
        .replace(\"__SUMMARY_TEXT__\", html.escape(story_summary))
        .replace(\"__ARTICLE_CARDS__\", \"\".join(article_cards))
    )
def scope_labels(args: argparse.Namespace) -> tuple[str, str, str]:
    if args.all_stories:
        return (
            \"Historico completo\",
            \"Clipping offline com todas as historias\",
            \"Arquivo HTML autossuficiente com todas as historias principais agrupadas no banco. A pagina abre filtrada em Flavio Valle e permite adicionar ou remover outros nomes sem depender da API local.\",
    return (
        f\"Janela {args.date_from} a {args.date_to}\",
        \"Clipping offline por periodo\",
        f\"Arquivo HTML autossuficiente com as historias principais agrupadas entre {args.date_from} e {args.date_to}. A pagina abre filtrada em Flavio Valle e permite combinar outros nomes localmente.\",
def output_path_for_args(args: argparse.Namespace) -> Path:
    if args.output:
        return Path(args.output).expanduser()
        return REPORTS_DIR / \"clipping_mobile_snapshot_all_stories.html\"
    return REPORTS_DIR / f\"clipping_mobile_snapshot_{args.date_from}_{args.date_to}.html\"
def build_html(
    *,
    args: argparse.Namespace,
    stories: list[dict[str, Any]],
    target_rows: list[dict[str, Any]],
    initial_targets: list[str],
    article_map: dict[int, dict[str, Any]],
) -> str:
    label_by_key = target_label_map(target_rows)
    generated_at = datetime.now(timezone.utc).strftime(\"%d/%m/%Y %H:%M UTC\")
    scope_kicker, scope_title, scope_text = scope_labels(args)
    total_story_count = len(stories)
    total_article_count = sum(int(story.get(\"articleCount\") or 0) for story in stories)
    total_ai_count = sum(int(story.get(\"aiCount\") or 0) for story in stories)
    total_raw_count = sum(int(story.[N(hits)
        searchable = \"\" if exact_body_only else \" \".join([candidate.title or \"\", candidate.snippet or \"\"])
        hits = [] if exact_body_only else matcher.find_hits(searchable)
        hits_from_preview = bool(hits)
        must_fetch_article = bool(force_full_fetch or exact_body_only or not hits or needs_published_extraction)
        if must_fetch_article:
                if exact_body_only:
                    hits = matcher.find_hits(full_text)
                elif not hits:
        if (force_full_fetch or exact_body_only) and not str(full_text or \"\").strip():
            emit_candidate(
                candidate=candidate,
                status=\"skipped\",
                reason=\"missing_body\",
                final_url=final_url,
                hits_for_candidate=[],
                title_value=clean_title(candidate.title or extracted_title or \"\"),
                published_value=published_at,
                stage=\"body_fetch\",
            )
            continue
        if needs_published_extraction and not published_at:
                reason=\"no_exact_body_match\" if exact_body_only else \"no_match_exact_name\",
    if collector == \"all\" and not options.custom_query.strip():
        target_keys = {str(target.key) for target in targets}
        if \"flavio_valle\" in target_keys:
            planned_urls = {candidate.url for _, _, batch in plans for candidate in batch if candidate.url}
   [O         per_internal_adapter_limit = max(
                6,
                min(20, max_candidates // max(1, len(FLAVIO_INTERNAL_SEARCH_TARGETS))),
            internal_candidates = collect_internal_site_search(
                queries=FLAVIO_INTERNAL_SEARCH_QUERIES,
                date_from=options.date_from,
                date_to=options.date_to,
                limit_per_adapter=per_internal_adapter_limit,
                max_pages_per_adapter=6,
                request_timeout=request_timeout,
            filtered_internal: list[CandidateArticle] = []
            for item in dedupe_candidates(internal_candidates):
                if item.url in planned_urls:
                    continue
                planned_urls.add(item.url)
                filtered_internal.append(item)
            plans.append((\"Internal Site Search\", \"internal_search\", filtered_internal))
            if progress_callback:
                progress_callback(
                    \"source_collected\",
                    {
                        \"source_name\": \"Internal Site Search\",
                        \"source_type\": \"internal_search\",
                        \"candidates_total\": len(filtered_internal),
                    },
                )
        source_options = options
        if source_type == \"internal_search\":
            source_options = replace(options, target_keys=[\"flavio_valle\"], archive_full_text=True)
                options=source_options,
    \�        errors=[],
            per_internal_adapter_limit = max(
        must_fetch_article = bool(force_f]cVn8bOy1Hw3T0uDWdDUBB7R1gPgpglFwig1ogS1_NDba1mKAARqiEiAO4DL9uZ46VJMJqbktnbrGTUbyNCtmBwES44MUj5Z1Uz097Z2foZbWuSlBVIcZ1h3_p5xyxrMOOFxyFPvNgnkKszE4Zg4-cRYFJNDM9ua-hd5l0aU-OdAnTtR7sAUTLO4vK-lvnARi_5HlGWKzkFZpJXk9pduAFTcJ70QIVki5keCggzwWKH3eQHW_2sIfom7jJewU3ZQdH5jRJd1AnS_WAsMngVGHVXfVvtZKqlacKcvTeAUss9LkyVfNWyKxOSgPC9X43OMwp2EDYdYIlHjxLpjTsaO0H7mBfHdcX0sfXYx5ob2eZs8MGcm9fP2tBEiC--0is_rgztxsaCLWGDx4E8OrdDeY967GyCuT9-oHZ4DimdFLKLOi0MVCHjZXP_rQuh1bmiJPZSZJDPuAcgL99gnAhoT8hMNvhVoyvrCkAbLEsixxraomXeCMWMzKLMP16D1E5Vi_w279KidsoyiomCEwbX0UvHcTmkgp4dyZ9-dgGn7kG3X_RkDV_aXNS6u3cvnHHs5urI4yzN2rieD3Vv2hgg3OYQ6Tp2ZeewXmoo6DbODU71nNWbLEfJbCPYoXaJ2d5nw6wcS_O6YxhNNCgz4c-VuWmMcznFhe8k0Zn4TMb-Tajj6gkmCHAB5rUwEYH1cnUu1gpoIlyw6FIEvODk2Dn7ptg7ODdBaedoVFbTlyxIZknMwHlAlf8RqzKi_xupWvaTVUgCMwoDEGMARvqN7zRIv6IcE8QgGW21UbCVWTdzJk2EhCK1h_ogrdM1AqoesDRPT0zRcWIxVTw3XrYQgESwfp4DSIahw66SBhJnLZx3mpVOwGzDXwGNdoI4TDzKjb5inJZ6zZ7h3WjidXnXlp3m2aC-7FUzelcZ_jWjYxXVfbTD7d39UgpR6JVDJFcMMVYL_yuOa0MGOMkFNX4WttDQxmzne1MQf_YsPanqOAOMXIWm29D2mSbNXU79M8mCgC89w5Le2C7F8v4W_W1pHsoX15AyYBn8cqmUVfn11bgo2r8UcESRVO0qcnk9zvINihCSS5VZZEiqhcCWLWovGr6VhhjZMXZQXU3ieJ3XqMPclAK6FovhSgBEXNegRXTvInbwTsO5AVdTb0XCp2VNdJs2LyyZmWbnGouIGVE5rsuR0iskWmgBUIfEV1Tazc9fuAxA9Ww9hOgC9dmWUtIGt3pdkdTMX-2h2HuTkaeyRPs46bjsqF2JRqOaaqqOKuAFl7_pdqVh-Je7lM6sF_Itu_7v9ZNy-Chv6xr22FYWR3K-360Y4dPUG0MZiywnHYvAcd9mooXOf5nnQppBJPL3WsI4sRLEt5m1fIZUsZX27BN4iqqtLX-xs5ecj5aZWVuu2q8gaFtdNDPGy3VpMuDf8eAduKZ2tXnhuuzOrz-cywUtti0KmFxtyiGgUG3KO6CoKcEbQD9ZxVPoQMSQSk6FoAIwBTguIgMg4FTeWBAGrax0TRqABh4LvPHYcidRL1LXSG_DTJoCAachhizOHAYZoj-TEv_ptTvnjCSFMjtarvQgAUytEQxW1v9NmAZb_8mCjR5smNeYlY-dPYOAbvnpzfnGZR84C09WYe7rthraeMJbENHn3P1OpRrKXArCxAs1bgrHR_X8MrlCIl053Df41hfF3fPUmraP_6Eh5do0TXJjfqNudn6HqUHbReOnaeXM5QFITpTGoOl7pLgWCUNJn8lpMxBiECHEOa7k5PdrS9YVvBhsHdHeoHkDvO6Z2LHGyCAuP5Nv6NQT2Mi8YT-dcjNk4zYIqCxBDbrJkN4KMR1Jhnm2ZkS502h7ARDIDZixdR1U4t984jJPZjfa5lYElE-4j5RQHLnlx_UtIABML-lajhWeZQFNWLpjgLBcIc_yr3phqyTxVSzF9EnkkInaOjHGW3Az2k60pQuYwpBGzCzkPZB156fg2QmGia1xiJzdUnH2urVKNlR0KVI2xgaVRMzINR52MdHNSCBvveKPtVTdRa74-A1R6xBlsC4OwIr-0PXBhTXiH_l62ji-wLBBOMK2mYpN4XYvfd7jX6UllbeLqsAVmeVC5UVUWHILuqHrRAerCNSuGO0NGpCwPonIIUmm_I_XAYJLFLhqMG2tdgjypaA172V7Qi8Vg0Cu2ckAKLtD2QsNP6Lj8iiB9y0kKc4GFh4iHHeoFGwU2uj-Dzqv_l5r-aaVn1utOo4jGHI2XivpQv90coWFQNytsOlFEuumslG0qBZCGCAsUZJ_JZg90FlK8heXGU6qrQX19S0VaxkkRDr6_Yrr_Brg1YZQgVqWg6y5wwPCyVQtWw6TfPu6FESC-dyz_7okXmZ8NJk3pknj2owWjLq6u8WczksnmH7jD3uafzH-xLLvDYjYXOMsWbHRFDHCVT4JBdRFRH-E9tSmsB3pHkpJQrmXtB6gC6Z88DOUOwZOX1rEDX23kLQBcI-unSYbEbSrSzv3RrhtEBZlY7lR5MEMliaMViJZDbJKbrNp0zJvkNYlzhdxM19sTTdDMU7mRxvXtxggyp1WNZ0GFe8Yt8PTcIj0EYmdEwHfMnrOy2ISradwSg56ZfzXdiX10uA6E1ZE5xltMcevAVyaJJpjh0EbsUBJ5R47t3So7BBERg54llYqBwGdsLG9RlnDkcfvaBPL4PyIGTVvdw_09pgUCgKEvjm8o7R1sktsu8Naa19PNC7OOe5UseBeZ2jmOd09hG7LixzXT3kXFwvY3r9zbV8p9i87klSP-Esqqp2YnZKbfuBowNDsL0RAnpudTEOxN1YVRPU20LozrkJ01-CjK12YbFcIrf2cWDL9diiXjEe5vbYeI9LGqZGUh0gDE9Dk8ZYrJoZ8fC7Hql7zbQOTMZtMMGrjTwWCLtdR6PzGkFCe2s3VKc2Io4dQ0UDcMWm185iOS9zwCxbhNSNtE0jYNcreu4jLnHPYd8AiLnPJuUunfaCMsHgld-YmhU-1W2Q04RSbs5GFcLJQYFWPSSwiRknIUj03OiAxtmU_xUwfEcNq0wFrPAG98ANkxt9CATgko4ALUUkIGZYAAkhjxZCbwKzJy6mZ3yR9S11yk9zFNnLuBoGskecLNlkeHkFkrFHxA7C2MQLuuPTsXbs2Gd6EOjXeDG0J4nRP1pLXucEK7TgRiIAH9l13dquxOBljOhioNUa8IOdYE4fhLnC77wC5b-z67CJD8EZAEHKaPEWnwifBiuNA0sGBBR112Sanh_rQHOnP3ftWnKnLMEp3xL98hu_dJxk15pn6Gd3B1pBBiOyiujuVUnqsOxrH7lhjB0qBKPbSNG14IutBVOBZjAE6mRwN0mVB9aQKFzw3raciVcM3Ung_dbgEFjagGNrTkHgHd7Bf3RgkQx6E7Z71gnDYkbJR7HuS08QjjOIPCf5AUM2qXK4vTx0Qb-c301VjDtdx4AescnQC2pFw2hWBiXaiV1nrn9yCMs4agkPouJWjS-eGK2aD9g4tC0LvgePYKx68kpbx-7N9iEUoWaUreDxZtBlqBo7mMF8Om1_HSooP7g4GUSqfPhtpZ9_QliJf-Lp_m7K3Basb2wsWqqd_5x_rr1BT1aKZcfH585JHipo64IZ95g8-V_3kW9G4RdidFO9CUqEWltHZoUAFJhZRsQThRPpYykcBjKdrzSyjjyj3gcbn-qmPXL_apDtV5G4tZUXpt3YdZeN9nYLaq_W"},{"type":"function_call",
    collect_extra_site,
    if collector == \"extra_site\":
        extra_candidates = collect_extra_site(
            date_from=options.date_from,
            date_to=options.date_to,
            limit_total=max_candidates,
            request_timeout=request_timeout,
        plans.append((\"Extra Site\", \"extra_site\", dedupe_candidates(extra_candidates)))
        planned_urls.update(candidate.url for candidate in extra_candidates if candidate.url)
        if progress_callback:
            progress_callback(
                \"source_collected\",
                {\"source_n
5s�
fspppppp

^^^^^^݁o���x
____gi�T6|UpTRACEcodex_app_server::codex_message_processorapp-server event: codex/event/token_countc�<���!�mgi�Y�<|TRACElogC:\Users\runneradmin\.cargo\git\checkouts\tokio-tungstenite-ea4445d9acecae62\132f5b3\src\compat.rs:154 Read.readpid:2916:2b2c31c9-a957-4a90-a018-52189e21fc05x(� �#gi�Y���TRACElogC:\Users\runneradmin\.cargo\git\checkouts\tokio-tungstenite-ea4445d9acecae62\132f5b3\src\lib.rs:304 Stream.with_context poll_next -> �M���7�
gi�Y�z�TRACElogC:\Users\runneradmin\.cargo\git\checkouts\tokio-tungstenite-ea4445d9acecae62\132f5b3\src\lib.rs:245 WebSocketStream.with_contextpid:2916:2b2c31c9-a957-4a90-a018-52189e21fc05���6�ugi�Y�j�TRACElogC:\Users\runneradmin\.cargo�}���E
_{__gi�]&LxTRACEcodex_app_server::codex_message_processorapp-server event: codex/event/exec_command_output_deltacodex_app_server::codex_message_processorapp-server\src\codex_message_processor.rs�pid:2916:2b2c31c9-a957-4a90-a018-52189e21fc05��d���D/�//Ugi�Z/.3�TRACEcodex_core::spawnspawn_child_async: "C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" ["-Command", "[Console]::OutputEncoding=[System.Text.Encoding]::UTF8;
                {\"source_name\": \"Extra Site\", \"source_type\": \"extra_site\", \"candidates_total\": len(extra_candidates)},
        if source_type in {\"internal_search\", \"sitemap_daily\", \"vejario_archive\", \"camara_archive\", \"odia_site\", \"r7_site\", \"extra_site\"}:
            queries=list(FLAVIO_QUERY_VARIANTS),
    collect_odia_site,
    collect_r7_site,
    if collector == \"odia_site\":
        odia_candidates = collect_odia_site(
            queries=[options.custom_query.strip()] if options.custom_query.strip() else list(FLAVIO_QUERY_VARIANTS),
            max_pages_per_query=6,
     �urce_cfg.get(\"host\") or \"noticias.r7.com\").strip() or \"noticias.r7.com\"
    day_index_url = str(source_cfg.get(\"day_index_url\") or \"\").strip()
    news_index_url = str(source_cfg.get(\"news_index_url\") or \"\").strip()
    section_index_url = str(source_cfg.get(\"section_index_url\") or \"\").strip()
    section_slugs = {str(item).strip() for item in (source_cfg.get(\"section_slugs\") or []) if str(item).strip()}
    requested_days = {day.date().isoformat() for day in _iter_window_days(date_from, date_to, default_days=7)}
    covered_days: set[str] = set()
    collected: list[CandidateArticle] = []
    seen_urls: set[str] = set()
    def append_sitemap_entries(*, sitemap_url: str, origin: str, allowed_days: set[str] | None = None) -> None:
        nonlocal collected, seen_urls
        if len(collected) >= max(1, limit_total):
            return
        try:
            _, xml_text = fetch_url(sitemap_url, timeout=request_timeout)
        except Exception:
        for row in _parse_sitemap_entries(xml_text):
            if len(collected) >= max(1, limit_total):
                break
            canon_url = canonicalize_url(str(row.get(\"loc\") or \"\").strip())
            if not canon_url or canon_url in seen_urls:
                continue
            if not is_likely_article_url(canon_url, expected_host_fragment=host):
            published_at = str(row.get(\"published_at\") or \"\").strip()
            if published_at and not _within_window(published_at, date_from=date_from, date_to=date_to):
            if allowed_days is not None and published_at:
                day_key = _day_key_from_iso(published_at)
                if day_key and day_key not in allowed_days:
            seen_urls.add(canon_url)
            collected.append(
                _build_specialized_candidate(
                    title=str(row.get(\"title\") or \"\"),
                    url=canon_url,
                    source_name=source_name,
                    source_type=\"r7_site\",
                    published_at=published_at,
                    metadata={
                        \"r7_source\": origin,
                        \"sitemap_url\": sitemap_url,
                        \"site_collector\": \"r7_site\",
    try:
        _, day_index_xml = fetch_url(day_index_url, timeout=request_timeout)
    except Exception:
        day_index_xml = \"\"
    for row in _parse_sitemap_index_entries(day_index_xml):
            break
        sitemap_url = canonicalize_url(str(row.get(\"loc\") or \"\").strip())
        day_key = _r7_day_from_sitemap_url(sitemap_url)
        if requested_days and day_key not in requested_days:
        if day_key:
            covered_days.add(day_key)
        append_sitemap_entries(sitemap_url=sitemap_url, origin=\"day_index\")
    missing_days = requested_days - covered_days
    should_run_fallback = bool(missing_days) or not collected
    if not should_run_fallback:
        return _dedupe_candidates_by_url(collected)
    fallback_day_filter = missing_days if missing_days else None
    fallback_sitemaps: list[tuple[str, str]] = []
        _, news_index_xml = fetch_url(news_index_url, timeout=request_timeout)
        news_index_xml = \"\"
    for row in _parse_sitemap_index_entries(news_index_xml):
        if sitemap_url:
            fallback_sitemaps.append((sitemap_url, \"news_index\"))
        _, section_index_xml = fetch_url(section_index_url, timeout=request_timeout)
        section_index_xml = \"\"
    for row in _parse_sitemap_index_entries(section_index_xml):
    �.strip() or day.replace(
                hour=12,
                minute=0,
                second=0,
                microsecond=0,
                tzinfo=timezone.utc,
            ).isoformat()
            if not _within_window(published_at, date_from=date_from, date_to=date_to):
                    source_type=\"odia_site\",
                        \"odia_source\": \"sitemap\",
                        \"site_collector\": \"odia_site\",
    for query in query_list:
        page = 1
        while page <= max(1, max_pages_per_query) and len(collected) < max(1, limit_total):
            search_url = search_template.format(query=quote_plus(query), page=page)
            try:
                _, body = fetch_url(search_url, timeout=request_timeout)
                payload = json.loads(body)
            except Exception:
            if not isinstance(payload, list) or not payload:
            page_new_urls = 0
            dated_hits = 0
            older_hits = 0
            for row in payload:
                if len(collected) >= max(1, limit_total):
                    break
                if not isinstance(row, dict):
                canon_url = canonicalize_url(str(row.get(\"url\") or \"\").strip())
                if not canon_url or canon_url in seen_urls:
                if not is_likely_article_url(canon_url, expected_host_fragment=host):
                published_at = _parse_unix_timestamp(str(row.get(\"publish\") or row.get(\"date\") or \"\"))
                if published_at:
                    dated_hits += 1
                    parsed = _parse_window_boundary(published_at, end_of_day=False)
                    if start and parsed and parsed < start:
                        older_hits += 1
                    if not _within_window(published_at, date_from=date_from, date_to=date_to):
                        continue
                seen_urls.add(canon_url)
                page_new_urls += 1
                collected.append(
                    _build_specialized_candidate(
                        title=str(row.get(\"title\") or \"\"),
                        url=canon_url,
                        source_name=source_name,
                        source_type=\"odia_site\",
                        published_at=published_at,
                        snippet=str(row.get(\"description\") or \"\"),
                        metadata={
                            \"odia_source\": \"search\",
                            \"search_url\": search_url,
                            \"query\": query,
                            \"site_collector\": \"odia_site\",
                        },
                    )
            if page_new_urls == 0:
            if dated_hits and older_hits == dated_hits:
            page += 1
    return _dedupe_candidates_by_url(collected)
def collect_r7_site(
    source: dict[str, object] | None = None,
    date_from: str = \"\",
    date_to: str = \"\",
    limit_total: int = 240,
    request_timeout: int = 10,
) -> list[CandidateArticle]:
    source_cfg = source or R7_SITE_SOURCE
    source_name = str(source_cfg.get(\"source_name\") or \"R7 Site\").strip() or \"R7 Site\"
    host = str(so�earchTarget,
    ODIA_SITE_SOURCE,
    R7_SITE_SOURCE,
def _parse_sitemap_index_entries(xml_text: str) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
        root = ET.fromstring(xml_text)
        return rows
    for sitemap_node in root.iter():
        if _xml_local_name(sitemap_node.tag) != \"sitemap\":
        loc = \"\"
        lastmod = \"\"
        for child in sitemap_node.iter():
            if child is sitemap_node:
            name = _xml_local_name(child.tag)
            value = _safe_text(child)
            if not value:
            if name == \"loc\" and not loc:
                loc = value
            elif name == \"lastmod\" and not lastmod:
                lastmod = _parse_datetime(value)
        if loc:
            rows.append({\"loc\": loc, \"lastmod\": lastmod})
    return rows
def _parse_unix_timestamp(value: str) -> str:
    raw = str(value or \"\").strip()
    if not raw or not raw.isdigit():
        return \"\"
        return datetime.fromtimestamp(int(raw), tz=timezone.utc).isoformat()
def _day_key_from_iso(value: str) -> str:
    if not raw:
        dt = datetime.fromisoformat(raw.replace(\"Z\", \"+00:00\"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).date().isoformat()
def _r7_day_from_sitemap_url(url: str) -> str:
    match = re.search(r\"/arc/outboundfeeds/sitemap\\d*/(\\d{4}-\\d{2}-\\d{2})/\", str(url or \"\"))
    return match.group(1) if match else \"\"
def collect_odia_site(
    queries: list[str] | None = None,
    max_pages_per_query: int = 6,
    source_cfg = source or ODIA_SITE_SOURCE
    source_name = str(source_cfg.get(\"source_name\") or \"O Dia Site\").strip() or \"O Dia Site\"
    host = str(source_cfg.get(\"host\") or \"odia.ig.com.br\").strip() or \"odia.ig.com.br\"
    sitemap_template = str(source_cfg.get(\"sitemap_url_template\") or \"\").strip()
    search_template = str(source_cfg.get(\"search_url_template\") or \"\").strip()
    query_list = [str(item or \"\").strip() for item in (queries or []) if str(item or \"\").strip()]
    if not query_list:
        query_list = [\"Flavio Valle\", \"Flávio Valle\"]
    start = _parse_window_boundary(date_from, end_of_day=False)
    for day in _iter_window_days(date_from, date_to, default_days=7):
        sitemap_url = sitemap_template.format(yyyy=day.strftime(\"%Y\"), mm=day.strftime(\"%m\"), dd=day.strftime(\"%d\"))
            published_at = str(row.get(\"published_at\") or \"\")�4REJ_Nx3ynw1waEl4Xxy9Sr3z_h9jDTNbc6aoapSFALZeZ2D8P_-orxHoVAgYa5-fQYkdygGtP4Klw82d5Ca5mlxn8AUiqzrqTE1x1v0rqSUshuVV4uOkhS9dtBtDMOH9YMWR-u5gQN04pHpZzifhrN0--EVrMLoS60JWN8-7UNZiRLur1cSOcoHYikKl09U53jVfB7y3cxMiU30WrhPSES2BYh_j5fdxiYiBhHvMlKZ0WQycyLuoNs_btJJ2PO4S6BH0XmOVObyRvowUtJsNunm2hg_dhp69kOIepdlt5Z3XfJEdG74NX5MTVxm0L116vWuUwmsARtUtqOMwt3nec59npPrSE4uDkSZRzcOb1I7akypMkjuExQv_tYQF8LFqjFZWAqx6kA1f7l4MEcpGrw5bG_cA_cPGM_csiAJeVh5l67KcT7JXOmGAeaNIqoca6vzS74Q3oY8lcvdKneQS5FogfXdI-lutgzpH-wwF5hQAxultLliQhDGEjLww=="},{"type":"custom_tool_call","status":"completed","call_id":"call_L4fcKuY9ZNmlwPwuC2HA74yU",
        if source_type in {
            \"internal_search\",
            \"sitemap_daily\",
            \"vejario_archive\",
            \"camara_archive\",
            \"odia_site\",
            \"r7_site\",
            \"extra_site\",
            \"diariodorio_site\",
            \"temporealrj_site\",
        }:
    collect_diariodorio_site,
    collect_temporealrj_site,
    DIARIO_DO_RIO_SITE_SOURCE,
    TEMPO_REAL_RJ_SITE_SOURCE,
    if collector in {\"all\", \"diariodorio_site\"} and \"flavio_valle\" in requested_target_keys:
        diario_candidates = collect_diariodorio_site(
            queries=[options.custom_query.strip()] if options.custom_query.strip() else None,
            source=DIARIO_DO_RIO_SITE_SOURCE,
        diario_source_name = str(DIARIO_DO_RIO_SITE_SOURCE.get(\"source_name\""1x5uruP65nlkzQtC1Wdd5pMkeLdlSSR-Kv3osvomJ6xSs5sPjyZkWaN168rR2dlV_fLX_vOgU3U8PNoj2LR4mWu5HyqB-4nlKfH1zlI1NEcdiCyozmG0NjCN84LqzfQFdF_johez0lFDhbtEUTxqjZtALMKpkgikwppUjMHh8cd3PxFQAZLiuJnkZKJafd6pzLkNYqNMeCertlgKD6Q_guuTXMro3XQyL1fd3_MHj2M3OxMQ9e-427lA7YQbxg_EtJ3X_5TvehGdPwc2s_HRNiSOHo8gP8G3XF2Fd_Ll50-xLXCbKcoJx0Gm9CRAWrgFSAE="},{"type":"message","role":"assistant","content":[{"type":"output_text","text":"Vou tentar a etapa Wix de forma segura: só atualização do editor e validação em `Site de teste`, sem publicação ao vivo. Se a sessão antiga não estiver mais realmente usável ou se os seletores do HTML iFrame não baterem, eu paro no erro e te devolvo exatamente onde travou."}],"phase":"commentary"},{"type":"function_call",
        source_name = str(DIARIO_DO_RIO_SITE_SOURCE.get(\"source_name\") or \"Diario do Rio Site\").strip() or \"Diario do Rio Site\"
        plans.append((source_name, \"diariodorio_site\", dedupe_candidates(diario_candidates)))
        planned_urls.update(candidate.url for candidate in diario_candidates if candidate.url)
        if progr]y date window + search term.
DIARIO_DO_RIO_SITE_SOURCE: dict[str, object] = {
    \"source_name\": \"Diario do Rio Site\",
    \"host\": \"diariodorio.com\",
    \"base_url\": \"https://diariodorio.com\",
    \"source_type\": \"diariodorio_site\",
    \"query_variants\": [\"Flavio Valle\", \"Fl\\u00e1vio Valle\", \"Valle\"],
}
TEMPO_REAL_RJ_SITE_SOURCE: dict[str, object] = {
    \"source_name\": \"Tempo Real RJ Site\",
    \"host\": \"temporealrj.com\",
    \"base_url\": \"https://temporealrj.com\",
    \"source_type\": \"temporealrj_site\",
WORDPRESS_SITE_SOURCES: list[dict[str, object]] = [
]
    host = str(source_cfg.get(\"host\") or \"noticias.r7.com\").strip() or \"noticias.r7.com\"
 �ed) >= max(1, limit_total):
            published_at = str(row.get(\"published_at\") or \"\").strip() or day.replace(
  �"},{"type":"message","role":"assistant","content":[{"type":"output_text","text":"I’ve got the config constants in. Next I’m wiring the actual `collect_odia_site` and `collect_r7_site` functions, keeping them isolated from `all` and reusing the existing strict-body validation metadata instead of touching the older collectors."}],"phase":"commentary"},{"type":"custom_tool_call","status":"completed","call_id":"call_gr2u9yqo7nWYU87KrLIj1qhR",
        plans.append((\"O Dia Site\", \"odia_site\", dedupe_candidates(odia_candidates)))
        planned_urls.update(candidate.url for candidate in odia_candidates if candidate.url)
                {\"source_name\": \"O Dia Site\", \"source_type\": \"odia_site\", \"candidates_total\": len(odia_candidates)},
    if collector == \"r7_site\":
        r7_candidates = collect_r7_site(
        plans.append((\"R7 Site\", \"r7_site\", dedupe_candidates(r7_candidates)))
        planned_urls.update(candidate.url for candidate in r7_candidates if candidate.url)
                {\"source_name\": \"R7 Site\", \"source_type\": \"r7_site\", \"candidates_total\": len(r7_candidates)},
        if source_type in {\"internal_search\", \"sitemap_daily\", \"vejario_archive\", \"camara_archive\", \"odia_site\", \"r7_site\"}:
from dataclasses import dataclass, replace
    collect_internal_site_search,
    FLAVIO_INTERNAL_SEARCH_QUERIES,
    target_keys: list[str] | None = None