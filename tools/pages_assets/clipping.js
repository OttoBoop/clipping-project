(function () {
  console.log("[clipping] build: live-runner-repair-20260501 · editor enabled for all coworkers");
  const app = document.getElementById("app");
  if (!app) return;

  const dataUrl = app.dataset.clippingDataUrl;
  const rawUrl = app.dataset.clippingRawUrl;
  // API base URL. Empty string = same-origin (the FastAPI web_app serves both
  // the dashboard at "/" and the classification endpoints under "/api/").
  const apiUrl = (app.dataset.clippingApiUrl || "").trim().replace(/\/$/, "");
  let editorEnabled = true;
  let csrfToken = "";
  let categoriesCache = [];

  function apiFetch(path, init) {
    return fetch(apiUrl + path, Object.assign({ credentials: "same-origin" }, init || {}));
  }

  function apiPost(path, body) {
    var headers = { "Content-Type": "application/json" };
    if (csrfToken) headers["X-CSRF-Token"] = csrfToken;
    return apiFetch(path, { method: "POST", headers: headers, body: JSON.stringify(body) });
  }
  const storyStack = document.getElementById("storyStack");
  const flatStack = document.getElementById("flatStack");
  const targetFilters = document.getElementById("targetFilters");
  const indexPanel = document.getElementById("indexPanel");
  const storyIndex = document.getElementById("storyIndex");
  const emptyState = document.getElementById("emptyState");
  const activeFilterText = document.getElementById("activeFilterText");
  const visibleStoriesStat = document.getElementById("visibleStoriesStat");
  const visibleArticlesStat = document.getElementById("visibleArticlesStat");
  const visibleAiStat = document.getElementById("visibleAiStat");
  const visibleRawStat = document.getElementById("visibleRawStat");
  const visibleIndexCount = document.getElementById("visibleIndexCount");
  const loadingState = document.getElementById("loadingState");
  const sortButtons = Array.from(document.querySelectorAll("[data-sort]"));
  const runTabs = Array.from(document.querySelectorAll("[data-run-tab]"));
  const runPanels = Array.from(document.querySelectorAll("[data-tab-panel]"));
  const updateRunForm = document.getElementById("updateRunForm");
  const addTargetForm = document.getElementById("addTargetForm");
  const primaryRunTargets = document.getElementById("primaryRunTargets");
  const secondaryRunTargets = document.getElementById("secondaryRunTargets");
  const dateFromInput = document.getElementById("dateFromInput");
  const dateToInput = document.getElementById("dateToInput");
  const runUpdateButton = document.getElementById("runUpdateButton");
  const cancelUpdateButton = document.getElementById("cancelUpdateButton");
  const freshnessBanner = document.getElementById("freshnessBanner");
  const freshnessBannerReload = document.getElementById("freshnessBannerReload");
  const runFormMessage = document.getElementById("runFormMessage");
  const addTargetMessage = document.getElementById("addTargetMessage");
  const runnerStatusPill = document.getElementById("runnerStatusPill");
  const sharedStatusPill = document.getElementById("sharedStatusPill");
  const progressFill = document.getElementById("updateProgressFill");
  const progressTarget = document.getElementById("progressTarget");
  const progressDates = document.getElementById("progressDates");
  const progressSource = document.getElementById("progressSource");
  const progressArticles = document.getElementById("progressArticles");
  const progressMentions = document.getElementById("progressMentions");
  const progressStories = document.getElementById("progressStories");
  const progressWarnings = document.getElementById("progressWarnings");
  const baseStoriesStat = document.getElementById("baseStoriesStat");
  const baseArticlesStat = document.getElementById("baseArticlesStat");
  const baseRawStat = document.getElementById("baseRawStat");
  const baseUpdatedText = document.getElementById("baseUpdatedText");
  const LAZY_BATCH = 50;

  let payload = null;
  let selectedTargets = new Set();
  let currentSort = "newest";
  let flatSorted = [];
  let flatRendered = 0;
  let loadMoreBtn = null;
  let rawTextsCache = null;
  let rawTextsPromise = null;
  let runTargets = [];
  let latestStatus = null;
  const labelsByKey = {};

  function escapeHtml(value) {
    return String(value == null ? "" : value)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  function renderText(value) {
    return escapeHtml(value).replace(/\n/g, "<br>");
  }

  function friendlySummaryLabel(value) {
    var raw = String(value || "");
    var normalized = raw.toLowerCase();
    if (normalized.indexOf("texto " + "bruto") !== -1) return "Texto completo";
    if (normalized.indexOf("trecho " + "bruto") !== -1) return "Trecho da materia";
    if (normalized === "resumo ia") return "Resumo";
    return raw || "Sem resumo";
  }

  function splitList(value) {
    return String(value || "")
      .split(/[\n,]+/)
      .map(function (item) { return item.trim(); })
      .filter(Boolean);
  }

  function parseMaybeJsonList(value) {
    if (Array.isArray(value)) return value;
    if (!value) return [];
    try {
      var parsed = JSON.parse(value);
      return Array.isArray(parsed) ? parsed : [];
    } catch (e) {
      return [];
    }
  }

  function todayDateString(offsetDays) {
    var date = new Date();
    date.setDate(date.getDate() + Number(offsetDays || 0));
    return date.toISOString().slice(0, 10);
  }

  function normalizeTargetsResponse(data) {
    var body = data || {};
    var nested = body.targets && !Array.isArray(body.targets) ? body.targets : body;
    var rows = Array.isArray(body.targets) ? body.targets : Array.isArray(nested.targets) ? nested.targets : [];
    var primaryKeys = Array.isArray(nested.primaryKeys) ? nested.primaryKeys : [];
    var hasPrimaryKeys = Array.isArray(nested.primaryKeys);
    return rows
      .filter(function (target) { return target && target.key; })
      .map(function (target) {
        var key = String(target.key);
        return {
          key: key,
          label: String(target.label || target.display_name || target.key),
          primary: hasPrimaryKeys ? primaryKeys.indexOf(key) !== -1 : Boolean(target.primary),
        };
      });
  }

  function applyRuntimeTargetsToPayload(targets) {
    if (!payload || !Array.isArray(payload.targets) || !Array.isArray(targets)) return;
    var byKey = {};
    targets.forEach(function (target) {
      byKey[target.key] = target;
    });
    payload.targets.forEach(function (target) {
      var runtime = byKey[String(target.key || "")];
      if (!runtime) return;
      target.label = runtime.label || target.label;
      target.primary = Boolean(runtime.primary);
    });
  }

  function setMessage(el, text, kind) {
    if (!el) return;
    el.textContent = text || "";
    el.classList.remove("is-error", "is-ok");
    if (kind) el.classList.add(kind === "error" ? "is-error" : "is-ok");
  }

  function friendlyError(error, fallback) {
    var raw = error && error.message ? error.message : String(error || "");
    console.error("[clipping] detailed error", error);
    if (raw.indexOf("job_already_running") !== -1) return "Ja existe uma atualizacao em andamento.";
    if (raw.indexOf("persistent_storage_not_configured") !== -1) return "A gravacao da base ainda nao esta pronta neste ambiente.";
    if (raw.indexOf("periodo_invalido") !== -1) return "Confira as datas: a inicial precisa vir antes da final.";
    if (raw.indexOf("data_futura") !== -1) return "As datas precisam ser de hoje ou anteriores.";
    if (raw.indexOf("data_invalida") !== -1) return "Preencha as duas datas.";
    if (raw.indexOf("unknown_target_keys") !== -1) return "Um dos nomes selecionados ainda nao esta disponivel. Atualize a pagina e tente de novo.";
    return fallback || "Nao foi possivel concluir agora. Tente novamente em instantes.";
  }

  function showFriendlyProblem(message) {
    setMessage(runFormMessage, message, "error");
    if (window.alert) window.alert(message);
  }

  function badgeHtml(keys) {
    return (keys || [])
      .map(function (key) {
        const label = labelsByKey[key] || key;
        return '<span class="chip">' + escapeHtml(label) + "</span>";
      })
      .join("");
  }

  function storyVisible(story) {
    const keys = story.targetKeys || [];
    if (!keys.length) return true;
    return keys.some(function (key) {
      return selectedTargets.has(key);
    });
  }

  function activeLabel() {
    const allKeys = (payload.targets || []).map(function (target) {
      return target.key;
    });
    if (!allKeys.length || selectedTargets.size === allKeys.length) {
      return "Todos os nomes monitorados";
    }
    return allKeys
      .filter(function (key) {
        return selectedTargets.has(key);
      })
      .map(function (key) {
        return labelsByKey[key] || key;
      })
      .join(" + ");
  }

  function sortStories(stories) {
    return stories.slice().sort(function (a, b) {
      const tempDiff = Number(b.temperature || 0) - Number(a.temperature || 0);
      if (tempDiff !== 0) return tempDiff;
      return String(b.lastPublishedAt || "").localeCompare(String(a.lastPublishedAt || ""));
    });
  }

  function visibleStories() {
    return sortStories((payload.stories || []).filter(storyVisible));
  }

  function visibleArticles(stories) {
    const articles = [];
    stories.forEach(function (story) {
      (story.articles || []).forEach(function (article) {
        articles.push({
          storyId: story.storyIdInt,
          storyTitle: story.title,
          storyTargets: story.targetKeys || [],
          articleId: article.articleId,
          title: article.title,
          url: article.url,
          sourceName: article.sourceName,
          sourceHost: article.sourceHost,
          publishedAt: article.publishedAt,
          publishedDisplay: article.publishedDisplay,
          targetKeys: article.targetKeys && article.targetKeys.length ? article.targetKeys : story.targetKeys || [],
          summaryLabel: article.summaryLabel,
          summaryPreview: article.summaryPreview,
          rawTextKey: article.rawTextKey,
          summarySource: article.summarySource || "raw",
          classifications: article.classifications || [],
        });
      });
    });
    articles.sort(function (a, b) {
      const cmp = String(b.publishedAt || "").localeCompare(String(a.publishedAt || ""));
      if (cmp !== 0) return cmp;
      return String(a.title || "").localeCompare(String(b.title || ""));
    });
    return articles;
  }

  function chipHtml(target) {
    var active = selectedTargets.has(target.key) ? " active" : "";
    var primary = target.primary ? " primary" : "";
    return (
      '<button type="button" class="filter-chip' +
      primary +
      active +
      '" data-filter-target="' +
      escapeHtml(target.key) +
      '">' +
      '<span class="filter-chip__label">' +
      escapeHtml(target.label) +
      "</span>" +
      '<span class="filter-chip__meta">' +
      escapeHtml(String(target.storyCount || 0)) +
      " historias</span>" +
      "</button>"
    );
  }

  function renderTargetButtons() {
    var primary = [];
    var other = [];
    (payload.targets || []).forEach(function (target) {
      if (target.primary) primary.push(target);
      else other.push(target);
    });
    targetFilters.innerHTML = primary.map(chipHtml).join("");
    var outrosEl = document.getElementById("outrosFilters");
    if (other.length > 0) {
      if (!outrosEl) {
        outrosEl = document.createElement("details");
        outrosEl.className = "outros-candidatos";
        outrosEl.id = "outrosFilters";
        targetFilters.parentNode.insertBefore(outrosEl, targetFilters.nextSibling);
      }
      outrosEl.innerHTML =
        "<summary>Outros candidatos (" + other.length + ")</summary>" +
        '<div class="filter-row">' +
        other.map(chipHtml).join("") +
        "</div>";
    } else if (outrosEl) {
      outrosEl.remove();
    }
  }

  function renderStats(stories) {
    const storyCount = stories.length;
    const articleCount = stories.reduce(function (sum, story) {
      return sum + Number(story.articleCount || 0);
    }, 0);
    const aiCount = stories.reduce(function (sum, story) {
      return sum + Number(story.aiCount || 0);
    }, 0);
    const rawCount = stories.reduce(function (sum, story) {
      return sum + Number(story.rawCount || 0);
    }, 0);
    if (visibleStoriesStat) visibleStoriesStat.textContent = storyCount + " / " + payload.meta.totalStories;
    if (visibleArticlesStat) visibleArticlesStat.textContent = articleCount + " / " + payload.meta.totalArticles;
    if (visibleAiStat) visibleAiStat.textContent = aiCount + " / " + payload.meta.totalAi;
    if (visibleRawStat) visibleRawStat.textContent = rawCount + " / " + payload.meta.totalRaw;
    if (visibleIndexCount) visibleIndexCount.textContent = String(storyCount);
    if (activeFilterText) activeFilterText.textContent = activeLabel();
    if (emptyState) emptyState.hidden = storyCount > 0;
    if (baseStoriesStat) baseStoriesStat.textContent = String(payload.meta.totalStories || 0);
    if (baseArticlesStat) baseArticlesStat.textContent = String(payload.meta.totalArticles || 0);
    if (baseRawStat) baseRawStat.textContent = String(payload.meta.totalRaw || 0);
    if (baseUpdatedText) {
      baseUpdatedText.textContent = "Ultima atualizacao publicada: " + (payload.meta.generatedAt || "data nao informada");
    }
  }

  function activateRunTab(tabName) {
    runTabs.forEach(function (button) {
      var active = button.dataset.runTab === tabName;
      button.classList.toggle("active", active);
      button.setAttribute("aria-selected", active ? "true" : "false");
    });
    runPanels.forEach(function (panel) {
      panel.hidden = panel.dataset.tabPanel !== tabName;
    });
  }

  function renderRunTarget(target) {
    var id = "run-target-" + target.key;
    var checked = target.primary ? " checked" : "";
    var cls = target.primary ? " run-target--primary" : "";
    var helper = target.primary ? "Principal" : "Opcional";
    return (
      '<label class="run-target' + cls + '" for="' + escapeHtml(id) + '">' +
      '<input type="checkbox" id="' + escapeHtml(id) + '" value="' + escapeHtml(target.key) + '"' + checked + ">" +
      '<span>' + escapeHtml(target.label) + '<small>' + helper + "</small></span>" +
      "</label>"
    );
  }

  function renderRunTargets() {
    if (!primaryRunTargets || !secondaryRunTargets) return;
    var primary = runTargets.filter(function (target) { return target.primary; });
    var secondary = runTargets.filter(function (target) { return !target.primary; });
    primaryRunTargets.innerHTML = primary.length ? primary.map(renderRunTarget).join("") : '<p class="filter-note">Carregando nomes principais...</p>';
    secondaryRunTargets.innerHTML = secondary.length ? secondary.map(renderRunTarget).join("") : '<p class="filter-note">Nenhum nome extra cadastrado ainda.</p>';
  }

  function fallbackTargetsFromPayload() {
    if (!payload || !payload.targets) return [];
    return (payload.targets || []).map(function (target) {
      return {
        key: String(target.key),
        label: String(target.label || target.key),
        primary: Boolean(target.primary),
      };
    });
  }

  function refreshTargets() {
    return apiFetch("/api/targets", { cache: "no-store" })
      .then(function (resp) {
        if (!resp.ok) throw new Error("HTTP " + resp.status);
        return resp.json();
      })
      .then(function (data) {
        runTargets = normalizeTargetsResponse(data);
        if (!runTargets.length) runTargets = fallbackTargetsFromPayload();
        applyRuntimeTargetsToPayload(runTargets);
        runTargets.forEach(function (target) {
          labelsByKey[target.key] = target.label || target.key;
        });
        renderRunTargets();
        if (payload) applyState();
      })
      .catch(function (error) {
        console.error("[clipping] target refresh failed", error);
        runTargets = fallbackTargetsFromPayload();
        renderRunTargets();
      });
  }

  function selectedRunTargetKeys() {
    var keys = [];
    [primaryRunTargets, secondaryRunTargets].forEach(function (container) {
      if (!container) return;
      container.querySelectorAll('input[type="checkbox"]:checked').forEach(function (input) {
        if (input.value && keys.indexOf(input.value) === -1) keys.push(input.value);
      });
    });
    return keys;
  }

  function applySuggestedDates(statusPayload) {
    if (!dateFromInput || !dateToInput) return;
    var current = statusPayload && statusPayload.current ? statusPayload.current : {};
    var recent = statusPayload && statusPayload.recent && statusPayload.recent.length ? statusPayload.recent[0] : {};
    var suggestedFrom = String(current.date_from || recent.date_from || "");
    var suggestedTo = String(current.date_to || recent.date_to || "");
    if (!suggestedFrom) suggestedFrom = todayDateString(-1);
    if (!suggestedTo) suggestedTo = todayDateString(0);
    if (!dateFromInput.value) dateFromInput.value = suggestedFrom.slice(0, 10);
    if (!dateToInput.value) dateToInput.value = suggestedTo.slice(0, 10);
    dateFromInput.max = todayDateString(0);
    dateToInput.max = todayDateString(0);
  }

  function statusLabel(status) {
    if (status === "running") return "Atualizando";
    if (status === "queued") return "Na fila";
    if (status === "exporting") return "Publicando";
    if (status === "succeeded") return "Concluido";
    if (status === "failed") return "Precisa de atencao";
    if (status === "cancelled") return "Cancelada";
    return "Pronto";
  }

  function placeholderText(status, kind) {
    if (status === "queued") {
      if (kind === "target") return "Na fila";
      if (kind === "source") return "Iniciando coleta...";
    }
    if (status === "running") {
      if (kind === "target") return "Buscando primeiro nome...";
      if (kind === "source") return "Buscando primeira fonte...";
    }
    if (status === "exporting") return "Publicando painel...";
    if (status === "succeeded") return "Rodada concluida";
    if (status === "failed") return "Rodada interrompida";
    if (status === "cancelled") return "Rodada cancelada";
    return "Sem rodada agora";
  }

  function latestProgressEvent(job) {
    var events = (job && job.events) || [];
    for (var i = 0; i < events.length; i++) {
      if (events[i] && events[i].payload) return events[i];
    }
    return null;
  }

  function progressPercent(job, event) {
    var status = job && job.status;
    if (status === "succeeded") return 100;
    if (status === "failed") return 100;
    if (status === "exporting") return 92;
    var payload = event && event.payload ? event.payload : {};
    var total = Number(payload.candidates_total || payload.max_candidates || 0);
    var seen = Number(payload.candidates_seen || 0);
    if (total > 0 && seen >= 0) return Math.max(8, Math.min(88, Math.round((seen / total) * 80)));
    if (status === "running") return 24;
    if (status === "queued") return 8;
    return 0;
  }

  function warningText(job) {
    if (!job) return "";
    if (job.status === "failed") return "A atualizacao parou antes de terminar. O detalhe tecnico ficou no console.";
    var events = job.events || [];
    for (var i = 0; i < events.length; i++) {
      var payload = events[i].payload || {};
      var errors = payload.errors || payload.warnings || [];
      if (Array.isArray(errors) && errors.length) {
        console.warn("[clipping] update warning", errors);
        return "Algumas fontes nao responderam, mas a atualizacao continua com as demais.";
      }
    }
    return "";
  }

  function renderStatus(statusPayload) {
    latestStatus = statusPayload || latestStatus || {};
    var current = latestStatus.current || {};
    var recent = latestStatus.recent || [];
    var job = current.status === "idle" && recent.length ? recent[0] : current;
    var event = latestProgressEvent(job);
    var eventPayload = event && event.payload ? event.payload : {};
    var status = job.status || "";
    var label = statusLabel(status);
    var isRunning = ["queued", "running", "exporting"].indexOf(status) !== -1;
    var isError = status === "failed";
    var isCancelled = status === "cancelled";
    [runnerStatusPill, sharedStatusPill].forEach(function (pill) {
      if (!pill) return;
      pill.textContent = label;
      pill.classList.toggle("is-running", isRunning);
      pill.classList.toggle("is-error", isError);
      pill.classList.toggle("is-cancelled", isCancelled);
    });
    if (progressFill) progressFill.style.width = progressPercent(job, event) + "%";
    var keys = parseMaybeJsonList(job.target_keys);
    if (!keys.length && Array.isArray(job.target_keys)) keys = job.target_keys;
    if (progressTarget) {
      var targetEvent = eventPayload && eventPayload.target_label ? eventPayload.target_label : "";
      var targetText = keys.map(function (key) { return labelsByKey[key] || key; }).join(" + ");
      progressTarget.textContent = targetEvent || targetText || placeholderText(status, "target");
    }
    if (progressDates) {
      var from = job.date_from || "";
      var to = job.date_to || "";
      progressDates.textContent = from && to ? from + " a " + to : placeholderText(status, "dates");
    }
    if (progressSource) progressSource.textContent = eventPayload.source_name || placeholderText(status, "source");
    if (progressArticles) progressArticles.textContent = String(job.articles_inserted || eventPayload.articles_inserted || 0);
    if (progressMentions) progressMentions.textContent = String(job.mentions_inserted || 0);
    if (progressStories) progressStories.textContent = String(job.stories_touched || 0);
    var warning = warningText(job);
    if (progressWarnings) {
      progressWarnings.hidden = !warning;
      progressWarnings.textContent = warning;
    }
    if (isError && job.error_message) console.error("[clipping] update failed", job.error_message);
    if (runUpdateButton) runUpdateButton.disabled = isRunning;
    if (cancelUpdateButton) {
      cancelUpdateButton.hidden = !isRunning;
      cancelUpdateButton.disabled = !isRunning;
    }
    updateFreshnessBanner(latestStatus);
  }

  function updateFreshnessBanner(statusPayload) {
    if (!freshnessBanner) return;
    if (!payload || !payload.meta) return;
    var generatedAt = String(payload.meta.generatedAt || "");
    var recent = (statusPayload && statusPayload.recent) || [];
    var latestSucceeded = null;
    for (var i = 0; i < recent.length; i++) {
      var row = recent[i] || {};
      if (row.status === "succeeded" && row.finished_at) {
        latestSucceeded = row;
        break;
      }
    }
    if (!latestSucceeded) {
      freshnessBanner.hidden = true;
      return;
    }
    var finished = String(latestSucceeded.finished_at || "");
    if (!generatedAt || finished > generatedAt) {
      freshnessBanner.hidden = false;
    } else {
      freshnessBanner.hidden = true;
    }
  }

  function pollStatus() {
    return apiFetch("/api/update/status", { cache: "no-store" })
      .then(function (resp) {
        if (!resp.ok) throw new Error("HTTP " + resp.status);
        return resp.json();
      })
      .then(function (data) {
        applySuggestedDates(data);
        renderStatus(data);
      })
      .catch(function (error) {
        console.error("[clipping] status polling failed", error);
        [runnerStatusPill, sharedStatusPill].forEach(function (pill) {
          if (!pill) return;
          pill.textContent = "Sem conexao";
          pill.classList.add("is-error");
        });
      });
  }

  function renderStoryIndex(stories) {
    storyIndex.innerHTML = stories
      .map(function (story) {
        return (
          '<a class="story-index-link" href="#story-' +
          story.storyIdInt +
          '" data-nav-story-id="' +
          story.storyIdInt +
          '">' +
          "<strong>" +
          escapeHtml(story.title || "Sem titulo") +
          "</strong>" +
          "<span>" +
          escapeHtml(String(story.articleCount || 0)) +
          " noticia(s)</span>" +
          "</a>"
        );
      })
      .join("");
  }

  var SENTIMENT_LABEL = { positive: "positivo", negative: "negativo", neutral: "neutro" };

  function classificationHtml(article) {
    var clsArr = article.classifications || [];
    if (!clsArr.length) return "";
    var parts = [];
    // Article sentiment once (all targets share the same value)
    var artSent = clsArr[0].article_sentiment;
    if (artSent) {
      parts.push(
        '<span class="chip chip--cls chip--cls-' + artSent + '" title="Sentimento da notícia">Notícia: ' +
        escapeHtml(SENTIMENT_LABEL[artSent] || artSent) + "</span>"
      );
    }
    // Categories deduplicated across all targets
    var seenCats = {};
    clsArr.forEach(function (cls) {
      (cls.categories || []).forEach(function (cat) {
        if (!seenCats[cat]) {
          seenCats[cat] = true;
          parts.push('<span class="chip chip--cls chip--cls-cat">' + escapeHtml(cat) + "</span>");
        }
      });
    });
    // Per-target sentiments
    clsArr.forEach(function (cls) {
      if (cls.target_sentiment) {
        var tLabel = escapeHtml(labelsByKey[cls.target_key] || cls.target_key || "");
        parts.push(
          '<span class="chip chip--cls chip--cls-' + cls.target_sentiment +
          '" title="Sentimento sobre ' + tLabel + '">' +
          tLabel + ": " + escapeHtml(SENTIMENT_LABEL[cls.target_sentiment] || cls.target_sentiment) +
          "</span>"
        );
      }
    });
    return parts.length ? '<div class="chips chips--cls">' + parts.join("") + "</div>" : "";
  }

  function findArticleById(aid) {
    if (!payload || !payload.stories) return null;
    for (var i = 0; i < payload.stories.length; i++) {
      var arr = payload.stories[i].articles || [];
      for (var j = 0; j < arr.length; j++) {
        if (Number(arr[j].articleId) === Number(aid)) return arr[j];
      }
    }
    return null;
  }

  function sentimentSelectHtml(field, current) {
    var opts = ["", "positive", "negative", "neutral"];
    var labels = { "": "—", positive: "Positivo", negative: "Negativo", neutral: "Neutro" };
    return (
      '<select data-cls-field="' + field + '">' +
      opts.map(function (v) {
        var sel = (current || "") === v ? " selected" : "";
        return '<option value="' + v + '"' + sel + ">" + labels[v] + "</option>";
      }).join("") +
      "</select>"
    );
  }

  function categoryChipHtml(name, selected) {
    return (
      '<button type="button" class="cls-cat-chip' +
      (selected ? " selected" : "") +
      '" data-cat-name="' +
      escapeHtml(name) +
      '">' +
      escapeHtml(name) +
      "</button>"
    );
  }

  function classificationEditorHtml(article) {
    if (!editorEnabled) return "";
    var aid = article.articleId;
    var targetKeys = article.targetKeys || [];
    if (!targetKeys.length) return "";
    var clsByTarget = {};
    (article.classifications || []).forEach(function (c) {
      clsByTarget[c.target_key] = c;
    });

    // Article-level: pick article_sentiment + categories from first saved classification
    var firstCls = (article.classifications || [])[0] || {};
    var artSentCurrent = firstCls.article_sentiment || "";
    var savedCats = [];
    (article.classifications || []).forEach(function (c) {
      (c.categories || []).forEach(function (cat) {
        if (savedCats.indexOf(cat) === -1) savedCats.push(cat);
      });
    });
    var allCatOptions = categoriesCache.slice();
    savedCats.forEach(function (c) {
      if (allCatOptions.indexOf(c) === -1) allCatOptions.push(c);
    });
    var catOptionsHtml = allCatOptions.map(function (name) {
      var sel = savedCats.indexOf(name) !== -1 ? " selected" : "";
      return '<option value="' + escapeHtml(name) + '"' + sel + ">" + escapeHtml(name) + "</option>";
    }).join("");

    var articleSection =
      '<div class="cls-article-section" data-article-id="' + escapeHtml(String(aid)) + '">' +
      '<div class="cls-row">' +
      '<label class="cls-field">Sentimento da notícia ' +
      sentimentSelectHtml("article_sentiment", artSentCurrent) +
      "</label>" +
      '<div class="cls-field">' +
      '<span class="cls-field-label">Categorias</span>' +
      '<select multiple class="cls-cat-select" size="4">' + catOptionsHtml + "</select>" +
      '<div class="cls-add-cat-row">' +
      '<input type="text" class="cls-new-cat-input" placeholder="Nova categoria…">' +
      '<button type="button" class="cls-add-cat-btn">Adicionar</button>' +
      "</div>" +
      "</div>" +
      "</div>" +
      "</div>";

    var fieldsets = targetKeys.map(function (tk) {
      var tLabel = labelsByKey[tk] || tk;
      var cur = clsByTarget[tk] || {};
      return (
        '<fieldset class="cls-fieldset" data-target-key="' + escapeHtml(tk) +
        '" data-target-name="' + escapeHtml(tLabel) + '">' +
        "<legend>" + escapeHtml(tLabel) + "</legend>" +
        '<div class="cls-row">' +
        '<label class="cls-field">Sentimento sobre ' + escapeHtml(tLabel) + " " +
        sentimentSelectHtml("target_sentiment", cur.target_sentiment) +
        "</label>" +
        "</div>" +
        "</fieldset>"
      );
    }).join("");

    return (
      '<details class="cls-editor"><summary>Classificar este artigo</summary>' +
      articleSection +
      fieldsets +
      '<div class="cls-row cls-actions-row">' +
      '<button type="button" class="cls-save-btn">Salvar</button>' +
      '<span class="cls-save-status"></span>' +
      "</div>" +
      "</details>"
    );
  }

  function articleSummaryClass(article) {
    return article.summarySource === "ai" || article.summaryLabel === "Resumo IA" ? "summary-ai" : "summary-raw";
  }

  function renderArticleCard(article) {
    const rawToggle = article.rawTextKey
      ? '<details class="raw-details" data-article-id="' +
        escapeHtml(String(article.articleId || "")) +
        '" data-raw-key="' +
        escapeHtml(article.rawTextKey) +
        '">' +
        "<summary>Ver texto completo</summary>" +
        '<div class="body-text full"></div>' +
        "</details>"
      : "";
    const linkHtml = article.url
      ? '<a class="text-link" href="' +
        escapeHtml(article.url) +
        '" target="_blank" rel="noreferrer">Abrir materia original</a>'
      : "";
    const titleHtml = article.url
      ? '<a href="' +
        escapeHtml(article.url) +
        '" target="_blank" rel="noreferrer">' +
        escapeHtml(article.title || "Sem titulo") +
        "</a>"
      : escapeHtml(article.title || "Sem titulo");

    return (
      '<article class="article-card" id="article-' +
      escapeHtml(String(article.articleId || "")) +
      '">' +
      '<div class="article-top">' +
      "<div>" +
      "<h3>" +
      titleHtml +
      "</h3>" +
      '<p class="article-meta">' +
      "<span>" +
      escapeHtml(article.sourceName || "Fonte nao identificada") +
      "</span>" +
      "<span>" +
      escapeHtml(article.publishedDisplay || "") +
      "</span>" +
      "<span>" +
      escapeHtml(article.sourceHost || "link externo") +
      "</span>" +
      "</p>" +
      "</div>" +
      '<div class="chips">' +
      badgeHtml(article.targetKeys || []) +
      "</div>" +
      '<div class="cls-display" data-article-cls="' +
      escapeHtml(String(article.articleId || "")) +
      '">' +
      classificationHtml(article) +
      "</div>" +
      "</div>" +
      classificationEditorHtml(article) +
      '<div class="article-links">' +
      linkHtml +
      "</div>" +
      '<div class="summary-box ' +
      articleSummaryClass(article) +
      '">' +
      '<div class="summary-label">' +
      escapeHtml(friendlySummaryLabel(article.summaryLabel)) +
      "</div>" +
      '<div class="body-text">' +
      renderText(article.summaryPreview || "") +
      "</div>" +
      rawToggle +
      "</div>" +
      "</article>"
    );
  }

  function formatDate(value) {
    if (!value) return "";
    if (value.indexOf("/") !== -1) return value;
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return value;
    const pad = function (num) {
      return String(num).padStart(2, "0");
    };
    return (
      pad(date.getUTCDate()) +
      "/" +
      pad(date.getUTCMonth() + 1) +
      "/" +
      date.getUTCFullYear() +
      " " +
      pad(date.getUTCHours()) +
      ":" +
      pad(date.getUTCMinutes()) +
      " UTC"
    );
  }

  function renderStoryCard(story) {
    return (
      '<details class="panel story-card" id="story-' +
      story.storyIdInt +
      '" data-story-id="' +
      story.storyIdInt +
      '">' +
      '<summary class="story-summary-row">' +
      '<div class="story-heading">' +
      '<span class="story-toggle" aria-hidden="true"></span>' +
      "<div>" +
      '<p class="eyebrow">Historia principal ' +
      story.storyIdInt +
      "</p>" +
      "<h2>" +
      escapeHtml(story.title || "Sem titulo") +
      "</h2>" +
      '<div class="chips">' +
      badgeHtml(story.targetKeys || []) +
      "</div>" +
      "</div>" +
      "</div>" +
      '<div class="story-stats">' +
      "<div><strong>" +
      escapeHtml(String(story.articleCount || 0)) +
      "</strong><span>noticias</span></div>" +
      "<div><strong>" +
      escapeHtml(String(Math.round(Number(story.temperature || 0)))) +
      "</strong><span>temperatura</span></div>" +
      "</div>" +
      "</summary>" +
      '<div class="story-meta">' +
      "<span>Primeira publicacao: " +
      escapeHtml(story.firstPublishedAt ? formatDate(story.firstPublishedAt) : "") +
      "</span>" +
      "<span>Ultima publicacao: " +
      escapeHtml(story.lastPublishedAt ? formatDate(story.lastPublishedAt) : "") +
      "</span>" +
      "</div>" +
      '<div class="story-blurb">' +
      '<div class="summary-label">' +
      escapeHtml(story.summaryLabel || "Resumo do agrupamento") +
      "</div>" +
      "<p>" +
      renderText(story.summaryText || "") +
      "</p>" +
      "</div>" +
      '<div class="story-articles">' +
      (story.articles || []).map(renderArticleCard).join("") +
      "</div>" +
      "</details>"
    );
  }

  function buildFlatView(stories) {
    storyStack.hidden = true;
    storyStack.innerHTML = "";
    flatStack.hidden = false;
    indexPanel.hidden = true;
    flatStack.innerHTML = "";
    flatRendered = 0;
    loadMoreBtn = null;
    flatSorted = visibleArticles(stories);

    if (!flatSorted.length) {
      flatStack.innerHTML = '<div class="panel empty-state">Nenhuma noticia corresponde aos filtros atuais.</div>';
      return;
    }

    const loading = document.createElement("div");
    loading.className = "flat-loading";
    loading.innerHTML = '<div class="flat-spinner"></div> Carregando noticias...';
    flatStack.appendChild(loading);
    window.requestAnimationFrame(function () {
      if (loading.parentNode) {
        loading.parentNode.removeChild(loading);
      }
      renderFlatBatch();
    });
  }

  function updateLoadMoreBtn() {
    const remaining = flatSorted.length - flatRendered;
    if (remaining <= 0) {
      if (loadMoreBtn && loadMoreBtn.parentNode) {
        loadMoreBtn.parentNode.removeChild(loadMoreBtn);
      }
      loadMoreBtn = null;
      return;
    }
    if (!loadMoreBtn) {
      loadMoreBtn = document.createElement("button");
      loadMoreBtn.type = "button";
      loadMoreBtn.className = "load-more-btn";
      loadMoreBtn.addEventListener("click", onLoadMore);
      flatStack.appendChild(loadMoreBtn);
    }
    loadMoreBtn.disabled = false;
    loadMoreBtn.textContent = "Carregar mais noticias (" + remaining + " restantes)";
  }

  function renderFlatBatch() {
    if (flatRendered >= flatSorted.length) return;
    const end = Math.min(flatRendered + LAZY_BATCH, flatSorted.length);
    const wrapper = document.createElement("div");
    wrapper.innerHTML = flatSorted.slice(flatRendered, end).map(renderArticleCard).join("");
    while (wrapper.firstChild) {
      if (loadMoreBtn) {
        flatStack.insertBefore(wrapper.firstChild, loadMoreBtn);
      } else {
        flatStack.appendChild(wrapper.firstChild);
      }
    }
    flatRendered = end;
    updateLoadMoreBtn();
  }

  function onLoadMore() {
    if (!loadMoreBtn) return;
    loadMoreBtn.disabled = true;
    loadMoreBtn.innerHTML = '<div class="flat-spinner"></div> Carregando...';
    window.requestAnimationFrame(renderFlatBatch);
  }

  let groupedSorted = [];
  let groupedRendered = 0;
  let groupedLoadMoreBtn = null;

  function renderGroupedBatch() {
    if (groupedRendered >= groupedSorted.length) return;
    var end = Math.min(groupedRendered + LAZY_BATCH, groupedSorted.length);
    var wrapper = document.createElement("div");
    wrapper.innerHTML = groupedSorted.slice(groupedRendered, end).map(renderStoryCard).join("");
    while (wrapper.firstChild) {
      if (groupedLoadMoreBtn) {
        storyStack.insertBefore(wrapper.firstChild, groupedLoadMoreBtn);
      } else {
        storyStack.appendChild(wrapper.firstChild);
      }
    }
    groupedRendered = end;
    updateGroupedLoadMoreBtn();
  }

  function updateGroupedLoadMoreBtn() {
    var remaining = groupedSorted.length - groupedRendered;
    if (remaining <= 0) {
      if (groupedLoadMoreBtn && groupedLoadMoreBtn.parentNode) {
        groupedLoadMoreBtn.parentNode.removeChild(groupedLoadMoreBtn);
      }
      groupedLoadMoreBtn = null;
      return;
    }
    if (!groupedLoadMoreBtn) {
      groupedLoadMoreBtn = document.createElement("button");
      groupedLoadMoreBtn.type = "button";
      groupedLoadMoreBtn.className = "load-more-btn";
      groupedLoadMoreBtn.addEventListener("click", function () {
        if (!groupedLoadMoreBtn) return;
        groupedLoadMoreBtn.disabled = true;
        groupedLoadMoreBtn.innerHTML = '<div class="flat-spinner"></div> Carregando...';
        window.requestAnimationFrame(renderGroupedBatch);
      });
      storyStack.appendChild(groupedLoadMoreBtn);
    }
    groupedLoadMoreBtn.disabled = false;
    groupedLoadMoreBtn.textContent = "Carregar mais historias (" + remaining + " restantes)";
  }

  function buildGroupedView(stories) {
    flatStack.hidden = true;
    flatStack.innerHTML = "";
    storyStack.hidden = false;
    indexPanel.hidden = false;
    storyStack.innerHTML = "";
    groupedRendered = 0;
    groupedLoadMoreBtn = null;
    groupedSorted = stories;
    renderGroupedBatch();
  }

  function renderCurrentView(stories) {
    if (currentSort === "newest") {
      buildFlatView(stories);
    } else {
      buildGroupedView(stories);
    }
    sortButtons.forEach(function (button) {
      button.classList.toggle("active", button.dataset.sort === currentSort);
    });
  }

  function applyState() {
    const stories = visibleStories();
    renderTargetButtons();
    renderStats(stories);
    renderStoryIndex(stories);
    renderCurrentView(stories);
  }

  function ensureRawTexts() {
    if (rawTextsCache) return Promise.resolve(rawTextsCache);
    if (rawTextsPromise) return rawTextsPromise;
    rawTextsPromise = fetch(rawUrl, { cache: "no-store" })
      .then(function (response) {
        if (!response.ok) throw new Error("Falha ao carregar texto completo");
        return response.json();
      })
      .then(function (json) {
        rawTextsCache = json || {};
        return rawTextsCache;
      });
    return rawTextsPromise;
  }

  function showError(message) {
    if (!loadingState) return;
    loadingState.classList.add("app-error");
    loadingState.hidden = false;
    loadingState.innerHTML =
      "<strong>Falha ao carregar o clipping.</strong><p>" + escapeHtml(message) + "</p>";
  }

  function hydrateRawDetails(el) {
    if (!el || !el.classList.contains("raw-details") || !el.open || el.dataset.loaded === "1") {
      return;
    }
    if (el.dataset.loading === "1") return;
    const rawKey = el.dataset.rawKey;
    if (!rawKey) return;

    const fullTextDiv = el.querySelector(".body-text.full");
    if (fullTextDiv && !fullTextDiv.textContent.trim()) {
      fullTextDiv.textContent = "Carregando texto completo...";
    }
    el.dataset.loading = "1";

    ensureRawTexts()
      .then(function (rawTexts) {
        if (fullTextDiv) {
          fullTextDiv.innerHTML = renderText(rawTexts[rawKey] || "");
        }
        el.dataset.loaded = "1";
        delete el.dataset.loading;
      })
      .catch(function () {
        if (fullTextDiv) {
          fullTextDiv.textContent = "Nao foi possivel carregar o texto completo.";
        }
        delete el.dataset.loading;
      });
  }

  app.addEventListener("click", function (event) {
    const runTab = event.target.closest("[data-run-tab]");
    if (runTab) {
      activateRunTab(runTab.dataset.runTab || "run");
      return;
    }

    const sortButton = event.target.closest("[data-sort]");
    if (sortButton) {
      currentSort = sortButton.dataset.sort || "newest";
      applyState();
      return;
    }

    const filterButton = event.target.closest("[data-filter-target]");
    if (!filterButton || !payload) return;
    const key = filterButton.dataset.filterTarget;
    if (!key) return;
    if (selectedTargets.has(key)) {
      selectedTargets.delete(key);
    } else {
      selectedTargets.add(key);
    }
    if (!selectedTargets.size) {
      var primaryTargets = (payload.targets || []).filter(function (t) { return t.primary; });
      (primaryTargets.length ? primaryTargets : payload.targets || []).forEach(function (target) {
        selectedTargets.add(target.key);
      });
    }
    applyState();
  });

  if (updateRunForm) {
    updateRunForm.addEventListener("submit", async function (event) {
      event.preventDefault();
      setMessage(runFormMessage, "Iniciando atualizacao...", "");
      var keys = selectedRunTargetKeys();
      if (!keys.length) {
        showFriendlyProblem("Selecione pelo menos um nome para acompanhar.");
        return;
      }
      var body = {
        preset: "custom",
        target_keys: keys,
        date_from: dateFromInput ? dateFromInput.value : "",
        date_to: dateToInput ? dateToInput.value : "",
        export: true,
      };
      if (runUpdateButton) runUpdateButton.disabled = true;
      try {
        var resp = await apiPost("/api/update/start", body);
        var data = await resp.json().catch(function () { return {}; });
        if (!resp.ok) throw new Error(data.detail || data.error || "HTTP " + resp.status);
        setMessage(runFormMessage, "Atualizacao iniciada. O progresso aparece na aba compartilhada.", "ok");
        activateRunTab("progress");
        await pollStatus();
      } catch (error) {
        showFriendlyProblem(friendlyError(error, "Nao foi possivel iniciar a atualizacao."));
      } finally {
        if (runUpdateButton) {
          var status = latestStatus && latestStatus.current ? latestStatus.current.status : "";
          runUpdateButton.disabled = ["queued", "running", "exporting"].indexOf(status) !== -1;
        }
      }
    });
  }

  if (cancelUpdateButton) {
    cancelUpdateButton.addEventListener("click", async function () {
      cancelUpdateButton.disabled = true;
      setMessage(runFormMessage, "Cancelando atualizacao...", "");
      try {
        var resp = await apiPost("/api/update/cancel", {});
        var data = await resp.json().catch(function () { return {}; });
        if (!resp.ok) throw new Error(data.detail || data.error || "HTTP " + resp.status);
        setMessage(runFormMessage, "Atualizacao cancelada. Voce pode iniciar outra agora.", "ok");
        await pollStatus();
      } catch (error) {
        setMessage(runFormMessage, friendlyError(error, "Nao foi possivel cancelar agora."), "error");
      } finally {
        var status = latestStatus && latestStatus.current ? latestStatus.current.status : "";
        var stillRunning = ["queued", "running", "exporting"].indexOf(status) !== -1;
        cancelUpdateButton.disabled = !stillRunning;
        cancelUpdateButton.hidden = !stillRunning;
      }
    });
  }

  if (freshnessBannerReload) {
    freshnessBannerReload.addEventListener("click", function () {
      window.location.reload();
    });
  }

  if (addTargetForm) {
    addTargetForm.addEventListener("submit", async function (event) {
      event.preventDefault();
      setMessage(addTargetMessage, "Salvando...", "");
      var submit = addTargetForm.querySelector('button[type="submit"]');
      if (submit) submit.disabled = true;
      var form = new FormData(addTargetForm);
      var body = {
        display_name: form.get("display_name"),
        keywords: splitList(form.get("keywords")),
        exact_aliases: splitList(form.get("exact_aliases")),
      };
      try {
        var resp = await apiPost("/api/targets", body);
        var data = await resp.json().catch(function () { return {}; });
        if (!resp.ok) throw new Error(data.detail || data.error || "HTTP " + resp.status);
        setMessage(addTargetMessage, "Nome extra salvo e disponivel para a proxima rodada.", "ok");
        addTargetForm.reset();
        await refreshTargets();
      } catch (error) {
        setMessage(addTargetMessage, friendlyError(error, "Nao foi possivel salvar este nome."), "error");
      } finally {
        if (submit) submit.disabled = false;
      }
    });
  }

  app.addEventListener(
    "toggle",
    function (event) {
      hydrateRawDetails(event.target);
    },
    true
  );

  function refreshArticleClsDisplay(article) {
    var aid = article.articleId;
    var html = classificationHtml(article);
    document
      .querySelectorAll('[data-article-cls="' + String(aid) + '"]')
      .forEach(function (el) { el.innerHTML = html; });
  }

  function applySavedClassification(saved) {
    var article = findArticleById(saved.article_id);
    if (!article) return;
    article.classifications = article.classifications || [];
    var idx = -1;
    for (var i = 0; i < article.classifications.length; i++) {
      if (article.classifications[i].target_key === saved.target_key) { idx = i; break; }
    }
    var record = {
      target_key: saved.target_key,
      article_sentiment: saved.article_sentiment,
      target_sentiment: saved.target_sentiment,
      centimetragem: saved.centimetragem,
      categories: (saved.categories || []).slice(),
    };
    if (idx >= 0) article.classifications[idx] = record;
    else article.classifications.push(record);
    refreshArticleClsDisplay(article);
  }

  function gatherEditorData(editor) {
    var section = editor.querySelector(".cls-article-section");
    var aid = parseInt(section.dataset.articleId, 10);
    var artSent = section.querySelector('[data-cls-field="article_sentiment"]').value || null;
    var cats = Array.from(section.querySelectorAll(".cls-cat-select option:checked")).map(function (o) {
      return o.value;
    });
    var targets = [];
    editor.querySelectorAll(".cls-fieldset").forEach(function (fs) {
      targets.push({
        target_key: fs.dataset.targetKey,
        target_name: fs.dataset.targetName || fs.dataset.targetKey,
        target_sentiment: fs.querySelector('[data-cls-field="target_sentiment"]').value || null,
      });
    });
    return { article_id: aid, article_sentiment: artSent, categories: cats, targets: targets };
  }

  async function onSaveArticleClassifications(editor) {
    var btn = editor.querySelector(".cls-save-btn");
    var status = editor.querySelector(".cls-save-status");
    btn.disabled = true;
    status.textContent = "Salvando...";
    status.className = "cls-save-status";
    try {
      var data = gatherEditorData(editor);
      for (var i = 0; i < data.targets.length; i++) {
        var t = data.targets[i];
        var resp = await apiPost("/api/classifications", {
          article_id: data.article_id,
          target_key: t.target_key,
          target_name: t.target_name,
          article_sentiment: data.article_sentiment,
          target_sentiment: t.target_sentiment,
          categories: data.categories,
        });
        var saved = await resp.json().catch(function () { return {}; });
        if (!resp.ok) throw new Error(saved.detail || saved.error || "HTTP " + resp.status);
        applySavedClassification(saved);
      }
      status.textContent = "Salvo ✓";
      status.classList.add("cls-save-status--ok");
      setTimeout(function () {
        if (status.textContent === "Salvo ✓") {
          status.textContent = "";
          status.classList.remove("cls-save-status--ok");
        }
      }, 2500);
    } catch (e) {
      status.textContent = "Erro: " + (e && e.message ? e.message : e);
      status.classList.add("cls-save-status--err");
    } finally {
      btn.disabled = false;
    }
  }

  async function onAddCategory(editor) {
    var input = editor.querySelector(".cls-new-cat-input");
    var name = (input ? input.value : "").trim();
    if (!name) return;
    try {
      var resp = await apiPost("/api/categories", { name: name });
      var data = await resp.json().catch(function () { return {}; });
      if (!resp.ok) throw new Error(data.detail || data.error || "HTTP " + resp.status);
      var canonical = data.name || name;
      if (categoriesCache.indexOf(canonical) === -1) categoriesCache.push(canonical);
      // Add option to every category select on the page; select it in this editor
      document.querySelectorAll(".cls-cat-select").forEach(function (sel) {
        var existing = sel.querySelector('option[value="' + canonical.replace(/"/g, "&quot;") + '"]');
        if (!existing) {
          var opt = document.createElement("option");
          opt.value = canonical;
          opt.textContent = canonical;
          sel.appendChild(opt);
          existing = opt;
        }
        if (sel.closest(".cls-editor") === editor) existing.selected = true;
      });
      if (input) input.value = "";
    } catch (e) {
      window.alert("Erro ao criar categoria: " + (e && e.message ? e.message : e));
    }
  }

  app.addEventListener("click", function (event) {
    if (!editorEnabled) return;
    var saveBtn = event.target.closest(".cls-save-btn");
    if (saveBtn) {
      event.preventDefault();
      var editor = saveBtn.closest(".cls-editor");
      if (editor) onSaveArticleClassifications(editor);
      return;
    }
    var addBtn = event.target.closest(".cls-add-cat-btn");
    if (addBtn) {
      event.preventDefault();
      var editor2 = addBtn.closest(".cls-editor");
      if (editor2) onAddCategory(editor2);
      return;
    }
  });


  // Categories are public. Always cache them so read-only users still see the
  // taxonomy on hover/inspection (and admins land with the cache populated).
  apiFetch("/api/categories", { cache: "no-store" })
    .then(function (r) { return r.ok ? r.json() : { categories: [] }; })
    .then(function (data) {
      categoriesCache = (data.categories || []).map(function (c) { return c.name; });
    })
    .catch(function () { /* leave categoriesCache empty */ });

  // Live classifications overlay — public read, applies to every visitor so
  // the static snapshot's classification chips stay current.
  apiFetch("/api/classifications", { cache: "no-store" })
    .then(function (r) { return r.ok ? r.json() : { classifications: [] }; })
    .then(function (data) {
      var liveByKey = {};
      (data.classifications || []).forEach(function (c) {
        var k = c.article_id + "|" + c.target_key;
        liveByKey[k] = c;
      });
      mergeWhenReady(liveByKey);
    })
    .catch(function () { /* network failure: keep static payload as is */ });

  function mergeWhenReady(liveByKey) {
    var timer = setInterval(function () {
      if (!payload || !payload.stories) return;
      clearInterval(timer);
      (payload.stories || []).forEach(function (story) {
        (story.articles || []).forEach(function (article) {
          var fresh = [];
          Object.keys(liveByKey).forEach(function (k) {
            var rec = liveByKey[k];
            if (rec && rec.article_id === article.articleId) {
              fresh.push(rec);
            }
          });
          article.classifications = fresh;
        });
      });
      applyState();
    }, 100);
  }

  fetch(dataUrl, { cache: "no-store" })
    .then(function (response) {
      if (!response.ok) throw new Error("Falha ao carregar dados do clipping");
      return response.json();
    })
    .then(function (json) {
      payload = json || {};
      document.title = (payload.meta && payload.meta.pageTitle) || document.title;
      (payload.targets || []).forEach(function (target) {
        labelsByKey[target.key] = target.label || target.key;
      });
      selectedTargets = new Set((payload.defaultTargets || []).filter(Boolean));
      if (!selectedTargets.size) {
        (payload.targets || []).forEach(function (target) {
          selectedTargets.add(target.key);
        });
      }
      if (loadingState) {
        loadingState.hidden = true;
      }
      applyState();
      refreshTargets();
      pollStatus();
      window.setInterval(pollStatus, 5000);
    })
    .catch(function (error) {
      showError(error && error.message ? error.message : "Erro inesperado.");
    });
})();
