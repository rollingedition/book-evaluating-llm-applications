# Ignore file

## The ignore file {#ignore-file}

The ignore file, `.sablefileignore`, sits in the project root and lists paths that sablefile must leave alone. Put one entry on each line. Blank lines are ignored. sync does not write an ignored target, check and diff skip it, and it gets no entry in the lock file. A project without an ignore file ignores nothing. The syntax of each entry depends on the version; see ignore-syntax.

## Syntax of ignore entries {#ignore-syntax}

In 1.1, each entry is a glob, as in 1.0, such as `*.log`, matched against the target path. Version 1.1 also accepts `**`, which matches across folders; see ignore-recursive. A target is ignored when any entry matches it. Negation is not available in 1.1.

## The double-star pattern {#ignore-recursive}

Version 1.1 adds `**`. It matches zero or more folders, so `docs/**/*.tmp` matches `docs/a.tmp`, `docs/x/a.tmp` and `docs/x/y/a.tmp`. Use one `**` entry in place of a list of per-level entries. Because it covers any depth, one entry stays correct when a folder tree grows deeper, which a list of per-level entries does not.
