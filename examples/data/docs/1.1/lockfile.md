# Lock file

## The lock file {#lockfile}

The lock file is `sablefile.lock` in the project root. It holds one line for each generated file: the SHA-256 hash of the file's content, then the file's mode, then the path. sync writes it, and check reads it. The format is plain text. Do not edit the lock file by hand. The mode field is described in lock-mode.

## File modes in the lock {#lock-mode}

Version 1.1 records each generated file's mode, the Unix permission bits such as `0644`, in the lock file. sync records the mode of each file it writes. check compares only the hash, so a change to the mode alone is not reported as drift in this version.
