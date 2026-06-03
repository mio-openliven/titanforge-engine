# AI Workflow Minimum

This is the minimum operating system for using Codex across many projects.

## Professional Baseline

Use:

- small scoped tasks
- implementation plan before large code changes
- repo instructions in `AGENTS.md`
- visible tests/smoke checks
- separate review context for critique
- git commits as rollback points

Avoid:

- one giant chat for everything
- one giant prompt for a huge feature
- asking Builder to plan, design, research, code, and review at once
- accepting code without tests
- creating many repos for one product too early
- importing donor code before license/inventory review

## User Risk Profile

The user is a beginner in code but highly motivated and project-heavy.

Default response style:

- short
- direct
- one next action
- micro-options only when useful
- explain like the user is not required to be an engineer

## Scope Gate

Before coding, ask:

1. Which project?
2. Which window/role?
3. Which task ID?
4. What artifact proves success?
5. Which command tests it?

If these are unknown, route to Window 0 or Planner.

## Skills Rule

Do not create giant skills.

Good skill:

- short trigger
- short workflow
- references loaded only when needed
- no huge project history

Bad skill:

- giant memory dump
- mixed projects
- old arguments and dead ideas
- no clear trigger

## Source Notes

OpenAI guidance aligns with this:

- Codex works best with structure, context, and iteration.
- For large changes, start with an implementation plan.
- Well-scoped tasks are safer than huge vague prompts.
- `AGENTS.md`-style files tell Codex how to navigate a repo and what tests to run.
