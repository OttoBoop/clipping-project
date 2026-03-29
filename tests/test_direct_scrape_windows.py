    monkeypatch.setattr(ingest, \"collect_internal_site_search\", lambda **kwargs: [])
    monkeypatch.setattr(ingest, \"collect_diariodorio_site\", lambda **kwargs: [])
    monkeypatch.setattr(ingest, \"collect_temporealrj_site\", lambda **kwargs: [])