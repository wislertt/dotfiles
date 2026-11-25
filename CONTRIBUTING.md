# Contributing

- Standards: [AGENTS.md](./AGENTS.md) holds this repo's conventions (four homes, secrets, bake verbs, four times, layout).
- Vocabulary: [GLOSSARY.md](./GLOSSARY.md). Decisions and their reasons: [docs/adr/](./docs/adr/).
- A new bake command is a new mixin in `src/python/commands/`; its pure logic goes in `src/python/core/`, and the mixin is added to the bakebook in `src/python/bakefile.py`. See "Layout and commands" in [AGENTS.md](./AGENTS.md).
- Run `bake lint` before committing. `bake test` runs the unit tests and `bake test-integration` runs the slow ones in a throwaway `HOME`.
- Never put a secret value in a file: see "Secrets" in [AGENTS.md](./AGENTS.md).
