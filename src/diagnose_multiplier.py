#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Diagnóstico manual da calibração do multiplicador de empates.

Este módulo executa trabalho imediatamente e não faz parte da suíte unittest.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from calibrator import (
    HistoricalDataLoader,
    HistoricalEloCalculator,
    DrawProbabilityCalibrator,
    DEFAULT_CSV_PATH,
    DEFAULT_CONFIG_PATH,
)

# Carregar dados
loader = HistoricalDataLoader(DEFAULT_CSV_PATH, DEFAULT_CONFIG_PATH)
games = loader.load_all_modalidades()
print(f"Total de jogos: {len(games)}")

# Calcular ELOs
modalidades = set(g["modalidade"] for g in games)
all_games_with_elo = []

for modalidade in sorted(modalidades):
    modalidade_games = [g for g in games if g["modalidade"] == modalidade]
    calculator = HistoricalEloCalculator()
    games_elo = calculator.calculate_historical_elos(modalidade_games)
    all_games_with_elo.extend(games_elo)

# Testar calibrador de empates para cada modalidade
for modalidade in sorted(modalidades):
    modalidade_games = [g for g in all_games_with_elo if g["modalidade"] == modalidade]

    # Encontrar taxa histórica de empates
    historical_draws = sum(1 for g in modalidade_games if g["is_draw"])
    historical_draw_rate = (
        historical_draws / len(modalidade_games) if modalidade_games else 0
    )

    # Treinar calibrador
    draw_cal = DrawProbabilityCalibrator()
    params = draw_cal.fit(modalidade_games, modalidade, None)

    # Calcular multiplicador
    multiplier = draw_cal.calculate_optimal_multiplier(
        all_games_with_elo, modalidade, None
    )

    print(f"\n{modalidade}:")
    print(f"  - Jogos: {len(modalidade_games)}")
    print(f"  - Taxa histórica de empates: {historical_draw_rate:.2%}")
    print(f"  - Modelo treinado: {draw_cal.model is not None}")
    if draw_cal.model is not None:
        print(f"    - Intercept: {draw_cal.model.intercept_[0]:.6f}")
        print(f"    - Coef linear: {draw_cal.model.coef_[0][0]:.8f}")
    print(f"  - Multiplicador ótimo: {multiplier}")

    # Calcular taxa prevista com multiplicador
    if draw_cal.model is not None:
        predicted_probs = []
        for g in modalidade_games:
            p = draw_cal.predict_draw_probability(g["elo_diff"])
            p_amplified = min(1.0, p * multiplier)
            predicted_probs.append(p_amplified)
        predicted_draw_rate = sum(predicted_probs) / len(predicted_probs)
        print(f"  - Taxa prevista com multiplicador: {predicted_draw_rate:.2%}")
        print(f"  - Erro: {abs(predicted_draw_rate - historical_draw_rate):.4f}")
