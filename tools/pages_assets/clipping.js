(function () {
  const app = document.getElementById("app");
  if (!app) return;

  const dataUrl = app.dataset.clippingDataUrl;
  const rawUrl = app.dataset.clippingRawUrl;
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

  function renderTargetButtons() {
    targetFilters.innerHTML = (payload.targets || [])
      .map(function (target) {
        const active = selectedTargets.has(target.key) ? " active" : "";
        const primary = target.primary ? " primary" : "";
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
      })
      .join("");
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
      "</div>" +
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

  function buildGroupedView(stories) {
    flatStack.hidden = true;
    storyStack.hidden = false;
    indexPanel.hidden = false;
    flatStack.innerHTML = "";
    storyStack.innerHTML = stories.map(renderStoryCard).join("");
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
      (payload.targets || []).forEach(function (target) {
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
