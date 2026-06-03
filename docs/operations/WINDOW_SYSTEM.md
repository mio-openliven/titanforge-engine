# Window System

Use this when running several Codex chats or several projects.

## Main Rule

One window = one role.

If a request is sent to the wrong role, the chat should refuse briefly and give the mini-prompt for the correct window.

## Window 0: Control / Ideas

Use for:

- ideas
- choosing project
- choosing role
- asking "where do I put this?"
- prioritizing across projects
- stopping scope chaos

Do not use for:

- coding
- reviewing code
- design polishing

Wrong-role response:

```text
This belongs in Window [number]. Paste this:
[mini prompt]
```

## Window 1: Planner

Use for PRD, task slicing, architecture, and acceptance criteria.

Mini prompt:

```text
Use project-conductor.
Role: Planner.
Project: [project name/path].
Task: turn this idea into 3-5 small tasks with acceptance criteria. Do not code.
```

## Window 2: Builder

Use for one task implementation.

Mini prompt:

```text
Use project-conductor.
Role: Builder.
Project: [project name/path].
Task ID: [id].
Read AGENTS.md/tasks.md, implement only this task, run tests, update docs, commit/push if allowed.
```

## Window 3: Designer

Use for UI/UX, preview readability, user-facing text, product feel, and visual direction.

Mini prompt:

```text
Use project-conductor.
Role: Designer.
Project: [project name/path].
Task: improve the user-facing experience/preview/text for [feature]. Give concrete UX/content guidance, no backend code.
```

## Window 4: Reviewer

Use for critique of latest diff/commit. No new features.

Mini prompt:

```text
Use project-conductor.
Role: Reviewer.
Project: [project name/path].
Review the latest commit/diff for bugs, risks, missing tests, and scope creep. Findings first. Do not add features.
```

## Window 5: Researcher

Use for donors, libraries, licenses, alternatives, and professional references.

Mini prompt:

```text
Use project-conductor.
Role: Researcher.
Project/topic: [name].
Find existing tools/donors/libraries for [task]. Return ranked options, license, integration risk, and what to use now.
```

## Two-Project Rule

If two projects are active, Window 0 must decide which project gets attention first.

Never let Builder work on two projects in one chat. Open a separate Builder chat per project.
