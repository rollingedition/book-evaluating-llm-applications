# Changelog

Changes from 1.0 to 1.1. Section IDs are listed as they appear in version 1.1. Sections that differ only in the version number shown in an example are not listed.

## Added

- `lock-mode`: New. Records each generated file's mode in the lock file.

## Changed

- `check-exit-status`: check exits with status 1 when a file has drifted (1.0 exits with status 0).
- `ignore-recursive`: Describes `**`. The 1.0 text states that it is not supported.
- `ignore-syntax`: Adds `**` to the glob syntax.
- `lockfile`: Lock lines gain a mode field.
- `quickstart-first-sync`: Output description includes the file mode.
- `remote-retries`: Retry count is 5 (was 3).
- `sync-lock-update`: Lock entries include the file mode.

## Removed

- None.
