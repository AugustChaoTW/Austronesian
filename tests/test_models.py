"""Tests for data models."""

import pytest

from austronesian.models.language import Language
from austronesian.models.lexeme import Lexeme
from austronesian.models.cognate import CognateSet


class TestLanguage:
    def test_from_abvd_dict_basic(self):
        data = {
            "id": "1",
            "language": "Malagasy",
            "silcode": "mlg",
            "glottocode": "mala1537",
            "location": "Madagascar",
            "latitude": "-18.9",
            "longitude": "47.5",
            "notes": "sample note",
        }
        lang = Language.from_abvd_dict(data)
        assert lang.id == 1
        assert lang.name == "Malagasy"
        assert lang.iso639_3 == "mlg"
        assert lang.glottocode == "mala1537"
        assert lang.region == "Madagascar"
        assert lang.latitude == pytest.approx(-18.9)
        assert lang.longitude == pytest.approx(47.5)
        assert lang.notes == "sample note"

    def test_from_abvd_dict_missing_coordinates(self):
        data = {"id": "2", "language": "Amis", "silcode": "ami",
                "glottocode": "", "location": "Taiwan",
                "latitude": "", "longitude": "", "notes": ""}
        lang = Language.from_abvd_dict(data)
        assert lang.latitude is None
        assert lang.longitude is None

    def test_str(self):
        lang = Language(name="Amis", iso639_3="ami", region="Taiwan")
        s = str(lang)
        assert "Amis" in s
        assert "ami" in s
        assert "Taiwan" in s

    def test_str_minimal(self):
        lang = Language(name="Amis")
        assert str(lang) == "Amis"


class TestLexeme:
    def test_from_abvd_dict_basic(self):
        data = {
            "id": "999",
            "word_id": "1",
            "word": "hand",
            "item": "lima",
            "annotation": "",
            "loan": "",
            "cognacy": "1",
        }
        lex = Lexeme.from_abvd_dict(data, language_id=42, language_name="Amis")
        assert lex.id == 999
        assert lex.language_id == 42
        assert lex.language_name == "Amis"
        assert lex.word_id == 1
        assert lex.meaning == "hand"
        assert lex.form == "lima"
        assert lex.cognate_class == "1"
        assert lex.loan is False

    def test_loan_flag(self):
        data = {
            "id": "1", "word_id": "5", "word": "book",
            "item": "libro", "annotation": "", "loan": "Spanish", "cognacy": "",
        }
        lex = Lexeme.from_abvd_dict(data)
        assert lex.loan is True

    def test_str(self):
        lex = Lexeme(form="mata", meaning="eye", language_name="Amis")
        s = str(lex)
        assert "mata" in s
        assert "eye" in s
        assert "Amis" in s


class TestCognateSet:
    def _make_set(self) -> CognateSet:
        members = [
            Lexeme(language_name="Amis", form="mata", meaning="eye"),
            Lexeme(language_name="Tagalog", form="mata", meaning="eye"),
            Lexeme(language_name="Malay", form="mata", meaning="eye"),
        ]
        return CognateSet(proto_form="*mata", meaning="eye", members=members)

    def test_len(self):
        cs = self._make_set()
        assert len(cs) == 3

    def test_language_names(self):
        cs = self._make_set()
        assert cs.language_names() == ["Amis", "Malay", "Tagalog"]

    def test_forms_by_language(self):
        cs = self._make_set()
        fbl = cs.forms_by_language()
        assert fbl["Amis"] == ["mata"]
        assert fbl["Tagalog"] == ["mata"]

    def test_str(self):
        cs = self._make_set()
        s = str(cs)
        assert "*mata" in s
        assert "eye" in s
