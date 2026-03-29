
def test_run_ingestion_wordpress_api_uses_site_specific_variants_and_dedupes(monkeypatch):
    wordpress_calls: list[tuple[str, str]] = []
    process_calls: list[tuple[str, list[str]]] = []
    monkeypatch.setattr(
        ingest,
        \"WORDPRESS_API_SITES\",
        [
            {
                \"source_name\": \"Agenda do Poder\",
                \"base_url\": \"https://agendadopoder.com.br\",
                \"query_variants\": [\"Flavio Valle\", \"Flávio Valle\", \"Valle\"],
            }
        ],
    )
    def fake_collect_wordpress_api(query: str, *, source_name: str, base_url: str, **kwargs):
        wordpress_calls.append((source_name, query))
        return [
            CandidateArticle(
                title=f\"{query} 1\",
                url=\"https://agendadopoder.com.br/post-unico\",
                source_name=source_name,
                source_type=\"wordpress_api\",
                published_at=\"2025-05-10T12:00:00+00:00\",
                snippet=\"Flavio Valle citado\",
                metadata={\"query\": query},
            )
        ]
    def fake_process_candidates(source_name: str, source_type: str, candidates, **kwargs):
        process_calls.append((source_type, [candidate.url for candidate in candidates]))
        return IngestionResult(
            source_name=source_name,
            source_type=source_type,
            candidates_seen=len(candidates),
            articles_inserted=0,
            mentions_inserted=0,
            stories_touched=0,
            errors=[],
        )
    monkeypatch.setattr(ingest, \"collect_wordpress_api\", fake_collect_wordpress_api)
    monkeypatch.setattr(ingest, \"process_candidates\", fake_process_candidates)
    run_ingestion(
        \"wordpress_api\",
        options=IngestionOptions(
            target_keys=[\"flavio_valle\"],
            date_from=\"2025-05-01\",
            date_to=\"2025-05-31\",
            max_candidates_per_source=20,
            max_process_seconds=60,
            request_timeout_seconds=3,
 [�eIxG-eePBUqzZb_qHzf08Zv0QWvOztPakMz7mFuPY3ZbFPPYGufwc91pl-pbPhizMVRAyCRzEdRF0jf30uAfqBYUSDln1nzd90_YOnydOMj-EXip9xy6gs0Obq2y8GSFPY3rd8uzmiepUte-_hkZweCVxSkDMS3HA7VCmx3DeiUoZNMHPkQ5jJJfnN8sdh8nMk5UVq_quyXVFNR_1pmgubVBZQ1YD7rbqtt6Lu2VoNhfSUb0Pknr8NWwTknoVEJvUdpLmPzpxmwwT6h9U2kQzuM1B2dnoWnmZNc00CgPdbWWSC0LJOf2Mqe-OnD8vP0piBW_4Uo8IjMYccS44zriSOKZCdaTetlCewldUTv_Pdb2DVG1lu2RXvh6i51OISx0ZoCNOscCmmAfjhAGDkd-uMaHfIxWABQCJgmGsMx6hVfuTyUnvwmtuPH74rwQqf9SknCX83zyJOcOQHSdxmpbA7LXejo1HOEMxC5OEd-DEUzfPViW-p52Q_2c9ALltY3thgZsGkLZWFc3VPa1iKv9MOlXC-xsVa5zEBuJRzGksqyozBpkwwFjnnAFAjQ4ZU_FBHVCMrNSkpH5DUJoGf9q8NUdtGAekQQ9oQ-VIP0nutb5PPP6ElSOkCJXk4u-2H0smJ94nMpOYISTjpVWStVYFCkrypKHTJSt4NkdwQsH1i2GGrmjozx-mktw5SLytSeGMf5716UyKGtJf8QEZZ8yC13N2XZxmoTtdXYQxyTAPdEUOHiOKZeIOAkvfl6FdUIIcFkLpH41WsLk9OTTxX1I5j9AXTN3j7DAeklrth3mfXNAuW3Up4rto_eXIqO905vSeOAwbE3H0RIVls3-q6SihsEs6V2nm4xsPqU="},{"type":"function_call",
        ),
    assert wordpress_calls == [
        (\"Agenda do Poder\", \"Flavio Valle\"),
        (\"Agenda do Poder\", \"Flávio Valle\"),
        (\"Agenda do Poder\", \"Valle\"),
    ]
    assert process_calls == [(\"wordpress_api\", [\"https://agendadopoder.com.br/post-unico\"])]
        '\"Flávio Valle\"',
        '\"Flávio Valle\" vereador',
    assert 'site:oglobo.globo.com \"Flávio Valle\"' in queries
                published_at=\"2025-05-10T12:00:00+00:00\c�X/Nu83Cu9ONz3Z/zFnfynueGVXoEb+Hv+7E95Ie7hL/78HDe8/CtyAy/MdbzFh70JN9z3S3z9T97Df4Qb3vYteWXO8RM/+Wf8Z7j+xtNw3+3czfNzD3fdDTfceDMv1Cu+HW93Dfzxn/wZ/5Hu+pM/465rXoGXu5GrrrrqqquuuuqqqwCA4KqrLnsFPvgDXxz+5jv55j/lhbvxLfnwNz3NXb/4DfzcnbxIXu5t34Qb7vslvv4n7+GFuvEtebuXgj/+1m/gL3j+7vrJb+An7ntx3u5tr+Nfdh1v8WFvwg33/RJf/9P38KJ6uY94X16Zv+frvuHP+Dd5xbfj7a45x098w89yF/9JbnxL3u6l4I+/9Rv4C56/u37yG/iJ+16ct3vb6/gX3fiWfPibnuauX/wGfuJu/gO8Ah/8gS8Of/OdfPOf8h/uhld6BW7g7/mzP+V53fmn/NF9p3mVV7qOF8UNN97Mf5g//QY+9RfP8cpv/ZbcwFVXXXXVVVddddVVAADBVVfd7xXfjre7Bv74p3+Wu3jhbnjbt+SVOcdP/OSf8SK58S35wg98ce76xc/hvb/uz3huf/F1H8I3/ymXvdxHfBZvd83f83Xv/xn83J08h7/4ug/hU38R3u5zPoyX40V041vy4W96mrvuO8eL7hX44A98cbjvHHfxb3Edb/GF78sr3/dLfOr7fwN/wXP502/gvb/uz/j3ermP+Cze7pq/5+ve/zP4uTt5Dn/xdR/Cp/4ivN3nfBgvx4vmhrf9MN7umnPcdR//MV7x7Xi7a+CPf/pnuYv/YDe+JW/3UvDH3/oZ/NydPMCf8c2f9Uvc9VJvyVvcyDP9Gd/8/t/AX/Cc/uLrPoefuO/Febu3vY7/CH/xdR/Ce3/r3/PKH/hNfPArctVVV1111VVXXXXVFQBUrvo/6O/5uvf/EJ7Tad7ucz6Pt7iRF+I63uKtX5yf+NZf4ut/8hX5wre9jhfsFXjLN/1Z/vgXv5Nv/tNX4INfkX/ZK34Y3/2K9/Bzn/o5vPf7fyfP6cX5iI/gma7jLb7wm3iLP/0G3vuzPoSf4AFe6n357m9/Bf61bnjbt+SVf/E7+WP+FV7x7Xi7n/57fuI+no9z/MRnfQg/wXN65Q/8Jj74FXmmV+CDv/0VeMuf/Aw+9f0/hOf2yh/4Yfz7XcdbfOE38RZ/+g2892d9CD/BA7zU+/Ld3/4K/Otcx1u89YvzE9/69/zHuI63eOsX5ye+9Zf4+p98Rb7wba/jir/n697/Q3hOp3m7z/k83uJGXmQv9xHfxBf+5GfwqZ/1IfwEz/bKH/hNfPcr8lz+nq97/w/hOVzzJnzht78lN/Dc/p6ve/8P4Tmd5u0+5/N4ixt5pr/n697/Q3gOL/W+fPe3vwJXXXXVVVddddVVVz0HAGTbXHXVVVddddVVV1111VVXXXXVfw4Agquuuuqqq6666qqrrrrqqquu+s8DQOWqq/6d7vrJz+BTf/Ecz9+L8xHf/mG8HFf9b3XXT34Gn/qL53j+XpyP+PYP4+W46qqrrrrqqquuuuqqFwgA2TZXXXXVVVddddVVV1111VVXXfWfA4Dgqquuuuqqq6666qqrrrrqqqv+8wAQXHXVVVddddVVV1111VVXXXXVfx4Agquuuuqqq6666qqrrrrqqquu+s8DQHDVVVddddVVV1111VVXXXXVVf95AAiuuuqqq6666qqrrrrqqquuuuo/DwDBVVddddVVV1111VVXXXXVVVf95wEguOqqq6666qqrrrrqqquuuuqq/zwABFddddVVV1111VVXXXXVVVdd9Z8HgOCqq6666qqrrrrqqquuuuqqq/7zABBcddVVV1111VVXXXXVVVddddV/HgCCq6666qqrrrrqqquuuuqqq676zwNAcNVVV1111VVXXXXVVVddddVV/3kACK666qqrrrrqqquuuuqqq6666j8PAMFVV1111VVXXXXVVVddddVVV/3nASC46qqrrrrqqquuuuqqq6666qr/PAAEV1111VVXXXXVVVddddVVV131nweA4Kqrrrrqqquuuuqqq6666qqr/vMAEFx11VVXXXXVVVddddVVV1111X8eAIKrrrrqqquuuuqqq6666qqrrvrPA0Bw1VVXXXXVVVddddVVV1111VX/eQAIrrrqqquuuuqqq6666qqrrrrqPw8AwVVXXXXVVVddddVVV1111VVX/ecBILjqqquuuuqqq6666qqrrrrqqv88AARXXXXVVVddddVVV1111VVXXfWfB4Dgqquuuuqqq6666qqrrrrqqqv+8wAQXHXVVVddddVVV1111VVXXXXVfx4Agquuuuqqq6666qqrrrrqqquu+s8DQHDVVVddddVVV1111VVXXXXVVf95AAiuuuqqq6666qqrrrrqqquuuuo/DwDBVVddddVVV1111VVXXXXVVVf95wEguOqqq6666qqrrrrqqquuuuqq/zwABFddddVVV1111VVXXXXVVVdd9Z8HgOCqq6666qqrrrrqqquuuuqqq/7zABBcddVVV1111VVXXXXVVVddddV/HgCCq6666qqrrrrqqquuuuqqq676zwNAcNVVV1111VVXXXXVVVddddVV/3kACK666qqrrrrqqquuuuqqq6666j8PAMFVV1111VVXXXXVVVddddVVV/3nASC46qqrrrrqqquuuuqqq6666qr/PAAEV1111VVXXXXVVVddddVVV131nweA4Kqrrrrqqquuuuqqq6666qqr/vMAEFx11VVXXXXVVVddddVVV1111X8eAIKrrrrqqquuuuqqq6666qqrrvrPA0Bw1VVXXXXVVVddddVVV1111VX/eQAIrrrqqquuuuqqq6666qqrrrrqPw8AwVVXXXXVVVddddVVV1111VVX/ecBILjqqquuuuqqq6666qqrrrrqqv88AARXXXXVVVddddVVV1111VVXXfWfB4Dgqquuuuqqq6666qqrrrrqqqv+8wAQXHXVVVddddVVV1111VVXXXXVfx4Agquuuuqqq6666qqrrrrqqquu+s8DQHDVVVddddVVV1111VVXXXXVVf95AAiuuuqqq6666qqrrrrqqquuuuo/DwDBVVddddVVV1111VVXXXXVVVf95wEguOqqq6666qqrrrrqqquuuuqq/zwABFddddVVV1111VVXXXXVVVdd9Z8HgOCqq6666qqrrrrqqquuuuqqq/7zABBcddVVV1111VVXXXXVVVddddV/HgCCq6666qqrrrrqqquuuuqqq676zwNAcNVVV1111VVXXXXVVVddddVV/3kACK666qqrrrrqqquuuuqqq6666j8PAMFVV1111VVXXXXVVVddddVVV/3nASC46qqrrrrqqquuuuqqq6666qr/PAAEV1111VVXXXXVVVddddVVV131nweA4Kqrrrrqqquuuuqqq6666qqr/vMAEFx11VVXXXXVVVddddVVV1111X8eAIKrrrrqqquuuuqqq6666qqrrvrPA0Bw1VVXXXXVVVddddVVV1111VX/eQAIrrrqqquuuuqqq6666qqrrrrqPw8AwVVXXXXVVVddddVVV1111VVX/ecBILjqqquuuuqqq6666qqrrrrqqv88AARXXXXVVVddddVVV1111VVXXfWfB4Dgqquuuuqqq6666qqrrrrqqqv+8wAQXHXVVVddddVVV1111VVXXXXVfx4Agquuuuqqq6666qqrrrrqqquu+s8DQHDVVVddddVVV1111VVXXXXVVf95AAiuuuqqq6666qqrrrrqqquuuuo/DwDBVVddddVVV1111VVXXXXVVVf95wEguOqqq6666qqrrrrqqquuuuqq/zwABFddddVVV1111VVXXXXVVVdd9Z8HgOCqq6666qqrrrrqqquuuuqqq/7zABBcddVVV1111VVXXXXVVVddddV/HgCCq6666qqrrrrqqquuuuqqq676zwNA5aqrHuDPbh35s6cP/P2dE087O3H3peTSMhkbV/0P0hU4tgiuPxY89EzlxW+svMJDel7hwR1XXXXVVVddddWz3XX3vdx79hznL1xkb/+Aw6MjhmEkM7nqf4ac�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 project\\tests\\test_internal_site_search_collectors.py
import json
import sys
from dataclasses import replace
from pathlib import Path
import pytest
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))
import pipeline.collectors as collectors
from pipeline.settings import FLAVIO_INTERNAL_SEARCH_TARGETS
def _adapter(host: str):
    return next(item for item in FLAVIO_INTERNAL_SEARCH_TARGETS if item.host == host)
@pytest.mark.parametrize(
    (\"host\", \"prefix\"),
    [
        (\"oglobo.globo.com\", \"https://oglobo.globo.com/rio/noticia\"),
        (\"g1.globo.com\", \"https://g1.globo.com/rj/rio-de-janeiro/noticia\"),
    ],
)
def test_collect_internal_site_search_globo_api_paginates_and_marks_body_validation(monkeypatch, host: str, prefix: str):
    adapter = replace(_adapter(host), page_size=2)
    payload_offsets: list[int] = []
    def fake_post_json(url: str, payload, timeout: int = 10):
        offset = int(payload[0][\"params\"][\"from\"])
        payload_offsets.append(offset)
        if offset == 0:
            hits = [
                {
                    \"_source\": {
                        \"title\": \"Primeira matéria\",
                        \"url\": f\"{prefix}-1\",
                        \"issued\": \"2025-01-20T12:00:00Z\",
                        \"body\": \"Flávio Valle citado.\",
                    }
                },
                        \"title\": \"Segunda matéria\",
                        \"url\": f\"{prefix}-2\",
                        \"issued\": \"2025-01-18T09:00:00Z\",
            ]
        else:
                        \"title\": \"Matéria antiga\",
                        \"url\": f\"{prefix}-antiga\",
                        \"issued\": \"2024-12-15T09:00:00Z\",
                }
        body = json.dumps([{\"result\": {\"hits\": {\"hits\": hits}}}])
        return url, body
    monkeypatch.setattr(collectors, \"post_json\", fake_post_json)
    items = collectors.collect_internal_site_search(
        queries=[\"Flavio Valle\"],
        adapters=[adapter],
        date_from=\"2025-01-01\",
        date_to=\"2025-01-31\",
        limit_per_adapter=10,
        request_timeout=3,
    assert payload_offsets == [0, 2]
    assert [item.url for item in items] == [f\"{prefix}-1\", f\"{prefix}-2\"]
    assert all(item.metadata[\"force_full_fetch\"] for item in items)
    assert all(item.metadata[\"exact_body_only\"] for item in items)
    assert all(item.metadata[\"require_published_extraction\"] is False for item in items)
    assert all(item.metadata[\"query\"] == \"Flavio Valle\" for item in items)
    (\"host\", \"search_url\", \"html_page\", \"expected_url\", \"expected_next\"),
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
dTbJ\xa6\xec\xf1P\x1d\xf9\x80\xf8\x89\xe06\xf3\x08\r\xe2;\x1b\xa2Q\x10\x92K\xa82\xdde\x80\x1d\xd7\x92\x87\x80\xe3eO\x80\x06\x94\x97'\xe7\xfd\x11\x8f\xa28\x17\0>\xe1\xe6\xa7\xf6\t\x1eV\x89\x9cR\xf0\x1a\xcf\xcc\xc6q\x82\x9f\xc2\x05\xa4\x05Qm\x04\xfd\xb0\x9a\xf0#\xfa\xf4
          <span class=\"author blog-image\"><time datetime=\"10:00\">| 10 maio 2025, 10h00</time></span>
        </div>
      </div>
    </div>
    <script>
      var infiniteScroll = {\"settings\":{\"path\":\"\\\\/coluna\\\\/lu-lacerda\\\\/pagina\\\\/%d\\\\/\",\"parameters\":\"\"}};
    </script>
    \"\"\"
    page2 = \"\"\"
    <div id=\"post-2\" class=\"card not-loaded list-item lu-lacerda\">
      <div class=\"row\">
        <div class=\"col-s-12 col-l-9\">
          <a href=\"https://vejario.abril.com.br/coluna/lu-lacerda/segunda-nota/\"><h2 class=\"title\">Segunda nota</h2></a>
          <span class=\"author blog-image\"><time datetime=\"11:00\">| 12 maio 2025, 11h00</time></span>
    def fake_fetch_url(url: str, timeout: int = 10):
        calls.append(url)
        if url.endswith(\"/coluna/lu-lacerda\"):
            return url, page1
        return url, page2
    monkeypatch.setattr(collectors, \"fetch_url\", fake_fetch_url)
    items = collectors.collect_vejario_archive(
        targets=[
                \"source_name\": \"Veja Rio Lu Lacerda Archive\",
                \"host\": \"vejario.abril.com.br\",
                \"start_url\": \"https://vejario.abril.com.br/coluna/lu-lacerda/\",
                \"article_path_prefix\": \"/coluna/lu-lacerda/\",
        date_from=\"2025-05-01\",
        date_to=\"2025-05-31\",
        limit_per_target=10,
        max_pages_per_target=2,
    assert calls == [
        \"https://vejario.abril.com.br/coluna/lu-lacerda\",
        \"https://vejario.abril.com.br/coluna/lu-lacerda/pagina/2\",
    assert [item.url for item in items] == [
        \"https://vejario.abril.com.br/coluna/lu-lacerda/primeira-nota\",
        \"https://vejario.abril.com.br/coluna/lu-lacerda/segunda-nota\",
    assert all(item.source_type == \"vejario_archive\" for item in items)
def test_collect_camara_archive_paginates_and_stops_when_window_ends(monkeypatch):
    calls: list[str] = []
    page1 = \"\"\"
    <span class=\"catItemDateCreated\">Sexta, 16 Maio 2025</span>
    <h3 class=\"catItemTitle\"><strong><a href=\"/comunicacao/noticias/100-primeira\">Primeira</a></strong></h3>
    <link rel=\"next\" href=\"/comunicacao/noticias?limit=10&amp;start=10\" />
    <span class=\"catItemDateCreated\">Quarta, 30 Abril 2025</span>
    <h3 class=\"catItemTitle\"><strong><a href=\"/comunicacao/noticias/090-antiga\">Antiga</a></strong></h3>
    <link rel=\"next\" href=\"/comunicacao/noticias?limit=10&amp;start=20\" />
        if \"start=10\" in url:
            return url, page2
        return url, page1
    items = collectors.collect_camara_archive(
        target={
            \"source_name\": \"Camara Rio Archive\",
            \"host\": \"camara.rio\",
            \"start_url\": \"https://camara.rio/comunicacao/noticias\",
            \"page_size\": 10,
        },
        limit_total=20,
        max_pages=5,
        \"https://camara.rio/comunicacao/noticias?limit=10&start=0\",
        \"https://camara.rio/comunicacao/noticias?limit=10&start=10\",
    assert [item.url for item in items] == [\"https://camara.rio/comunicacao/noticias/100-primeira\"]
    assert items[0].metadata[\"exact_body_only\"] is True
    monkeypatch.setattr(ingest, \"colc�ured = isLlmConfigured();\r
        wordpress_calls.apr�nthropic_batch\",\r
        process_calls.append((source_type, [candidate.url for candidate in candidatu�es]))
     u�   ingest,
        '\"Flávio Valle\" vereador
6T1
�^�2zB�6�'��|
MMKei�+�*i�HINFOcodex_otel::traces::otel_managercodex_otel::traces::otel_managerotel\src\traces\otel_manager.rs�pid:668:144eaa79-eb9c-4706-a491-074439ab28f0c�$��{MUM�wei�+�%Gq|TRACEhyper_util::client::legacy::poolpool closed, canceling idle intervalhyper_util::client::legacy::poolC:\Users\runneradmin\.cargo\registry\src\index.crates.io-1949cf8c6b5b557f\hyper-util-0.1.19\src\client\legacy\pool.rs2pid:668:144eaa79-eb9c-4706-a491-074439ab28f0ނ2��zMqM�wei�+�%�DEBUGhyper_util::client::legacy::poolpooling idle connection for ("https", chatgpt.com)hyper_util::client::legacy::poolC:\Users\runneradmin\.cargo\registry\src\index.crates.io-1949cf8c6b5b557f\hyper-util-0.1.19\src\client\legacy\pool.rs�pid:668:144eaa79-eb9c-4706-a491-074439ab28f0�3��yMsM�wei�+�%4�TRACEhyper_util::client::legacy::poolput; add idle connection for ("https", chatgpt.com)hyper_util::client::legacy::poolC:\Users\runneradmin\.cargo\registry\src\index.crates.io-1949cf8c6b5b557f\hyper-util-0.1.19\src\client\legacy\pool.rsbpid:668:144eaa79-eb9c-4706-a491-074439ab28f0�3��x
E/EQei�+�".TDEBUGcodex_client::default_clientRequest completedcodex_client::default_clientcodex-client\src\default_client.rsvpid:668:144eaa79-eb9c-4706-a491-074439ab28f0pZ��w
-ei�+�"+�LTRACElogshouldn't retry!pid:668:144eaa79-eb9c-4706-a491-074439ab28f0�I��v
?k?Iei�+��KTRACEcodex_api::sse::responsesunhandled responses event: response.in_progresscodex_api::sse::responsescodex-api\src\sse\responses.rsYpid:668:144eaa79-eb9c-4706-a491-074439ab28f0���	��u?��g?Iei�+���@TRACEcodex_api::sse::responsesSSE event: {"type":"response.in_progress","response":{"id":"resp_0d2445626ef902090169b52b8f59fc8191bbe897fc2a68eef0","object":"response","created_at":1773480847,"status":"in_progress","background":false,"completed_at":null,"error":null,"frequency_penalty":0.0,"incomplete_details":null,"instructions":"You are Codex, a coding agent based on GPT-5. You and the user share the same workspace and collaborate to achieve the user's goals.
                \"source_n
� ?
�"B
�	&E�(H�,K��'��s
MMKei�-$ؓ\INFOcodex_otel::traces::otel_managercodex_otel::traces::otel_managerotel\src\traces\otel_manager.rs�pid:668:144eaa79-eb9c-4706-a491-074439ab28f0c�'��r
MMKei�-$ؓ\INFOcodex_otel::traces::otel_managercodex_otel::traces::otel_managerotel\src\traces\otel_manager.rs�pid:668:144eaa79-eb9c-4706-a491-074439ab28f0c�\��q?�?Iei�-$��dTRACEcodex_api::sse::responsesunhandled responses event: response.function_call_arguments.deltacodex_api::sse::responsescodex-api\src\sse\responses.rsYpid:668:144eaa79-eb9c-4706-a491-074439ab28f0��k��p?�-?Iei�-$�pTRACEcodex_api::sse::responsesSSE event: {"type":"response.function_call_arguments.delta","delta":"_E","item_id":"fc_09e53a03ce50ae3a0169b52d2459e081919739a1081d8bbfb7","obfuscation":"oXahGw6PUIFpYC","output_index":1,"sequence_number":21}codex_api::sse::responsescodex-api\src\sse\responses.rs�pid:668:144eaa79-eb9c-4706-a491-074439ab28f0%�'��o
MMKei�-$�Z�INFOcodex_otel::traces::otel_managercodex_otel::traces::otel_managerotel\src\traces\otel_manager.rs�pid:668:144eaa79-eb9c-4706-a491-074439ab28f0c�[��n?�
?Iei�-$�&4TRACEcodex_api::sse::responsesunhandled responses event: response.custom_tool_call_input.deltacodex_api::sse::responsescodex-api\src\sse\responses.rsYpid:668:144eaa79-eb9c-4706-a491-074439ab28f0��l��m?�/?Iei�-$��TRACEcodex_api::sse::responsesSSE event: {"type":"response.custom_tool_call_input.delta","delta":" datetime","item_id":"ctc_0508041cc126e1bb0169b52d23e3188191be7601e5584d26b1","obfuscation":"mjmgmus","output_index":2,"sequence_number":113}codex_api::sse::responsescodex-api\src\sse\responses.rs�pid:668:144eaa79-eb9c-4706-a491-074439ab28f0&�'��l
MMKei�-$�INFOcodex_otel::traces::otel_managercodex_otel::traces::otel_managerotel\src\traces\otel_manager.rs�pid:668:144eaa79-eb9c-4706-a491-074439ab28f0c�\��k?�?Iei�-$���TRACEcodex_api::sse::responsesunhandled responses event: response.function_call_arguments.deltacodex_api::sse::responsescodex-api\src\sse\responses.rsYpid:668:144eaa79-eb9c-4706-a491-074439ab28f0��k��j?�-?Iei�-$��TRACEcodex_api::sse::responsesSSE event: {"type":"response.function_call_arguments.delta","delta":"IA","item_id":"fc_09e53a03ce50ae3a0169b52d2459e081919739a1081d8bbfb7","obfuscation":"dZYSKsWPA0os2X","output_index":1,"sequence_number":20}codex_api::sse::responsescodex-api\src\sse\responses.rs�pid:668:144eaa79-eb9c-4706-a491-074439ab28f0%�'��i
MMKei�-$�R�INFOcodex_otel::traces::otel_managercodex_otel::traces::otel_managerotel\src\traces\otel_manager.rs�pid:668:144eaa79-eb9c-4706-a491-074439ab28f0c�[��h?�
?Iei�-$�MTRACEcodex_api::sse::responsesunhandled responses event: response.custom_tool_call_input.deltacodex_api::sse::responsescodex-api\src\sse\responses.rsYpid:668:144eaa79-eb9c-4706-a491-074439ab28f0��l��g?�/?Iei�-$�(LTRACEcodex_api::sse::responsesSSE event: {"type":"response.custom_tool_call_input.delta","delta":" import","item_id":"ctc_0508041cc126e1bb0169b52d23e3188191be7601e5584d26b1","obfuscation":"43fu5ZVe2","output_index":2,"sequence_number":112}codex_api::sse::responsescodex-api\src\sse\responses.rs�pid:668:144eaa79-eb9c-4706-a491-074439ab28f0&�'��f
MMKei�-$�INFOcodex_otel::traces::otel_managercodex_otel::traces::otel_managerotel\src\traces\otel_manager.rs�pid:668:144eaa79-eb9c-4706-a491-074439ab28f0c�\��e?�?Iei�-$��TRACEcodex_api::sse::responsesunhandled responses event: response.function_call_arguments.deltacodex_api::sse::responsescodex-api\src\sse\responses.rsYpid:668:144eaa79-eb9c-4706-a491-074439ab28f0��[��d?�
?Iei�-$�spTRACEcodex_api::sse::responsesunhandled responses event: response.custom_tool_call_input.deltacodex_api::sse::responsescodex-api\src\sse\responses.rsYpid:668:144eaa79-eb9c-4706-a491-074439ab28f0�~�    \"dezembro\": 12,\r
    all_keys = [str(row[\"key\"]) for row in target_rows]
    if set(selected_targets) == set(all_keys):
        return \"Todos os nomes monitorados\"
    labels = [str(row[\"label\"]) for row in target_rows if str(row[\"key\"]) in set(selected_targets)]
    if not labels:
    return \" + \".join(labels)
def render_filter_buttons(target_rows: list[dict[str, Any]], active_targets: list[str]) -> str:
    active_set = set(active_targets)
    buttons: list[str] = []
    for row in target_rows:
        active_class = \" active\" if str(row[\"key\"]) in active_set else \"\"
        primary_class = \" primary\" if bool(row.get(\"primary\", False)) else \"\"
        buttons.append(
            <button type=\"button\" class=\"filter-chip__button__\" data-filter-target=\"__KEY__\">
              <span class=\"filter-chip__label\">__LABEL__</span>
              <span class=\"filter-chip__meta\">__COUNT__ historias</span>
            </button>
            .replace(\"filter-chip__button__\", f\"filter-chip{primary_class}{active_class}\")
            .replace(\"__KEY__\", html.escape(str(row[\"key\"])))
            .replace(\"__LABEL__\", html.escape(str(row[\"label\"])))
            .replace(\"__COUNT__\", str(int(row.get(\"storyCount\") or 0)))
    return \"\".join(buttons)
def render_story_index(stories: list[dict[str, Any]], visible_story_ids: set[int]) -> str:
    links: list[str] = []
    for story in stories:
        sid = int(story.get(\"storyIdInt\") or 0)
        hidden_attr = \"\" if sid in visible_story_ids else \" hidden\"
        links.append(
            <a class=\"story-index-link\" href=\"#story-__SID__\" data-nav-story-id=\"__SID__\"__HIDDEN__>
              <strong>__TITLE__</strong>
              <span>__COUNT__ noticia(s)</span>
            </a>
            .replace(\"__SID__\", str(sid))
            .replace(\"__TITLE__\", html.escape(str(story.get(\"title\") or \"Sem titulo\")))
            .replace(\"__COUNT__\", str(int(story.get(\"articleCount\") or 0)))
            .replace(\"__HIDDEN__\", hidden_attr)
    return \"\".join(links)
def render_article_card(article: dict[str, Any], label_by_key: dict[str, str]) -> str:
    label, preview_html, full_html = render_text_block(article)
    aid = int(article.get(\"article_id\") or 0)
    title = html.escape(str(article.get(\"title\") or \"Sem titulo\"))
    url = str(article.get(\"url\") or \"\").strip()
    source = str(article.get(\"source_name\") or \"Fonte nao identificada\").strip()
    source_host = host_from_url(url)
    external_link = (
        f'<a class=\"text-link\" href=\"{html.escape(url)}\" target=\"_blank\" rel=\"noreferrer\">Abrir materia original</a>'
        if url
        else \"\"
    full_toggle = \"\"
    if full_html:
        full_toggle = \"\"\"
        <details class=\"raw-details\">
          <summary>Ver texto bruto completo</summary>
          <div class=\"body-text full\">__FULL_TEXT__</div>
        </details>
        \"\"\".replace(\"__FULL_TEXT__\", full_html)
    title_html = title
    if url:
        title_html = f'<a href=\"{html.escape(url)}\" target=\"_blank\" rel=\"noreferrer\">{title}</a>'
    return (
        \"\"\"
        <article class=\"article-card\" id=\"article-__AID__\">
          <div class=\"article-top\">
            <div>
              <h3>__TITLE_HTML__</h3>
              <p class=\"article-meta\">
                <span>__SOURCE__</span>
                <span>__PUBLISHED__</span>
                <span>__HOST__</span>
              </p>
            <div class=\"chips\">__TARGET_BADGES__</div>
          </div>
          <div class=\"article-links\">__EXTERNAL_LINK__</div>
          <div class=\"summary-box __SUMMARY_CLASS__\">
            <div cla
�z
���
�
>���D���JÃ��?�[?Iei�+�^_�TRACEcodex_api::sse::responsesSSE event: {"type":"response.output_text.delta","content_index":0,"delta":"`
    monkeypatch.setattr(ingest, \"collect_wordpre�Gf__rpEKLpOP-A9avZ623jngZyfiDtl_EjAep7VnOL8n1JknHhyg6We0QSlaHTIlUycVwu_nlfPoPtSNLJOfMb6Mgf8uRy8yl1Oy8AnqrMT5ss6tpm-1Ij5un83NImNWNf_W8RFEs0dY8X4ohDvNsBz_lywmNA8BiRCN2Hoif6gls2Y4fdiURH4eKTvg9hjqvwBvN-x-63RB4-ZW2C98EX9LK-GQbjnbxnNrghCxFmg0L53cMlMXOhWL7PgrSapO-37Yh3c5bsHH-TKSE0HCM-doCtWG3_BmDTa4Ru_h6uySDOaMv5WuUJgA2yw7BjDXdh2hRP_Kn7WqfZZq27hb77VYr2c4uRutcpleuSXKwcRKbD5mYLrRYK5YzPBuJeZlJwHxgvOOSH1OITn95COdIlH75tItBKF9tSpHIaJisRWyug9mJ7sSinSYVOiFq5fazgCpY3-_SVrRRPLJ6zuWdPpsmtkPyPmvwN-4Di7zNt-cy8ZUXtUqGRHq0UWzT2dchCBxsw5HCZsucVGJ2Jjtyx5-j4ZTV6Fz0_4pUZoEGE-YiFIB_dyXT4yu1AKBGfRfaAHEshIkjMPmICnWDHNKENlriGMI5o5By_b__FRe45jexBkW-9Y4wzJ0bJU8gjYZUEzPVKbndDrUklmYuB8TxZ8dJrrEy7YIXNA6XMlHoh416-HCu8YCE1KFT_JUXzaz4qc3T-x65jzE7fYCIMVxyP7oGBmBZBJLmv4PbM8GpMK91aMewOqSd67cMtGpY3o1NfUGpqSqVqiTQAqMmUq1VyzXbjq-NljuNtdpPTufDVcZQ3DNcv-glqZGHSNOeVCSP3T90_UpgqoJG1wOfUHGf1WbQiXdWiHXgRT--nBn-pVuNmhVSK0gG7ZjPUEbvudHBLvF046DvWlC74v7iPUU9kAfVRCjV9Culy7qyhuVLhqUoJ1KFae_ZbOl6BimtELsnw60DF3A_XhGPR4zLqNHXJD7yZddwzOOKP776iiuThwKOIpwNrSEUUB9u7I9XrH6Y1Rv2_VU3KRwShRCM1XpYNP8-4NKTUsTnygff0aLe2wxdov_A3DFi1vxnP07wTKbwakSpZwcRRAfB1huOi6x3e-OooDg878kjXM_o5rGIONvoDFVxBeeMvGf_4Jo8NEwjWQqJDXNqjl6v8UyxEmPg8joz5mB528LGRIB40lxbteRON30eXSpHdwtmdZ6hED7g6fPm2GD8iPz6YaKRPUDgIgwLsGlEuMGIOTtJhPofWwZOlXwl1j7p9zy3RafbcajQ-FZkOJQjJOVUg4AE4Xq2WHmM5pCwfWjCjAsS6FI4OSMeafsb_9qXycKcNbU61rjcSD7G2wxyhYeBzphViw-NqzKXRkh-vIJhKmfE_5Qw2nRsvmgBxps37qM48kbBWFNUNJ_bQtMt4bh_0Pk81sTJ2JZcvaIDX9DvwSHnOw4jmiQtQQVmDMAyF0rH9WptxLCLgDwoHm1GWXx8UsKPg4TwyWCjLuNbV4FCpDWam6kJA2tad8zoxEhumeH7p3a161OfuxEEb3wBVkRMfCU5Jx2lgJzDnAxFqEBVOCEwtd9RJ8V2dpoFrpZB9bocZWcsEcKiGAaeUJq9-qzMb4xcuMbCkeJGf2X8PUh_lzbRaOXU0zrI5DYWZBvVy993zyZbAmECYqvcNcTevQslnOoZutjW75hYeKOuC5t59L2tBjVR_llS34XFgXnawgPKXqcEYvy9ZcelZJkY2XKpDdCs403vvXqlPdno7cxPbnaW3jnLJ_RZ3HFOsFzkQNywuss3Wj6P6P4KMzHelDvmEezxOiJThmZh5d2gr5A1HJXk_PwW6FojzqA0-wyhrztnR0x2JDtVlkDs0JWhFkbfZ1vErvW0xFyV0499Hcpo3iFMU2CfZ-z-OQT7r-A4TyrN2YTKdD5nmwz3Jo144V5DNK5l-XMGnTzoieqrEBFQ6iLbn4FV6jXvtcQok8T4gGxRkzBLwKippAvdrKib19inBDivpaeIYl4t3hr2-Fs2T_JkU2VhyNMnzhbdqlC8jQ3MOR_iy_mdWufgAfwmPRMtYLCmFOYv2Q9YQm5KhBwBMQYlb2IAbKfdiFkJGC9JUvXdHARaSykd6gesxvUZlKhChb6e4ckRtCMn-MzzRMzLvmTEmfjiIFaHXG9lbuFGYOp3_s66DgKxjJgEdDsQIoLJP-DLWIpqUWzS5cuz-HiGWgt52GID1sLE2qFnAhIGllRJEWnL5aPRevTaodzynA6u6V-JQcAGn0DW2OePW-s6J3RZFE4XXWXzbBs62eUsraAQ1DUMZVfX-Vj4IGsL68kHxKSL33WriSx6Kubm35zjG568c9YXDMlYfjO58J-N-gLy_gqZKkJBvXp0nkP_wkhw2SaYmJRmsxQqW5C9scLTCUFbh814DSGxitvG5SWg3FuELzGtuyhgFEbTlK8ybtswIZfnFESLyqyXlTDHbhKeHledSHcFxybq0QNIgCbjye2e-pTk4_Zbr___B6yi8ivzuOH_PwBxQGPZ1orkDBE9DyBfj5P2NdMOLVxAapDKN5IArq63c3GZvIXftP8iFh2Ko0DEsxfzUlJxJ6h4kGDACN_YrFyNnHuI5elErTzRwMYKlXS92X41cGpLXOyUfr2fFGDKOwB9nipRXTLILIkcbjk03_VhAXN6UrxNbTaMoT-17REhz1o5DZFVEqRuqAHZzXAD9pQ4Wb9mW-IHuaognYDwrG2ywJkFU25BeEoyf2dlTYUy6strNHmbffiwyGE3HTsvDVS4WD_yBd7Ad3Y4W-6MXzgXo6VeAtuojBzoBG2S9pzqIyT7vY9iVEvvYX_PS_cJ-FoZ3oDiAkrwDpkvnh7JavV12QfuMW6z0aMW-ncEmRgnbN-DBDAPQAg7iooIOL8evR0iTibsFekJzyOC-gtb6hoAo1x21cUJK2joLZHfMmEK8hPHwkgSnJvtthqx-Vs2Bx6kM1LCbCzI9KML4dgDmrWk4jQWz5lFzYnSAuCBvpwqW8pJ7V5Q5UU74if-6GKAqXpK4yyr_oDqHxuWQn4-vprMKZPg73iZ0XSJnlWmibxZ6SAYYEnol7Rm7Dja16K5AqzPMKClD5mrv6j_9uWq-VOFFRbpplM1lvev3wDAJKV5u18BI-n8qXVd6Tiag_WmZsvEmP2Yq4C9OybLqY3Pcw6LspjjCc14QZx80l9nGxm-gbiIbwLT0vBQp4v2vvnXHhdSHVPNESrUNDaf-oV-QPvfc3c693ka1KZEmRp9XxOQbA40hpdWrtMBvWFLCAZCY39tncoAlwmZSYNqZaXHJ01aOkWWWISz2nYDyApjpeDIB-ay8k-9fT_mbqoe5nPopWHQp_VYh_qn34zO2kDZ2fsIZ4eZOAOm3GzbWlIv0jRqscuP0Ue9WcTT3Acr9fczNpnqGoLhHeHGIliiCSUoKUBcROk_IIJm5RvGJDGEdFOyW4k_NEaIhPfHkyzOjRpaSbFy2lYJqBipptwy058KUCnK8lzhY5ScAMJiRaFSbt4R-YkxDWQYhD4KTv3xeJMcluFjz5cNLDGHKGrLIEpyxFk4STPHCN3a3aA2f_PwBerg7F2YUMCbJa29L9_2XY_tStLFjwL2hIfF0TSvpejM5OzYN8JPt_1jAdRPuhMlG32vFFjJJrnnu3sFV_NmRyzaaRl7MdVthu5tEFl0H3kCV4hi63sD07uH6bcyGCloOVkCj5RKPZ_mP8ium1w0Xk-3uPgtlR8ItoTzkJKr0g0opOslABcScaVQ1nUnE6qjX6KP4-g04DH6U9EortqWpTSA_oPTLr1F32eiTS4sjC9YVA5bwIBb3GDF76tH-irZVrq6DmeImQ_uxiYaZBiGJP4vXPeUIu3ONtjaUf0on50Ase_A1USEQtFL9a8-wkVq0xcTATmfqLdKiKfpxWgyqXDQR9rcBohgW6irPLYfIyB21mUWmyrO_Gm9tGj3shhU7D8yh5Zav8sx2_8Dfs8qjc4ivaZUxJIpF1zV4khXrwiKlYJI7HNoyjdMzc05DF-SqcPfgbNzzzZ9Wewyz6o7qy4LajYuNmugX2YoL54V78EyQee31Wnek7MWH3ui3up8mHM
i�z7��n+
�
�
b
��V��J
�
�
>	�	�	u	2��iBipid:16064:fd12f7dd-9a49-4dd6-86ab-3f584b043267i�77	vx�n�nBipid:16064:fd12f7dd-9a49-4dd6-86ab-3f584b043267i�77%�5��o�oBipid:16064:fd12f7dd-9a49-4dd6-86ab-3f584b043267i�77%�Y�p�pBipid:16064:fd12f7dd-9a49-4dd6-86ab-3f584b043267i�77%�r��q�qBipid:16064:fd12f7dd-9a49-4dd6-86ab-3f584b043267i�77%����r�rBipid:16064:fd12f7dd-9a49-4dd6-86ab-3f584b043267i�77%���s�sBipid:16064:fd12f7dd-9a49-4dd6-86ab-3f584b043267i�77%��$�t�tBipid:16064:fd12f7dd-9a49-4dd6-86ab-3f584b043267i�77%�]D�u�uBipid:16064:fd12f7dd-9a49-4dd6-86ab-3f584b043267i�77%�q0�v�vBipid:16064:fd12f7dd-9a49-4dd6-86ab-3f584b043267i�77%��`�w�wBipid:16064:fd12f7dd-9a49-4dd6-86ab-3f584b043267i�77%����x�xBipid:16064:fd12f7dd-9a49-4dd6-86ab-3f584b043267i�77%����y�yBipid:16064:fd12f7dd-9a49-4dd6-86ab-3f584b043267i�77%��,�z�zBipid:16064:fd12f7dd-9a49-4dd6-86ab-3f584b043267i�77%��X�{�{Bipid:16064:fd12f7dd-9a49-4dd6-86ab-3f584b043267i�77%�#x�|�|Bipid:16064:fd12f7dd-9a49-4dd6-86ab-3f584b043267i�77%�o��}�}Bipid:16064:fd12f7dd-9a49-4dd6-86ab-3f584b043267i�77%ƅ��~�~Bipid:16064:fd12f7dd-9a49-4dd6-86ab-3f584b043267i�77%ƛd��Bipid:16064:fd12f7dd-9a49-4dd6-86ab-3f584b043267i�77%�������Bipid:16064:fd12f7dd-9a49-4dd6-86ab-3f584b043267i�77%��0����Bipid:16064:fd12f7dd-9a49-4dd6-86ab-3f584b043267i�77%������Bipid:16064:fd12f7dd-9a49-4dd6-86ab-3f584b043267i�77%������Bipid:16064:fd12f7dd-9a49-4dd6-86ab-3f584b043267i�77%������Bipid:16064:fd12f7dd-9a49-4dd6-86ab-3f584b043267i�77%�(�����Bipid:16064:fd12f7dd-9a49-4dd6-86ab-3f584b043267i�77%�o����Bipid:16064:fd12f7dd-9a49-4dd6-86ab-3f584b043267i�77%�~�����Bipid:16064:fd12f7dd-9a49-4dd6-86ab-3f584b043267i�77%� �����Bipid:16064:fd12f7dd-9a49-4dd6-86ab-3f584b043267i�77%�6�����Bipid:16064:fd12f7dd-9a49-4dd6-86ab-3f584b043267i�77%�}������$ss_api\", fake_collect_wordpress_api)
    def fake_collect_wordpress_ap
Brr=�?oz��������t��Y
_k__ei�`�
H�TRACEcodex_app_server::codex_message_processorapp-server event: codex/event/patch_apply_begincodex_app_server::codex_message_processorapp-server\src\codex_message_processor.rsypid:668:144eaa79-eb9c-4706-a491-074439ab28f0��K��X
MMKUei�`�
F�XINFOcodex_otel::traces::otel_managercodex_otel::traces::otel_managerotel\src\traces\otel_manager.rs�019ce360-cc34-7e23-8e87-7abff913dfafpid:668:144eaa79-eb9c-4706-a491-074439ab28f0c�-W
MMKei�`�5�DINFOcodex_otel::traces::otel_man�n��h
____ei�a
�TRACEcodex_app_server::codex_message_processorapp-server event: codex/event/token_countcodex_app_server::codex_message_processorapp-server\src\codex_message_processor.rsypid:668:144eaa79-eb9c-4706-a491-074439ab28f0��K��g
MMKUei�a

�dINFOcodex_otel::traces::otel_managercodex_otel::traces::otel_managerotel\src\traces\otel_manager.rs�019ce360-cc34-7e23-8e87-7abff913dfafpid:668:144eaa79-eb9c-4706-a491-074439ab28f0c�W��f
E/EQUei�a
4�DEBUGcodex_client::default_clientRequest completedcodex_client::default_clientcodex-client\src\default_client.rsv019ce360-cc34-7e23-8e87-7abff913dfafpid:668:144eaa79-eb9c-4706-a491-074439ab28f0p~��e
-Uei�a
	�(TRACElogshouldn't retry!019ce360-cc34-7e23-8e87-7abff913dfafpid:668:144eaa79-eb9c-4706-a491-074439ab28f0���d
'//Uei�`�^g�INFOfeedback_tagscodex_core::codexcore\src\codex.rs�019ce360-cc34-7e23-8e87-7abff913dfafpid:668:144eaa79-eb9c-4706-a491-074439ab28f03�9��c
/?//Uei�`�W�TRACEcodex_core::codexpost sampling token usagecodex_core::codexcore\src\codex.rs 019ce360-cc34-7e23-8e87-7abff913dfafpid:668:144eaa79-eb9c-4706-a491-074439ab28f0Qb
_k__ei�`�
M�XTRACEcodex_app_server::codex_message_processorapp-server event: codex/event/raw_response_itemcodex_app_server::codex_message_processorapp-server\src\codex_message_processor.rsypid:668:144eaa79-eb9c-4706-a491-074439ab28f0��a
QSQQei�`�
MW�TRACEcodex_app_server::outgoing_messageapp-server event: turn/diff/updatedcodex_app_server::outgoing_messageapp-server\src\outgoing_message.rsvpid:668:144eaa79-eb9c-4706-a491-074439ab28f0��`
_[__ei�`�
L�TRACEcodex_app_server::codex_message_processorapp-server event: codex/event/turn_diffcodex_app_server::codex_message_processorapp-server\src\codex_message_processor.rsypid:668:144eaa79-eb9c-4706-a491-074439ab28f0��_
QeQQei�`�
L�(TRACEcodex_app_server::outgoing_messageapp-server event: account/rateLimits/updatedcodex_app_server::outgoing_messageapp-server\src\outgoing_message.rsvpid:668:144eaa79-eb9c-4706-a491-074439ab28f0�^
QcQQei�`�
L�`TRACEcodex_app_server::outgoing_messageapp-server event: thread/tokenUsage/updatedcodex_app_server::outgoing_messageapp-server\src\outgoing_message.rsvpid:668:144eaa79-eb9c-4706-a491-074439ab28f0��]
____ei�`�
K�lTRACEcodex_app_server::codex_message_processorapp-server event: codex/event/token_countcodex_app_server::codex_message_processorapp-server\src\codex_message_processor.rsypid:668:144eaa79-eb9c-4706-a491-074439ab28f0��\
QMQQei�`�
KS�TRACEcodex_app_server::outgoing_messageapp-ser�\��k
QeQQei�a
$,TRACEcodex_app_server::outgoing_messageapp-server event: account/rateLimits/updatedcodex_app_server::outgoing_messageapp-server\src\outgoing_message.rsvpid:668:144eaa79-eb9c-4706-a491-074439ab28f0��j
QcQQei�a
PTRACEcodex_app_server::outgoing_messageapp-server event: thread/tokenUsage/updatedcodex_app_server::outgoing_messageapp-server\src\outgoing_message.rsvpid:668:144eaa79-eb9c-4706-a491-074439ab28f0����i
SUei�a
z�TRACElogwindows::current_platform is called019ce360-cc34-7e23-8e87-7abff913dfafpid:668:144eaa79-eb9c-4706-a491-074439ab28f0+�k��S-�%--Uei�`�	��ERRORcodex_core::execexec error: O nome do arquivo ou a extensão é muito grande. (os error 206)codex_core::execcore\src\exec.rs�019ce360-cc34-7e23-8e87-7abff913dfafpid:668:144eaa79-eb9c-4706-a491-074439ab28f0��'i(query: str, *, source_name: str, base_url: str, **kwargs):
            date_fro
�
�
�
�
�������'��r
MMKei�-�INFOcodex_otel::traces::otel_managercodex_otel::traces::otel_managerotel\src\traces\otel_manager.rs�pid:668:144eaa79-eb9c-4706-a491-074439ab28f0c�[��q?�
?Iei�-��TRACEcodex_api::sse::responsesunhandled responses event: response.custom_tool_call_input.deltacodex_api::sse::responsescodex-api\src\sse\responses.rsYpid:668:144eaa79-eb9c-4706-a491-074439ab28f0��k��p?�-?Iei�-��XTRACEcodex_api::sse::responsesSSE event: {"type":"response.custom_tool_call_input.delta","delta":"@@","item_id":"ctc_08793bbc6dee6c120169b52d1e57708191bc8bc87c6f976b9a","obfuscation":"fuglpvj5tVGo16","output_index":1,"sequence_number":33}codex_api::sse::responsescodex-api\src\sse\responses.rs�pid:668:144eaa79-eb9c-4706-a491-074439ab28f0%�'��o
MMKei�-��(INFOcodex_otel::traces::otel_managercodex_otel::traces::otel_managerotel\src\traces\otel_manager.rs�pid:668:144eaa79-eb9c-4706-a491-074439ab28f0c�[��n?�
?Iei�-F�TTRACEcodex_api::sse::responsesunhandled responses event: response.custom_tool_call_input.deltacodex_api::sse::responsescodex-api\src\sse\responses.rsYpid:668:144eaa79-eb9c-4706-a491-074439ab28f0��l��m?�/?Iei�-F��TRACEcodex_api::sse::responsesSSE event: {"type":"response.custom_tool_call_input.delta","delta":"
    monkeypatch.setattr(ingest, \"process_candidates\", fake_pr��Admin\\\\.vscode\\\\docs\\\\The Clipping project\\\\tools\\\\export_mobile_snapshot.py' | Select-Object -First 220\",\"workdir\":\"c:\\\\Users\\\\Admin\\\\.vscode\",\"timeout_ms\":10000}","call_id":"call_3nifDn1dYQz5V8V210OUfADo"},{"type":"function_call",
        wordpress_calls.append((source_n��ame, query))