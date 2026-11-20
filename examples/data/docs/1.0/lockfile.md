# Lock file

## The lock file {#lockfile}

The lock file is `sablefile.lock` in the project root. It holds one line for each generated file: the SHA-256 hash of the file's content, two spaces, then the path. sync writes it, and check reads it. The format is plain text. Do not edit the lock file by hand, because a hand edit can make check report drift for a correct file, or miss a change you did not mean to make.
