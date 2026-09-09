"""Confirmed namesakes/credits must not remove separate politician mentions."""
from dataclasses import asdict
import json
from pathlib import Path

import pytest

from pipeline.matcher import CitationMatcher,Target,target_metadata


def target(key):
    rows=json.loads((Path(__file__).resolve().parents[1]/'data/targets.json').read_text())
    row=next(row for row in rows if row['key']==key)
    return Target(key=row['key'],display_name=row['display_name'],keywords=row['keywords'],exact_aliases=row['exact_aliases'],**target_metadata(row))


def keys(text,*targets):return {hit.target_key for hit in CitationMatcher(targets,exact_names_only=True).find_hits(text)}


@pytest.mark.parametrize('text',[
    'Outros dois policiais militares, Hugo Leal de Oliveira Reis e Victor Henrique de Jesus, também respondem pelo caso.',
    'Coronel Rubens Pierrotti Junior foi condenado pela Justiça Militar após publicar livro com denúncias sobre o ExércitoFoto: Hugo Leal/Divulgação Exército Brasileiro/ND Mais',
    'Rubens Pierrotti Junior afirma que vai recorrerFoto: Hugo Leal/Divulgação/ND Mais',
])
def test_hugo_real_police_and_glued_photo_credit_occurrences_are_excluded(text):
    assert not keys(text,target('hugo_leal'))


def test_pedro_paulo_malta_is_not_the_politician_despite_nearby_rio_context():
    text='Convidados: Alfredo Del-Penho e Pedro Paulo Malta (Mediação: João Carino)Descrição: Parte do livro Zezinho de Nervina e aborda a boemia clássica do Rio de Janeiro e a construção da malandragem através da música e do samba.'
    assert not keys(text,target('pedro_paulo'))


@pytest.mark.parametrize('key,homonym,genuine',[
    ('hugo_leal','O policial Hugo Leal de Oliveira Reis responde pelo caso.','O deputado Hugo Leal apresentou propostas para o Rio.'),
    ('hugo_leal','ExércitoFoto: Hugo Leal/Divulgação/ND Mais.','Hugo Leal Melo da Silva participou da reunião.'),
    ('pedro_paulo','Pedro Paulo Malta cantou no Rio.','O deputado federal Pedro Paulo apresentou a proposta.'),
    ('pedro_paulo','Pedro Paulo Malta cantou no Rio.','Pedro Paulo Carvalho Teixeira apresentou a proposta.'),
])
def test_same_article_keeps_separate_genuine_politician_occurrence_in_both_orders(key,homonym,genuine):
    person=target(key)
    assert keys(homonym+' '+genuine,person)=={key}
    assert keys(genuine+' '+homonym,person)=={key}


def test_occurrence_exclusion_precedes_even_an_explicit_alias_exemption():
    person=Target(key='hugo',display_name='Hugo Leal',keywords=['Hugo Leal'],
        match_context={'exempt_aliases':['Hugo Leal'],'excluded_phrases':['Hugo Leal de Oliveira Reis']})
    assert not keys('O policial Hugo Leal de Oliveira Reis foi citado.',person)
    assert keys('Hugo Leal de Oliveira Reis foi citado. O deputado Hugo Leal falou.',person)=={'hugo'}


def test_plain_hugo_mentions_keep_existing_permissive_rule_and_other_names_are_untouched():
    assert keys('Hugo Leal esteve no encontro.',target('hugo_leal'))=={'hugo_leal'}
    other=Target(key='other',display_name='Outro Nome',keywords=['Outro Nome'])
    assert keys('Pedro Paulo Malta e Outro Nome estiveram no Rio.',target('pedro_paulo'),other)=={'other'}


def test_excluded_phrases_metadata_roundtrip_preserves_existing_context_and_fields():
    row={'match_context':{'required_for':['Pedro Paulo'],'any_of':['Rio'],'none_of':['goleiro Pedro Paulo'],
                         'exempt_aliases':['Pedro Paulo Carvalho Teixeira'],'excluded_phrases':[' Pedro Paulo Malta ',''],
                         'window_chars':220}}
    normalized=target_metadata(row)
    assert normalized['match_context']['excluded_phrases']==['Pedro Paulo Malta']
    assert target_metadata(asdict(Target(key='person',**normalized)))['match_context']==normalized['match_context']
    assert normalized['match_context']['any_of']==['Rio'] and normalized['match_context']['none_of']==['goleiro Pedro Paulo']
    assert target_metadata({'match_context':{'excluded_phrases':'not-a-list'}})['match_context']['excluded_phrases']==[]
