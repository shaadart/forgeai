"""Build colab/forgeai_colab.zip, the upload the notebook asks for. Run: python colab/make_zip.py"""

import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INCLUDE = ["forge", "prompts", "briefs", "data", "forge.colab.toml", "forge.toml", "pyproject.toml"]

with zipfile.ZipFile(ROOT / "colab" / "forgeai_colab.zip", "w", zipfile.ZIP_DEFLATED) as archive:
    for name in INCLUDE:
        path = ROOT / name
        for file in sorted(path.rglob("*")) if path.is_dir() else [path]:
            if file.is_file() and "__pycache__" not in file.parts:
                archive.write(file, file.relative_to(ROOT))
    print(f"{archive.filename}: {len(archive.namelist())} files")
