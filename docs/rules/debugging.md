# Bug Investigation Priority

Priority:

1. Recent git diff
2. Recent modified files
3. Recent reports
4. Related module
5. Full project scan

Never start with full project analysis.

Maximum dependency depth:
3 levels.

Generate hypotheses before code changes.

Do not modify code until root cause is identified.

# Investigation Output

After root cause is identified:

1. Fix the issue.
2. Document root cause.
3. Document prevention strategy.
4. Update knownIssues.md or lessonsLearned.md if reusable.

Do not modify debugging.md unless the debugging process itself improved.