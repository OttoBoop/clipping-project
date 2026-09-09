"""Exact migrated Diário DOM observed in live articles2278 and2319.

The public samples contain td-post-content.tagdiv-type, td-category and
ddr-author-box. Article2319 repeats its prose inside ordinary editorial nodes;
these tests deliberately forbid treating that as a removable print wrapper.
"""
import json

import pytest

from web_app.political_discovery import extract_article


PARAGRAPH = "Eduardo Paes apresentou propostas para os municípios durante o encontro. " * 5
LATER_SECTION = "Pedro Paulo explicou a próxima etapa do projeto e respondeu às perguntas da comunidade."


def page(body, *, host="www.diariodorio.com", structured_body=None):
    url = f"https://{host}/politica/2026/08/25/reportagem.html"
    structured = "" if structured_body is None else '<script type="application/ld+json">' + json.dumps({
        "@type": "NewsArticle", "url": url, "articleBody": structured_body}) + '</script>'
    return f'''<html><head><link rel="canonical" href="{url}">
        <meta property="og:title" content="Reportagem local">
        <meta property="article:published_time" content="2026-08-25T12:14:00Z">{structured}</head>
        <body><article><header><h1>Reportagem local</h1></header>
        <div class="td-post-sharing-top"><span>Compartilhar no Facebook</span></div>
        <div class="td-post-content tagdiv-type">{body}</div>
        <p>Texto da navegação exterior ao conteúdo editorial.</p></article></body></html>'''


@pytest.mark.parametrize("host", ["diariodorio.com", "www.diariodorio.com"])
def test_diario_selects_editorial_container_and_preserves_later_sections(host):
    markup = f'''<div class="td-post-featured-image"><figcaption>Legenda editorial preservada.</figcaption></div>
        <p class="isSelectedEnd">{PARAGRAPH}</p>
        <div class="td-a-rec td-a-rec-id-content_top">Publicidade com Flávio Valle.</div>
        <h3>Próxima etapa</h3><p class="texto">{LATER_SECTION}</p>
        <ul data-spread="false"><li>Primeira proposta</li><li>Segunda proposta</li></ul>
        <ul class="td-category"><li>Átila Nunes</li><li>Pesquisa eleitoral</li></ul>
        <div class="ddr-author-box"><div class="ddr-author-info">Quintino Gomes Freire</div>
        <div class="ddr-author-social">Redes do autor</div></div>'''
    result = extract_article(page(markup, host=host, structured_body=PARAGRAPH * 10 + " Átila Nunes"))
    assert result["extraction_state"] == "full_text"
    assert PARAGRAPH.strip() in result["full_text"] and LATER_SECTION in result["full_text"]
    assert "Próxima etapa" in result["full_text"] and "Segunda proposta" in result["full_text"]
    assert "Legenda editorial preservada." in result["full_text"]
    for pollution in ("Facebook", "Flávio Valle", "Átila Nunes", "Quintino", "Redes do autor", "navegação exterior"):
        assert pollution not in result["full_text"]
    assert result["published_at"] == "2026-08-25T12:14:00+00:00"


def test_diario_does_not_guess_that_repeated_editorial_paragraphs_are_print_wrappers():
    prose = "A frase editorial reaparece como repetição publicada pelo próprio veículo."
    markup = f"<div><p>{prose}</p></div><p>{prose}</p><p>{prose}</p><p>{LATER_SECTION}</p>"
    result = extract_article(page(markup))
    assert result["full_text"].count(prose) == 3
    assert LATER_SECTION in result["full_text"]


@pytest.mark.parametrize("body", ["<p>Conteúdo indisponível.</p>", ""])
def test_diario_short_or_empty_editorial_body_cannot_be_replaced_by_polluted_structured_text(body):
    markup = body + '<ul class="td-category"><li>Eduardo Paes</li></ul><div class="ddr-author-box">Autor</div>'
    result = extract_article(page(markup, structured_body=PARAGRAPH * 20))
    assert result["extraction_state"] == "metadata_only"
    assert result["full_text"] == ("Conteúdo indisponível." if body else "")


def test_diario_template_cleanup_is_not_applied_to_another_publisher():
    markup = f'<p>{PARAGRAPH}</p><div class="ddr-author-box">Conteúdo de outra estrutura.</div>'
    result = extract_article(page(markup, host="another-publisher.example"))
    assert "Conteúdo de outra estrutura." in result["full_text"]
