# Ignore file

## The ignore file {#ignore-file}

The ignore file, `.sablefileignore`, sits in the project root and lists paths that sablefile must leave alone. Put one entry on each line. Blank lines are ignored. sync does not write an ignored target, check and diff skip it, and it gets no entry in the lock file. A project without an ignore file ignores nothing. The syntax of each entry depends on the version; see ignore-syntax.

## Syntax of ignore entries {#ignore-syntax}

In 1.0, each entry is a shell glob, such as `*.log`, matched against the target path. A target is ignored when any entry matches it. Shell globs have no negation, so `!` has no special meaning in 1.0. Use one entry for each pattern you need. The `**` pattern is not available in this version; see ignore-recursive.

## The double-star pattern {#ignore-recursive}

Version 1.0 does not support `**`. Shell globs do not match across folders, so to cover more than one level you need an entry for each level, such as `docs/*.tmp` and `docs/*/*.tmp`. The first pattern ignores only the files directly in `docs`, and the second ignores files one folder deeper. Deeper folders need their own entries, and a file in a folder deeper than your last entry is still generated.
