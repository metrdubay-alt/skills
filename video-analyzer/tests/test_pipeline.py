from video_analyzer.pipeline import Stage, run_pipeline


def test_stage_with_multiple_artifacts_reruns_when_one_is_missing(tmp_path):
    (tmp_path / "document.md").write_text("ok", encoding="utf-8")
    calls = []

    def run(workdir, _config):
        calls.append(workdir)
        (workdir / "document.docx").write_bytes(b"docx")

    run_pipeline(
        [Stage("document", ("document.md", "document.docx"), run)],
        tmp_path,
        {},
    )

    assert calls == [tmp_path]
    assert (tmp_path / "document.docx").exists()
