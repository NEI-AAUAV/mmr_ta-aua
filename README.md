# Taça UA — ELO e previsões | ELO ratings and predictions

[![Português](https://img.shields.io/badge/lang-pt-green.svg)](#português)
[![English](https://img.shields.io/badge/lang-en-red.svg)](#english)
[![Testes](https://github.com/SlicF/mmr_ta-aua/actions/workflows/tests.yml/badge.svg)](https://github.com/SlicF/mmr_ta-aua/actions/workflows/tests.yml)
[![Atualização](https://github.com/SlicF/mmr_ta-aua/actions/workflows/updater.yml/badge.svg)](https://github.com/SlicF/mmr_ta-aua/actions/workflows/updater.yml)
[![Licença: MIT](https://img.shields.io/badge/licen%C3%A7a-MIT-blue.svg)](LICENSE)

Interface pública: [slicf.github.io/mmr_ta-aua](https://slicf.github.io/mmr_ta-aua/)

---

<a id="português"></a>

## 🇵🇹 Português

### Visão geral

Sistema de classificação ELO e previsão de resultados para a **Taça da
Universidade de Aveiro**. Extrai as grelhas oficiais, calcula ratings, calibra
modelos de resultados e executa simulações de Monte Carlo para produzir
classificações, previsões de jogos e probabilidades de progressão.

São processadas oito modalidades: andebol misto, basquetebol feminino e
masculino, futebol de 7 masculino, futsal feminino e masculino e voleibol
feminino e masculino.

### Fluxo de dados

1. **`extrator.py`** descarrega o Excel oficial, identifica a época e as
   modalidades, normaliza equipas e gera CSVs por modalidade.
2. **`mmr_taçaua.py`** processa os resultados cronologicamente e exporta ELO,
   classificações, detalhe dos jogos e desempates.
3. **`calibrator.py`** estima parâmetros de distribuição a partir do histórico.
4. **`preditor.py`** simula a época com 10 mil, 100 mil ou 1 milhão de iterações.
5. **`docs/app.js`** apresenta os outputs estáticos publicados por GitHub Pages.

O pipeline usa ainda `calendario_parser.py` e `playoffs_parser.py` para enriquecer
datas e eliminatórias, `backtest_validation.py` para validação retrospetiva e
`run_calibration_pipeline.py` para orquestrar calibração e backtesting.

### Requisitos e instalação

- Python 3.11, versão usada nas GitHub Actions.
- Acesso à internet para descarregar a folha oficial.
- Node.js apenas para verificar a sintaxe do frontend; a interface publicada não
  requer build.

```bash
git clone https://github.com/SlicF/mmr_ta-aua.git
cd mmr_ta-aua
python -m pip install -r requirements.txt
```

### Configuração da fonte de dados

O extrator procura o URL por esta ordem:

1. `results_url` em `docs/config/config.json`;
2. variável de ambiente `RESULTS_URL`, se o valor anterior estiver ausente ou
   vazio;
3. ficheiro local mais recente em `data/`, se o download não estiver disponível.

São aceites links comuns de Google Sheets, Google Drive e OneDrive. Exemplo:

```json
{
  "results_url": "https://docs.google.com/spreadsheets/d/ID_DA_FOLHA/edit"
}
```

### Execução manual

A partir da raiz do repositório:

```bash
cd src
python extrator.py
python mmr_taçaua.py
python calibrator.py
python preditor.py
```

Principais opções:

| Comando | Função |
| --- | --- |
| `python extrator.py --force` | Reprocessa um ficheiro igual ao seu backup; não ignora a proteção entre épocas. |
| `python mmr_taçaua.py --season 25_26` | Processa uma época específica. |
| `python preditor.py --modalidade "FUTSAL MASCULINO"` | Simula apenas uma modalidade. |
| `python preditor.py --deep-simulation` | Executa 100 mil simulações. |
| `python preditor.py --deeper-simulation` | Executa 1 milhão de simulações. |
| `python preditor.py --hardset ID 2-1` | Fixa um resultado para explorar um cenário. |
| `python preditor.py --hardset-csv ficheiro.csv --compare` | Compara o cenário fixado com o baseline. |
| `python preditor.py --calibrated-config caminho.json` | Usa um ficheiro de calibração alternativo. |

Use `python <script> --help` para consultar todas as opções.

### Atualização e publicação automáticas

O workflow `updater.yml` corre às 00:00, 06:00, 12:00 e 18:00 UTC e também pode
ser iniciado manualmente. Quando o Excel mudou, executa extração, ELO,
calibração e previsões de 10 mil, 100 mil e 1 milhão de simulações. Cada nível é
guardado por commits automáticos do `github-actions[bot]`.

Os ficheiros em `docs/` são a aplicação estática usada pelo GitHub Pages. Assim,
os commits do updater publicam os novos dados sem um build de frontend separado.

### Mudança de época e proteção contra duplicados

As épocas mudam em agosto. Os organizadores podem reutilizar o mesmo URL antes
de limparem a folha da época anterior, pelo que o extrator compara os valores e
as fórmulas do workbook novo com o anterior:

- se forem iguais, elimina o download temporário, devolve `data_changed=false`
  e não executa ELO, calibração ou previsões;
- formatação, propriedades e metadados do `.xlsx` são ignorados;
- a primeira alteração real de uma célula desbloqueia a nova época;
- `docs/output/seasons.json` só inclui épocas publicáveis, sendo lido
  automaticamente pelo frontend.

O preditor usa a mesma viragem de agosto. Por exemplo, a época `26_27` produz
ficheiros de previsão com o ano final `2027`.

### Inputs e outputs

| Caminho | Conteúdo |
| --- | --- |
| `data/Resultados Taça UA AA_BB.xlsx` | Workbook oficial de cada época. |
| `data/backup_*.xlsx` | Cópias usadas para detetar alterações. |
| `docs/config/` | URL da fonte, nomes de cursos e regras de playoffs. |
| `docs/calendários/AA_BB/` | PDFs de calendário regular e playoffs. |
| `docs/output/csv_modalidades/` | Jogos normalizados por modalidade e época. |
| `docs/output/elo_ratings/` | ELO, classificações, detalhe e desempates. |
| `docs/output/calibration/` | Parâmetros calibrados e comparações. |
| `docs/output/previsoes/` | Forecasts, previsões e cenários de liguilha. |
| `docs/output/cenarios/` | Simulações produzidas por hardsets. |
| `docs/output/seasons.json` | Épocas disponibilizadas no frontend. |

O formato de cada CSV e JSON está descrito no
[dicionário de dados](docs/DATA_DICTIONARY.md).

### Frontend local

O frontend versionado é a aplicação estática em `docs/`. Para evitar limitações
de `file://`, sirva-a por HTTP a partir da raiz:

```bash
python -m http.server 8000 --directory docs
```

Depois abra `http://localhost:8000`. A pasta local `web/`, quando presente, é
uma migração experimental para React e está deliberadamente ignorada pelo Git;
não faz parte da aplicação publicada.

### Modelo ELO

A probabilidade esperada usa escala 250:

$$P(vitória) = \frac{1}{1 + 10^{-(\Delta ELO)/250}}$$

As equipas novas começam, por defeito, com 1000 pontos na 1.ª divisão, 500 na
2.ª e 750 quando a divisão é desconhecida. Sempre que possível, o rating é
herdado da época anterior.

A atualização usa:

$$K = 100 \times M_{fase} \times M_{proporção}$$

- `M_fase` é contínuo no início da época, neutro na fase regular, reforçado após
  a pausa de inverno, `1.5` em eliminatórias e `0.75` no jogo do 3.º lugar
  (`E3L`).
- `M_proporção` é calculado por
  $\max(s_1/s_2, s_2/s_1)^{1/10}$; resultados a zero usam `0.5` no denominador.
- Consequentemente, o código não impõe um intervalo global rígido de 65–210 ao
  K-factor.

### Calibração e backtesting

```bash
cd src

python run_calibration_pipeline.py
python run_calibration_pipeline.py --modalidade "FUTSAL MASCULINO"
python backtest_validation.py --compare-all
python backtest_validation.py --validate
```

Os resultados documentados incluem Brier Score de `0.133–0.175` e RMSE de
posição de `1.6–2.8`. Consulte [BACKTEST_RESULTS.md](docs/BACKTEST_RESULTS.md)
para contexto, amostra e limitações.

Ferramentas operacionais adicionais:

```bash
python backup_manual_playoffs.py --season 25_26
python calendario_parser.py 25_26
python playoffs_parser.py caminho/para/playoffs.pdf
python diagnose_multiplier.py
```

### Testes

A CI leve corre em pushes para `master` e pull requests relevantes. Instala as
dependências, verifica a sintaxe Python e JavaScript e executa os testes de
mudança de época e publicação. Não descarrega a folha oficial nem executa o
pipeline desportivo completo.

```bash
python -m compileall -q src
cd src
python -m unittest discover -p "test_*.py" -v
cd ..
node --check docs/app.js
```

### Documentação

1. [Arquitetura](docs/ARCHITECTURE.md)
2. [ELO e previsões](docs/ELO_AND_PREDICTION.md)
3. [Calibração detalhada](docs/CALIBRATION_DETAILED.md)
4. [Modelos de simulação](docs/SIMULATION_MODELS.md)
5. [Guia de operações](docs/OPERATIONS_GUIDE.md)
6. [Casos especiais](docs/SPECIAL_CASES.md)
7. [Resultados de backtesting](docs/BACKTEST_RESULTS.md)
8. [Arquitetura do frontend](docs/FRONTEND_ARCHITECTURE.md)
9. [Dicionário de dados](docs/DATA_DICTIONARY.md)

### Contribuição e licença

Consulte o [guia de contribuição](CONTRIBUTING.md) antes de abrir um pull
request. Problemas operacionais podem ser reportados nos
[GitHub Issues](https://github.com/SlicF/mmr_ta-aua/issues).

O código é disponibilizado sob a [licença MIT](LICENSE), com copyright de
Fábio Matias. Esta licença permite usar, copiar, modificar e redistribuir o
código, desde que sejam preservados o aviso de copyright e a licença. Os dados
importados das fontes oficiais da Taça UA mantêm os direitos e condições das
respetivas fontes e não são automaticamente abrangidos pela licença do código.

O modelo de manutenção institucional ainda não está decidido. Até lá,
`@SlicF` permanece como responsável no [`CODEOWNERS`](.github/CODEOWNERS); a
estrutura pode depois receber colaboradores individuais ou uma equipa do NEI,
consoante o repositório permaneça pessoal ou seja transferido para a
organização.

---

<a id="english"></a>

## 🇬🇧 English

### Overview

ELO rating and match prediction system for the **University of Aveiro Cup
(Taça UA)**. It extracts the official fixtures, computes ratings, calibrates
score models, and runs Monte Carlo simulations to produce standings, match
predictions, and progression probabilities.

Eight sports are processed: mixed handball, women's and men's basketball,
men's seven-a-side football, women's and men's futsal, and women's and men's
volleyball.

### Data flow

1. **`extrator.py`** downloads the official workbook, detects its season and
   sports, normalizes team names, and creates one CSV per sport.
2. **`mmr_taçaua.py`** processes results chronologically and exports ELO,
   standings, match details, and tiebreak data.
3. **`calibrator.py`** estimates score-distribution parameters from history.
4. **`preditor.py`** simulates the season with 10 thousand, 100 thousand, or
   1 million iterations.
5. **`docs/app.js`** presents the static outputs published through GitHub Pages.

Supporting modules include `calendario_parser.py` and `playoffs_parser.py` for
calendar and knockout data, `backtest_validation.py` for retrospective
validation, and `run_calibration_pipeline.py` for calibration orchestration.

### Requirements and installation

- Python 3.11, matching GitHub Actions.
- Internet access to download the official workbook.
- Node.js only for frontend syntax checks; the published UI requires no build.

```bash
git clone https://github.com/SlicF/mmr_ta-aua.git
cd mmr_ta-aua
python -m pip install -r requirements.txt
```

### Data-source configuration

The extractor looks for the results URL in this order:

1. `results_url` in `docs/config/config.json`;
2. the `RESULTS_URL` environment variable when the previous value is absent or
   empty;
3. the newest local workbook in `data/` when downloading is unavailable.

Common Google Sheets, Google Drive, and OneDrive links are accepted:

```json
{
  "results_url": "https://docs.google.com/spreadsheets/d/SHEET_ID/edit"
}
```

### Manual execution

From the repository root:

```bash
cd src
python extrator.py
python mmr_taçaua.py
python calibrator.py
python preditor.py
```

Main options:

| Command | Purpose |
| --- | --- |
| `python extrator.py --force` | Reprocesses a file equal to its backup; it does not bypass cross-season protection. |
| `python mmr_taçaua.py --season 25_26` | Processes a specific season. |
| `python preditor.py --modalidade "FUTSAL MASCULINO"` | Simulates one sport only. |
| `python preditor.py --deep-simulation` | Runs 100 thousand simulations. |
| `python preditor.py --deeper-simulation` | Runs 1 million simulations. |
| `python preditor.py --hardset ID 2-1` | Fixes a result for scenario exploration. |
| `python preditor.py --hardset-csv file.csv --compare` | Compares a fixed scenario with the baseline. |
| `python preditor.py --calibrated-config path.json` | Uses an alternative calibration file. |

Run `python <script> --help` for the complete option list.

### Automated updates and publishing

The `updater.yml` workflow runs at 00:00, 06:00, 12:00, and 18:00 UTC and can
also be started manually. When the workbook changes, it runs extraction, ELO,
calibration, and predictions at 10-thousand, 100-thousand, and 1-million
simulation depths. Each level is stored through automated
`github-actions[bot]` commits.

The files under `docs/` are the static GitHub Pages application. Updater commits
therefore publish new data without a separate frontend build.

### Season rollover and duplicate protection

Seasons roll over in August. Organizers may reuse the same URL before clearing
the previous season's sheet, so the extractor compares the new workbook's cell
values and formulas with the previous one:

- identical data removes the temporary download, returns `data_changed=false`,
  and skips ELO, calibration, and predictions;
- formatting, workbook properties, and `.xlsx` metadata are ignored;
- the first actual cell change enables the new season;
- `docs/output/seasons.json` contains only publishable seasons and is consumed
  automatically by the frontend.

The predictor follows the same August rollover. For example, season `26_27`
produces prediction files whose final year is `2027`.

### Inputs and outputs

| Path | Contents |
| --- | --- |
| `data/Resultados Taça UA YY_YY.xlsx` | Official workbook for each season. |
| `data/backup_*.xlsx` | Copies used for change detection. |
| `docs/config/` | Source URL, course names, and playoff rules. |
| `docs/calendários/YY_YY/` | Regular-season and playoff calendar PDFs. |
| `docs/output/csv_modalidades/` | Normalized matches by sport and season. |
| `docs/output/elo_ratings/` | ELO, standings, details, and tiebreak data. |
| `docs/output/calibration/` | Calibrated parameters and comparisons. |
| `docs/output/previsoes/` | Forecasts, predictions, and secondary-bracket scenarios. |
| `docs/output/cenarios/` | Simulations produced from hardsets. |
| `docs/output/seasons.json` | Seasons exposed by the frontend. |

See the [data dictionary](docs/DATA_DICTIONARY_EN.md) for every CSV and JSON
field.

### Local frontend

The tracked frontend is the static application under `docs/`. Serve it over
HTTP to avoid `file://` restrictions:

```bash
python -m http.server 8000 --directory docs
```

Then open `http://localhost:8000`. The local `web/` directory, when present, is
an experimental React migration deliberately ignored by Git; it is not part of
the published application.

### ELO model

Expected win probability uses a 250-point scale:

$$P(win) = \frac{1}{1 + 10^{-(\Delta ELO)/250}}$$

New teams default to 1000 points in division 1, 500 in division 2, and 750 when
the division is unknown. Ratings are inherited from the previous season when
available.

Rating updates use:

$$K = 100 \times M_{phase} \times M_{proportion}$$

- `M_phase` varies continuously early in the season, is neutral during the
  regular phase, increases after the winter break, equals `1.5` in knockouts,
  and equals `0.75` in the third-place match (`E3L`).
- `M_proportion` is
  $\max(s_1/s_2, s_2/s_1)^{1/10}$; zero scores use `0.5` in the denominator.
- The implementation therefore does not enforce a global 65–210 K-factor
  range.

### Calibration and backtesting

```bash
cd src

python run_calibration_pipeline.py
python run_calibration_pipeline.py --modalidade "FUTSAL MASCULINO"
python backtest_validation.py --compare-all
python backtest_validation.py --validate
```

Documented results include a `0.133–0.175` Brier Score and a `1.6–2.8` position
RMSE. See [BACKTEST_RESULTS_EN.md](docs/BACKTEST_RESULTS_EN.md) for context,
sample sizes, and limitations.

Additional operational tools:

```bash
python backup_manual_playoffs.py --season 25_26
python calendario_parser.py 25_26
python playoffs_parser.py path/to/playoffs.pdf
python diagnose_multiplier.py
```

### Tests

Lightweight CI runs on pushes to `master` and relevant pull requests. It
installs dependencies, checks Python and JavaScript syntax, and runs the season
rollover and publication tests. It does not download the official workbook or
execute the full sports pipeline.

```bash
python -m compileall -q src
cd src
python -m unittest discover -p "test_*.py" -v
cd ..
node --check docs/app.js
```

### Documentation

1. [Architecture](docs/ARCHITECTURE_EN.md)
2. [ELO and predictions](docs/ELO_AND_PREDICTION_EN.md)
3. [Detailed calibration](docs/CALIBRATION_DETAILED_EN.md)
4. [Simulation models](docs/SIMULATION_MODELS_EN.md)
5. [Operations guide](docs/OPERATIONS_GUIDE_EN.md)
6. [Special cases](docs/SPECIAL_CASES_EN.md)
7. [Backtesting results](docs/BACKTEST_RESULTS_EN.md)
8. [Frontend architecture](docs/FRONTEND_ARCHITECTURE_EN.md)
9. [Data dictionary](docs/DATA_DICTIONARY_EN.md)

### Contributing and license

Read the [contribution guide](CONTRIBUTING.md) before opening a pull request.
Operational problems can be reported through
[GitHub Issues](https://github.com/SlicF/mmr_ta-aua/issues).

The code is distributed under the [MIT License](LICENSE), copyright Fábio
Matias. The license permits using, copying, modifying, and redistributing the
code as long as its copyright and license notices are preserved. Data imported
from official Taça UA sources remains subject to the rights and terms of those
sources and is not automatically covered by the code license.

The institutional maintenance model has not been decided yet. Until then,
`@SlicF` remains responsible in [`CODEOWNERS`](.github/CODEOWNERS). The structure
can later list individual collaborators or an NEI team, depending on whether
the repository remains personal or is transferred to the organization.
