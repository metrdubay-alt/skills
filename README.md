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

### Research

- `perplex` - Fast current web research through the Perplexity Sonar API.
- `deep` - Analyst-grade, source-backed deep research through Parallel Task API.

### Prompting

- `po` - Prompt Optimizer. Generates three optimized prompts for a user request.

### Reasoning

- `reasoning-personas` - Activates multi-persona reasoning modes such as `/rp`, Gonzo Truth-Seeker, Devil's Advocate, Pattern Hunter, and Integrator.

### Design and frontend

- `design-md` - Creates and validates `DESIGN.md` design-system specifications.
- `refero-design` - Research-first product and web design methodology, with optional Refero MCP research.
- `refero-web-design` - Routes website work through Refero references, `DESIGN.md`, Taste, Hallmark, and image-to-code.
- `hallmark` - Designs, audits, studies, and redesigns interfaces while avoiding generic AI patterns.
- `taste-skill` - Premium frontend visual-polish rules and anti-slop checks.
- `design-taste-frontend` - Compatibility name for the Taste frontend workflow.
- `image` - Writes structured prompts for GPT Image 2 and Nano Banana.
- `image-to-code` - Turns approved visual targets into frontend implementations.
- `webd` - End-to-end web design workflow for landing pages, SaaS sites, and frontend projects.

### Deployment

- `deploy-to-vercel` - Creates Vercel preview deployments; production requires an explicit request.
- `vercel-cli-with-tokens` - Uses Vercel CLI safely with environment-based token authentication.

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

To install every personal skill from the repository on Linux/macOS:

```bash
mkdir -p ~/.codex/skills
for skill in */; do cp -R "$skill" ~/.codex/skills/; done
```

On Windows PowerShell:

```powershell
New-Item -ItemType Directory -Force "$HOME\.codex\skills" | Out-Null
Get-ChildItem -Directory | ForEach-Object {
  Copy-Item $_.FullName "$HOME\.codex\skills\$($_.Name)" -Recurse
}
```

Keep API keys and access tokens in environment variables or local `.env` files. Never commit them to this repository.

## Update a skill

```bash
cd skills
git pull
rm -rf ~/.codex/skills/po
cp -R po ~/.codex/skills/po
```
