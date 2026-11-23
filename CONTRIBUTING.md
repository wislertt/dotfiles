# Contributing

- Standards: [AGENTS.md](./AGENTS.md) holds this repo's conventions (four homes, secrets, bake verbs, four times, layout).
- Vocabulary: [GLOSSARY.md](./GLOSSARY.md). Decisions and their reasons: [docs/adr/](./docs/adr/).
- Run `bake lint` before committing. `bake test` runs the unit tests and `bake test-integration` runs the slow ones in a throwaway `HOME`.
- Never put a secret value in a file: see "Secrets" in [AGENTS.md](./AGENTS.md).
