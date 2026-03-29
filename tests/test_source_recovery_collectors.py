    <h3 class=\"catItemTita": "C:\\Windows\\System32\\Drivers\\DriverData", "PATHEXT": ".COM;.EXE;.BAT;.CMD;.VBS;.VBE;.JS;.JSE;.WSF;.WSH;.MSC;.PY;.PYW", "ComSpec": "C:\\Windows\\system32\\cmd.exe", "CHROME_CRASHPAD_PIPE_NAME": "\\\\.\\pipe\\crashpad_6364_WDERUNSGQXHKSCUD", "ALLUSERSPROFILE": "C:\\ProgramData", "ChocolateyLastPathUpdate": "134152378285374647", "FPS_BROWSER_APP_PROFILE_STRING": "Internet Explorer", "ProgramFiles": "C:\\Program Files", "SystemRoot": "C:\\Windows", "PSModulePath": "C:\\Program Files\\WindowsPowerShell\\Modules;C:\\Windows\\system32\\WindowsPowerShell\\v1.0\\Modules", "VSCODE_CWD": "C:\\Users\\Admin\\AppData\\Local\\Programs\\Microsoft VS Code", "LOGONSERVER": "\\\\DESKTOP-EA4TFLP", "VSCODE_HANDLES_UNCAUGHT_ERRORS": "true", "VSCODE_PID": "6364", "VSCODE_NLS_CONFIG": "{\"userLocale\":\"en-us\",\"osLocale\":\"pt-br\",\"resolvedLanguage\":\"en\",\"defaultMessagesFile\":\"C:\\\\Users\\\\Admin\\\\AppData\\\\Local\\\\Programs\\\\Microsoft VS Code\\\\591199df40\\\\resources\\\\app\\\\out\\\
    <h3 class=\"catItemTitle\"><strong><a href=\"/comunicacao/noticias/100-primeira-noticia-camara\">Primeira</a></strong></h3>
    <h3 class=\"catItemTitle\"><strong><a href=\"/comunicacao/noticias/090-noticia-antiga-camara\">Antiga</a></strong></h3>
    assert [item.url for item in items] == [\"https://camara.rio/comunicacao/noticias/100-primeira-noticia-camara\"]

def test_collect_sitemap_daily_can_disable_prefilter_and_use_sitemap_day_membership(monkeypatch):
    xml = \"\"\"
    <urlset xmlns=\"http://www.sitemaps.org/schemas/sitemap/0.9\" xmlns:news=\"http://www.google.com/schemas/sitemap-news/0.9\">
      <url>
        <loc>https://oglobo.globo.com/rio/noticia/2025/05/20/exemplo.ghtml</loc>
        <news:publication_date>2025-05-21T01:10:00Z</news:publication_date>
        <news:title>Praias do Rio entram em debate</news:title>
      </url>
    </urlset>
    \"\"\"
    monkeypatch.setattr(collectors, \"fetch_url\", lambda url, timeout=10: (url, xml))
    items = collectors.collect_sitemap_daily(
        queries=[\"Flavio Valle\"],
        sources=[
            {
                \"source_name\": \"O Globo Sitemap\",
                \"host\": \"oglobo.globo.com\",
                \"sitemap_url_template\": \"https://example.com/{yyyy}/{mm}/{dd}.xml\",
                \"prefilter_queries\": False,
                \"window_by_sitemap_day\": True,
            }
        ],
        date_from=\"2025-05-20\",
        date_to=\"2025-05-20\",
        limit_per_source=20,
        request_timeout=3,
    )
    assert [item.url for item in items] == [\"https://oglobo.globo.com/rio/noticia/2025/05/20/exemplo.ghtml\"]
    assert items[0].metadata[\"query_prefilter_applied\"] is False
    assert items[0].metadata[\"window_by_sitemap_day\"] is True
    ry fechou `10/10`; 1 miss restante e `site_content_gap` | Classificar como gap editorial se confirmado |
+| `extra.globo.com` | `sitemap_daily` | `dias do Excel no testing set` | 5 | `5/533` | `5/7` | Verde | O sitemap diario passou a recuperar tudo no testing set e ainda trouxe 2 extras | Manter configuracao nova |
+
+## Fontes Zeradas com Evidencia de Existencia
+
+Relatorio historico do benchmark completo antes do sprint da familia Globo:
+
+- `oglobo.globo.com` via `sitemap_daily`: `0/46`
+- `g1.globo.com` via `sitemap_daily`: `0/10`
+- `extra.globo.com` via `sitemap_daily`: `0/5`
+- `vejario.abril.com.br` via `sitemap_daily`, `internal_search` e `vejario_archive`: `0/25`
+- `camara.rio` via `camara_archive` e `internal_search`: `0/11`
+
+Leitura correta desse zero historico:
+
+- para `oglobo/g1/extra`, o zero era um falso negativo de discovery causado por `title/url prefilter`;
+- para `vejario` e `camara`, o zero ainda parece ser estrutural e ainda exige wiring novo.
+
+## Fontes Parciais
+
+- `conib.org.br`: `raw_match 10/14`, `saved_match 0/14`, bloqueado por `fetch_fail:getaddrinfo`
+- `noticias.r7.com`: `3/4`
+- `oglobo.globo.com`: `41/46` salvas no benchmark pratico por dias do Excel; 4 misses sao `site_content_gap` e 1 miss e de discovery por drift de data
+- `g1.globo.com`: `9/10` salvas; o miss restante esta classificado como `site_content_gap`
+- `camara.rio`: teve `1/4` na janela curta, mas continua zerado na janela completa
+
+## Fontes Verdes
+
+- `cbn.globo.com`
+- `agendadopoder.com.br`
+- `diariodorio.com`
+- `temporealrj.com`
+- `odia.ig.com.br`
+- `extra.globo.com` via `sitemap_daily` no benchmark pratico por dias do Excel
+- `extra.globo.com` via `extra_site` no benchmark experimental por dias exatos
+
+## Backlog Ainda Sem Benchmark Formal
+
+Hosts verificados que ainda nao tem benchmark formal dedicado no runner atual:
+
+- `a3noticias.com.br`
+- `ademi.org.br`
+- `almapreta.com.br`
+- `band.com.br`
+- `bbc.com`
+- `boletimrj.com.br`
+- `campos24horas.com.br`
+- `canalvoxnoticias.com.br`
+- `colunadogilson.com.br`
+- `diariocarioca.com`
+- `enfoco.com.br`
+- `errejotanoticias.com.br`
+- `eurio.com.br`
+- `folhadoleste.com.br`
+- `gazetasulflu.com.br`
+- `iclipping.com.br`
+- `ilovecorrida.com.br`
+- `mancheterio.com.br`
+- `mercadoeeventos.com.br`
+- `newmag.com.br`
+- `portaltela.com`
+- `povonarua.com.br`
+- `tnh1.com.br`
+- `tribunadaserra.com.br`
+- `tupi.fm`
+- `www1.folha.uol.com.br`
+- `youtu.be`
+
+## Proxima Frente: Globo/G1/Extra
+
+Hipoteses que ficaram confirmadas no sprint:
+
+- As URLs do Excel de `oglobo`, `g1` e `extra` aparecem nos sitemaps diarios.
+- O `prefilter` por `title/url` derrubava a descoberta dessas fontes e explicava o zero historico.
+- O diagnostico por URL mostrou que a maior parte das paginas tem o nome no corpo extraido:
+  - `extra`: `5/5` como `extractor_hit`
+  - `g1`: `9/10` como `extractor_hit`, `1/10` como `site_content_gap`
+  - `oglobo`: `43/47` linhas do Excel como `extractor_hit`, `4/47` como `site_content_gap`
+- Nao apareceu um bucket relevante de `extractor_loss_raw_html_has_name` ou `extractor_loss_full_page_has_name` na familia Globo; o problema real era discovery, nao parser.
+
+Estado atual da familia Globo:
+
+- `extra` esta resolvido para o testing set no caminho de sitemap.
+- `g1` esta praticamente resolvido; o miss atual nao parece bug de extracao nem de discovery.
+- `oglobo` melhorou muito, mas ainda precisa separar dois casos:
+  - `1` miss de discovery ligado a drift entre data do Excel e dia do sitemap;
+  - `4` misses que o diagnostico classifica como `site_content_gap`.
+
+Proxima acao recomendada:
+
+1. Fechar `oglobo` com um recovery direcionado para misses de discovery por drift de data.
+2. Marcar formalmente os misses de `g1/oglobo` sem nome no HTML como `site_content_gap`.
+3. So depois voltar para os provedores realmente quebrados: `vejario`, `camara` e `conib`.
                \"sitemap_url_template\": \"https_://example.com/{yyyy}/{mm}/{dd}.xml\",
    assert items[0].metadata[\"window_by_sitemap_day\"]qpage_text_contains_flavio_vale=False,
        )
        == \"extractor_loss_full_page_has_name\"
    assert (
        classify_failure_bucket(
            fetch_status=\"ok\",
            matcher_hit=False,
            raw_html_contains_flavio_valle=True,
            raw_html_contains_flavio_vale=False,
            full_page_text_contains_flavio_valle=False,
            full_page_text_contains_flavio_vale=False,
        == \"extractor_loss_raw_html_has_name\"
def test_diagnose_url_row_reports_extractor_loss_when_name_only_exists_in_script(monkeypatch):
    raw_html = \"\"\"
    <html>
      <body>
        <main><p>Resumo curto.</p></main>
        <script>
          window.__DATA__ = {\"articleBody\":\"Flavio Valle aparece apenas no payload de hidratacao para este teste.\"};
        </script>
      </body>
    </html>
    monkeypatch.setattr(\"tools.globo_family_diagnostic.fetch_url\", lambda url, timeout=20: (url, raw_html))
    result = diagnose_url_row(
        {\"url\": \"https://oglobo.globo.com/rio/noticia/2025/05/20/exemplo.ghtml\", \"host\": \"oglobo.globo.com\"},
        matcher=get_flavio_matcher(),
        request_timeout=20,
    assert result[\"fetch_status\"] == \"ok\"
    assert result[\"raw_html_contains_flavio_valle\"] is True
    assert result[\"article_text_contains_flavio_valle\"] is True
    assert result[\"matcher_hit\"] is True
    assert result[\"failure_bucket\"] == \"extractor_hit\"
def test_diagnose_url_row_marks_site_content_gap_when_name_absent(monkeypatch):
    raw_html = \"<html><body><article><p>Materia sobre outro tema.</p></article></body></html>\"
        {\"url\": \"https://g1.globo.com/rj/noticia/2025/05/20/exemplo.ghtml\", \"host\": \"g1.globo.com\"},
    assert result[\"matcher_hit\"] is False
    assert result[\"failure_bucket\"] == \"site_content_gap\"
                \"source_name\": B\"O Globo Sitemap\",
R    \"\"\"
    assert [item.url for item in items] == I�[\"https://oglobo.globo.com/rio/noticia/2025/05/20/exemplo.ghtml\"]
    assert [item.url for item in items] ==  F[\"https://oglobo.globo.com/rio/noticia/2025/05/20/exemplo.ghtml\"]