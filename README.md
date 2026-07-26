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

### Legal

- `chip-legal-web-rf` - Drafts and reviews a public-clean Russian website legal pack: offers, privacy and personal-data policies, consent checkboxes, cookies, advertising consent, subscriptions, and product addenda. Use it before publishing a Russian-facing website or service. It needs public product facts, not credentials or private client data, and does not replace case-specific legal advice.

### Planning

- `chip-supergoal` - Creates a verified, plan-only `.supergoal` package for non-trivial software work, including roadmap, state, phase specifications, and review gates, then hands execution off explicitly through `/goal`. It plans the work but does not implement it.

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

### Server operations

- `server-doctor` - Provides public-safe diagnosis and repair patterns for Hermes Agent, OpenClaw, Telegram gateways, services, providers, sessions, and small server fleets. Use it for incidents, health checks, maintained-fork updates, deployment verification, and postmortems. Keep credentials, host inventories, and private topology in a separate protected SSOT, never in this repository.

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
