from kms_cli.formatters import format_detail, format_json, format_records


def test_format_json_keeps_non_ascii_text():
    assert format_json({"name": "知识库"}) == '{\n  "name": "知识库"\n}'


def test_format_records_uses_common_id_and_name_fields():
    text = format_records({"items": [{"id": "1", "name": "渠道 A"}]}, title="渠道")

    assert "渠道" in text
    assert "1" in text
    assert "渠道 A" in text


def test_format_detail_renders_nested_json_readably():
    text = format_detail({"id": "faq-1", "title": "问题", "answer": "答案"})

    assert '"faq-1"' in text
    assert '"问题"' in text
