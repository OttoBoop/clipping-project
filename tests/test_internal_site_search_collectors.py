
    items = collectors.collect_internal_site_search(
        queries=[\"Flavio Valle\"],
        adapters=[adapter],
        date_from=\"2025-01-01\",
        date_to=\"2025-01-31\",
        limit_per_adapter=10,
        request_timeout=3,
    )
    assert payload_offsets == [0, 2]
    assert [item.url for item in items] == [f\"{prefix}-1\", f\"{prefix}-2\"]
    assert all(item.metadata[\"force_full_fetch\"] for item in items)
    assert all(item.metadata[\"exact_body_only\"] for item in items)
    assert all(item.metadata[\"require_published_extraction\"] is False for item in items)
    assert all(item.metadata[\"query\"] == \"Flavio Valle\" for item in items)
@pytest.mark.parametrize(
    (\"host\", \"search_url\", \"html_page\", \"expected_url\", \"expected_next\"),
    [
        (
            \"vejario.abril.com.br\",
            \"https://vejario.abril.com.br/busca/?s=Flavio+Valle&orderby=date\",
            \"\"\"
            <div id=\"post-486958\" class=\"card not-loaded list-item\">
              <div class=\"row\">
                <div class=\"col-s-12 col-l-9\">
                  <a href=\"https://vejario.abril.com.br/cidade/prioridade-novo-subprefeito-zona-sul/\">
                    <h2 class=\"title\">A prioridade do novo subprefeito da Zona Sul do Rio</h2>
                  </a>
                  <span class=\"description\">Flávio Valle aparece no corpo.</span>
                  <span class=\"date-post\">5 fev 2026, 11h33</span>
                </div>
              </div>
            </div>
            <script>
              var infiniteScroll = {\"settings\":{\"history\":{\"host\":\"vejario.abril.com.br\",\"path\":\"\\\\/busca\\\\/pagina\\\\/%d\\\\/\",\"parameters\":\"?s=Flavio+Valle&orderby=date\"}}};
            </script>
            \"\"\",
            \"https://vejario.abril.com.br/cidade/prioridade-novo-subprefeito-zona-sul\",
            \"https://vejario.abril.com.br/busca/pagina/2?s=Flavio+Valle&orderby=date\",
        ),
            \"camara.rio\",
            \"https://camara.rio/index.php?option=com_search&view=search&searchword=Flavio+Valle&searchphrase=exact&ordering=newest\",
            <dl class=\"search-results\">
              <dt class=\"result-title\">
                <a href=\"/comunicacao/noticias/2979-fazenda-presta-contas\">Fazenda presta contas</a>
              </dt>
              <dd class=\"result-category\"><span class=\"small\">(Notícias)</span></dd>
              <dd class=\"result-text\">Flávio Valle questionou os dados.</dd>
              <dd class=\"result-created\">Criado em 04 Dezembro 2025</dd>
            </dl>
            <link rel=\"next\" href=\"/search/newest-first/page-2?option=com_search&searchword=Flavio+Valle\" />
            \"https://camara.rio/comunicacao/noticias/2979-fazenda-presta-contas\",
            \"https://camara.rio/search/newest-first/page-2\",
            \"www.conib.org.br\",
            \"https://www.conib.org.br/pesquisar.html?searchword=Flavio+Valle&searchphrase=exact&ordering=newest\",
            <article class=\"uk-article\">
              <h2><a href=\"/eventos/combate-ao-antissemitismo\">Combate ao antissemitismo</a></h2>
              <p>Flávio Valle participou do encontro.</p>
            </article>
            <a class=\"next\" href=\"/pesquisar.html?searchword=Flavio+Valle&searchphrase=exact&ordering=newest&start=20\" title=\"Próximo\">Próximo</a>
            \"https://www.conib.org.br/eventos/combate-ao-antissemitismo\",
            \"https://www.conib.org.br/pesquisar.html?searchword=Flavio+Valle&searchphrase=exact&ordering=newest&start=20\",
    ],
)
def test_extract_internal_search_results_for_html_hosts(host: str, search_url: str, html_page: str, expected_url: str, expected_next: str):
    adapter = _aX�3lsKfo4lHOURnPj","output":"Exit code: 0
            \"https://vejario.abril.com.br/busca/pagina/2\",
            \"https://www.conib.org.br/pesquisar.html\",
    adapter = _a[�est_direct_scrape_windows.py:72`, `c:\\Users\\Admin\\.vscode\\docs\\The Clipping project\\tests\\test_flavio_query_expansion.py:17`, `c:\\Users\\Admin\\.vscode\\docs\\The Clipping project\\tests\\test_google_news_collector.py:28`, and `c:\\Users\\Admin\\.vscode\\docs\\The Clipping project\\tests\\test_run_ingestion_dedup.py:13`.
    adapter = _a`3lsKfo4lHOURnPj","output":"Exit code: 0
    adapter = _ahlY {order_by}\"\r
    adapter = _ap�3lsKfo4lHOURnPj","output":"Exit code: 0
    adapter = _a?�3lsKfo4lHOURnPj","output":"Exit code: 0