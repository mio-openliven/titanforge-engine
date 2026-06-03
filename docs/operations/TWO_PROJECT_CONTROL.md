# Two Project Control

Use this when running Codex across TitanForge Engine and MSLaunch.

## Projects

TitanForge Engine:

```text
C:\Users\Li2Fox\Documents\ГИГАНТ
```

Purpose: Minecraft cinematic location generator. Current useful output is a location pack with mask preview, cleanup preview, layout JSON, heightmap preview, report, and manifest.

MSLaunch:

```text
C:\Users\Li2Fox\Documents\Лаунчер
```

Purpose: Minecraft launcher/modpack synchronizer. Current priority is recovery, stabilization, update/install flow, and release discipline.

## Main Rule

Window 0 decides project and role. Builder windows must work on one project only.

## Recommended Windows

- Window 0: Control Router for ideas, role choice, and priority.
- Window 1: Planner/Audit.
- Window 2: Builder for one scoped task.
- Window 3: Designer/User Experience.
- Window 4: Reviewer/Release QA.
- Window 5: Researcher/Donors.

## Launcher Start

Open a new Codex chat and paste:

```text
C:\Users\Li2Fox\Documents\Лаунчер\handoff_chat_kit\PROMPT_00_CONTROL_ROUTER.txt
```

That chat must not code. It chooses whether the next step goes to audit, launcher stability, panel, release, or mascot.

## TitanForge Start

Open a new Codex chat and say:

```text
Continue TitanForge Engine.
Working folder: C:\Users\Li2Fox\Documents\ГИГАНТ
Use titanforge-engine and project-conductor.
First run git status --short --branch and git pull origin main.
Then read AGENTS.md and docs/operations/WINDOW_SYSTEM.md.
Pick one safe next pass.
```

## Beginner Rule

If the user is confused, return one next action only.

Example:

```text
Open Window 0 for MSLaunch and paste PROMPT_00_CONTROL_ROUTER.txt. Do not paste launcher code there.
```

## Do Not Do

- Do not mix launcher and TitanForge code in one Builder chat.
- Do not let mascot/assets work modify launcher UI without approval.
- Do not let research import donor code before license/inventory review.
- Do not start a GUI for TitanForge before CLI/file formats/previews are stable.
