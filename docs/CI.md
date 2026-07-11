# Continuous Integration

`.github/workflows/ci.yml` validates the supported modern package rather than the archived v3 tree.

## Gates

1. Ubuntu tests on Python 3.11, 3.12 and 3.13 with `seven/` coverage.
2. Package/script byte compilation.
3. Regeneration of tracked-file and legacy-symbol inventories; undocumented drift fails CI.
4. Windows Python 3.13 wheel build and asset verification.
5. Windows wheel install with declared core dependencies, console help and identity load.
6. Wheel uninstall with absence of the installed package confirmed outside the checkout.

The baseline workflow was invalid: it referenced a missing root `requirements-stable.txt` and measured archived `core`, `integrations` and `utils` paths. It could not prove the current `seven/` package worked.

Live Ollama, physical audio/camera/robotics and long-running soak tests remain separate gates because shared GitHub runners do not provide the required local models and hardware.
