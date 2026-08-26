# -*- coding: utf-8 -*-
"""
Sistema de Previsão de Competições Desportivas (Taçaua)

OTIMIZAÇÕES DE PERFORMANCE IMPLEMENTADAS:
==========================================
✓ ProcessPoolExecutor: Substitui ThreadPoolExecutor para superar o Python GIL
  - 5-10x speedup em operações CPU-bound (simulações Monte Carlo)
  - Utiliza todos os cores da CPU eficientemente

✓ Progress Tracking Simplificado: Otimizado para multiprocessing
  - Usa multiprocessing.Manager() para shared state entre processos
  - Progress bar limpa e atualizada in-place (reduz overhead de I/O)

✓ Serialização Adequada: Dados preparados como primitivos/tuplas
  - Objetos são reconstruídos em cada worker process
  - Evita problemas de pickling complexo

✓ Probabilidade de Empate Dinâmica: Baseada em diferença de ELO
  - Usa distribuição gaussiana: p_draw(elo_diff) = peak * exp(-(elo_diff²)/(2*sigma²))
  - Empates mais prováveis quando ELOs são similares
  - Taxa histórica de empates define a média, não probabilidade constante

MELHORIAS FUTURAS SUGERIDAS:
============================
→ joblib: Biblioteca otimizada para ML pipelines
  - from joblib import Parallel, delayed
  - results = Parallel(n_jobs=-1)(delayed(worker)(args) for args in tasks)
  - Vantagens: caching inteligente, progress bar integrado, melhor gestão de memória

→ Benchmark: Comparar tempos antes/depois com timeit ou time.perf_counter()
→ Tuning: Ajustar max_workers baseado no tipo de CPU (P-cores vs E-cores)
"""

import math
import random
import json
import functools
import logging
import numpy as np
from dataclasses import dataclass, field
from pathlib import Path
from collections import defaultdict
from typing import List, Tuple, Dict, Set, Sequence, Any
from typing import TypedDict
import csv
import os
from datetime import datetime
import sys
import io
import locale
import re
import multiprocessing
import gc
from concurrent.futures import ProcessPoolExecutor

logger = logging.getLogger(__name__)

# Configurar encoding UTF-8 para Windows
if sys.platform == "win32":
    # Forçar UTF-8 em stdout e stderr
    sys.stdout = io.TextIOWrapper(
        sys.stdout.buffer, encoding="utf-8", line_buffering=True
    )
    sys.stderr = io.TextIOWrapper(
        sys.stderr.buffer, encoding="utf-8", line_buffering=True
    )

    # Tentar configurar locale para português
    try:
        locale.setlocale(locale.LC_ALL, "pt_PT.UTF-8")
    except Exception:
        try:
            locale.setlocale(locale.LC_ALL, "pt_PT")
        except Exception:
            pass


# ============================================================================
# CONSTANTES GLOBAIS
# ============================================================================

# --- Sistema ELO ---
ELO_DIVISOR: float = 250.0  # Denominador da fórmula logística ELO
ELO_K_BASE: float = 100.0  # K-factor base padrão
ELO_SCALE_NORMALIZED: float = 8.0  # Escala normalizada para número de jogos

# Multiplicadores de fase de época
PHASE_MULT_E3L: float = 0.75  # Jogo do 3.º lugar (E3L)
PHASE_MULT_PLAYOFFS: float = 1.5  # Playoffs / eliminatórias
PHASE_EARLY_THRESHOLD: float = 1 / 3  # Primeiros 1/3 da época = fase inicial

# --- ELOs iniciais por divisão (fallback quando não há época anterior) ---
ELO_DEFAULT_DIV1: float = 1000.0
ELO_DEFAULT_DIV2: float = 500.0
ELO_DEFAULT_UNKNOWN: float = 750.0  # Sem divisão ou divisão desconhecida

# --- Número de simulações Monte Carlo ---
N_SIMULATIONS_DEFAULT: int = 10_000
N_SIMULATIONS_DEEP: int = 100_000
N_SIMULATIONS_DEEPER: int = 1_000_000


def season_context(today: datetime | None = None) -> tuple[str, str, int]:
    """Devolve (época atual, época anterior, ano final) com rollover em agosto."""
    now = today or datetime.now()
    start_year = now.year if now.month >= 8 else now.year - 1
    end_year = start_year + 1
    current = f"{start_year % 100:02d}_{end_year % 100:02d}"
    previous = f"{(start_year - 1) % 100:02d}_{start_year % 100:02d}"
    return current, previous, end_year


# Slots de playoffs padrão quando nenhum placeholder é encontrado no CSV
PLAYOFF_SLOTS_DEFAULT: int = 8

# --- Modelo de empate (curva gaussiana) ---
DRAW_GAUSSIAN_SIGMA: float = 180.0  # Largura da curva: ~180 ELO → queda significativa
DRAW_GAUSSIAN_PEAK_FACTOR: float = 2.5  # Pico ≈ 2.5 × taxa histórica de empates

# --- Basquete 3×3 ---
BASQUETE_MAX_SCORE: int = 21
BASQUETE_OT_WIN_2PT_PROB: float = 0.30  # P(vencer prolongamento com cesto de 2 pts)
BASQUETE_OT_LOSE_1PT_PROB: float = 0.40  # P(adversário marcar 1 pt antes do 2.º cesto)

# --- Proporção de golos (cálculo K-factor) ---
SCORE_PROPORTION_EXPONENT: float = 1 / 10  # Expoente da proporção de golos

# --- Nomes de colunas CSV (evita typos silenciosos e facilita renomear) ---
COL_EQUIPA_1: str = "Equipa 1"
COL_EQUIPA_2: str = "Equipa 2"
COL_GOLOS_1: str = "Golos 1"
COL_GOLOS_2: str = "Golos 2"
COL_DIVISAO: str = "Divisão"
COL_GRUPO: str = "Grupo"
COL_JORNADA: str = "Jornada"
COL_DIA: str = "Dia"
COL_HORA: str = "Hora"
COL_FALTA_COMPARENCIA: str = "Falta de Comparência"

# --- Sub-pastas de output (relativas a docs/output/) ---
DIR_PREVISOES: str = "previsoes"
DIR_CENARIOS: str = "cenarios"
DIR_CSV_MODALIDADES: str = "csv_modalidades"
DIR_ELO_RATINGS: str = "elo_ratings"
DIR_CALIBRATION: str = "calibration"


def normalize_team_name(team_name: str, mapping: Dict[str, str]) -> str:
    """
    Normaliza o nome do curso usando o mapeamento.
    Se não encontrar, retorna o nome original (trimmed).
    """
    if not mapping:
        return team_name.strip()
    normalized = team_name.strip()
    return mapping.get(normalized, normalized)


def get_team_short_name(team_name: str, mapping_short: Dict[str, str]) -> str:
    """
    Retorna o nome curto da equipa para usar em match_id.
    """
    if not mapping_short:
        return team_name.strip()
    normalized = team_name.strip()
    return mapping_short.get(normalized, normalized)


class SimulationResult(TypedDict):
    """Resultado devolvido por _run_single_simulation_worker.

    Usar TypedDict em vez de Dict[str, Any] garante type-checking estático
    e elimina a possibilidade de typos silenciosos nas 12 chaves de string.
    """

    expected_points: Dict[str, float]
    final_elos: Dict[str, float]
    regular_season_places: Dict[str, int]
    playoff_count: Dict[str, int]
    semifinal_count: Dict[str, int]
    final_count: Dict[str, int]
    champion_count: Dict[str, int]
    promotion_count: Dict[str, int]
    relegation_count: Dict[str, int]
    liguilla_stats: Dict[str, Dict[str, int]]
    liguilla_scenarios: Dict[str, Dict[str, Dict[str, Any]]]
    match_stats: Dict[str, Dict[str, int]]
    match_elo_sum: Dict[str, Dict[str, float]]
    match_score_stats: Dict[str, Dict[str, int]]


@dataclass(slots=True)
class Team:
    name: str
    elo: float
    games_played: int = 0
    games_before_winter: int = 0


# ============================================================================
# SISTEMA ELO COMPLETO - Extraído de mmr_taçaua.py
# ============================================================================


class CompleteTacauaEloSystem:
    """
    Sistema ELO EXATO do mmr_taçaua.py com fórmula completa.

    FÓRMULA: ΔElo = K_factor × (Score_real - Score_esperado)

    Componentes:
    1. Score_esperado = 1/(1 + 10^((ELO_B - ELO_A)/250))
    2. K_factor = K_base × Season_Phase_Multiplier × Proportion_Multiplier
    3. Score_real = 1 (vitória), 0.5 (empate), 0 (derrota)
    """

    def __init__(self, k_base: float = 100):
        self.k_base = k_base

    def elo_win_probability(self, elo_a: float, elo_b: float) -> float:
        """P(A vence) = 1 / (1 + 10^((ELO_B - ELO_A) / ELO_DIVISOR))"""
        return 1.0 / (1.0 + 10 ** ((elo_b - elo_a) / ELO_DIVISOR))

    def calculate_season_phase_multiplier(
        self,
        game_number: int,
        total_group_games: int,
        game_number_before_winter: int = None,
        jornada: str = None,
    ) -> float:
        """
        Multiplier que varia ao longo da época.

        Casos:
        - Jogo do 3º lugar (E3L): 0.75
        - Playoffs: 1.5
        - Após pausa de inverno: 1 / log(4×(scaled - 4), 16)^(1/2)
        - Início (primeiros 1/3): 1 / log(4×scaled, 16)
        - Resto: 1.0
        """
        if jornada and str(jornada).upper() == "E3L":
            return PHASE_MULT_E3L

        game_number_scaled = (game_number / total_group_games) * ELO_SCALE_NORMALIZED

        if game_number_scaled > ELO_SCALE_NORMALIZED:
            return PHASE_MULT_PLAYOFFS
        elif game_number_before_winter is not None:
            game_number_after = game_number - game_number_before_winter
            game_number_after_scaled = (
                5 + (game_number_after - 1) / total_group_games * ELO_SCALE_NORMALIZED
            )

            if (
                game_number_after_scaled
                < ELO_SCALE_NORMALIZED * PHASE_EARLY_THRESHOLD + 5
            ):
                return (1 / math.log(4 * (game_number_after_scaled - 4), 16)) ** (1 / 2)
            return 1.0
        elif game_number_scaled < ELO_SCALE_NORMALIZED * PHASE_EARLY_THRESHOLD:
            game_number_start_scaled = (
                1 + (game_number - 1) / total_group_games * ELO_SCALE_NORMALIZED
            )
            return 1 / math.log(4 * game_number_start_scaled, 16)
        else:
            return 1.0

    def calculate_score_proportion(self, score1: int, score2: int) -> float:
        """
        Multiplier baseado na proporção de golos.
        proportion_multiplier = max(score1/score2, score2/score1)^(1/10)
        """
        if score2 == 0:
            score2 = 0.5
        if score1 == 0:
            score1 = 0.5

        return max((score1 / score2), (score2 / score1)) ** SCORE_PROPORTION_EXPONENT

    def calculate_elo_change(
        self,
        team1_elo: float,
        team2_elo: float,
        score1: int,
        score2: int,
        game_number_team1: int,
        game_number_team2: int,
        total_group_games_team1: int,
        total_group_games_team2: int,
        games_before_winter_team1: int = None,
        games_before_winter_team2: int = None,
        jornada: str = None,
        has_absence: bool = False,
    ) -> Tuple[float, float]:
        """
        Calcula mudança de ELO com sistema completo.

        Fast-path: quando não há E3L, sem pausa de inverno e ambas as equipas
        estão na fase média da época (phase_mult == 1.0), evita dois math.log
        e três chamadas de método — que seriam o caso em ~60-70% dos jogos
        de simulação futura.
        """
        expected1 = self.elo_win_probability(team1_elo, team2_elo)

        if score1 > score2:
            score_real_1 = 1.0
        elif score1 < score2:
            score_real_1 = 0.0
        else:
            score_real_1 = 0.5

        proportion_mult = self.calculate_score_proportion(score1, score2)

        # Fast-path: sem E3L, sem pausa de inverno, e na fase média → phase_mult = 1.0
        if (
            not jornada
            and games_before_winter_team1 is None
            and games_before_winter_team2 is None
            and not has_absence
        ):
            scaled1 = (
                game_number_team1 / total_group_games_team1
            ) * ELO_SCALE_NORMALIZED
            scaled2 = (
                game_number_team2 / total_group_games_team2
            ) * ELO_SCALE_NORMALIZED
            early_threshold = ELO_SCALE_NORMALIZED * PHASE_EARLY_THRESHOLD
            if (
                early_threshold <= scaled1 <= ELO_SCALE_NORMALIZED
                and early_threshold <= scaled2 <= ELO_SCALE_NORMALIZED
            ):
                k = self.k_base * proportion_mult
                expected2 = 1.0 - expected1
                score_real_2 = 1.0 - score_real_1
                return round(k * (score_real_1 - expected1)), round(
                    k * (score_real_2 - expected2)
                )

        phase_mult_1 = self.calculate_season_phase_multiplier(
            game_number_team1,
            total_group_games_team1,
            games_before_winter_team1,
            jornada,
        )
        phase_mult_2 = self.calculate_season_phase_multiplier(
            game_number_team2,
            total_group_games_team2,
            games_before_winter_team2,
            jornada,
        )

        k_factor_1 = self.k_base * phase_mult_1 * proportion_mult
        k_factor_2 = self.k_base * phase_mult_2 * proportion_mult

        score_real_2 = 1.0 - score_real_1
        expected2 = 1.0 - expected1

        elo_delta_1 = round(k_factor_1 * (score_real_1 - expected1))
        elo_delta_2 = round(k_factor_2 * (score_real_2 - expected2))

        if has_absence:
            return 0, 0

        return elo_delta_1, elo_delta_2


# ============================================================================
# HARDSET DE RESULTADOS - Sistema de cenários "What-If"
# ============================================================================


@dataclass(slots=True)
class FixedResult:
    """Representa um resultado fixado para simulação."""

    match_id: str
    score_a: int
    score_b: int

    def __str__(self) -> str:
        return f"{self.match_id}: {self.score_a}-{self.score_b}"


class HardsetManager:
    """
    Gere resultados fixados para simulações "what-if".

    Permite explorar cenários tipo:
    - "E se o jogo X acabar 5-4?"
    - "Como isso afeta os ELOs esperados?"
    - "Qual o efeito borboleta nos outros jogos?"

    NOTA: Suporta tanto match_id curtos (EGI) como longos (Eng. e Gestão Industrial).
    """

    def __init__(self, mapping_short: Dict[str, str] = None):
        self.fixed_results: Dict[str, FixedResult] = {}
        self.mapping_short = mapping_short or {}
        # Índice alternativo para busca por variações do match_id
        self.match_id_aliases: Dict[str, str] = {}

    def get_affected_modalidades(self) -> set:
        """Retorna o conjunto de modalidades afetadas pelos hardsets."""
        modalidades = set()
        for match_id in self.fixed_results:
            # match_id formato: "FUTSAL FEMININO_5_EGI_EI"
            parts = match_id.split("_")
            if len(parts) >= 2:
                # Primeira parte é a modalidade (pode ter espaços)
                # Procurar onde o número da jornada (inteiro) aparece
                for i, part in enumerate(parts):
                    if part and part[0].isdigit() and i > 0:
                        # Parte antes de i é a modalidade
                        modalidade = "_".join(parts[:i])
                        modalidades.add(modalidade)
                        break
        return modalidades

    def _normalize_match_id_for_lookup(self, match_id: str) -> str:
        """
        Normaliza match_id para lookup, tratando variações curtas/longas.

        Se o match_id não existir diretamente, tenta converter nomes curtos em longos.

        Exemplos:
        - "FUTSAL FEMININO_5_EGI_Direito" -> procura por "FUTSAL FEMININO_5_EGI_Direito"
        - Se não encontrar, tenta expandir "EGI" em "Eng. e Gestão Industrial"
        """
        # Primeiro, verificar se existe diretamente
        if match_id in self.fixed_results:
            return match_id

        # Se não, tentar expandir formas curtas em longas
        parts = match_id.split("_")
        if len(parts) >= 4:
            # Formato esperado: MODALIDADE_JORNADA_TEAM_A_TEAM_B
            # Mas TEAM_A e TEAM_B podem ter múltiplas partes por terem espaços

            # Reconstruir com lookup no mapping
            modalidade_jornada = "_".join(parts[:2])
            rest = "_".join(parts[2:])

            # Tentar encontrar no alias
            if match_id in self.match_id_aliases:
                return self.match_id_aliases[match_id]

        return match_id

    def add_fixed_result(self, match_id: str, score_a: int, score_b: int) -> None:
        """
        Adiciona um resultado fixado.

        Args:
            match_id: ID do jogo (ex: "FUTSAL MASCULINO_5_EGI_Gestão")
            score_a: Golos da equipa A
            score_b: Golos da equipa B
        """
        self.fixed_results[match_id] = FixedResult(match_id, score_a, score_b)
        logger.info(f"Resultado fixado: {match_id} → {score_a}-{score_b}")

    def add_from_dict(self, fixed_dict: Dict[str, Tuple[int, int]]) -> None:
        """
        Adiciona múltiplos resultados de um dicionário.

        Args:
            fixed_dict: {match_id: (score_a, score_b)}

        Exemplo:
            hardset.add_from_dict({
                "FUTSAL MASCULINO_5_Eng_Gestão": (5, 4),
                "FUTSAL MASCULINO_6_Direito_Medicina": (2, 2),
            })
        """
        for match_id, (score_a, score_b) in fixed_dict.items():
            self.add_fixed_result(match_id, score_a, score_b)

    def add_from_csv(self, csv_file: str) -> None:
        """
        Carrega resultados fixados de um CSV.

        Formato CSV:
        match_id,score_a,score_b
        FUTSAL MASCULINO_5_Eng_Gestão,5,4
        FUTSAL MASCULINO_6_Direito_Medicina,2,2

        NOTA: Normaliza nomes de equipas usando mapping_short para compatibilidade com
              nomes curtos gerados pelo sistema.
        """
        try:
            with open(csv_file, "r", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    match_id = row["match_id"]
                    score_a = int(row["score_a"])
                    score_b = int(row["score_b"])

                    # Normalizar match_id: converter nomes de equipas longas em curtas
                    # Se mapping_short está disponível, tentar normalizar
                    if self.mapping_short:
                        parts = match_id.split("_")
                        if len(parts) >= 4:
                            # Tentar normalizar o team_a (partes a partir do índice 2)
                            # Procurar por nomes conhecidos no mapping_short
                            for long_name, short_name in self.mapping_short.items():
                                if "_" + long_name in match_id:
                                    match_id = match_id.replace(long_name, short_name)

                    self.add_fixed_result(match_id, score_a, score_b)
            logger.info(
                f"Carregados {len(self.fixed_results)} resultados de {csv_file}"
            )
        except Exception as e:
            logger.error(f"Erro ao carregar hardset CSV: {e}")

    def get_fixed_result(self, match_id: str) -> FixedResult | None:
        """Retorna resultado fixado para um jogo, se existir."""
        # Procurar com normalização
        normalized = self._normalize_match_id_for_lookup(match_id)
        return self.fixed_results.get(normalized)

    def has_fixed_result(self, match_id: str) -> bool:
        """Verifica se um jogo tem resultado fixado."""
        # Procurar com normalização
        normalized = self._normalize_match_id_for_lookup(match_id)
        return normalized in self.fixed_results

    def clear(self) -> None:
        """Remove todos os resultados fixados."""
        self.fixed_results.clear()
        self.match_id_aliases.clear()
        logger.info("Todos os resultados fixados foram removidos")

    def summary(self) -> str:
        """Retorna resumo dos resultados fixados."""
        if not self.fixed_results:
            return "Nenhum resultado fixado"

        lines = [f"Resultados fixados ({len(self.fixed_results)}):"]
        for fr in self.fixed_results.values():
            lines.append(f"  • {fr}")
        return "\n".join(lines)


class SportScoreSimulator:
    """
    Simula resultados realistas por modalidade.

    Modelos:
    - Voleibol: Binário (2-0 ou 2-1)
    - Basquete 3x3: Até 21 pontos, perdedor >= 2
    - Futsal/Andebol/Futebol7: Poisson híbrido
    """

    def __init__(self, sport_type: str = "futsal"):
        self.sport_type = sport_type
        # Baselines médios por modalidade (golos por equipa por jogo)
        self.baselines = {
            "futsal": {
                "base_goals": 3.2,  # Calibrado: ~3.15 (universitário tem menos golos)
                "elo_scale": 600,
                "elo_scale_mult": 0.75,
                "dispersion_k": 5.0,
                "forced_draw_fraction": 0.98,  # 98% forçados - eliminar empates Poisson (1.1% histórico)
                "elo_adjustment_limit": 1.2,  # Permite surras bem maiores (725 ELO diff)
            },
            "andebol": {
                "base_goals": 20.5,  # Calibrado: ~20.6 (histórico universitário)
                "elo_scale": 500,
                "elo_scale_mult": 0.75,
                "dispersion_k": 15.0,  # Calibrado: ~14.9
                "forced_draw_fraction": 0.55,  # 55% forçados - empates comuns (4.4% histórico)
                "elo_adjustment_limit": 0.45,  # Reduzido: evita spreads irrealistas com base_goals alto
            },
            "basquete": {
                "max_score": 21,
                "min_score": 2,
                "elo_scale": 400,
                "sigma": 5.5,  # Aumentado de 3.5 para mais variância, evita zeros
                "sigma_mult": 1.3,
                "elo_adjustment_limit": 0.5,  # Limita ajuste de ELO em basquete
            },
            "volei": {"elo_scale": 500},
            "futebol7": {
                "base_goals": 2.4,  # Calibrado: ~2.41 (histórico universitário)
                "elo_scale": 600,
                "elo_scale_mult": 0.75,
                "dispersion_k": 3.0,  # Calibrado: ~2.95
                "forced_draw_fraction": 0.90,  # 90% forçados - reduzir empates Poisson (11.7% histórico)
                "elo_adjustment_limit": 1.0,  # Um meio termo
            },
        }
        self.params = self.baselines.get(sport_type, self.baselines["futsal"]).copy()
        self.division_baselines = {}
        self.division_draw_rates = {}
        self.default_draw_rate = 0.0
        # Atributos cacheados derivados de self.params — evitam dict lookups por simulação
        self._has_logit_model: bool = False
        self._forced_draw_fraction: float = self.params.get("forced_draw_fraction", 0.7)
        self._draw_multiplier: float = 1.0

    def _refresh_draw_cache(self) -> None:
        """Recalcula os atributos cacheados de empate após qualquer alteração a self.params."""
        dm = self.params.get("draw_model", {})
        self._has_logit_model = bool(
            dm.get("intercept", 0.0) != 0.0 or dm.get("coef_linear", 0.0) != 0.0
        )
        if self._has_logit_model:
            self._draw_multiplier = self.params.get("draw_multiplier", 1.4)
            self._forced_draw_fraction = self._draw_multiplier
        else:
            self._draw_multiplier = 1.0
            self._forced_draw_fraction = self.params.get("forced_draw_fraction", 0.7)

    def apply_calibrated_params(self, calibrated_params: Dict) -> None:
        """Aplica parâmetros calibrados ao simulador."""
        if not calibrated_params:
            return

        # Atualizar parâmetros base
        for key in (
            "base_goals",
            "base_goals_std",
            "dispersion_k",
            "base_draw_rate",
            "draw_elo_sensitivity",
            "margin_elo_slope",
            "margin_elo_intercept",
            "elo_adjustment_limit",
            "draw_multiplier",
        ):
            if key in calibrated_params:
                self.params[key] = calibrated_params[key]

        # Parâmetros específicos de basquete (modelo Gaussiano)
        if self.sport_type == "basquete":
            if "base_score" in calibrated_params:
                self.params["base_score"] = calibrated_params["base_score"]
            if "sigma" in calibrated_params:
                self.params["sigma"] = calibrated_params["sigma"]

        # Parâmetros específicos de voleibol (modelo de sets)
        if self.sport_type == "volei":
            if "p_sweep_base" in calibrated_params:
                self.params["p_sweep_base"] = calibrated_params["p_sweep_base"]

        # Modelo de empate calibrado (só se tiver coeficientes válidos)
        if "draw_model" in calibrated_params:
            dm = calibrated_params["draw_model"]
            # Não aplicar modelos com coeficientes zerados (insufficient_draws)
            if dm.get("intercept", 0.0) != 0.0 or dm.get("coef_linear", 0.0) != 0.0:
                self.params["draw_model"] = dm

        # Definir taxa base de empate como fallback
        if "base_draw_rate" in calibrated_params:
            self.default_draw_rate = calibrated_params["base_draw_rate"]

        # Divisões (opcional)
        division_params = calibrated_params.get("division_params")
        if division_params:
            for div, div_cfg in division_params.items():
                # Atualizar baselines por divisão (se houver)
                base_goals = div_cfg.get("base_goals")
                if base_goals is not None:
                    # Preservar std histórico se já existe, e adicionar dispersion_k calibrado
                    existing = self.division_baselines.get(int(div), {})
                    updated = dict(existing)
                    updated["mean"] = base_goals
                    if "dispersion_k" in div_cfg:
                        updated["dispersion_k"] = div_cfg["dispersion_k"]
                    self.division_baselines[int(div)] = updated
                elif "dispersion_k" in div_cfg:
                    # Sem base_goals mas com dispersion_k — atualizar só o dispersion_k
                    existing = self.division_baselines.get(int(div), {})
                    updated = dict(existing)
                    updated["dispersion_k"] = div_cfg["dispersion_k"]
                    self.division_baselines[int(div)] = updated
                # Atualizar taxa de empate por divisão (se houver)
                if "base_draw_rate" in div_cfg:
                    self.division_draw_rates[int(div)] = div_cfg["base_draw_rate"]

        # Actualizar cache de atributos derivados
        self._refresh_draw_cache()

    def set_division_baselines(
        self, baselines: Dict[int | None, Dict[str, float]]
    ) -> None:
        # Cópia rasa para evitar aliasing com o dict original (apply_calibrated_params
        # adiciona novas entradas, não muta os sub-dicts existentes)
        self.division_baselines = dict(baselines) if baselines else {}

    def set_division_draw_rates(self, draw_rates: Dict[int | None, float]) -> None:
        self.division_draw_rates = draw_rates or {}

    def _get_division_baseline(self, division: int | None) -> Dict[str, float] | None:
        if division in self.division_baselines:
            return self.division_baselines[division]
        return self.division_baselines.get(None)

    def _get_division_draw_rate(self, division: int | None) -> float:
        if division in self.division_draw_rates:
            return self.division_draw_rates[division]
        if None in self.division_draw_rates:
            return self.division_draw_rates[None]
        if self.default_draw_rate > 0:
            return self.default_draw_rate
        return self.params.get("base_draw_rate", 0.0)

    def _calculate_draw_probability(
        self, elo_a: float, elo_b: float, target_draw_rate: float
    ) -> float:
        """
        Calcula a probabilidade de empate baseada na diferença de ELO usando uma curva gaussiana.

        A probabilidade de empate é máxima quando os ELOs são iguais e decresce com a diferença.

        Args:
            elo_a: ELO da equipa A
            elo_b: ELO da equipa B
            target_draw_rate: Taxa média histórica de empates (usada para calibração)

        Returns:
            Probabilidade de empate para este confronto específico

        Fórmula: p_draw = peak_rate * exp(-(elo_diff²) / (2 * sigma²))

        Onde:
        - peak_rate: Probabilidade máxima quando ELOs são iguais (~1.5x target_draw_rate)
        - sigma: Controla quão rápido a probabilidade decai (200 pontos ELO)
        - elo_diff: Diferença absoluta de ELO
        """
        draw_model = self.params.get("draw_model")
        if draw_model:
            coef_linear = draw_model.get("coef_linear", 0.0)
            coef_quadratic = draw_model.get("coef_quadratic", 0.0)
            intercept = draw_model.get("intercept", 0.0)
            if intercept != 0.0 or coef_linear != 0.0 or coef_quadratic != 0.0:
                elo_diff = abs(elo_a - elo_b)
                logit = (
                    intercept + coef_linear * elo_diff + coef_quadratic * (elo_diff**2)
                )
                try:
                    p_draw = 1.0 / (1.0 + math.exp(-logit))
                except OverflowError:
                    p_draw = 0.0 if logit < 0 else 1.0
                return max(0.0, min(1.0, p_draw))

        if target_draw_rate <= 0:
            return 0.0

        elo_diff = abs(elo_a - elo_b)

        # Parâmetros da curva gaussiana
        sigma = DRAW_GAUSSIAN_SIGMA
        peak_rate = target_draw_rate * DRAW_GAUSSIAN_PEAK_FACTOR

        # Curva gaussiana: máxima no centro (elo_diff=0), decai para as caudas
        draw_probability = peak_rate * np.exp(-(elo_diff**2) / (2 * sigma**2))

        # Garantir que não excede limites razoáveis
        draw_probability = min(peak_rate, max(0.0, draw_probability))

        return draw_probability

    def simulate_score(
        self,
        elo_a: float,
        elo_b: float,
        force_winner: bool = False,
        division: int | None = None,
    ) -> Tuple[int, int]:
        """Simula resultado baseado no tipo de desporto e ELOs.

        Args:
            elo_a: ELO da equipa A
            elo_b: ELO da equipa B
            force_winner: Se True (playoffs), força desempate. Se False (época regular),
                         permite empates naturais (quando aplicável).

        Para Voleibol: Nunca tem empate (sempre força vencedor).
        Para Basquete: Permite empates em época regular, força vencedor em playoffs.
        Para Poisson (Futsal/Andebol/Futebol7): Permite empates em época regular,
                                                 força vencedor em playoffs.
        """
        division_baseline = self._get_division_baseline(division)
        target_draw_rate = self._get_division_draw_rate(division)

        # Se temos parâmetros calibrados, usar o base_draw_rate calibrado (não histórico)
        has_calibrated_params = (
            "draw_model" in self.params
            and self.params.get("draw_model", {}).get("intercept") is not None
        )
        if has_calibrated_params and "base_draw_rate" in self.params:
            # Usar a taxa calibrada ao invés da histórica
            target_draw_rate = self.params["base_draw_rate"]

        if self.sport_type == "volei":
            # Voleibol nunca tem empates
            p_a = 1.0 / (1.0 + 10 ** ((elo_b - elo_a) / ELO_DIVISOR))
            winner_is_a = random.random() < p_a
            return self._simulate_volei(elo_a, elo_b, winner_is_a)

        elif self.sport_type == "basquete":
            # Basquete 3x3: NUNCA tem empates (sempre vai a prolongamento)
            base_score = (
                division_baseline["mean"]
                if division_baseline and "mean" in division_baseline
                else self.params.get("base_score", self.params.get("base_goals", 15))
            )
            sigma = (
                division_baseline.get("std")
                if division_baseline and "std" in division_baseline
                else self.params.get("sigma", 3.5)
            )
            sigma = max(2.0, sigma) * self.params.get("sigma_mult", 1.0)
            # SEMPRE força vencedor - basquete não tem empates
            return self._simulate_basquete(elo_a, elo_b, True, base_score, sigma)

        else:
            # Poisson (Futsal, Andebol, Futebol7)
            base_goals = (
                division_baseline["mean"]
                if division_baseline and "mean" in division_baseline
                else self.params.get("base_goals", 4.5)
            )
            elo_scale = self.params.get("elo_scale", 600) * self.params.get(
                "elo_scale_mult", 1.0
            )
            # Usar dispersion_k por divisão (calibrado) se disponível, senão fallback global
            dispersion_k = (
                division_baseline.get("dispersion_k")
                if division_baseline and "dispersion_k" in division_baseline
                else None
            ) or self.params.get("dispersion_k", 6.0)
            forced_draw_fraction = self.params.get("forced_draw_fraction", 0.7)

            if force_winner:
                # Em playoffs, simular até ter vencedor
                while True:
                    score_a, score_b = self._simulate_poisson(
                        elo_a, elo_b, base_goals, elo_scale, dispersion_k
                    )
                    if score_a != score_b:
                        return (score_a, score_b)
            else:
                # Em época regular, usar probabilidade de empate dinâmica baseada em ELO
                # Calcular probabilidade de empate para este confronto específico
                draw_probability = self._calculate_draw_probability(
                    elo_a, elo_b, target_draw_rate
                )

                # Usar atributos cacheados (calculados uma vez em apply_calibrated_params)
                has_logit_model = self._has_logit_model
                forced_draw_fraction = self._forced_draw_fraction

                # Decidir se este jogo terá empate forçado
                if draw_probability > 0 and random.random() < (
                    draw_probability * forced_draw_fraction
                ):
                    # Empate forçado com placar realista
                    goals = max(0, int(np.random.poisson(base_goals)))
                    return (goals, goals)

                # Poisson normal - com modelo calibrado, ser mais permissivo com empates naturais
                # Sem modelo, descartar empates se taxa histórica baixa (<20%)
                if has_logit_model:
                    # Modelo calibrado: aceitar empates naturais até 30% de taxa histórica
                    max_attempts = 30 if target_draw_rate < 0.30 else 1
                else:
                    # Sem modelo: descartar empates se taxa baixa (<20%)
                    max_attempts = 50 if target_draw_rate < 0.20 else 1

                for attempt in range(max_attempts):
                    score_a, score_b = self._simulate_poisson(
                        elo_a, elo_b, base_goals, elo_scale, dispersion_k
                    )
                    # Se não é empate OU taxa alta permite empates naturais, aceitar
                    if score_a != score_b or target_draw_rate >= (
                        0.30 if has_logit_model else 0.20
                    ):
                        return (score_a, score_b)
                    # Taxa baixa: tentar novamente para evitar empate Poisson

                # Fallback após todas tentativas (improvável)
                return (score_a, score_b)

    def _simulate_volei(
        self, elo_a: float, elo_b: float, winner_is_a: bool
    ) -> Tuple[int, int]:
        """
        Voleibol: Distribuição de Bell sobre 4 resultados possíveis.

        Resultados (do ponto de vista do favorito):
        - 0: 0-2 sweep (azarão vence bem)
        - 1: 1-2 derrota apertada
        - 2: 2-1 vitória apertada
        - 3: 2-0 sweep (favorito vence bem)

        Modelo:
        - Equipas equilibradas (ELO_diff=0): centro em 1.5 (2-1 e 1-2 prováveis)
        - Favorito forte: centro move para 3 (2-0 mais provável)
        - Azarão que vence: centro move para 0 (0-2 mais provável)

        **NOVO**: ELO scaling mais agressivo + sigma adapta-se a desequilíbrio
        - ELO factor: multiplicador aumentado para +1.5 a +2.0 em vez de +0.4
        - Sigma: BAIXA quando desequilibrado (resultado previsível)
                 ALTA quando equilibrado (resultado incerto)
        """
        import numpy as np

        # Calcular diferença de ELO ASSINADA
        if winner_is_a:
            elo_diff_signed = elo_a - elo_b
        else:
            elo_diff_signed = elo_b - elo_a

        # ========== CENTER: Usar parâmetros calibrados ==========
        # Antes: elo_factor e elo_divisor eram hardcoded
        # Agora: vêm da calibração automática

        elo_factor = self.params.get("elo_factor", 1.8)  # default 1.8
        elo_divisor = self.params.get("elo_divisor", 600)  # default 600

        center = 1.5 + (elo_diff_signed / elo_divisor) * elo_factor
        center = max(-0.5, min(3.5, center))  # clipping

        # ========== SIGMA: Varia com desequilíbrio ==========
        # Base sigma do calibrador
        sigma_base = self.params.get("volei_sigma", 0.85)

        # Quanto maior |elo_diff_signed|, menor sigma (resultado mais previsível)
        # Quando elo_diff = 0, sigma = sigma_base (máxima variabilidade)
        # Quando elo_diff = ±800, sigma = sigma_base * 0.4 (mínima variabilidade)

        abs_elo_diff = abs(elo_diff_signed)
        sigma_reduction = min(abs_elo_diff / 800, 0.6)  # redução máxima de 60%
        sigma = sigma_base * (1.0 - sigma_reduction)
        sigma = max(0.3, sigma)  # mínimo de 0.3 para evitar muito previsível

        # Distribuição de Bell sobre os 4 resultados possíveis
        outcomes = np.array([0, 1, 2, 3])
        probabilities = np.exp(-((outcomes - center) ** 2) / (2 * sigma**2))
        probabilities = probabilities / np.sum(probabilities)

        # Sample do resultado
        result_idx = np.random.choice([0, 1, 2, 3], p=probabilities)

        # Converter índice para score (sets)
        if result_idx == 0:  # 0-2 (azarão sweep)
            return (0, 2) if winner_is_a else (2, 0)
        elif result_idx == 1:  # 1-2 (derrota apertada)
            return (1, 2) if winner_is_a else (2, 1)
        elif result_idx == 2:  # 2-1 (vitória apertada)
            return (2, 1) if winner_is_a else (1, 2)
        else:  # result_idx == 3: 2-0 (favorito sweep)
            return (2, 0) if winner_is_a else (0, 2)

    def _simulate_basquete(
        self,
        elo_a: float,
        elo_b: float,
        force_winner: bool = False,
        base_score: float = 15.0,
        sigma: float = 3.5,
    ) -> Tuple[int, int]:
        """
        Basquete 3x3: Até 21 pontos no tempo regulamentar.
        Cestos: 1 ponto (normal) ou 2 pontos (longo).
        Prolongamento: primeira equipa a marcar 2 pontos vence.

        Args:
            elo_a: ELO da equipa A
            elo_b: ELO da equipa B
            force_winner: Se True (playoffs), força desempate até haver vencedor.
                         Se False (época regular), permite empate natural.

        Retorna (score_a, score_b)
        """
        # Tempo regulamentar
        # Ajuste de ELO mais conservador para basquete (dividir por 250 em vez de 150)
        elo_adjustment_limit = self.params.get("elo_adjustment_limit", 0.5)
        elo_diff = (elo_a - elo_b) / 250
        elo_diff = max(-elo_adjustment_limit, min(elo_adjustment_limit, elo_diff))

        # Usar sigma passado como argumento (do division_baseline) se válido,
        # senão fallback para o parâmetro configurado
        if sigma is None or sigma <= 0:
            sigma = self.params.get("sigma", 3.5)

        base_score_a = base_score + elo_diff
        base_score_b = base_score - elo_diff

        score_a = min(
            BASQUETE_MAX_SCORE, max(0, int(np.random.normal(base_score_a, sigma)))
        )
        score_b = min(
            BASQUETE_MAX_SCORE, max(0, int(np.random.normal(base_score_b, sigma)))
        )

        # Se não há empate ou não força vencedor, retornar
        if score_a != score_b or not force_winner:
            return (score_a, score_b)

        # PROLONGAMENTO: Sudden death até 2 pontos
        # Primeira equipa a marcar 2 pontos vence
        p_a = 1.0 / (1.0 + 10 ** ((elo_b - elo_a) / ELO_DIVISOR))

        if random.random() < p_a:
            # Equipa A vence prolongamento
            if random.random() < BASQUETE_OT_WIN_2PT_PROB:
                # Cesto de 2 pontos: jogo acaba imediatamente
                return (score_a + 2, score_b + 0)
            else:
                # Dois cestos de 1 ponto: B pode marcar 0 ou 1
                b_scored = 1 if random.random() < BASQUETE_OT_LOSE_1PT_PROB else 0
                return (score_a + 2, score_b + b_scored)
        else:
            # Equipa B vence prolongamento
            if random.random() < BASQUETE_OT_WIN_2PT_PROB:
                return (score_a + 0, score_b + 2)
            else:
                # Dois cestos de 1 ponto: A pode marcar 0 ou 1
                a_scored = 1 if random.random() < BASQUETE_OT_LOSE_1PT_PROB else 0
                return (score_a + a_scored, score_b + 2)

    def _simulate_poisson(
        self,
        elo_a: float,
        elo_b: float,
        base_goals: float,
        elo_scale: float,
        dispersion_k: float,
    ) -> Tuple[int, int]:
        """Futsal/Andebol/Futebol7: Modelo Poisson independente (permite empates)."""
        base = base_goals

        # Ajuste baseado em ELO
        elo_adjustment = (elo_a - elo_b) / elo_scale
        # Limitar conforme o desporto para evitar valores absurdos
        # Futsal: 1.2 (permite surras) | Andebol: 0.7 (mais conservador) | Futebol7: 1.0
        elo_adjustment_limit = self.params.get("elo_adjustment_limit", 0.6)
        elo_adjustment = max(
            -elo_adjustment_limit, min(elo_adjustment_limit, elo_adjustment)
        )

        # base_goals e' media por equipa; ajustar diretamente
        lambda_a = base * (1.0 + elo_adjustment)
        lambda_b = base * (1.0 - elo_adjustment)

        # Overdispersion para resultados mais extremos
        if dispersion_k and dispersion_k > 0:
            gamma_a = np.random.gamma(dispersion_k, 1.0 / dispersion_k)
            gamma_b = np.random.gamma(dispersion_k, 1.0 / dispersion_k)
            # Clipar multiplicador Gamma para evitar resultados irrealistas
            # Para desportos de golos altos (andebol), clip mais agressivo
            if base > 10:
                gamma_a = np.clip(gamma_a, 0.75, 1.30)
                gamma_b = np.clip(gamma_b, 0.75, 1.30)
            else:
                gamma_a = np.clip(gamma_a, 0.5, 1.8)
                gamma_b = np.clip(gamma_b, 0.5, 1.8)
            lambda_a *= gamma_a
            lambda_b *= gamma_b

        # Garantir valores positivos e dentro de limites razoáveis
        # Para desportos de golos altos, cap mais conservador (1.4x base vs 2x)
        max_lambda = max(15.0, base * 1.4) if base > 10 else max(15.0, base * 2.0)
        lambda_a = max(0.2, min(max_lambda, lambda_a))
        lambda_b = max(0.2, min(max_lambda, lambda_b))

        # Amostrar golos de forma independente
        try:
            goals_a = int(np.random.poisson(lambda_a))
            goals_b = int(np.random.poisson(lambda_b))
        except (ValueError, OverflowError):
            # Fallback em caso de erro com valores extremos
            goals_a = max(0, int(lambda_a + np.random.normal(0, 1)))
            goals_b = max(0, int(lambda_b + np.random.normal(0, 1)))

        return (max(0, goals_a), max(0, goals_b))

    def sample_margin(self, elo_diff: float) -> int:
        """Compatibilidade com código antigo - retorna margem estimada."""
        if self.sport_type == "volei":
            return 1  # Margem sempre 1 ou 2
        elif self.sport_type == "basquete":
            return min(19, max(1, int(5 + elo_diff / 100)))
        else:
            base = self.params.get("base_goals", 4.0) / 2
            return max(1, int(base + abs(elo_diff) / 300))


def load_playoff_rules(docs_dir: str = None) -> Dict:
    """Carrega as regras de playoff do ficheiro JSON."""
    if docs_dir:
        path = Path(docs_dir) / "config" / "playoff_rules.json"
    else:
        path = Path("..") / "docs" / "config" / "playoff_rules.json"

    if not path.exists():
        # Tentar no diretório local como fallback
        path = Path("playoff_rules.json")
        if not path.exists():
            return {}

    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Erro ao carregar playoff_rules.json: {e}")
        return {}


def load_course_mapping(docs_dir: str = None) -> Tuple[Dict[str, str], Dict[str, str]]:
    """
    Carrega o mapeamento de nomes de cursos do config_cursos.json.

    Args:
        docs_dir: Caminho para o diretório docs. Se None, usa caminho relativo.

    Retorna:
        (mapping_to_display, mapping_to_short)

    - mapping_to_display: {"EGI" -> "Eng. e Gestão Industrial", "Eng. e Gestão Industrial" -> "Eng. e Gestão Industrial"}
    - mapping_to_short: {"Eng. e Gestão Industrial" -> "EGI", "EGI" -> "EGI"}
    """
    try:
        if docs_dir:
            config_path = Path(docs_dir) / "config" / "config_cursos.json"
        else:
            config_path = Path("..") / "docs" / "config" / "config_cursos.json"

        with open(config_path, encoding="utf-8-sig") as f:
            config = json.load(f)
            mapping_display = {}
            mapping_short = {}

            # Primeiro pass: mapear course_key -> (display_name, course_key)
            # Manter track de qual é o "course_key preferido" para cada displayName (forma curta sem espaços)
            displayName_to_preferred_key = {}  # displayName -> course_key_preferido

            for course_key, course_info in config.get("courses", {}).items():
                display_name = course_info.get("displayName", course_key)

                # Mapeamento para forma display (longa)
                mapping_display[course_key] = display_name
                mapping_display[display_name] = display_name

                # Mapeamento para forma curta
                mapping_short[course_key] = course_key

                # Definir curso_key preferido para cada displayName
                # Preferir o que tem menos espaços (forma mais curta)
                if display_name not in displayName_to_preferred_key:
                    displayName_to_preferred_key[display_name] = course_key
                else:
                    # Se este course_key é mais curto (menos caracteres), usar este
                    current_key = displayName_to_preferred_key[display_name]
                    if len(course_key) < len(current_key):
                        displayName_to_preferred_key[display_name] = course_key

            # Segundo pass: atribuir o course_key preferido a cada displayName em mapping_short
            for display_name, course_key in displayName_to_preferred_key.items():
                mapping_short[display_name] = course_key

            # Adicionar aliases para formas expandidas comuns
            aliases = {
                "Engenharia Informática": "Eng. Informática",
                "Engenharia Civil": "Eng. Civil",
                "Engenharia Biomédica": "Eng. Biomédica",
                "Engenharia Mecânica": "Eng. Mecânica",
                "Engenharia Materiais": "Eng. Materiais",
                "Engenharia Gestão Industrial": "Eng. e Gestão Industrial",
                "Eng. e Gestão Industrial": "Eng. e Gestão Industrial",
            }

            for alias, canonical_display in aliases.items():
                # Encontrar o course_key para este displayName canonical
                if canonical_display in displayName_to_preferred_key:
                    course_key = displayName_to_preferred_key[canonical_display]
                    mapping_display[alias] = mapping_display.get(
                        canonical_display, canonical_display
                    )
                    mapping_short[alias] = course_key

            return mapping_display, mapping_short
    except Exception as e:
        logger.error(f"Erro ao carregar config_cursos.json: {e}")
        return {}, {}


def load_calibrated_config(
    docs_dir: str = None, custom_path: str | None = None
) -> Dict:
    """Carrega configuração calibrada gerada pelo calibrator.py."""
    if custom_path:
        config_path = custom_path
    elif docs_dir:
        config_path = (
            Path(docs_dir)
            / "output"
            / "calibration"
            / "calibrated_simulator_config.json"
        )
    else:
        config_path = (
            Path("..")
            / "docs"
            / "output"
            / DIR_CALIBRATION
            / "calibrated_simulator_config.json"
        )

    if not Path(config_path).exists():
        logger.warning(f"Config calibrada não encontrada: {config_path}")
        return {}

    try:
        with open(config_path, encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.warning(f"Erro ao ler config calibrada: {e}")
        return {}


def parse_playoff_slots(csv_rows: List[Dict]) -> Tuple[Dict[Tuple[int, str], int], int]:
    """Inferir quantas vagas de playoffs existem por divisão/grupo.

    Baseia-se nas linhas de eliminatórias (jornadas que começam por "E")
    que usam placeholders como "1º Class. 1ª Div. Gr. A".
    Retorna (slots_por_grupo, total_slots).
    """

    slots = defaultdict(int)
    # Regex flexível para capturar 1º Class. 2ª Div. Gr. A, Grupo B, etc.
    pattern = re.compile(
        r"(\d+)[ºo]?\s*Class\.\s*(\d+)[ªa]?\s*Div\.?\s*(?:Gr\.?|Grupo)?\s*([A-Za-z0-9]+)?",
        re.IGNORECASE,
    )

    for row in csv_rows:
        jornada_val = str(row.get(COL_JORNADA, "")).strip().upper()
        if not jornada_val.startswith("E"):
            continue

        for key in ("Equipa 1", "Equipa 2"):
            name = str(row.get(key, "")).strip()
            if not name:
                continue

            match = pattern.search(name)
            if match:
                div = int(match.group(2))
                grp = (match.group(3) or "").upper()
                slots[(div, grp)] += 1

    total_slots = sum(slots.values())
    return slots, total_slots


def infer_slots_from_rules(
    modalidade: str, playoff_rules: Dict, epoch: str = "25_26"
) -> Tuple[Dict[Tuple[int, str], int], int]:
    """Inferir vagas de playoff a partir do playoff_rules.json."""
    if not playoff_rules:
        return {}, 0

    epoch_data = playoff_rules.get("epochs", {}).get(epoch, {})
    modalidade_rules = epoch_data.get("modalidades", {}).get(modalidade, {})
    if not modalidade_rules:
        return {}, 0

    fmt = modalidade_rules.get("format")
    slots = defaultdict(int)

    if fmt == "divisions-and-groups":
        # Rule: 1st of each 2nd div group + Top N of 1st div
        n_groups_2nd = modalidade_rules.get("n_groups_2nd_div", 0)
        total_slots = 8  # Default for this format
        # 1 slot for each group in 2nd div (A, B, C...)
        for i in range(n_groups_2nd):
            grp_name = chr(ord("A") + i)
            slots[(2, grp_name)] = 1
        # Remaining slots for 1st div
        slots[(1, "")] = max(0, total_slots - n_groups_2nd)

    elif fmt == "divisions-only":
        # Rule: Top 7 of 1st + 1st of 2nd
        slots[(1, "")] = 7
        slots[(2, "")] = 1

    elif fmt == "groups-only":
        # Rule: 4 of each group (assuming 2 groups A/B)
        n_groups = modalidade_rules.get("n_groups", 2)
        for i in range(n_groups):
            grp_name = chr(ord("A") + i)
            slots[(1, grp_name)] = 4

    elif fmt == "single-league":
        # Rule: Top 8
        slots[(1, "")] = 8

    total_slots = sum(slots.values())
    if total_slots > 0:
        logger.info(
            f"Vagas de playoff inferidas das regras para {modalidade}: {dict(slots)} (Total: {total_slots})"
        )

    return slots, total_slots


def infer_secondary_brackets_from_rules(
    modalidade: str, playoff_rules: Dict, epoch: str = "25_26"
) -> Tuple[List[Tuple[Dict, Dict]], List[Dict]]:
    """Inferir liguilhas (LM) ou playoffs (PM) das regras quando não há no CSV."""
    if not playoff_rules:
        return [], []

    epoch_data = playoff_rules.get("epochs", {}).get(epoch, {})
    mod_rules = epoch_data.get("modalidades", {}).get(modalidade, {})
    if not mod_rules:
        return [], []

    bracket_type = mod_rules.get("secondary_bracket")
    n_groups_2nd = mod_rules.get("n_groups_2nd_div", 0)
    direct_relegation = mod_rules.get("directRelegation", 3)

    pm1 = []
    lm = []

    # O "maintenance slot" da 1ª divisão é geralmente o 1º acima da zona de descida direta.
    # Ex: se descem 3 (pos 12, 11, 10), a manutenção é o 9º (pos total - 3).
    # Como não sabemos o total aqui, usamos kind: "maintenance" para resolver depois.
    maintenance_slot = {"kind": "maintenance", "div": 1, "offset": direct_relegation}

    if bracket_type == "LM":
        # LM: 2º de cada grupo da 2ª + maintenance da 1ª
        participants = []
        for i in range(n_groups_2nd):
            grp_name = chr(ord("A") + i)
            participants.append({"kind": "slot", "pos": 2, "div": 2, "grp": grp_name})
        participants.append(maintenance_slot)

        # Gerar confrontos todos-contra-todos (round-robin)
        for i in range(len(participants)):
            for j in range(i + 1, len(participants)):
                lm.append({"a": participants[i], "b": participants[j], "jornada": "LM"})

    elif bracket_type == "PM":
        # PM: Geralmente Meias-Finais: (Maint 1ª vs 2º Gr.C) e (2º Gr.A vs 2º Gr.B)?
        # Regras Tacaua: 2º de cada grupo 2ª + 4º pior 1ª.
        # Se 3 grupos (A, B, C):
        # MF1: Maintenance vs 2º Gr.C
        # MF2: 2º Gr.A vs 2º Gr.B
        if n_groups_2nd == 3:
            pm1.append(
                (maintenance_slot, {"kind": "slot", "pos": 2, "div": 2, "grp": "C"})
            )
            pm1.append(
                (
                    {"kind": "slot", "pos": 2, "div": 2, "grp": "A"},
                    {"kind": "slot", "pos": 2, "div": 2, "grp": "B"},
                )
            )
        elif n_groups_2nd == 2:
            # Se fosse PM com 2 grupos, seria Maint vs 2ºA e 2ºB? (Pouco comum)
            pm1.append(
                (maintenance_slot, {"kind": "slot", "pos": 2, "div": 2, "grp": "A"})
            )
            # Faltaria um adversário para 2ºB se for playoff. Se for liguilha, usa LM.

    return pm1, lm


def parse_secondary_playoff_structure(
    csv_rows: List[Dict], course_mapping: Dict[str, str] = None
) -> List[Tuple[Dict[str, Any], Dict[str, Any]]]:
    """Extrai os confrontos PM1 definidos no CSV.

    Cada confronto é devolvido como dois descritores de slot:
    - {"kind": "slot", "pos": <int>, "div": <int>, "grp": <str>}
    - {"kind": "team", "name": <str>} para nomes explícitos.

    Ignora placeholders de vencedor/perdedor (ex.: "Vencedor MF1"),
    pois esses são simulados dinamicamente a partir das meias PM1.
    """
    pattern = re.compile(
        r"(\d+)[ºo]?\s*Class\.\s*(\d+)[ªa]?\s*Div\.?\s*(?:Gr\.\s*)?([A-Za-z0-9]+)?",
        re.IGNORECASE,
    )

    def parse_entry(raw_value: Any) -> Dict[str, Any] | None:
        raw = str(raw_value or "").strip()
        if not raw:
            return None

        upper = raw.upper()
        if (
            upper.startswith("VENCEDOR")
            or upper.startswith("PERDEDOR")
            or upper.startswith("VENCIDO")
        ):
            return None

        match = pattern.search(raw)
        if match:
            return {
                "kind": "slot",
                "pos": int(match.group(1)),
                "div": int(match.group(2)),
                "grp": (match.group(3) or "").upper(),
            }

        name_norm = normalize_team_name(raw, course_mapping) if course_mapping else raw
        return {"kind": "team", "name": name_norm}

    pm1_pairs: List[Tuple[Dict[str, Any], Dict[str, Any]]] = []
    for row in csv_rows:
        jornada_val = str(row.get(COL_JORNADA, "")).strip().upper()
        if not jornada_val.startswith("PM1"):
            continue

        entry_a = parse_entry(row.get(COL_EQUIPA_1, ""))
        entry_b = parse_entry(row.get(COL_EQUIPA_2, ""))
        if entry_a and entry_b:
            pm1_pairs.append((entry_a, entry_b))

    return pm1_pairs


def parse_secondary_liguilla_structure(
    csv_rows: List[Dict], course_mapping: Dict[str, str] = None
) -> List[Dict[str, Any]]:
    """Extrai os jogos da liguilha (LM) definidos no CSV.

    A liguilha é tratada como uma mini-liga: as linhas LM do calendário são
    convertidas em confrontos que serão simulados com empates permitidos e
    classificação por pontos + desempates do campeonato normal.
    """
    pattern = re.compile(
        r"(\d+)[ºo]?\s*Class\.\s*(\d+)[ªa]?\s*Div\.?\s*(?:Gr\.\s*)?([A-Za-z0-9]+)?",
        re.IGNORECASE,
    )

    def parse_entry(raw_value: Any) -> Dict[str, Any] | None:
        raw = str(raw_value or "").strip()
        if not raw:
            return None

        upper = raw.upper()
        if (
            upper.startswith("VENCEDOR")
            or upper.startswith("PERDEDOR")
            or upper.startswith("VENCIDO")
        ):
            return None

        match = pattern.search(raw)
        if match:
            return {
                "kind": "slot",
                "pos": int(match.group(1)),
                "div": int(match.group(2)),
                "grp": (match.group(3) or "").upper(),
            }

        name_norm = normalize_team_name(raw, course_mapping) if course_mapping else raw
        return {"kind": "team", "name": name_norm}

    liguilla_matches: List[Dict[str, Any]] = []
    for row in csv_rows:
        jornada_val = str(row.get(COL_JORNADA, "")).strip().upper()
        if not jornada_val.startswith("LM"):
            continue

        entry_a = parse_entry(row.get(COL_EQUIPA_1, ""))
        entry_b = parse_entry(row.get(COL_EQUIPA_2, ""))
        if not entry_a or not entry_b:
            continue

        jornada_num = re.search(r"\d+", jornada_val)
        liguilla_matches.append(
            {
                "jornada": str(row.get(COL_JORNADA, "")).strip(),
                "order": int(jornada_num.group(0)) if jornada_num else 0,
                "a": entry_a,
                "b": entry_b,
            }
        )

    return liguilla_matches


# Normalizar nome do curso usando o mapeamento
# Normalizar nome do curso usando o mapeamento
def is_valid_team(team_name: str) -> bool:
    """Verifica se o nome é de uma equipa válida."""
    invalid_keywords = [
        "Class.",
        "Vencedor",
        "Vencido",
        "QF",
        "MF",
        "QF1",
        "QF2",
        "QF3",
        "QF4",
        "PM1",
        "PM2",
        "LM1",
        "LM2",
        "LM3",
    ]
    for keyword in invalid_keywords:
        if keyword in team_name:
            return False
    return True


def is_b_team(name: str) -> bool:
    """Verifica se uma equipa é equipa B."""
    return name.strip().endswith(" B")


def base_team(name: str) -> str:
    """Retorna o nome base da equipa (sem o B)."""
    return name[:-2].strip() if is_b_team(name) else name


def calculate_real_points(
    past_matches_rows: List[Dict],
    course_mapping: Dict[str, str],
    withdrawn_teams: Set[str] = None,
    modalidade: str | None = None,
) -> Dict[str, int]:
    """
    Calcula os pontos reais já alcançados pelas equipas na época regular.

    Retorna dicionário: {team_name: real_points}
    Jogos contra equipas desistentes são ignorados.
    """
    if withdrawn_teams is None:
        withdrawn_teams = set()
    real_points = defaultdict(int)
    is_volei = bool(modalidade and str(modalidade).upper().startswith("VOLEIBOL"))

    for row in past_matches_rows:
        team_a_raw = row[COL_EQUIPA_1].strip()
        team_b_raw = row[COL_EQUIPA_2].strip()

        if not is_valid_team(team_a_raw) or not is_valid_team(team_b_raw):
            continue

        team_a = normalize_team_name(team_a_raw, course_mapping)
        team_b = normalize_team_name(team_b_raw, course_mapping)

        # Ignorar jogos que envolvam equipas desistentes
        if team_a in withdrawn_teams or team_b in withdrawn_teams:
            continue

        golos_1_str = str(row.get(COL_GOLOS_1, "")).strip()
        golos_2_str = str(row.get(COL_GOLOS_2, "")).strip()
        falta = str(row.get(COL_FALTA_COMPARENCIA, "")).strip()

        if not golos_1_str or not golos_2_str:
            if falta:
                # Se há falta mas não há golos, inferir 3-0 ou 0-3 (ou 2-0 para volei)
                # O nome na coluna falta é a equipa que FALTOU.
                falta_norm = normalize_team_name(falta, course_mapping)
                if falta_norm == team_a:
                    golos_1, golos_2 = (0, 3 if not is_volei else 2)
                elif falta_norm == team_b:
                    golos_1, golos_2 = (3 if not is_volei else 2, 0)
                else:
                    # Caso estranho onde a equipa na coluna falta não bate com as do jogo
                    continue
            else:
                continue
        else:
            try:
                # Converter para float primeiro (CSV pode ter "4.0"), depois int
                golos_1 = int(float(golos_1_str))
                golos_2 = int(float(golos_2_str))
            except ValueError:
                continue

        # Distribuir pontos de acordo com a modalidade.
        # No voleibol o CSV guarda sets (2-0, 2-1, 1-2, 0-2), não uma regra 3/1/0.
        if is_volei:
            if golos_1 == 2 and golos_2 == 0:
                real_points[team_a] += 3
            elif golos_1 == 2 and golos_2 == 1:
                real_points[team_a] += 2
                real_points[team_b] += 1
            elif golos_1 == 1 and golos_2 == 2:
                real_points[team_a] += 1
                real_points[team_b] += 2
            elif golos_1 == 0 and golos_2 == 2:
                real_points[team_b] += 3
            elif golos_1 > golos_2:
                real_points[team_a] += 3
            elif golos_2 > golos_1:
                real_points[team_b] += 3
        else:
            if golos_1 > golos_2:
                real_points[team_a] += 3
            elif golos_2 > golos_1:
                real_points[team_b] += 3
            else:
                # Empate
                real_points[team_a] += 1
                real_points[team_b] += 1

    return dict(real_points)


def extract_played_matches_for_tiebreak(
    past_matches_rows: List[Dict],
    course_mapping: Dict[str, str],
    withdrawn_teams: Set[str] = None,
    modalidade: str | None = None,
) -> List[Tuple[str, str, int, int]]:
    """Extrai jogos concluídos para desempates (h2h e critérios gerais)."""
    if withdrawn_teams is None:
        withdrawn_teams = set()

    played_matches: List[Tuple[str, str, int, int]] = []

    for row in past_matches_rows:
        team_a_raw = row.get(COL_EQUIPA_1, "").strip()
        team_b_raw = row.get(COL_EQUIPA_2, "").strip()
        if not is_valid_team(team_a_raw) or not is_valid_team(team_b_raw):
            continue

        team_a = normalize_team_name(team_a_raw, course_mapping)
        team_b = normalize_team_name(team_b_raw, course_mapping)
        if team_a in withdrawn_teams or team_b in withdrawn_teams:
            continue

        score_a_raw = row.get(COL_GOLOS_1, "").strip()
        score_b_raw = row.get(COL_GOLOS_2, "").strip()
        falta = str(row.get(COL_FALTA_COMPARENCIA, "")).strip()
        is_volei = bool(modalidade and str(modalidade).upper().startswith("VOLEIBOL"))

        if not score_a_raw or not score_b_raw:
            if falta:
                falta_norm = normalize_team_name(falta, course_mapping)
                if falta_norm == team_a:
                    score_a, score_b = (0, 3 if not is_volei else 2)
                elif falta_norm == team_b:
                    score_a, score_b = (3 if not is_volei else 2, 0)
                else:
                    continue
            else:
                continue
        else:
            try:
                score_a = int(float(score_a_raw))
                score_b = int(float(score_b_raw))
            except ValueError:
                continue

        played_matches.append((team_a, team_b, score_a, score_b))

    return played_matches


def separate_past_and_future_matches(
    csv_rows: List[Dict],
) -> Tuple[List[Dict], List[Dict]]:
    """
    Separa jogos passados (com resultados) de jogos futuros (sem resultados).

    Retorna (past_matches, future_matches)
    """
    past_matches = []
    future_matches = []

    for row in csv_rows:
        golos_1 = str(row.get(COL_GOLOS_1, "")).strip()
        golos_2 = str(row.get(COL_GOLOS_2, "")).strip()
        falta = str(row.get(COL_FALTA_COMPARENCIA, "")).strip()

        # Se ambos os scores estão preenchidos OU há falta de comparência, é um jogo passado
        if (golos_1 and golos_2) or falta:
            past_matches.append(row)
        else:
            future_matches.append(row)

    return past_matches, future_matches


def simulate_match(
    team_a: Team,
    team_b: Team,
    elo_system: CompleteTacauaEloSystem,
    score_simulator: SportScoreSimulator,
    total_group_games: int = 10,
    is_playoff: bool = False,
    division: int | None = None,
    hardset_manager: "HardsetManager | None" = None,
    match_id: str | None = None,
) -> Tuple[str, int, int, int]:
    """
    Simula um jogo com sistema ELO completo.

    Quando hardset_manager e match_id são fornecidos e o jogo tiver resultado
    fixado, usa esse resultado em vez de simular aleatoriamente.

    Args:
        team_a, team_b: Equipas
        elo_system: Sistema ELO
        score_simulator: Simulador de resultados
        total_group_games: Total de jogos para cálculo de K_factor
        is_playoff: Se True, força vencedor (sem empates em desportos que suportam prolongamento)
        division: Divisão do jogo (para baselines por divisão)
        hardset_manager: Gestor de resultados fixados (opcional)
        match_id: ID do jogo para lookup no hardset_manager (opcional)

    Retorna (vencedor, margem, score_a, score_b).
    Atualiza ELOs das equipas.
    """
    # Verificar se há resultado fixado
    if hardset_manager and match_id and hardset_manager.has_fixed_result(match_id):
        fixed = hardset_manager.get_fixed_result(match_id)
        score1, score2 = fixed.score_a, fixed.score_b
    else:
        score1, score2 = score_simulator.simulate_score(
            team_a.elo,
            team_b.elo,
            force_winner=is_playoff,
            division=division,
        )

    margin = abs(score1 - score2)

    if score1 > score2:
        winner_name = team_a.name
    elif score2 > score1:
        winner_name = team_b.name
    else:
        winner_name = "Draw"

    delta_a, delta_b = elo_system.calculate_elo_change(
        team_a.elo,
        team_b.elo,
        score1,
        score2,
        team_a.games_played + 1,
        team_b.games_played + 1,
        total_group_games,
        total_group_games,
    )

    team_a.elo += delta_a
    team_b.elo += delta_b
    team_a.games_played += 1
    team_b.games_played += 1

    return winner_name, margin, score1, score2


def _preprocess_fixtures(
    fixtures: List[Dict],
    teams: Dict[str, "Team"],
) -> List[Tuple]:
    """Pré-processa fixtures uma vez por execução de main(), não por simulação.

    Converte cada fixture num named-tuple leve:
        (a, b, match_id, division, is_future, total_games_a)

    Ao pré-computar total_games e division aqui, eliminamos O(N_teams × N_fixtures)
    trabalho que antes se repetia em cada uma das 10 000+ simulações.

    Deve ser chamado ANTES de monte_carlo_forecast, com as fixtures já filtradas.
    O resultado é passado ao worker em vez da lista de dicts original.
    """
    # total_games por equipa (para K-factor do ELO)
    total_games: Dict[str, int] = {}
    for team_name in teams:
        count = sum(1 for m in fixtures if team_name in (m["a"], m["b"]))
        total_games[team_name] = count if count > 0 else 1

    processed = []
    for match in fixtures:
        div_raw = str(match.get("divisao", "")).strip()
        division = None
        if div_raw:
            try:
                division = int(div_raw)
            except ValueError:
                pass

        processed.append(
            (
                match["a"],
                match["b"],
                match.get("id"),
                division,
                bool(match.get("is_future")),
                total_games.get(match["a"], 1),
                # preservar campos de output para o CSV de previsões
                match.get("jornada", ""),
                match.get("dia", ""),
                match.get("hora", ""),
                match.get("grupo", ""),
            )
        )
    return processed


def simulate_season(
    teams: Dict[str, "Team"],
    preprocessed_fixtures: List[Tuple],
    elo_system: "CompleteTacauaEloSystem",
    score_simulator: "SportScoreSimulator",
    hardset_manager: "HardsetManager | None" = None,
) -> Tuple[Dict[str, int], Dict[str, float], Dict[str, float], Dict]:
    """Simula uma época completa com sistema ELO completo.

    Recebe `preprocessed_fixtures` (saída de `_preprocess_fixtures`) em vez
    da lista de dicts raw. Isto elimina a reanálise de strings e o cálculo
    de total_games em cada uma das 10k+ simulações.

    Quando hardset_manager é fornecido, expected_points é calculado com base
    no resultado real (hardsets ficam visíveis nos expected_points).

    Retorna (points, expected_points, final_elos, season_results).
    season_results só inclui jogos futuros (is_future=True), que são os únicos
    consultados pelo worker — jogos passados eram overhead desnecessário.
    """
    use_hardset = hardset_manager is not None

    points: Dict[str, int] = defaultdict(int)
    expected_points: Dict[str, float] = defaultdict(float)
    # Apenas jogos futuros entram em season_results (reduz alocações ~50%)
    season_results: Dict[str, Dict] = {}

    for (
        a,
        b,
        match_id,
        division,
        is_future,
        total_games_a,
        jornada,
        _dia,
        _hora,
        _grupo,
    ) in preprocessed_fixtures:

        # Jogos de playoff/eliminatórias não contam para os pontos da fase regular
        # (Jornadas que começam por E, PM, LM)
        is_regular_season = not str(jornada).upper().startswith(("E", "PM", "LM"))

        elo_a_before = teams[a].elo
        elo_b_before = teams[b].elo

        if not use_hardset:
            p_a = elo_system.elo_win_probability(elo_a_before, elo_b_before)
            target_draw_rate = score_simulator._get_division_draw_rate(division)
            p_draw = score_simulator._calculate_draw_probability(
                elo_a_before, elo_b_before, target_draw_rate
            )
            p_a_adj = p_a * (1 - p_draw)
            p_b_adj = (1 - p_a) * (1 - p_draw)
            if is_regular_season:
                expected_points[a] += p_a_adj * 3 + p_draw
                expected_points[b] += p_b_adj * 3 + p_draw

        winner, margin, score_a, score_b = simulate_match(
            teams[a],
            teams[b],
            elo_system,
            score_simulator,
            total_games_a,
            division=division,
            hardset_manager=hardset_manager,
            match_id=match_id,
        )

        # Guardar resultado apenas para jogos futuros (worker só consulta esses)
        if is_future and match_id:
            season_results[match_id] = (
                winner,
                score_a,
                score_b,
                elo_a_before,
                elo_b_before,
            )

        if winner == a:
            if is_regular_season:
                points[a] += 3
                if use_hardset:
                    expected_points[a] += 3
        elif winner == b:
            if is_regular_season:
                points[b] += 3
                if use_hardset:
                    expected_points[b] += 3
        elif winner == "Draw":
            if is_regular_season:
                points[a] += 1
                points[b] += 1
                if use_hardset:
                    expected_points[a] += 1
                    expected_points[b] += 1

    final_elos = {team: teams[team].elo for team in teams}
    return points, dict(expected_points), final_elos, season_results


def simulate_playoffs(
    teams: Dict[str, Team],
    ranking: List[Tuple[str, int]],
    elo_system: CompleteTacauaEloSystem,
    score_simulator: SportScoreSimulator,
    exclude_teams: Set[str] | None = None,
) -> Tuple[str, List[str], List[str], List[Dict]]:
    """
    Simula playoffs com árvore de eliminatória.
    Top 8 entram nos playoffs (quartos, semifinais e final).
    Retorna (campeão, [semifinalistas], [finalistas], list_of_playoff_matches).

    IMPORTANTE: Os ELOs dos teams são MODIFICADOS durante os playoffs.
    Para não contaminar as simulações seguintes, este método deve ser chamado
    com uma CÓPIA profunda dos teams (não os teams originais).

    Todos os jogos de playoff usam force_winner=True para garantir vencedor,
    sem depender de sorteio em caso de empate.

    Equipas B não podem ir aos playoffs - se estiverem no top 8, a próxima
    equipa não-B ocupa a posição.
    """
    # Filtrar equipas B do ranking e qualquer equipa já eliminada em jogos de playoff reais
    exclude_teams = exclude_teams or set()
    eligible_ranking = [
        (team, pts)
        for team, pts in ranking
        if not is_b_team(team) and team not in exclude_teams
    ]

    if len(eligible_ranking) < 2:
        champion = eligible_ranking[0][0] if eligible_ranking else None
        return (champion, [], [champion] if champion else [], [])

    playoff_matches = []

    # Helper para simular jogo eliminatório com vencedor garantido
    def resolve_match(team_a_name: str, team_b_name: str, stage: str) -> str:
        elo_a = teams[team_a_name].elo
        elo_b = teams[team_b_name].elo
        winner, _margin, score_a, score_b = simulate_match(
            teams[team_a_name],
            teams[team_b_name],
            elo_system,
            score_simulator,
            is_playoff=True,  # CRUCIAL: força vencedor
            division=None,
        )
        t1, t2 = sorted([team_a_name, team_b_name])
        match_id = f"PLAYOFF_STAGE|{stage}|{t1}|{t2}"
        playoff_matches.append(
            {
                "id": match_id,
                "a": t1,
                "b": t2,
                "winner": winner,
                "score_a": score_a if t1 == team_a_name else score_b,
                "score_b": score_b if t1 == team_a_name else score_a,
                "elo_a": elo_a if t1 == team_a_name else elo_b,
                "elo_b": elo_b if t1 == team_a_name else elo_a,
                "stage": stage,
            }
        )
        return winner

    # Determinar quantas equipas estão disponíveis para playoffs (apenas não-B)
    num_teams_for_playoffs = min(8, len(eligible_ranking))

    loser_sf1 = None
    loser_sf2 = None

    if num_teams_for_playoffs < 4:
        # Se menos de 4, fazer semifinal entre 1º e 2º
        finalist_a = eligible_ranking[0][0]
        finalist_b = eligible_ranking[1][0]
        semifinalists = [finalist_a, finalist_b]
    elif num_teams_for_playoffs < 8:
        # Se 4-7 equipas, fazer top 4 tradicional
        semi1_a = eligible_ranking[0][0]
        semi1_b = eligible_ranking[3][0]

        semi2_a = eligible_ranking[1][0]
        semi2_b = eligible_ranking[2][0]

        semifinalists = [semi1_a, semi1_b, semi2_a, semi2_b]

        winner_sf1 = resolve_match(semi1_a, semi1_b, "Semifinais")
        winner_sf2 = resolve_match(semi2_a, semi2_b, "Semifinais")

        finalist_a = winner_sf1
        finalist_b = winner_sf2
        loser_sf1 = semi1_a if finalist_a == semi1_b else semi1_b
        loser_sf2 = semi2_a if finalist_b == semi2_b else semi2_b
    else:
        # 8 equipas: quartos (1v8, 2v7, 3v6, 4v5), depois semifinais
        qf1_a = eligible_ranking[0][0]  # 1º
        qf1_b = eligible_ranking[7][0]  # 8º

        qf2_a = eligible_ranking[1][0]  # 2º
        qf2_b = eligible_ranking[6][0]  # 7º

        qf3_a = eligible_ranking[2][0]  # 3º
        qf3_b = eligible_ranking[5][0]  # 6º

        qf4_a = eligible_ranking[3][0]  # 4º
        qf4_b = eligible_ranking[4][0]  # 5º

        # Simulação dos quartos
        winner_qf1 = resolve_match(qf1_a, qf1_b, "Quartos")
        winner_qf2 = resolve_match(qf2_a, qf2_b, "Quartos")
        winner_qf3 = resolve_match(qf3_a, qf3_b, "Quartos")
        winner_qf4 = resolve_match(qf4_a, qf4_b, "Quartos")

        semifinalists = [winner_qf1, winner_qf2, winner_qf3, winner_qf4]

        # Simulação das semifinais
        winner_sf1 = resolve_match(winner_qf1, winner_qf2, "Semifinais")
        winner_sf2 = resolve_match(winner_qf3, winner_qf4, "Semifinais")

        finalist_a = winner_sf1
        finalist_b = winner_sf2
        loser_sf1 = winner_qf1 if finalist_a == winner_qf2 else winner_qf2
        loser_sf2 = winner_qf3 if finalist_b == winner_qf4 else winner_qf4

    # Final e 3º Lugar
    finalists = [finalist_a, finalist_b]
    champion = resolve_match(finalist_a, finalist_b, "Final")
    if loser_sf1 and loser_sf2:
        resolve_match(loser_sf1, loser_sf2, "3º Lugar")

    return (champion, semifinalists, finalists, playoff_matches)


def _points_from_score(score_a: int, score_b: int) -> Tuple[int, int]:
    """Regra de pontos atualmente usada no preditor (3/1/0)."""
    if score_a > score_b:
        return 3, 0
    if score_b > score_a:
        return 0, 3
    return 1, 1


def _points_from_score_for_modalidade(
    score_a: int, score_b: int, modalidade: str | None = None
) -> Tuple[int, int]:
    """Calcula pontos por jogo, com regra especial para voleibol."""
    if modalidade and str(modalidade).upper().startswith("VOLEIBOL"):
        if score_a == 2 and score_b == 0:
            return 3, 0
        if score_a == 2 and score_b == 1:
            return 2, 1
        if score_a == 1 and score_b == 2:
            return 1, 2
        if score_a == 0 and score_b == 2:
            return 0, 3

    return _points_from_score(score_a, score_b)


def _rank_group_with_tiebreak(
    group_teams: List[str],
    points: Dict[str, int],
    played_matches: List[Tuple[str, str, int, int]],
    modalidade: str | None = None,
) -> List[str]:
    """Ordena equipas de um grupo com critérios de desempate do mmr_taçaua."""
    if not group_teams:
        return []

    team_set = set(group_teams)
    global_stats = {t: {"gf": 0, "ga": 0} for t in group_teams}

    for team_a, team_b, score_a, score_b in played_matches:
        if team_a in team_set:
            global_stats[team_a]["gf"] += score_a
            global_stats[team_a]["ga"] += score_b
        if team_b in team_set:
            global_stats[team_b]["gf"] += score_b
            global_stats[team_b]["ga"] += score_a

    base_sorted = sorted(group_teams, key=lambda t: (-points.get(t, 0), t))
    resolved: List[str] = []
    idx = 0

    while idx < len(base_sorted):
        tie_points = points.get(base_sorted[idx], 0)
        tied = [base_sorted[idx]]
        idx += 1

        while idx < len(base_sorted) and points.get(base_sorted[idx], 0) == tie_points:
            tied.append(base_sorted[idx])
            idx += 1

        if len(tied) == 1:
            resolved.extend(tied)
            continue

        tied_set = set(tied)
        h2h_stats = {t: {"points": 0, "gf": 0, "ga": 0} for t in tied}

        for team_a, team_b, score_a, score_b in played_matches:
            if team_a not in tied_set or team_b not in tied_set:
                continue

            p_a, p_b = _points_from_score_for_modalidade(score_a, score_b, modalidade)
            h2h_stats[team_a]["points"] += p_a
            h2h_stats[team_b]["points"] += p_b
            h2h_stats[team_a]["gf"] += score_a
            h2h_stats[team_a]["ga"] += score_b
            h2h_stats[team_b]["gf"] += score_b
            h2h_stats[team_b]["ga"] += score_a

        # Ordem equivalente ao mmr_taçaua para critérios disponíveis aqui:
        # Para modalidades com liga única (Futsal Feminino e Basket Feminino):
        # 1. Diferença de golos geral
        # 2. Confronto direto (pontos, diferença, golos)
        # 3. Golos marcados gerais
        # Para outras modalidades:
        # Confronto direto -> Diferença de golos geral -> Golos marcados gerais
        is_single_league = False
        if modalidade:
            norm_mod = modalidade.upper().strip()
            is_single_league = norm_mod in ("FUTSAL FEMININO", "BASQUETEBOL FEMININO")

        if is_single_league:
            tied_sorted = sorted(
                tied,
                key=lambda t: (
                    -(global_stats[t]["gf"] - global_stats[t]["ga"]),  # 1º Diferença de golos geral
                    -h2h_stats[t]["points"],                           # 2º Pontos H2H
                    -(h2h_stats[t]["gf"] - h2h_stats[t]["ga"]),        # 3º Diferença de golos H2H
                    -h2h_stats[t]["gf"],                               # 4º Golos marcados H2H
                    -global_stats[t]["gf"],                            # 5º Golos marcados gerais
                    t,
                ),
            )
        else:
            tied_sorted = sorted(
                tied,
                key=lambda t: (
                    -h2h_stats[t]["points"],
                    -(h2h_stats[t]["gf"] - h2h_stats[t]["ga"]),
                    -h2h_stats[t]["gf"],
                    -(global_stats[t]["gf"] - global_stats[t]["ga"]),
                    -global_stats[t]["gf"],
                    t,
                ),
            )
        resolved.extend(tied_sorted)

    return resolved


def build_ranking_with_tiebreak(
    points: Dict[str, int],
    team_division: Dict[str, Tuple[int, str]],
    played_matches: List[Tuple[str, str, int, int]],
    modalidade: str | None = None,
) -> Tuple[List[Tuple[str, int]], Dict[Tuple[int, str], List[str]]]:
    """Constrói ranking global e por grupo/divisão já com desempate aplicado."""
    if not team_division:
        teams = list(points.keys())
        ordered = _rank_group_with_tiebreak(
            teams, points, played_matches, modalidade=modalidade
        )
        return [(t, points.get(t, 0)) for t in ordered], {(1, ""): ordered}

    groups: Dict[Tuple[int, str], List[str]] = defaultdict(list)
    for team in points:
        groups[team_division.get(team, (1, ""))].append(team)

    ranked_by_group: Dict[Tuple[int, str], List[str]] = {}
    ranking: List[Tuple[str, int]] = []
    for group_key in sorted(groups.keys(), key=lambda k: (k[0], k[1])):
        ordered = _rank_group_with_tiebreak(
            groups[group_key], points, played_matches, modalidade=modalidade
        )
        ranked_by_group[group_key] = ordered
        ranking.extend((t, points.get(t, 0)) for t in ordered)

    return ranking, ranked_by_group


def calculate_promotions_relegations(
    points: Dict[str, int],
    team_division: Dict[str, Tuple[int, str]],
    sim_teams: Dict[str, Team],
    has_liguilla: bool,
    ranked_by_group: Dict[Tuple[int, str], List[str]] = None,
    withdrawn_teams: Set[str] = None,
    secondary_liguilla_top_team: str | None = None,
) -> Tuple[Set[str], Set[str]]:
    if not team_division:
        return set(), set()

    # Construir standings por divisão/grupo (com desempate quando já disponível)
    div_points: Dict[int, Dict[str, List[Tuple[str, int]]]] = defaultdict(
        lambda: defaultdict(list)
    )
    if ranked_by_group:
        for (div, grp), ordered_teams in ranked_by_group.items():
            div_points[div][grp] = [
                (team, points.get(team, 0)) for team in ordered_teams
            ]
    else:
        for team, pts in points.items():
            div, grp = team_division.get(team, (1, ""))
            div_points[div][grp].append((team, pts))

        for div in div_points:
            for grp in div_points[div]:
                div_points[div][grp] = sorted(
                    div_points[div][grp], key=lambda x: x[1], reverse=True
                )

    # Detectar grupos na 2ª divisão
    div2_groups = div_points.get(2, {})
    num_groups_div2 = len(div2_groups)
    ranking_div1 = []
    for grp_list in div_points.get(1, {}).values():
        ranking_div1.extend(grp_list)
    ranking_div1 = sorted(ranking_div1, key=lambda x: x[1], reverse=True)

    protected_as = set()
    promoted = set()
    relegated = set()

    # Equipas desistentes da 1ª divisão já desceram automaticamente.
    # Cada desistente "ocupa" uma vaga de descida, reduzindo as vagas
    # disponíveis para as equipas que completaram a época.
    withdrawn_div1: Set[str] = set()
    if withdrawn_teams:
        for t in withdrawn_teams:
            div, _ = team_division.get(t, (None, ""))
            if div == 1:
                withdrawn_div1.add(t)
    n_withdrawn_div1 = len(withdrawn_div1)

    # Helper para escolher próximo não-B
    def next_non_b(lst):
        return next((t for t in lst if not is_b_team(t)), None)

    if num_groups_div2 == 0:
        pass
    elif num_groups_div2 == 1:
        group_key = next(iter(div2_groups))
        promo = []
        for t, _ in div2_groups[group_key][:]:
            if not is_b_team(t):
                promo.append(t)
            if len(promo) == 2:
                break
        promoted.update(promo)
        # proteção A
        for t in promo:
            if is_b_team(t):
                protected_as.add(base_team(t))
        # relegar os últimos não protegidos (2 vagas menos as já ocupadas por desistentes)
        max_relegations = max(0, 2 - n_withdrawn_div1)
        down_list = [t for t, _ in reversed(ranking_div1)]
        for t in down_list:
            if t in protected_as:
                continue
            if len(relegated) < max_relegations:
                relegated.add(t)
        # Se B promove, protege A
    elif num_groups_div2 == 2:
        # Se há liguilha (LM presente) usa regra de 3 equipas: 2 ficam na 1ª, 1 desce
        if has_liguilla:
            down_list = [t for t, _ in reversed(ranking_div1)]
            # Descem diretos os 3 ultimos (4o a contar do fim vai a liguilha)
            # Deduzir vagas já ocupadas por desistentes da 1ª divisão
            max_direct_rel = max(0, 3 - n_withdrawn_div1)
            for t in down_list:
                if t in protected_as:
                    continue
                if len(relegated) < max_direct_rel:
                    relegated.add(t)

            grp_keys = list(div2_groups.keys())
            top_a = (
                next_non_b([t for t, _ in div2_groups[grp_keys[0]]])
                if grp_keys
                else None
            )
            top_b = (
                next_non_b([t for t, _ in div2_groups[grp_keys[1]]])
                if len(grp_keys) > 1
                else None
            )

            # Sobem diretos os 1os de cada grupo (2a divisao)
            if top_a:
                promoted.add(top_a)
            if top_b:
                promoted.add(top_b)

            # Liguillha: 2os de cada grupo + 4o a contar do fim da 1a divisao
            second_a = (
                next_non_b([t for t, _ in div2_groups[grp_keys[0]][1:]])
                if grp_keys and len(div2_groups[grp_keys[0]]) > 1
                else None
            )
            second_b = (
                next_non_b([t for t, _ in div2_groups[grp_keys[1]][1:]])
                if len(grp_keys) > 1 and len(div2_groups[grp_keys[1]]) > 1
                else None
            )
            fourth_worst = down_list[3] if len(down_list) >= 4 else None
            candidates = [c for c in [second_a, second_b, fourth_worst] if c]

            if candidates:
                # Usa o resultado simulado da liguilha quando disponível.
                # Fallback por ELO mantém compatibilidade com execuções antigas.
                winner = secondary_liguilla_top_team
                if not winner or winner not in candidates:
                    winner = max(
                        candidates,
                        key=lambda t: sim_teams.get(t, Team(t, 750)).elo,
                    )
                # So ha promocao se o vencedor for da 2a divisao
                if winner != fourth_worst:
                    promoted.add(winner)
                    if fourth_worst:
                        relegated.add(fourth_worst)
                # Se o 4o a contar do fim vencer, mantém-se e nao ha promocao extra
        else:
            # Sem liguilha: sobem 2 por grupo, descem 4 (menos desistentes da 1ª)
            for grp_list in div2_groups.values():
                promo_grp = []
                for t, _ in grp_list:
                    if not is_b_team(t):
                        promo_grp.append(t)
                    if len(promo_grp) == 2:
                        break
                promoted.update(promo_grp)
            max_relegations = max(0, 4 - n_withdrawn_div1)
            down_list = [t for t, _ in reversed(ranking_div1)]
            for t in down_list:
                if t in protected_as:
                    continue
                if len(relegated) < max_relegations:
                    relegated.add(t)
    elif num_groups_div2 == 3:
        # 3 sobem diretos (1º de cada grupo)
        seconds = []
        for grp_list in div2_groups.values():
            # direct
            for t, _ in grp_list:
                if not is_b_team(t):
                    promoted.add(t)
                    break
            # collect second for playoff
            sec = (
                next_non_b([t for t, _ in grp_list[1:]]) if len(grp_list) > 1 else None
            )
            if sec:
                seconds.append(sec)
        # descem os últimos diretos (3 vagas menos as já ocupadas por desistentes da 1ª)
        max_direct_rel = max(0, 3 - n_withdrawn_div1)
        down_list = [t for t, _ in reversed(ranking_div1)]
        for t in down_list[:max_direct_rel]:
            if t in protected_as:
                continue
            relegated.add(t)
        # playoff dos segundos com (max_direct_rel+1)º pior da 1ª
        # (a posição do "4º pior" desloca-se se houver desistentes)
        playoff_pos = max_direct_rel  # índice do elemento após os descidos diretos
        if len(ranking_div1) > playoff_pos:
            fourth_worst = down_list[playoff_pos]
            candidates = seconds + [fourth_worst]
            # Escolhe melhor por ELO
            winner = max(candidates, key=lambda t: sim_teams.get(t, Team(t, 750)).elo)
            if winner != fourth_worst:
                relegated.add(fourth_worst)
                promoted.add(winner)

    # Proteção de A se B promove: se equipa B sobe, a equipa A fica protegida
    for t in list(promoted):
        if is_b_team(t):
            a_team = base_team(t)
            protected_as.add(a_team)
    # Remove equipas protegidas da relegação
    relegated = {t for t in relegated if t not in protected_as}

    return promoted, relegated


# ============================================================================
# DETECÇÃO DE THREADS E FUNÇÕES PARALELAS
# ============================================================================


class ProgressTracker:
    """Rastreador simplificado para progresso (tracking no processo principal)."""

    def __init__(self, num_workers: int, n_simulations: int):
        self.num_workers = num_workers
        self.n_simulations = n_simulations
        self.completed = 0
        self.last_percent = 0

    def increment(self) -> None:
        """Incrementa o contador (chamado apenas no processo principal)."""
        self.completed += 1
        current_percent = int((self.completed / self.n_simulations) * 100)

        # Mostrar progresso a cada 5% ou na primeira/última simulação
        if (
            current_percent >= self.last_percent + 5
            or self.completed == 1
            or self.completed == self.n_simulations
        ):

            progress_bar = "▓" * (current_percent // 2)
            progress_bar = progress_bar.ljust(50, "░")
            print(
                f"\r  {progress_bar} {self.completed}/{self.n_simulations} ({current_percent}%)",
                end="",
                flush=True,
            )
            self.last_percent = current_percent

    def print_summary(self) -> None:
        """Imprime sumário final."""
        print(f"\n\n✓ CONCLUÍDO")
        print(f"  Workers usados: {self.num_workers}")
        print(f"  Simulações: {self.completed}/{self.n_simulations}")


def get_num_workers() -> int:
    """
    Detecta e retorna o número de workers/cores disponíveis.
    Usa cpu_count() para ProcessPoolExecutor (bypass do GIL).
    Fallback seguro para ambientes onde cpu_count() falha.
    """
    num_workers = None

    # Tentar multiprocessing.cpu_count() primeiro
    try:
        num_workers = multiprocessing.cpu_count()
    except (NotImplementedError, AttributeError):
        pass

    # Fallback para os.cpu_count() se necessário
    if num_workers is None:
        try:
            num_workers = os.cpu_count()
        except (NotImplementedError, AttributeError):
            pass

    # Garantir valor válido (mínimo 1 worker)
    if num_workers is None or num_workers < 1:
        num_workers = 1

    return num_workers


@functools.lru_cache(maxsize=64)
def _load_csv_rows_cached(csv_file: str) -> tuple:
    """Carrega e cacheia linhas de CSV (lru_cache; imutável — retorna tupla).

    O lru_cache é seguro para uso no processo principal. Cada processo filho
    terá a sua própria cópia do cache (comportamento normal de fork/spawn),
    o que é aceitável dado que os workers não chamam esta função diretamente.

    Returns:
        Tupla de dicionários (imutável para compatibilidade com lru_cache).
    """
    with open(csv_file, newline="", encoding="utf-8-sig") as csvfile:
        return tuple(csv.DictReader(csvfile))


def _clear_csv_cache() -> None:
    """Limpa o cache de CSV (útil em testes ou entre execuções longas)."""
    _load_csv_rows_cached.cache_clear()


def _run_single_simulation_worker(args_tuple) -> SimulationResult:
    """
    Worker unificado para Monte Carlo — suporta modo normal e hardset.

    Recebe preprocessed_fixtures (saída de _preprocess_fixtures) em vez
    da lista de dicts raw, eliminando parsing repetido por simulação.
    """
    (
        sim_idx,
        worker_id,
        teams,
        preprocessed_fixtures,
        elo_system,
        score_simulator,
        n_simulations,
        team_division,
        has_liguilla,
        real_points,
        playoff_slots,
        total_playoff_slots,
        secondary_playoff_pm1,
        secondary_liguilla_rows,
        past_played_matches,
        hardset_manager,
        withdrawn_teams,
        playoff_eliminated_teams,
        playoff_active_winners,
        modalidade,
        playoff_rules,
    ) = args_tuple

    sim_teams = {
        name: Team(name, team.elo, team.games_played) for name, team in teams.items()
    }

    points_future, sim_expected_points, final_elos, season_results = simulate_season(
        sim_teams,
        preprocessed_fixtures,
        elo_system,
        score_simulator,
        hardset_manager=hardset_manager,
    )

    points = {
        team: points_future.get(team, 0) + real_points.get(team, 0) for team in teams
    }

    simulated_played_matches: List[Tuple[str, str, int, int]] = []
    for (a, b, mid, _div, is_future, _tg, *_rest) in preprocessed_fixtures:
        if not is_future or not mid:
            continue
        res = season_results.get(mid)
        if not res:
            continue
        _winner, score_a, score_b, _elo_a, _elo_b = res
        simulated_played_matches.append((a, b, score_a, score_b))

    played_matches_for_tiebreak = (
        list(past_played_matches or []) + simulated_played_matches
    )
    ranking, ranked_by_group = build_ranking_with_tiebreak(
        points,
        team_division,
        played_matches_for_tiebreak,
        modalidade=modalidade,
    )
    # Excluir equipas que já foram eliminadas em jogos de playoff já realizados
    playoff_teams = {
        name: Team(name, final_elos[name])
        for name in final_elos
        if name not in (playoff_eliminated_teams or set())
    }

    # Acumular estatísticas apenas de jogos futuros
    # season_results: {match_id: (winner, score_a, score_b, elo_a_before, elo_b_before)}
    match_stats_sim: Dict = {}
    match_elo_sum_sim: Dict = {}
    match_score_stats_sim: Dict = {}

    for (a, b, mid, _div, is_future, _tg, *_rest) in preprocessed_fixtures:
        if not is_future or not mid:
            continue
        res = season_results.get(mid)
        if not res:
            continue

        winner, score_a, score_b, elo_a, elo_b = res

        # match_stats
        if mid not in match_stats_sim:
            match_stats_sim[mid] = {"1": 0, "X": 0, "2": 0, "total": 0}
        ms = match_stats_sim[mid]
        if winner == a:
            ms["1"] += 1
        elif winner == b:
            ms["2"] += 1
        else:
            ms["X"] += 1
        ms["total"] += 1

        # elo sums
        if mid not in match_elo_sum_sim:
            match_elo_sum_sim[mid] = {
                "a_sum": 0.0,
                "a_sq": 0.0,
                "b_sum": 0.0,
                "b_sq": 0.0,
                "count": 0,
            }
        me = match_elo_sum_sim[mid]
        me["a_sum"] += elo_a
        me["a_sq"] += elo_a * elo_a
        me["b_sum"] += elo_b
        me["b_sq"] += elo_b * elo_b
        me["count"] += 1

        # score distribution
        score_key = f"{score_a}-{score_b}"
        if mid not in match_score_stats_sim:
            match_score_stats_sim[mid] = {}
        sc = match_score_stats_sim[mid]
        sc[score_key] = sc.get(score_key, 0) + 1

    expected_points_sim = {}
    final_elos_sim = {}
    regular_season_places_sim = {}

    for team in teams:
        expected_points_sim[team] = real_points.get(team, 0) + sim_expected_points.get(
            team, 0.0
        )
        final_elos_sim[team] = final_elos.get(team, teams[team].elo)

    standings_by_group_for_places: Dict = {}
    if team_division:
        standings_by_group_for_places = ranked_by_group

        for group_key, group_teams in standings_by_group_for_places.items():
            for place, team in enumerate(group_teams, 1):
                regular_season_places_sim[team] = place
    else:
        for place, (team, _) in enumerate(ranking, 1):
            regular_season_places_sim[team] = place

    playoff_count_sim: Dict = {}
    playoff_bracket_ranking: List[Tuple[str, int]] = []

    # Se há vencedores ativos de playoff (rondas já jogadas), usar APENAS esses.
    # Isto evita substituir eliminados por equipas do ranking regular que nunca
    # chegaram a disputar os playoffs, o que criaria confrontos impossíveis.
    if playoff_active_winners:
        points_map = {t: pts for t, pts in ranking}
        for team, pts in ranking:
            if team in playoff_active_winners and not is_b_team(team):
                playoff_count_sim[team] = 1
                playoff_bracket_ranking.append((team, points_map[team]))
    elif playoff_slots:
        # Necessitamos do dictionary em points para mapear ranking original
        points_map = {t: pts for t, pts in ranking}

        # Sort group slots deterministically (e.g. A->B->C) to pair them systematically
        for group_key in sorted(playoff_slots.keys(), key=lambda k: (k[0], k[1])):
            slots = playoff_slots[group_key]
            placed = 0
            for team in ranked_by_group.get(group_key, []):
                if is_b_team(team) or team in (playoff_eliminated_teams or set()):
                    continue
                playoff_count_sim[team] = 1
                playoff_bracket_ranking.append((team, points_map[team]))
                placed += 1
                if placed >= slots:
                    break
    else:
        playoff_qualifiers = 0
        for team, pts in ranking:
            if playoff_qualifiers >= total_playoff_slots:
                break
            if not is_b_team(team) and team not in (playoff_eliminated_teams or set()):
                playoff_count_sim[team] = 1
                playoff_bracket_ranking.append((team, pts))
                playoff_qualifiers += 1

    champion, semifinalists, finalists, playoff_matches = simulate_playoffs(
        playoff_teams,
        playoff_bracket_ranking,
        elo_system,
        score_simulator,
        exclude_teams=playoff_eliminated_teams,
    )

    secondary_liguilla_top_team: str | None = None

    def _resolve_secondary_slot(
        entry: Dict[str, Any], standings: Dict[Tuple[int, str], List[str]]
    ) -> str | None:
        kind = entry.get("kind")
        if kind == "team":
            name = str(entry.get("name", "")).strip()
            return name if name in sim_teams and not is_b_team(name) else None

        if kind == "maintenance":
            div = int(entry.get("div", 1))
            offset = int(entry.get("offset", 3))
            # No Tacaua, manutenção é o 1º acima dos descidos diretos
            candidates = [t for t in standings.get((div, ""), []) if not is_b_team(t)]
            if not candidates:
                return None
            pos = len(candidates) - offset
            if pos < 1:
                return None
            return candidates[pos - 1]

        if kind != "slot":
            return None

        div = int(entry.get("div", 1))
        grp = str(entry.get("grp", "")).upper()
        pos = int(entry.get("pos", 0))
        if pos <= 0:
            return None

        candidates = [
            team_name
            for team_name in standings.get((div, grp), [])
            if not is_b_team(team_name)
        ]
        if len(candidates) < pos:
            return None
        return candidates[pos - 1]

    def _accumulate_simulated_match(
        mid: str,
        a: str,
        b: str,
        winner: str,
        score_a: int,
        score_b: int,
        elo_a: float,
        elo_b: float,
    ) -> None:
        if mid not in match_stats_sim:
            match_stats_sim[mid] = {"1": 0, "X": 0, "2": 0, "total": 0}
        ms = match_stats_sim[mid]
        if winner == a:
            ms["1"] += 1
        elif winner == b:
            ms["2"] += 1
        else:
            ms["X"] += 1
        ms["total"] += 1

        if mid not in match_elo_sum_sim:
            match_elo_sum_sim[mid] = {
                "a_sum": 0.0,
                "a_sq": 0.0,
                "b_sum": 0.0,
                "b_sq": 0.0,
                "count": 0,
            }
        me = match_elo_sum_sim[mid]
        me["a_sum"] += elo_a
        me["a_sq"] += elo_a * elo_a
        me["b_sum"] += elo_b
        me["b_sq"] += elo_b * elo_b
        me["count"] += 1

        score_key = f"{score_a}-{score_b}"
        if mid not in match_score_stats_sim:
            match_score_stats_sim[mid] = {}
        sc = match_score_stats_sim[mid]
        sc[score_key] = sc.get(score_key, 0) + 1

    liguilla_stats_sim: Dict[str, Dict[str, int]] = {}
    liguilla_scenarios_sim: Dict[str, Dict[str, Dict[str, Any]]] = {}
    secondary_liguilla_top_team: str | None = None

    if secondary_liguilla_rows and team_division:
        standings_by_group: Dict[Tuple[int, str], List[str]] = defaultdict(list)
        for team, _pts in ranking:
            div, grp = team_division.get(team, (1, ""))
            standings_by_group[(div, grp)].append(team)

        liguilla_points: Dict[str, int] = defaultdict(int)
        liguilla_played_matches: List[Tuple[str, str, int, int]] = []
        liguilla_participants: List[str] = []
        liguilla_stats: Dict[str, Dict[str, int]] = defaultdict(
            lambda: {
                "lm1_participated": 0,
                "lm1_won": 0,
                "lm2_participated": 0,
                "lm2_won": 0,
                "lm3_participated": 0,
                "lm3_won": 0,
                "promoted": 0,
            }
        )
        team_liguilla_games_sim: Dict[str, List[Tuple[str, str, str]]] = defaultdict(
            list
        )

        ordered_rows = sorted(
            secondary_liguilla_rows, key=lambda item: item.get("order", 0)
        )
        for idx, match_row in enumerate(ordered_rows, start=1):
            team_a_name = _resolve_secondary_slot(
                match_row.get("a", {}), standings_by_group
            )
            team_b_name = _resolve_secondary_slot(
                match_row.get("b", {}), standings_by_group
            )

            if not team_a_name or not team_b_name or team_a_name == team_b_name:
                continue

            if team_a_name not in liguilla_participants:
                liguilla_participants.append(team_a_name)
            if team_b_name not in liguilla_participants:
                liguilla_participants.append(team_b_name)

            # Registar participação na ronda correcta
            liguilla_stats[team_a_name][f"lm{idx}_participated"] += 1
            liguilla_stats[team_b_name][f"lm{idx}_participated"] += 1

            elo_a = sim_teams[team_a_name].elo
            elo_b = sim_teams[team_b_name].elo
            winner, _margin, score_a_raw, score_b_raw = simulate_match(
                sim_teams[team_a_name],
                sim_teams[team_b_name],
                elo_system,
                score_simulator,
                is_playoff=False,
                division=int(team_division.get(team_a_name, (1, ""))[0] or 1),
            )

            t1, t2 = sorted([team_a_name, team_b_name])
            score_a = score_a_raw if t1 == team_a_name else score_b_raw
            score_b = score_b_raw if t1 == team_a_name else score_a_raw
            elo_t1 = elo_a if t1 == team_a_name else elo_b
            elo_t2 = elo_b if t1 == team_a_name else elo_a

            # Registar vitória na ronda correcta
            liguilla_stats[winner][f"lm{idx}_won"] += 1

            stage_label = str(match_row.get("jornada", f"LM{idx}")).upper().strip()
            team_liguilla_games_sim[team_a_name].append(
                (
                    stage_label,
                    team_b_name,
                    (
                        "W"
                        if winner == team_a_name
                        else ("L" if winner == team_b_name else "D")
                    ),
                )
            )
            team_liguilla_games_sim[team_b_name].append(
                (
                    stage_label,
                    team_a_name,
                    (
                        "W"
                        if winner == team_b_name
                        else ("L" if winner == team_a_name else "D")
                    ),
                )
            )

            mid = f"SECONDARY_STAGE|{match_row.get('jornada', 'LM')}|L{idx}|{t1}|{t2}"
            _accumulate_simulated_match(
                mid, t1, t2, winner, score_a, score_b, elo_t1, elo_t2
            )

            liguilla_played_matches.append((team_a_name, team_b_name, score_a, score_b))
            if winner == team_a_name:
                liguilla_points[team_a_name] += 3
            elif winner == team_b_name:
                liguilla_points[team_b_name] += 3
            else:
                liguilla_points[team_a_name] += 1
                liguilla_points[team_b_name] += 1

        if liguilla_participants:
            liguilla_ranking = _rank_group_with_tiebreak(
                liguilla_participants,
                liguilla_points,
                liguilla_played_matches,
            )
            if liguilla_ranking:
                secondary_liguilla_top_team = liguilla_ranking[0]
                # Registar promoção do vencedor da liguilha
                liguilla_stats[secondary_liguilla_top_team]["promoted"] += 1

        # Copiar para liguilla_stats_sim para retorno
        liguilla_stats_sim = dict(liguilla_stats)

        for team_name in liguilla_participants:
            games_for_team = team_liguilla_games_sim.get(team_name, [])
            if len(games_for_team) < 2:
                continue

            def _stage_order(value: str) -> int:
                match = re.search(r"(\d+)", str(value))
                return int(match.group(1)) if match else 99

            sorted_games = sorted(
                games_for_team, key=lambda item: _stage_order(item[0])
            )
            stage_1, opponent_1, result_1 = sorted_games[0]
            stage_2, opponent_2, result_2 = sorted_games[1]

            scenario_key = f"{stage_1}:{opponent_1}|{stage_2}:{opponent_2}"
            team_scenarios = liguilla_scenarios_sim.setdefault(team_name, {})
            scenario_stats = team_scenarios.setdefault(
                scenario_key,
                {
                    "stage_game1": stage_1,
                    "opponent_game1": opponent_1,
                    "stage_game2": stage_2,
                    "opponent_game2": opponent_2,
                    "scenario_count": 0,
                    "promoted_count": 0,
                    "game1_wins": 0,
                    "game1_draws": 0,
                    "game1_losses": 0,
                    "game2_wins": 0,
                    "game2_draws": 0,
                    "game2_losses": 0,
                },
            )

            scenario_stats["scenario_count"] += 1
            if secondary_liguilla_top_team == team_name:
                scenario_stats["promoted_count"] += 1

            if result_1 == "W":
                scenario_stats["game1_wins"] += 1
            elif result_1 == "D":
                scenario_stats["game1_draws"] += 1
            else:
                scenario_stats["game1_losses"] += 1

            if result_2 == "W":
                scenario_stats["game2_wins"] += 1
            elif result_2 == "D":
                scenario_stats["game2_draws"] += 1
            else:
                scenario_stats["game2_losses"] += 1

    # Simular playoff secundário de manutenção (PM1 -> PM2) quando configurado no CSV.
    if secondary_playoff_pm1 and team_division:
        standings_by_group: Dict[Tuple[int, str], List[str]] = defaultdict(list)
        for team, _pts in ranking:
            div, grp = team_division.get(team, (1, ""))
            standings_by_group[(div, grp)].append(team)

        pm1_winners: List[str] = []
        for idx, (slot_a, slot_b) in enumerate(secondary_playoff_pm1, start=1):
            team_a_name = _resolve_secondary_slot(slot_a, standings_by_group)
            team_b_name = _resolve_secondary_slot(slot_b, standings_by_group)

            if not team_a_name or not team_b_name or team_a_name == team_b_name:
                continue

            elo_a = sim_teams[team_a_name].elo
            elo_b = sim_teams[team_b_name].elo
            winner, _margin, score_a_raw, score_b_raw = simulate_match(
                sim_teams[team_a_name],
                sim_teams[team_b_name],
                elo_system,
                score_simulator,
                is_playoff=True,
                division=None,
            )

            t1, t2 = sorted([team_a_name, team_b_name])
            score_a = score_a_raw if t1 == team_a_name else score_b_raw
            score_b = score_b_raw if t1 == team_a_name else score_a_raw
            elo_t1 = elo_a if t1 == team_a_name else elo_b
            elo_t2 = elo_b if t1 == team_a_name else elo_a

            mid = f"SECONDARY_STAGE|1ºFase|MF{idx}|{t1}|{t2}"
            _accumulate_simulated_match(
                mid, t1, t2, winner, score_a, score_b, elo_t1, elo_t2
            )
            pm1_winners.append(winner)

        if len(pm1_winners) >= 2:
            finalist_a = pm1_winners[0]
            finalist_b = pm1_winners[1]
            if finalist_a != finalist_b:
                elo_a = sim_teams[finalist_a].elo
                elo_b = sim_teams[finalist_b].elo
                winner, _margin, score_a_raw, score_b_raw = simulate_match(
                    sim_teams[finalist_a],
                    sim_teams[finalist_b],
                    elo_system,
                    score_simulator,
                    is_playoff=True,
                    division=None,
                )

                t1, t2 = sorted([finalist_a, finalist_b])
                score_a = score_a_raw if t1 == finalist_a else score_b_raw
                score_b = score_b_raw if t1 == finalist_a else score_a_raw
                elo_t1 = elo_a if t1 == finalist_a else elo_b
                elo_t2 = elo_b if t1 == finalist_a else elo_a

                mid = f"SECONDARY_STAGE|Fase final|F|{t1}|{t2}"
                _accumulate_simulated_match(
                    mid, t1, t2, winner, score_a, score_b, elo_t1, elo_t2
                )
                secondary_liguilla_top_team = winner

    for pm in playoff_matches:
        mid = pm["id"]
        a = pm["a"]
        b = pm["b"]
        winner = pm["winner"]
        score_a = pm["score_a"]
        score_b = pm["score_b"]
        elo_a = pm["elo_a"]
        elo_b = pm["elo_b"]

        _accumulate_simulated_match(mid, a, b, winner, score_a, score_b, elo_a, elo_b)

    promotion_count_sim: Dict = {}
    relegation_count_sim: Dict = {}

    if team_division:
        promoted, relegated = calculate_promotions_relegations(
            points,
            team_division,
            sim_teams,
            has_liguilla,
            ranked_by_group=ranked_by_group,
            withdrawn_teams=withdrawn_teams,
            secondary_liguilla_top_team=secondary_liguilla_top_team,
        )
        for t in promoted:
            promotion_count_sim[t] = 1
        for t in relegated:
            relegation_count_sim[t] = 1

    return {
        "expected_points": expected_points_sim,
        "final_elos": final_elos_sim,
        "regular_season_places": regular_season_places_sim,
        "playoff_count": playoff_count_sim,
        "semifinal_count": {t: 1 for t in semifinalists},
        "final_count": {t: 1 for t in finalists},
        "champion_count": {champion: 1} if champion else {},
        "promotion_count": promotion_count_sim,
        "relegation_count": relegation_count_sim,
        "liguilla_stats": dict(liguilla_stats_sim),
        "liguilla_scenarios": liguilla_scenarios_sim,
        "match_stats": match_stats_sim,
        "match_elo_sum": match_elo_sum_sim,
        "match_score_stats": match_score_stats_sim,
    }


def monte_carlo_forecast(
    teams: Dict[str, Team],
    fixtures: List[Dict],
    elo_system: CompleteTacauaEloSystem,
    score_simulator: SportScoreSimulator,
    n_simulations: int = 10000,
    team_division: Dict[str, Tuple[int, str]] = None,
    has_liguilla: bool = False,
    real_points: Dict[str, int] = None,
    playoff_slots: Dict[Tuple[int, str], int] = None,
    total_playoff_slots: int = 8,
    secondary_playoff_pm1: List[Tuple[Dict[str, Any], Dict[str, Any]]] = None,
    secondary_liguilla_rows: List[Dict[str, Any]] = None,
    past_played_matches: List[Tuple[str, str, int, int]] = None,
    hardset_manager: "HardsetManager | None" = None,
    withdrawn_teams: Set[str] = None,
    playoff_eliminated_teams: Set[str] = None,
    playoff_active_winners: Set[str] = None,
    modalidade: str | None = None,
    playoff_rules: Dict | None = None,
) -> Tuple[
    Dict[str, Dict[str, float]],
    Dict[str, Dict[str, float]],
    Dict[str, Dict[str, float]],
    Dict[str, Dict[str, int]],
    Dict[str, Dict[str, Dict[str, Any]]],
]:
    """Monte Carlo com suporte opcional a resultados fixados (hardset).

    Quando hardset_manager é fornecido, os jogos com resultado fixado usam
    esse resultado em todas as simulações. Exibe um resumo dos hardsets ativos
    no início da execução.
    """
    if real_points is None:
        real_points = {}

    if withdrawn_teams is None:
        withdrawn_teams = set()

    if playoff_eliminated_teams is None:
        playoff_eliminated_teams = set()

    if playoff_active_winners is None:
        playoff_active_winners = set()

    if secondary_playoff_pm1 is None:
        secondary_playoff_pm1 = []
    if secondary_liguilla_rows is None:
        secondary_liguilla_rows = []
    if past_played_matches is None:
        past_played_matches = []

    if hardset_manager and hardset_manager.fixed_results:
        print(f"\n{'='*60}")
        print(hardset_manager.summary())
        print(f"{'='*60}\n")

    preprocessed_fixtures = _preprocess_fixtures(fixtures, teams)

    playoff_count = defaultdict(int)
    semifinal_count = defaultdict(int)
    final_count = defaultdict(int)
    champion_count = defaultdict(int)
    promotion_count = defaultdict(int)
    relegation_count = defaultdict(int)
    liguilla_stats_agg: Dict[str, Dict[str, int]] = defaultdict(
        lambda: {
            "lm1_participated": 0,
            "lm1_won": 0,
            "lm2_participated": 0,
            "lm2_won": 0,
            "lm3_participated": 0,
            "lm3_won": 0,
            "promoted": 0,
        }
    )
    liguilla_scenarios_agg: Dict[str, Dict[str, Dict[str, Any]]] = defaultdict(dict)

    expected_points_sum = defaultdict(float)
    expected_points_sq_sum = defaultdict(float)
    regular_places_sum = defaultdict(float)
    regular_places_sq_sum = defaultdict(float)
    final_elos_sum = defaultdict(float)
    final_elos_sq_sum = defaultdict(float)

    match_stats = defaultdict(lambda: {"1": 0, "X": 0, "2": 0, "total": 0})
    match_elo_sum = defaultdict(
        lambda: {"a_sum": 0.0, "a_sq": 0.0, "b_sum": 0.0, "b_sq": 0.0, "count": 0}
    )
    match_score_stats = defaultdict(lambda: defaultdict(int))

    num_workers = get_num_workers()
    print(f"\n✓ Detectados {num_workers} cores disponíveis")

    if n_simulations >= 1000000:
        batch_size = 50000
        chunksize = 500
    elif n_simulations >= 100000:
        batch_size = 10000
        chunksize = 100
    else:
        batch_size = n_simulations
        chunksize = max(1, n_simulations // (num_workers * 4))

    num_batches = (n_simulations + batch_size - 1) // batch_size
    print(
        f"✓ {n_simulations} simulações em {num_batches} batch(es) | Chunksize: {chunksize}\n"
    )

    progress_tracker = ProgressTracker(num_workers, n_simulations)

    with ProcessPoolExecutor(max_workers=num_workers) as executor:
        for batch_num in range(num_batches):
            batch_start = batch_num * batch_size
            batch_end = min(batch_start + batch_size, n_simulations)

            simulation_args = []
            for sim_idx in range(batch_start, batch_end):
                worker_id = sim_idx % num_workers
                simulation_args.append(
                    (
                        sim_idx,
                        worker_id,
                        teams,
                        preprocessed_fixtures,
                        elo_system,
                        score_simulator,
                        n_simulations,
                        team_division,
                        has_liguilla,
                        real_points,
                        playoff_slots,
                        total_playoff_slots,
                        secondary_playoff_pm1,
                        secondary_liguilla_rows,
                        past_played_matches,
                        hardset_manager,
                        withdrawn_teams,
                        playoff_eliminated_teams,
                        playoff_active_winners,
                        modalidade,
                        playoff_rules,
                    )
                )

            for sim_result in executor.map(
                _run_single_simulation_worker, simulation_args, chunksize=chunksize
            ):
                progress_tracker.increment()

                for team in teams:
                    if team in sim_result["expected_points"]:
                        val = sim_result["expected_points"][team]
                        expected_points_sum[team] += val
                        expected_points_sq_sum[team] += val * val

                        elo_val = sim_result["final_elos"][team]
                        final_elos_sum[team] += elo_val
                        final_elos_sq_sum[team] += elo_val * elo_val

                        place_val = sim_result["regular_season_places"][team]
                        regular_places_sum[team] += place_val
                        regular_places_sq_sum[team] += place_val * place_val

                for team, count in sim_result["playoff_count"].items():
                    playoff_count[team] += count
                for team, count in sim_result["semifinal_count"].items():
                    semifinal_count[team] += count
                for team, count in sim_result["final_count"].items():
                    final_count[team] += count
                for team, count in sim_result["champion_count"].items():
                    champion_count[team] += count
                for team, count in sim_result["promotion_count"].items():
                    promotion_count[team] += count
                for team, count in sim_result["relegation_count"].items():
                    relegation_count[team] += count

                for team, team_lm_stats in sim_result.get("liguilla_stats", {}).items():
                    for stat_key, count in team_lm_stats.items():
                        liguilla_stats_agg[team][stat_key] += count

                for team, scenarios in sim_result.get("liguilla_scenarios", {}).items():
                    team_agg = liguilla_scenarios_agg[team]
                    for scenario_key, scenario_stats in scenarios.items():
                        if scenario_key not in team_agg:
                            team_agg[scenario_key] = {
                                "stage_game1": scenario_stats.get("stage_game1", ""),
                                "opponent_game1": scenario_stats.get(
                                    "opponent_game1", ""
                                ),
                                "stage_game2": scenario_stats.get("stage_game2", ""),
                                "opponent_game2": scenario_stats.get(
                                    "opponent_game2", ""
                                ),
                                "scenario_count": 0,
                                "promoted_count": 0,
                                "game1_wins": 0,
                                "game1_draws": 0,
                                "game1_losses": 0,
                                "game2_wins": 0,
                                "game2_draws": 0,
                                "game2_losses": 0,
                            }

                        agg_stats = team_agg[scenario_key]
                        for key in [
                            "scenario_count",
                            "promoted_count",
                            "game1_wins",
                            "game1_draws",
                            "game1_losses",
                            "game2_wins",
                            "game2_draws",
                            "game2_losses",
                        ]:
                            agg_stats[key] += int(scenario_stats.get(key, 0) or 0)

                for mid, stats in sim_result["match_stats"].items():
                    for key in ["1", "X", "2", "total"]:
                        match_stats[mid][key] += stats[key]

                for mid, elo_sums in sim_result["match_elo_sum"].items():
                    match_elo_sum[mid]["a_sum"] += elo_sums["a_sum"]
                    match_elo_sum[mid]["a_sq"] += elo_sums["a_sq"]
                    match_elo_sum[mid]["b_sum"] += elo_sums["b_sum"]
                    match_elo_sum[mid]["b_sq"] += elo_sums["b_sq"]
                    match_elo_sum[mid]["count"] += elo_sums["count"]

                for mid, score_data in sim_result["match_score_stats"].items():
                    for score_key, count in score_data.items():
                        match_score_stats[mid][score_key] += count

        gc.collect()

    results = {}
    for team in teams:
        n = n_simulations

        mean_xpts = (
            expected_points_sum[team] / n if team in expected_points_sum else 0.0
        )
        variance_xpts = (
            (expected_points_sq_sum[team] / n - mean_xpts**2)
            if team in expected_points_sq_sum
            else 0.0
        )
        std_xpts = variance_xpts**0.5 if variance_xpts > 0 else 0.0

        mean_place = (
            regular_places_sum[team] / n if team in regular_places_sum else len(teams)
        )
        variance_place = (
            (regular_places_sq_sum[team] / n - mean_place**2)
            if team in regular_places_sq_sum
            else 0.0
        )
        std_place = variance_place**0.5 if variance_place > 0 else 0.0

        mean_elo = (
            final_elos_sum[team] / n if team in final_elos_sum else teams[team].elo
        )
        variance_elo = (
            (final_elos_sq_sum[team] / n - mean_elo**2)
            if team in final_elos_sq_sum
            else 0.0
        )
        std_elo = variance_elo**0.5 if variance_elo > 0 else 0.0

        results[team] = {
            "p_playoffs": playoff_count[team] / n_simulations,
            "p_meias_finais": semifinal_count[team] / n_simulations,
            "p_finais": final_count[team] / n_simulations,
            "p_champion": champion_count[team] / n_simulations,
            "expected_points": mean_xpts,
            "expected_points_std": std_xpts,
            "expected_place": mean_place,
            "expected_place_std": std_place,
            "avg_final_elo": mean_elo,
            "avg_final_elo_std": std_elo,
            "p_promocao": promotion_count[team] / n_simulations,
            "p_descida": relegation_count[team] / n_simulations,
        }

    match_forecasts = {}
    for mid, stats in match_stats.items():
        total = stats["total"]
        if total > 0:
            match_forecasts[mid] = {
                "p_win_a": stats["1"] / total,
                "p_draw": stats["X"] / total,
                "p_win_b": stats["2"] / total,
                "ocorrencias": total,
            }

    match_elo_forecast = {}
    for mid, elo_sums in match_elo_sum.items():
        count = elo_sums["count"]
        if count > 0:
            mean_a = elo_sums["a_sum"] / count
            variance_a = elo_sums["a_sq"] / count - mean_a**2
            std_a = variance_a**0.5 if variance_a > 0 else 0.0

            mean_b = elo_sums["b_sum"] / count
            variance_b = elo_sums["b_sq"] / count - mean_b**2
            std_b = variance_b**0.5 if variance_b > 0 else 0.0

            match_elo_forecast[mid] = {
                "elo_a_mean": mean_a,
                "elo_a_std": std_a,
                "elo_b_mean": mean_b,
                "elo_b_std": std_b,
            }

    progress_tracker.print_summary()

    return (
        results,
        match_forecasts,
        match_elo_forecast,
        match_score_stats,
        dict(liguilla_stats_agg),
        {team: dict(scenarios) for team, scenarios in liguilla_scenarios_agg.items()},
    )


# ============================================================================
# VALIDAÇÃO E BACKTEST - Avaliar precisão das previsões
# ============================================================================


def _season_csv_path(
    modalidade: str, season_pattern: str, docs_dir: str | None
) -> Path:
    """Devolve o caminho para o CSV de uma época de uma modalidade."""
    if docs_dir:
        return (
            Path(docs_dir)
            / "output"
            / DIR_CSV_MODALIDADES
            / f"{modalidade}_{season_pattern}.csv"
        )
    return (
        Path("..")
        / "docs"
        / "output"
        / DIR_CSV_MODALIDADES
        / f"{modalidade}_{season_pattern}.csv"
    )


def _load_season_rows(
    modalidade: str,
    past_seasons: Sequence[str],
    current_rows: Sequence[Dict],
    docs_dir: str | None,
) -> List[Dict]:
    """Carrega e concatena todas as linhas de CSV de épocas anteriores + época actual.

    Centraliza a lógica de resolução de caminho e o lru_cache que antes estava
    duplicada em calculate_historical_draw_rate, calculate_division_baselines e
    calculate_division_draw_rates. Cada CSV é lido uma única vez graças ao cache.

    Args:
        modalidade: Nome da modalidade.
        past_seasons: Padrões de época anteriores (ex: ["23_24", "24_25"]).
        current_rows: Linhas da época actual (já em memória).
        docs_dir: Raiz do directório docs; None usa caminho relativo.

    Returns:
        Lista combinada de todos os rows, épocas anteriores primeiro.
    """
    all_rows: List[Dict] = []
    for season_pattern in past_seasons:
        csv_path = _season_csv_path(modalidade, season_pattern, docs_dir)
        if not csv_path.exists():
            continue
        try:
            all_rows.extend(_load_csv_rows_cached(str(csv_path)))
        except FileNotFoundError:
            continue
    all_rows.extend(current_rows)
    return all_rows


def _parse_score_row(row: Dict) -> tuple[int, int, int | None] | None:
    """Extrai (golos_1, golos_2, divisao) de uma linha de CSV.

    Retorna None se a linha não tiver marcador válido.
    A divisão é None quando o campo está vazio ou não é inteiro.
    """
    g1_str = row.get(COL_GOLOS_1, "").strip()
    g2_str = row.get(COL_GOLOS_2, "").strip()
    if not g1_str or not g2_str:
        return None
    try:
        g1 = int(float(g1_str))
        g2 = int(float(g2_str))
    except ValueError:
        return None

    div_raw = str(row.get(COL_DIVISAO, "")).strip()
    div: int | None = None
    if div_raw:
        try:
            div = int(div_raw)
        except ValueError:
            pass
    return g1, g2, div


def calculate_historical_draw_rate(
    modalidade: str,
    past_seasons: Sequence[str],
    docs_dir: str | None = None,
) -> float:
    """Taxa histórica de empates para uma modalidade ao longo de épocas anteriores.

    Returns:
        Fracção de jogos que terminaram empatados (0.0–1.0).
    """
    total = draws = 0
    for row in _load_season_rows(modalidade, past_seasons, [], docs_dir):
        parsed = _parse_score_row(row)
        if parsed is None:
            continue
        g1, g2, _ = parsed
        total += 1
        if g1 == g2:
            draws += 1
    return draws / total if total else 0.0


def calculate_division_baselines(
    modalidade: str,
    past_seasons: Sequence[str],
    current_rows: Sequence[Dict],
    docs_dir: str | None = None,
) -> Dict[int | None, Dict[str, float]]:
    """Média e desvio padrão de golos por divisão (épocas anteriores + actual).

    Returns:
        {divisao: {"mean": x, "std": y}, None: {"mean": x, "std": y}}
    """
    score_data: Dict[int | None, List[int]] = defaultdict(list)
    for row in _load_season_rows(modalidade, past_seasons, current_rows, docs_dir):
        parsed = _parse_score_row(row)
        if parsed is None:
            continue
        g1, g2, div = parsed
        score_data[div].extend([g1, g2])
        score_data[None].extend([g1, g2])

    return {
        div: {"mean": float(np.mean(scores)), "std": float(np.std(scores))}
        for div, scores in score_data.items()
        if scores
    }


def calculate_division_draw_rates(
    modalidade: str,
    past_seasons: Sequence[str],
    current_rows: Sequence[Dict],
    docs_dir: str | None = None,
) -> Dict[int | None, float]:
    """Taxa de empates por divisão (épocas anteriores + actual).

    Returns:
        {divisao: rate, None: rate_global}
    """
    totals: Dict[int | None, int] = defaultdict(int)
    draws: Dict[int | None, int] = defaultdict(int)

    for row in _load_season_rows(modalidade, past_seasons, current_rows, docs_dir):
        parsed = _parse_score_row(row)
        if parsed is None:
            continue
        g1, g2, div = parsed
        totals[div] += 1
        totals[None] += 1
        if g1 == g2:
            draws[div] += 1
            draws[None] += 1

    return {div: draws[div] / t for div, t in totals.items() if t > 0}


def calculate_predicted_division_stats(
    fixtures: List[Dict],
    match_score_stats: Dict[str, Dict[str, int]],
) -> Dict[int | None, Dict[str, float]]:
    """
    Calcula medias previstas e taxa de empates por divisao.

    Retorna dict: {divisao: {"mean": x, "draw_rate": y, "matches": n}, None: {...}}
    """
    agg = defaultdict(lambda: {"sum_goals": 0.0, "sum_draw": 0.0, "matches": 0})

    for match in fixtures:
        if not match.get("is_future") or not match.get("id"):
            continue

        mid = match["id"]
        score_dist = match_score_stats.get(mid)
        if not score_dist:
            continue

        total = sum(score_dist.values())
        if total <= 0:
            continue

        exp_goals_a = 0.0
        exp_goals_b = 0.0
        exp_draw = 0.0
        for score_key, count in score_dist.items():
            try:
                score_a_str, score_b_str = score_key.split("-")
                score_a = int(score_a_str)
                score_b = int(score_b_str)
            except ValueError:
                continue
            prob = count / total
            exp_goals_a += score_a * prob
            exp_goals_b += score_b * prob
            if score_a == score_b:
                exp_draw += prob

        div_raw = str(match.get("divisao", "")).strip()
        div_key = None
        if div_raw:
            try:
                div_key = int(div_raw)
            except ValueError:
                div_key = None

        total_goals = exp_goals_a + exp_goals_b
        agg[div_key]["sum_goals"] += total_goals
        agg[div_key]["sum_draw"] += exp_draw
        agg[div_key]["matches"] += 1

        agg[None]["sum_goals"] += total_goals
        agg[None]["sum_draw"] += exp_draw
        agg[None]["matches"] += 1

    stats: Dict[int | None, Dict[str, float]] = {}
    for div_key, data in agg.items():
        if data["matches"] > 0:
            mean_per_team = (data["sum_goals"] / data["matches"]) / 2.0
            draw_rate = data["sum_draw"] / data["matches"]
            stats[div_key] = {
                "mean": mean_per_team,
                "draw_rate": draw_rate,
                "matches": data["matches"],
            }

    return stats


# ============================================================================
# FUNÇÃO AUXILIAR: Comparar Cenários
# ============================================================================


def example_hardset_usage():
    """Exemplo de como usar o sistema de hardset."""

    # Criar hardset manager
    hardset = HardsetManager()

    # OPÇÃO 1: Adicionar resultados manualmente
    # Nota: Usar nomes curtos (ex: "EGI" em vez de "Engenharia Informática")
    hardset.add_fixed_result("FUTSAL MASCULINO_5_EGI_Gestão", 5, 4)
    hardset.add_fixed_result("FUTSAL MASCULINO_6_Direito_Medicina", 2, 2)

    # OPÇÃO 2: Adicionar de dicionário
    hardset.add_from_dict(
        {
            "FUTSAL MASCULINO_7_Economia_Letras": (3, 1),
            "FUTSAL MASCULINO_8_Arquitetura_Ciências": (4, 4),
        }
    )

    # OPÇÃO 3: Carregar de CSV
    # hardset.add_from_csv("cenarios/upset_engenharia.csv")

    # Mostrar resumo
    print(hardset.summary())


def detect_withdrawn_teams_from_csv(
    csv_rows: List[Dict],
    course_mapping: Dict[str, str],
) -> Set[str]:
    """
    Detecta equipas desistentes (100% dos jogos sem participação efetiva).

    Lógica alinhada com o mmr_taçaua:
    - conta ausência se o score do lado da equipa está vazio/NaN, ou
    - equipa marcada em "Falta de Comparência" (incluindo listas separadas por vírgula).

    Args:
        csv_rows: Lista de dicionários com jogos da modalidade
        course_mapping: Mapeamento de nomes de cursos

    Returns:
        Set com nomes normalizados de equipas desistentes
    """
    team_game_count = {}  # {team: {'total': count, 'absent': count}}

    def _is_team_marked_absent(falta_value, team_name: str) -> bool:
        if falta_value is None:
            return False

        raw_value = str(falta_value).strip()
        if not raw_value:
            return False

        if normalize_team_name(raw_value, course_mapping) == team_name:
            return True

        if "," in raw_value:
            for piece in raw_value.split(","):
                if normalize_team_name(piece.strip(), course_mapping) == team_name:
                    return True

        return False

    for row in csv_rows:
        team_a_raw = row.get(COL_EQUIPA_1, "").strip()
        team_b_raw = row.get(COL_EQUIPA_2, "").strip()

        if not team_a_raw or not team_b_raw:
            continue

        # Verificar coluna de falta de comparência (única coluna partilhada por ambas as equipas)
        falta_valor = row.get(COL_FALTA_COMPARENCIA)
        has_falta = bool(falta_valor and str(falta_valor).strip())

        golos_1_raw = row.get(COL_GOLOS_1)
        golos_2_raw = row.get(COL_GOLOS_2)
        g1_empty = golos_1_raw is None or str(golos_1_raw).strip() == ""
        g2_empty = golos_2_raw is None or str(golos_2_raw).strip() == ""

        # Se AMBOS os scores estão vazios E não há falta de comparência registada,
        # é um jogo futuro (ainda não realizado) — NÃO conta como ausência.
        # Slots de playoff (ex: "1º Class. 1ª Div.", "Vencedor QF1") só aparecem
        # neste tipo de linhas e NÃO devem ser detectados como desistentes.
        if g1_empty and g2_empty and not has_falta:
            continue

        resultado1_absent = g1_empty
        resultado2_absent = g2_empty

        # Normalizar nomes
        team_a = normalize_team_name(team_a_raw, course_mapping)
        team_b = normalize_team_name(team_b_raw, course_mapping)

        if team_a:
            if team_a not in team_game_count:
                team_game_count[team_a] = {"total": 0, "absent": 0}
            team_game_count[team_a]["total"] += 1
            if resultado1_absent or _is_team_marked_absent(falta_valor, team_a):
                team_game_count[team_a]["absent"] += 1

        if team_b:
            if team_b not in team_game_count:
                team_game_count[team_b] = {"total": 0, "absent": 0}
            team_game_count[team_b]["total"] += 1
            if resultado2_absent or _is_team_marked_absent(falta_valor, team_b):
                team_game_count[team_b]["absent"] += 1

    # Identificar desistentes (100% de ausências)
    withdrawn_teams = set()
    for team, counts in team_game_count.items():
        if counts["total"] > 0 and counts["absent"] == counts["total"]:
            withdrawn_teams.add(team)
            logger.warning(
                f"Equipa desistente detectada: {team} ({counts['total']} jogos com ausência)"
            )

    return withdrawn_teams


def get_initial_rating_from_division(
    team_name: str,
    division: int | None,
    initial_elos: Dict[str, float],
) -> float:
    """
    Obtém ELO inicial da equipa, considerando ELOs da época anterior e divisão.

    Args:
        team_name: Nome normalizado da equipa
        division: Divisão da equipa (1, 2, etc.) ou None se sem divisões
        initial_elos: Dicionário com ELOs carregados da época anterior

    Returns:
        ELO inicial apropriado para a equipa
    """
    # Prioridade 1: Se tem ELO da época anterior, usar esse
    if team_name in initial_elos:
        return initial_elos[team_name]

    # Prioridade 2: Usar ELO padrão baseado em divisão
    if division == 1:
        return ELO_DEFAULT_DIV1
    elif division == 2:
        return ELO_DEFAULT_DIV2
    else:
        # Sem divisão ou divisão desconhecida → ELO padrão
        return ELO_DEFAULT_UNKNOWN


def _build_hardset_manager(
    hardset_args: list | None,
    hardset_csv: str | None,
    course_mapping_short: Dict[str, str],
) -> HardsetManager | None:
    """Inicializa e povoa um HardsetManager a partir de argumentos CLI e/ou CSV.

    Retorna None se não houver resultados fixados a carregar.
    """
    if not hardset_args and not hardset_csv:
        return None

    manager = HardsetManager(mapping_short=course_mapping_short)

    if hardset_args:
        print("\n🎯 HARDSET CARREGADO VIA ARGUMENTOS:\n")
        for match_id, score in hardset_args:
            try:
                parts = score.split("-")
                if len(parts) != 2:
                    logger.error(f"Formato inválido para score: {score}. Use 'A-B'")
                    continue
                score_a, score_b = int(parts[0]), int(parts[1])
                manager.add_fixed_result(match_id, score_a, score_b)
            except ValueError:
                logger.error(f"Erro ao processar score: {score}")

    if hardset_csv:
        manager.add_from_csv(hardset_csv)

    print()
    return manager


def _load_modalidade_data(
    modalidade: str,
    date_pattern: str,
    past_seasons: List[str],
    docs_dir: str,
    modalidades_path: str,
    modalidade_file: str,
    course_mapping: Dict[str, str],
    score_simulator: SportScoreSimulator,
    calibrated_config: Dict | None,
) -> Tuple[Dict[str, float], list, list, list, Dict, Dict]:
    """Carrega todos os dados necessários para simular uma modalidade.

    Retorna:
        (initial_elos, all_csv_rows, past_matches_rows, future_matches_rows,
         division_baselines, division_draw_rates)
    """
    # Carregar ELOs da época anterior
    elo_file = (
        Path(docs_dir)
        / "output"
        / "elo_ratings"
        / f"elo_{modalidade}{date_pattern}.csv"
    )
    initial_elos: Dict[str, float] = {}
    if Path(str(elo_file)).exists():
        with open(elo_file, newline="", encoding="utf-8-sig") as csvfile:
            reader = csv.reader(csvfile)
            headers = next(reader)
            rows = list(reader)
            if rows:
                last_row = rows[-1]
                for i, team_name in enumerate(headers):
                    if i < len(last_row):
                        try:
                            normalized_name = normalize_team_name(
                                team_name, course_mapping
                            )
                            initial_elos[normalized_name] = float(last_row[i])
                        except ValueError:
                            continue

    # Carregar e separar jogos
    all_csv_rows = _load_csv_rows_cached(str(Path(modalidades_path) / modalidade_file))
    past_matches_rows, future_matches_rows = separate_past_and_future_matches(
        all_csv_rows
    )

    # Calcular e aplicar baselines históricos ao simulador
    division_baselines = calculate_division_baselines(
        modalidade, past_seasons, past_matches_rows, docs_dir
    )
    division_draw_rates = calculate_division_draw_rates(
        modalidade, past_seasons, past_matches_rows, docs_dir
    )
    score_simulator.set_division_baselines(division_baselines)
    score_simulator.set_division_draw_rates(division_draw_rates)

    # Aplicar parâmetros calibrados (têm prioridade sobre os históricos)
    if calibrated_config and modalidade in calibrated_config:
        score_simulator.apply_calibrated_params(calibrated_config[modalidade])

    return (
        initial_elos,
        all_csv_rows,
        past_matches_rows,
        future_matches_rows,
        division_baselines,
        division_draw_rates,
    )


def _build_teams_and_fixtures(
    all_csv_rows,
    past_matches_rows,
    future_matches_rows,
    course_mapping: Dict[str, str],
    course_mapping_short: Dict[str, str],
    initial_elos: Dict[str, float],
    modalidade: str,
) -> Tuple[
    Dict[str, Team],
    List[Dict],
    Set[str],
    Dict[str, Tuple[int, str]],
    Set[str],
    Set[str],
]:
    """Constrói teams, fixtures, all_teams_in_epoch, team_division e withdrawn_teams.

    Retorna:
        (teams, fixtures, all_teams_in_epoch, team_division, withdrawn_teams)
    """
    teams: Dict[str, Team] = {}
    fixtures: List[Dict] = []
    all_teams_in_epoch: Set[str] = set()

    # Detectar desistentes antes de processar qualquer jogo (lógica alinhada com mmr_taçaua)
    withdrawn_teams = detect_withdrawn_teams_from_csv(all_csv_rows, course_mapping)

    if withdrawn_teams:
        logger.info(
            f"Equipas desistentes excluídas da simulação em {modalidade}: "
            f"{sorted(withdrawn_teams)}"
        )

    # Mapear divisão/grupo para todas as equipas (passado + futuro)
    team_division: Dict[str, Tuple[int, str]] = {}
    for row in all_csv_rows:
        t1_raw = row.get(COL_EQUIPA_1, "").strip()
        t2_raw = row.get(COL_EQUIPA_2, "").strip()
        if not t1_raw or not t2_raw:
            continue
        t1 = normalize_team_name(t1_raw, course_mapping)
        t2 = normalize_team_name(t2_raw, course_mapping)
        div = row.get(COL_DIVISAO, "") or "1"
        grp = (row.get(COL_GRUPO, "") or "").strip().upper()
        try:
            div_int = int(div)
        except ValueError:
            div_int = 1
        if t1 and t1 not in team_division:
            team_division[t1] = (div_int, grp)
        if t2 and t2 not in team_division:
            team_division[t2] = (div_int, grp)

    def _register_team(name: str) -> None:
        if name not in teams:
            div = team_division.get(name, (None, None))[0]
            teams[name] = Team(
                name, get_initial_rating_from_division(name, div, initial_elos)
            )

    # Jogos futuros → fixtures de simulação
    for row in future_matches_rows:
        team_a_raw = row[COL_EQUIPA_1].strip()
        team_b_raw = row[COL_EQUIPA_2].strip()
        if not is_valid_team(team_a_raw) or not is_valid_team(team_b_raw):
            continue
        team_a = normalize_team_name(team_a_raw, course_mapping)
        team_b = normalize_team_name(team_b_raw, course_mapping)
        if team_a in withdrawn_teams or team_b in withdrawn_teams:
            continue

        jornada_val = str(row.get(COL_JORNADA, "")).strip().upper()
        # Se for jogo de playoff (E), PM ou LM, saltamos pois são simulados
        # por lógica especializada no worker (evita duplicação no output)
        if jornada_val.startswith(("E", "PM", "LM")):
            continue

        all_teams_in_epoch.add(team_a)
        all_teams_in_epoch.add(team_b)
        _register_team(team_a)
        _register_team(team_b)

        team_a_short = get_team_short_name(team_a, course_mapping_short)
        team_b_short = get_team_short_name(team_b, course_mapping_short)
        match_id = (
            f"{modalidade}_{row.get('Jornada', '0')}_{team_a_short}_{team_b_short}"
        )

        fixtures.append(
            {
                "a": team_a,
                "b": team_b,
                "is_future": True,
                "id": match_id,
                "jornada": row.get(COL_JORNADA, ""),
                "dia": row.get(COL_DIA, ""),
                "hora": row.get(COL_HORA, ""),
                "divisao": row.get(COL_DIVISAO, ""),
                "grupo": row.get(COL_GRUPO, ""),
            }
        )

    # Jogos passados → registar equipas (para histórico de ELO)
    for row in past_matches_rows:
        team_a_raw = row[COL_EQUIPA_1].strip()
        team_b_raw = row[COL_EQUIPA_2].strip()
        if not is_valid_team(team_a_raw) or not is_valid_team(team_b_raw):
            continue
        team_a = normalize_team_name(team_a_raw, course_mapping)
        team_b = normalize_team_name(team_b_raw, course_mapping)
        if team_a in withdrawn_teams or team_b in withdrawn_teams:
            continue

        all_teams_in_epoch.add(team_a)
        all_teams_in_epoch.add(team_b)
        _register_team(team_a)
        _register_team(team_b)

    # Detectar equipas já eliminadas em playoffs (resultados passados com jornadas E/PM/LM)
    # E também os vencedores ativos (ainda não eliminados em rondas seguintes)
    playoff_eliminated: Set[str] = set()
    playoff_all_winners: Set[str] = set()
    for row in past_matches_rows:
        jornada_val = str(row.get(COL_JORNADA, "")).strip().upper()
        if not jornada_val.startswith(("E", "PM", "LM")):
            continue

        team_a_raw = row.get(COL_EQUIPA_1, "").strip()
        team_b_raw = row.get(COL_EQUIPA_2, "").strip()
        if not team_a_raw or not team_b_raw:
            continue

        team_a = normalize_team_name(team_a_raw, course_mapping)
        team_b = normalize_team_name(team_b_raw, course_mapping)

        golos_1_str = str(row.get(COL_GOLOS_1, "")).strip()
        golos_2_str = str(row.get(COL_GOLOS_2, "")).strip()
        falta = str(row.get(COL_FALTA_COMPARENCIA, "")).strip()

        if not golos_1_str or not golos_2_str:
            # Se falta de comparência registada, determinar vencedor/derrotado
            if falta:
                falta_norm = normalize_team_name(falta, course_mapping)
                if falta_norm == team_a:
                    # team_a faltou -> team_b venceu
                    playoff_eliminated.add(team_a)
                    playoff_all_winners.add(team_b)
                elif falta_norm == team_b:
                    playoff_eliminated.add(team_b)
                    playoff_all_winners.add(team_a)
            continue

        try:
            g1 = int(float(golos_1_str))
            g2 = int(float(golos_2_str))
        except ValueError:
            continue

        if g1 == g2:
            # Empates em fases eliminatórias não resolvidos aqui
            continue
        if g1 > g2:
            playoff_eliminated.add(team_b)
            playoff_all_winners.add(team_a)
        else:
            playoff_eliminated.add(team_a)
            playoff_all_winners.add(team_b)

    # Vencedores ativos = ganharam pelo menos uma ronda mas ainda não foram eliminados
    # (ex: após E1, os 4 vencedores dos quartos ainda estão vivos)
    playoff_active_winners: Set[str] = playoff_all_winners - playoff_eliminated

    if playoff_active_winners:
        logger.info(
            f"Vencedores ativos de playoff em {modalidade}: "
            f"{sorted(playoff_active_winners)} "
            f"(eliminados: {sorted(playoff_eliminated)})"
        )

    return (
        teams,
        fixtures,
        all_teams_in_epoch,
        team_division,
        withdrawn_teams,
        playoff_eliminated,
        playoff_active_winners,
    )


def _export_results(
    docs_dir: str,
    modalidade: str,
    ano_atual: int,
    n_simulations: int,
    hardset_manager: HardsetManager | None,
    all_teams_in_epoch: Set[str],
    teams: Dict[str, Team],
    team_division: Dict[str, Tuple[int, str]],
    initial_elos: Dict[str, float],
    real_points: Dict[str, int],
    results: Dict,
    fixtures: List[Dict],
    match_forecasts: Dict,
    match_elo_forecast: Dict,
    match_score_stats: Dict,
    liguilla_stats: Dict[str, Dict[str, int]],
    liguilla_scenarios: Dict[str, Dict[str, Dict[str, Any]]],
) -> None:
    """Escreve os dois CSVs de output: forecast de equipas e previsões de jogos."""

    def _format_prediction_jornada(jornada_value: str) -> str:
        """Normaliza labels de jornada para o CSV de previsões.

        Regras específicas pedidas para fases secundárias:
        - PM1 -> 1ºFase
        - PM2 -> Fase final
        - LM<n> -> Liguilha <n>
        """
        jornada_str = str(jornada_value or "").strip()
        jornada_upper = jornada_str.upper()

        if jornada_upper.startswith("PM1"):
            return "1ºFase"
        if jornada_upper.startswith("PM2"):
            return "Fase final"
        if jornada_upper.startswith("LM"):
            lm_match = re.match(r"LM\s*(\d+)", jornada_upper)
            if lm_match:
                return f"Liguilha {int(lm_match.group(1))}"
            return "Liguilha"

        return jornada_str

    is_hardset = bool(hardset_manager and hardset_manager.fixed_results)
    subfolder = "cenarios" if is_hardset else "previsoes"
    suffix = "_hardset" if is_hardset else ""

    out_dir = Path(docs_dir) / "output" / subfolder
    output_file = (
        out_dir / f"forecast_{modalidade}_{ano_atual}_{n_simulations}{suffix}.csv"
    )
    predictions_file = (
        out_dir / f"previsoes_{modalidade}_{ano_atual}_{n_simulations}{suffix}.csv"
    )

    # --- CSV 1: Forecast de equipas ---
    with open(output_file, "w", newline="", encoding="utf-8-sig") as csvfile:
        fieldnames = [
            "team",
            "p_playoffs",
            "p_meias_finais",
            "p_finais",
            "p_champion",
            "p_promocao",
            "p_descida",
            "expected_points",
            "expected_points_std",
            "expected_place_in_group",
            "expected_place_in_group_std",
            "avg_final_elo",
            "avg_final_elo_std",
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for team in sorted(all_teams_in_epoch):
            if team in results:
                r = results[team]
                row = {
                    "team": team,
                    "p_playoffs": f"{r['p_playoffs'] * 100:.4f}",
                    "p_meias_finais": f"{r['p_meias_finais'] * 100:.4f}",
                    "p_finais": f"{r['p_finais'] * 100:.4f}",
                    "p_champion": f"{r['p_champion'] * 100:.4f}",
                    "p_promocao": f"{r['p_promocao'] * 100:.4f}",
                    "p_descida": f"{r['p_descida'] * 100:.4f}",
                    "expected_points": f"{r['expected_points']:.2f}",
                    "expected_points_std": f"{r['expected_points_std']:.2f}",
                    "expected_place_in_group": f"{r['expected_place']:.2f}",
                    "expected_place_in_group_std": f"{r['expected_place_std']:.2f}",
                    "avg_final_elo": f"{r['avg_final_elo']:.1f}",
                    "avg_final_elo_std": f"{r['avg_final_elo_std']:.1f}",
                }
            else:
                team_div = team_division.get(team, (None, ""))[0]
                row = {
                    "team": team,
                    "p_playoffs": "0.0000",
                    "p_meias_finais": "0.0000",
                    "p_finais": "0.0000",
                    "p_champion": "0.0000",
                    "p_promocao": "0.0000",
                    "p_descida": "0.0000",
                    "expected_points": f"{real_points.get(team, 0.0):.2f}",
                    "expected_points_std": "0.00",
                    "expected_place_in_group": f"{float(len(all_teams_in_epoch)):.2f}",
                    "expected_place_in_group_std": "0.00",
                    "avg_final_elo": f"{get_initial_rating_from_division(team, team_div, initial_elos):.1f}",
                    "avg_final_elo_std": "0.0",
                }
            writer.writerow(row)

    print(f"Resultados guardados em {output_file}")

    # --- CSV 2: Previsões de jogos futuros ---
    future_count = 0
    with open(predictions_file, "w", newline="", encoding="utf-8-sig") as csvfile:
        fieldnames = [
            "jornada",
            "dia",
            "hora",
            "team_a",
            "team_b",
            "expected_elo_a",
            "expected_elo_a_std",
            "expected_elo_b",
            "expected_elo_b_std",
            "prob_vitoria_a",
            "prob_empate",
            "prob_vitoria_b",
            "expected_goals_a",
            "expected_goals_a_std",
            "expected_goals_b",
            "expected_goals_b_std",
            "ocorrencias",
            "divisao",
            "grupo",
            "distribuicao_placares",
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        playoff_fixtures = []
        for mid in match_forecasts:
            mid_str = str(mid)
            if mid_str.startswith("PLAYOFF_STAGE|"):
                parts = str(mid).split("|")
                if len(parts) >= 4:
                    playoff_fixtures.append(
                        {
                            "id": mid,
                            "a": parts[2],
                            "b": parts[3],
                            "is_future": True,
                            "jornada": parts[1],
                            "dia": "-",
                            "hora": "-",
                            "divisao": "1",
                            "grupo": "",
                        }
                    )
            elif mid_str.startswith("SECONDARY_STAGE|"):
                parts = mid_str.split("|")
                if len(parts) >= 5:
                    playoff_fixtures.append(
                        {
                            "id": mid,
                            "a": parts[3],
                            "b": parts[4],
                            "is_future": True,
                            "jornada": parts[1],
                            "dia": "-",
                            "hora": "-",
                            "divisao": "1",
                            "grupo": "",
                        }
                    )

        # O utilizador pediu uma ordenação estrita das fases de playoff: Quartos, Meias, 3º Lugar, Final
        def get_playoff_order(match):
            jornada = str(match.get("jornada", ""))
            stage_order = {
                "1ºFase": 1,
                "Fase final": 2,
                "Quartos": 1,
                "Semifinais": 2,
                "3º Lugar": 3,
                "Final": 4,
            }
            return stage_order.get(jornada, 99)

        playoff_fixtures.sort(key=get_playoff_order)
        all_matches_to_export = fixtures + playoff_fixtures

        for match in all_matches_to_export:
            if not (match.get("is_future") and match.get("id") in match_forecasts):
                continue

            mid = match["id"]
            fc = match_forecasts[mid]
            elo_fc = match_elo_forecast.get(mid, {})
            score_dist = match_score_stats.get(mid, {})

            elo_a_expected = elo_fc.get("elo_a_mean", teams[match["a"]].elo)
            elo_a_std = elo_fc.get("elo_a_std", 0.0)
            elo_b_expected = elo_fc.get("elo_b_mean", teams[match["b"]].elo)
            elo_b_std = elo_fc.get("elo_b_std", 0.0)

            # Calcular golos esperados e desvio padrão a partir da distribuição de placares
            expected_goals_a = expected_goals_b = 0.0
            variance_a = variance_b = 0.0
            if score_dist:
                total_sims = sum(score_dist.values())
                for score_str, count in score_dist.items():
                    try:
                        ga, gb = (int(x) for x in score_str.split("-"))
                        w = count / total_sims
                        expected_goals_a += ga * w
                        expected_goals_b += gb * w
                    except (ValueError, IndexError):
                        pass
                for score_str, count in score_dist.items():
                    try:
                        ga, gb = (int(x) for x in score_str.split("-"))
                        w = count / total_sims
                        variance_a += w * (ga - expected_goals_a) ** 2
                        variance_b += w * (gb - expected_goals_b) ** 2
                    except (ValueError, IndexError):
                        pass

                sorted_scores = sorted(
                    score_dist.items(), key=lambda x: x[1], reverse=True
                )
                distribuicao_str = "|".join(
                    f"{s}:{(c / total_sims) * 100:.4f}%" for s, c in sorted_scores
                )
            else:
                distribuicao_str = ""

            writer.writerow(
                {
                    "jornada": _format_prediction_jornada(match.get("jornada", "")),
                    "dia": match.get("dia", ""),
                    "hora": match.get("hora", ""),
                    "team_a": match["a"],
                    "team_b": match["b"],
                    "expected_elo_a": f"{elo_a_expected:.1f}",
                    "expected_elo_a_std": f"{elo_a_std:.1f}",
                    "expected_elo_b": f"{elo_b_expected:.1f}",
                    "expected_elo_b_std": f"{elo_b_std:.1f}",
                    "prob_vitoria_a": f"{fc.get('p_win_a', 0) * 100:.4f}",
                    "prob_empate": f"{fc.get('p_draw', 0) * 100:.4f}",
                    "prob_vitoria_b": f"{fc.get('p_win_b', 0) * 100:.4f}",
                    "expected_goals_a": f"{expected_goals_a:.2f}",
                    "expected_goals_a_std": f"{variance_a ** 0.5:.2f}",
                    "expected_goals_b": f"{expected_goals_b:.2f}",
                    "expected_goals_b_std": f"{variance_b ** 0.5:.2f}",
                    "ocorrencias": fc.get("ocorrencias", n_simulations),
                    "divisao": match.get("divisao", ""),
                    "grupo": match.get("grupo", ""),
                    "distribuicao_placares": distribuicao_str,
                }
            )
            future_count += 1
    # --- CSV 3: Estatísticas de Liguilha (se houver) ---
    if liguilla_stats:
        liguilla_file = (
            out_dir / f"liguilla_{modalidade}_{ano_atual}_{n_simulations}{suffix}.csv"
        )
        with open(liguilla_file, "w", newline="", encoding="utf-8-sig") as csvfile:
            fieldnames = [
                "team",
                "p_disputa_lm1",
                "p_ganho_lm1_cond",
                "p_disputa_lm2_cond",
                "p_ganho_lm2_cond",
                "p_disputa_lm3_cond",
                "p_ganho_lm3_cond",
                "p_promocao",
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            for team in sorted(all_teams_in_epoch):
                if team not in liguilla_stats:
                    continue

                stats = liguilla_stats[team]
                n = n_simulations

                # Probabilidades
                p_lm1 = stats["lm1_participated"] / n
                p_lm1_won = (
                    stats["lm1_won"] / stats["lm1_participated"]
                    if stats["lm1_participated"] > 0
                    else 0
                )
                p_lm2 = stats["lm2_participated"] / n
                p_lm2_won = (
                    stats["lm2_won"] / stats["lm2_participated"]
                    if stats["lm2_participated"] > 0
                    else 0
                )
                p_lm3 = stats["lm3_participated"] / n
                p_lm3_won = (
                    stats["lm3_won"] / stats["lm3_participated"]
                    if stats["lm3_participated"] > 0
                    else 0
                )
                p_promoted = stats["promoted"] / n

                writer.writerow(
                    {
                        "team": team,
                        "p_disputa_lm1": f"{p_lm1 * 100:.4f}",
                        "p_ganho_lm1_cond": f"{p_lm1_won * 100:.4f}",
                        "p_disputa_lm2_cond": (
                            f"{p_lm2 / n * 100:.4f}" if n > 0 else "0.0000"
                        ),
                        "p_ganho_lm2_cond": f"{p_lm2_won * 100:.4f}",
                        "p_disputa_lm3_cond": (
                            f"{p_lm3 / n * 100:.4f}" if n > 0 else "0.0000"
                        ),
                        "p_ganho_lm3_cond": f"{p_lm3_won * 100:.4f}",
                        "p_promocao": f"{p_promoted * 100:.4f}",
                    }
                )
        print(f"Estatísticas de liguilha guardadas em {liguilla_file}\n")

    # --- CSV 4: Cenários agregados de Liguilha (se houver) ---
    if liguilla_scenarios:
        liguilla_scenarios_file = (
            out_dir
            / f"liguilla_scenarios_{modalidade}_{ano_atual}_{n_simulations}{suffix}.csv"
        )
        with open(
            liguilla_scenarios_file, "w", newline="", encoding="utf-8-sig"
        ) as csvfile:
            fieldnames = [
                "team",
                "scenario_key",
                "stage_game1",
                "opponent_game1",
                "p_win_game1",
                "p_draw_game1",
                "p_loss_game1",
                "stage_game2",
                "opponent_game2",
                "p_win_game2",
                "p_draw_game2",
                "p_loss_game2",
                "p_cenario",
                "p_passa_cenario_cond",
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            for team in sorted(liguilla_scenarios.keys()):
                scenarios = liguilla_scenarios.get(team, {})
                ordered_scenarios = sorted(
                    scenarios.items(),
                    key=lambda item: int(item[1].get("scenario_count", 0)),
                    reverse=True,
                )
                for scenario_key, stats in ordered_scenarios:
                    scenario_count = int(stats.get("scenario_count", 0) or 0)
                    if scenario_count <= 0:
                        continue

                    p_cenario = (
                        scenario_count / n_simulations if n_simulations > 0 else 0
                    )
                    p_passa_cenario_cond = (
                        int(stats.get("promoted_count", 0) or 0) / scenario_count
                    )

                    writer.writerow(
                        {
                            "team": team,
                            "scenario_key": scenario_key,
                            "stage_game1": stats.get("stage_game1", ""),
                            "opponent_game1": stats.get("opponent_game1", ""),
                            "p_win_game1": f"{(int(stats.get('game1_wins', 0) or 0) / scenario_count) * 100:.4f}",
                            "p_draw_game1": f"{(int(stats.get('game1_draws', 0) or 0) / scenario_count) * 100:.4f}",
                            "p_loss_game1": f"{(int(stats.get('game1_losses', 0) or 0) / scenario_count) * 100:.4f}",
                            "stage_game2": stats.get("stage_game2", ""),
                            "opponent_game2": stats.get("opponent_game2", ""),
                            "p_win_game2": f"{(int(stats.get('game2_wins', 0) or 0) / scenario_count) * 100:.4f}",
                            "p_draw_game2": f"{(int(stats.get('game2_draws', 0) or 0) / scenario_count) * 100:.4f}",
                            "p_loss_game2": f"{(int(stats.get('game2_losses', 0) or 0) / scenario_count) * 100:.4f}",
                            "p_cenario": f"{p_cenario * 100:.4f}",
                            "p_passa_cenario_cond": f"{p_passa_cenario_cond * 100:.4f}",
                        }
                    )

        print(f"Cenários de liguilha guardados em {liguilla_scenarios_file}\n")

    if future_count > 0:
        print(
            f"Previsões de {future_count} jogos futuros guardadas em {predictions_file}\n"
        )
    else:
        print(
            f"Nenhum jogo futuro encontrado para {modalidade} (ou sem previsões disponíveis)\n"
        )


def main(
    hardset_args: Tuple | None = None,
    hardset_csv: str | None = None,
    filter_modalidade: str | None = None,
    deep_simulation: bool = False,
    deeper_simulation: bool = False,
    use_calibrated: bool = False,
    calibrated_config_path: str | None = None,
):
    """
    Orquestra a pipeline completa: carrega dados, corre Monte Carlo e exporta resultados.

    Args:
        hardset_args: Lista de tuplas (match_id, score) do argparse (opcional).
        hardset_csv: Caminho para CSV com resultados fixados (opcional).
        filter_modalidade: Processar apenas uma modalidade específica (opcional).
        deep_simulation: Usar 100k iterações em vez de 10k (opcional).
        deeper_simulation: Usar 1M iterações em vez de 10k (opcional).
        use_calibrated: Usar parâmetros calibrados (opcional).
        calibrated_config_path: Caminho customizado para config calibrada (opcional).
    """
    docs_dir = str(Path(__file__).resolve().parent.parent / "docs")

    os.makedirs(Path(docs_dir) / "output" / "previsoes", exist_ok=True)
    os.makedirs(Path(docs_dir) / "output" / "cenarios", exist_ok=True)

    course_mapping, course_mapping_short = load_course_mapping(docs_dir)
    playoff_rules = load_playoff_rules(docs_dir)
    print(f"Carregado mapeamento de {len(course_mapping)} variações de nomes de cursos")
    if playoff_rules:
        print("✅ Regras de playoff carregadas do ficheiro JSON\n")
    else:
        print("⚠️ Aviso: playoff_rules.json não encontrado ou inválido\n")

    hardset_manager = _build_hardset_manager(
        hardset_args, hardset_csv, course_mapping_short
    )

    elo_system = CompleteTacauaEloSystem(k_base=ELO_K_BASE)
    sport_simulators = {
        "FUTSAL FEMININO": SportScoreSimulator("futsal"),
        "FUTSAL MASCULINO": SportScoreSimulator("futsal"),
        "ANDEBOL MISTO": SportScoreSimulator("andebol"),
        "BASQUETEBOL FEMININO": SportScoreSimulator("basquete"),
        "BASQUETEBOL MASCULINO": SportScoreSimulator("basquete"),
        "VOLEIBOL FEMININO": SportScoreSimulator("volei"),
        "VOLEIBOL MASCULINO": SportScoreSimulator("volei"),
        "FUTEBOL DE 7 MASCULINO": SportScoreSimulator("futebol7"),
    }

    calibrated_config = load_calibrated_config(docs_dir, calibrated_config_path)
    if calibrated_config:
        print("✅ Parâmetros calibrados carregados - serão utilizados nesta simulação")

    season_token, previous_season, season_end_year = season_context()

    # Determinar quais modalidades processar (filtragem por hardset ou argumento)
    hardset_modalidades: Set[str] = set()
    if hardset_manager and hardset_manager.fixed_results:
        hardset_modalidades = hardset_manager.get_affected_modalidades()
        if hardset_modalidades:
            print(
                f"\n🎯 Hardset afeta modalidades: {', '.join(sorted(hardset_modalidades))}"
            )
            print("ℹ️ Processando APENAS essas modalidades...\n")
        else:
            print("\n⚠️ Aviso: Hardset carregado mas nenhuma modalidade foi detectada")
            print("ℹ️ Processando TODAS as modalidades...\n")

    n_simulations = (
        N_SIMULATIONS_DEFAULT
        if not deep_simulation and not deeper_simulation
        else (N_SIMULATIONS_DEEPER if deeper_simulation else N_SIMULATIONS_DEEP)
    )

    modalidades_path = Path(docs_dir) / "output" / "csv_modalidades"
    season_suffix = f"_{season_token}"

    for modalidade_file in os.listdir(modalidades_path):
        if not modalidade_file.endswith(f"{season_suffix}.csv"):
            continue

        modalidade = modalidade_file.replace(f"{season_suffix}.csv", "")

        if hardset_modalidades and modalidade not in hardset_modalidades:
            continue
        if filter_modalidade and modalidade != filter_modalidade:
            continue

        print(f"Simulando modalidade: {modalidade}")

        score_simulator = sport_simulators.get(
            modalidade, sport_simulators["FUTSAL MASCULINO"]
        )
        past_seasons = [previous_season, season_token]

        historical_draw_rate = calculate_historical_draw_rate(
            modalidade, past_seasons, docs_dir
        )
        if historical_draw_rate > 0:
            print(f"  Taxa histórica de empates: {historical_draw_rate:.1%}")

        # --- Carregar dados ---
        (
            initial_elos,
            all_csv_rows,
            past_matches_rows,
            future_matches_rows,
            division_baselines,
            division_draw_rates,
        ) = _load_modalidade_data(
            modalidade,
            season_suffix,
            past_seasons,
            docs_dir,
            modalidades_path,
            modalidade_file,
            course_mapping,
            score_simulator,
            calibrated_config,
        )

        # --- Construir equipas e fixtures ---
        (
            teams,
            fixtures,
            all_teams_in_epoch,
            team_division,
            withdrawn_teams,
            playoff_eliminated_teams,
            playoff_active_winners,
        ) = _build_teams_and_fixtures(
            all_csv_rows,
            past_matches_rows,
            future_matches_rows,
            course_mapping,
            course_mapping_short,
            initial_elos,
            modalidade,
        )

        if withdrawn_teams:
            print(
                f"  ⚠️  Equipas desistentes detectadas (excluídas da simulação e com descida garantida): "
                f"{', '.join(sorted(withdrawn_teams))}"
            )

        if playoff_active_winners:
            print(
                f"  🏆 Vencedores ativos de playoff (rondas já jogadas): "
                f"{', '.join(sorted(playoff_active_winners))}"
            )

        # --- Correr simulação ---
        teams_with_fixtures = {t: teams[t] for t in all_teams_in_epoch if t in teams}

        has_liguilla = any(
            str(row.get(COL_JORNADA, "")).upper().startswith(("LM", "PM"))
            for row in all_csv_rows
        )
        playoff_slots, total_playoff_slots = parse_playoff_slots(all_csv_rows)

        # Se não encontramos vagas via placeholders, tentamos via regras
        if not playoff_slots and playoff_rules:
            playoff_slots, total_playoff_slots = infer_slots_from_rules(
                modalidade, playoff_rules
            )

        secondary_playoff_pm1 = parse_secondary_playoff_structure(
            all_csv_rows, course_mapping
        )
        secondary_liguilla_rows = parse_secondary_liguilla_structure(
            all_csv_rows, course_mapping
        )

        # Fallback para regras se o CSV não tem liguilhas/playoffs secundários definidos
        if not secondary_playoff_pm1 and not secondary_liguilla_rows and playoff_rules:
            pm1_inferred, lm_inferred = infer_secondary_brackets_from_rules(
                modalidade, playoff_rules
            )
            if pm1_inferred:
                secondary_playoff_pm1 = pm1_inferred
                has_liguilla = True
            if lm_inferred:
                secondary_liguilla_rows = lm_inferred
                has_liguilla = True
        real_points = calculate_real_points(
            past_matches_rows,
            course_mapping,
            withdrawn_teams=withdrawn_teams,
            modalidade=modalidade,
        )
        past_played_matches = extract_played_matches_for_tiebreak(
            past_matches_rows,
            course_mapping,
            withdrawn_teams=withdrawn_teams,
            modalidade=modalidade,
        )

        if (
            not fixtures
            and not playoff_slots
            and not secondary_playoff_pm1
            and not secondary_liguilla_rows
        ):
            print(
                f"Nenhum jogo futuro ou estrutura de playoff encontrada para {modalidade}\n"
            )
            continue

        (
            results,
            match_forecasts,
            match_elo_forecast,
            match_score_stats,
            liguilla_stats,
            liguilla_scenarios,
        ) = monte_carlo_forecast(
            teams_with_fixtures,
            fixtures,
            elo_system,
            score_simulator,
            n_simulations=n_simulations,
            team_division=team_division,
            has_liguilla=has_liguilla,
            real_points=real_points,
            playoff_slots=playoff_slots,
            total_playoff_slots=(
                total_playoff_slots
                if total_playoff_slots > 0
                else PLAYOFF_SLOTS_DEFAULT
            ),
            secondary_playoff_pm1=secondary_playoff_pm1,
            secondary_liguilla_rows=secondary_liguilla_rows,
            past_played_matches=past_played_matches,
            hardset_manager=hardset_manager,
            withdrawn_teams=withdrawn_teams,
            playoff_eliminated_teams=playoff_eliminated_teams,
            playoff_active_winners=playoff_active_winners,
            modalidade=modalidade,
            playoff_rules=playoff_rules,
        )

        # --- Diagnóstico de baselines ---
        predicted_stats = calculate_predicted_division_stats(
            fixtures, match_score_stats
        )
        print("Medias historicas e previstas (golos por equipa) e taxa de empates:")
        all_divs = set(division_baselines.keys()) | set(predicted_stats.keys())
        all_divs.add(None)
        for div_key in sorted([d for d in all_divs if d is not None]) + [None]:
            hist_base = division_baselines.get(div_key)
            hist_draw = division_draw_rates.get(div_key, 0.0)
            pred = predicted_stats.get(div_key)
            div_label = f"Div {div_key}" if div_key is not None else "Geral"
            hist_mean = hist_base["mean"] if hist_base else 0.0
            hist_std = hist_base.get("std", 0.0) if hist_base else 0.0
            pred_mean = pred["mean"] if pred else 0.0
            pred_draw = pred["draw_rate"] if pred else 0.0
            pred_n = pred["matches"] if pred else 0
            print(
                f"  {div_label}: historico={hist_mean:.2f} +/- {hist_std:.2f}, "
                f"empates={hist_draw:.1%} | previsto={pred_mean:.2f}, "
                f"empates={pred_draw:.1%} (jogos={pred_n})"
            )

        print(f"Equipas com fixtures: {len(all_teams_in_epoch)}")

        if playoff_slots:
            print("Somas de p_playoffs por grupo (devem bater com vagas x 100%):")
            for (div, grp), slots in sorted(playoff_slots.items()):
                group_key = (div, grp)
                group_teams = [t for t, tg in team_division.items() if tg == group_key]
                prob_sum = sum(
                    results.get(t, {}).get("p_playoffs", 0.0) * 100.0
                    for t in group_teams
                )
                expected_sum = slots * 100.0
                print(
                    f"  Div {div} Grupo {grp or '-'}: vagas={slots}, "
                    f"soma={prob_sum:.2f}, esperado={expected_sum:.2f}, "
                    f"diff={prob_sum - expected_sum:.2f}"
                )
            print()

        # --- Exportar resultados ---
        _export_results(
            docs_dir,
            modalidade,
            season_end_year,
            n_simulations,
            hardset_manager,
            all_teams_in_epoch,
            teams,
            team_division,
            initial_elos,
            real_points,
            results,
            fixtures,
            match_forecasts,
            match_elo_forecast,
            match_score_stats,
            liguilla_stats,
            liguilla_scenarios,
        )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Simula futuras épocas e gera previsões com suporte a cenários hardset",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
EXEMPLOS DE USO:

1. Simulação baseline (sem hardset):
   python preditor.py

2. Com um resultado fixado via argumentos:
   python preditor.py --hardset "FUTSAL MASCULINO_5_Engenharia_Gestão" "5-4"

3. Com múltiplos resultados fixados:
   python preditor.py \\
     --hardset "FUTSAL MASCULINO_5_Engenharia_Gestão" "5-4" \\
     --hardset "FUTSAL MASCULINO_6_Direito_Medicina" "2-2"

4. Carregando hardset de um CSV:
   python preditor.py --hardset-csv "cenarios/upset_engenharia.csv"

5. Combinando argumentos e CSV:
   python preditor.py \\
     --hardset "FUTSAL MASCULINO_5_Engenharia_Gestão" "5-4" \\
     --hardset-csv "cenarios/outros_jogos.csv"

6. Modo Deep Simulation (simular 100 000 de vezes em vez de 10 000):

Formato do CSV (match_id,score_a,score_b):
FUTSAL MASCULINO_5_Engenharia_Gestão,5,4
FUTSAL MASCULINO_6_Direito_Medicina,2,2
        """,
    )

    parser.add_argument(
        "--hardset",
        nargs=2,
        action="append",
        metavar=("MATCH_ID", "SCORE"),
        help="Fixar resultado: match_id e score (ex: 'FUTSAL MASCULINO_5_Eng_Gestão' '5-4')",
    )

    parser.add_argument(
        "--hardset-csv",
        type=str,
        help="Carregar resultados fixados de um CSV (formato: match_id,score_a,score_b)",
    )

    parser.add_argument(
        "--compare",
        action="store_true",
        help="Correr simulação baseline E com hardset, mostrando comparação",
    )

    parser.add_argument(
        "--modalidade",
        type=str,
        help="Processar apenas uma modalidade específica (ex: 'FUTSAL FEMININO')",
    )

    parser.add_argument(
        "--example",
        action="store_true",
        help="Mostrar exemplo de uso do sistema de hardset",
    )

    parser.add_argument(
        "--deep-simulation",
        action="store_true",
        help="Usar simulação profunda (100 000 de iterações em vez de 10 000)",
    )

    parser.add_argument(
        "--deeper-simulation",
        action="store_true",
        help="Usar simulação ainda mais profunda (1 000 000 de iterações em vez de 10 000)",
    )

    parser.add_argument(
        "--use-calibrated",
        action="store_true",
        help="Usar parâmetros calibrados do calibrator.py",
    )

    parser.add_argument(
        "--calibrated-config",
        type=str,
        help="Caminho customizado para calibrated_simulator_config.json",
    )

    args = parser.parse_args()

    # Se --example, mostrar exemplo e sair
    if args.example:
        print("\n" + "=" * 80)
        print("EXEMPLO DE USO DO SISTEMA DE HARDSET")
        print("=" * 80 + "\n")
        example_hardset_usage()
        sys.exit(0)

    # Inicializar hardset manager se houver argumentos ou CSV
    hardset_args = args.hardset if args.hardset else None
    hardset_csv = args.hardset_csv if args.hardset_csv else None
    deep_simulation = args.deep_simulation
    deeper_simulation = (
        args.deeper_simulation if hasattr(args, "deeper_simulation") else False
    )
    filter_modalidade = (
        args.modalidade if hasattr(args, "modalidade") and args.modalidade else None
    )

    # Se --compare, rodar simulação baseline E com hardset
    if args.compare and (hardset_args or hardset_csv):
        print("\n" + "=" * 80)
        print("MODO COMPARAÇÃO: Baseline vs Hardset")
        print("=" * 80 + "\n")

        print("🔄 Rodando simulação BASELINE (sem hardset)...\n")
        main(
            hardset_args=None,
            hardset_csv=None,
            filter_modalidade=filter_modalidade,
            deep_simulation=deep_simulation,
            deeper_simulation=deeper_simulation,
            use_calibrated=args.use_calibrated,
            calibrated_config_path=args.calibrated_config,
        )

        # Guardar resultados baseline
        # TODO: Implementar se necessário para comparação completa

        print("\n🔄 Rodando simulação COM HARDSET...\n")
        main(
            hardset_args=hardset_args,
            hardset_csv=hardset_csv,
            filter_modalidade=filter_modalidade,
            deep_simulation=deep_simulation,
            deeper_simulation=deeper_simulation,
            use_calibrated=args.use_calibrated,
            calibrated_config_path=args.calibrated_config,
        )
    else:
        # Simulação normal (com ou sem hardset)
        main(
            hardset_args=hardset_args,
            hardset_csv=hardset_csv,
            filter_modalidade=filter_modalidade,
            deep_simulation=deep_simulation,
            deeper_simulation=deeper_simulation,
            use_calibrated=args.use_calibrated,
            calibrated_config_path=args.calibrated_config,
        )
