"""Execute the analysis notebooks in fresh kernels without editing source notebooks."""
import os
from pathlib import Path
import nbformat
from nbclient import NotebookClient

ROOT = Path(__file__).resolve().parents[1]
# Keep all runtime/config/font caches inside the writable project.
cache = ROOT / "artifacts" / "runtime"
cache.mkdir(parents=True, exist_ok=True)
for key, directory in (("IPYTHONDIR", "ipython"), ("JUPYTER_RUNTIME_DIR", "jupyter"), ("MPLCONFIGDIR", "matplotlib")):
    os.environ.setdefault(key, str(cache / directory))
output = ROOT / "artifacts" / "executed"
output.mkdir(parents=True, exist_ok=True)

for path in sorted((ROOT / "notebooks").glob("*.ipynb")):
    notebook = nbformat.read(path, as_version=4)
    nbformat.validate(notebook)
    client = NotebookClient(notebook, timeout=120, kernel_name="sat-lab",
                            resources={"metadata": {"path": str(ROOT)}})
    client.execute()
    nbformat.write(notebook, output / path.name)
    print(f"PASS {path.name}", flush=True)
