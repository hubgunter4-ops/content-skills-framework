# Content Skills Toolkit Implementation Plan

> **For agentic workers:** Implement and verify this plan task-by-task.

**Goal:** Deliver a private, multi-folder repository containing one detailed, reusable module for every skill in the supplied catalog, plus a safe local CLI for discovery and validation.

**Architecture:** Each skill is an independent Markdown module with a stable frontmatter name, workflow, inputs, outputs, guardrails, request template, and checklist. A dependency-free Python CLI discovers modules from the filesystem and validates the required sections without executing external actions.

**Tech Stack:** Python 3.10+, Markdown, `unittest`, setuptools-style `pyproject.toml`.

**Spec:** `/home/ubuntu/upload/pasted_content.txt`.

## Global Constraints

- Omit all usage and star counts from generated content.
- Preserve the supplied skill names and descriptions in Spanish.
- Do not add credentials, external publishing, network automation, or destructive actions.
- Keep direct CLI usage and guided menu usage available.

---

### Task 1: Generate the skill catalog

**Files:** `skills/*/SKILL.md`, `README.md`

- [x] Parse each named skill and remove usage/star counts.
- [x] Create one independently reviewable folder per skill.
- [x] Add workflow, input/output contract, guardrails, request template, and checklist.

### Task 2: Add local discovery and validation

**Files:** `toolkit/__main__.py`, `toolkit/catalog.py`, `tests/test_toolkit.py`

- [x] Discover skill frontmatter from `skills/`.
- [x] Support `list`, `show`, and `validate` commands.
- [x] Provide a menu for no-argument execution with invalid input and cancellation handling.
- [x] Keep all actions local and read-only.

### Task 3: Document maintenance and safety

**Files:** `CONTRIBUTING.md`, `SECURITY.md`, `CHANGELOG.md`, `pyproject.toml`

- [x] Document review, naming, and validation conventions.
- [x] State the no-credentials and no-external-actions boundary.
- [x] Add a minimal install/test configuration.
