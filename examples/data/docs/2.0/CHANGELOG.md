# Changelog

Changes from 1.1 to 2.0. Section IDs are listed as they appear in version 2.0. Sections that differ only in the version number shown in an example are not listed.

## Added

- `apply-flag`: New. Describes the `--apply` flag and the plan lines.
- `lock-migration`: New. Describes the migration of `sablefile.lock`.
- `no-fail-flag`: New. Describes the `--no-fail` flag.
- `retries-flag`: New. Describes the `--retries` flag.

## Changed

- `check-exit-status`: Exit status is 1 on drift. `--no-fail` gives 0.
- `config-values`: Example uses `${project}`.
- `glossary-terms`: Placeholder syntax in the glossary is `${name}`.
- `ignore-recursive`: `**` follows gitignore rules.
- `ignore-syntax`: Entries use gitignore syntax in place of shell globs.
- `install-upgrade`: Adds a note on the lock file move.
- `lock-mode`: Mode is recorded in the new lock file.
- `lockfile`: The lock file moves to `.sablefile/lock.json`, in JSON form, with no timestamps.
- `placeholders`: Syntax changes to `${name}`. The double-brace form is an error.
- `quickstart-edit-template`: Placeholder syntax changes to `${name}`.
- `quickstart-first-sync`: Sync prints the plan. `--apply` writes the files.
- `remote-retries`: Default is 5 retries. `--retries N` sets another count.
- `sync-create-dirs`: Folders are created only with `--apply`.
- `sync-default`: With no flag, sync prints the plan and writes nothing. `--apply` writes (1.1 writes files with no flag).
- `sync-lock-update`: The lock file is `.sablefile/lock.json`.
- `troubleshoot-drift`: The sync command needs `--apply`.

## Removed

- None.
