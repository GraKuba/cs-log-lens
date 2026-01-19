# CS Log Lens - Project Guidelines

## Package Management

- Always use `uv` for Python package management and virtual environments
- When working with new dependencies, ALWAYS call context-7-mcp for relevant context

## Task Management

### Task Tracking with tasks.md

All development work MUST be tracked in `docs/tasks.md`. This file serves as:
1. **Project roadmap** - Shows all tasks and their dependencies
2. **Context map** - Links tasks to specific lines in PRD and tech spec
3. **Progress tracker** - Shows what's done, in progress, and blocked
4. **Testing checklist** - Each task has acceptance criteria and required tests

### Working with Tasks

1. **Before starting work:**
   - Read `docs/tasks.md` to find the next task
   - Review the task's references in PRD and tech spec
   - Check for blockers and dependencies
   - Review acceptance criteria and test requirements

2. **During work:**
   - Update task status to "🟡 In Progress"
   - Follow the acceptance criteria exactly
   - Write tests as specified in "Tests Required"
   - Reference specific lines from PRD/tech spec as noted in the task

3. **After completing work:**
   - Run all tests listed in the task
   - Check off all acceptance criteria
   - Update task status to "🟢 Completed"
   - Add completion date
   - Update overall progress counters
   - Update "Completed Tasks" and "Next Up" sections

4. **If blocked:**
   - Update task status to "🔴 Blocked"
   - Document the blocker in the task
   - Add to "Blocked Tasks" section with explanation

### Task Update Format

When marking a task complete, update these sections:
```markdown
**Status:** 🟢 Completed
**Completed:** YYYY-MM-DD
**Acceptance Criteria:**
- [x] All items checked off
```

And update the progress table at the top of tasks.md.

## Conversation History

All conversations with Claude Code and Cursor must be logged in `docs/2-history/`.

### Naming Convention
```
YYYY-MM-DD-HHMM-<short-topic>.md
```

Example: `2026-01-19-1430-setup-history-tracking.md`

### Log Format
Each history file should include:
1. **Date/Time**: When the conversation started
2. **Tool**: Claude Code or Cursor
3. **Summary**: Brief description of what was discussed/accomplished
4. **Key Changes**: Files created, modified, or deleted
5. **Tasks Completed**: List of task IDs from tasks.md that were completed
6. **Conversation Log**: The actual back-and-forth (can be summarized for long convos)

### When to Create a New Log
- Start of each new conversation session
- Major topic changes within a session can be split into separate logs

## Development Workflow

1. Check `docs/tasks.md` for next task
2. Review task references in PRD/tech spec
3. Start work, update task status to in progress
4. Complete work according to acceptance criteria
5. Write and run tests
6. Mark task complete in tasks.md
7. Log work in `docs/2-history/`
8. Move to next task
