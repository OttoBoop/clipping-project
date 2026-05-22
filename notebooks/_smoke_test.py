"""Smoke test do Diarios_Oficiais_Rio_Downloader.ipynb.

Carrega as funcoes definidas no notebook (sem a celula de configuracao nem o runner)
e roda 3-4 cenarios reais. Saida via stdout com tags OK/FAIL pro workflow ler.

Roda no GitHub Actions (egress aberto). Localmente no sandbox do Anthropic, falha
no proxy. Esperado.
"""
import json
import os
import sys
import traceback
import datetime

NB_PATH = os.environ.get("NB_PATH", "notebooks/Diarios_Oficiais_Rio_Downloader.ipynb")
DESTINO = os.environ.get("DESTINO", "downloads_smoke")

os.makedirs(DESTINO, exist_ok=True)
print(f"[smoke] notebook = {NB_PATH}")
print(f"[smoke] destino  = {os.path.abspath(DESTINO)}")

nb = json.load(open(NB_PATH))
code_to_run = ""
for c in nb["cells"]:
    if c["cell_type"] != "code":
        continue
    src = "".join(c["source"])
    # pular celula de configuracao - definimos manualmente abaixo
    if "O QUE BAIXAR" in src:
        continue
    # pular runner (chama variaveis MODO/FONTE) e bloco final do pandas
    if "def rodar():" in src or "linhas = []" in src:
        continue
    # pular installs comentados
    if src.lstrip().startswith("# !pip install"):
        continue
    code_to_run += src + "\n\n"

ns = {"DESTINO": DESTINO}
print(f"[smoke] carregando {len(code_to_run)} chars de codigo do notebook...")
exec(code_to_run, ns)
print("[smoke] codigo carregado.")

# Patch para o ambiente do GitHub Actions: o runner tem chromium-browser, nao
# google-chrome, e o chromedriver procura /usr/bin/google-chrome por padrao.
# Como sobrescrevemos _dcm_novo_driver no mesmo namespace, todas as funcoes
# DCM (baixar_dcm_hoje, baixar_dcm_edicao) passam a usa-lo.
import shutil as _shutil
_chrome_bin = _shutil.which("google-chrome") or _shutil.which("google-chrome-stable")
if not _chrome_bin:
    _chromium_bin = _shutil.which("chromium-browser") or _shutil.which("chromium")
    if _chromium_bin:
        print(f"[smoke] patch: forcando binary_location={_chromium_bin}")
        def _patched_driver():
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options as ChromeOptions
            opts = ChromeOptions()
            for arg in ("--headless", "--no-sandbox", "--disable-dev-shm-usage",
                        "--disable-gpu", "--window-size=1920,1080"):
                opts.add_argument(arg)
            opts.binary_location = _chromium_bin
            return webdriver.Chrome(options=opts)
        ns["_dcm_novo_driver"] = _patched_driver
    else:
        print("[smoke] AVISO: nem google-chrome nem chromium encontrados; DCM vai falhar.")


def is_pdf(path):
    if not path or not os.path.exists(path):
        return False
    with open(path, "rb") as f:
        magic = f.read(5)
    return magic == b"%PDF-"


def run_cenario(nome, fn, *args, **kwargs):
    print(f"\n========== CENARIO: {nome} ==========")
    inicio = datetime.datetime.now()
    try:
        saida = fn(*args, destino=DESTINO, **kwargs) if "destino" not in kwargs else fn(*args, **kwargs)
    except TypeError:
        # algumas funcoes recebem destino como posicional
        try:
            saida = fn(*args, DESTINO)
        except Exception as e:
            traceback.print_exc()
            return (nome, False, f"raise {type(e).__name__}: {e}")
    except Exception as e:
        traceback.print_exc()
        return (nome, False, f"raise {type(e).__name__}: {e}")
    dur = (datetime.datetime.now() - inicio).total_seconds()

    if isinstance(saida, list):
        # range: lista de paths
        ok = all(is_pdf(p) for p in saida) and len(saida) > 0
        print(f"  -> range com {len(saida)} arquivos, todos PDF? {ok} ({dur:.1f}s)")
        for p in saida:
            tam = os.path.getsize(p) if os.path.exists(p) else 0
            print(f"     - {os.path.basename(p)} {tam/1024/1024:.2f} MB  pdf={is_pdf(p)}")
        return (nome, ok, f"{len(saida)} arquivos em {dur:.1f}s")
    else:
        ok = is_pdf(saida)
        tam = os.path.getsize(saida) if saida and os.path.exists(saida) else 0
        print(f"  -> {saida}  {tam/1024/1024:.2f} MB  pdf={ok}  ({dur:.1f}s)")
        return (nome, ok, f"{tam} bytes em {dur:.1f}s")


resultados = []

# --- DOP ---
resultados.append(run_cenario("DOP_hoje", ns["baixar_dop_hoje"]))

# --- DCM ---
resultados.append(run_cenario("DCM_hoje", ns["baixar_dcm_hoje"]))

# --- DCM edicao especifica (ano corrente, primeira edicao - costuma existir) ---
ano = datetime.date.today().year
resultados.append(run_cenario(f"DCM_edicao_1_{ano}", ns["baixar_dcm_edicao"], ano, 1))

# --- DCM range curto (2 edicoes) ---
resultados.append(run_cenario(f"DCM_range_1a2_{ano}", ns["baixar_dcm_range"], ano, 1, 2))


print("\n\n========== RESUMO ==========")
sucesso_total = True
for nome, ok, detalhe in resultados:
    flag = "OK  " if ok else "FAIL"
    print(f"  [{flag}] {nome:30s} {detalhe}")
    sucesso_total = sucesso_total and ok

print(f"\n========== ARQUIVOS EM {DESTINO} ==========")
for f in sorted(os.listdir(DESTINO)):
    full = os.path.join(DESTINO, f)
    print(f"  {os.path.getsize(full)/1024/1024:8.2f} MB  {f}")

sys.exit(0 if sucesso_total else 1)
