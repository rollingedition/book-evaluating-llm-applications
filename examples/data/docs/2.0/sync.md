# Sync

## What sync does by default {#sync-default}

`sablefile sync` renders each `[[file]]` template and compares the result with its target. With no flag, sync prints the plan and writes nothing. `--apply` writes the files and updates the lock file, `.sablefile/lock.json`. Run `sablefile sync` to preview and `sablefile sync --apply` to write. The plan lines are described in apply-flag.

## Folders for targets {#sync-create-dirs}

If the folder of a target does not exist, sync creates it before it writes the file, and only when you pass `--apply`, because a plain sync writes nothing. A target such as `docs/guide/index.md` therefore needs no setup. sync never removes a folder, so empty folders you leave behind stay where they are.

## Lock entries after sync {#sync-lock-update}

After sync writes a target, it records that file's SHA-256 hash and mode in the lock file, `.sablefile/lock.json`. Files that sync did not write keep their earlier entries. The lock file is how check finds drift, so run sync after each change you intend to keep. Commit the lock file with the rest of the project if you use version control.

## Exit status of sync {#sync-exit-status}

sync exits with status 0 when it finishes. It exits with status 1 when it cannot finish, for example when a template file is missing or a remote template cannot be fetched. The error message names the file that caused the failure. A status of 0 shows that sync completed, not that the generated text is what you want, so open the generated files to check them.

## The `--apply` flag {#apply-flag}

`--apply` tells sync to write the files. Without it, sync only prints the plan. Each plan line starts with an action: `create` for a target that does not exist, `update` for a target whose content would change, and `unchanged` for a target that already matches its template. Nothing is written in the plan step, not even the lock file. With `--apply`, sync writes the targets, creates folders as needed and updates `.sablefile/lock.json`.
