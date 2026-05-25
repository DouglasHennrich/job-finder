<!-- SPECKIT START -->

For additional context about technologies to be used, project structure,
shell commands, and other important information, read the current plan
at `specs/003-src-restructure-capgemini-scraper/plan.md`.

<!-- SPECKIT END -->

<!-- SQUAD OVERRIDES -->

## speckit.implement → Squad Route

**IMPORTANT:** `speckit.implement` is overridden in this project.
Do NOT execute tasks sequentially. Instead:

1. Read `.github/skills/speckit-implement-squad-route/SKILL.md`
2. Follow the skill exactly — group tasks by agent, fan out in parallel per phase
3. After all phases, trigger the Speckit Tasks Audit ceremony (tasks-auditor)

This override applies whenever the user says "speckit implement", "implement the tasks",
"implement speckit tasks", or the `speckit.implement` agent is invoked.

<!-- END SQUAD OVERRIDES -->

<!-- SPECKIT HOOKS -->

## Hook Execution — Mandatory Protocol

After **every** speckit command completes, you MUST run ALL hooks for the corresponding event.

**Never skip a hook because you already processed the first one.**

### How to do it

1. Run the hook list script to get every hook for the event:

   ```
   bash .specify/scripts/bash/list-hooks.sh <event>
   ```

   Replace `<event>` with the event name (e.g., `after_tasks`, `after_specify`).

2. The script outputs one line per enabled hook:

   ```
   COMMAND=speckit.squad.route OPTIONAL=false PROMPT=Routing tasks to Squad agents...
   ```

3. Process **every line**:
   - `OPTIONAL=false` → execute immediately with `runSubagent("<COMMAND>")`
   - `OPTIONAL=true` → announce to the user and ask for confirmation before executing

### Event ↔ Command mapping

| After completing...   | Event name            |
| --------------------- | --------------------- |
| speckit.specify       | `after_specify`       |
| speckit.clarify       | `after_clarify`       |
| speckit.plan          | `after_plan`          |
| speckit.tasks         | `after_tasks`         |
| speckit.implement     | `after_implement`     |
| speckit.checklist     | `after_checklist`     |
| speckit.analyze       | `after_analyze`       |
| speckit.constitution  | `after_constitution`  |
| speckit.taskstoissues | `after_taskstoissues` |

Same pattern applies to `before_*` hooks (run the script with the before event name before invoking the command).

<!-- END SPECKIT HOOKS -->
