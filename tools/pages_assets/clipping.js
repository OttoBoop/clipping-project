(function () {
  const app = document.getElementById("app");
  if (!app) return;

  const dataUrl = app.dataset.clippingDataUrl;
  const rawUrl = app.dataset.clippingRawUrl;
  const apiUrl = (app.dataset.clippingApiUrl || "").trim().replace(/\/$/, "");
  const editorEnabled = !!apiUrl;
  let categoriesCache = [];
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
  const LAZY_BATCH = 50;

  let payload = null;
  let selectedTargets = new Set();
  let currentSort = "newest";
  let flatSorted = [];
  let flatRendered = 0;
  let loadMoreBtn = null;
  let rawTextsCache = null;
  let rawTextsPromise = null;
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
    visibleStoriesStat.textContent = storyCount + " / " + payload.meta.totalStories;
    visibleArticlesStat.textContent = articleCount + " / " + payload.meta.totalArticles;
    visibleAiStat.textContent = aiCount + " / " + payload.meta.totalAi;
    visibleRawStat.textContent = rawCount + " / " + payload.meta.totalRaw;
    visibleIndexCount.textContent = String(storyCount);
    activeFilterText.textContent = activeLabel();
    emptyState.hidden = storyCount > 0;
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
    clsArr.forEach(function (cls) {
      var targetLabel = escapeHtml(labelsByKey[cls.target_key] || cls.target_key || "");
      if (cls.article_sentiment) {
        parts.push(
          '<span class="chip chip--cls chip--cls-' +
            cls.article_sentiment +
            '" title="Sentimento da notícia">Notícia: ' +
            escapeHtml(SENTIMENT_LABEL[cls.article_sentiment] || cls.article_sentiment) +
            "</span>"
        );
      }
      if (cls.target_sentiment) {
        parts.push(
          '<span class="chip chip--cls chip--cls-' +
            cls.target_sentiment +
            '" title="Sentimento sobre ' +
            targetLabel +
            '">' +
            targetLabel +
            ": " +
            escapeHtml(SENTIMENT_LABEL[cls.target_sentiment] || cls.target_sentiment) +
            "</span>"
        );
      }
      (cls.categories || []).forEach(function (cat) {
        parts.push('<span class="chip chip--cls chip--cls-cat">' + escapeHtml(cat) + "</span>");
      });
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

    var fieldsets = targetKeys.map(function (tk) {
      var tLabel = labelsByKey[tk] || tk;
      var cur = clsByTarget[tk] || {};
      var selectedCats = (cur.categories || []).slice();
      var allCats = categoriesCache.slice();
      selectedCats.forEach(function (c) {
        if (allCats.indexOf(c) === -1) allCats.push(c);
      });
      var chipsHtml = allCats
        .map(function (n) { return categoryChipHtml(n, selectedCats.indexOf(n) !== -1); })
        .join("");
      return (
        '<fieldset class="cls-fieldset" data-target-key="' +
        escapeHtml(tk) +
        '" data-article-id="' +
        escapeHtml(String(aid)) +
        '">' +
        "<legend>" + escapeHtml(tLabel) + "</legend>" +
        '<div class="cls-row">' +
        '<label class="cls-field">Sentimento da notícia ' +
        sentimentSelectHtml("article_sentiment", cur.article_sentiment) +
        "</label>" +
        '<label class="cls-field">Sentimento sobre ' + escapeHtml(tLabel) + " " +
        sentimentSelectHtml("target_sentiment", cur.target_sentiment) +
        "</label>" +
        "</div>" +
        '<div class="cls-row cls-cats-row">' +
        '<span class="cls-cat-label">Categorias:</span>' +
        '<div class="cls-cat-chips">' + chipsHtml + "</div>" +
        '<button type="button" class="cls-add-cat-btn">+ Nova</button>' +
        "</div>" +
        '<div class="cls-row cls-actions-row">' +
        '<button type="button" class="cls-save-btn">Salvar</button>' +
        '<span class="cls-save-status"></span>' +
        "</div>" +
        "</fieldset>"
      );
    }).join("");

    return (
      '<details class="cls-editor"><summary>Classificar este artigo</summary>' +
      fieldsets +
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
        "<summary>Ver texto bruto completo</summary>" +
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
      escapeHtml(article.summaryLabel || "Sem resumo") +
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
        if (!response.ok) throw new Error("Falha ao carregar texto bruto");
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
      fullTextDiv.textContent = "Carregando texto bruto...";
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
          fullTextDiv.textContent = "Nao foi possivel carregar o texto bruto.";
        }
        delete el.dataset.loading;
      });
  }

  app.addEventListener("click", function (event) {
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

  function gatherFieldset(fs) {
    var aid = parseInt(fs.dataset.articleId, 10);
    var tk = fs.dataset.targetKey;
    var artSent = fs.querySelector('[data-cls-field="article_sentiment"]').value || null;
    var tgtSent = fs.querySelector('[data-cls-field="target_sentiment"]').value || null;
    var cats = Array.from(fs.querySelectorAll(".cls-cat-chip.selected")).map(function (c) {
      return c.dataset.catName;
    });
    return {
      article_id: aid,
      target_key: tk,
      article_sentiment: artSent,
      target_sentiment: tgtSent,
      categories: cats,
    };
  }

  async function onSaveClassification(fs) {
    var btn = fs.querySelector(".cls-save-btn");
    var status = fs.querySelector(".cls-save-status");
    btn.disabled = true;
    status.textContent = "Salvando...";
    status.className = "cls-save-status";
    try {
      var resp = await fetch(apiUrl + "/api/classifications", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(gatherFieldset(fs)),
      });
      var data = await resp.json().catch(function () { return {}; });
      if (!resp.ok) throw new Error(data.error || "HTTP " + resp.status);
      status.textContent = "Salvo ✓";
      status.classList.add("cls-save-status--ok");
      applySavedClassification(data);
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

  async function onAddCategory(fs) {
    var name = window.prompt("Nome da nova categoria:");
    if (!name || !name.trim()) return;
    name = name.trim();
    try {
      var resp = await fetch(apiUrl + "/api/categories", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name: name }),
      });
      var data = await resp.json().catch(function () { return {}; });
      if (!resp.ok) throw new Error(data.error || "HTTP " + resp.status);
      var canonical = data.name || name;
      if (categoriesCache.indexOf(canonical) === -1) categoriesCache.push(canonical);
      document.querySelectorAll(".cls-fieldset").forEach(function (other) {
        var chips = other.querySelector(".cls-cat-chips");
        if (!chips) return;
        var existing = chips.querySelector('[data-cat-name="' + canonical.replace(/"/g, '\\"') + '"]');
        if (existing) {
          if (other === fs) existing.classList.add("selected");
          return;
        }
        chips.insertAdjacentHTML("beforeend", categoryChipHtml(canonical, other === fs));
      });
    } catch (e) {
      window.alert("Erro ao criar categoria: " + (e && e.message ? e.message : e));
    }
  }

  if (editorEnabled) {
    app.addEventListener("click", function (event) {
      var saveBtn = event.target.closest(".cls-save-btn");
      if (saveBtn) {
        event.preventDefault();
        var fs = saveBtn.closest(".cls-fieldset");
        if (fs) onSaveClassification(fs);
        return;
      }
      var addBtn = event.target.closest(".cls-add-cat-btn");
      if (addBtn) {
        event.preventDefault();
        var fs2 = addBtn.closest(".cls-fieldset");
        if (fs2) onAddCategory(fs2);
        return;
      }
      var chip = event.target.closest(".cls-cat-chip");
      if (chip) {
        event.preventDefault();
        chip.classList.toggle("selected");
        return;
      }
    });

    fetch(apiUrl + "/api/categories", { cache: "no-store" })
      .then(function (r) { return r.ok ? r.json() : { categories: [] }; })
      .then(function (data) {
        categoriesCache = (data.categories || []).map(function (c) { return c.name; });
      })
      .catch(function () { /* leave categoriesCache empty */ });
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
    })
    .catch(function (error) {
      showError(error && error.message ? error.message : "Erro inesperado.");
    });
})();
