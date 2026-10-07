---
name: close-coding-session
description: Close out a substantial coding task by independently validating the work, promoting only durable session knowledge into authoritative project artifacts, preserving necessary continuation state, and producing a minimal handoff plus a fresh-session bootstrap prompt. Use only when the user explicitly invokes this skill after deciding that a large task or session is ready for closeout; never invoke it implicitly.
---

# Close Coding Session

Treat the repository as the source of truth. Use the conversation as a source of leads, not as proof. Preserve project knowledge that deserves to survive the session, not the conversation itself.

## 1. Verify the task state

1. Read every applicable `AGENTS.md`, starting at the repository root and following nested scope. Read relevant project documentation and any current task or execution plan.
2. Inspect `git status`, staged and unstaged diffs, and untracked files. Distinguish pre-existing user changes from work attributable to the task when possible.
3. Reconstruct the requested outcome and compare it with the repository. Do not accept a prior completion claim without evidence.
4. Run the relevant tests, type checks, lint, build, or other validation commands documented by the repository or clearly established during the task. Avoid inventing broad or destructive validation.
5. Classify the result as complete, incomplete, blocked, or unverified. Record exact unresolved failures and skipped validation.

Do not change implementation merely to force a complete result. Continue implementation only when the user explicitly asks. Do not commit, push, deploy, start another task, or perform destructive Git operations.

## 2. Extract and classify durable knowledge

Search existing `AGENTS.md` files, architecture/project documentation, ADRs, plans, and progress artifacts before writing. Classify each useful fact by lifetime:

- **Project-wide invariant:** Promote a verified, recurring rule to the narrowest applicable existing `AGENTS.md`. Keep it concise. Never add temporary instructions or implementation history.
- **Architecture or project knowledge:** Update the existing authoritative document that owns the topic. Preserve its conventions and explain only verified decisions, constraints, trade-offs, failure modes, or integration semantics. Create a new document only when no suitable location exists.
- **Task-durable state:** For unfinished or multi-session work, update the established plan or progress artifact with the objective, completed and remaining work, decisions, blockers, validation state, and next action. Do not create a progress file for a small completed task.
- **Reusable procedure:** Report it as a possible future Skill. Do not create another Skill without an explicit request.
- **Ephemeral information:** Discard raw logs, large stack traces, failed hypotheses, temporary output, intermediate searches, and dead ends.

Do not duplicate existing guidance. Update stale material only when current evidence is sufficient. Report uncertainty instead of inventing project knowledge.

## 3. Promote only necessary knowledge

Make the smallest documentation-only changes needed for future sessions. Prefer editing existing authoritative files over adding files. Do not overwrite useful documentation with a session summary, and do not modify `AGENTS.md` merely to preserve conversation history.

If no durable knowledge needs promotion, make no repository changes. Preserve unrelated working-tree changes.

## 4. Produce the minimal handoff

Return the handoff in the final response. Create or update a repository handoff file only when the repository already has that convention or the user explicitly requests one.

Include only applicable items not already clear from authoritative files:

- current task status;
- unresolved issues and validation status;
- important modified files;
- next recommended action;
- minimal reading list using paths to authoritative files.

Reference project artifacts instead of copying them. Do not reproduce the transcript or repeat content the next session can read directly.

## 5. Generate a fresh-session bootstrap prompt

End with a short, paste-ready prompt. Adapt paths to the handoff, but keep this shape:

```text
Read the applicable AGENTS.md files and [authoritative docs or task plan]. Inspect the current Git status and diff, then reconstruct the project and task state from the repository. Briefly report your understanding, including validation gaps or unresolved work, before making any changes.
```

If the task is incomplete, say so plainly and preserve only the continuation state required to resume it safely.
