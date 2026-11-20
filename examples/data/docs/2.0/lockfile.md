# Lock file

## The lock file {#lockfile}

The lock file is `.sablefile/lock.json`, a JSON document. It records a format string, `"2.0"`, and one entry for each generated file with its SHA-256 hash and mode:

```
{
  "format": "2.0",
  "files": {
    "README.md": {"sha256": "<64 hex digits>", "mode": "0644"}
  }
}
```

The file has no timestamps, so syncing the same content again produces an identical file. Do not edit it by hand. An older `sablefile.lock` is handled as described in lock-migration.

## File modes in the lock {#lock-mode}

Version 2.0 records each generated file's mode, the Unix permission bits such as `0644`, in `.sablefile/lock.json`, as 1.1 does. check compares only the hash, so a change to the mode alone is not reported as drift. When a lock file is migrated from `sablefile.lock`, the mode is kept where the old file has one; see lock-migration.

## Migrating an older lock file {#lock-migration}

Version 2.0 keeps its lock file in `.sablefile/lock.json`. When a 2.0 command finds an older `sablefile.lock` and no `.sablefile/lock.json`, it reads the old file and prints a warning that names both files. If the command writes files, as `sync --apply` does, it also writes `.sablefile/lock.json` with each entry's SHA-256 hash, and keeps the mode where the old file has one. A command that writes nothing leaves both files as they are. sablefile does not delete `sablefile.lock`; remove it yourself once the new file exists. After migration, 2.0 reads only the new file.
