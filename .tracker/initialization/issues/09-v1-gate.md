# 09: v1 gate

Status: ready-for-human

Blocked by: 07 (Duplicates report), 08 (Tool decisions)

Spec: `.tracker/initialization/spec.md`.

**What to build:** The final checks before calling v1.

- [ ] `mise dotfiles diff` reviewed with no surprises
- [ ] A clean secret scan over the full history of the public and private repos
- [ ] One real new-machine run of `mise install`, `bake setup-dev` and `bake apply` works
- [ ] Each v1 gate item in the spec is ticked off, and the owner confirms v1
