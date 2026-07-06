# Codex Skills

Personal Codex skills synced for reuse across machines.

## Structure

Keep the repository flat:

```text
skills/
  po/
    SKILL.md
    references/
    scripts/
  another-skill/
    SKILL.md
```

One top-level folder is one Codex skill. Do not group skills into nested category folders, because Codex expects installed skills as direct children of `~/.codex/skills`.

## Skills

### Prompting

- `po` - Prompt Optimizer. Generates three optimized prompts for a user request.

### Video

- `video-analyzer` - Converts videos into Markdown and JSON using local transcription, scene detection, and OpenAI/Anthropic vision models.

## Install a skill

Clone this repository, then copy or symlink a skill folder into your Codex skills directory.

```bash
git clone https://github.com/metrdubay-alt/skills.git
mkdir -p ~/.codex/skills
cp -R skills/po ~/.codex/skills/po
```

After installing, start a new Codex session so the skill list refreshes.

## Update a skill

```bash
cd skills
git pull
rm -rf ~/.codex/skills/po
cp -R po ~/.codex/skills/po
```
