# Repository Guidelines

This repository is **云想衣裳 (YunXiangYiShang)**, an AI-powered wardrobe and outfit recommendation platform built with Flask, PyTorch, and Ollama.

## Project Structure & Module Organization

`app/` contains the Flask application. Key blueprints include `auth/`, `main/`, `wardrobe/`, `search/`, `recommendation/`, `fashion_advisor/`, and `style_analysis/`. Shared models live in `app/models.py`, reusable AI logic lives in `app/services/`, and configuration is in `config/default.py`. Frontend assets are split between `templates/` for Jinja2 views and `static/` for CSS, JS, and uploads. Tests live in `tests/`, and longer-form documentation lives in `docs/`.

## Build, Test, and Development Commands

- `python run.py` — start the Flask dev server on `http://localhost:5000`.
- `pip install -r requirements.txt` — install Python dependencies.
- `npm install` — install the Node.js Ollama proxy dependencies from `package.json`.
- `pytest tests/ -v` — run the existing pytest suite.
- `python -m compileall app/` — quick syntax verification for all backend modules.
- `docker-compose up --build` — build and run the full stack with Docker.

## Coding Style & Naming Conventions

Use Python 3.10+ with **4-space indentation** and follow PEP 8. Keep modules, functions, and variables in `snake_case`; class names in `PascalCase`; CSS classes in `kebab-case`. Blueprint template folders should match blueprint names, for example `templates/wardrobe/`. Use UTF-8 for every source file. Chinese copy must be literal, correct Chinese text only — no mojibake, no `?` placeholders, and no `\uXXXX` escapes in committed content.

## Testing Guidelines

The repository uses **pytest** with Flask’s `test_client()`. Add tests under `tests/` using the `test_<feature>.py` pattern. Reuse the local `client` fixture pattern from existing tests by calling `create_app()` with `TESTING=True`. Prefer endpoint-level tests for blueprint changes and focused service tests for pure Python logic.

## Commit & Pull Request Guidelines

Git history currently starts with a minimal `Initial commit`, so use clear imperative commit messages such as `Add advisor knowledge retrieval` or `Fix image search overlay clipping`. For pull requests, include a short summary, affected modules, manual verification steps, and screenshots for UI changes.

## Security & Configuration Tips

Keep secrets in `.env`, never in source files. MySQL and Ollama settings are loaded through `config/default.py`. Large local model weights belong under `app/models/` and should stay untracked. Before merging, verify both `pytest tests/ -v` and `python -m compileall app/` pass cleanly.
