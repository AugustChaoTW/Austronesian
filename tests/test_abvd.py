"""Tests for ABVD database client (using mocked HTTP responses)."""

import json
import pytest
import responses as responses_lib

from austronesian.databases.abvd import ABVDClient, _BASE_URL
from austronesian.models.language import Language
from austronesian.models.lexeme import Lexeme


_LANGUAGE_RESPONSE = {
    "data": [
        {
            "id": "1",
            "language": "Malagasy",
            "silcode": "mlg",
            "glottocode": "mala1537",
            "location": "Madagascar",
            "latitude": "-18.9",
            "longitude": "47.5",
            "notes": "",
        }
    ]
}

_WORD_RESPONSE = {
    "data": [
        {
            "id": "10",
            "word_id": "1",
            "word": "hand",
            "item": "tanana",
            "annotation": "",
            "loan": "",
            "cognacy": "1",
            "language": {"language": "Malagasy"},
        },
        {
            "id": "11",
            "word_id": "2",
            "word": "eye",
            "item": "maso",
            "annotation": "",
            "loan": "",
            "cognacy": "2",
            "language": {"language": "Malagasy"},
        },
    ]
}

_LANGUAGES_RESPONSE = {
    "data": [
        {"id": "1", "language": "Malagasy", "silcode": "mlg",
         "glottocode": "mala1537", "location": "Madagascar",
         "latitude": "-18.9", "longitude": "47.5", "notes": ""},
        {"id": "2", "language": "Amis", "silcode": "ami",
         "glottocode": "amis1246", "location": "Taiwan",
         "latitude": "23.0", "longitude": "121.0", "notes": ""},
    ]
}


def _make_client() -> ABVDClient:
    """Return a client with zero crawl delay for faster tests."""
    return ABVDClient(delay=0)


@responses_lib.activate
def test_get_language():
    responses_lib.add(
        responses_lib.GET,
        _BASE_URL,
        json=_LANGUAGE_RESPONSE,
        status=200,
    )
    client = _make_client()
    lang = client.get_language(1)
    assert isinstance(lang, Language)
    assert lang.name == "Malagasy"
    assert lang.iso639_3 == "mlg"


@responses_lib.activate
def test_get_language_not_found():
    responses_lib.add(
        responses_lib.GET,
        _BASE_URL,
        json={"data": []},
        status=200,
    )
    client = _make_client()
    with pytest.raises(ValueError, match="No language found"):
        client.get_language(9999)


@responses_lib.activate
def test_get_words():
    responses_lib.add(
        responses_lib.GET,
        _BASE_URL,
        json=_WORD_RESPONSE,
        status=200,
    )
    client = _make_client()
    words = client.get_words(1)
    assert len(words) == 2
    assert all(isinstance(w, Lexeme) for w in words)
    assert words[0].meaning == "hand"
    assert words[0].form == "tanana"
    assert words[0].language_name == "Malagasy"
    assert words[1].meaning == "eye"
    assert words[1].form == "maso"


@responses_lib.activate
def test_list_languages():
    responses_lib.add(
        responses_lib.GET,
        _BASE_URL,
        json=_LANGUAGES_RESPONSE,
        status=200,
    )
    client = _make_client()
    langs = client.list_languages()
    assert len(langs) == 2
    assert langs[0].name == "Malagasy"
    assert langs[1].name == "Amis"


@responses_lib.activate
def test_search_languages_match():
    responses_lib.add(
        responses_lib.GET,
        _BASE_URL,
        json=_LANGUAGES_RESPONSE,
        status=200,
    )
    client = _make_client()
    result = client.search_languages("Amis")
    assert len(result) == 1
    assert result[0].name == "Amis"


@responses_lib.activate
def test_search_languages_no_match():
    responses_lib.add(
        responses_lib.GET,
        _BASE_URL,
        json=_LANGUAGES_RESPONSE,
        status=200,
    )
    client = _make_client()
    result = client.search_languages("Zzzznotexist")
    assert result == []


@responses_lib.activate
def test_compare_word():
    # Two calls: one for each language id
    responses_lib.add(
        responses_lib.GET, _BASE_URL, json=_WORD_RESPONSE, status=200
    )
    responses_lib.add(
        responses_lib.GET, _BASE_URL, json=_WORD_RESPONSE, status=200
    )
    client = _make_client()
    table = client.compare_word("eye", [1, 2])
    # Both mock calls return the same data → Malagasy with "maso"
    for forms in table.values():
        assert "maso" in forms


@responses_lib.activate
def test_http_error_raises():
    responses_lib.add(
        responses_lib.GET, _BASE_URL, status=500
    )
    client = _make_client()
    with pytest.raises(Exception):
        client.get_language(1)
