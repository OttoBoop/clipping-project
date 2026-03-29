import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

import pipeline.collectors as collectors
import pipeline.ingest as ingest
from pipeline.collectors import CandidateArticle
from pipeline.ingest import IngestionOptions, process_candidates
from pipeline.matcher import CitationMatcher, Target


def test_collect_sitemap_daily_cbn_skips_query_prefilter(monkeypatch):
    xml = """
    <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:news="http://www.google.com/schemas/sitemap-news/0.9">
      <url>
        <loc>https://cbn.globo.com/rio-de-janeiro/noticia/2025/05/21/paes-deve-participar-na-proxima-semana-de-reuniao-para-debater-decreto-sobre-praias-com-vereadores.ghtml</loc>
        <news:news>
          <news:publication_date>2025-05-21T14:08:07Z</news:publication_date>
          <news:title>Paes deve participar na prÃ³xima semana de reuniÃ£o para debater decreto sobre praias com vereadores</news:title>
        </news:news>
      </url>
    </urlset>
    """

    monkeypatch.setattr(collectors, "fetch_url", lambda url, timeout=10: (url, xml))

    items = collectors.collect_sitemap_daily(
        queries=["Flavio Valle"],
        sources=[
            {
                "source_name": "CBN Sitemap",
                "host": "cbn.globo.com",
                "sitemap_url_template": "https://cbn.globo.com/sitemap/cbn/{yyyy}/{mm}/{dd}_1.xml",
                "prefilter_queries": False,
            }
        ],
        date_from="2025-05-21",
        date_to="2025-05-21",
        limit_per_source=20,
        request_timeout=3,
    )

    assert [item.url for item in items] == [
        "https://cbn.globo.com/rio-de-janeiro/noticia/2025/05/21/paes-deve-participar-na-proxima-semana-de-reuniao-para-debater-decreto-sobre-praias-com-vereadores.ghtml"
    ]
    assert items[0].metadata["query_prefilter_applied"] is False
    assert items[0].metadata["exact_body_only"] is True


def test_citation_matcher_exact_names_only_supports_explicit_aliases():
    matcher = CitationMatcher(
        [
            Target(
                key="flavio_valle",
                display_name="Flavio Valle",
                priority=1,
                keywords=["Flavio Valle"],
                exact_aliases=["Flavio Vale"],
            )
        ],
        exact_names_only=True,
    )

    hits = matcher.find_hits("O vereador Flavio Vale, do PSD, tambÃ©m relatou a experiÃªncia.")

    assert len(hits) == 1
    assert hits[0].target_key == "flavio_valle"
    assert hits[0].keyword == "Flavio Vale"


def test_process_candidates_accepts_flavio_vale_alias(monkeypatch, tmp_path: Path):
    db_path = tmp_path / "cbn_alias.db"
    monkeypatch.setattr(ingest, "DB_PATH", db_path)

    monkeypatch.setattr(
        ingest,
        "get_active_targets",
        lambda: [
            Target(
                key="flavio_valle",
                display_name="Flavio Valle",
          pX\xa0\x83\x8c6cQ`\x9f_%Q\xf9\xeb\xae\xecrU\xbdY\xbd\xac\x0c\xe3\xf1\xbd\xa0\xea\xd9\xa5\xe8E\x8f_T\xf9x)\x9as\xc3\xdb7\xa3/h)\xb9+\xbd\xd1\xce\xd9\xad\xe9\x0bZI\xefQo4s~\xa3\x9a\xb4\xf3\xcf\x12W\xbe[\xa7qWU\x94\x8a0\x9a\x93\xe4\xeaI\xb9\xff\x91\xf3d\x07\xeb\x97\xb6W\xd6L\xa8\x07\xf5a\x16\xec\x04W\xbf^F\xf9\x98\xec\x91+\r\x03\x90B\x82,~K\0\xd8\xed\xff\xf1T\xb3p\xc7\x08\xe6\x1e\xa8[\xc6F\0t2\x05\xc9\xed\x0e\xf8|\x14.\xee\xeb+^ m|<\x1e\xb8\xd2\xcb\xa1,\xce\x088I&\x19\xc6
\x99\xa2\xf5!\x89=\x95\x06%?\xc6D{8v\xe1\x98bn\xff\x90\xac:$R\x99M\xc8s\x87\xd1\x9bRd\xe4$!L\xb3\xe8\x11\xd9-\z\x01\xa6\x1dUL\xb9a\xedQX\xfe\xef.\xda\xbc\xdc\x86\xe9\xcbT\x19\xaeR\x1a:[\xd5\x0b\xd6)%\xd5\xc9\xb7\xfb\x0eo9\xa3C\x7f&96\xc1\xc8\xa0e;\xbc\xcb\xfcGR\x9d\x1f\xa8\x08=\xa35\xf0 \x11\xdcU\xbd%\xbb\xedY\xe5[v\xbb\x9a\xcb\xf1\xe9\xad*\xa4\x13\x99\xa6\x03~N5/R\x14\xbak	\xa6>\xbewX\xb9\xa3\xbc\x0eL7\xb2\xd5$\x80\xcd\xe5~\xc9\x0f.A\xa4(\xe0\xd8\x12\xfc\xf7\xdf\x189\x1b>e\x7f\xbb\xa3\xbd{\x9a\x82\xf2\xe6\xeex\x91\xf1\xd9\x15\xd0[\xb6Y\xb7\xf88X\xd4<\x0f4h\xf6\x96\x85\xda]\xa1\xfa\x12`\xa2\xc1I-\xd7>'\xf6g_[\x0f\xfb\xc6z\xf8\xf3\xf5\x9e\xb1~{\xa9\x90\x9e)\xf3nL\xd3w\x99\xca\xdd\x15\xab\xce\xa4*\x18\x86\x0f\x9c\x87\x0b\xa1\xfb1\xd5\x7f}e3\xa9\x88w\xa7\x95\xe3T|\xa1\x91z6\xdc\x94\x06\x14\x0c\xdf\x8d\xbc k)3\x85;\xc7\xa3\x0f/n.\x9d\xb3\x8c\xc8\6x9\xe7\x1f\xbe\x87\x8c\xff#\x88\xc2i\xf8\xd5kE\xd0\xc7\xbbRv\xa2U\x82\xc7;\xc0\x12\xf3\x89\xbe\xa6\x18\x8f\x86\xed\xcaI\xc3\xffJ\xb2\xae\xc3\xb6\xbe\xc4/a\xa1B\xf1\x84
I\xda\x8a\x9b=x~%\xa15\x83\x03Q\xec\x9b\x07rD\xc1\xf3a@7\x8b7\x1f\xc6\xf8\x18\xc5\xed[\xc6q\xda\x90g\x03\xf9\x9eA\xdcD\xf7\xf4!\xc7\xb8+\x14\xcdK}\xfee\xa5\xf9\x8efC\xcb\x80\x8b\x0f	o\xb2\x02\xcf\x96\xf6\xc7\xf4\xdb\x80B\xecC\x13\x08\xa6\xf8\xd5\x0e\xc9\xfd3\xd3B^R\xe8\xaa\xc8\xa9\x8d\xf43~\xea\xf4i\xbb\x9cZ\x12-p z\xd2\xa1\xebF\xae`\xc4\x9a\x1fdI&\xe1%2J\x9c\xc1H\x1f\xfe:\xce\x86#\xa7\xaeY\xb00\xf1\xe4\xad\x08$r\x98\x0e\xe0c\x81\x84\x9f\x92\xda\xdf`!q\xcf\xfa\xe6e\x16\x12\xb7lf\x9e\xb1Op\0Z&B\x9e\xef\xc2\xb8\x82\xd0z W|\xa7B\xda-\xcb\x82\x93\xa1\x02\xb4\x10\x90\xd2\x83_\xf1\xfa\xfe \xb5\xcb\x83n\x7f\xd7\x86\x0c\xc7\xfa\xa9L\x18\x05\xc9\xc6\xc8\xd0\x04\x9cA#hg\x03\xbb\x06d\xda\x19T*[G\xaf\xde$"\r\x1c\xbca\x1c\xf6G\xf2)\x87\xffk\xfa\xf3\x0b\x86\xfb\x17
\xac\xb4FF{o\x97\xff#\xebWWr" \x02C\rs\0\xaf$\xe0\xeb\xc1\x95z\x1e\x8cN\xcb\xcd\x02\xa2\xe0h\x12\xe0\x9dB%>5\x08\0\x022\xbc\xf7\xb7$;\xc8\x8d\x02\xa2 \xc9\x0e\xe0\xa4\xe7\xf3T\xcd\x9e\x1f2\x83+\x1d;<\x8b\x9e\xa9\xca\xe1\xb8\x93\x99\xe4#/\xf3sp\x13-%\x8c)\xf6\xd9I\xefS
\x7f\xf4\x07\\xaf\xd4\x143\x05\xe3\x1f\x90\xf6\xec\x01\x9b)hNl\xf9\xae\x03m\xd6@+\xd8ca\0\x0e\xb4\x85?2\xad\xe4\x1f\x10\xda\x1f\xe7*\xca?R\x8b\x82\xa4\x07\xf9\xe9\xf4\x88\x0e\xf9\xa5\xb0\x93\xad\xf4c\x8a|\xda\x85\xdd\x8b\xaa\x05\x96\x01-Z\xf2\xfb\x84Kk\x08\xd8\x18,v\xb4\xf6LMHad\xcf \x95\xf8\x8f\xc7_,\xc7\xa0&\xccZb\xdb\xf0\xd7\x1f\x7f\xfc\xe1A\x07\xc0\xc40\xef\xb3\x93\xd2\x83Bq]\x88\xc1H\x0b\x8f\xf0\xdf\xcfN\xfa\xbf\xcf|\xa2\xd0\r>\x7f.\x81M\x1b\x83\x19}\xf4\x02\x14\xd4\xb1\xbc\x82\x95\xb6X(\xfa\x89n\xc0\xf2\xb5\xc4\xaa\xef1\x84\xf1\x89a\xa2\xcbt`N\x1a\xe3:\xbfX\xfbx\xa3\x07\xcbl\xcf\xe4Sp\xac\x0e\xfa\x9d+\x0f\x83#\xca'\xca\x16Hs\x8a\x85jj\xde\x91\x14xL_M\x9eZy$:\x98dI2-LV\xb4\xa9?w\xcfc\x85\xf7l?NF\x1f\x99V\xe5\x89\xedG\xde\xd5\x9b\xca\x9a\x14x-\xd5Y\xdd\xd7\xd8\x1c\x0f\xfbg\xa1G\x13B\x91D\x8c\xbeq\x08\rr\xb8\xe7J\x9c\x14X.	\x9en\x8e\xf6\xb9\xfa&\x9b\x8b\x99\x04\x03\xad^*q\xb2O\xd5\xe3&\xcb\xae\x9c\xb2\xf7#h\x1d|S\x89\x97\x178\x9b\xbe\xa7]=6q4-\x86s\0\xe8\xae&\xad\x8fn@\x05\x80hZ\xe2y\xef\xa6s\x9cm\xe7\x1c\xab\xb9Ku\x1f|[\xb2\xb7\xd2>(\xe4\xe1T\xcf\xa8tz\xef\x99\x14\xcc\xf7}\xa6#\xfa\x98R\xaf{\x86Z\xc9\x9eO\xb7\xd3\xc7\xa3\xda\x0eL\xd5Q?\x96\x9f\x95>;\xf8\xd1\x94\xe7\xe3q\x10\x0f\xe9\x91\xfe![\xbf3Q<\xdf\xfb\xc7\xe1Bn\x96)\x19\x92}\xfct\xe6\xbel\xdf\x03m\x9dTWK,\xe9@[0\xbe\xac\x93\x86F\x84\xbe\xc1\xa7	\xc9c\x87\x1c\x99\xcc\xd1]\xef\xccQ/r\xf2>\x9e^\x9e,\xd7\xc3\xafd,\x85\xad\x14@\xf5\x87\xeb\xa4\xfcUS\xaf\xa3\xebjkYS\xd5\xd3\x9e:z\xa8\xe5\xdd\x06\x9dm\xc2Al\xe1\x90\x94U\x8a>\xe7\xc6\xf2\xc7k\xd7\xa3Z \xa1\xa00\xaaLR6I \x93y$pYn6282:                                ${data.alunos.map(a => `<tr><td><strong>${a.nome}</strong></td><td>${a.matricula || '-'}</td><td>${a.email || '-'}</td><td><button class="btn btn-sm" onclick="showAluno('${a.id}')">Ver</button> <button class="btn btn-sm btn-danger" onclick="excluirAluno('${a.id}')">🗑️</button></td></tr>`).join('')}
6295:            currentAluno = null;
6323:                        <button class="btn btn-primary" onclick="openModalPipelineCompleto('${atividadeId}', 'aluno')" data-tooltip="Corrige automaticamente a prova de um aluno específico" data-tooltip-pos="bottom">⚡ Pipeline Aluno</button>
6329:                        <div class="stat-card"><div class="stat-value">${data.alunos.total}</div><div class="stat-label">Alunos na turma</div></div>
6338:                        <div class="card-header"><h3 class="card-title">👥 Provas dos Alunos</h3><button class="btn btn-primary btn-sm" onclick="openModalUpload('${atividadeId}', 'aluno')">+ Upload Prova</button></div>
6339:                        <div class="table-container"><table><thead><tr><th>Aluno</th><th>Prova</th><th>Correção</th><th>Relatório</th><th>Ações</th></tr></thead><tbody>
6340:                            ${data.alunos.detalhes.map(a => `<tr><td><strong>${a.aluno_nome}</strong></td><td>${a.tem_prova ? '<span class="badge badge-success">✓</span>' : '<span class="badge badge-danger">Falta</span>'}</td><td>${a.tem_correcao ? '<span class="badge badge-success">✓</span>' : '<span class="badge badge-warning">Pendente</span>'}</td><td>${a.tem_relatorio ? '<span class="badge badge-success">✓</span>' : '<span class="badge badge-warning">Pendente</span>'}</td><td><button class="btn btn-sm" onclick="showResultadoAluno('${atividadeId}', '${a.aluno_id}')">Ver Resultado</button></td></tr>`).join('')}
6477:        async function showAlunos() {
6480:            setBreadcrumb([{nome: 'Início', onclick: 'showDashboard()'}, {nome: 'Todos os Alunos', onclick: 'showAlunos()'}]);
6486:                    <div class="page-header"><h1 class="page-title">Todos os Alunos</h1><p class="page-subtitle">${data.alunos.length} aluno(s)</p></div>
6488:                        <div class="card-header"><h3 class="card-title">Lista de Alunos</h3><button class="btn btn-primary btn-sm" onclick="openModal('modal-aluno')">+ Novo</button></div>
6491:                                ${data.alunos.map(a => `<tr><td><strong>${a.nome}</strong></td><td>${a.matricula || '-'}</td><td>${a.email || '-'}</td><td><button class="btn btn-sm" onclick="showAluno('${a.id}')">Ver Turmas</button> <button class="btn btn-sm btn-danger" onclick="excluirAluno('${a.id}')">🗑️</button></td></tr>`).join('')}
6691:        async function showChatGeral(preselectedAtividadeId = null, preselectedAlunoId = null) {
6697:            window._chatGeralAlunoId = preselectedAlunoId;
7167:        async function showAluno(alunoId) {
7172:                setBreadcrumb([{nome: 'Início', onclick: 'showDashboard()'}, {nome: 'Alunos', onclick: 'showAlunos()'}, {nome: data.aluno.nome, onclick: `showAluno('${alunoId}')`}]);
7177:                        <button class="btn" onclick="showDashboardAluno('${alunoId}')">📊 Dashboard do Aluno</button>
7180:                        <div class="card-header"><h3 class="card-title">Turmas do Aluno (${data.total_turmas})</h3></div>
7217:        let todosAlunos = [];  // Cache de todos os alunos para filtragem
7218:        let alunosDisponiveis = [];  // Alunos que não estão na turma atual
7222:        async function openModalAluno(turmaId) {
7232:            switchAlunoTab('selecionar');
7235:            await carregarAlunosParaSelecao(turmaId);
7240:        function switchAlunoTab(tab) {
7263:        async function carregarAlunosParaSelecao(turmaId) {
7270:                todosAlunos = resultAll.alunos || [];
7281:                alunosDisponiveis = todosAlunos.filter(a => !idsNaTurma.has(a.id));
7286: