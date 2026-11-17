from config.runtime import source_fingerprint


def test_worker_fingerprint_detects_content_and_path_changes(tmp_path):
    folder = tmp_path / "backend" / "apps"
    folder.mkdir(parents=True)
    source = folder / "service.py"
    source.write_text("VERSION = 1\n")
    original = source_fingerprint(tmp_path)
    # Metadata-only changes should not require a worker restart.
    source.touch()
    assert source_fingerprint(tmp_path) == original
    source.write_text("VERSION = 2\n")
    changed = source_fingerprint(tmp_path)
    assert changed != original
    source.rename(folder / "renamed.py")
    assert source_fingerprint(tmp_path) != changed
