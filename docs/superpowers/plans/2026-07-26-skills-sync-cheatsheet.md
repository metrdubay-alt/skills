# Skills Sync and Cheatsheet Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add `chip-legal-web-rf`, `chip-supergoal`, and `server-doctor` to the private skills repository, document them, update the existing Word cheatsheet, and publish the verified result to `main`.

**Architecture:** Treat the current local skill folders as immutable release inputs: copy them without rewriting their content, validate each package with its own checks, and keep secrets and private infrastructure data outside Git. Update the repository catalog separately from the user-facing `.docx`, preserving the existing Word layout by cloning its established section and table formatting.

**Tech Stack:** Git, PowerShell, Python 3, `python-docx`, package-provided Python/Node/shell validators.

## Global Constraints

- Add exactly `chip-legal-web-rf`, `chip-supergoal`, and `server-doctor`.
- Preserve each skill's complete folder structure, including scripts, references, templates, tests, and licenses.
- Do not commit `.env` files, credentials, tokens, private keys, caches, temporary files, or a private infrastructure SSOT.
- Describe `server-doctor` as public-safe operational guidance, not as a private inventory.
- Describe `chip-supergoal` as plan-only; it creates a `.supergoal` package and does not execute the implementation.
- Preserve the current structure and visual style of `E:\Users\Andrey\Desktop\Рабочая\AI\skills-cheatsheet.docx`.
- Publish only after package validation, secret scanning, repository checks, and DOCX structural verification succeed.

---

### Task 1: Import the three existing skill packages

**Files:**
- Create: `chip-legal-web-rf/**`
- Create: `chip-supergoal/**`
- Create: `server-doctor/**`

**Interfaces:**
- Consumes: local release inputs under `C:\Users\Andrey\.codex\skills\<skill-name>`.
- Produces: three installable top-level skill directories with a required `SKILL.md`.

- [ ] **Step 1: Confirm the destination folders do not already exist**

Run:

```powershell
Test-Path .\chip-legal-web-rf
Test-Path .\chip-supergoal
Test-Path .\server-doctor
```

Expected: all three commands return `False`.

- [ ] **Step 2: Copy each source package without transformation**

Run:

```powershell
Copy-Item "$HOME\.codex\skills\chip-legal-web-rf" . -Recurse
Copy-Item "$HOME\.codex\skills\chip-supergoal" . -Recurse
Copy-Item "$HOME\.codex\skills\server-doctor" . -Recurse
```

Expected: each destination contains `SKILL.md`; no source file is changed.

- [ ] **Step 3: Compare source and destination file hashes**

Run a PowerShell comparison over relative path plus SHA-256 for all files in each package.

Expected: no missing, extra, or changed files.

### Task 2: Update the repository catalog

**Files:**
- Modify: `README.md`

**Interfaces:**
- Consumes: the actual frontmatter and package requirements of the three imported skills.
- Produces: discoverable catalog entries with purpose, trigger examples, dependencies, and safety boundaries.

- [ ] **Step 1: Add three catalog groups**

Add:

```markdown
### Legal
- `chip-legal-web-rf` - Public-clean Russian website legal-pack drafting and review.

### Planning
- `chip-supergoal` - Plan-only SuperGoal package creation for non-trivial software work.

### Server operations
- `server-doctor` - Public-safe diagnosis and repair patterns for bots, services, and small server fleets.
```

Include a compact trigger and requirements note for each skill. State explicitly that credentials and private topology remain outside the repository.

- [ ] **Step 2: Check Markdown and repository whitespace**

Run:

```powershell
git diff --check
```

Expected: exit code `0` and no output.

### Task 3: Update the Word cheatsheet without redesigning it

**Files:**
- Modify: `E:\Users\Andrey\Desktop\Рабочая\AI\skills-cheatsheet.docx`
- Create temporarily: `E:\Users\Andrey\Documents\New project\update_skills_cheatsheet.py`

**Interfaces:**
- Consumes: the existing section-heading, skill-heading, and four-row table formatting in the DOCX.
- Produces: one new section containing three skill entries with the fields `Команда`, `Что делает`, `Когда применять`, and `Что требуется`.

- [ ] **Step 1: Write a structural preflight check**

The script must assert before editing:

```python
assert any(p.text.strip() == "video-analyzer" for p in document.paragraphs)
assert len(document.tables) == 16
assert all(len(table.rows) == 4 and len(table.columns) == 2 for table in document.tables)
```

Expected: the script stops without replacing the DOCX if its known structure has changed.

- [ ] **Step 2: Append the new section using cloned formatting**

Append a section titled `ПРАВО, ПЛАНИРОВАНИЕ И СЕРВЕРЫ`, then entries for:

```text
chip-legal-web-rf
chip-supergoal
server-doctor
```

For every entry, clone the existing skill heading and 4×2 table structure; replace only visible text. Write to a temporary `.docx` first.

- [ ] **Step 3: Verify the generated document structurally**

Open the temporary file with `python-docx` and assert:

```python
assert len(document.tables) == 19
assert all(name in full_text for name in (
    "chip-legal-web-rf",
    "chip-supergoal",
    "server-doctor",
))
assert "HUMAN20_BEARER_TOKEN" not in full_text
```

Expected: all assertions pass, then atomically replace the requested DOCX.

- [ ] **Step 4: Attempt visual rendering**

Run the bundled `render_docx.py` against the updated file.

Expected: rendered pages are inspected if LibreOffice is available. If the runtime lacks LibreOffice, record that limitation and rely on the successful structural checks without claiming visual-render verification.

- [ ] **Step 5: Remove the temporary update script**

Delete only `E:\Users\Andrey\Documents\New project\update_skills_cheatsheet.py` after the updated DOCX passes verification.

### Task 4: Validate every imported package and scan for secrets

**Files:**
- Test: `chip-legal-web-rf/tests/**`
- Test: `chip-supergoal/tests/**`
- Test: `server-doctor/tests/**`

**Interfaces:**
- Consumes: the imported package trees.
- Produces: evidence that the copied releases are structurally valid, operationally testable, and public-safe.

- [ ] **Step 1: Validate skill metadata**

Run the bundled `skill-creator/scripts/quick_validate.py` once for each skill directory.

Expected: all three validations pass.

- [ ] **Step 2: Run package-owned validation**

Run:

```powershell
python .\chip-legal-web-rf\scripts\validate_public_skill.py
python .\server-doctor\scripts\privacy_gate.py --root .\server-doctor
```

Run the documented `chip-supergoal` test entry point and the relevant local test commands for the other packages.

Expected: all invoked tests exit `0`; any skipped environment-specific tests are reported explicitly.

- [ ] **Step 3: Scan tracked candidates for sensitive material**

Search filenames and contents for `.env`, private-key files, bearer tokens, API keys, passwords, host/user inventories, and credential-like assignments.

Expected: no secrets or private infrastructure records are present. Example placeholders and public-safe documentation are allowed only after manual inspection.

- [ ] **Step 4: Verify the complete repository**

Run:

```powershell
git status --short
git diff --check
git ls-files
```

Expected: only the planned skills, README, design spec, and implementation plan are changed or added.

### Task 5: Commit and publish the verified update

**Files:**
- Modify: Git history on `codex/update-skills-cheatsheet`
- Modify: remote `main`

**Interfaces:**
- Consumes: verified repository changes.
- Produces: the updated private GitHub skills repository on `main`.

- [ ] **Step 1: Commit the implementation**

Run:

```powershell
git add README.md chip-legal-web-rf chip-supergoal server-doctor docs/superpowers/plans/2026-07-26-skills-sync-cheatsheet.md
git commit -m "Add legal planning and server skills"
```

Expected: one implementation commit after the existing design-spec commit.

- [ ] **Step 2: Fast-forward local main**

Run:

```powershell
git switch main
git merge --ff-only codex/update-skills-cheatsheet
```

Expected: `main` advances without a merge commit.

- [ ] **Step 3: Push main**

Run:

```powershell
git push origin main
```

Expected: the remote reports a successful update and `git status --short` is empty.

## Self-Review

- Spec coverage: all three packages, README catalog, DOCX update, safety exclusions, validation, commit, and push are covered.
- Placeholder scan: the plan contains no `TBD`, `TODO`, or unspecified implementation step.
- Interface consistency: package names, source paths, destination paths, document path, and branch names are consistent across tasks.
