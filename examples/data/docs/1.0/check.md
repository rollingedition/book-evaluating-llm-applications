# Check

## What check reports {#check-command}

`sablefile check` reads the lock file and hashes each file that the lock lists. For each file whose hash differs from its entry in the lock, it prints `DRIFT` and the path. Files whose hashes match print nothing. check does not fetch remote templates and does not render templates, so it works without a network connection. Drift means a change to a generated file, not a change to a template; see drift-meaning.

## Exit status of check {#check-exit-status}

When check finds a drifted file, it prints `DRIFT` and the path, and exits with status 0. Because the status is 0 even when files have drifted, a script cannot detect drift from the exit status in this version. Read the printed lines instead. If check itself cannot run, for example because the lock file cannot be read, it prints an error message.

## What drift means {#drift-meaning}

A file has drifted when its current content no longer matches the SHA-256 hash that sync recorded for it in the lock file. In practice, the generated file was edited or replaced after the last sync. A change to a template is not drift. The generated file still matches the lock until sync runs again, so check prints nothing for it. To see how a template differs from its target, use diff.
