(function () {
  const app = document.getElementById("app");
  if (!app) return;

  const dataUrl = app.dataset.clippingDataUrl;
  const rawUrl = app.dataset.clippingRawUrl;
  // API base URL. Empty string = same-origin unless this is a generated static bundle.
  const apiUrl = (app.dataset.clippingApiUrl || "").trim().replace(/\/$/, "");
  const staticBundle = app.dataset.clippingStatic === "1";
  const initialSessionRole = (app.dataset.clippingSessionRole || "").trim();
  const apiAvailable = Boolean(apiUrl) || !staticBundle;
  let editorEnabled = apiAvailable;
  let csrfToken = "";
  let csrfPromise = null;
  let categoriesCache = [];

  function apiFetch(path, init) {
    if (!apiAvailable) return Promise.reject(new Error("api_unavailable"));
    return fetch(apiUrl + path, Object.assign({ credentials: "same-origin" }, init || {}));
  }

  function ensureCsrfToken() {
    if (!apiAvailable) return Promise.reject(new Error("api_unavailable"));
    if (csrfToken) return Promise.resolve(csrfToken);
    if (!csrfPromise) {
      csrfPromise = apiFetch("/api/csrf", { cache: "no-store" })
        .then(function (resp) {
          if (!resp.ok) throw new Error("HTTP " + resp.status);
          return resp.json();
        })
        .then(function (data) {
          csrfToken = String((data && data.csrf) || "");
          if (!csrfToken) throw new Error("csrf_unavailable");
          return csrfToken;
        })
        .catch(function (error) {
          csrfPromise = null;
          throw error;
        });
    }
    return csrfPromise;
  }

  async function apiPost(path, body) {
    await ensureCsrfToken();
    var headers = { "Content-Type": "application/json" };
    if (csrfToken) headers["X-CSRF-Token"] = csrfToken;
    return apiFetch(path, { method: "POST", headers: headers, body: JSON.stringify(body) });
  }
  async function apiPatch(path, body) {
    await ensureCsrfToken();
    var headers = { "Content-Type": "application/json" };
    if (csrfToken) headers["X-CSRF-Token"] = csrfToken;
    return apiFetch(path, { method: "PATCH", headers: headers, body: JSON.stringify(body) });
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
  const manageTargetsBox = document.getElementById("manageTargetsBox");
  const manageTargetsList = document.getElementById("manageTargetsList");
  const archivedTargetsList = document.getElementById("archivedTargetsList");
  const manageTargetsBlocked = document.getElementById("manageTargetsBlocked");
  const manageTargetsMessage = document.getElementById("manageTargetsMessage");
  const primaryRunTargets = document.getElementById("primaryRunTargets");
  const secondaryRunTargets = document.getElementById("secondaryRunTargets");
  const dateFromInput = document.getElementById("dateFromInput");
  const dateToInput = document.getElementById("dateToInput");
  const runUpdateButton = document.getElementById("runUpdateButton");
  const cancelUpdateButton = document.getElementById("cancelUpdateButton");
  const cancelUpdateButtonProgress = document.getElementById("cancelUpdateButtonProgress");
  const resumeUpdateButton = document.getElementById("resumeUpdateButton");
  const runFormMessage = document.getElementById("runFormMessage");
  const addTargetMessage = document.getElementById("addTargetMessage");
  const runnerStatusPill = document.getElementById("runnerStatusPill");
  const sharedStatusPill = document.getElementById("sharedStatusPill");
  const progressFill = document.getElementById("updateProgressFill");
  const progressPercentText = document.getElementById("progressPercentText");
  const progressActionMessage = document.getElementById("progressActionMessage");
  const progressSteps = Array.from(document.querySelectorAll("[data-progress-step]"));
  const progressTarget = document.getElementById("progressTarget");
  const progressDates = document.getElementById("progressDates");
  const progressSource = document.getElementById("progressSource");
  const progressArticles = document.getElementById("progressArticles");
  const progressMentions = document.getElementById("progressMentions");
  const progressStories = document.getElementById("progressStories");
  const progressLiveResults = document.getElementById("progressLiveResults");
  const progressRecentSources = document.getElementById("progressRecentSources");
  const progressWarnings = document.getElementById("progressWarnings");
  const baseStoriesStat = document.getElementById("baseStoriesStat");
  const baseArticlesStat = document.getElementById("baseArticlesStat");
  const baseRawStat = document.getElementById("baseRawStat");
  const baseUpdatedText = document.getElementById("baseUpdatedText");
  const LAZY_BATCH = 50;
  const ACTIVE_RUN_MESSAGE = "Já existe uma atualização em andamento. Acompanhe em Progresso compartilhado.";

  let payload = null;
  let selectedTargets = new Set();
  let currentSort = "newest";
  let flatSorted = [];
  let flatRendered = 0;
  let loadMoreBtn = null;
  let rawTextsCache = null;
  let rawTextsPromise = null;
  let runTargets = [];
  let managedTargets = [];
  let activeTargetKeys = new Set();
  let editingTargetKey = "";
  let pendingArchiveKey = "";
  let latestStatus = null;
  let liveResultsSignature = "";
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
    if (normalized.indexOf("trecho " + "bruto") !== -1) return "Trecho da matéria";
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

  function isoToBrDate(value) {
    var raw = String(value || "").trim();
    var match = raw.slice(0, 10).match(/^(\d{4})-(\d{2})-(\d{2})$/);
    if (match) return match[3] + "/" + match[2] + "/" + match[1];
    if (/^\d{2}\/\d{2}\/\d{4}$/.test(raw)) return raw;
    return raw;
  }

  function brDateToIso(value) {
    var raw = String(value || "").trim();
    var iso = raw.match(/^(\d{4})-(\d{2})-(\d{2})$/);
    if (iso) return raw;
    var match = raw.match(/^(\d{2})\/(\d{2})\/(\d{4})$/);
    if (!match) return "";
    var day = Number(match[1]);
    var month = Number(match[2]);
    var year = Number(match[3]);
    var date = new Date(Date.UTC(year, month - 1, day));
    if (date.getUTCFullYear() !== year || date.getUTCMonth() !== month - 1 || date.getUTCDate() !== day) return "";
    return match[3] + "-" + match[2] + "-" + match[1];
  }

  function dateMaskValue(value) {
    var digits = String(value || "").replace(/\D/g, "").slice(0, 8);
    if (digits.length <= 2) return digits;
    if (digits.length <= 4) return digits.slice(0, 2) + "/" + digits.slice(2);
    return digits.slice(0, 2) + "/" + digits.slice(2, 4) + "/" + digits.slice(4);
  }

  function attachDateMask(input) {
    if (!input) return;
    input.addEventListener("input", function () {
      input.value = dateMaskValue(input.value);
    });
  }

  function normalizeTargetsResponse(data, options) {
    options = options || {};
    var body = data || {};
    var nested = body.targets && !Array.isArray(body.targets) ? body.targets : body;
    var rows = Array.isArray(body.targets) ? body.targets : Array.isArray(nested.targets) ? nested.targets : [];
    var primaryKeys = Array.isArray(nested.primaryKeys) ? nested.primaryKeys : [];
    return rows
      .filter(function (target) { return target && target.key; })
      .map(function (target) {
        var hasPrimary = Object.prototype.hasOwnProperty.call(target, "primary");
        return {
          key: String(target.key),
          label: String(target.label || target.display_name || target.key),
          primary: hasPrimary ? Boolean(target.primary) : primaryKeys.indexOf(String(target.key)) !== -1,
          archived: Boolean(target.archived),
          keywords: Array.isArray(target.keywords) ? target.keywords.map(String) : [],
          exact_aliases: Array.isArray(target.exact_aliases) ? target.exact_aliases.map(String) : [],
          archived_at: String(target.archived_at || ""),
          archive_reason: String(target.archive_reason || ""),
        };
      })
      .filter(function (target) { return options.includeArchived || !target.archived; });
  }

  function isPublicTarget(target) {
    var key = String(target && target.key || "");
    if (!key || Boolean(target && target.archived)) return false;
    return !activeTargetKeys.size || activeTargetKeys.has(key);
  }

  function payloadCountsForTarget(key) {
    var counts = { storyCount: 0, articleCount: 0 };
    if (!payload || !Array.isArray(payload.stories)) return counts;
    (payload.stories || []).forEach(function (story) {
      var keys = Array.isArray(story.targetKeys) ? story.targetKeys.map(String) : [];
      if (keys.indexOf(key) === -1) return;
      counts.storyCount += 1;
      counts.articleCount += storyArticleCountForTarget(story, key);
    });
    return counts;
  }

  function mergeRuntimeTargetsIntoPayload(targets) {
    if (!payload) return;
    if (!Array.isArray(payload.targets)) payload.targets = [];
    var byKey = {};
    payload.targets.forEach(function (target) {
      if (target && target.key) byKey[String(target.key)] = target;
    });
    (targets || []).forEach(function (target) {
      if (!target || !target.key || target.archived) return;
      var key = String(target.key);
      var usage = payloadCountsForTarget(key);
      var existing = byKey[key];
      if (existing) {
        existing.label = target.label || existing.label || key;
        existing.primary = Boolean(existing.primary || target.primary);
        existing.archived = false;
        existing.storyCount = usage.storyCount;
        existing.articleCount = usage.articleCount;
        return;
      }
      payload.targets.push({
        key: key,
        label: target.label || key,
        primary: Boolean(target.primary),
        archived: false,
        storyCount: usage.storyCount,
        articleCount: usage.articleCount,
      });
    });
  }

  function activeTargetKeysFrom(keys) {
    var rows = (keys || [])
      .map(function (key) { return String(key || "").trim(); })
      .filter(Boolean);
    if (!activeTargetKeys.size) return rows;
    return rows.filter(function (key) { return activeTargetKeys.has(key); });
  }

  function ensureSelectedTargets() {
    if (!payload || !payload.targets) return;
    var visibleTargets = (payload.targets || []).filter(isPublicTarget);
    var next = new Set();
    selectedTargets.forEach(function (key) {
      if (!activeTargetKeys.size || activeTargetKeys.has(key)) next.add(key);
    });
    selectedTargets = next;
    if (!selectedTargets.size) {
      var primaryTargets = visibleTargets.filter(function (target) { return target.primary; });
      (primaryTargets.length ? primaryTargets : visibleTargets).forEach(function (target) {
        selectedTargets.add(target.key);
      });
    }
  }

  function setMessage(el, text, kind) {
    if (!el) return;
    el.textContent = text || "";
    el.classList.remove("is-error", "is-ok");
    if (kind) el.classList.add(kind === "error" ? "is-error" : "is-ok");
  }

  function apiErrorMessage(data, status) {
    var payload = data && typeof data === "object" ? data : {};
    var detail = payload.detail;
    var parts = [];
    if (detail && typeof detail === "object") {
      if (detail.message) parts.push(String(detail.message));
      if (detail.suggestion) parts.push(String(detail.suggestion));
    } else if (typeof detail === "string") {
      parts.push(detail);
    }
    if (!parts.length && payload.message) parts.push(String(payload.message));
    if (!parts.length && typeof payload.error === "string") parts.push(payload.error);
    if (payload.suggestion && parts.indexOf(String(payload.suggestion)) === -1) parts.push(String(payload.suggestion));
    if (detail && typeof detail === "object" && detail.cause) parts.push("Detalhe: " + String(detail.cause));
    else if (payload.cause) parts.push("Detalhe: " + String(payload.cause));
    return parts.filter(Boolean).join(" ") || "HTTP " + status;
  }

  function friendlyError(error, fallback) {
    var raw = error && error.message ? error.message : String(error || "");
    console.error("[clipping] detailed error", error);
    if (raw.indexOf("Aguarde a atualização terminar") !== -1) return "Aguarde a atualização terminar para mudar os nomes acompanhados.";
    if (raw.indexOf("job_already_running") !== -1) return "Já existe uma atualização em andamento.";
    if (raw.indexOf("persistent_storage_not_configured") !== -1) return "A gravação da base ainda não está pronta neste ambiente.";
    if (raw.indexOf("periodo_muito_longo") !== -1) return "Escolha um período de até 7 dias.";
    if (raw.indexOf("periodo_invalido") !== -1) return "Confira as datas: a inicial precisa vir antes da final.";
    if (raw.indexOf("data_futura") !== -1) return "As datas precisam ser de hoje ou anteriores.";
    if (raw.indexOf("data_invalida") !== -1) return "Preencha as duas datas.";
    if (raw.indexOf("unknown_target_keys") !== -1) return "Um dos nomes selecionados ainda não está disponível. Atualize a página e tente de novo.";
    if (raw && raw !== "[object Object]" && raw.indexOf("HTTP ") !== 0) return raw;
    return fallback || "Não foi possível concluir agora. Tente novamente em instantes.";
  }

  function targetMutationMessage(base, data) {
    var message = base;
    var sync = data && data.targetSync ? data.targetSync : null;
    if (sync) {
      var count = Number(sync.updatedCount || 0);
      if (count > 0) {
        message += " " + count + (count === 1 ? " notícia existente entrou" : " notícias existentes entraram") + " na Base atual.";
      } else {
        message += " A base atual foi conferida para esse nome.";
      }
    }
    if (data && data.activeJobNotice) message += " " + data.activeJobNotice;
    if (data && data.warning && data.warning.message) message += " " + data.warning.message;
    return message;
  }

  function showFriendlyProblem(message) {
    setMessage(runFormMessage, message, "error");
    if (window.alert) window.alert(message);
  }

  function badgeHtml(keys) {
    return activeTargetKeysFrom(keys || [])
      .map(function (key) {
        const label = labelsByKey[key] || key;
        return '<span class="chip">' + escapeHtml(label) + "</span>";
      })
      .join("");
  }

  function storyVisible(story) {
    const keys = activeTargetKeysFrom(story.targetKeys || []);
    if (activeTargetKeys.size && (story.targetKeys || []).length && !keys.length) return false;
    if (!keys.length) return true;
    return keys.some(function (key) {
      return selectedTargets.has(key);
    });
  }

  function allPublicTargetsSelected() {
    const allKeys = (payload.targets || []).filter(isPublicTarget).map(function (target) {
      return target.key;
    });
    return !allKeys.length || allKeys.every(function (key) { return selectedTargets.has(key); });
  }

  function articleTargetKeys(article, story) {
    var keys = article && Array.isArray(article.targetKeys) && article.targetKeys.length ? article.targetKeys : story.targetKeys || [];
    return activeTargetKeysFrom(keys || []);
  }

  function articleVisibleForSelection(article, story) {
    var keys = articleTargetKeys(article, story);
    if (!activeTargetKeys.size && !keys.length) return true;
    if (!keys.length) return true;
    if (allPublicTargetsSelected()) return true;
    return keys.some(function (key) { return selectedTargets.has(key); });
  }

  function visibleArticlesForStory(story) {
    return (story.articles || []).filter(function (article) {
      return articleVisibleForSelection(article, story);
    });
  }

  function storyArticleCountForTarget(story, key) {
    return (story.articles || []).filter(function (article) {
      return articleTargetKeys(article, story).indexOf(key) !== -1;
    }).length;
  }

  function activeLabel() {
    const allKeys = (payload.targets || []).filter(isPublicTarget).map(function (target) {
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
      visibleArticlesForStory(story).forEach(function (article) {
        var originalTargetKeys = articleTargetKeys(article, story);
        var visibleTargetKeys = originalTargetKeys.slice();
        if (!allPublicTargetsSelected()) {
          visibleTargetKeys = visibleTargetKeys.filter(function (key) { return selectedTargets.has(key); });
        }
        articles.push({
          storyId: story.storyIdInt,
          storyTitle: story.title,
          storyTargets: activeTargetKeysFrom(story.targetKeys || []),
          articleId: article.articleId,
          title: article.title,
          url: article.url,
          sourceName: article.sourceName,
          sourceHost: article.sourceHost,
          publishedAt: article.publishedAt,
          publishedDisplay: article.publishedDisplay,
          targetKeys: visibleTargetKeys.length ? visibleTargetKeys : originalTargetKeys,
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
      " histórias</span>" +
      "</button>"
    );
  }

  function renderTargetButtons() {
    var primary = [];
    var other = [];
    (payload.targets || []).filter(isPublicTarget).forEach(function (target) {
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
        "<summary>Nomes secundários (" + other.length + ")</summary>" +
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
      return sum + visibleArticlesForStory(story).length;
    }, 0);
    const aiCount = stories.reduce(function (sum, story) {
      return sum + visibleArticlesForStory(story).filter(function (article) {
        return article.summarySource === "ai";
      }).length;
    }, 0);
    const rawCount = articleCount - aiCount;
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
      baseUpdatedText.textContent = "Última atualização publicada: " + (payload.meta.generatedAt || "data não informada");
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

  function viewerIsAdmin() {
    if (!apiAvailable) return false;
    if (initialSessionRole) return initialSessionRole === "admin";
    if (!payload || !payload.meta || !Object.prototype.hasOwnProperty.call(payload.meta, "viewerRole")) return true;
    return payload.meta.viewerRole === "admin";
  }

  function applyViewerControls() {
    var isAdmin = viewerIsAdmin();
    editorEnabled = isAdmin && !(payload && payload.meta && payload.meta.editorEnabled === false);
    document.body.classList.toggle("viewer-readonly", !isAdmin);
    runTabs.forEach(function (button) {
      var tab = button.dataset.runTab || "";
      button.hidden = !isAdmin && tab !== "base";
    });
    if (!isAdmin) {
      activateRunTab("base");
      if (addTargetForm && addTargetForm.closest("details")) {
        addTargetForm.closest("details").hidden = true;
      }
      if (manageTargetsBox) manageTargetsBox.hidden = true;
    } else {
      if (addTargetForm && addTargetForm.closest("details")) {
        addTargetForm.closest("details").hidden = false;
      }
      if (manageTargetsBox) manageTargetsBox.hidden = false;
    }
  }

  applyViewerControls();

  function renderRunTarget(target) {
    var id = "run-target-" + target.key;
    var checked = target.primary ? " checked" : "";
    var cls = target.primary ? " run-target--primary" : "";
    var helper = target.primary ? "Marcado por padrão" : "Disponível";
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
    primaryRunTargets.innerHTML = primary.length ? primary.map(renderRunTarget).join("") : '<p class="filter-note">Carregando nomes acompanhados...</p>';
    secondaryRunTargets.innerHTML = secondary.length ? secondary.map(renderRunTarget).join("") : '<p class="filter-note">Nenhum nome secundário cadastrado ainda.</p>';
  }

  function fallbackTargetsFromPayload() {
    if (!payload || !payload.targets) return [];
    return (payload.targets || []).map(function (target) {
      return {
        key: String(target.key),
        label: String(target.label || target.key),
        primary: Boolean(target.primary),
        archived: Boolean(target.archived),
        keywords: Array.isArray(target.keywords) ? target.keywords.map(String) : [],
        exact_aliases: Array.isArray(target.exact_aliases) ? target.exact_aliases.map(String) : [],
      };
    }).filter(isPublicTarget);
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
        activeTargetKeys = new Set(runTargets.map(function (target) { return target.key; }));
        runTargets.forEach(function (target) {
          labelsByKey[target.key] = target.label || target.key;
        });
        mergeRuntimeTargetsIntoPayload(runTargets);
        ensureSelectedTargets();
        renderRunTargets();
        renderManageTargets();
        if (payload) applyState();
      })
      .catch(function (error) {
        console.error("[clipping] target refresh failed", error);
        runTargets = fallbackTargetsFromPayload();
        activeTargetKeys = new Set(runTargets.map(function (target) { return target.key; }));
        ensureSelectedTargets();
        renderRunTargets();
        renderManageTargets();
        if (payload) applyState();
      });
  }

  function targetActionsLocked() {
    return false;
  }

  function visibleTargetKeywords(target) {
    var display = String(target.label || target.key || "");
    return (target.keywords || []).filter(function (item) {
      return String(item || "").trim() && String(item || "").trim() !== display;
    });
  }

  function listText(items, emptyText) {
    var cleaned = (items || []).map(function (item) { return String(item || "").trim(); }).filter(Boolean);
    return cleaned.length ? cleaned.map(escapeHtml).join(", ") : '<span class="muted-inline">' + escapeHtml(emptyText) + "</span>";
  }

  function managedTargetForm(target, locked) {
    var disabled = locked ? " disabled" : "";
    return (
      '<form class="manage-target-form" data-manage-target-key="' + escapeHtml(target.key) + '">' +
      '<label>Nome <input name="display_name" value="' + escapeHtml(target.label || target.key) + '" required minlength="3"' + disabled + "></label>" +
      '<label>Termos relacionados <textarea name="keywords" rows="3"' + disabled + ">" + escapeHtml(visibleTargetKeywords(target).join(", ")) + "</textarea></label>" +
      '<label>Correspondências exatas <textarea name="exact_aliases" rows="3"' + disabled + ">" + escapeHtml((target.exact_aliases || []).join(", ")) + "</textarea></label>" +
      '<div class="manage-target-actions">' +
      '<button type="submit" class="primary-action"' + disabled + ">Salvar</button>" +
      '<button type="button" class="secondary-action" data-target-edit-cancel="' + escapeHtml(target.key) + '">Cancelar</button>' +
      "</div>" +
      "</form>"
    );
  }

  function managedTargetCard(target) {
    var key = escapeHtml(target.key);
    var locked = targetActionsLocked();
    var disabled = locked ? " disabled" : "";
    var disabledAttr = locked ? ' aria-disabled="true"' : "";
    var archived = Boolean(target.archived);
    var classes = "manage-target-card" + (archived ? " is-archived" : "");
    var meta =
      '<dl class="manage-target-meta">' +
      "<div><dt>Termos relacionados</dt><dd>" + listText(visibleTargetKeywords(target), "Sem termos extras") + "</dd></div>" +
      "<div><dt>Correspondências exatas</dt><dd>" + listText(target.exact_aliases || [], "Sem correspondências exatas") + "</dd></div>" +
      "</dl>";
    var body = '<div class="manage-target-card-head"><div><strong>' + escapeHtml(target.label || target.key) + "</strong><small>" + escapeHtml(target.key) + "</small></div></div>";
    if (!archived && editingTargetKey === target.key) {
      body += managedTargetForm(target, locked);
    } else {
      body += meta;
      if (archived) {
        body +=
          '<p class="manage-target-archive-note">' +
          escapeHtml(target.archive_reason || "Arquivado pela equipe.") +
          (target.archived_at ? " · " + escapeHtml(target.archived_at) : "") +
          "</p>" +
          '<div class="manage-target-actions">' +
          '<button type="button" class="secondary-action" data-target-restore="' + key + '"' + disabled + disabledAttr + ">Restaurar</button>" +
          "</div>";
      } else if (pendingArchiveKey === target.key) {
        body +=
          '<div class="manage-target-danger" role="alert">' +
          "<strong>Arquivar este nome?</strong>" +
          "<p>Este nome deixará de aparecer nas próximas atualizações e nos filtros do painel. As notícias antigas continuam preservadas internamente.</p>" +
          '<div class="manage-target-actions">' +
          '<button type="button" class="danger-action" data-target-archive-confirm="' + key + '"' + disabled + disabledAttr + ">Arquivar nome</button>" +
          '<button type="button" class="secondary-action" data-target-archive-cancel="' + key + '">Cancelar</button>' +
          "</div>" +
          "</div>";
      } else {
        body +=
          '<div class="manage-target-actions">' +
          '<button type="button" class="secondary-action" data-target-edit="' + key + '"' + disabled + disabledAttr + ">Editar</button>" +
          '<button type="button" class="danger-action" data-target-archive-start="' + key + '"' + disabled + disabledAttr + ">Arquivar</button>" +
          "</div>";
      }
    }
    return '<article class="' + classes + '">' + body + "</article>";
  }

  function renderManageTargets() {
    if (!manageTargetsList || !archivedTargetsList) return;
    var locked = targetActionsLocked();
    if (manageTargetsBlocked) manageTargetsBlocked.hidden = !locked;
    var active = managedTargets.filter(function (target) { return !target.primary && !target.archived; });
    var archived = managedTargets.filter(function (target) { return !target.primary && target.archived; });
    manageTargetsList.innerHTML = active.length
      ? active.map(managedTargetCard).join("")
      : '<p class="filter-note">Nenhum nome secundário ativo cadastrado.</p>';
    archivedTargetsList.innerHTML = archived.length
      ? archived.map(managedTargetCard).join("")
      : '<p class="filter-note">Nenhum nome arquivado.</p>';
  }

  function refreshManageTargets() {
    if (!manageTargetsBox) return Promise.resolve();
    return apiFetch("/api/targets?include_archived=1", { cache: "no-store" })
      .then(function (resp) {
        return resp.json().catch(function () { return {}; }).then(function (data) {
          if (!resp.ok) throw new Error(apiErrorMessage(data, resp.status));
          return data;
        });
      })
      .then(function (data) {
        managedTargets = normalizeTargetsResponse(data, { includeArchived: true });
        managedTargets.forEach(function (target) {
          labelsByKey[target.key] = target.label || target.key;
        });
        renderManageTargets();
      })
      .catch(function (error) {
        setMessage(manageTargetsMessage, friendlyError(error, "Não foi possível carregar os nomes extras."), "error");
      });
  }

  async function reloadTargetsAfterManagement(targetKey, options) {
    var opts = options || {};
    await refreshTargets();
    if (targetKey) {
      if (opts.remove) selectedTargets.delete(targetKey);
      if (opts.select) selectedTargets.add(targetKey);
      ensureSelectedTargets();
      if (payload) applyState();
    }
    await pollBaseLiveResults();
    if (manageTargetsBox && manageTargetsBox.open) await refreshManageTargets();
  }

  async function archiveManagedTarget(key) {
    setMessage(manageTargetsMessage, "Arquivando...", "");
    try {
      var resp = await apiPost("/api/targets/" + encodeURIComponent(key) + "/archive", {
        reason: "Arquivado pelo painel de gerenciamento.",
      });
      var data = await resp.json().catch(function () { return {}; });
      if (!resp.ok) throw new Error(apiErrorMessage(data, resp.status));
      pendingArchiveKey = "";
      editingTargetKey = "";
      setMessage(manageTargetsMessage, targetMutationMessage("Nome arquivado. Ele não aparecerá nas próximas atualizações.", data), "ok");
      await reloadTargetsAfterManagement(key, { remove: true });
    } catch (error) {
      setMessage(manageTargetsMessage, friendlyError(error, "Não foi possível arquivar este nome."), "error");
      renderManageTargets();
    }
  }

  async function restoreManagedTarget(key) {
    setMessage(manageTargetsMessage, "Restaurando...", "");
    try {
      var resp = await apiPost("/api/targets/" + encodeURIComponent(key) + "/restore", {});
      var data = await resp.json().catch(function () { return {}; });
      if (!resp.ok) throw new Error(apiErrorMessage(data, resp.status));
      pendingArchiveKey = "";
      editingTargetKey = "";
      setMessage(manageTargetsMessage, targetMutationMessage("Nome restaurado. Ele já vale para a Base atual e para próximas rodadas.", data), "ok");
      await reloadTargetsAfterManagement(key, { select: true });
    } catch (error) {
      setMessage(manageTargetsMessage, friendlyError(error, "Não foi possível restaurar este nome."), "error");
      renderManageTargets();
    }
  }

  function selectedRunTargetKeys() {
    var keys = [];
    [primaryRunTargets, secondaryRunTargets].forEach(function (container) {
      if (!container) return;
      container.querySelectorAll('input[type="checkbox"]:checked').forEach(function (input) {
        if (keys.indexOf(input.value) === -1) keys.push(input.value);
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
    if (!dateFromInput.value) dateFromInput.value = isoToBrDate(suggestedFrom);
    if (!dateToInput.value) dateToInput.value = isoToBrDate(suggestedTo);
  }

  function statusLabel(status) {
    if (status === "running") return "Atualizando";
    if (status === "queued") return "Na fila";
    if (status === "exporting") return "Publicando";
    if (status === "cancel_requested") return "Cancelando";
    if (status === "succeeded") return "Concluído";
    if (status === "complete") return "Fonte concluída";
    if (status === "pending") return "Aguardando fonte";
    if (status === "retrying") return "Tentando novamente";
    if (status === "interrupted_resumable") return "Pronto para retomar";
    if (status === "failed_needs_fix") return "Fonte precisa de correção";
    if (status === "interrupted") return "Interrompido";
    if (status === "failed") return "Precisa de atenção";
    if (status === "cancelled" || status === "canceled") return "Cancelado";
    return "Pronto";
  }

  function latestProgressEvent(job) {
    var events = (job && job.events) || [];
    for (var i = 0; i < events.length; i++) {
      if (events[i] && events[i].payload) return events[i];
    }
    events = (job && job.recentEvents) || [];
    for (var j = 0; j < events.length; j++) {
      if (events[j] && events[j].payload) return events[j];
    }
    return null;
  }

  function numberValue(value) {
    var num = Number(value || 0);
    return Number.isFinite(num) ? num : 0;
  }

  function activeStatus(status) {
    return ["queued", "running", "exporting", "cancel_requested"].indexOf(status) !== -1;
  }

  function progressValue(progress, camelName, snakeName) {
    if (!progress) return undefined;
    if (Object.prototype.hasOwnProperty.call(progress, camelName)) return progress[camelName];
    return progress[snakeName];
  }

  function progressState(job, event) {
    var status = job && job.status;
    if (status === "succeeded") return { known: true, percent: 100, label: "Concluído" };
    if (status === "interrupted_resumable") return { known: true, percent: 100, label: "Interrompido, com retomada disponível" };
    if (status === "failed_needs_fix") return { known: true, percent: 100, label: "Fonte precisa de correção" };
    if (status === "interrupted") return { known: true, percent: 100, label: "Interrompido por reinício" };
    if (status === "failed") return { known: true, percent: 100, label: "Interrompido por erro" };
    if (status === "cancelled" || status === "canceled") return { known: true, percent: 0, label: "Cancelado" };
    if (status === "cancel_requested") return { known: false, percent: 0, label: "Cancelamento solicitado" };
    var aggregate = job && job.progress ? job.progress : {};
    var total = numberValue(progressValue(aggregate, "candidatesTotal", "candidates_total"));
    var seen = numberValue(progressValue(aggregate, "candidatesSeen", "candidates_seen"));
    if (total > 0) {
      var percent = Math.max(0, Math.min(98, Math.round((seen / total) * 100)));
      return { known: true, percent: percent, label: seen + " de " + total + " itens verificados" };
    }
    var payload = event && event.payload ? event.payload : {};
    total = numberValue(payload.candidates_total || payload.max_candidates);
    seen = numberValue(payload.candidates_seen);
    if (total > 0) {
      return { known: true, percent: Math.max(0, Math.min(98, Math.round((seen / total) * 100))), label: seen + " de " + total + " itens nesta fonte" };
    }
    if (activeStatus(status)) return { known: false, percent: 0, label: "Atualização em andamento" };
    return { known: false, percent: 0, label: "Aguardando início" };
  }

  function progressStepState(status, step, hasSaved) {
    var order = ["prepare", "search", "save", "publish"];
    var currentByStatus = {
      queued: "prepare",
      running: hasSaved ? "save" : "search",
      cancel_requested: hasSaved ? "save" : "search",
      exporting: "publish",
    };
    if (status === "succeeded") return "done";
    if (status === "interrupted_resumable") return step === "search" || step === "save" ? "error" : "pending";
    if (status === "failed_needs_fix") return step === "search" ? "error" : "pending";
    if (status === "interrupted") return step === "search" ? "error" : "pending";
    if (status === "failed") return step === "search" ? "error" : "pending";
    if (status === "cancelled" || status === "canceled") return step === "search" ? "cancelled" : "pending";
    var current = currentByStatus[status] || "";
    if (!current) return "pending";
    var currentIndex = order.indexOf(current);
    var stepIndex = order.indexOf(step);
    if (stepIndex < currentIndex) return "done";
    if (stepIndex === currentIndex) return "active";
    return "pending";
  }

  function renderProgressSteps(status, hasSaved) {
    progressSteps.forEach(function (stepEl) {
      var state = progressStepState(status, stepEl.dataset.progressStep || "", hasSaved);
      stepEl.classList.toggle("is-done", state === "done");
      stepEl.classList.toggle("is-active", state === "active");
      stepEl.classList.toggle("is-error", state === "error");
      stepEl.classList.toggle("is-cancelled", state === "cancelled");
    });
  }

  function progressCount(job, event, camelName, snakeName, rowName) {
    var progress = job && job.progress ? job.progress : {};
    var payload = event && event.payload ? event.payload : {};
    return Math.max(
      numberValue(progressValue(progress, camelName, snakeName)),
      numberValue(job && job[rowName]),
      numberValue(payload[snakeName])
    );
  }

  function progressSummary(job, event, state, currentTarget, currentSource) {
    var status = job && job.status;
    if (status === "queued") return "Preparando a rodada.";
    if (status === "running") {
      var targetPart = currentTarget ? " de " + currentTarget : "";
      var sourcePart = currentSource ? " em " + currentSource : "";
      var detail = state && state.known && state.label ? " " + state.label + "." : "";
      var savedStories = progressCount(job, event, "storiesTouched", "stories_touched", "stories_touched");
      var savedPart = savedStories > 0
        ? " Histórias salvas nesta rodada: " + savedStories + ". A Base atual já mostra o que foi salvo."
        : "";
      return "Buscando notícias" + targetPart + sourcePart + "." + detail + savedPart;
    }
    if (status === "exporting") return "Publicando o painel atualizado.";
    if (status === "cancel_requested") return "Cancelamento solicitado. A rodada vai parar ao fim da etapa atual.";
    if (status === "succeeded") return "Atualização concluída.";
    if (status === "interrupted_resumable") return "O servidor reiniciou, mas há checkpoint salvo. A atualização pode ser retomada.";
    if (status === "failed_needs_fix") return "Uma fonte falhou e precisa de correção antes de fechar a cobertura.";
    if (status === "interrupted") return "A atualização foi interrompida por reinício do servidor. As notícias já salvas continuam preservadas.";
    if (status === "failed") return "A atualização encontrou um problema e não terminou.";
    if (status === "cancelled" || status === "canceled") return "Atualização cancelada.";
    return state && state.label ? state.label : "Aguardando início";
  }

  function warningText(job) {
    if (!job) return "";
    if (job.failedSources && job.failedSources.length) return "Há fonte com falha visível. Corrija a fonte e retome a atualização para completar a cobertura.";
    if (job.status === "interrupted_resumable") return "A atualização não foi cancelada; ela parou por reinício e pode continuar do checkpoint.";
    if (job.status === "interrupted") return "A atualização não foi cancelada por alguém; o servidor reiniciou antes da publicação final.";
    if (job.status === "failed") return "A atualização parou antes de terminar.";
    if (job.freshness && job.freshness.stale) return "A publicação pode estar desatualizada em relação à última execução concluída.";
    var warnings = [];
    var events = (job.recentEvents || []).concat(job.events || []);
    for (var i = 0; i < events.length; i++) {
      var payload = events[i].payload || {};
      var errors = payload.errors || payload.warnings || [];
      if (Array.isArray(errors)) {
        errors.forEach(function (item) {
          if (item && warnings.indexOf(String(item)) === -1) warnings.push(String(item));
        });
      } else if (errors) {
        warnings.push(String(errors));
      }
      if (payload.error) warnings.push(String(payload.error));
    }
    if (warnings.length) {
      console.warn("[clipping] update warning", warnings);
      return "Algumas fontes não responderam. A atualização continua com as demais.";
    }
    return "";
  }

  function eventSourceLabel(event) {
    var payload = event && event.payload ? event.payload : {};
    return String(payload.source_name || payload.source || payload.source_type || "").trim();
  }

  function eventTargetLabel(event, progress) {
    var payload = event && event.payload ? event.payload : {};
    var key = String(payload.target_key || "").trim();
    var labels = progressValue(progress, "targetLabels", "target_labels") || {};
    if (payload.target_label) return String(payload.target_label);
    if (key && labels[key]) return String(labels[key]);
    return key ? labelsByKey[key] || key : "";
  }

  function renderRecentSources(job) {
    if (!progressRecentSources) return;
    if (job && Array.isArray(job.sourceRuns) && job.sourceRuns.length) {
      var counts = job.sourceRunCounts || {};
      var totalSources = numberValue(job.sourceRunCount);
      var visibleSources = numberValue(job.sourceRunVisibleCount) || job.sourceRuns.length;
      var summaryParts = [];
      ["running", "retrying", "interrupted_resumable", "failed_needs_fix", "pending", "complete"].forEach(function (statusKey) {
        var count = numberValue(counts[statusKey]);
        if (count > 0) summaryParts.push(count + " " + statusLabel(statusKey).toLowerCase());
      });
      var summary = summaryParts.length ? summaryParts.join(", ") : "";
      if (totalSources > visibleSources) {
        summary += (summary ? " · " : "") + visibleSources + "/" + totalSources + " fontes exibidas";
      }
      var sourceRows = job.sourceRuns.slice(0, 8).map(function (source) {
        var status = statusLabel(source.status || "");
        var detail = [];
        var total = numberValue(source.candidatesTotal);
        var seen = numberValue(source.candidatesSeen);
        if (total > 0 || seen > 0) detail.push(seen + "/" + Math.max(total, seen) + " itens");
        if (numberValue(source.storiesTouched) > 0) detail.push(numberValue(source.storiesTouched) + " história(s)");
        if (source.cursor && source.cursor.day) detail.push(isoToBrDate(source.cursor.day));
        if (source.cursor && source.cursor.page) detail.push("página " + source.cursor.page);
        if (source.lastError) detail.push(source.lastError);
        return (
          "<li><strong>" + escapeHtml(source.sourceName || source.sourceType || "Fonte") + "</strong>" +
          " · " + escapeHtml(status) +
          (detail.length ? " · " + escapeHtml(detail.join(", ")) : "") +
          "</li>"
        );
      });
      progressRecentSources.hidden = !sourceRows.length;
      progressRecentSources.innerHTML = sourceRows.length ? "<h2>Cobertura por fonte</h2>" + (summary ? "<p>" + escapeHtml(summary) + "</p>" : "") + "<ul>" + sourceRows.join("") + "</ul>" : "";
      return;
    }
    var events = job ? (job.recentEvents || []).concat(job.events || []) : [];
    var rows = [];
    var seenKeys = {};
    events.forEach(function (event) {
      if (rows.length >= 5 || !event || !event.payload) return;
      var name = eventSourceLabel(event);
      if (!name) return;
      var payload = event.payload;
      var target = eventTargetLabel(event, job.progress || {});
      var key = [target, name, event.event].join("|");
      if (seenKeys[key]) return;
      seenKeys[key] = true;
      var total = numberValue(payload.candidates_total);
      var seen = numberValue(payload.candidates_seen);
      var articles = numberValue(payload.articles_inserted);
      var stories = numberValue(payload.stories_touched);
      var detail = "";
      if (total > 0 && seen > 0) detail = seen + "/" + total + " itens";
      else if (total > 0) detail = total + " itens encontrados";
      if (articles > 0) detail += (detail ? ", " : "") + articles + " notícia(s) nova(s)";
      if (stories > 0) detail += (detail ? ", " : "") + stories + " história(s) salva(s)";
      rows.push(
        "<li><strong>" + escapeHtml(name) + "</strong>" +
        (target ? " · " + escapeHtml(target) : "") +
        (detail ? " · " + escapeHtml(detail) : "") +
        "</li>"
      );
    });
    progressRecentSources.hidden = !rows.length;
    progressRecentSources.innerHTML = rows.length ? "<h2>Fontes recentes</h2><ul>" + rows.join("") + "</ul>" : "";
  }

  function renderStatus(statusPayload) {
    latestStatus = statusPayload || latestStatus || {};
    var current = latestStatus.current || {};
    var recent = latestStatus.recent || [];
    var job = current.status === "idle" && recent.length ? recent[0] : current;
    var event = latestProgressEvent(job);
    var eventPayload = event && event.payload ? event.payload : {};
    var label = statusLabel(job.status);
    var isRunning = activeStatus(job.status);
    var isError = job.status === "failed";
    [runnerStatusPill, sharedStatusPill].forEach(function (pill) {
      if (!pill) return;
      pill.textContent = label;
      pill.classList.toggle("is-running", isRunning);
      pill.classList.toggle("is-error", isError);
    });
    var progress = job.progress || {};
    var state = progressState(job, event);
    var savedStories = progressCount(job, event, "storiesTouched", "stories_touched", "stories_touched");
    renderProgressSteps(job.status, savedStories > 0);
    if (progressFill) {
      progressFill.classList.toggle("is-indeterminate", isRunning && !state.known);
      progressFill.style.width = state.known ? state.percent + "%" : "0%";
    }
    var aggregateKeys = progressValue(progress, "targetKeys", "target_keys");
    var aggregateLabels = progressValue(progress, "targetLabels", "target_labels") || {};
    var keys = Array.isArray(aggregateKeys) ? aggregateKeys.slice() : parseMaybeJsonList(job.target_keys);
    if (!keys.length && Array.isArray(job.target_keys)) keys = job.target_keys;
    var currentTarget = eventTargetLabel(event, progress);
    var currentSource = eventSourceLabel(event);
    if (progressTarget) {
      progressTarget.textContent = currentTarget || keys.map(function (key) {
        return aggregateLabels[key] ? aggregateLabels[key] : labelsByKey[key] || key;
      }).join(" + ") || "Aguardando";
    }
    if (progressDates) {
      var from = job.date_from || (dateFromInput && dateFromInput.value) || "";
      var to = job.date_to || (dateToInput && dateToInput.value) || "";
      progressDates.textContent = from && to ? isoToBrDate(from) + " a " + isoToBrDate(to) : "Aguardando";
    }
    if (progressSource) progressSource.textContent = currentSource || "Aguardando";
    if (progressPercentText) progressPercentText.textContent = progressSummary(job, event, state, currentTarget || progressTarget && progressTarget.textContent, currentSource);
    if (progressArticles) progressArticles.textContent = String(progressCount(job, event, "articlesInserted", "articles_inserted", "articles_inserted"));
    if (progressMentions) progressMentions.textContent = String(progressCount(job, event, "mentionsInserted", "mentions_inserted", "mentions_inserted"));
    if (progressStories) progressStories.textContent = String(savedStories);
    renderRecentSources(job);
    var warning = warningText(job);
    if (progressWarnings) {
      progressWarnings.hidden = !warning;
      progressWarnings.textContent = warning;
    }
    if (isError && job.error_message) console.error("[clipping] update failed", job.error_message);
    if (runUpdateButton) runUpdateButton.disabled = isRunning;
    if (resumeUpdateButton) {
      resumeUpdateButton.hidden = !job.resumeAvailable || isRunning;
      resumeUpdateButton.disabled = false;
    }
    if (runFormMessage) {
      if (isRunning) setMessage(runFormMessage, ACTIVE_RUN_MESSAGE, "");
      else if (runFormMessage.textContent === ACTIVE_RUN_MESSAGE) setMessage(runFormMessage, "", "");
    }
    [cancelUpdateButton, cancelUpdateButtonProgress].forEach(function (button) {
      if (!button) return;
      button.hidden = !isRunning;
      button.disabled = false;
    });
    renderManageTargets();
  }

  function renderStaticBundleStatus() {
    [runnerStatusPill, sharedStatusPill].forEach(function (pill) {
      if (!pill) return;
      pill.textContent = "Arquivo estático";
      pill.classList.remove("is-error");
    });
    if (runUpdateButton) runUpdateButton.disabled = true;
    if (resumeUpdateButton) resumeUpdateButton.hidden = true;
    [cancelUpdateButton, cancelUpdateButtonProgress].forEach(function (button) {
      if (!button) return;
      button.hidden = true;
      button.disabled = true;
    });
    setMessage(runFormMessage, "Este arquivo estático não dispara atualizações.", "");
  }

  function pollStatus() {
    if (!apiAvailable) {
      renderStaticBundleStatus();
      return Promise.resolve();
    }
    return apiFetch("/api/update/status", { cache: "no-store" })
      .then(function (resp) {
        if (!resp.ok) throw new Error("HTTP " + resp.status);
        return resp.json();
      })
      .then(function (data) {
        applySuggestedDates(data);
        renderStatus(data);
        pollLiveResults(data);
      })
      .catch(function (error) {
        console.error("[clipping] status polling failed", error);
        [runnerStatusPill, sharedStatusPill].forEach(function (pill) {
          if (!pill) return;
          pill.textContent = "Sem conexão";
          pill.classList.add("is-error");
        });
      });
  }

  function pollLiveResults(statusPayload) {
    if (!apiAvailable) return Promise.resolve();
    if (!payload) return Promise.resolve();
    var current = (statusPayload && statusPayload.current) || {};
    var recent = statusPayload && statusPayload.recent && statusPayload.recent.length ? statusPayload.recent[0] : {};
    var job = current.status === "idle" && recent.id ? recent : current;
    var jobId = String(job.id || "");
    var url = "/api/update/live-results" + (jobId ? "?job_id=" + encodeURIComponent(jobId) : "");
    return apiFetch(url, { cache: "no-store" })
      .then(function (resp) {
        if (!resp.ok) throw new Error("HTTP " + resp.status);
        return resp.json();
      })
      .then(function (data) {
        var signature = JSON.stringify((data.items || []).map(function (item) {
          return [item.articleId, item.storyId, item.publicationState, item.targetKeys || []];
        }));
        var changed = mergeLiveResultsIntoPayload(data);
        renderLiveResults(data);
        if (changed || signature !== liveResultsSignature) {
          liveResultsSignature = signature;
          ensureSelectedTargets();
          applyState();
        }
      })
      .catch(function () {
        if (progressLiveResults) {
          progressLiveResults.hidden = true;
          progressLiveResults.innerHTML = "";
        }
      });
  }

  function pollBaseLiveResults() {
    if (!apiAvailable) return Promise.resolve();
    if (!payload) return Promise.resolve();
    return apiFetch("/api/update/live-results?scope=base&limit=240", { cache: "no-store" })
      .then(function (resp) {
        if (!resp.ok) throw new Error("HTTP " + resp.status);
        return resp.json();
      })
      .then(function (data) {
        if (mergeLiveResultsIntoPayload(data)) {
          ensureSelectedTargets();
          applyState();
        }
      })
      .catch(function () {
        // Keep the published snapshot usable if the live overlay is unavailable.
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
          escapeHtml(story.title || "Sem título") +
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
        if (activeTargetKeys.size && !activeTargetKeys.has(String(cls.target_key || ""))) return;
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
    var targetKeys = activeTargetKeysFrom(article.targetKeys || []);
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
        '" target="_blank" rel="noreferrer">Abrir matéria original</a>'
      : "";
    const titleHtml = article.url
      ? '<a href="' +
        escapeHtml(article.url) +
        '" target="_blank" rel="noreferrer">' +
        escapeHtml(article.title || "Sem título") +
        "</a>"
      : escapeHtml(article.title || "Sem título");

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
      escapeHtml(article.sourceName || "Fonte não identificada") +
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

  function hostFromUrl(url) {
    try {
      return new URL(String(url || "")).hostname.replace(/^www\./, "");
    } catch (e) {
      return "";
    }
  }

  function liveSummary(item) {
    return String(item.summary || item.snippet || "Notícia confirmada e salva nesta rodada.");
  }

  function ensureLiveTargetRows(items) {
    if (!payload) return;
    if (!Array.isArray(payload.targets)) payload.targets = [];
    var byKey = {};
    (payload.targets || []).forEach(function (target) {
      if (target && target.key) byKey[String(target.key)] = target;
    });
    (items || []).forEach(function (item) {
      var labels = item.targetLabels || {};
      (item.targetKeys || []).forEach(function (key) {
        key = String(key || "").trim();
        if (!key) return;
        labelsByKey[key] = labels[key] || labelsByKey[key] || key;
        if (activeTargetKeys.size) activeTargetKeys.add(key);
        if (!byKey[key]) {
          byKey[key] = {
            key: key,
            label: labelsByKey[key],
            primary: false,
            archived: false,
            storyCount: 0,
            articleCount: 0,
          };
          payload.targets.push(byKey[key]);
        }
      });
    });
  }

  function recomputeTargetCounts() {
    if (!payload || !Array.isArray(payload.targets)) return;
    var counts = {};
    (payload.stories || []).forEach(function (story) {
      (story.targetKeys || []).forEach(function (key) {
        key = String(key || "");
        if (!key) return;
        if (!counts[key]) counts[key] = { storyCount: 0, articleCount: 0 };
        counts[key].storyCount += 1;
        counts[key].articleCount += storyArticleCountForTarget(story, key);
      });
    });
    (payload.targets || []).forEach(function (target) {
      var usage = counts[target.key] || { storyCount: 0, articleCount: 0 };
      target.storyCount = usage.storyCount;
      target.articleCount = usage.articleCount;
    });
  }

  function normalizePayloadCounts() {
    if (!payload || !Array.isArray(payload.stories)) return;
    if (!payload.meta) payload.meta = {};
    var totalArticles = 0;
    var totalAi = 0;
    (payload.stories || []).forEach(function (story) {
      if (!Array.isArray(story.articles)) story.articles = [];
      var articleCount = story.articles.length;
      var aiCount = story.articles.filter(function (article) {
        return article.summarySource === "ai";
      }).length;
      story.articleCount = articleCount;
      story.aiCount = aiCount;
      story.rawCount = articleCount - aiCount;
      totalArticles += articleCount;
      totalAi += aiCount;
    });
    payload.meta.totalStories = payload.stories.length;
    payload.meta.totalArticles = totalArticles;
    payload.meta.totalAi = totalAi;
    payload.meta.totalRaw = totalArticles - totalAi;
    recomputeTargetCounts();
  }

  function mergeLiveResultsIntoPayload(data) {
    if (!payload || !Array.isArray(data && data.items) || !data.items.length) return false;
    if (!Array.isArray(payload.stories)) payload.stories = [];
    if (!payload.meta) payload.meta = {};
    ensureLiveTargetRows(data.items);
    var changed = false;
    var storiesById = {};
    (payload.stories || []).forEach(function (story) {
      storiesById[String(story.storyIdInt || story.id || "")] = story;
    });

    data.items.forEach(function (item) {
      var storyId = Number(item.storyId || item.articleId || 0);
      if (!storyId) return;
      var storyKey = String(storyId);
      var targetKeys = (item.targetKeys || []).map(String).filter(Boolean);
      var story = storiesById[storyKey];
      if (!story) {
        story = {
          id: "st-" + storyId,
          storyIdInt: storyId,
          title: item.title || "Notícia salva nesta rodada",
          summaryLabel: "Salvo nesta rodada",
          summaryText: liveSummary(item),
          temperature: 34,
          createdAt: item.savedAt || item.publishedAt || "",
          updatedAt: item.savedAt || item.publishedAt || "",
          firstPublishedAt: item.publishedAt || item.savedAt || "",
          lastPublishedAt: item.publishedAt || item.savedAt || "",
          targetKeys: [],
          articleCount: 0,
          aiCount: 0,
          rawCount: 0,
          articles: [],
          isLiveResult: item.publicationState !== "published",
        };
        storiesById[storyKey] = story;
        payload.stories.unshift(story);
        changed = true;
      }
      if (!Array.isArray(story.targetKeys)) story.targetKeys = [];
      if (!Array.isArray(story.articles)) story.articles = [];
      targetKeys.forEach(function (key) {
        if (story.targetKeys.indexOf(key) === -1) {
          story.targetKeys.push(key);
          changed = true;
        }
      });
      var articleId = Number(item.articleId || 0);
      var existingArticle = null;
      (story.articles || []).forEach(function (article) {
        if (Number(article.articleId || 0) === articleId) existingArticle = article;
      });
      if (!existingArticle) {
        story.articles.push({
          articleId: articleId,
          title: item.title || "Sem título",
          url: item.url || "",
          sourceName: item.sourceName || "Fonte não identificada",
          sourceHost: hostFromUrl(item.url),
          publishedAt: item.publishedAt || item.savedAt || "",
          publishedDisplay: formatDate(item.publishedAt || item.savedAt || ""),
          targetKeys: targetKeys,
          summaryLabel: item.publicationState === "published" ? "Publicado no painel" : "Salvo agora",
          summaryPreview: liveSummary(item),
          rawTextKey: "",
          summarySource: "raw",
          classifications: [],
          isLiveResult: item.publicationState !== "published",
        });
        changed = true;
      } else {
        targetKeys.forEach(function (key) {
          if ((existingArticle.targetKeys || []).indexOf(key) === -1) {
            existingArticle.targetKeys = (existingArticle.targetKeys || []).concat([key]);
            changed = true;
          }
        });
      }
      story.articleCount = story.articles.length;
      story.rawCount = story.articleCount - Number(story.aiCount || 0);
    });

    if (changed) {
      recomputeTargetCounts();
      payload.meta.totalStories = Math.max(Number(payload.meta.totalStories || 0), payload.stories.length);
      var totalArticles = 0;
      (payload.stories || []).forEach(function (story) {
        totalArticles += Number(story.articleCount || (story.articles || []).length || 0);
      });
      payload.meta.totalArticles = Math.max(Number(payload.meta.totalArticles || 0), totalArticles);
    }
    return changed;
  }

  function renderLiveResults(data) {
    if (!progressLiveResults) return;
    var items = Array.isArray(data && data.items) ? data.items : [];
    progressLiveResults.hidden = !items.length;
    if (!items.length) {
      progressLiveResults.innerHTML = "";
      return;
    }
    var rows = items.slice(0, 8).map(function (item) {
      var badges = badgeHtml(item.targetKeys || []);
      var state = item.publicationState === "published" ? "Publicado no painel" : "Salvo agora";
      var title = escapeHtml(item.title || "Sem título");
      var url = item.url ? '<a href="' + escapeHtml(item.url) + '" target="_blank" rel="noreferrer">' + title + "</a>" : title;
      return (
        "<li>" +
        '<div><strong>' + url + "</strong>" +
        '<span>' + escapeHtml(item.sourceName || "Fonte não identificada") + " · " + escapeHtml(formatDate(item.publishedAt || item.savedAt || "")) + "</span></div>" +
        '<div class="chips">' + badges + '<span class="chip chip--live">' + escapeHtml(state) + "</span></div>" +
        "</li>"
      );
    });
    progressLiveResults.innerHTML =
      "<h2>Notícias salvas nesta rodada</h2>" +
      "<p>Estes itens já foram confirmados, salvos e entram automaticamente na Base atual.</p>" +
      "<ul>" + rows.join("") + "</ul>";
  }

  function renderStoryCard(story) {
    var storyArticles = visibleArticlesForStory(story);
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
      '<p class="eyebrow">História principal ' +
      story.storyIdInt +
      "</p>" +
      "<h2>" +
      escapeHtml(story.title || "Sem título") +
      "</h2>" +
      '<div class="chips">' +
      badgeHtml(story.targetKeys || []) +
      "</div>" +
      "</div>" +
      "</div>" +
      '<div class="story-stats">' +
      "<div><strong>" +
      escapeHtml(String(storyArticles.length)) +
      "</strong><span>notícias</span></div>" +
      "<div><strong>" +
      escapeHtml(String(Math.round(Number(story.temperature || 0)))) +
      "</strong><span>temperatura</span></div>" +
      "</div>" +
      "</summary>" +
      '<div class="story-meta">' +
      "<span>Primeira publicação: " +
      escapeHtml(story.firstPublishedAt ? formatDate(story.firstPublishedAt) : "") +
      "</span>" +
      "<span>Última publicação: " +
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
      storyArticles.map(renderArticleCard).join("") +
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
      flatStack.innerHTML = '<div class="panel empty-state">Nenhuma notícia corresponde aos filtros atuais.</div>';
      return;
    }

    const loading = document.createElement("div");
    loading.className = "flat-loading";
    loading.innerHTML = '<div class="flat-spinner"></div> Carregando notícias...';
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
    loadMoreBtn.textContent = "Carregar mais notícias (" + remaining + " restantes)";
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
    groupedLoadMoreBtn.textContent = "Carregar mais histórias (" + remaining + " restantes)";
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
          fullTextDiv.textContent = "Não foi possível carregar o texto completo.";
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

    const editTargetButton = event.target.closest("[data-target-edit]");
    if (editTargetButton) {
      if (targetActionsLocked()) {
        setMessage(manageTargetsMessage, "Aguarde a atualização terminar para mudar os nomes acompanhados.", "error");
        return;
      }
      editingTargetKey = editTargetButton.dataset.targetEdit || "";
      pendingArchiveKey = "";
      setMessage(manageTargetsMessage, "", "");
      renderManageTargets();
      return;
    }

    const cancelEditButton = event.target.closest("[data-target-edit-cancel]");
    if (cancelEditButton) {
      editingTargetKey = "";
      renderManageTargets();
      return;
    }

    const archiveStartButton = event.target.closest("[data-target-archive-start]");
    if (archiveStartButton) {
      if (targetActionsLocked()) {
        setMessage(manageTargetsMessage, "Aguarde a atualização terminar para mudar os nomes acompanhados.", "error");
        return;
      }
      pendingArchiveKey = archiveStartButton.dataset.targetArchiveStart || "";
      editingTargetKey = "";
      setMessage(manageTargetsMessage, "", "");
      renderManageTargets();
      return;
    }

    const archiveCancelButton = event.target.closest("[data-target-archive-cancel]");
    if (archiveCancelButton) {
      pendingArchiveKey = "";
      renderManageTargets();
      return;
    }

    const archiveConfirmButton = event.target.closest("[data-target-archive-confirm]");
    if (archiveConfirmButton) {
      if (targetActionsLocked()) {
        setMessage(manageTargetsMessage, "Aguarde a atualização terminar para mudar os nomes acompanhados.", "error");
        return;
      }
      archiveConfirmButton.disabled = true;
      archiveManagedTarget(archiveConfirmButton.dataset.targetArchiveConfirm || "");
      return;
    }

    const restoreButton = event.target.closest("[data-target-restore]");
    if (restoreButton) {
      if (targetActionsLocked()) {
        setMessage(manageTargetsMessage, "Aguarde a atualização terminar para mudar os nomes acompanhados.", "error");
        return;
      }
      restoreButton.disabled = true;
      restoreManagedTarget(restoreButton.dataset.targetRestore || "");
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
      var visibleTargets = (payload.targets || []).filter(isPublicTarget);
      var primaryTargets = visibleTargets.filter(function (t) { return t.primary; });
      (primaryTargets.length ? primaryTargets : visibleTargets).forEach(function (target) {
        selectedTargets.add(target.key);
      });
    }
    applyState();
  });

  if (updateRunForm) {
    attachDateMask(dateFromInput);
    attachDateMask(dateToInput);
    updateRunForm.addEventListener("submit", async function (event) {
      event.preventDefault();
      setMessage(runFormMessage, "Iniciando atualização...", "");
      var keys = selectedRunTargetKeys();
      if (!keys.length) {
        showFriendlyProblem("Selecione pelo menos um nome para acompanhar.");
        return;
      }
      var dateFromIso = brDateToIso(dateFromInput ? dateFromInput.value : "");
      var dateToIso = brDateToIso(dateToInput ? dateToInput.value : "");
      if (!dateFromIso || !dateToIso) {
        showFriendlyProblem("Preencha as datas no formato DD/MM/AAAA.");
        return;
      }
      if (dateFromIso > dateToIso) {
        showFriendlyProblem("Confira as datas: a inicial precisa vir antes da final.");
        return;
      }
      var body = {
        preset: "custom",
        target_keys: keys,
        date_from: dateFromIso,
        date_to: dateToIso,
        export: true,
      };
      if (runUpdateButton) runUpdateButton.disabled = true;
      try {
        var resp = await apiPost("/api/update/start", body);
        var data = await resp.json().catch(function () { return {}; });
        if (!resp.ok) throw new Error(apiErrorMessage(data, resp.status));
        setMessage(runFormMessage, "Atualização iniciada. O progresso aparece na aba compartilhada.", "ok");
        activateRunTab("progress");
        await pollStatus();
      } catch (error) {
        showFriendlyProblem(friendlyError(error, "Não foi possível iniciar a atualização."));
      } finally {
        if (runUpdateButton) {
          var status = latestStatus && latestStatus.current ? latestStatus.current.status : "";
          runUpdateButton.disabled = activeStatus(status);
        }
      }
    });
  }

  async function cancelActiveUpdate() {
    setMessage(progressActionMessage || runFormMessage, "Parando atualização...", "");
    [cancelUpdateButton, cancelUpdateButtonProgress].forEach(function (button) {
      if (button) button.disabled = true;
    });
    try {
      var resp = await apiPost("/api/update/cancel", {});
      var data = await resp.json().catch(function () { return {}; });
      if (!resp.ok) throw new Error(apiErrorMessage(data, resp.status));
      var nextCurrent = Object.assign({}, latestStatus && latestStatus.current ? latestStatus.current : {}, data);
      var stillActive = activeStatus(nextCurrent.status);
      setMessage(
        progressActionMessage || runFormMessage,
        stillActive ? "Cancelamento solicitado. Aguarde a atualização encerrar com segurança." : "Atualização parada. Você já pode iniciar outra rodada.",
        "ok"
      );
      latestStatus = { current: nextCurrent };
      renderStatus(latestStatus);
      if (runUpdateButton) runUpdateButton.disabled = stillActive;
      await pollStatus();
    } catch (error) {
      setMessage(progressActionMessage || runFormMessage, friendlyError(error, "Não foi possível parar a atualização."), "error");
      [cancelUpdateButton, cancelUpdateButtonProgress].forEach(function (button) {
        if (button) button.disabled = false;
      });
    }
  }

  [cancelUpdateButton, cancelUpdateButtonProgress].forEach(function (button) {
    if (!button) return;
    button.addEventListener("click", cancelActiveUpdate);
  });

  async function resumeActiveUpdate() {
    if (!resumeUpdateButton) return;
    setMessage(progressActionMessage || runFormMessage, "Retomando atualização...", "");
    resumeUpdateButton.disabled = true;
    try {
      await apiPost("/api/update/resume", latestStatus && latestStatus.current && latestStatus.current.id ? { job_id: latestStatus.current.id } : {});
      setMessage(progressActionMessage || runFormMessage, "Atualização retomada. Acompanhe as fontes nesta aba.", "ok");
      await pollStatus();
    } catch (error) {
      setMessage(progressActionMessage || runFormMessage, friendlyError(error, "Não foi possível retomar a atualização."), "error");
      resumeUpdateButton.disabled = false;
    }
  }

  if (resumeUpdateButton) resumeUpdateButton.addEventListener("click", resumeActiveUpdate);

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
        if (!resp.ok) throw new Error(apiErrorMessage(data, resp.status));
        setMessage(addTargetMessage, targetMutationMessage("Nome extra salvo. Ele já vale para a Base atual e para próximas rodadas.", data), "ok");
        addTargetForm.reset();
        await refreshTargets();
        if (data && data.key) {
          selectedTargets.add(data.key);
          ensureSelectedTargets();
          if (payload) applyState();
        }
        await pollBaseLiveResults();
        if (manageTargetsBox && manageTargetsBox.open) await refreshManageTargets();
      } catch (error) {
        setMessage(addTargetMessage, friendlyError(error, "Não foi possível salvar este nome."), "error");
      } finally {
        if (submit) submit.disabled = false;
      }
    });
  }

  app.addEventListener("submit", async function (event) {
    const targetForm = event.target.closest(".manage-target-form");
    if (!targetForm) return;
    event.preventDefault();
    if (targetActionsLocked()) {
      setMessage(manageTargetsMessage, "Aguarde a atualização terminar para mudar os nomes acompanhados.", "error");
      return;
    }
    var key = targetForm.dataset.manageTargetKey || "";
    var submit = targetForm.querySelector('button[type="submit"]');
    if (submit) submit.disabled = true;
    setMessage(manageTargetsMessage, "Salvando alterações...", "");
    var form = new FormData(targetForm);
    var body = {
      display_name: form.get("display_name"),
      keywords: splitList(form.get("keywords")),
      exact_aliases: splitList(form.get("exact_aliases")),
    };
    try {
      var resp = await apiPatch("/api/targets/" + encodeURIComponent(key), body);
      var data = await resp.json().catch(function () { return {}; });
      if (!resp.ok) throw new Error(apiErrorMessage(data, resp.status));
      editingTargetKey = "";
      pendingArchiveKey = "";
      setMessage(manageTargetsMessage, targetMutationMessage("Nome extra atualizado.", data), "ok");
      await reloadTargetsAfterManagement(data.key || key, { select: true });
    } catch (error) {
      setMessage(manageTargetsMessage, friendlyError(error, "Não foi possível atualizar este nome."), "error");
      if (submit) submit.disabled = false;
    }
  });

  app.addEventListener(
    "toggle",
    function (event) {
      if (event.target === manageTargetsBox && manageTargetsBox.open) {
        refreshManageTargets();
      }
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
      if (!resp.ok) throw new Error(apiErrorMessage(data, resp.status));
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


  if (apiAvailable) {
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
  }

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
      normalizePayloadCounts();
      document.title = (payload.meta && payload.meta.pageTitle) || document.title;
      (payload.targets || []).forEach(function (target) {
        labelsByKey[target.key] = target.label || target.key;
      });
      applyViewerControls();
      var visibleKeys = (payload.targets || []).filter(isPublicTarget).map(function (target) { return target.key; });
      selectedTargets = new Set((payload.defaultTargets || []).filter(function (key) {
        return visibleKeys.indexOf(key) !== -1;
      }));
      if (!selectedTargets.size) {
        (payload.targets || []).filter(isPublicTarget).forEach(function (target) {
          selectedTargets.add(target.key);
        });
      }
      if (loadingState) {
        loadingState.hidden = true;
      }
      applyState();
      if (apiAvailable) {
        refreshTargets();
        if (viewerIsAdmin()) pollStatus();
        pollBaseLiveResults();
        if (viewerIsAdmin()) window.setInterval(pollStatus, 5000);
        window.setInterval(pollBaseLiveResults, 5000);
      } else {
        renderStaticBundleStatus();
      }
    })
    .catch(function (error) {
      showError(error && error.message ? error.message : "Erro inesperado.");
    });
})();
