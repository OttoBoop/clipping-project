from pipeline.matcher import CitationMatcher, Target


def test_citation_matcher_is_accent_and_punctuation_insensitive():
    targets = [
        Target(
            key="seguranca_presente",
            display_name="Seguran\u00e7a Presente",
            keywords=["Seguran\u00e7a Presente"],
            primary=True,
        ),
        Target(
            key="percepcao_de_seguranca",
            display_name="percep\u00e7\u00e3o de seguran\u00e7a",
            keywords=["percep\u00e7\u00e3o de seguran\u00e7a"],
            primary=True,
        ),
    ]
    matcher = CitationMatcher(targets, exact_names_only=True)

    hits = matcher.find_hits("Seguranca-Presente amplia percepcao-de-seguranca no Centro")

    assert {hit.target_key for hit in hits} == {"seguranca_presente", "percepcao_de_seguranca"}
