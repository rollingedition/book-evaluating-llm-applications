# Sync

## What sync does by default {#sync-default}

`sablefile sync` renders each `[[file]]` template and writes the result to its target. With no flag, sync writes files. Each written file is then recorded in the lock file, `sablefile.lock`. To see the changes before they are written, run `sablefile diff`, which shows the same differences without writing anything.

## Folders for targets {#sync-create-dirs}

If the folder of a target does not exist, sync creates it before it writes the file. A target such as `docs/guide/index.md` therefore needs no setup. sync never removes a folder, so empty folders you leave behind stay where they are.

## Lock entries after sync {#sync-lock-update}

After sync writes a target, it records that file's SHA-256 hash and mode in the lock file, `sablefile.lock`. Files that sync did not write keep their earlier entries. The lock file is how check finds drift, so run sync after each change you intend to keep. Commit the lock file with the rest of the project if you use version control.

## Exit status of sync {#sync-exit-status}

sync exits with status 0 when it finishes. It exits with status 1 when it cannot finish, for example when a template file is missing or a remote template cannot be fetched. The error message names the file that caused the failure. A status of 0 shows that sync completed, not that the generated text is what you want, so open the generated files to check them.
