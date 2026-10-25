import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
project = "mini_pix"
extensions = ["myst_parser", "sphinx.ext.autodoc", "sphinx.ext.napoleon", "sphinx.ext.viewcode"]
source_suffix = {".md": "markdown", ".rst": "restructuredtext"}
root_doc = "index"
language = os.environ.get("DOC_LANGUAGE", "en")
html_theme = "sphinx_rtd_theme"
exclude_patterns = ["_build", "_generated"]
autodoc_mock_imports = ["grpc_frame", "ese774_frame", "pixet", "pypixet", "cv2", "numpy"]
