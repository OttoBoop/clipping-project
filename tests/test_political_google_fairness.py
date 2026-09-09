"""Every person reaches Google discovery before another alias/window round."""
from web_app.political_discovery import _google_tasks,build_tasks


def test_primary_queries_interleave_all_people_before_next_window_and_alias():
    targets=[{'key':'first','display_name':'Pessoa Primeira','keywords':['Primeira A','Primeira B','Primeira C']},
             {'key':'second','display_name':'Pessoa Segunda','keywords':['Segunda A']},
             {'key':'third','display_name':'Pessoa Terceira','keywords':[]}]
    tasks=_google_tasks(targets,{'key':'google_news'},'2026-06-01','2026-06-14')
    assert [(r['target_ids'],r['date_from']) for r in tasks[:6]]==[
        ([key],day) for day in ['2026-06-01','2026-06-08'] for key in ['first','second','third']]
    assert all(r['query'].startswith('"Pessoa ') for r in tasks[:6])
    assert tasks[6]['query']=='"Primeira A"' and tasks[7]['query']=='"Segunda A"'
    assert len(tasks)==14
    assert len({(r['query'],r['date_from'],r['date_to']) for r in tasks})==14


def test_shared_accent_alias_dedup_preserves_query_payload_and_all_target_associations():
    targets=[{'key':'first','display_name':'Nome Primeiro','keywords':['Nome Compartilhado']},
             {'key':'second','display_name':'Nome Compártilhado','keywords':['Nome Compártilhado']}]
    tasks=_google_tasks(targets,{'key':'rc24h','domain':'rc24h.com.br'},'2026-06-01','2026-06-08')
    # The first-seen spelling and merged IDs are the same as the previous queue
    # protocol; only order changes when an alias is another person's primary name.
    expected=[]
    for query,ids in [('"Nome Primeiro" site:rc24h.com.br',['first']),
                      ('"Nome Compartilhado" site:rc24h.com.br',['first','second'])]:
        for start,stop in [('2026-06-01','2026-06-07'),('2026-06-08','2026-06-08')]:
            expected.append({'source_key':'rc24h','strategy':'google_news','cursor':{},'query':query,
                             'target_ids':ids,'date_from':start,'date_to':stop})
    assert all(task in expected for task in tasks) and len(tasks)==len(expected)
    assert [r['target_ids'] for r in tasks[:2]]==[['first'],['first','second']]


def test_real_24_target_job_gets_one_primary_query_per_person_before_second_window():
    targets=[{'key':f'target_{i}','display_name':f'Pessoa Completa {i}',
              'keywords':[f'Nome Alternativo {i}',f'Apelido {i}']} for i in range(24)]
    tasks=build_tasks(targets,'2026-06-01','2026-06-30',source_keys=['google_news'])
    assert {r['target_ids'][0] for r in tasks[:24]}=={r['key'] for r in targets}
    assert {r['date_from'] for r in tasks[:24]}=={'2026-06-01'}
    assert {r['date_from'] for r in tasks[24:48]}=={'2026-06-08'}
    assert len(tasks)==24*3*5
