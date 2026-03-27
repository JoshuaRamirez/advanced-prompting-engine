# ADR-006: Canonical/User Data Separation with SQLite Write Protection

**Date**: 2026-03-27
**Status**: Accepted

## Context

The engine ships with a pre-populated graph (canonical data) and allows clients to extend it (user data). These two data sets have fundamentally different integrity requirements:
- Canonical data must be immutable and consistent across all installations
- User data must be freely extensible and mutable
- User data must be able to reference and connect to canonical data
- Canonical data must survive user errors, contradictions, and version upgrades

## Decision

Separate canonical and user data into **distinct SQLite tables** with **DB-level write protection** on canonical tables. Merge at query time in the Graph Query Layer.

```
SQLite tables:
  canonical_nodes    (read-only via BEFORE UPDATE/DELETE triggers)
  canonical_edges    (read-only via BEFORE UPDATE/DELETE triggers)
  user_nodes         (read-write)
  user_edges         (read-write, FK to canonical OR user nodes)
```

## Rationale

- DB-level triggers are enforceable even if application code has bugs — defense in depth
- Separation at the persistence layer means canonical data can be shipped as a pre-built SQLite file and dropped in
- The merged graph view in NetworkX is a runtime construct — it never persists in a combined state that could be corrupted
- Foreign key constraints on user_edges ensure referential integrity to canonical nodes
- Canonical node IDs are permanent (namespaced: `branch.construct_name`) — never changed across versions

## Consequences

- **Positive**: Canonical data integrity is guaranteed at the database level, not just application level
- **Positive**: User data can be exported, backed up, or reset independently of canonical data
- **Positive**: Version upgrades can replace the canonical tables entirely without touching user data
- **Positive**: Provenance-scoped queries are trivial (filter by table source)
- **Negative**: Graph load at startup must merge two table sets into one NetworkX graph — slight complexity
- **Negative**: Cross-provenance edges (user edge between two canonical nodes) require FK references across tables
- **Trade-off**: Two-table merge adds startup complexity but guarantees data separation that single-table provenance tagging cannot.
