Traceback (most recent call last):
  File "C:\Users\Admin\.vscode\docs\The Clipping project\	ools\benchmark_sources_vs_excel.py", line 1149, in <module>
    raise SystemExit(main())
                     ~~~~^^
  File "C:\Users\Admin\.vscode\docs\The Clipping project\	ools\benchmark_sources_vs_excel.py", line 1107, in main
    result = evaluate_source_module(
        source_module,
    ...<17 lines>...
        excel_day_padding=max(0, int(args.excel_day_padding)),
    )
  File "C:\Users\Admin\.vscode\docs\The Clipping project\	ools\benchmark_sources_vs_excel.py", line 983, in evaluate_source_module
    return evaluator(
        source_module,
    ...<2 lines>...
        excel_days=excel_days,
    )
  File "C:\Users\Admin\.vscode\docs\The Clipping project\	ools\benchmark_sources_vs_excel.py", line 884, in evaluate_source_module_cbn_fast
    payload = run_cbn_day_prescreen(
        source_module,
    ...<3 lines>...
        matcher=matcher,
    )
  File "C:\Users\Admin\.vscode\docs\The Clipping project\	ools\benchmark_sources_vs_excel.py", line 790, in run_cbn_day_prescreen
    day_candidates = collect_cbn_day_candidates(source_module, day_str=day_str, day_limit=int(options.cbn_day_limit))
  File "C:\Users\Admin\.vscode\docs\The Clipping project\	ools\benchmark_sources_vs_excel.py", line 744, in collect_cbn_day_candidates
    raise RuntimeError(f"sitemap_fetch_error:{day_str}:{last_error}")
RuntimeError: sitemap_fetch_error:2025-01-30:<urlopen error timed out>
"},{