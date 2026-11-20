# Glossary

## Terms used in these docs {#glossary-terms}

- **Config file**: `sablefile.toml`, the configuration of a project.
- **Drift**: a change to a generated file after the last sync. See drift-meaning.
- **Ignore file**: `.sablefileignore`, the list of paths that sablefile leaves alone. See ignore-file.
- **Lock file**: the file that records the hash of each generated file as sync last wrote it. See lockfile.
- **Placeholder**: a name in a template that sync replaces with a value. In this version it is written `${project}`.
- **Target**: the file that sync writes, named by the `target` key of a `[[file]]` table.
- **Template**: the file that sync reads, named by the `template` key. It can be a URL.
- **Value**: a string in the `[values]` table of the config file.
