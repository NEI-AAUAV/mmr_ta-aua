# -*- coding: utf-8 -*-
"""
Fonte de resultados da Taça UA a partir da API pública de https://tacaua.aauav.pt/.

A partir da época 2026/2027 os resultados deixam de ser publicados em Excel.
Este módulo descarrega os jogos da API e gera os mesmos CSVs por modalidade
que o ExcelProcessor produz (docs/output/csv_modalidades/<MODALIDADE>_<YY_YY>.csv).
"""

import csv
import hashlib
import json
import logging
import re
import time
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional
from zoneinfo import ZoneInfo

API_BASE_URL = "https://tacaua.aauav.pt/api/public"
API_PAGE_SIZE = 100  # máximo aceite pela API
API_TIMEOUT_SECONDS = 30
API_RETRIES = 3
LISBON_TZ = ZoneInfo("Europe/Lisbon")

# Colunas do CSV legado; Divisão/Grupo são inseridos a seguir a "Equipa 2".
CSV_BASE_HEADERS = [
    "Jornada",
    "Dia",
    "Hora",
    "Local",
    "Equipa 1",
    "Golos 1",
    "Golos 2",
    "Equipa 2",
    "Fonte_Data",
    "Fonte_Local",
    "Data_Placeholder",
    "Local_Placeholder",
    "Falta de Comparência",
]
_DIVISION_HEADERS = ["Divisão", "Grupo"]

_DIVISION_RE = re.compile(r"(\d)\s*[ªº]\s*divis[ãa]o", re.IGNORECASE)
_GROUP_RE = re.compile(r"grupo\s+([A-Z])\b", re.IGNORECASE)
_SEASON_RE = re.compile(r"(\d{4})\s*[/_-]\s*(\d{4})")

Getter = Callable[[str, Dict[str, Any]], Dict[str, Any]]


# ── Descarregamento ──────────────────────────────────────────────────────────


def _http_get_json(url: str, params: Dict[str, Any]) -> Dict[str, Any]:
    import requests

    last_error: Optional[Exception] = None
    for attempt in range(1, API_RETRIES + 1):
        try:
            response = requests.get(url, params=params, timeout=API_TIMEOUT_SECONDS)
            response.raise_for_status()
            return response.json()
        except Exception as exc:  # rede, HTTP ou JSON inválido
            last_error = exc
            logging.warning("API Taça UA (tentativa %d/%d): %s", attempt, API_RETRIES, exc)
            time.sleep(2 * attempt)
    raise RuntimeError(f"Falha ao consultar {url}: {last_error}")


def fetch_all(
    path: str,
    getter: Getter = _http_get_json,
    page_size: int = API_PAGE_SIZE,
    base_url: str = API_BASE_URL,
) -> List[Dict[str, Any]]:
    """Percorre todas as páginas de um endpoint de listagem."""
    items: List[Dict[str, Any]] = []
    page = 1
    while True:
        payload = getter(f"{base_url}{path}", {"page": page, "page_size": page_size})
        page_items = payload.get("items") or []
        items.extend(page_items)
        total = payload.get("total", len(items))
        if not page_items or len(items) >= total:
            return items
        page += 1


def season_token_from_name(name: str) -> Optional[str]:
    """'Época 2026/2027' -> '26_27'."""
    match = _SEASON_RE.search(name or "")
    if not match:
        return None
    return f"{match.group(1)[2:]}_{match.group(2)[2:]}"


def fetch_active_season(
    getter: Getter = _http_get_json, base_url: str = API_BASE_URL
) -> Optional[str]:
    seasons = fetch_all("/seasons", getter=getter, base_url=base_url)
    active = [s for s in seasons if s.get("is_active")] or seasons
    for season in active:
        token = season_token_from_name(season.get("name", ""))
        if token:
            return token
    return None


def snapshot_hash(matches: List[Dict[str, Any]]) -> str:
    canonical = json.dumps(matches, sort_keys=True, ensure_ascii=False)
    return hashlib.md5(canonical.encode("utf-8")).hexdigest()


# ── Conversão para o formato dos CSVs ────────────────────────────────────────


def _sheet_name(modality: str) -> str:
    """'Futebol 7 Masculino' -> 'FUTEBOL DE 7 MASCULINO' (nome legado da folha)."""
    name = re.sub(r"\s+", " ", modality.strip()).upper()
    return re.sub(r"^FUTEBOL (\d)", r"FUTEBOL DE \1", name)


def _team_name(name: str, aliases: Dict[str, str]) -> str:
    """Aplica aliases explícitos (ex.: 'EGI A' -> 'EGI', nome usado no histórico)."""
    clean = name.strip()
    return aliases.get(clean, clean)


def load_aliases(path: str | Path) -> Dict[str, str]:
    path = Path(path)
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def load_overrides(path: str | Path) -> Dict[tuple[str, str, str], str]:
    """Faltas de comparência conhecidas: Modalidade,Equipa 1,Equipa 2,Falta de Comparência."""
    path = Path(path)
    if not path.exists():
        return {}
    with open(path, encoding="utf-8", newline="") as handle:
        return {
            (r["Modalidade"].strip().upper(), r["Equipa 1"].strip(), r["Equipa 2"].strip()): r[
                "Falta de Comparência"
            ].strip()
            for r in csv.DictReader(handle)
        }


REQUIRED_MATCH_KEYS = ("match_id", "status", "start_time", "modality_name", "participants", "results")


def validate_matches(matches: List[Dict[str, Any]]) -> None:
    """Falha cedo se a API mudar de esquema, em vez de gerar CSVs errados."""
    for match in matches:
        missing = [k for k in REQUIRED_MATCH_KEYS if k not in match]
        if missing:
            raise ValueError(
                f"Esquema da API mudou: jogo {match.get('match_id')} sem campos {missing}"
            )
        for participant in match["participants"]:
            if "participant_id" not in participant or "participant_name" not in participant:
                raise ValueError(
                    f"Esquema da API mudou: participante inválido no jogo {match['match_id']}"
                )


SUPPORTED_FORMATS = {"league", "free"}


def unsupported_tournaments(tournaments: List[Dict[str, Any]]) -> List[str]:
    """Torneios com formato ainda não tratado (ex.: playoffs)."""
    return [
        f"{t.get('tournament_name')} ({t.get('format')})"
        for t in tournaments
        if t.get("format") not in SUPPORTED_FORMATS
    ]


def known_teams(csv_dir: str | Path, exclude_season: str) -> set:
    """Nomes de equipa vistos em CSVs de outras épocas."""
    names: set = set()
    for path in Path(csv_dir).glob("*.csv"):
        if path.stem.endswith(exclude_season):
            continue
        with open(path, encoding="utf-8", newline="") as handle:
            for row in csv.DictReader(handle):
                names.update(filter(None, (row.get("Equipa 1"), row.get("Equipa 2"))))
    return names


def unknown_teams(tables: Dict[str, List[Dict[str, Any]]], known: set) -> List[str]:
    seen = {r[k] for rows in tables.values() for r in rows for k in ("Equipa 1", "Equipa 2")}
    return sorted(seen - known) if known else []


def prune_stale_csvs(
    tables: Dict[str, List[Dict[str, Any]]], season: str, output_dir: str | Path
) -> List[Path]:
    """Remove CSVs da época que a API não devolveu (cópias de épocas anteriores)."""
    removed = []
    keep = {f"{sheet}_{season}.csv" for sheet in tables}
    for path in Path(output_dir).glob(f"*_{season}.csv"):
        if path.name not in keep:
            path.unlink()
            removed.append(path)
            logging.warning("CSV sem dados na API removido: %s", path.name)
    return removed


def _score(match: Dict[str, Any], participant_id: str) -> Any:
    if match.get("status") != "finished":
        return ""
    for result in match.get("results") or []:
        if result.get("participant_id") == participant_id:
            score = result.get("score")
            return "" if score is None else int(score)
    return ""


def _parse_division_group(tournament: str) -> tuple[Any, str]:
    division = _DIVISION_RE.search(tournament or "")
    group = _GROUP_RE.search(tournament or "")
    return (
        int(division.group(1)) if division else "",
        group.group(1).upper() if group else "",
    )


def _is_team_match(match: Dict[str, Any]) -> bool:
    participants = match.get("participants") or []
    return len(participants) == 2 and all(
        p.get("participant_type") == "team" for p in participants
    )


def matches_to_tables(
    matches: List[Dict[str, Any]],
    aliases: Optional[Dict[str, str]] = None,
    overrides: Optional[Dict[tuple[str, str, str], str]] = None,
) -> Dict[str, List[Dict[str, Any]]]:
    """Converte jogos da API em linhas por modalidade (nova estrutura, input intacto)."""
    aliases = aliases or {}
    overrides = overrides or {}
    team_matches = []
    for match in matches:
        if _is_team_match(match):
            team_matches.append(match)
        else:
            logging.info(
                "Jogo ignorado (não é equipa vs equipa): %s / %s",
                match.get("modality_name"),
                match.get("match_id"),
            )

    ordered = sorted(
        team_matches, key=lambda m: (m.get("start_time") or "", m.get("match_id") or "")
    )

    last_round: Dict[tuple[str, str], int] = defaultdict(int)
    tables: Dict[str, List[Dict[str, Any]]] = defaultdict(list)

    for match in ordered:
        home, away = match["participants"]
        tournament = match.get("tournament_name") or ""
        key_home = (tournament, home["participant_id"])
        key_away = (tournament, away["participant_id"])
        jornada = max(last_round[key_home], last_round[key_away]) + 1
        last_round[key_home] = last_round[key_away] = jornada

        local_start = datetime.fromisoformat(
            match["start_time"].replace("Z", "+00:00")
        ).astimezone(LISBON_TZ)
        division, group = _parse_division_group(tournament)

        sheet = _sheet_name(match.get("modality_name") or "")
        team1 = _team_name(home["participant_name"], aliases)
        team2 = _team_name(away["participant_name"], aliases)
        tables[sheet].append(
            {
                "Jornada": jornada,
                "Dia": local_start.strftime("%Y-%m-%d 00:00:00"),
                "Hora": local_start.strftime("%Hh%M"),
                "Local": match.get("location") or "",
                "Equipa 1": team1,
                "Golos 1": _score(match, home["participant_id"]),
                "Golos 2": _score(match, away["participant_id"]),
                "Equipa 2": team2,
                "Divisão": division,
                "Grupo": group,
                "Fonte_Data": "API",
                "Fonte_Local": "API",
                "Data_Placeholder": False,
                "Local_Placeholder": False,
                "Falta de Comparência": overrides.get((sheet, team1, team2), ""),
            }
        )
    return dict(tables)


def write_tables(
    tables: Dict[str, List[Dict[str, Any]]], season: str, output_dir: str | Path
) -> List[Path]:
    """Escreve <MODALIDADE>_<season>.csv com o cabeçalho legado."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    written: List[Path] = []
    for sheet, rows in sorted(tables.items()):
        has_division = any(r["Divisão"] != "" for r in rows)
        has_group = any(r["Grupo"] != "" for r in rows)
        extra = (["Divisão"] if has_division else []) + (["Grupo"] if has_group else [])
        headers = CSV_BASE_HEADERS[:8] + extra + CSV_BASE_HEADERS[8:]
        path = output_dir / f"{sheet}_{season}.csv"
        with open(path, "w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=headers, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(rows)
        written.append(path)
        logging.info("CSV escrito: %s (%d jogos)", path.name, len(rows))
    return written
