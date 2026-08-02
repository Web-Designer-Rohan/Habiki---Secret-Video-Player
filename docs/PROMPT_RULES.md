PROMPT_RULES.md

---

title: AI Development Rules
project: Hibiki
version: 1.0.0
status: Active
owner: Rohan
last_updated: 2026-08-02

Hibiki AI Development Rules

Purpose

This document defines the mandatory rules every AI coding agent must follow when working on Hibiki.

These rules exist to maintain consistency, code quality, documentation quality, and long-term maintainability.

If a requested change conflicts with these rules, the AI should explain the conflict and recommend the better engineering solution before implementation.

---

Core Philosophy

The objective is not to generate the largest amount of code.

The objective is to build software that looks and feels like it was created by an experienced engineering team.

Every change should improve the project.

Never sacrifice maintainability for speed.

---

Documentation First

Before implementing new functionality, the AI must read:

1. PRD.md
2. TRD.md
3. ARCHITECTURE.md
4. DESIGN.md
5. MEMORY_BANK.md
6. DECISIONS.md

Implementation must follow the documented architecture.

Documentation is the project's source of truth.

---

Think Before Coding

The AI should always:

- Understand the task.
- Consider multiple approaches.
- Choose the simplest maintainable solution.
- Explain significant trade-offs.
- Avoid unnecessary complexity.

Do not generate code immediately without understanding the context.

---

Scope Discipline

Implement only the requested functionality.

Do not silently add unrelated features.

Do not remove existing functionality unless explicitly instructed.

Future ideas belong in the roadmap rather than the implementation.

---

Architecture Compliance

Every change must respect the established architecture.

Do not:

- Mix frontend and backend responsibilities.
- Place business logic inside UI code.
- Access the filesystem directly from the frontend.
- Duplicate existing functionality.

---

Code Quality

Generated code should be:

- Readable
- Modular
- Predictable
- Consistent
- Self-explanatory

Prefer clarity over cleverness.

Avoid unnecessary abstractions.

---

Reuse Before Create

Before creating:

- A component
- A utility
- A helper
- A service
- A style

The AI must first determine whether an existing solution already exists.

Avoid duplicate implementations.

---

Simplicity

Prefer:

- Small functions
- Small modules
- Clear naming
- Explicit logic

Avoid overengineering.

---

Dependency Policy

Do not introduce new dependencies unless they provide a significant long-term benefit.

Before adding a dependency, evaluate:

- Maintenance
- Stability
- Community support
- Cross-platform compatibility
- License compatibility

The standard library should be preferred whenever practical.

---

Security Rules

Never:

- Store plaintext passwords.
- Hardcode secrets.
- Expose sensitive data.
- Trust user input.
- Disable security mechanisms for convenience.

Security should be considered during implementation, not after it.

---

Performance Rules

Prefer:

- Efficient algorithms
- Lazy loading where appropriate
- Small assets
- Optimized rendering
- Minimal allocations

Avoid premature optimization, but do not ignore obvious performance issues.

---

Accessibility Rules

Generated interfaces should support:

- Keyboard navigation
- Semantic HTML
- Screen readers
- Visible focus states
- High contrast
- Reduced motion preferences

Accessibility is a requirement, not an enhancement.

---

Error Handling

Errors should:

- Be handled gracefully.
- Provide useful diagnostics.
- Avoid exposing internal implementation details.
- Preserve application stability whenever possible.

---

Logging

Log useful operational information.

Do not log:

- Passwords
- Tokens
- Personal data
- Sensitive configuration

Logs should support troubleshooting without compromising privacy.

---

Documentation Updates

Whenever a significant architectural or functional change is introduced, the AI should determine whether the documentation requires updates.

Code and documentation should remain synchronized.

---

Testing Expectations

Where practical, new functionality should include appropriate tests.

Changes should avoid breaking existing behavior.

If testing is not implemented immediately, the AI should identify what should be tested.

---

User Experience

Every UI decision should improve one or more of the following:

- Readability
- Usability
- Consistency
- Performance

Avoid decorative elements that reduce usability.

---

AI Behaviour

The AI should:

- Ask questions only when required.
- Make sensible engineering decisions when requirements are clear.
- Explain important trade-offs.
- Respect existing project conventions.
- Keep responses concise and technically accurate.

Do not invent requirements that are not documented.

---

Decision Making

When multiple valid solutions exist, prefer the solution that offers the best balance of:

1. Maintainability
2. Simplicity
3. Performance
4. Security
5. Extensibility

Document major architectural decisions in "DECISIONS.md".

---

Completion Checklist

Before considering a task complete, verify:

- Requirements are satisfied.
- Architecture remains consistent.
- Code style matches the project.
- Existing functionality is preserved.
- Documentation is updated if necessary.
- No unnecessary dependencies were introduced.

---

Final Principle

Every contribution should leave Hibiki in a better state than it was before.

If a change improves quality, maintainability, readability, or consistency without introducing unnecessary complexity, it is generally the preferred solution.
