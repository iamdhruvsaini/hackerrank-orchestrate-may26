# Contributing Guidelines: Commit Message Format

To keep the commit history clean and meaningful, follow these conventions for all commits in this repository:

## Commit Message Structure

Each commit message must be structured as follows:

```
<label>: <short summary>

[Optional body: more detailed explanatory text, wrapped to 72 characters.]
```

### Labels
Use one of the following labels at the start of your commit message:
- **feat**:     New feature
- **fix**:      Bug fix
- **docs**:     Documentation only changes
- **style**:    Formatting, missing semi colons, etc; no code change
- **refactor**: Code change that neither fixes a bug nor adds a feature
- **perf**:     Performance improvement
- **test**:     Adding or correcting tests
- **chore**:    Build process, CI, tooling, or other non-code changes

### Examples
```
feat: add agent escalation logic
fix: handle empty subject in ticket parser
chore: update requirements.txt
```

### Body (optional)
If needed, add a body after the summary to explain the motivation, context, or consequences of the change. Wrap lines at 72 characters.

---

## Additional Guidelines
- Use the imperative mood in the summary (e.g., "add" not "added" or "adds").
- Limit the summary to 50 characters.
- Separate subject from body with a blank line.
- Reference issues or tickets if relevant (e.g., `Fixes #123`).
- Use English for all commit messages.

---

Thank you for keeping the commit history clean and meaningful!
