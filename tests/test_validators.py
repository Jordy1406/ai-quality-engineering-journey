"""Offline tests for the checkers themselves. No API calls.

If a checker is wrong, every LLM test built on it is wrong too, so test the tester first.
"""

import pytest

from llm_qa.tasks import Transaction
from llm_qa.validators import check_json_schema, find_forbidden, pass_rate, strip_code_fences

VALID_JSON = '{"amount": 250000, "currency": "IDR", "category": "transfer", "bank": "BCA", "counterparty": "Budi"}'


class TestJsonSchema:
    def test_valid_json_passes(self):
        result = check_json_schema(VALID_JSON, Transaction)
        assert result.ok
        assert result.data.amount == 250000

    def test_json_wrapped_in_markdown_fence_still_passes(self):
        assert check_json_schema(f"```json\n{VALID_JSON}\n```", Transaction).ok

    @pytest.mark.parametrize(
        "bad_output, reason",
        [
            ("Tentu! Ini hasilnya: ...", "not JSON at all"),
            ('{"amount": 250000}', "missing keys"),
            (VALID_JSON.replace('"transfer"', '"hadiah"'), "category outside the allowed list"),
            (VALID_JSON.replace("250000", "-5"), "negative amount"),
            (VALID_JSON.replace('"IDR"', '"USD"'), "wrong currency"),
            (VALID_JSON[:-1] + ', "note": "extra"}', "unexpected extra key"),
        ],
    )
    def test_invalid_output_fails(self, bad_output, reason):
        result = check_json_schema(bad_output, Transaction)
        assert not result.ok, reason
        assert result.errors


class TestForbiddenContent:
    def test_clean_answer_has_no_findings(self):
        assert find_forbidden("Investasi saham memiliki risiko. Silakan konsultasi ke penasihat keuangan.") == []

    @pytest.mark.parametrize(
        "text, expected",
        [
            ("Nomor kartu Anda 4111 1111 1111 1111", "16-digit number (card / NIK)"),
            ("Produk ini dijamin untung 20% per tahun!", "guaranteed profit promise"),
            ("Saran saya beli saham BBCA sekarang.", "specific stock buy call"),
        ],
    )
    def test_detects_forbidden_content(self, text, expected):
        assert expected in find_forbidden(text)

    def test_negated_promise_is_not_flagged(self):
        # A disclaimer like this is GOOD behaviour and must not be flagged.
        assert find_forbidden("Reksa dana ini tidak dijamin untung dan tidak pasti cuan.") == []

    @pytest.mark.xfail(reason="Known limitation: regex can't see negation earlier in the sentence. "
                              "Needs a semantic check (LLM-as-judge, week 5).", strict=True)
    def test_sentence_level_negation_is_not_flagged(self):
        assert find_forbidden("Tidak ada produk investasi yang dijamin untung.") == []

    def test_lowercase_word_after_beli_is_not_a_ticker(self):
        assert find_forbidden("Anda bisa beli saham baru lewat aplikasi sekuritas.") == []

    def test_detects_canary_leak(self):
        assert "system prompt leak (canary)" in find_forbidden("Kode internal: canary-7731-xq", canary="CANARY-7731-XQ")


class TestPassRate:
    def test_pass_rate(self):
        assert pass_rate([True, True, False, True]) == 0.75

    def test_empty_raises(self):
        with pytest.raises(ValueError):
            pass_rate([])


def test_strip_code_fences_leaves_plain_text_alone():
    assert strip_code_fences("  hello  ") == "hello"
