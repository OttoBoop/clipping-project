(() => {
  "use strict";
  const $ = id => document.getElementById(id);
  const state = {targets: [], defaultTargets: [], sources: [], selected: new Set(), items: [], cursor: "", previous: [], next: "", storyId: "", job: null, csrf: "", configured: false, canRun: false, sequence: 0, article: null, classifications: []};
  const pageParams = new URLSearchParams(location.search);
  const simulation = pageParams.get("as_profile");
  const clientProfile = pageParams.get("client");
  const activeStates = new Set(["queued", "running", "cancel_requested", "reviewing"]);
  const labels = {queued: "Na fila", running: "Coleta em andamento", reviewing: "Revisão em andamento", succeeded: "Concluída", completed: "Concluída", complete: "Concluída", completed_with_gaps: "Concluída com pendências", cancelled: "Cancelada", cancel_requested: "Cancelamento solicitado", failed: "Falha na coleta", interrupted: "Interrompida", retryable: "Aguardando nova tentativa", blocked: "Fonte indisponível", exhausted: "Consulta concluída", empty_verified: "Sem resultados no período", empty_unverified: "Resultado vazio sem confirmação", capped: "Limite de resultados atingido", available: "Texto disponível", metadata_only: "Somente referência", legacy_body: "Texto preservado do arquivo", pending: "Texto pendente"};
  const text = (tag, value, cls) => {const e = document.createElement(tag); e.textContent = value == null ? "" : String(value); if (cls) e.className = cls; return e;};
  const displayName = key => state.targets.find(t => t.key === key)?.display_name || state.targets.find(t => t.key === key)?.label || key;
  const sourceName = key => state.sources.find(s => s.key === key)?.name || key;
  const gapCount = metrics => (metrics.tasks || []).filter(t => ["gap", "failed", "retryable"].includes(t.status)).reduce((n, t) => n + Number(t.count || 0), 0);
  function gapReason(code = "") {
    if (/429/.test(code)) return "A fonte limitou os acessos; nova tentativa necessária.";
    if (/403|401|blocked/.test(code)) return "A fonte não permitiu o acesso público.";
    if (/timeout/i.test(code)) return "A fonte demorou além do limite de espera.";
    if (/google_daily_result_cap/.test(code)) return "O limite diário de resultados impede confirmar a cobertura completa.";
    if (/cap|too_large/.test(code)) return "O limite desta consulta foi atingido; a cobertura está incompleta.";
    if (/body_missing|extract/.test(code)) return "O texto principal não pôde ser extraído.";
    if (/google_url_unresolved/.test(code)) return "O link da publicação original não pôde ser resolvido.";
    if (/malformed|parsing|xml|json|markup|cyclic/i.test(code)) return "A resposta da fonte não pôde ser interpretada.";
    if (/404/.test(code)) return "A página não foi encontrada; a consulta precisa de revisão.";
    return code ? "A consulta falhou e precisa de revisão." : "";
  }
  const formatDate = value => {if (!value) return "Data a revisar"; if (/^\d{4}-\d{2}-\d{2}$/.test(value)) return value.split("-").reverse().join("/"); const d = new Date(value); return Number.isNaN(d.valueOf()) ? "Data a revisar" : d.toLocaleDateString("pt-BR", {timeZone: "America/Sao_Paulo"});};
  const classificationRows = value => (Array.isArray(value) ? value : value.classifications || value.items || []).map(row => ({...row, ...(row.payload || {})}));
  function message(value, error = false) {$("message").textContent = value; $("message").classList.toggle("error", error);}
  async function api(path, options = {}) {
    const url = new URL(path, location.origin);
    if (simulation) url.searchParams.set("as_profile", simulation);
    if (clientProfile) url.searchParams.set("client", clientProfile);
    const headers = {...options.headers};
    if (options.body) {headers["Content-Type"] = "application/json"; headers["X-CSRF-Token"] = state.csrf;}
    if (options.method && options.method !== "GET") headers["X-CSRF-Token"] = state.csrf;
    const response = await fetch(url, {...options, headers, credentials: "same-origin", cache: "no-store"});
    if (response.status === 401) {location.assign("/"); throw new Error("Entre novamente para continuar.");}
    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
      const known = {political_service_unavailable: "A coleta ainda não está disponível. Tente novamente após a configuração do serviço.", political_scope_denied: "Este registro não está disponível para o seu perfil.", political_record_not_found: "Esta notícia não foi encontrada ou não está disponível para o seu perfil.", select_allowed_targets: "Selecione pelo menos um nome disponível.", archived_target: "Um nome selecionado foi arquivado. Atualize a página.", simulation_is_read_only: "Saia da simulação para alterar dados."};
      throw new Error(known[data.detail] || (response.status === 403 ? "Seu perfil não pode realizar esta ação." : "Não foi possível concluir esta ação. Tente novamente."));
    }
    return data;
  }
  function renderGroups() {
    const groups = new Map();
    for (const target of state.targets) {
      const key = target.group || "existing";
      if (!groups.has(key)) groups.set(key, {label: target.group_label || "Outros nomes acompanhados", targets: []});
      groups.get(key).targets.push(target);
    }
    $("groups").replaceChildren();
    for (const [key, group] of groups) {
      const field = text("fieldset", "", "group"); field.append(text("legend", group.label));
      const select = text("button", "Selecionar grupo"); select.type = "button";
      select.addEventListener("click", () => {const all = group.targets.every(t => state.selected.has(t.key)); group.targets.forEach(t => all ? state.selected.delete(t.key) : state.selected.add(t.key)); renderGroups();});
      field.append(select);
      for (const target of group.targets) {
        const label = document.createElement("label"), input = document.createElement("input");
        input.type = "checkbox"; input.value = target.key; input.checked = state.selected.has(target.key);
        input.addEventListener("change", () => input.checked ? state.selected.add(target.key) : state.selected.delete(target.key));
        label.append(input, text("span", target.display_name || target.label)); field.append(label);
      }
      field.dataset.group = key; $("groups").append(field);
    }
  }
  function filters() {
    const query = new URLSearchParams({page_size: "50"});
    state.selected.forEach(key => query.append("target_key", key));
    for (const [id, key] of [["query", "q"], ["date-from", "date_from"], ["date-to", "date_to"], ["source", "source_key"], ["body-status", "body_status"]]) if ($(id).value) query.set(key, $(id).value);
    if (state.cursor) query.set("cursor", state.cursor);
    if (state.storyId) query.set("story_id", state.storyId);
    return query;
  }
  function articleCard(article) {
    const card = text("article", "", "news-card");
    card.append(text("div", `${article.sourceName || article.sourceKey || "Fonte a revisar"} · ${formatDate(article.publishedAt)}`, "news-meta"));
    const heading = text("h3", ""), link = text("a", article.title || "Notícia sem título");
    try {const url = new URL(article.url); if (["https:", "http:"].includes(url.protocol)) {link.href = url.href; link.target = "_blank"; link.rel = "noopener noreferrer";}} catch (_) { /* Missing source URL remains visible. */ }
    heading.append(link); card.append(heading);
    if (article.summary || article.snippet) card.append(text("p", article.summary || article.snippet));
    const tags = text("div", "", "tags");
    (article.targetKeys || []).forEach(key => tags.append(text("span", displayName(key), "tag")));
    tags.append(text("span", article.bodyStatus === "body_extracted" ? "Texto disponível" : labels[article.bodyStatus] || "Texto pendente", "tag")); card.append(tags);
    const open = text("button", "Ler e classificar"); open.addEventListener("click", () => openArticle(article)); card.append(open);
    return card;
  }
  function renderResults() {
    $("results").replaceChildren();
    if (!state.items.length) $("results").append(text("p", "Nenhuma notícia encontrada com estes filtros.", "empty"));
    for (const item of state.items) {
      if (Array.isArray(item.articles)) {
        const group = text("section", "", "story-group"); group.append(text("h3", item.title || "História"));
        item.articles.forEach(a => group.append(articleCard(a)));
        if (Number(item.articleCount || 0) > item.articles.length) {
          const more = text("button", `Ver as ${item.articleCount} notícias desta história`);
          more.addEventListener("click", () => {state.storyId = item.id; $("view").value = "articles"; loadResults(true);}); group.append(more);
        }
        $("results").append(group);
      } else $("results").append(articleCard(item));
    }
    $("previous").disabled = !state.previous.length; $("next").disabled = !state.next;
    $("page-state").textContent = `Página ${state.previous.length + 1} · ${state.items.length} ${$("view").value === "stories" ? "histórias" : "notícias"}`;
  }
  async function loadResults(reset = false) {
    if (reset) {state.cursor = ""; state.previous = [];}
    const sequence = ++state.sequence;
    if (!state.configured) return;
    if (!state.selected.size) {state.items = []; state.next = ""; renderResults(); message("Selecione nomes para consultar."); return;}
    try {
      const data = await api(`/api/political/${$("view").value}?${filters()}`);
      if (sequence !== state.sequence) return;
      state.items = data.items || []; state.next = data.nextCursor || ""; renderResults();
      message("Resultados atualizados. Cada notícia pode aparecer associada a vários nomes.");
    } catch (error) {if (sequence === state.sequence) message(error.message, true);}
  }
  function renderMetrics(metrics = {}) {
    metrics = {...metrics, unresolvedGaps: gapCount(metrics)};
    const fields = [["uniqueCandidates", "URLs encontradas"], ["articlesInserted", "Notícias novas"], ["duplicates", "URLs repetidas"], ["mentionsInserted", "Associações a nomes"], ["bodyExtracted", "Textos disponíveis"], ["fetchPending", "Textos pendentes"], ["unknownDates", "Datas a revisar"], ["unresolvedGaps", "Consultas com pendências"]];
    $("metrics").replaceChildren();
    for (const [key, label] of fields) {const pair = document.createElement("div"); pair.append(text("dt", label), text("dd", Number(metrics[key] || 0).toLocaleString("pt-BR"))); $("metrics").append(pair);}
  }
  async function refreshStatus() {
    if (!state.configured) return;
    try {
      const data = await api("/api/political/status"); state.job = data.current || null;
      const job = state.job;
      $("job-state").textContent = job ? `${labels[job.status] || job.status} · ${formatDate(job.dateFrom)} a ${formatDate(job.dateTo)}` : "Nenhuma coleta iniciada.";
      renderMetrics(job?.metrics || data.metrics || {});
      $("cancel").hidden = !state.canRun || !job || !activeStates.has(job.status);
      $("resume").hidden = !state.canRun || !job || !["failed", "interrupted", "cancelled", "completed_with_gaps"].includes(job.status);
      if (job?.status === "queued" && !(data.workers || []).some(w => w.healthy)) $("job-state").textContent += " · Aguardando o coletor ficar disponível.";
    } catch (error) {$("job-state").textContent = error.message;}
  }
  async function loadCoverage() {
    if (!state.configured) return;
    try {
      const data = await api(`/api/political/coverage${state.job?.id ? "?job_id=" + encodeURIComponent(state.job.id) : ""}`);
      const items = [...(data.items || data.sources || data.windows || []), ...(data.gaps || [])];
      const table = document.createElement("table"), head = document.createElement("tr");
      ["Fonte", "Período", "Situação", "Pendência"].forEach(v => head.append(text("th", v))); table.append(head);
      for (const row of items) {const tr = document.createElement("tr"); [row.sourceName || sourceName(row.source_key || row.sourceKey) || row.name, row.date_from || row.dateFrom ? `${formatDate(row.dateFrom || row.date_from)} – ${formatDate(row.dateTo || row.date_to)}` : "Período da coleta", `${labels[row.status] || (row.status === "gap" ? "Consulta incompleta" : row.status === "split" ? "Consulta dividida em períodos menores" : row.status) || "Pendente"}${row.count ? " · " + row.count + " consultas" : ""}`, gapReason(row.error_type || row.errorType)].forEach(v => tr.append(text("td", v))); table.append(tr);}
      const totalGaps = gapCount(data.metrics || {});
      if (totalGaps > (data.gaps || []).length) table.append(text("caption", `Detalhes de ${(data.gaps || []).length} das ${totalGaps} consultas com pendências. Os totais por fonte incluem todas as consultas.`));
      $("coverage-list").replaceChildren(items.length ? table : text("p", "Nenhuma consulta a fontes registrada."));
    } catch (error) {$("coverage-list").replaceChildren(text("p", error.message));}
  }
  async function startJob(kind) {
    if (!state.selected.size) {message("Selecione pelo menos um nome.", true); return;}
    if (!$("date-from").value || !$("date-to").value) {message("Informe as duas datas para iniciar a coleta ou revisão.", true); return;}
    $("start").disabled = $("review").disabled = true;
    try {
      await api("/api/political/jobs", {method: "POST", body: JSON.stringify({kind, target_keys: [...state.selected], date_from: $("date-from").value, date_to: $("date-to").value})});
      message(kind === "review" ? "Revisão solicitada. Os registros e classificações existentes serão preservados." : "Coleta solicitada. Você pode fechar esta página e acompanhar o resultado depois."); await refreshStatus();
    } catch (error) {message(error.message, true);} finally {$("start").disabled = $("review").disabled = !state.configured;}
  }
  function populateClassification() {
    const record = state.classifications.find(c => (c.target_key || c.targetKey) === $("classification-target").value) || {};
    $("article-sentiment").value = record.article_sentiment || ""; $("target-sentiment").value = record.target_sentiment || "";
    $("categories").value = (record.categories || []).join(", "); $("centimetragem").value = record.centimetragem ?? "";
  }
  function setArticleLink(id = null) {
    const url = new URL(location.href);
    if (id === null) url.searchParams.delete("article");
    else url.searchParams.set("article", String(id));
    history.replaceState(history.state, "", url.pathname + url.search + url.hash);
  }
  async function openLinkedArticle() {
    if (!pageParams.has("article")) return;
    const rawId = pageParams.get("article"), id = Number(rawId);
    if (pageParams.getAll("article").length !== 1 || !/^[1-9]\d*$/.test(rawId) || !Number.isSafeInteger(id)) {
      message("O link da notícia é inválido.", true); return;
    }
    try {
      const article = await api(`/api/political/articles/${id}`);
      if (article.id !== id) throw new Error("Não foi possível abrir esta notícia.");
      await openArticle(article);
    } catch (error) {message(error.message, true);}
  }
  async function openArticle(article) {
    state.article = article; state.classifications = []; $("article-title").textContent = article.title || "Notícia";
    $("article-text").textContent = "Carregando texto…"; $("article-message").textContent = ""; $("classification-message").textContent = "";
    try {
      const url = new URL(article.url);
      if (["https:", "http:"].includes(url.protocol)) {
        const source = text("a", "Abrir publicação original"); source.href = url.href; source.target = "_blank"; source.rel = "noopener noreferrer";
        $("article-message").append(source);
      }
    } catch (_) { /* A missing publisher URL does not prevent reading saved text. */ }
    $("classification-target").replaceChildren(...(article.targetKeys || []).map(key => {const o = text("option", displayName(key)); o.value = key; return o;}));
    $("classification").hidden = Boolean(simulation); populateClassification(); $("article-dialog").showModal();
    const id = article.id || article.articleId;
    if (Number.isSafeInteger(id) && id > 0) setArticleLink(id);
    const results = await Promise.allSettled([api(`/api/political/articles/${id}/text`), api(`/api/political/articles/${id}/classifications`)]);
    if (state.article !== article) return;
    const body = results[0]; $("article-text").textContent = body.status === "fulfilled" ? body.value.text || "Texto indisponível. Consulte a publicação original pelo link da notícia." : body.reason.message;
    if (results[1].status === "fulfilled") {state.classifications = classificationRows(results[1].value); populateClassification();}
    else $("classification-message").textContent = results[1].reason.message;
  }
  $("classification-form").addEventListener("submit", async event => {
    event.preventDefault(); if (!state.article) return;
    try {const saved = await api(`/api/political/articles/${state.article.id || state.article.articleId}/classifications`, {method: "POST", body: JSON.stringify({target_key: $("classification-target").value, article_sentiment: $("article-sentiment").value || null, target_sentiment: $("target-sentiment").value || null, categories: $("categories").value.split(",").map(v => v.trim()).filter(Boolean), centimetragem: $("centimetragem").value ? Number($("centimetragem").value) : null})}); state.classifications = classificationRows(saved); $("classification-message").textContent = "Classificação salva.";} catch (error) {$("classification-message").textContent = error.message;}
  });
  $("classification-target").addEventListener("change", populateClassification);
  $("close-article").addEventListener("click", () => $("article-dialog").close());
  $("article-dialog").addEventListener("close", () => {state.article = null; state.classifications = []; setArticleLink();});
  $("filters").addEventListener("submit", event => {event.preventDefault(); state.storyId = ""; loadResults(true);});
  $("select-requested").addEventListener("click", () => {state.selected = new Set(state.defaultTargets); renderGroups();});
  $("select-all").addEventListener("click", () => {state.selected = new Set(state.targets.map(t => t.key)); renderGroups();});
  $("select-none").addEventListener("click", () => {state.selected.clear(); renderGroups();});
  $("all-dates").addEventListener("click", () => {$("date-from").value = ""; $("date-to").value = ""; loadResults(true);});
  $("next").addEventListener("click", () => {state.previous.push(state.cursor); state.cursor = state.next; loadResults();});
  $("previous").addEventListener("click", () => {state.cursor = state.previous.pop() || ""; loadResults();});
  $("start").addEventListener("click", () => startJob("collect")); $("review").addEventListener("click", () => startJob("review"));
  for (const action of ["resume", "cancel"]) $(action).addEventListener("click", async () => {if (!state.job) return; try {await api(`/api/political/jobs/${state.job.id}/${action}`, {method: "POST", body: "{}"}); await refreshStatus();} catch (error) {message(error.message, true);}});
  $("refresh").addEventListener("click", async () => {await refreshStatus(); await loadResults(); if ($("coverage").open) await loadCoverage();});
  $("coverage").addEventListener("toggle", () => {if ($("coverage").open) loadCoverage();});
  $("logout").addEventListener("click", async () => {try {await api("/api/logout", {method: "POST", body: "{}"}); location.assign("/");} catch (error) {message(error.message, true);}});
  $("manual-form").addEventListener("submit", async event => {
    event.preventDefault();
    if (!state.selected.size) {$("manual-message").textContent = "Selecione os nomes associados à notícia."; return;}
    try {
      await api("/api/political/manual-story", {method: "POST", body: JSON.stringify({target_keys: [...state.selected], title: $("manual-title").value, url: $("manual-url").value, published_at: $("manual-date").value || null, source_name: $("manual-source").value, full_text: $("manual-text").value})});
      $("manual-message").textContent = "Notícia salva."; $("manual-form").reset(); await loadResults(true);
    } catch (error) {$("manual-message").textContent = error.message;}
  });
  async function poll() {if (!document.hidden && activeStates.has(state.job?.status)) {await refreshStatus(); await loadResults(); if ($("coverage").open) await loadCoverage();} window.setTimeout(poll, 10000);}
  async function init() {
    try {
      const [meta, token, sourceData] = await Promise.all([api("/api/political/meta"), api("/api/csrf"), api("/api/political/sources")]);
      state.csrf = token.csrf; state.targets = meta.targets || []; state.sources = sourceData.sources || []; state.configured = Boolean(meta.configured); state.canRun = Boolean(meta.canRun) && !simulation;
      state.defaultTargets = (meta.defaultTargets || []).filter(key => state.targets.some(t => t.key === key));
      if (!state.defaultTargets.length) state.defaultTargets = state.targets.map(t => t.key);
      state.selected = new Set(state.defaultTargets);
      if (!state.selected.size) state.selected = new Set(state.targets.map(t => t.key));
      const parts = new Intl.DateTimeFormat("en-CA", {timeZone: "America/Sao_Paulo", year: "numeric", month: "2-digit", day: "2-digit"}).formatToParts(new Date());
      const part = name => parts.find(p => p.type === name).value; $("date-to").value = `${part("year")}-${part("month")}-${part("day")}`;
      for (const source of sourceData.sources || []) {const option = text("option", source.name || source.key); option.value = source.key; $("source").append(option);}
      renderGroups(); $("run-controls").hidden = !state.canRun; $("start").disabled = $("review").disabled = !state.configured;
      $("select-all").textContent = `Todos os ${state.targets.length} nomes da lista`;
      $("account-label").textContent = meta.clientLabel || meta.clientProfile || "";
      $("psd-client-link").hidden = !meta.psdClientAvailable || Boolean(clientProfile);
      const management = new URL("/?view=legacy", location.origin);
      if (clientProfile || simulation) management.searchParams.set("as_profile", clientProfile || simulation);
      $("manage-account").href = management.pathname + management.search;
      if (!state.configured) {message("Os nomes estão organizados. A nova coleta estará disponível quando o serviço de armazenamento for conectado."); renderResults(); return;}
      await refreshStatus(); await loadResults(); await openLinkedArticle(); poll();
    } catch (error) {message(error.message, true);}
  }
  init();
})();
