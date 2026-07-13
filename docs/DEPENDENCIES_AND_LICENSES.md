# Dependencies, provenance and licenses

`pyproject.toml` declares dependencies and `uv.lock` is the exact universal resolution. `DEPENDENCY_PROVENANCE.csv` snapshots every locked package/version, source, project URL and publisher-declared license metadata for that exact PyPI release. Regenerate it with `python scripts/generate_dependency_provenance.py` after changing the lock.

Seven is Apache-2.0. Optional groups separate voice, browser, robotics, MCP, document, music, tray and development dependencies. The lifecycle verifier runs `pip check`; uninstall removes Seven and its entry points, not shared third-party packages.

The CSV is engineering evidence, not legal advice. `UNKNOWN` means usable publisher metadata was unavailable, not that a package is unlicensed. Commercial redistributors must inspect actual distribution license files and bundled native components. Ollama models, Playwright browser engines, FFmpeg, OS speech engines, firmware and external coding-agent CLIs retain separate terms. Model weights are never bundled.

The current unresolved publisher declarations are NVIDIA CUDA/cuDNN/NCCL/NVSHMEM packages selected by the optional Whisper/Torch graph and `pypiwin32`; redistribution must use their shipped license/EULA files. These are not core Seven dependencies.

Notable direct optionals include LGPL pygame/pystray and MPL-2.0 pyttsx3; they are dynamically installed dependencies, not copied Seven source.
