"""Seed genlayer-test 0.29.x's cache with the official pinned GenVM asset.

The test package requests genvm-universal.tar.xz, while v0.3.0-rc7 publishes
the equivalent runner bundle as genvm-runners-all.tar.xz.
"""

from hashlib import sha256
from pathlib import Path
from tempfile import NamedTemporaryFile
from urllib.request import Request, urlopen
import os


VERSION = "v0.3.0-rc7"
URL = (
    "https://github.com/genlayerlabs/genvm/releases/download/"
    f"{VERSION}/genvm-runners-all.tar.xz"
)
EXPECTED_SHA256 = "e218a1854214681560351051f76fe2b878545cf3409455ef372d57014a88ca67"
TARGET = Path.home() / ".cache" / "gltest-direct" / f"genvm-universal-{VERSION}.tar.xz"


def digest(path: Path) -> str:
    check = sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            check.update(chunk)
    return check.hexdigest()


def main() -> None:
    if TARGET.is_file() and digest(TARGET) == EXPECTED_SHA256:
        print(f"Verified GenVM runner: {TARGET}")
        return

    TARGET.parent.mkdir(parents=True, exist_ok=True)
    request = Request(URL, headers={"User-Agent": "ObligationGraph-test-setup"})
    temporary = None
    try:
        with urlopen(request, timeout=300) as response:
            with NamedTemporaryFile(dir=TARGET.parent, delete=False) as sink:
                temporary = Path(sink.name)
                for chunk in iter(lambda: response.read(1024 * 1024), b""):
                    sink.write(chunk)
        if digest(temporary) != EXPECTED_SHA256:
            raise RuntimeError("Downloaded GenVM runner checksum did not match")
        os.replace(temporary, TARGET)
        temporary = None
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    print(f"Verified GenVM runner: {TARGET}")


if __name__ == "__main__":
    main()
