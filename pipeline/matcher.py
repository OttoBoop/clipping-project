    exact_aliases: list[str] | None = None
            exact_aliases = [str(item).strip() for item in (target.exact_aliases or []) if str(item).strip()]
            if self.exact_names_only:
                keyword_set = [target.display_name, *exact_aliases]
            else:
                keyword_set = [target.display_name, *exact_aliases, *target.keywords]
        </div>
      </div>
      <div class=\"story-meta\">
        <span>Primeira publicacao: {html.escape(first_pub)}</span>
        <span>Ultima publicacao: {html.escape(last_pub)}</span>
      <div class=\"story-summary\">
        <div class=\"summary-label\">{html.escape(summary_label)}</div>
        <p>{html.escape(story_summary)}</p>
      <div class=\"story-articles\">
        {''.join(article_cards)}
    </section>
    \"\"\"

def render_article_card(
    article: dict[str, Any],
    *,
    target_labels: dict[str, str],
    show_story_link: bool,
) -> str:
    label, preview_html, full_html = render_text_block(article)
    aid = int(article.get(\"article_id\") or 0)
    story_id = int(article.get(\"story_id\") or 0)
    title = html.escape(str(article.get(\"title\") or \"Sem titulo\"))
    url = str(article.get(\"url\") or \"\").strip()
    source = str(article.get(\"source_name\") or \"Fonte nao identificada\").strip()
    source_host = host_from_url(url)
    sentiment = SENTIMENT_LABEL.get(str(article.get(\"sentiment\") or \"neutral\"), \"Neutro\")
    story_link = (
        f'<a class=\"text-link\" href=\"#story-{story_id}\">Ir para a historia principal</a>'
        if show_story_link and story_id > 0
        else \"\"
    )
    full_toggle = \"\"
    if full_html:
        full_toggle = f\"\"\"
        <details class=\"raw-details\">
          <summary>Ver texto bruto completo</summary>
          <div class=\"body-text full\">{full_html}</div>
        </details>
        \"\"\"
    title_html = title
    if url:
        title_html = f'<a href=\"{html.escape(url)}\" target=\"_blank\" rel=\"noreferrer\">{title}</a>'
    return f\"\"\"
    <article class=\"article-card\" id=\"article-{aid}\">
      <div class=\"article-top\">
        <div>
          <h3>{title_html}</h3>
          <p class=\"article-meta\">
            <span>{html.escape(source)}</span>
            <span>{html.escape(fmt_dt(str(article.get(\"published_at\") or \"\")))}</span>
            <span>{html.escape(sentiment)}</span>
            <span>{html.escape(source_host or \"link externo\")}</span>
          </p>
        <div class=\"chips\">{target_badges(list(article.get(\"target_keys\") or []), target_labels)}</div>
      <div class=\"article-links\">
        {story_link}
        <a class=\"text-link\" href=\"{html.escape(url)}\" target=\"_blank\" rel=\"noreferrer\">Abrir materia original</a>
      <div class=\"summary-box {'summary-ai' if label == 'Resumo IA' else 'summary-raw'}\">
        <div class=\"summary-label\">{html.escape(label)}</div>
        <div class=\"body-text\">{preview_html}</div>
        {full_toggle}
    </article>
def build_html(
    date_from: str,
    date_to: str,
    filtered_stories: list[dict[str, Any]],
    ungrouped_articles: list[dict[str, Any]],
    all_articles: list[dict[str, Any]],
    article_map: dict[int, dict[str, Any]],
    generated_at = datetime.now(timezone.utc).strftime(\"%d/%m/%Y %H:%M UTC\")
    ai_count = sum(1 for article in all_articles if article.get(\"has_ai_summary\"))
    raw_count = len(all_articles) - ai_count
    grouped_count = len(all_articles) - len(ungrouped_articles)
    story_links = \"\".join(
        f\"\"\"
        <a class=\"story-link\" href=\"#story-{story_id_int(story.get('id'))}\">
          <strong>{html.escape(str(story.get('title') or 'Sem titulo'))}</strong>
          <span>{len(story.get('articles', []))} noticia(s)</span>
        </a>
        for story in filtered_stories
    story_sections = \"\".join(
        render_story_section(story, article_map=article_map, target_labels=target_labels)
        for story in filtered
\�������t`L8$�������p\H4 
�
�
�
�
�
�
�
l
X
D
0

������|hT@,������xdP<(
�
�
�
�
�
�
t
`
L
8
$
	�	�	�	�	�	�	�	p	\	H	4	 	���i�-W&q�q�i�-W]�q�q�i�-I�4q�q�i�-I�Hq�q�i�-J/Hq�q�i�-Z4tq�q�i�-Zj�q�q�i�-Z�q�q�i�-ƷLq�q�i�-���q�q�i�-� `q�q�i�-#��q�q�i�-$4�q�q�i�-$k�q�q�i�-�>$q�q�i�-�{�q�q�i�-���q�q�i�-���q�q�i�-�Lq�q�i�-��q�q�i�-�P�q�q�i�-É�q�q�i�-ù|q�q�i�-�dq�q�i�-�)tq�q�i�-�K�q�q�i�- V�\q�q�i�- W�q�q�i�- W?�q�q�i�-!#��q�q�i�-!#�Xq�q�i�-!#� q�q�i�-"���q�q�i�-"���q�q�i�-"��q�q�i�-"�=�q�q�i�-"�oxq�q�i�-"���q�q�i�-#oq�q�i�-#oWHq�q�i�-#o��q�q�i�-$���q�q�i�-$�90q�q�i�-$�sdq�q�i�-$�tLq�q�i�-$��8q�q�i�-$�q�q�i�-%yT�q�q�i�-%y��q�q�i�-%y�Hq�q�i�-&J0q�q�i�-&JUDq�q�i�-1�	hq�q�i�-1�Q�q�q�i�-1���q�q�i�-1�&Hq�q�i�-1�U�q�q�i�-1�z�q�q�i�-2��8q�q�i�-2�� q�q�i�-2�+lq�q�i�-3�e�q�q�i�-3֥�q�q�i�-3��4q�q�i�-3��q�q�i�-3�Q�q�q�i�-3��q�q�i�-4���q�q�i�-4��Xq�q�i�-4���q�q�i�-5�q�q�i�-5�	�q�q�i�-5�B<q�q�i�-5�k�q�q�i�-5ԉ0q�q�i�-5ԡ�q�q�i�-7%8q�q�i�-7%Uq�q�i�-7%�Xq�q�i�-7�{�q�q�i�-7��Xq�q�i�-7��Dq�q�i�-8vaq�q�i�-8v�q�q�i�-8v�dq�q�i�-8�j�q�q�i�-8��<q�q�i�-8��<q�q�i�-9�,hq�q�i�-9�a�q�q�i�-9���q�q�i�-:S�q�q�m!
            exact_aliases = [str(item).strip() for item in (target.exact_aliases or []) if }�str(item).strip()]