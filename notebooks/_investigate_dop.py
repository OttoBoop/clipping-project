"""Investiga o portal DOP pra descobrir como baixar edições antigas.

Roda no CI (GitHub Actions) onde tem egress aberto.
Resultado salvo em notebooks/_investigate_dop_results.json.
"""
import json
import os
import re
import datetime
import requests

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0 Safari/537.36")
HEADERS = {"User-Agent": UA}
BASE = "https://doweb.rio.rj.gov.br"
RESULTS = {}


def probe(label, url, **kwargs):
    print(f"\n--- {label} ---")
    print(f"  URL: {url}")
    try:
        r = requests.get(url, headers=HEADERS, timeout=20, **kwargs)
        info = {
            "status": r.status_code,
            "content_type": r.headers.get("Content-Type", ""),
            "body_preview": r.text[:1000] if "text" in r.headers.get("Content-Type", "") or
                            "json" in r.headers.get("Content-Type", "") or
                            "html" in r.headers.get("Content-Type", "") else f"[binary {len(r.content)} bytes]",
            "headers": dict(r.headers),
        }
        # Tenta parsear JSON
        try:
            info["json"] = r.json()
        except Exception:
            pass
        print(f"  Status: {r.status_code} | Content-Type: {info['content_type']}")
        print(f"  Body: {info['body_preview'][:200]}")
        RESULTS[label] = info
        return r
    except Exception as e:
        info = {"error": f"{type(e).__name__}: {e}"}
        print(f"  ERRO: {info['error']}")
        RESULTS[label] = info
        return None


# 1. Home — pegar DADOS_ULTIMA_DATA e qualquer outra variável JS
print("=" * 60)
print("FASE 1: Home do DOP")
print("=" * 60)
r_home = probe("home", BASE)
if r_home and r_home.status_code == 200:
    html = r_home.text
    # Extrair todas as variáveis JS "let X = ..."
    js_vars = re.findall(r"let\s+(\w+)\s*=\s*(\{.*?\});", html, re.DOTALL)
    RESULTS["home_js_vars"] = {name: val[:500] for name, val in js_vars}
    print(f"\n  Variáveis JS encontradas: {[name for name, _ in js_vars]}")

    # Extrair links/URLs internas
    links = set(re.findall(r'href="(/[^"]+)"', html))
    RESULTS["home_links"] = sorted(links)[:50]
    print(f"  Links internos: {len(links)} encontrados")

    # Extrair DADOS_ULTIMA_DATA
    m = re.search(r"let DADOS_ULTIMA_DATA = (\{.*?\});", html, re.DOTALL)
    if m:
        dados = json.loads(m.group(1))
        RESULTS["dados_ultima_data"] = dados
        itens = dados.get("itens", [])
        print(f"\n  DADOS_ULTIMA_DATA: {len(itens)} itens")
        for item in itens[:3]:
            print(f"    {json.dumps(item, ensure_ascii=False)[:200]}")

# 2. Endpoint apifront — existe?
print("\n" + "=" * 60)
print("FASE 2: Testar endpoints /apifront/")
print("=" * 60)

ontem = (datetime.date.today() - datetime.timedelta(days=1)).isoformat()
semana = (datetime.date.today() - datetime.timedelta(days=7)).isoformat()

probe("apifront_from_data_query", f"{BASE}/apifront/portal/edicoes/edicoes_from_data/?data={ontem}")
probe("apifront_from_data_path", f"{BASE}/apifront/portal/edicoes/edicoes_from_data/{ontem}")
probe("apifront_from_data_noarg", f"{BASE}/apifront/portal/edicoes/edicoes_from_data/")
probe("apifront_edicoes", f"{BASE}/apifront/portal/edicoes/")
probe("apifront_portal", f"{BASE}/apifront/portal/")

# 3. Home com parâmetro de data — muda DADOS_ULTIMA_DATA?
print("\n" + "=" * 60)
print("FASE 3: Home com parâmetro de data")
print("=" * 60)

for param in [f"?data={ontem}", f"?data={semana}", f"?edicao={ontem}"]:
    r = probe(f"home{param}", f"{BASE}/{param}")
    if r and r.status_code == 200:
        m = re.search(r"let DADOS_ULTIMA_DATA = (\{.*?\});", r.text, re.DOTALL)
        if m:
            dados = json.loads(m.group(1))
            itens = dados.get("itens", [])
            RESULTS[f"home{param}_itens"] = itens[:3]
            print(f"  DADOS_ULTIMA_DATA com {param}: {len(itens)} itens")

# 4. IDs sequenciais — testar download com IDs próximos ao atual
print("\n" + "=" * 60)
print("FASE 4: IDs sequenciais no download")
print("=" * 60)

id_atual = None
if "dados_ultima_data" in RESULTS:
    itens = RESULTS["dados_ultima_data"].get("itens", [])
    for item in itens:
        if item.get("suplemento", "") == "":
            id_atual = item.get("id")
            break

if id_atual:
    print(f"  ID atual (caderno principal): {id_atual}")
    # Testa IDs próximos: atual-1, atual-2, ..., atual-5
    for delta in range(-1, -6, -1):
        test_id = id_atual + delta
        url = f"{BASE}/portal/edicoes/download/{test_id}"
        r = probe(f"download_id_{test_id}", url, allow_redirects=True, stream=True)
        if r and r.status_code == 200:
            ct = r.headers.get("Content-Type", "")
            cd = r.headers.get("Content-Disposition", "")
            cl = r.headers.get("Content-Length", "?")
            RESULTS[f"download_id_{test_id}"]["content_disposition"] = cd
            RESULTS[f"download_id_{test_id}"]["content_length"] = cl
            RESULTS[f"download_id_{test_id}"]["body_preview"] = f"[PDF stream, Content-Length={cl}]"
            print(f"    Content-Disposition: {cd}")
            print(f"    Content-Length: {cl}")
        r.close() if r else None
else:
    print("  Não consegui extrair ID atual da home.")
    RESULTS["download_sequential"] = "skipped — no id_atual"

# 5. Busca nova
print("\n" + "=" * 60)
print("FASE 5: /buscanova/")
print("=" * 60)
probe("buscanova", f"{BASE}/buscanova/")

# 6. Páginas de edição
print("\n" + "=" * 60)
print("FASE 6: Outras rotas")
print("=" * 60)
probe("portal_edicoes", f"{BASE}/portal/edicoes/")
if id_atual:
    probe("portal_ver", f"{BASE}/portal/edicoes/ver/{id_atual}/1/conteudo")

# Salvar resultados
out_path = os.path.join(os.path.dirname(__file__) or ".", "_investigate_dop_results.json")
with open(out_path, "w") as f:
    json.dump(RESULTS, f, indent=2, ensure_ascii=False, default=str)
print(f"\n\nResultados salvos em {out_path}")
print(f"Total de probes: {len(RESULTS)}")
