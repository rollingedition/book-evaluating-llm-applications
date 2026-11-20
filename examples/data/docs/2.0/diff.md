# Diff

## What diff shows {#diff-command}

`sablefile diff` renders each `[[file]]` template and prints a unified diff between the rendered text and the file on disk. Lines that match are not printed. diff shows what sync would change in the file's content. It does not write any file and does not change the lock file. Use it before a sync when you want to review changes.

## Which files diff covers {#diff-scope}

diff covers every `[[file]]` table in `sablefile.toml`, except targets that the ignore file excludes; see ignore-file. It does not read files that are not listed in the configuration file, so a file you added by hand is never compared. diff fetches remote templates in the same way as sync, and it retries failed fetches as described in remote-retries. Output follows the order of the `[[file]]` tables.
