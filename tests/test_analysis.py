"""Tests for analysis utilities: cognates, sound_change, and roots."""

import pytest

from austronesian.analysis.cognates import (
    levenshtein,
    normalised_distance,
    find_potential_cognates,
    group_by_cognate_class,
)
from austronesian.analysis.sound_change import (
    tokenise,
    apply_rules,
    build_correspondence_table,
    top_correspondences,
)
from austronesian.analysis.roots import (
    normalise_proto,
    reconstruct_proto,
    format_comparison_table,
)
from austronesian.models.cognate import CognateSet
from austronesian.models.lexeme import Lexeme


# ---------------------------------------------------------------------------
# Levenshtein / distance
# ---------------------------------------------------------------------------

class TestLevenshtein:
    def test_identical(self):
        assert levenshtein("mata", "mata") == 0

    def test_single_substitution(self):
        assert levenshtein("mata", "maka") == 1

    def test_insertion(self):
        assert levenshtein("mat", "mata") == 1

    def test_deletion(self):
        assert levenshtein("mata", "mat") == 1

    def test_empty_strings(self):
        assert levenshtein("", "") == 0
        assert levenshtein("abc", "") == 3
        assert levenshtein("", "abc") == 3

    def test_completely_different(self):
        assert levenshtein("abc", "xyz") == 3


class TestNormalisedDistance:
    def test_identical(self):
        assert normalised_distance("mata", "mata") == 0.0

    def test_completely_different(self):
        assert normalised_distance("abc", "xyz") == pytest.approx(1.0)

    def test_empty(self):
        assert normalised_distance("", "") == 0.0
        assert normalised_distance("abc", "") == pytest.approx(1.0)

    def test_partial(self):
        d = normalised_distance("mata", "maka")
        assert 0.0 < d < 1.0


# ---------------------------------------------------------------------------
# find_potential_cognates
# ---------------------------------------------------------------------------

class TestFindPotentialCognates:
    def _lexemes(self):
        return [
            Lexeme(language_name="Amis", form="mata", meaning="eye"),
            Lexeme(language_name="Tagalog", form="mata", meaning="eye"),
            Lexeme(language_name="Malay", form="mata", meaning="eye"),
            Lexeme(language_name="Hawaiian", form="maka", meaning="eye"),
            Lexeme(language_name="Japanese", form="me", meaning="eye"),
        ]

    def test_identical_forms_grouped(self):
        lexemes = self._lexemes()
        sets = find_potential_cognates(lexemes, "eye", threshold=0.4)
        # "mata"/"mata"/"mata"/"maka" should cluster together; "me" may be separate
        all_forms = {
            form
            for cs in sets
            for m in cs.members
            for form in [m.form]
        }
        assert "mata" in all_forms

    def test_empty_forms_excluded(self):
        lexemes = [
            Lexeme(language_name="Amis", form="mata"),
            Lexeme(language_name="X", form=""),
        ]
        sets = find_potential_cognates(lexemes, "eye")
        all_members = [m for cs in sets for m in cs.members]
        assert all(m.form for m in all_members)

    def test_no_lexemes(self):
        assert find_potential_cognates([], "eye") == []


# ---------------------------------------------------------------------------
# group_by_cognate_class
# ---------------------------------------------------------------------------

class TestGroupByCognateClass:
    def test_basic_grouping(self):
        lexemes = [
            Lexeme(language_name="Amis", form="mata", cognate_class="A"),
            Lexeme(language_name="Tagalog", form="mata", cognate_class="A"),
            Lexeme(language_name="Malay", form="eye", cognate_class="B"),
        ]
        groups = group_by_cognate_class(lexemes)
        assert "A" in groups
        assert "B" in groups
        assert len(groups["A"].members) == 2
        assert len(groups["B"].members) == 1


# ---------------------------------------------------------------------------
# Tokenisation
# ---------------------------------------------------------------------------

class TestTokenise:
    def test_simple(self):
        assert tokenise("mata") == ["m", "a", "t", "a"]

    def test_ng_digraph(self):
        tokens = tokenise("ngipen")
        assert "ng" in tokens

    def test_empty(self):
        assert tokenise("") == []

    def test_single_char(self):
        assert tokenise("a") == ["a"]


# ---------------------------------------------------------------------------
# apply_rules
# ---------------------------------------------------------------------------

class TestApplyRules:
    def test_single_rule(self):
        assert apply_rules("mata", {"t": "d"}) == "mada"

    def test_multiple_rules(self):
        assert apply_rules("pitu", {"p": "f", "t": "d"}) == "fidu"

    def test_no_match(self):
        assert apply_rules("mata", {"x": "y"}) == "mata"

    def test_empty_form(self):
        assert apply_rules("", {"t": "d"}) == ""


# ---------------------------------------------------------------------------
# build_correspondence_table
# ---------------------------------------------------------------------------

class TestBuildCorrespondenceTable:
    def _make_cognate_sets(self):
        return [
            CognateSet(
                proto_form="*mata",
                meaning="eye",
                members=[
                    Lexeme(language_name="Amis", form="mata"),
                    Lexeme(language_name="Tagalog", form="mata"),
                ],
            ),
            CognateSet(
                proto_form="*lima",
                meaning="hand",
                members=[
                    Lexeme(language_name="Amis", form="lima"),
                    Lexeme(language_name="Tagalog", form="lima"),
                ],
            ),
        ]

    def test_basic_table(self):
        table = build_correspondence_table(
            self._make_cognate_sets(), "Amis", "Tagalog"
        )
        assert ("m", "m") in table
        assert table[("m", "m")] == 2  # appears in both "mata" and "lima" (l→l)

    def test_missing_language(self):
        table = build_correspondence_table(
            self._make_cognate_sets(), "Amis", "Hawaiian"
        )
        assert table == {}

    def test_top_correspondences(self):
        table = build_correspondence_table(
            self._make_cognate_sets(), "Amis", "Tagalog"
        )
        top = top_correspondences(table, n=5)
        assert isinstance(top, list)
        # Should return at most 5 items
        assert len(top) <= 5


# ---------------------------------------------------------------------------
# Proto-form utilities
# ---------------------------------------------------------------------------

class TestNormaliseProto:
    def test_strip_asterisk(self):
        assert normalise_proto("*mata") == "mata"

    def test_double_asterisk(self):
        assert normalise_proto("**ma-qetil") == "ma-qetil"

    def test_no_asterisk(self):
        assert normalise_proto("mata") == "mata"

    def test_empty(self):
        assert normalise_proto("") == ""


class TestReconstructProto:
    def test_identical_forms(self):
        cs = CognateSet(
            meaning="eye",
            members=[
                Lexeme(form="mata"),
                Lexeme(form="mata"),
                Lexeme(form="mata"),
            ],
        )
        assert reconstruct_proto(cs) == "*mata"

    def test_majority_vote(self):
        cs = CognateSet(
            meaning="eye",
            members=[
                Lexeme(form="mata"),
                Lexeme(form="mata"),
                Lexeme(form="maca"),
            ],
        )
        result = reconstruct_proto(cs)
        assert result.startswith("*")
        assert "mat" in result

    def test_empty_members(self):
        cs = CognateSet(meaning="eye", members=[])
        assert reconstruct_proto(cs) == ""

    def test_empty_forms_ignored(self):
        cs = CognateSet(
            meaning="eye",
            members=[
                Lexeme(form=""),
                Lexeme(form="mata"),
            ],
        )
        result = reconstruct_proto(cs)
        assert result == "*mata"


class TestFormatComparisonTable:
    def test_basic_output(self):
        cs = CognateSet(
            proto_form="*mata",
            meaning="eye",
            members=[
                Lexeme(language_name="Amis", form="mata"),
                Lexeme(language_name="Tagalog", form="mata"),
            ],
        )
        table = format_comparison_table(cs)
        assert "eye" in table
        assert "*mata" in table
        assert "Amis" in table
        assert "Tagalog" in table

    def test_missing_languages_shown_as_dash(self):
        cs = CognateSet(
            proto_form="*mata",
            meaning="eye",
            members=[
                Lexeme(language_name="Amis", form="mata"),
            ],
        )
        # Request Hawaiian which is absent
        table = format_comparison_table(cs, languages=["Amis", "Hawaiian"])
        assert "—" in table

    def test_no_proto(self):
        cs = CognateSet(
            meaning="eye",
            members=[Lexeme(language_name="Amis", form="mata")],
        )
        table = format_comparison_table(cs, include_proto=False)
        assert "Proto" not in table
