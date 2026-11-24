"""A changed input must not inherit an older snapshot's dates or remove outputs."""

from pathlib import Path
from tempfile import TemporaryDirectory
import shutil
import pytest
from okf_planning.build import build_bundle

ROOT = Path(__file__).resolve().parents[1]


def test_changed_source_fails_before_replacing_generated_output():
    with TemporaryDirectory(prefix="okf-planning-source-lock-") as directory:
        root = Path(directory)
        source = root / "source"
        source.mkdir()
        for name in ("dataset.json", "organisation.json", "snapshot-lock.json"):
            shutil.copyfile(ROOT / "source" / name, source / name)
        with (source / "dataset.json").open("a") as stream:
            stream.write("\n")
        output = root / "bundle"
        output.mkdir()
        retained = output / "index.md"
        retained.write_text("Retained previous candidate\n")
        with pytest.raises(ValueError, match="Source bytes differ from the reviewed snapshot"):
            build_bundle(str(output), cache_dir=str(source))
        assert retained.read_text() == "Retained previous candidate\n"
