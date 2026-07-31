from kernel.system.answer_log import write_answer, ANSWER_FILE, PREVIOUS_ANSWER_FILE


def test_write_answer_creates_file_with_timestamp_footer(tmp_path):
    write_answer(tmp_path, "First answer")
    content = (tmp_path / ANSWER_FILE).read_text(encoding="utf-8")
    assert "First answer" in content
    assert "Generálva:" in content


def test_write_answer_rotates_previous(tmp_path):
    write_answer(tmp_path, "First answer")
    write_answer(tmp_path, "Second answer")

    current = (tmp_path / ANSWER_FILE).read_text(encoding="utf-8")
    previous = (tmp_path / PREVIOUS_ANSWER_FILE).read_text(encoding="utf-8")

    assert "Second answer" in current
    assert "First answer" in previous
    assert "Second answer" not in previous
