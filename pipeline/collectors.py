                            if not _within_window(item.published_at, date_from=date_from, date_to=date_to):
                                continue
                metadata = dict(item.metadata or {})
                metadata.setdefault(\"query\", query)
                metadata.updatX�(hits)
        searchable = \"\" if exact_body_only else \" \".join([candidate.title or \"\", candidate.snippet or \"\"])
        hits = [] if exact_body_only else matcher.find_hits(searchable)
        hits_from_preview = bool(hits)
        must_fetch_article = bool(force_full_fetch or exact_body_only or not hits or needs_published_extraction)

        if must_fetch_article:
                if exact_body_only:
                    hits = matcher.find_hits(full_text)
                elif not hits:
        if (force_full_fetch or exact_body_only) and not str(full_text or \"\").strip():
            emit_candidate(
                candidate=candidate,
                status=\"skipped\",
                reason=\"missing_body\",
                final_url=final_url,
                hits_for_candidate=[],
                title_value=clean_title(candidate.title or extracted_title or \"\"),
                published_value=published_at,
                stage=\"body_fetch\",
            )
            continue
        if needs_published_extraction and not published_at:
                reason=\"no_exact_body_match\" if exact_body_only else \"no_match_exact_name\",
    targets = select_targets(get_active_targets(), options.target_keys)
    if collector == \"all\" and not options.custom_query.strip():
        target_keys = {str(target.key) for target in targets}
        if \"flavio_valle\" in target_keys:
            planned_urls = {candidate.url for _, _, batch in plans for candidate in batch if candidate.url}
   X�yEaimM_EphALMR8GzbhwLJ2l5F9bsL6hU-9Mow8VHamCi-Ic5rEgSnt1u5HxqtifOfnbBaZFiH3VY6MRlRxDIjxFlyT1YLE5n29ZFQAgeE0tRQ2GzgHUEhcDhCguqK_h6O_fDamoQ4eevSDwXm2t3PM_i_eVRqHztxkfhPiQhTNjIA8LKwRdSaRDTNCu0RnUFdfUUYIhmdCZOQz2zTuFl2bITtZ5eRsmG-V1w4yLP8t-yMjh2Ksg9gOMAlol2NDyNo3VLaAcdpN4JhX28SU7HjvES9"},{"type":"custom_tool_call","status":"completed","call_id":"call_fChXHmU9cVtTR4or8dF4IEp2",
                metadata.updat[�e(
                    {
                        \"force_full_fetch\": True,
                        \"exact_body_only\": True,
                        \"require_published_extraction\": not bool(item.published_at),
                    }
                )
                item.metadata = metadata
                metadata.update(
                metadata.updat]o(hits)
   ]pyEaimM_EphALMR8GzbhwLJ2l5F9bsL6hU-9Mow8VHamCi-Ic5rEgSnt1u5HxqtifOfnbBaZFiH3VY6MRlRxDIjxFlyT1YLE5n29ZFQAgeE0tRQ2GzgHUEhcDhCguqK_h6O_fDamoQ4eevSDwXm2t3PM_i_eVRqHztxkfhPiQhTNjIA8LKwRdSaRDTNCu0RnUFdfUUYIhmdCZOQz2zTuFl2bITtZ5eRsmG-V1w4yLP8t-yMjh2Ksg9gOMAlol2NDyNo3VLaAcdpN4JhX28SU7HjvES9"},{"type":"custom_tool_call","status":"completed","call_id":"call_fChXHmU9cVtTR4or8dF4IEp2",
                metadata.updat`�(hits)
   `�yEaimM_EphALMR8GzbhwLJ2l5F9bsL6hU-9Mow8VHamCi-Ic5rEgSnt1u5HxqtifOfnbBaZFiH3VY6MRlRxDIjxFlyT1YLE5n29ZFQAgeE0tRQ2GzgHUEhcDhCguqK_h6O_fDamoQ4eevSDwXm2t3PM_i_eVRqHztxkfhPiQhTNjIA8LKwRdSaRDTNCu0RnUFdfUUYIhmdCZOQz2zTuFl2bITtZ5eRsmG-V1w4yLP8t-yMjh2Ksg9gOMAlol2NDyNo3VLaAcdpN4JhX28SU7HjvES9"},{"type":"custom_tool_call","status":"completed","call_id":"call_fChXHmU9cVtTR4or8dF4IEp2",
                metadata.updat
�%�b
�
LI�
�	�	)i��i�X��3ԣ]�c]gei�(�$G�TRACEcodex_api::endpoint::responses_websocketwebsocket event: {"type":"response.output_text.delta","content_index":0,"delta":" and","item_id":"msg_0ab33425aef0f08a0169b528b988f08191934f74e8450213a2","logprobs":[],"obfuscation":"XgHQjcGXnHGy","output_index":1,"sequence_number":25}codex_api::endpoint::responses_websocketcodex-api\src\endpoint\responses_websocket.rs4pid:668:144eaa79-eb9c-4706-a491-074439ab28f0m�'ԣ
MMKei�(�$G��INFOcodex_otel::traces::otel_managercodex_otel::traces::otel_managerotel\src\traces\otel_manager.rsDpid:668:144eaa79-eb9c-4706-a491-074439ab28f0c�4ԣ]�e]gei�(�$Gm@TRACEcodex_api::endpoint::responses_websocketwebsocket event: {"type":"response.output_text.delta","content_index":0,"delta":"\"`","item_id":"msg_0ab33425aef0f08a0169b528b988f08191934f74e8450213a2","logprobs":[],"obfuscation":"LlHbDBtsZtnJYY","output_index":1,"sequence_number":24}codex_api::endpoint::responses_websocketcodex-api\src\endpoint\responses_websocket.rs4pid:668:144eaa79-eb9c-4706-a491-074439ab28f0n�'ԣ
MMKei�(�$G]<INFOcodex_otel::traces::otel_managercodex_otel::traces::otel_managerotel\src\traces\otel_manager.rsDpid:668:144eaa79-eb9c-4706-a491-074439ab28f0cTԣ
!ei�(�$F��TRACElogWouldBlockpid:668:144eaa79-eb9c-4706-a491-074439ab28f0�Vԣ�!ei�(�$F��TRACElogC:\Users\runneradmin\.cargo\git\checkouts\tokio-tungstenite-ea4445d9acecae62\132f5b3\src\compat.rs:157 Read.with_context read -> poll_readpid:668:144eaa79-eb9c-4706-a491-074439ab28f0��Hԣ�ei�(�$F�LTRACElogC:\Users\runneradmin\.cargo\git\checkouts\tokio-tungstenite-ea4445d9acecae62\132f5b3\src\compat.rs:131 AllowStd.with_contextpid:668:144eaa79-eb9c-4706-a491-074439ab28f0��;ԣ�mei�(�$F�PTRACElogC:\Users\runneradmin\.cargo\git\checkouts\tokio-tungstenite-ea4445d9acecae62\132f5b3\src\compat.rs:154 Read.readpid:668:144eaa79-eb9c-4706-a491-074439ab28f0x�WԢ�#ei�(�$Fu4TRACElogC:\Users\runneradmin\.cargo\git\checkouts\tokio-tungstenite-ea4445d9acecae62\132f5b3\src\lib.rs:304 Stream.with_context poll_next -> read()pid:668:144eaa79-eb9c-4706-a491-074439ab28f0��LԢ~�
ei�(�$Fl�TRACElogC:\Users\runneradmin\.cargo\git\checkouts\tokio-tungstenite-ea4445d9acecae62\132f5b3\src\lib.rs:245 WebSocketStream.with_contextpid:668:144eaa79-eb9c-4706-a491-074439ab28f0��?Ԣ}�uei�(�$Fc<TRACElogC:\Users\runneradmin\.cargo\git\checkouts\tokio-tungstenite-ea4445d9acecae62\132f5b3\src\lib.rs:294 Stream.poll_nextpid:668:144eaa79-eb9c-4706-a491-074439ab28f0|�7Ԣ|�cei�(�$FY�TRACElogReceived message {"type":"response.output_text.delta","content_index":0,"delta":" pulling","item_id":"msg_0ab33425aef0f08a0169b528b988f08191934f74e8450213a2","logprobs":[],"obfuscation":"GVpt6urN","output_index":1,"sequence_number":33}pid:668:144eaa79-eb9c-4706-a491-074439ab28f0�oԢ{
Wei�(�$FF�TRACElogdecompressing 24 bytes in final framepid:668:144eaa79-eb9c-4706-a491-074439ab28f0-�~Ԣz�qei�(�$F=�TRACElogreceived frame 
<FRAME>
final: true
reserved: true false false
opcode: TEXT
length: 26
payload length: 24
payload: 0xa238d640fb84e8d28f710f2b28312b2df223ce67c6b50000
            pid:668:144eaa79-eb9c-4706-a491-074439ab28f0�WԢy
'ei�(�$F'xTRACElogMasked: falsepid:668:144eaa79-eb9c-4706-a491-074439ab28f0\Ԣx
1ei�(�$F �TRACElogOpcode: Data(Text)pid:668:144eaa79-eb9c-4706-a491-074439ab28f0WԢw
'ei�(�$F�TRACElogSecond: 11000pid:668:144eaa79-eb9c-4706-a491-074439ab28f0YԢv
+ei�(�$F(TRACElogFirst: 11000001pid:668:144eaa79-eb9c-4706-a491-074439ab28f0bԢu
=ei�(�$F�TRACElogParsed headers [193, 24]pid:668:144eaa79-eb9c-4706-a491-074439ab28f0 �VԢt�!ei�(�$FTRACElogC:\Users\runneradmin\.cargo\git\checkouts\tokio-tungstenite-ea4445d9acecae62\132f5b3\src\compat.rs:157 Read.with_context read -> poll_readpid:668:144eaa79-eb9c-4706-a491-074439ab28f0�
b�~=��z9
�
�
v
5��r1��n-
�
�
j
)	�	�	f	%��b@epid:668:144eaa79-eb9c-4706-a491-074439ab28f0i�-7j4p
p
@epid:668:144eaa79-eb9c-4706-a491-074439ab28f0i�-7�Hpp@epid:668:144eaa79-eb9c-4706-a491-074439ab28f0i�-e�pp@epid:668:144eaa79-eb9c-4706-a491-074439ab28f0i�-f�p
p
@epid:668:144eaa79-eb9c-4706-a491-074439ab28f0i�-pHhpp@epid:668:144eaa79-eb9c-4706-a491-074439ab28f0i�-p�pp@epid:668:144eaa79-eb9c-4706-a491-074439ab28f0i�-q�pp@epid:668:144eaa79-eb9c-4706-a491-074439ab28f0i�-rv8pp@epid:668:144eaa79-eb9c-4706-a491-074439ab28f0i�-r�`pp@epid:668:144eaa79-eb9c-4706-a491-074439ab28f0i�-s_�pp@epid:668:144eaa79-eb9c-4706-a491-074439ab28f0i�-t88pp@epid:668:144eaa79-eb9c-4706-a491-074439ab28f0i�-t�tpp@epid:668:144eaa79-eb9c-4706-a491-074439ab28f0i�-v�lpp@epid:668:144eaa79-eb9c-4706-a491-074439ab28f0i�-w?8pp@epid:668:144eaa79-eb9c-4706-a491-074439ab28f0i�-w�pp@epid:668:144eaa79-eb9c-4706-a491-074439ab28f0i�-xJ�pp@epid:668:144eaa79-eb9c-4706-a491-074439ab28f0i�-~��pp@epid:668:144eaa79-eb9c-4706-a491-074439ab28f0i�-\�pp@epid:668:144eaa79-eb9c-4706-a491-074439ab28f0i�-��pp@epid:668:144eaa79-eb9c-4706-a491-074439ab28f0i�-�X�pp@epid:668:144eaa79-eb9c-4706-a491-074439ab28f0i�-��Lpp@epid:668:144eaa79-eb9c-4706-a491-074439ab28f0i�-�'Dpp@epid:668:144eaa79-eb9c-4706-a491-074439ab28f0i�-���p p @epid:668:144eaa79-eb9c-4706-a491-074439ab28f0i�-��4p!p!@epid:668:144eaa79-eb9c-4706-a491-074439ab28f0i�-�` p"p"@epid:668:144eaa79-eb9c-4706-a491-074439ab28f0i�-�,p#p#@epid:668:144eaa79-eb9c-4706-a491-074439ab28f0i�-���p$p$@epid:668:144eaa79-eb9c-4706-a491-074439ab28f0i�-��Pp%p%@epid:668:144eaa79-eb9c-4706-a491-074439ab28f0i�-��pp&p&@epid:668:144eaa79-eb9c-4706-a491-074439ab28f0i�-�p'p'h�(hits)
   
�
�
�
�
�������'��6
MMKei�-�ŐINFOcodex_otel::traces::otel_managercodex_otel::traces::otel_managerotel\src\traces\otel_manager.rs�pid:668:144eaa79-eb9c-4706-a491-074439ab28f0c�[��5?�
?Iei�-��<TRACEcodex_api::sse::responsesunhandled responses event: response.custom_tool_call_input.deltacodex_api::sse::responsescodex-api\src\sse\responses.rsYpid:668:144eaa79-eb9c-4706-a491-074439ab28f0��l��4?�/?Iei�-�^�TRACEcodex_api::sse::responsesSSE event: {"type":"response.custom_tool_call_input.delta","delta":"_pref","item_id":"ctc_07668849256373ac0169b52cfb77988191b284020f489e6aa6","obfuscation":"uxZceVomjE3","output_index":1,"sequence_number":624}codex_api::sse::responsescodex-api\src\sse\responses.rs�pid:668:144eaa79-eb9c-4706-a491-074439ab28f0&�'��3
MMKei�-�*<INFOcodex_otel::traces::otel_managercodex_otel::traces::otel_managerotel\src\traces\otel_manager.rs�pid:668:144eaa79-eb9c-4706-a491-074439ab28f0c�[��2?�
?Iei�-�TRACEcodex_api::sse::responsesunhandled responses event: response.custom_tool_call_input.deltacodex_api::sse::responsescodex-api\src\sse\responses.rsYpid:668:144eaa79-eb9c-4706-a491-074439ab28f0��l��1?�/?Iei�-��0TRACEcodex_api::sse::responsesSSE event: {"type":"response.custom_tool_call_input.delta","delta":"query","item_id":"ctc_07668849256373ac0169b52cfb77988191b284020f489e6aa6","obfuscation":"Gs6eytByjRF","output_index":1,"sequence_number":623}codex_api::sse::responsescodex-api\src\sse\responses.rs�pid:668:144eaa79-eb9c-4706-a491-074439ab28f0&�'��0
MMKei�-ɟ�INFOcodex_otel::traces::otel_managercodex_otel::traces::otel_managerotel\src\traces\otel_manager.rs�pid:668:144eaa79-eb9c-4706-a491-074439ab28f0c�[��/?�
?Iei�-�0TRACEcodex_api::sse::responsesunhandled responses event: response.custom_tool_call_input.deltacodex_api::sse::responsescodex-api\src\sse\responses.rsYpid:668:144eaa79-eb9c-4706-a491-074439ab28f0��m��.?�1?Iei�-�z�TRACEcodex_api::sse::responsesSSE event: {"type":"response.custom_tool_call_input.delta","delta":"[\"","item_id":"ctc_07668849256373ac0169b52cfb77988191b284020f489e6aa6","obfuscation":"BJweMBQE5esLGR","output_index":1,"sequence_number":622}codex_api::sse::responsescodex-api\src\sse\responses.rs�pid:668:144eaa79-eb9c-4706-a491-074439ab28f0'�'��-
MMKei�-�B�INFOcodex_otel::traces::otel_managercodex_otel::traces::otel_managerotel\src\traces\otel_manager.rs�pid:668:144eaa79-eb9c-4706-a491-074439ab28f0c�[��,?�
?Iei�-$ETRACEcodex_api::sse::responsesunhandled responses event: response.custom_tool_call_input.deltacodex_api::sse::responsescodex-api\src\sse\responses.rsYpid:668:144eaa79-eb9c-4706-a491-074439ab28f0��l��+?�/?Iei�-#��TRACEcodex_api::sse::responsesSSE event: {"type":"response.custom_tool_call_input.delta","delta":"metadata","item_id":"ctc_07668849256373ac0169b52cfb77988191b284020f489e6aa6","obfuscation":"EwNx3yDb","output_index":1,"sequence_number":621}codex_api::sse::responsescodex-api\src\sse\responses.rs�pid:668:144eaa79-eb9c-4706-a491-074439ab28f0&�'��*
MMKei�-#�(INFOcodex_otel::traces::otel_managercodex_otel::traces::otel_managerotel\src\traces\otel_manager.rs�pid:668:144eaa79-eb9c-4706-a491-074439ab28f0c�[��)?�
?Iei�-
o��TRACEcodex_api::sse::responsesunhandled responses event: response.custom_tool_call_input.deltacodex_api::sse::responsescodex-api\src\sse\responses.rsYpid:668:144eaa79-eb9c-4706-a491-074439ab28f0��l��(?�/?Iei�-
oU�TRACEcodex_api::sse::responsesSSE event: {"type":"response.custom_tool_call_input.delta","delta":"].","item_id":"ctc_07668849256373ac0169b52cfb77988191b284020f489e6aa6","obfuscation":"EoDWuFY90TAoYk","output_index":1,"sequence_number":620}codex_api::sse::responsescodex-api\src\sse\responses.rs�pid:668:144eaa79-eb9c-4706-a491-074439ab28f0&
b�~=��z9
�
�
v
5��r1��n-
�
�
j
)	�	�	f	%��b@epid:668:144eaa79-eb9c-4706-a491-074439ab28f0i�)96��/�/�@epid:668:144eaa79-eb9c-4706-a491-074439ab28f0i�)96��@/�/�@epid:668:144eaa79-eb9c-4706-a491-074439ab28f0i�)96��/�/�@epid:668:144eaa79-eb9c-4706-a491-074439ab28f0i�)96�	�/�/�@epid:668:144eaa79-eb9c-4706-a491-074439ab28f0i�)96�N�/�/�@epid:668:144eaa79-eb9c-4706-a491-074439ab28f0i�)96�V/�/�@epid:668:144eaa79-eb9c-4706-a491-074439ab28f0i�)96�\�/�/�@epid:668:144eaa79-eb9c-4706-a491-074439ab28f0i�)96�fh/�/�@epid:668:144eaa79-eb9c-4706-a491-074439ab28f0i�)96�l�/�/�@epid:668:144eaa79-eb9c-4706-a491-074439ab28f0i�)96���/�/�@epid:668:144eaa79-eb9c-4706-a491-074439ab28f0i�)96��$/�/�@epid:668:144eaa79-eb9c-4706-a491-074439ab28f0i�)96��/�/�@epid:668:144eaa79-eb9c-4706-a491-074439ab28f0i�)96���/�/�@epid:668:144eaa79-eb9c-4706-a491-074439ab28f0i�)96�ռ/�/�@epid:668:144eaa79-eb9c-4706-a491-074439ab28f0i�)96���/�/�@epid:668:144eaa79-eb9c-4706-a491-074439ab28f0i�)96���/�/�@epid:668:144eaa79-eb9c-4706-a491-074439ab28f0i�)96��L/�/�@epid:668:144eaa79-eb9c-4706-a491-074439ab28f0i�)96��/�/�@epid:668:144eaa79-eb9c-4706-a491-074439ab28f0i�)96�
�/�/�@epid:668:144eaa79-eb9c-4706-a491-074439ab28f0i�)96��D/�/�@epid:668:144eaa79-eb9c-4706-a491-074439ab28f0i�)96���/�/�@epid:668:144eaa79-eb9c-4706-a491-074439ab28f0i�)96��/�/�@epid:668:144eaa79-eb9c-4706-a491-074439ab28f0i�)96�~�/�/�@epid:668:144eaa79-eb9c-4706-a491-074439ab28f0i�)96�A(/�/�@epid:668:144eaa79-eb9c-4706-a491-074439ab28f0i�)96�[T/�/�@epid:668:144eaa79-eb9c-4706-a491-074439ab28f0i�)96�nx/�/�@epid:668:144eaa79-eb9c-4706-a491-074439ab28f0i�)96���/�/�@epid:668:144eaa79-eb9c-4706-a491-074439ab28f0i�)96���/�/�@epid:668:144eaa79-eb9c-4706-a491-074439ab28f0i�)96��t/�/�@epid:668:144eaa79-eb9c-4706-a491-074439ab28f0i�)96���/�/�h�yEaimM_EphALMR8GzbhwLJ2l5F9bsL6hU-9Mow8VHamCi-Ic5rEgSnt1u5HxqtifOfnbBaZFiH3VY6MRlRxDIjxFlyT1YLE5n29ZFQAgeE0tRQ2GzgHUEhcDhCguqK_h6O_fDamoQ4eevSDwXm2t3PM_i_eVRqHztxkfhPiQhTNjIA8LKwRdSaRDTNCu0RnUFdfUUYIhmdCZOQz2zTuFl2bITtZ5eRsmG-V1w4yLP8t-yMjh2Ksg9gOMAlol2NDyNo3VLaAcdpN4JhX28SU7HjvES9"},{"type":"custom_tool_call","status":"completed","call_id":"call_fChXHmU9cVtTR4or8dF4IEp2",
                metadata.updatp�(hits)
   p�yEaimM_EphALMR8GzbhwLJ2l5F9bsL6hU-9Mow8VHamCi-Ic5rEgSnt1u5HxqtifOfnbBaZFiH3VY6MRlRxDIjxFlyT1YLE5n29ZFQAgeE0tRQ2GzgHUEhcDhCguqK_h6O_fDamoQ4eevSDwXm2t3PM_i_eVRqHztxkfhPiQhTNjIA8LKwRdSaRDTNCu0RnUFdfUUYIhmdCZOQz2zTuFl2bITtZ5eRsmG-V1w4yLP8t-yMjh2Ksg9gOMAlol2NDyNo3VLaAcdpN4JhX28SU7HjvES9"},{"type":"custom_tool_call","status":"completed","call_id":"call_fChXHmU9cVtTR4or8dF4IEp2",
    EXTRA_SITE_SOURCE,
def collect_extra_site(
    *,
    source: dict[str, object] | None = None,
    date_from: str = \"\",
    date_to: str = \"\",
    limit_total: int = 240,
    request_timeout: int = 10,
) -> list[CandidateArticle]:
    source_cfg = source or EXTRA_SITE_SOURCE
    source_name = str(source_cfg.get(\"source_name\") or \"Extra Site\").strip() or \"Extra Site\"
    host = str(source_cfg.get(\"host\") or \"extra.globo.com\").strip() or \"extra.globo.com\"
    sitemap_template = str(source_cfg.get(\"sitemap_url_template\") or \"\").strip()
    collected: list[CandidateArticle] = []
    seen_urls: set[str] = set()
    for day in _iter_window_days(date_from, date_to, default_days=7):
        if len(collected) >= max(1, limit_total):
            break
        sitemap_url = sitemap_template.format(
            yyyy=day.strftime(\"%Y\"),
            mm=day.strftime(\"%m\"),
            dd=day.strftime(\"%d\"),
        )
        try:
            _, xml_text = fetch_url(sitemap_url, timeout=request_timeout)
        except Exception:
        for row in _parse_sitemap_entries(xml_text):
            if len(collected) >= max(1, limit_total):
                break
            canon_url = canonicalize_url(str(row.get(\"loc\") or \"\").strip())
            if not canon_url or canon_url in seen_urls:
                continue
            if not is_likely_article_url(canon_url, expected_host_fragment=host):
            published_at = str(row.get(\"published_at\") or \"\").strip() or day.replace(
                hour=12,
                minute=0,
                second=0,
                microsecond=0,
                tzinfo=timezone.utc,
            ).isoformat()
            if not _within_window(published_at, date_from=date_from, date_to=date_to):
            seen_urls.add(canon_url)
            collected.append(
                _build_specialized_candidate(
                    title=str(row.get(\"title\") or \"\"),
                    url=canon_url,
                    source_name=source_name,
                    source_type=\"extra_site\",
                    published_at=published_at,
                    metadata={
                        \"extra_source\": \"daily_sitemap\",
                        \"sitemap_url\": sitemap_url,
                        \"site_collector\": \"extra_site\",
                        \"query_prefilter_applied\": False,
                    },
    return _dedupe_candidates_by_url(collected)
            seen_urls.add(canon_& um consegue até agora. O sucesso é medido por metricas iniividuais, com cada fonte tendo seu criterio para sucesso baseado em acharmos todas as noticias relevantes sobrre o flavio valle presentes no excel \"testing set\" naquele periodo. Se progredirmos por todo o periodo inicial, movemos para o preiodo do ano passado todo
        �yAmYUGGprc1JbNBB_Vmcf69vHZOCi-g96exYdjwte7jYpYCKxQ8ON6isqg1w6fF1qHhxAnjQ4kLQqpMW1KqcJHBra8TI726Z-uguuTXEuE1F9g5inOpgZ5iPmlOiTfjiAdERk0mLoI6sZv7E3JE3HvqbBN5AIOsWvY9icNDVM_WK-U1-MX5_eDv2IQ0-c5T0-_-rVAyPqws7f6s4uAx9eThoJR77dgmnyik8pynSnpUk1Ezpf6m1GPw2dE7zg-N0l3BzDVmVeNbL4MecTWsR9vayKiik_v40vOVoaTJcMvyb4kUnz9lOlhLIj-fPkzAvim3Y9tZYtxFnEbsAPJHzD03AMw4NRYtxgU31bZ9T2JGprEqGVLoi35cWY_DfeETaKDo12PNQHP0lGckx8iAELkk8VO0bxGJXYGMBOgLWbF51UjoDP2leYSHQCrND2NUi7pAUycQkkTPziaBDLM9Phvh804dyW99n02u3ReLWynW5DD-wcakrFVQsJuCXyei-HX29xsq90MoienQz1gxe8flsr8-TjBAWXEL2CTUrGIjnBYv49oG0eAfH2mGIUOck9OBN1CSYL0zrcOmGFaiVkMQsToyz_Jl0IPnYDiWITpn9x57Efv6MCvaDNPUCwIUSrO0hCXnpxZkwZlkXvCfE6KnAdieoG2KwTjpnXoBMNy5n_3_szl45plSJMAABjRX8qlsEbBzNglM61Ej8N_Eyy-KnHwSjh2a8tBSirgWW70PFZk8PUZLcZaVyJfDkkUq-l8OpNkEmLAw7r3zwRUX8JtDkayX-JrTz1GcMKL6o-biZsJKZO9GRj3i49czipSmp_TVddNxzLV6gyUuVSaA5GUEzSPrfMLJEgCZD-IsSKSnKZlq4My2ALpmfMTiGKBIeejyePU02MkH9wV0oSKtauHoTx3ZURRsZOGOHhu-CKxz2zYjmExVjO3ltBBzvIZH0-kQrjPmuaFpQ3JYqIJpKOp8jGCmsTTps7nXkhULomlVB1pHNcV8M_hur7d6QOfUkctkGOqjYAze-M_3jN5icKimC_eP2wp3EBD3kvHlYOeCrtn2VMG_ejvvb-TzdQwaksgwYdshVm7_nNIPOegFq7N8zcKo_9maWGMNwa6Q86GsHl8tV-cxPL9LxNb0GbDxnXxwpWhqNoAdIU5vL_zzI-yfZ0Rw4EpKWaRmvekrdvtNFGKUlzr99olWZRLpmXjZM9tvqd2qWYfwVMjp6uRFqqIvpv_92eEaoiCjHIUVdhscL0O9o2OA0wR9QSMkEgmQoIP5ItCUzdF7W3EC0sIXaXQ3QT00vbLPW9ntO26luEh8YHMmmLr-16Czr54BBmmCPnzGSVrVmlVYg-XCKnxOY076FHeIofM41T1l7MXYOc110-zJZD-6Kls-Q9SxZCL368jpTRk8-CR_nDxJKNkKm8CzkEJoTrHm7AKAEIo60PJHSUyRARGNnFFAYB9IEnFC2HS77bvfPaQKDCyUDS5fzvrpJytl8iv2NnV3kVtzddcehNHMfDUzQ2OOVTMOODSeboLSnluu4yLPpUaKQV7pAVs_SM8Cu6qjkvGrN0e62bi5PTJFF8ojrqLct5MyizvMZoeq7m5R-Kv1jCvBE68gFL71wRX8WBlHGR3-sftv3_FnW5paw7gq-BcH4nXd9JLDuDU40cqnMwWdBYEpP261xnP3K_BFUmE2UEAoeHJZs2JXia0m_2UbO0nDAq5mQyAZk_l_FTSFYbiB0ki-Sd3rGN9RiwPnL8SIA17FkS9pnZxJeMzwB97b4dFQS3zJGf8G5f5X3izGQh8Oy6IMNSzdnsDNx_HSH3x9YwTqV0pb99nyLCFIR6kGiiaIO0Oqjojsh00MqhQfRLlvfXB0KxboLmayknfytaEkVxhqSyz5PceUziKJ4VE9AblB4TCckKN1AwAKehAaZ5gakgfQ67QhMkqEaf6-Hubj1-NhvrakhPMfdu4vaS-bWZEwUsvaiqTw_zSx_mwM9JEGpHPnhNsDFDRxeA7-AlTluXLApIK3WjAOoPmXVipcD3NHwZYG_VSfLhz3ftQNeinErlKiM_yRDCieO-DTrkKPIPL21XejdNfkus8dpNF6uB2nODl8RRiZAVwa6KCLOp2XRXRAI288DYUDptCjKXlUuv3YZKGTe8m6w2Fo8gC-cWqMZg-uBhWKfsFtio4WIpkQzZfhkr38Auq2RPBW7CeF_k7ViBYfm7Nq9Espuh9Js5UrtiKCntn1lQvczcO8812MolIv1JlmPe3R9u829qn39uEPirhRWJCbF1S5rV7Nzq0zGAuVpKDO58mWJjqlSuMFOBFpYRkySszWrHCCm12t1OOaO9mXOF11luoHZFEQl9f3kJ03-eR4DBJk9dMw8ggk-taotWnsRp-s779KQq7on640fCaCGFTYxwjJHRDSEY84i2Vg6JwI5qAg1zIozHuL84Kykht6ymlSpUlmbpEtd9OPnaR0ncJfDqEdyFTYW5NevK_ToywGJ8Px1ngtVufzYGyDv-DKwRA0Dryett7WQonvQv02owQoTgAyw0cFlD4C_ie3Xun-qpw_Ze7NpptWwq2uJWlnsVnPVvhedO-d33wwTCTVqSwSHxoVDArSnY7S73HUXtXcTAmJX1LYsIvYTipZwW-ClWtrno_W6ZyA4H3HEVrddJXPl1P-EWZTxFgUpRg8sluFABpOsymqBNn1mKby2p2plaj5GAnVtM4PCZ6JDd-23s1ojdv8hh8U2H170Tkt56oDWTku2C1gsitRza_z0muDeX7YydibrbZnlTrdBS5dAzspEZo0lk2t80IFiCuIbcj8QtrEOMcOiXdB2Qochf1FKwWQp6kI_czEdVVgyIH20MpeTOYTLkkP3p5ViqQVs1xE8qnWfL3IdDJWTBId2dbDh0ZUb_j_S7Iayqu0a5AXhZS7qlsYwgoP8K9vxT-fUIqETikBkDLfQM6Cbys16W4emT5v7FMRO9wjINMMt21tZnUxuEJgigD8o3FxSmaoFyiOYGXL_3T-xd4Xvc20lBQC9dJRrA_0lu84c0YYR4YU3tNzgq0ImFETiWcl7M_nlmJidlrfGi4Ny9giRbOnHJc5OfUGbjcsQ_g3jFkXb9F5nSxrlhwjVqgThQ2Mghe78D13s63PdYsbvk2drrDfazX4Jv-9VCtVxZmBKxwPVn_MVnkbHbZl9obvkkya1xoobEi1nCQ4bofTfIyUv58-J_OZPDH-zK1FAjSap5ahC3mhoi3mF9IQEHu7hnZluLib7XBxjiGH0y-g-XHT-R_2-q_mWcTI-x7MM05VyEK6UF51-ClralRZp1GNnJrhKL_ofSggj-NGZdbJpYAb0sqYG6i1-1-46vci6luuRzDymHj6qmlYaX1SejgpsF8KXibNBWF5GkctSwFmICVj2yat3iv9S2XVH_YHRbgxP_W31A7FLzSAa24sQdWm_16EJk7uKlj8ev4ZKKQIt1hZtBLDhBY0wzhAtWV49MjIbIIjatWB5W3E5tEaMYyIn93w0_VGnO3cMLuPNYY2zjexdk72jli28PQo_GCbwa_r5YyJd7ZrspbK4oo7P3S4EGpIg5E_CaIb60kwbEzTt6D1O-W0INmx7ly2k-0vHR0sfPtjWRslbRcsIl1snJ73dbIL_xmSy0Ba9TEnDn8HgvFtg15icsnd888eYC4WeKuG88yMzdwZ6AuYS5b_8c="},{"type":"function_call",
    match = re.search(r\"/arc/outboundfeeds/sitemap\\d*/(\\d{4}-\\d{2}-\\d{2})(?:/|$)\", str(url or \"\"))
        sitemap_url = str(row.get(\"loc\") or \"\").strip()
        \"published_at\": published_at,
        \"body_word_count\": len(article_text.split()),
        \"raw_html_contains_flavio_valle\": raw_flags[\"flavio_valle\"],
        \"raw_html_contains_flavio_vale\": raw_flags[\"flavio_vale\"],
        \"article_text_contains_flavio_valle\": article_flags[\"flavio_valle\"],
        \"article_text_contains_flavio_vale\": article_flags[\"flavio_vale\"],
        \"full_page_text_contains_flavio_valle\": page_flags[\"flavio_valle\"],
        \"full_page_text_contains_flavio_vale\": page_flags[\"flavio_vale\"],
        \"matcher_hit\": matcher_hit,
        \"failure_bucket\": failure_bucket,
    }
def summarize_rows(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    by_host: dict[str, Counter[str]] = {}
    for row in rows:
        host = str(row.get(\"host\") or \"\").strip()
        bucket = str(row.get(\"failure_bucket\") or \"\").strip() or \"unknown\"
        if not host:
        by_host.setdefault(host, Counter())
        by_host[host][bucket] += 1
        if bool(row.get(\"matcher_hit\")):
            by_host[host][\"matcher_hit_total\"] += 1
    return [
        {
            \"host\": host,
            \"rows\": sum(count for key, count in counts.items() if key != \"matcher_hit_total\"),
            \"matcher_hit_total\": counts.get(\"matcher_hit_total\", 0),
            \"bucket_counts\": dict(sorted((key, value) for key, value in counts.items() if key != \"matcher_hit_total\")),
        }
        for host, counts in sorted(by_host.items())
    ]
def write_reports(payload: dict[str, object]) -> tuple[Path, Path]:
    out_dir = PROJECT_ROOT / \"data\" / \"experiments\"
    out_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime(\"%Y%m%d_%H%M%S\")
    json_path = out_dir / f\"globo_family_diagnostic_{timestamp}.json\"
    csv_path = out_dir / f\"globo_family_diagnostic_{timestamp}.csv\"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding=\"utf-8\")
    rows = list(payload.get(\"rows\", []))
    fieldnames = [
        \"url\",
        \"host\",
        \"fetch_status\",
        \"final_url\",
        \"published_at\",
        \"body_word_count\",
        \"raw_html_contains_flavio_valle\",
        \"raw_html_contains_flavio_vale\",
        \"article_text_contains_flavio_valle\",
        \"article_text_contains_flavio_vale\",
        \"full_page_text_contains_flavio_valle\",
        \"full_page_text_contains_flavio_vale\",
        \"matcher_hit\",
        \"failure_bucket\",
    with csv_path.open(\"w\", encoding=\"utf-8\", newline=\"\") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, \"\") for field in fieldnames})
    return json_path, csv_path
def main() -> int:
    parser = argparse.ArgumentParser(description=\"Diagnose Globo/G1/Extra Excel URLs by fetch and extraction bucket\")
    parser.add_argument(\"--excel\", default=str(EXCEL_DEFAULT), help=\"Path to Acompanhamento GVFV.xlsx\")
    parser.add_argument(\"--sheet\", default=\"Assessoria de Imprensa\", help=\"Sheet name\")
    parser.add_argument(\"--start-date\", default=DEFAULT_START_DATE, help=\"Lower bound (YYYY-MM-DD)\")
    parser.add_argument(\"--end-date\", default=DEFAULT_END_DATE, help=\"Upper bound (YYYY-MM-DD)\")
    parser.add_argument(\"--hosts\", default=\",\".join(DEFAULT_HOSTS), help=\"Comma-separated hosts\")
    parser.add_argument(\"--workers\", type=int, default=8)
    parser.add_argument(\"--request-timeout\", type=int, default=20)
    args = parser.parse_args(sys.argv[1:])
    excel_path = Path(args.excel)
    if not excel_path.exists():
        raise SystemExit(f\"Excel not found: {excel_path}\")
    selected_hosts = {item.strip().lower() for item in str(args.hosts \or \"\").split(\",\") if item.strip()}
    excel_rows = load_excel_rows(
        excel_path,
        sheet=args.sheet,
        start_date=args.start_date,
        end_date=args.end_date,
    )
    rows = [row for row in excel_rows if row.get(\"host\") in selected_hosts]
    matcher = get_flavio_matcher()
    results: list[dict[str, object]] = []
    with ThreadPoolExecutor(max_workers=max(1, int(args.workers))) as executor:
        futures = {
            executor.submit(
                diagnose_url_row,
                row,
                matcher=matcher,
                request_timeout=max(3, int(args.request_timeout)),
            ): row
            for row in rows
        for future in as_completed(futures):
            results.append(future.result())
    results.sort(key=lambda item: (str(item.get(\"host\") or \"\"), str(item.get(\"url\") or \"\")))
    payload = {
        \"start_date\": args.start_date,
        \"end_date\": args.end_date,
        \"hosts\": sorted(selected_hosts),
        \"row_count\": len(results),
        \"summary\": summarize_rows(results),
        \"rows\": results,
    json_path, csv_path = write_reports(payload)
    for host_summary in payload[\"summary\"]:
        bucket_counts = host_summary[\"bucket_counts\"]
        print(
            f\"{host_summary['host']} rows={host_summary['rows']} \"
            f\"matcher_hit={host_summary['matcher_hit_total']} buckets={json.dumps(bucket_counts, ensure_ascii=False, sort_keys=True)}\"
    print(f\"JSON: {json_path}\")
    print(f\"CSV: {csv_path}\")
    return 0
if __name__ == \"__main__\":
    raise SystemExit(main())
    DIARIO_DO_RIO_SITE_SOURCE,
    TEMPO_REAL_RJ_SITE_SOURCE,
def collect_wordpress_site(
    queries: list[str] | None = None,
    source: dict[str, object],
    source_cfg = dict(source or {})
    source_name = str(source_cfg.get(\"source_name\") or \"WordPress Site\").strip() or \"WordPress Site\"
    source_type = str(source_cfg.get(\"source_type\") or \"wordpress_site\").strip() or \"wordpress_site\"
    host = str(source_cfg.get(\"host\") or \"\").strip()
    base_url = str(source_cfg.get(\"base_url\") or \"\").strip()
    if not base_url:
        return []
    query_list = [str(item or \"\").strip() for item in (queries or []) if str(item or \"\").strip()]
    if not query_list:
        query_list = [
         1crape timestamp (now-ish), outside the requested window.\r
            str(item or \"\").strip()
            for item in (source_cfg.get(\"query_variants\") or [])
            if str(item or \"\").strip()
        ]
        query_list = list(FLAVIO_INTERNAL_SEARCH_QUERIES)
    for query in query_list:
        batch = collect_wordpress_api(
            query,
            source_name=source_name,
            base_url=base_url,
            date_from=date_from,
            date_to=date_to,
            per_site_limit=max(1, limit_total),
            request_timeout=request_timeout,
        for item in batch:
            canon_url = canonicalize_url(item.url)
            if host and not is_likely_article_url(canon_url, expected_host_fragment=host):
            metadata = dict(item.metadata or {})
            metadata.update(
                {
                    \"query\": query,
            
-fD�~<��v4��n,��d��	
	�	L
T
	�
�
�"��\�f�|:��t2
�
�
l
*�^D�~<��v4��n,�_gi�3Agpid:6916:94a054c8-c51f-42a5-98fc-c6f6f3a9479bi�-7�μ4�q4�qAgpid:6916:94a054c8-c51f-42a5-98fc-c6f6f3a9479bi�-7���4�p4�pAgpid:6916:94a054c8-c51f-42a5-98fc-c6f6f3a9479bi�-7�2|4�o4�oAgpid:6916:94a054c8-c51f-42a5-98fc-c6f6f3a9479bi��7c�t4�m4�mAgpid:6916:94a054c8-c51f-42a5-98fc-c6f6f3a9479bi��7dcL4�n4�nAgpid:6916:94a054c8-c51f-42a5-98fc-c6f6f3a9479bi��7b�(4�j4�jAgpid:6916:94a054c8-c51f-42a5-98fc-c6f6f3a9479bi��7cQx4�k4�kAgpid:6916:94a054c8-c51f-42a5-98fc-c6f6f3a9479bi��7c�|4�l4�lAgpid:6916:94a054c8-c51f-42a5-98fc-c6f6f3a9479bi��6��4�g4�gAgpid:6916:94a054c8-c51f-42a5-98fc-c6f6f3a9479bi��6��\4�h4�hAgpid:6916:94a054c8-c51f-42a5-98fc-c6f6f3a9479bi��6�-�4�i4�iAgpid:6916:94a054c8-c51f-42a5-98fc-c6f6f3a9479bi�y6ܞ�4�c4�cAgpid:6916:94a054c8-c51f-42a5-98fc-c6f6f3a9479bi�y6���4�d4�dAgpid:6916:94a054c8-c51f-42a5-98fc-c6f6f3a9479bi��6�� 4�e4�eAgpid:6916:94a054c8-c51f-42a5-98fc-c6f6f3a9479bi��6��t4�f4�fAgpid:6916:94a054c8-c51f-42a5-98fc-c6f6f3a9479bi��8pI�4�4�Agpid:6916:94a054c8-c51f-42a5-98fc-c6f6f3a9479bi��8pet4�4�Agpid:6916:94a054c8-c51f-42a5-98fc-c6f6f3a9479bi��9>Հ4�4�Agpid:6916:94a054c8-c51f-42a5-98fc-c6f6f3a9479bi��9?�4�4�Agpid:6916:94a054c8-c51f-42a5-98fc-c6f6f3a9479bi��9?>04�4�Agpid:6916:94a054c8-c51f-42a5-98fc-c6f6f3a9479bi��9?uD4�4�Agpid:6916:94a054c8-c51f-42a5-98fc-c6f6f3a9479bi�
9�84�4�Agpid:6916:94a054c8-c51f-42a5-98fc-c6f6f3a9479bi�
9���4�4�Agpid:6916:94a054c8-c51f-42a5-98fc-c6f6f3a9479bi�
9�Ӏ4�4�Agpid:6916:94a054c8-c51f-42a5-98fc-c6f6f3a9479bi�
9��t4�4�Agpid:6916:94a054c8-c51f-42a5-98fc-c6f6f3a9479bi�
9��4�4�Agpid:6916:94a054c8-c51f-42a5-98fc-c6f6f3a9479bi�I:���4�4�Agpid:6916:94a054c8-c51f-42a5-98fc-c6f6f3a9479bi�I:��|4�4�Agpid:6916:94a054c8-c51f-42a5-98fc-c6f6f3a9479bi�I:���4�4�Agpid:6916:94a054c8-c51f-42a5-98fc-c6f6f3a9479bi�I:��4�4�Agpid:6916:94a054c8-c51f-42a5-98fc-c6f6f3a9479bi�I:�\�4�4�Agpid:6916:94a054c8-c51f-42a5-98fc-c6f6f3a9479bi��8�4�4�Agpid:6916:94a054c8-c51f-42a5-98fc-c6f6f3a9479bi��8�4�4�Agpid:6916:94a054c8-c51f-42a5-98fc-c6f6f3a9479bi��8�*h4�4�Agpid:6916:94a054c8-c51f-42a5-98fc-c6f6f3a9479bi�Y8��4�4�Agpid:6916:94a054c8-c51f-42a5-98fc-c6f6f3a9479bi��8�4�4�Agpid:6916:94a054c8-c51f-42a5-98fc-c6f6f3a9479bi�Y8�^@4�4�Agpid:6916:94a054c8-c51f-42a5-98fc-c6f6f3a9479bi�Y8�4�4�Agpid:6916:94a054c8-c51f-42a5-98fc-c6f6f3a9479bi�Y8��4�4�Agpid:6916:94a054c8-c51f-42a5-98fc-c6f6f3a9479bi�8��44�4�Agpid:6916:94a054c8-c51f-42a5-98fc-c6f6f3a9479bi�8� X4�4�Agpid:6916:94a054c8-c51f-42a5-98fc-c6f6f3a9479bi�Y8��4�4�Agpid:6916:94a054c8-c51f-42a5-98fc-c6f6f3a9479bi��8p�44�4�Agpid:6916:94a054c8-c51f-42a5-98fc-c6f6f3a9479bi�8��\4�4�Agpid:6916:94a054c8-c51f-42a5-98fc-c6f6f3a9479bi�8�L<4�4�Agpid:6916:94a054c8-c51f-42a5-98fc-c6f6f3a9479bi�8�4�4�Agpid:6916:94a054c8-c51f-42a5-98fc-c6f6f3a9479bi��8���4�4�Agpid:6916:94a054c8-c51f-42a5-98fc-c6f6f3a9479bi��9>n`4�4�Agpid:6916:94a054c8-c51f-42a5-98fc-c6f6f3a9479bi�i7�At4�t4�tAgpid:6916:94a054c8-c51f-42a5-98fc-c6f6f3a9479bi�i7� 4�u4�uAgpid:6916:94a054c8-c51f-42a5-98fc-c6f6f3a9479bi�i7�ZP4�v4�vAgpid:6916:94a054c8-c51f-42a5-98fc-c6f6f3a9479bi�i7�v�4�w4�wAgpid:6916:94a054c8-c51f-42a5-98fc-c6f6f3a9479bi�i7��4�x4�xAgpid:6916:94a054c8-c51f-42a5-98fc-c6f6f3a9479bi��8E��4�y4�yAgpid:6916:94a054c8-c51f-42a5-98fc-c6f6f3a9479bi��8F)X4�z4�zAgpid:6916:94a054c8-c51f-42a5-98fc-c6f6f3a9479bi��8Fgt4�{4�{Agpid:6916:94a054c8-c51f-42a5-98fc-c6f6f3a9479bi��8F��4�|4�|Agpid:6916:94a054c8-c51f-42a5-98fc-c6f6f3a9479bi��8F�T4�}4�}Agpid:6916:94a054c8-c51f-42a5-98fc-c6f6f3a9479bi��8o�\4�~4�~Agpid:6916:94a054c8-c51f-42a5-98fc-c6f6f3a9479bi��8p$4�4�surn data.get(\"content\", \"\")\r
        if not any(f\"/category/{slug}\" in path for slug in section_slugs):
    ODIA_SITE_SOURCE,
    R7_SITE_SOURCE,
def _parse_sitemap_index_entries(xml_text: str) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    try:
        root = ET.fromstring(xml_text)
    except Exception:
        return rows
    for sitemap_node in root.iter():
        if _xml_local_name(sitemap_node.tag) != \"sitemap\":
        loc = \"\"
        lastmod = \"\"
        for child in sitemap_node.iter():
            if child is sitemap_node:
            name = _xml_local_name(child.tag)
            value = _safe_text(child)
            if not value:
            if name == \"loc\" and not loc:
                loc = value
            elif name == \"lastmod\" and not lastmod:
                lastmod = _parse_datetime(value)
        if loc:
            rows.append({\"loc\": loc, \"lastmod\": lastmod})
    return rows
def _parse_unix_timestamp(value: str) -> str:
    raw = str(value or \"\").strip()
    if not raw or not raw.isdigit():
        return \"\"
        return datetime.fromtimestamp(int(raw), tz=timezone.utc).isoformat()
def _day_key_from_iso(value: str) -> str:
    if not raw:
        dt = datetime.fromisoformat(raw.replace(\"Z\", \"+00:00\"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).date().isoformat()
def _r7_day_from_sitemap_url(url: str) -> str:
    match = re.search(r\"/arc/outboundfeeds/sitemap\\d*/(\\d{4}-\\d{2}-\\d{2})/\", str(url or \"\"))
    return match.group(1) if match else \"\"
def collect_odia_site(
    max_pages_per_query: int = 6,
    source_cfg = source or ODIA_SITE_SOURCE
    source_name = str(source_cfg.get(\"source_name\") or \"O Dia Site\").strip() or \"O Dia Site\"
    host = str(source_cfg.get(\"host\") or \"odia.ig.com.br\").strip() or \"odia.ig.com.br\"
    search_template = str(source_cfg.get(\"search_url_template\") or \"\").strip()
        query_list = [\"Flavio Valle\", \"Flávio Valle\"]
    start = _parse_window_boundary(date_from, end_of_day=False)
        if len(collect�1Tf3aK8NWSLzqy1lte_9ELhTg38b9ZQ5w6XQf6jqkylJ5C94o3Z06ETJuSwLKgbpyCD0tw2MsbdIl9EXjxb0bkmnxTUXSnUnjWhRM77p6I8G7BKyHA0wsmwty82Q4XL981TgQvuXv5cu54GPm8ydcPhTpq9ZKgWljpmsr5JGOaKBOSeBg8d3JsGx9hcR8jFGiChkLyfYa14Bz75z33XGUMapiJ7AJsln2R0YRlotgKG7FFusPRPOAE55srWd_ZbxV3gfJ9Ed4beC820L48lOqizcxGR60jY5CfVqog0UoMG0iJJj6qEEbYxux_nCY7NLyetPBvzySPQ6XuPJNHK4jBfYb-na-mKmSLQH7gmbX37uKHoQFQ5uokKLmuVCzRtmEI0PCQdLmZXXl-8riDtShtrmLcGToLBwOF8bSymnPF8lwDTY-mSRlBPQuncIA46yojpoxBDLAny57twRulCsxjOkblUDOutDkJ6dF-d-BbK2sZ9r9XpvZc0XYiKb48LUxR81oKNWvTezHIrUPdGh7cHB0MfqrAO3A3jCmVmSdg3FND3q24gwM677kX2KoEJJcy797CSrYYNv7PbJrw1xjXqV2M-WfJyO-T7G8wZL9xtoND9hobLw0f87VeI3uggts0AmaRcvCEv7XiDjPSlCn8azRGfG9KkFKannDAjOEnrBztpQzcNFx86rpQsBrgsuSsqqpOuJIyVCA0me2CYnsWEgmBKlfhaDqY0L2JPb7wk0ZkE7R4REJ_Nx3ynw1waEl4Xxy9Sr3z_h9jDTNbc6aoapSFALZeZ2D8P_-orxHoVAgYa5-fQYkdygGtP4Klw82d5Ca5mlxn8AUiqzrqTE1x1v0rqSUshuVV4uOkhS9dtBtDMOH9YMWR-u5gQN04pHpZzifhrN0--EVrMLoS60JWN8-7UNZiRLur1cSOcoHYikKl09U53jVfB7y3cxMiU30WrhPSES2BYh_j5fdxiYiBhHvMlKZ0WQycyLuoNs_btJJ2PO4S6BH0XmOVObyRvowUtJsNunm2hg_dhp69kOIepdlt5Z3XfJEdG74NX5MTVxm0L116vWuUwmsARtUtqOMwt3nec59npPrSE4uDkSZRzcOb1I7akypMkjuExQv_tYQF8LFqjFZWAqx6kA1f7l4MEcpGrw5bG_cA_cPGM_csiAJeVh5l67KcT7JXOmGAeaNIqoca6vzS74Q3oY8lcvdKneQS5FogfXdI-lutgzpH-wwF5hQAxultLliQhDGEjLww=="},{"type":"custom_tool_call","status":"completed","call_id":"call_L4fcKuY9ZNmlwPwuC2HA74yU",
         o   break
        sitemap_url = sitemap_template.format(yyyy=day.strftime(\"%Y\"), mm=day.strftime(\"%m\"), dd=day.strftime(\"%d\"))
                    source_type=\"odia_site\",
                        \"odia_source\": \"sitemap\",
                        \"site_collector\": \"odia_site\",
        page = 1
        while page <= max(1, max_pages_per_query) and len(collected) < max(1, limit_total):
            search_url = search_template.format(query=quote_plus(query), page=page)
            try:
                _, body = fetch_url(search_url, timeout=request_timeout)
                payload = json.loads(body)
            except Exception:
            if not isinstance(payload, list) or not payload:
            page_new_urls = 0
            dated_hits = 0
            older_hits = 0
            for row in payload:
                if len(collected) >= max(1, limit_total):
                    break
                if not isinstance(row, dict):
                    continue
                canon_url = canonicalize_url(str(row.get(\"url\") or \"\").strip())
                if not canon_url or canon_url in seen_urls:
                if not is_likely_article_url(canon_url, expected_host_fragment=host):
                published_at = _parse_unix_timestamp(str(row.get(\"publish\") or row.get(\"date\") or \"\"))
                if published_at:
                    dated_hits += 1
                    parsed = _parse_window_boundary(published_at, end_of_day=False)
                    if start and parsed and parsed < start:
                        older_hits += 1
                    if not _within_window(published_at, date_from=date_from, date_to=date_to):
                        continue
                seen_urls.add(canon_url)
                page_new_urls += 1
                collected.append(
                    _build_specialized_candidate(
                        title=str(row.get(\"title\") or \"\"),
                        url=canon_url,
                        source_name=source_name,
                        source_type=\"odia_site\",
                        published_at=published_at,
                        snippet=str(row.get(\"description\") or \"\"),
                        metadata={
                            \"odia_source\": \"search\",
                            \"search_url\": search_url,
                            \"query\": qu_oQaQCqq2vTtkLbJnqjg3ZCZf0F9Dk37sUwu-ucnB77Cg1cHos2OxnB9WAGNFZntoFUXVQcQXkd-zVoEuMC0SqFqrib0q4u2emiMVZAFaoHjWMzYFm72mtfDSwzB9cHpTpduXkYK7OOzjAYgp7J8rArDhsDgq5Tlu7vmugmMQT9KQcBfqQm0yWJsgtCVQ6Fc7JAeS5FXkhIOO2q_OUHPSpZr95FRfv4GaL_Al09m_3uNC2cQuwwyNGwXUkVr6IcfxnVHuw3quSyVbGBxFbdq90bNyVLwfg_3P6kvbv1s2kzqDp61Aj-4_EqBUQ4cLqQ_V0T1T04AKHhKp9wrIrqx1BbgLsnesfCWuod1mIi0Lqpto4LPiEXEzE5vx7QyjPsFwzpE_VF7mm0vM8GF3Cd4fmIi__jdqZxe6FfPavC9HNugwvNhvkEZKZ9U9M44T42NfoXXpMnkagzsHLph396piL4G25kBEnrsRN8RjnaEbB-EgXaSYY7DXbe_Af7vS07QwOEjNpJsOIMp4AfecbpFQEqoQ4RnOg9ehv8QfX9dHcesr9Hz6XxNVR1XwpUwQF42dSzv7Qh2D0hX6bIPPDv0niiVSExarzNIExqv73PWJm0BtnvlEY8ZRK7vsAITEBjGWpyVQUXpL1AsqdNSHTJtMANq1Z7D9BkhUScRxcDu5meM1mKpgUJEC60q20lBHwfsgn19YhCPNfwApLZTkbSoRPTmwib1sq2mur3ft6Z-HHhF1ky0pXkflIWLEgoudN2ItADfRRXwbRO7SWFLaNNL5fysT9pRkhQw_pwWFezPLFrYgNCTwsUGdI-bU8Z8wnx7SmusmJhzhmv6ZyxaFNL-NjWSyk7735gqGO9s6Z8iGt7K15gIWqUIvsBm8LV1_bX9-_VHxOrujsQl2XnI9g0xOlVlnOT4rraU3nwTTDgiXP5uk5SL5RsdTzZelFSb645UPXdZ3hfJ_PSbd_onn1XM6Yzj13QB6EabzLS4ENtJUbr2IYN7hZtSUsIcLnei01i0dyQTkh0u171AGpXkOmuHMZuQpZK5pj_Ak40xcOr506Vueb65OdgQgaijP_7JQ_D9z6aclNeDTfPT-AuIiKk52NqJ8N54gO4IdQ6Jzgi9or6UczinZJhiZTAWAvb_LD8UVz37Gb4523TQiSlNjXCDiBGX-MZYB9a11guQ21vL2dOw5drElPNrXoYt2ZQFUYEq1croXe41Qu2eJKKoW9G6jTVG9eBop5dsRbvqtZm78hDVMV9kDiR_yFHFcVri5_4fzxy2nJbaPKSedGpvPgweHOZkoLK__BUbkCbHkwduzdPTh8H1mApWf6ohJSnGubiPDMqABSZXOyMdFkqGZvi5hflnNuotH0geYcFs1ARI3PUSIWMW9CLf2Ckri950comfj9vb6dlTYxTp4YKG_pu2wLapr159Ir_gRYpY0L2BZPDi_qZSOO8RzZf3WJVrNP-2YcK72EKQXV-yJE8kbXB-Ehwb5GhOZBfikl5S7RiCsYyzbpgDm4oQt-f2m3M5UNZ6EygTwVcbc3zEJX5ZBbaZ7jvm9y6nRnPk-p-HjjBPqCMtv2V3Bo07wWTdLfgjWeFGkZfcQ2Wcn85H8NFQPa8nUfXI4dOpIBuM7TVBY1K98BX_DzH0JR8upfsujcgI7F2wbemnRYFyS2wLfJz82f3nVK3iq0RCXEUNw0F7-ODc0z8wPNGqWVmCNUNYP1Jz_jynsve0vtJ4aah11G1AT1GbVbgV5k1-P0Xdv-GLXSI3_ZKDZTqAGGbg-NGmkA-BAPJ5PjYxZj4h_ZupacnBeRpvv9kCN1dEQk_o_xRAc3bl7AJWqGcO1VkGXmz7Obgo6hZNtSS09F2hcYimSWpaz_CeMd44Xav5L5bpbJ21FX_Usw1MKZS5B0YTU3INSctIS1YDJxrAHhV27PwmojUA9VXxmvlT88T6pLyYF8fvAKhGFWd-Nkry6EuXvGp27BVhDNKPwMSzIrF3MaeK-RdGoZg0zr4aFIAhxh72heGkcoQW8tIWYens06Ra5ZZq1qA5txY4KqW4_lz9U49sAtAILYnlLZ7QavAnKbRUKge1_igppxdxGOlb0swqVrKTPmWXNABbA7JyaKoP7jXIJiZU35KTJmTo6tFHC0L3dju0lC6vZqhClDl6w2yRMXzP7jXm2dNwsqmRSIeaqFSD7_QvSec6S5EBsetUnlSfy3JSUNuhKG7R8RIlV6tl-MOk23mu-5_UYJ9aDOdO9jzCjtU4K99_Pph7emG1WOkg6mDhgGeH_w0Pg6mzPtYvwubSNRgSoH9NrY0P1cDk_PiGLB8r68ZGsGKjfn9wflyrPwMyHsWYwr-d5oY5qq7a_CquY0yGjR7b-a6s3hQwHZUdRfOuI0TdpZlGbLpWManH1rTjIJUhwVEQf2JuiEQc27PlLvc5GxORHH9iCMmlPC5M8YOj5ZM9SPvkatv5PInIUcPDh-b9I6MQSqVtG9iv0yewZZTWE4RnPhjWmlQ2RZvDRJwpBGxMYl7SDYBEFBiOnjjuLXbHYDEriwu6sLqnsP4loIMUnLUzPxvANEarf4nRd7BQgYrkFrXnAdEnfeus2bGyRSZ23MCbROY_uYonWulxnFZ4i9eVzTvFpC28luY0YUv6xzojowKLbZYkWXejL_3awCf3_LZhI0W7vANoDqr2XTaf6PqpDL4wq68K5Ir0uQVR5CUSbtmo1v6G9e7NT8kBfIa9R4hzXTTvkRpJ4E2Dw0Zb5f90HPxDpTbnTZHLobdYRfj3y4Ggceksay-rBUoEOyH4wnKRXerY5AMbY5fNRmuAZ94xDDxn_xwm9CtU0qSJz-VKSDbSiDk6pkU8Q0eWNuHGKJNmLrKyGwxlBvH4uTiE0BcUeIETQFX8OhTYV2K9881n5peAEGTkTL9LyWKypGHX58A0oWJ9t0UInMHCUilXLIwAaZfPSZSPmSC57ziO1m-6MakWljZldlTuKkpYvbRn9eiW47gj4QDNjMyG0vFSiNF9VW6RGDwwpGwTbspwSGc6U0FukrWC8tj50iNYAEQ8BdoE8rXt0EkoUlo60oF8mOjJ38iUzq010l0KrtyyglD8s4h70pfSkRBeNSi9Y3Pb1acvTKeTGj3eCwEHY1RemKm2VHQLqpne9nD2ilCGZ1DZj3hBctn1ESDd2_TYwEWm9mBZmQJPKeXq9eOHO93d18lSlpUdmUPzbvALa4Er7bWcQDsDo3SeOg6wZ-_N9d1HIdXdoFtrdAq3huV1tbswyCbkxoBl8qS5f_xeKfoDqKJ3TDG4_viyJTC1TrjQVji1ziLjp0Yh-6G5PVHsxnbhURjNP4iKTqagITt2rSVEimKYZzGZ6fgGEaSbSZJAXjso7d_nn-mamm0I66pMtwQ3dZyZaVVX_j9oPIwI4Ud7FdNLVq-q0s1cBJNZEeIWYAt5QLzqMgbPE5f715GQJlMBdw-AOSp9ZJBvdf_az1jnt2Ip04QxO1fBbqPHaGZT7b9-II-nMjdRsqJEVN0Dl9y5KfiVHSFXZO1_nTp1NCCHKxUOEClueNVImf6mlwtjOOti6D1JZoeND4WEU6s47EBEXtH2uHiIakbxz0Bez1cvDRL87VSVcGEiivJzhahD-YB7bYhlSlHJ8zZWBsDK7-n1JIenQQosrsDNibObRWH1TgtTXGbEm269zvKqV8XILv3Or2euiEvWuInoZnJl6jb9da1JZn7MOaYye-cDTbCXYUdkA8zQ2c5w4w89WpZxu0BAebdZ81J4rw38U9djixVYgda3ZcBEM90SRbH0W9KMEBg8KJFRubZZjRfEwcJnCHiuUKP2S0nPgGT8f4eYpHxiGj3yft95JpwkwRmb-GTPu6FQggt9VVXhST0iBFLPHM-bnhRflmZZQI2Be1O8eEHeU6xZHl3ndurVoOvAScxm7EyOOJ_1q8YHY1SEQoUDtW6Q_13iP2n0tqJ1ksQYwTubwbGwDRSJWskDgbD5slD_nKamuXSXLGPVRACCXTbkcFW0CKIe6nHzEZF_SNYI0AK0yeoAcjMqw0xGsedIyy842En_L4X2CbKzychw5XbsR86PV7iex8szzVavz4YRH8SFx\")
    assert Path(result[\"summaryPath\"]).is_file()
    assert len(calls) == 3
    collected: list[Can�didateArticle] = []
          �              snippet=str(row.get(\"description\") or \"\"),
                            \"query\": query,
                            \"site_collector\": \"odia_site\",
                        },
                    )
            if page_new_urls == 0:
            if dated_hits and older_hits == dated_hits:
            page += 1
def collect_r7_site(
    source_cfg = source or R7_SITE_SOURCE
    source_name = str(source_cfg.get(\"source_name\") or \"R7 Site\").strip() or \"R7 Site\"
    host = str(source_cfg.get(\"host\") or \"noticias.r7.com\").strip() or \"noticias.r7.com\"
    day_index_url = str(source_cfg.get(\"day_index_url\") or \"\").strip()
    news_index_url = str(source_cfg.get(\"news_index_url\") or \"\").strip()
    section_index_url = str(source_cfg.get(\"section_index_url\") or \"\").strip()
    section_slugs = {str(item).strip() for item in (source_cfg.get(\"section_slugs\") or []) if str(item).strip()}
    requested_days = {day.date().isoformat() for day in _iter_window_days(date_from, date_to, default_days=7)}
    covered_days: set[str] = set()
    def append_sitemap_entries(*, sitemap_url: str, origin: str, allowed_days: set[str] | None = None) -> None:
        nonlocal collected, seen_urls
            return
            published_at = str(row.get(\"published_at\") or \"\").strip()
            if published_at and not _within_window(published_at, date_from=date_from, date_to=date_to):
            if allowed_days is not None and published_at:
                day_key = _day_key_from_iso(published_at)
                if day_key and day_key not in allowed_days:
                    source_type=\"r7_site\",
                        \"r7_source\": origin,
                        \"site_collector\": \"r7_site\",
        _, day_index_xml = fetch_url(day_index_url, timeout=request_timeout)
        day_index_xml = \"\"
    for row in _parse_sitemap_index_entries(day_index_xml):
        sitemap_url = canonicalize_url(str(row.get(\"loc\") or \"\").strip())
        day_key = _r7_day_from_sitemap_url(sitemap_url)
        if requested_days and day_key not in requested_days:
        if day_key:
            covered_days.add(day_key)
        append�_sitemap_entries(sitemap_url=sitemap_url, origin=\"day_index\")
    missing_days = requested_days - covered_days
    should_run_fallback = bool(missing_days) or not collected
    if not should_run_fallback:
        return _dedupe_candidates_by_url(collected)
    fallback_day_filter = missing_days if missing_days else None
    fallback_sitemaps: list[tuple[str, str]] = []
        _, news_index_xml = fetch_url(news_index_url, timeout=request_timeout)
        news_index_xml = \"\"
    for row in _parse_sitemap_index_entries(news_index_xml):
        if sitemap_url:
            fallback_sitemaps.append((sitemap_url, \"news_index\"))
        _, section_index_xml = fetch_url(section_index_url, timeout=request_timeout)
        section_index_xml = \"\"
    for row in _parse_sitemap_index_entries(section_index_xml):
        if not sitemap_url:
        path = urlparse(sitemap_url).path or \"\"
        if not any(f\"/category/{slug}/\" in path for slug in section_slugs):
        fallback_sitemaps.append((sitemap_url, \"section_index\"))
    seen_sitemaps: set[str] = set()
    for sitemap_url, origin in fallback_sitemaps:
        if sitemap_url in seen_sitemaps:
        seen_sitemaps.add(sitemap_url)
        append_sitemap_entries(sitemap_url=sitemap_url, origin=origin, allowed_days=fallback_day_filter)
                    source#E_type=\"extra_site\",
import urllib.parse
    post_json,
    FLAVIO_INTERNAL_SEARCH_QUERIES,
    FLAVIO_INTERNAL_SEARCH_TARGETS,
    InternalSearchTarget,
A_TAG_RE = re.compile(r\"\"\"(?is)<a\\b([^>]*?)href=[\"']([^\"'#]+)[\"']([^>]*)>(.*?)</a>\"\"\")
DIV_CARD_RE = re.compile(r'(?is)<div id=\"post-\\d+\" class=\"[^\"]*\\blist-item\\b[^\"]*\">(.*?)</div>\\s*</div>\\s*</div>')
VEJARIO_DATE_RE = re.compile(r'(?is)<span class=\"date-post\">\\s*(.*?)\\s*</span>')
CAMARA_RESULT_RE = re.compile(
    r'(?is)<dt class=\"result-title\">.*?<a href=\"([^\"]+)\">\\s*(.*?)\\s*</a>.*?</dt>'
    r'.*?<dd class=\"result-category\">.*?</dd>'
    r'.*?<dd class=\"result-text\">\\s*(.*?)\\s*</dd>'
    r'.*?<dd class=\"result-created\">\\s*(.*?)\\s*</dd>'
)
CONIB_ARTICLE_RE = re.compile(r'(?is)<article class=\"uk-article\">(.*?)</article>')
CONIB_NEXT_RE = re.compile(r'(?is)<a class=\"next\" href=\"([^\"]+)\"')
CAMARA_NEXT_RE = re.compile(r'(?is)<link rel=\"next\" href=\"([^\"]+)\"')
PT_MONTHS = {
    \"jan\": 1,
    \"janeiro\": 1,
    \"fev\": 2,
    \"fevereiro\": 2,
    \"mar\": 3,
    \"marco\": 3,
    \"março\": 3,
    \"abr\": 4,
    \"abril\": 4,
    \"mai\": 5,
    \"maio\": 5,
    \"jun\": 6,
    \"junho\": 6,
    \"jul\": 7,
    \"julho\": 7,
    \"ago\": 8,
    \"agosto\": 8,
    \"set\": 9,
    \"setembro\": 9,
    \"out\": 10,
    \"outubro\": 10,
    \"nov\": 11,
    \"novembro\": 11,
    \"dez\": 12,
    \"dezembro\": 12,
}
def _clean_html_fragment(value: str) -> str:
    text = html.unescape(TAG_RE.sub(\" \", value or \"\"))
    return WS_RE.sub(\" \", text).strip()
def _host_matches(host: str, expected: str) -> bool:
    left = (host or \"\").lower().lstrip(\".\")
    right = (expected or \"\").lower().lstrip(\".\")
    return left == right or left.endswith(f\".{right}\")
def _parse_pt_br_datetime(value: str) -> str:
    text = _clean_html_fragment(value).lower()
    if not text:
    text = text.replace(\"atualizado em\", \" \").replace(\"criado em\", \" \")
    text = text.replace(\"às\", \" \").replace(\" as \", \" \").replace(\"•\", \" \")
    text = text.replace(\"º\", \"\").replace(\"ª\", \"\")
    text = WS_RE.sub(\" \", text).strip()
    match = re.search(r\"(\\d{1,2})\\s+([a-zç]+)\\s+(\\d{4})(?:,\\s*(\\d{1,2})h(\\d{2}))?\", text)
    if not match:
    day = int(match.group(1))
    month = PT_MONTHS.get(match.group(2), 0)
    year = int(match.group(3))
    hour = int(match.group(4) or 12)
    minute = int(match.group(5) or 0)
    if not month:
        retur'?
�-O
���z
�
[	�	"��wn���,L���J��[�ii������TRACElogC:\Users\runneradmin\.cargo\git\checkouts\tokio-tungstenite-ea4445d9acecae62\132f5b3\src\compat.rs:131 AllowStd.with_contextpid:10812:584e3330-5a3c-44c8-aa9d-a78cc3e20b4e��?��Z�qii�����pTRACElogC:\Users\runneradmin\.cargo\git\checkouts\tokio-tungstenite-ea4445d9acecae62\132f5b3\src\compat.rs:183 Write.flushpid:10812:584e3330-5a3c-44c8-aa9d-a78cc3e20b4ez�[��Y�'ii����Z�TRACElogC:\Users\runneradmin\.cargo\git\checkouts\tokio-tungstenite-ea4445d9acecae62\132f5b3\src\compat.rs:174 Write.with_context write -> poll_writepid:10812:584e3330-5a3c-44c8-aa9d-a78cc3e20b4e��J��X�ii����0TTRACElogC:\Users\runneradmin\.cargo\git\checkouts\tokio-tungstenite-ea4445d9acecae62\132f5b3\src\compat.rs:131 AllowStd.with_contextpid:10812:584e3330-5a3c-44c8-aa9d-a78cc3e20b4e��?��W�qii����	DTRACElogC:\Users\runneradmin\.cargo\git\checkouts\tokio-tungstenite-ea4445d9acecae62\132f5b3\src\compat.rs:172 Write.writepid:10812:584e3330-5a3c-44c8-aa9d-a78cc3e20b4ez�N��V�
ii�����LTRACElogC:\Users\runneradmin\.cargo\git\checkouts\tokio-tungstenite-ea4445d9acecae62\132f5b3\src\lib.rs:245 WebSocketStream.with_contextpid:10812:584e3330-5a3c-44c8-aa9d-a78cc3e20b4e��W��U�ii����TRACElogwriting frame 
<FRAME>
final: true
reserved: false false false
opcode: PONG
length: 10
payload length: 4
payload: 0x5b5ce9d4
            pid:10812:584e3330-5a3c-44c8-aa9d-a78cc3e20b4e����T�yii����TTRACElogSending frame: Frame { header: FrameHeader { is_final: true, rsv1: false, rsv2: false, rsv3: false, opcode: Control(Pong), mask: Some([227, 48, 63, 248]) }, payload: b"[\\\xe9\xd4" }pid:10812:584e3330-5a3c-44c8-aa9d-a78cc3e20b4e�^��S
1ii�����XTRACElogSending pong/closepid:10812:584e3330-5a3c-44c8-aa9d-a78cc3e20b4e�N��R�
ii����$TRACElogC:\Users\runneradmin\.cargo\git\checkouts\tokio-tungstenite-ea4445d9acecae62\132f5b3\src\lib.rs:245 WebSocketStream.with_contextpid:10812:584e3330-5a3c-44c8-aa9d-a78cc3e20b4e�r��Q
Yii����wPTRACElogReceived message Binary Data<length=4>pid:10812:584e3330-5a3c-44c8-aa9d-a78cc3e20b4e.�W��P�ii����%�TRACElogreceived frame 
<FRAME>
final: true
reserved: false false false
opcode: PING
length: 6
payload length: 4
payload: 0x5b5ce9d4
            pid:10812:584e3330-5a3c-44c8-aa9d-a78cc3e20b4e�Y��O
'ii����$TRACElogMasked: falsepid:10812:584e3330-5a3c-44c8-aa9d-a78cc3e20b4ea��N
7ii�����TRACElogOpcode: Control(Ping)pid:10812:584e3330-5a3c-44c8-aa9d-a78cc3e20b4eW��M
#ii����[�TRACElogSecond: 100pid:10812:584e3330-5a3c-44c8-aa9d-a78cc3e20b4e[��L
+ii���� �TRACElogFirst: 10001001pid:10812:584e3330-5a3c-44c8-aa9d-a78cc3e20b4ec��K
;ii������TRACElogParsed headers [137, 4]pid:10812:584e3330-5a3c-44c8-aa9d-a78cc3e20b4e�X��J�!ii����
�TRACElogC:\Users\runneradmin\.cargo\git\checkouts\tokio-tungstenite-ea4445d9acecae62\132f5b3\src\compat.rs:157 Read.with_context read -> poll_readpid:10812:584e3330-5a3c-44c8-aa9d-a78cc3e20b4e��J��I�ii�����TRACElogC:\Users\runneradmin\.cargo\git\checkouts\tokio-tungstenite-ea4445d9acecae62\132f5b3\src\compat.rs:131 AllowStd.with_contextpid:10812:584e3330-5a3c-44c8-aa9d-a78cc3e20b4e��=��H�mii�����TRACElogC:\Users\runneradmin\.cargo\git\checkouts\tokio-tungstenite-ea4445d9acecae62\132f5b3\src\compat.rs:154 Read.readpid:10812:584e3330-5a3c-44c8-aa9d-a78cc3e20b4ex�Y��G�#ii����>PTRACElogC:\Users\runneradmin\.cargo\git\checkouts\tokio-tungstenite-ea4445d9acecae62\132f5b3\src\lib.rs:304 Stream.with_context poll_next -> read()pid:10812:584e3330-5a3c-44c8-aa9d-a78cc3e20b4e��N��F�
ii�����TRACElogC:\Users\runneradmin\.cargo\git\checkouts\tokio-tungstenite-ea4445d9acecae62\132f5b3\src\lib.rs:245 WebSocketStream.with_contextpid:10812:584e3330-5a3c-44c8-aa9d-a78cc3e20b4e�d=h
�
�
�
�
�
o
V
=
$
	�	�	�	�	�	u	\	C	*	���������jQ8�����pW>%
�
�
�
�
�
v
]
D
+
�����|cJ1������iP7�|cJ1������iP7�����oV={i����
�����i���4�	������i���^�@�J�Ji����(������i���!�o<���i����Y�Y�i���x������i���A"���i���+#A�d�d�i���9�=<�����i���
��<���i��� `:��o�o�i���-�?�����i�����`�!�!�i����h�z�z�i��� w�������i���/�PX�,�,�i���t ������i���&Ƽ�����i���5���7�7	i��� 	'�����	i���6O�P����	i��
3ΈBB	i��%9��$��	,i��J~����!li��h)q,((!�i��h-����!�i��/�0��!�i���[?�66
�i���(2���!�i���	�
���
�i���!�	hAA"i��
=����i��!��(��"Li��E,�%LL$
i��^	�W���$6i���%1�|��%Qi���_��WW%�i���c���%�i���/�+0		'�i�� r��bb
�i��),|��'�i��e:l�h
�i���3�A(mm
�i���+gD��
�i��*|�
�i��$ަ$xx
�i��Y�|���
�i���O&@**	?i��b1��MM0i���:Sw���i����>���
i���9J�XX�i����Kh���i���2D�

i��-�cc!i��&3����*i��("�1i��-*p�ss8i��13��p��=i��16�0P((Di��2	/bL��	�i��2	?����	�i��2
4�33	�i��2����	�i��2G���
%i��2��t>>	�i��3$����	�i��:���
i��>",MM
i��@5I���
i��B�T�		
,i��F(X�	^	^
3i��G,���	�	�
=i��K6r�


Fi��O3��|
q
q
Pi��R�(L
�
�
Xi��_!� T%%
ai��_,�@P��
ji��_7v�<��
zi��`
��22
�i��`�����
�i��`$�R���i��`/�`@
=
=4i��`;�
�
��i��aS.�
�
��i��a �� HHDi��b)z,��Vi��bO\t���i��c���TTi��c&	�x��Oi��c4��L 0i��d$�__ Pi��e%<���� �i��f
��� �i��f/��pjj
ii��g=����!i��g#��!,i��g2�Duu!Di��hćp��
i�z7��n+
�
�
b
��V��J
�
�
>	�	�	u	2��iBipid:10788:5537a0aa-172b-431b-a455-248691d32365i�)`�����Bipid:10788:5537a0aa-172b-431b-a455-248691d32365i�)`]0����Bipid:10788:5537a0aa-172b-431b-a455-248691d32365i�)`h�����Bipid:10788:5537a0aa-172b-431b-a455-248691d32365i�)`st����Bipid:10788:5537a0aa-172b-431b-a455-248691d32365i�)`�X����Bipid:10788:5537a0aa-172b-431b-a455-248691d32365i�)`�����Bipid:10788:5537a0aa-172b-431b-a455-248691d32365i�)`������Bipid:10788:5537a0aa-172b-431b-a455-248691d32365i�)`� ����Bipid:10788:5537a0aa-172b-431b-a455-248691d32365i�)`�|����Bipid:10788:5537a0aa-172b-431b-a455-248691d32365i�)a#<����Bipid:10788:5537a0aa-172b-431b-a455-248691d32365i�)a0�����Bipid:10788:5537a0aa-172b-431b-a455-248691d32365i�)a=����Bipid:10788:5537a0aa-172b-431b-a455-248691d32365i�)aJ�����Bipid:10788:5537a0aa-172b-431b-a455-248691d32365i�)aV�����Bipid:10788:5537a0aa-172b-431b-a455-248691d32365i�)ab�����Bipid:10788:5537a0aa-172b-431b-a455-248691d32365i�)a}����Bipid:10788:5537a0aa-172b-431b-a455-248691d32365i�)bKT����Bipid:10788:5537a0aa-172b-431b-a455-248691d32365i�)b`����Bipid:10788:5537a0aa-172b-431b-a455-248691d32365i�)b������Bipid:10788:5537a0aa-172b-431b-a455-248691d32365i�)�|����Bipid:10788:5537a0aa-172b-431b-a455-248691d32365i�)������Bipid:10788:5537a0aa-172b-431b-a455-248691d32365i�)�����Bipid:10788:5537a0aa-172b-431b-a455-248691d32365i�)�@����Bipid:10788:5537a0aa-172b-431b-a455-248691d32365i�)	�����Bipid:10788:5537a0aa-172b-431b-a455-248691d32365i�)@����Bipid:10788:5537a0aa-172b-431b-a455-248691d32365i�)b�����Bipid:10788:5537a0aa-172b-431b-a455-248691d32365i�)n�����Bipid:10788:5537a0aa-172b-431b-a455-248691d32365i�)y����Bipid:10788:5537a0aa-172b-431b-a455-248691d32365i�)������
���U
Os�
�

	-i���!C���{��A��E�uii�����TRACElogC:\Users\runneradmin\.cargo\git\checkouts\tokio-tungstenite-ea4445d9acecae62\132f5b3\src\lib.rs:294 Stream.poll_nextpid:10812:584e3330-5a3c-44c8-aa9d-a78cc3e20b4e|V��D
!ii������TRACElogWouldBlockpid:10812:584e3330-5a3c-44c8-aa9d-a78cc3e20b4e�X��C�!ii����xTRACElogC:\Users\runneradmin\.cargo\git\checkouts\tokio-tungstenite-ea4445d9acecae62\132f5b3\src\compat.rs:157 Read.with_context read -> poll_readpid:10812:584e3330-5a3c-44c8-aa9d-a78cc3e20b4e��J��B�ii����g0TRACElogC:\Users\runneradmin\.cargo\git\checkouts\tokio-tungstenite-ea4445d9acecae62\132f5b3\src\compat.rs:131 AllowStd.with_contextpid:10812:584e3330-5a3c-44c8-aa9d-a78cc3e20b4e��=��A�mii����E�TRACElogC:\Users\runneradmin\.cargo\git\checkouts\tokio-tungstenite-ea4445d9acecae62\132f5b3\src\compat.rs:154 Read.readpid:10812:584e3330-5a3c-44c8-aa9d-a78cc3e20b4ex�Y��@�#ii�����TRACElogC:\Users\runneradmin\.cargo\git\checkouts\tokio-tungstenite-ea4445d9acecae62\132f5b3\src\lib.rs:304 Stream.with_context poll_next -> read()pid:10812:584e3330-5a3c-44c8-aa9d-a78cc3e20b4e��N��?�
ii������TRACElogC:\Users\runneradmin\.cargo\git\checkouts\tokio-tungstenite-ea4445d9acecae62\132f5b3\src\lib.rs:245 WebSocketStream.with_contextpid:10812:584e3330-5a3c-44c8-aa9d-a78cc3e20b4e��A��>�uii�����TRACElogC:\Users\runneradmin\.cargo\git\checkouts\tokio-tungstenite-ea4445d9acecae62\132f5b3\src\lib.rs:294 Stream.poll_nextpid:10812:584e3330-5a3c-44c8-aa9d-a78cc3e20b4e|�[��=�'ii�����TRACElogC:\Users\runneradmin\.cargo\git\checkouts\tokio-tungstenite-ea4445d9acecae62\132f5b3\src\compat.rs:185 Write.with_context flush -> poll_flushpid:10812:584e3330-5a3c-44c8-aa9d-a78cc3e20b4e��J��<�ii����gTTRACElogC:\Users\runneradmin\.cargo\git\checkouts\tokio-tungstenite-ea4445d9acecae62\132f5b3\src\compat.rs:131 AllowStd.with_contextpid:10812:584e3330-5a3c-44c8-aa9d-a78cc3e20b4e��?��;�qii����9�TRACElogC:\Users\runneradmin\.cargo\git\checkouts\tokio-tungstenite-ea4445d9acecae62\132f5b3\src\compat.rs:183 Write.flushpid:10812:584e3330-5a3c-44c8-aa9d-a78cc3e20b4ez�[��:�'ii������TRACElogC:\Users\runneradmin\.cargo\git\checkouts\tokio-tungstenite-ea4445d9acecae62\132f5b3\src\compat.rs:174 Write.with_context write -> poll_writepid:10812:584e3330-5a3c-44c8-aa9d-a78cc3e20b4e��J��9�ii���ۼ�TRACElogC:\Users\runneradmin\.cargo\git\checkouts\tokio-tungstenite-ea4445d9acecae62\132f5b3\src\compat.rs:131 AllowStd.with_contextpid:10812:584e3330-5a3c-44c8-aa9d-a78cc3e20b4e��?��8�qii���ۚTRACElogC:\Users\runneradmin\.cargo\git\checkouts\tokio-tungstenite-ea4445d9acecae62\132f5b3\src\compat.rs:172 Write.writepid:10812:584e3330-5a3c-44c8-aa9d-a78cc3e20b4ez�N��7�
ii����s\TRACElogC:\Users\runneradmin\.cargo\git\checkouts\tokio-tungstenite-ea4445d9acecae62\132f5b3\src\lib.rs:245 WebSocketStream.with_contextpid:10812:584e3330-5a3c-44c8-aa9d-a78cc3e20b4e��W��6�ii����2�TRACElogwriting frame 
<FRAME>
final: true
reserved: false false false
opcode: PONG
length: 10
payload length: 4
payload: 0x41946a6c
            pid:10812:584e3330-5a3c-44c8-aa9d-a78cc3e20b4e����5�sii�����8TRACElogSending frame: Frame { header: FrameHeader { is_final: true, rsv1: false, rsv2: false, rsv3: false, opcode: Control(Pong), mask: Some([196, 229, 206, 70]) }, payload: b"A\x94jl" }pid:10812:584e3330-5a3c-44c8-aa9d-a78cc3e20b4e�^��4
1ii����'�TRACElogSending pong/closepid:10812:584e3330-5a3c-44c8-aa9d-a78cc3e20b4e�N��3�
ii�����TRACElogC:\Users\runneradmin\.cargo\git\checkouts\tokio-tungstenite-ea4445d9acecae62\132f5b3\src\lib.rs:245 WebSocketStream.with_contextpid:10812:584e3330-5a3c-44c8-aa9d-a78cc3e20b4e�r��2
Yii���٧4TRACElogReceived message Binary Data<length=4>pid:10812:584e3330-5a3c-44c8-aa9d-a78cc3e20b4e.
-R
��1
S	���|�\�F��-�A���uii�*�$�s�TRACElogC:\Users\runneradmin\.cargo\git\checkouts\tokio-tungstenite-ea4445d9acecae62\132f5b3\src\lib.rs:294 Stream.poll_nextpid:10788:5537a0aa-172b-431b-a455-248691d32365|�X���!ii�*�$�h�TRACElogReceived message {"type":"response.custom_tool_call_input.done","input":"
                            if not _within_window(item.published_at, date_from=date_from, date_to=date_to):U#ent=2)\r
                metadata.updat?�(hits)
   ?�yEaimM_EphALMR8GzbhwLJ2l5F9bsL6hU-9Mow8VHamCi-Ic5rEgSnt1u5HxqtifOfnbBaZFiH3VY6MRlRxDIjxFlyT1YLE5n29ZFQAgeE0tRQ2GzgHUEhcDhCguqK_h6O_fDamoQ4eevSDwXm2t3PM_i_eVRqHztxkfhPiQhTNjIA8LKwRdSaRDTNCu0RnUFdfUUYIhmdCZOQz2zTuFl2bITtZ5eRsmG-V1w4yLP8t-yMjh2Ksg9gOMAlol2NDyNo3VLaAcdpN4JhX28SU7HjvES9"},{"type":"custom_tool_call","status":"completed","call_id":"call_fChXHmU9cVtTR4or8dF4IEp2",