import json
import tempfile
import unittest
from pathlib import Path

from tacaua_api import (
    CSV_BASE_HEADERS,
    fetch_all,
    known_teams,
    load_overrides,
    prune_stale_csvs,
    unknown_teams,
    unsupported_tournaments,
    validate_matches,
    matches_to_tables,
    season_token_from_name,
    write_tables,
)


def _match(
    mid,
    start,
    t1,
    t2,
    s1=None,
    s2=None,
    status="finished",
    tournament="Futsal Masculino 2ª Divisão Grupo B",
    modality="Futsal Masculino",
    ptype="team",
    location="Caixa UA",
):
    return {
        "match_id": mid,
        "status": status,
        "start_time": start,
        "location": location,
        "tournament_name": tournament,
        "modality_name": modality,
        "participants": [
            {"participant_id": f"id-{t1}", "participant_name": t1, "participant_type": ptype},
            {"participant_id": f"id-{t2}", "participant_name": t2, "participant_type": ptype},
        ],
        "results": [
            {"participant_id": f"id-{t1}", "score": s1},
            {"participant_id": f"id-{t2}", "score": s2},
        ],
    }


class SeasonTokenTests(unittest.TestCase):
    def test_parses_portuguese_season_name(self):
        self.assertEqual(season_token_from_name("Época 2026/2027"), "26_27")

    def test_returns_none_for_unknown_name(self):
        self.assertIsNone(season_token_from_name("Torneio"))


class MatchesToTablesTests(unittest.TestCase):
    def test_converts_utc_to_lisbon_and_formats_columns(self):
        # Outubro: Lisboa em WEST (UTC+1)
        tables = matches_to_tables(
            [_match("a", "2026-10-15T22:00:00Z", "Eng. Física", "Matemática", 1, 11)]
        )
        row = tables["FUTSAL MASCULINO"][0]
        self.assertEqual(row["Dia"], "2026-10-15 00:00:00")
        self.assertEqual(row["Hora"], "23h00")
        self.assertEqual(row["Golos 1"], 1)
        self.assertEqual(row["Golos 2"], 11)
        self.assertEqual(row["Divisão"], 2)
        self.assertEqual(row["Grupo"], "B")

    def test_date_rolls_over_after_midnight_lisbon(self):
        tables = matches_to_tables(
            [_match("a", "2026-10-15T23:30:00Z", "A", "B", 0, 0)]
        )
        row = tables["FUTSAL MASCULINO"][0]
        self.assertEqual(row["Dia"], "2026-10-16 00:00:00")
        self.assertEqual(row["Hora"], "00h30")

    def test_scheduled_match_has_blank_scores(self):
        tables = matches_to_tables(
            [_match("a", "2026-10-21T20:00:00Z", "A", "B", 3, 2, status="scheduled")]
        )
        row = tables["FUTSAL MASCULINO"][0]
        self.assertEqual(row["Golos 1"], "")
        self.assertEqual(row["Golos 2"], "")

    def test_skips_non_team_participants(self):
        tables = matches_to_tables(
            [_match("a", "2026-10-21T20:00:00Z", "X", "Y", 1, 0, ptype="athlete")]
        )
        self.assertEqual(tables, {})

    def test_modality_name_matches_legacy_sheet_name(self):
        tables = matches_to_tables(
            [
                _match(
                    "a",
                    "2026-10-21T20:00:00Z",
                    "A",
                    "B",
                    1,
                    0,
                    modality="Futebol 7 Masculino",
                    tournament="Futebol 7 Masculino (Fase de Liga)",
                )
            ]
        )
        self.assertIn("FUTEBOL DE 7 MASCULINO", tables)
        self.assertEqual(tables["FUTEBOL DE 7 MASCULINO"][0]["Divisão"], "")

    def test_jornada_increments_per_team_within_tournament(self):
        matches = [
            _match("1", "2026-10-06T20:00:00Z", "A", "B", 1, 0),
            _match("2", "2026-10-06T21:00:00Z", "C", "D", 1, 0),
            _match("3", "2026-10-13T20:00:00Z", "A", "C", 1, 0),
            _match("4", "2026-10-13T21:00:00Z", "B", "D", 1, 0),
            _match("5", "2026-10-20T20:00:00Z", "A", "D", 1, 0),
        ]
        rows = matches_to_tables(matches)["FUTSAL MASCULINO"]
        self.assertEqual([r["Jornada"] for r in rows], [1, 1, 2, 2, 3])

    def test_jornada_is_independent_between_tournaments(self):
        matches = [
            _match("1", "2026-10-06T20:00:00Z", "A", "B", 1, 0),
            _match(
                "2",
                "2026-10-07T20:00:00Z",
                "A",
                "B",
                1,
                0,
                tournament="Futsal Masculino 1º Divisão",
            ),
        ]
        rows = matches_to_tables(matches)["FUTSAL MASCULINO"]
        self.assertEqual([r["Jornada"] for r in rows], [1, 1])

    def test_team_a_suffix_is_dropped_but_b_is_kept(self):
        tables = matches_to_tables(
            [_match("1", "2026-10-06T20:00:00Z", "EGI A", "EGI B", 1, 0)],
            aliases={"EGI A": "EGI"},
        )
        row = tables["FUTSAL MASCULINO"][0]
        self.assertEqual((row["Equipa 1"], row["Equipa 2"]), ("EGI", "EGI B"))

    def test_override_marks_forfeit(self):
        tables = matches_to_tables(
            [_match("1", "2026-10-06T20:00:00Z", "A", "B", 3, 0)],
            overrides={("FUTSAL MASCULINO", "A", "B"): "B"},
        )
        self.assertEqual(tables["FUTSAL MASCULINO"][0]["Falta de Comparência"], "B")

    def test_does_not_mutate_input(self):
        matches = [_match("1", "2026-10-06T20:00:00Z", "A", "B", 1, 0)]
        snapshot = json.dumps(matches, sort_keys=True)
        matches_to_tables(matches)
        self.assertEqual(json.dumps(matches, sort_keys=True), snapshot)


class WriteTablesTests(unittest.TestCase):
    def test_writes_csv_with_legacy_header_and_division_columns(self):
        tables = matches_to_tables(
            [_match("a", "2026-10-15T22:00:00Z", "Eng. Física", "Matemática", 1, 11)]
        )
        with tempfile.TemporaryDirectory() as tmp:
            paths = write_tables(tables, "26_27", tmp)
            self.assertEqual(paths[0].name, "FUTSAL MASCULINO_26_27.csv")
            lines = paths[0].read_text(encoding="utf-8").splitlines()
        self.assertEqual(
            lines[0],
            ",".join(
                CSV_BASE_HEADERS[:8]
                + ["Divisão", "Grupo"]
                + CSV_BASE_HEADERS[8:]
            ),
        )
        self.assertIn("Eng. Física,1,11,Matemática,2,B,API,API,False,False,", lines[1])


class FetchAllTests(unittest.TestCase):
    def test_follows_pagination_until_total(self):
        pages = {
            1: {"items": [{"i": 1}, {"i": 2}], "total": 3},
            2: {"items": [{"i": 3}], "total": 3},
        }
        calls = []

        def getter(url, params):
            calls.append(params["page"])
            return pages[params["page"]]

        items = fetch_all("/matches", getter=getter, page_size=2)
        self.assertEqual([i["i"] for i in items], [1, 2, 3])
        self.assertEqual(calls, [1, 2])

    def test_stops_on_empty_page(self):
        def getter(url, params):
            return {"items": [], "total": 5}

        self.assertEqual(fetch_all("/matches", getter=getter), [])


class GuardTests(unittest.TestCase):
    def test_validate_rejects_missing_fields(self):
        bad = _match("1", "2026-10-06T20:00:00Z", "A", "B")
        del bad["start_time"]
        with self.assertRaises(ValueError):
            validate_matches([bad])

    def test_validate_accepts_real_shape(self):
        validate_matches([_match("1", "2026-10-06T20:00:00Z", "A", "B", 1, 0)])

    def test_unsupported_tournaments_flags_other_formats(self):
        found = unsupported_tournaments(
            [
                {"tournament_name": "Liga", "format": "league"},
                {"tournament_name": "Playoffs", "format": "knockout"},
            ]
        )
        self.assertEqual(found, ["Playoffs (knockout)"])

    def test_prune_removes_only_unreturned_csvs_of_season(self):
        tables = matches_to_tables(
            [_match("1", "2026-10-06T20:00:00Z", "A", "B", 1, 0)]
        )
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp)
            for name in (
                "FUTSAL MASCULINO_26_27.csv",
                "VOLEIBOL MASCULINO_26_27.csv",
                "VOLEIBOL MASCULINO_25_26.csv",
            ):
                (d / name).write_text("x", encoding="utf-8")
            removed = prune_stale_csvs(tables, "26_27", d)
            self.assertEqual([p.name for p in removed], ["VOLEIBOL MASCULINO_26_27.csv"])
            self.assertTrue((d / "VOLEIBOL MASCULINO_25_26.csv").exists())

    def test_unknown_teams_reports_names_missing_from_history(self):
        tables = matches_to_tables(
            [_match("1", "2026-10-06T20:00:00Z", "Velha", "Nova", 1, 0)]
        )
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "X_25_26.csv").write_text(
                "Equipa 1,Equipa 2\nVelha,Outra\n", encoding="utf-8"
            )
            known = known_teams(tmp, "26_27")
        self.assertEqual(unknown_teams(tables, known), ["Nova"])

    def test_load_overrides_reads_csv(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "o.csv"
            p.write_text(
                "Modalidade,Equipa 1,Equipa 2,Falta de Comparência\nfutsal masculino,A,B,B\n",
                encoding="utf-8",
            )
            self.assertEqual(load_overrides(p), {("FUTSAL MASCULINO", "A", "B"): "B"})


if __name__ == "__main__":
    unittest.main()
