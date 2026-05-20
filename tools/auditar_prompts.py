"""Extrai prompts do Otávio nos transcripts JSONL do Claude Code e gera relatório
cruzado com os documentos de longo prazo do loop CCM-2026-05-19.

Uso:
    python3 tools/auditar_prompts.py [--since 2026-05-19] [--out relatorio.md]

Saída padrão: stdout (Markdown). Com --out: grava arquivo.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

PROJECTS_DIR = Path.home() / ".claude" / "projects" / "-home-otavio-Documents-vscode"
LOOP_DIR = Path("/home/otavio/Documents/vscode/clipping-project/md documents/clipping-client-management-loop-2026-05-19")
LOOP_DOCS = {
    "LONG_TERM_GOALS.md": LOOP_DIR / "LONG_TERM_GOALS.md",
    "MANTRA.md": LOOP_DIR / "MANTRA.md",
    "WORK_LOG_MAJOR.md": LOOP_DIR / "WORK_LOG_MAJOR.md",
    "GOALS_ATINGIDOS.md": LOOP_DIR / "GOALS_ATINGIDOS.md",
}

CLIPPING_KEYWORDS = re.compile(
    r"clipping|target|viewer|admin|dashboard|render|flavio|shakira|"
    r"rio.economic|senha|password|logout|onboarding|simulate|segrega|"
    r"perfil|profile|csrf|deploy|prod|payload|stories|news|notici|mantra",
    re.IGNORECASE,
)
COMMAND_RE = re.compile(r"^<command-name>", re.MULTILINE)
SYSTEM_REMINDER_RE = re.compile(r"^<system-reminder>", re.MULTILINE)
LOCAL_CAVEAT_RE = re.compile(r"<local-command-caveat>")


@dataclass
class Prompt:
    timestamp: str
    session_id: str
    cwd: str
    text: str
    slug: str = ""

    @property
    def dt(self) -> datetime:
        return datetime.fromisoformat(self.timestamp.replace("Z", "+00:00"))

    @property
    def short(self) -> str:
        snippet = self.text.strip().replace("\n", " ")
        return snippet[:200] + ("…" if len(snippet) > 200 else "")


def extract_text_content(content) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for block in content:
            if not isinstance(block, dict):
                continue
            if block.get("type") == "text":
                parts.append(str(block.get("text") or ""))
        return "\n".join(parts).strip()
    return ""


def is_real_prompt(text: str) -> bool:
    """Filtra mensagens que são realmente prompts do humano,
    não system-reminders, tool results, ou commands de slash internas."""
    if not text.strip():
        return False
    if SYSTEM_REMINDER_RE.search(text) and len(text) < 500:
        return False
    if text.strip().startswith("Caveat:"):
        return False
    # Slash-commands locais (/compact, /clear) costumam vir embrulhados
    if text.strip().startswith("<command-name>") and "</command-name>" in text:
        return False
    if "<command-stdout>" in text and len(text) < 300:
        return False
    return True


def load_prompts(jsonl_path: Path) -> list[Prompt]:
    prompts: list[Prompt] = []
    try:
        fh = jsonl_path.open("r", encoding="utf-8")
    except OSError:
        return prompts
    with fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            if record.get("type") != "user":
                continue
            message = record.get("message") or {}
            if message.get("role") != "user":
                continue
            text = extract_text_content(message.get("content"))
            # Pula tool_result wrappers
            if not text:
                continue
            if not is_real_prompt(text):
                continue
            prompts.append(
                Prompt(
                    timestamp=str(record.get("timestamp") or ""),
                    session_id=str(record.get("sessionId") or jsonl_path.stem),
                    cwd=str(record.get("cwd") or ""),
                    text=text,
                    slug=str(record.get("slug") or ""),
                )
            )
    return prompts


def filter_clipping_relevant(prompts: list[Prompt]) -> list[Prompt]:
    out: list[Prompt] = []
    for p in prompts:
        if "clipping" in p.cwd.lower():
            out.append(p)
            continue
        if CLIPPING_KEYWORDS.search(p.text):
            out.append(p)
    return out


def load_doc(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""


def keyword_count(text: str, pattern: re.Pattern[str]) -> int:
    return len(pattern.findall(text))


def report(prompts: list[Prompt], since: datetime | None) -> str:
    if since is not None:
        prompts = [p for p in prompts if p.dt >= since]
    prompts.sort(key=lambda p: p.dt)

    lines: list[str] = []
    lines.append("# Auditoria de Prompts vs Documentos de Longo Prazo")
    lines.append("")
    lines.append(f"**Gerado:** {datetime.now(timezone.utc).isoformat()}")
    lines.append(f"**Prompts capturados:** {len(prompts)}")
    if prompts:
        lines.append(f"**Janela temporal:** {prompts[0].timestamp} → {prompts[-1].timestamp}")
    lines.append("")

    by_session: dict[str, list[Prompt]] = {}
    for p in prompts:
        by_session.setdefault(p.session_id, []).append(p)
    lines.append("## Distribuição por sessão")
    lines.append("")
    for sid, items in sorted(by_session.items(), key=lambda kv: kv[1][0].dt):
        lines.append(f"- `{sid}` ({len(items)} prompts) — slug: `{items[0].slug or '—'}`")
    lines.append("")

    lines.append("## Prompts em ordem cronológica")
    lines.append("")
    for idx, p in enumerate(prompts, 1):
        lines.append(f"### #{idx} — {p.timestamp}")
        lines.append(f"**Sessão:** `{p.session_id}` · **cwd:** `{p.cwd}`")
        lines.append("")
        lines.append("```text")
        # Limita a 1200 chars para o relatório ser navegável
        body = p.text.strip()
        if len(body) > 1200:
            body = body[:1200] + "\n… [truncado]"
        lines.append(body)
        lines.append("```")
        lines.append("")

    # Temas extraídos via heurística
    lines.append("## Temas recorrentes (heurística de keywords)")
    lines.append("")
    themes = {
        "Adicionar target / segregação de view": re.compile(r"(adicionar|adicione).*(target|viewer|perfil|segreg|view)|segrega", re.IGNORECASE | re.DOTALL),
        "Logout / trocar senha": re.compile(r"logout|trocar.*senha|change.password", re.IGNORECASE),
        "Senha simples / comunicável": re.compile(r"senha.*simples|simplif.*senha|wpp|whatsapp.*senha", re.IGNORECASE),
        "Regressão / quebra de feature antiga": re.compile(r"regress|quebr|sumiu|sumiram|destruiu|destruir|n[ãa]o consigo", re.IGNORECASE),
        "Erro claro / mensagens de erro": re.compile(r"erro.*claro|mensagem.*erro|spinner|something went wrong", re.IGNORECASE),
        "Não parar / autonomia": re.compile(r"n[ãa]o.*par(e|ar|ou)|continue|n[ãa]o.*pare", re.IGNORECASE),
        "Ler/repetir mantra": re.compile(r"mantra|repetir|repeat.*mantra", re.IGNORECASE),
        "Commit local / push": re.compile(r"commit.*local|nunca.*commit|push|deploy", re.IGNORECASE),
        "Raiva / regressão funcional": re.compile(r"(raiva|infuri|caralho|porra|merda|filho da puta)", re.IGNORECASE),
    }
    for theme, pat in themes.items():
        matches = [p for p in prompts if pat.search(p.text)]
        lines.append(f"### {theme} — {len(matches)} prompts")
        for p in matches[:6]:
            lines.append(f"- `{p.timestamp[:19]}` — {p.short}")
        if len(matches) > 6:
            lines.append(f"- … (+{len(matches)-6} mais)")
        lines.append("")

    # Comparação contra docs
    lines.append("## Cruzamento com documentos de longo prazo")
    lines.append("")
    for name, path in LOOP_DOCS.items():
        text = load_doc(path)
        lines.append(f"### {name}")
        if not text:
            lines.append("⚠️ Documento não pôde ser lido.")
            lines.append("")
            continue
        lines.append(f"- Tamanho: {len(text):,} chars · {text.count(chr(10))+1} linhas")
        for theme, pat in themes.items():
            occ = keyword_count(text, pat)
            prompt_occ = sum(1 for p in prompts if pat.search(p.text))
            if prompt_occ or occ:
                lines.append(f"  - **{theme}** — prompts: {prompt_occ} · doc: {occ}")
        lines.append("")

    return "\n".join(lines) + "\n"


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--since", default="2026-05-19", help="ISO date — só prompts a partir daqui (default 2026-05-19, início do loop CCM)")
    ap.add_argument("--out", default="", help="Caminho do arquivo de saída (default stdout)")
    ap.add_argument("--all", action="store_true", help="Não filtrar por clipping-relevant — exporta tudo")
    args = ap.parse_args(argv)

    since: datetime | None = None
    if args.since:
        since = datetime.fromisoformat(args.since + "T00:00:00+00:00")

    if not PROJECTS_DIR.is_dir():
        print(f"Diretório não encontrado: {PROJECTS_DIR}", file=sys.stderr)
        return 2

    all_prompts: list[Prompt] = []
    for jsonl in sorted(PROJECTS_DIR.glob("*.jsonl")):
        all_prompts.extend(load_prompts(jsonl))

    if not args.all:
        all_prompts = filter_clipping_relevant(all_prompts)

    text = report(all_prompts, since=since)
    if args.out:
        Path(args.out).write_text(text, encoding="utf-8")
        print(f"OK — gravado em {args.out} ({len(text):,} chars)")
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
