# Ignore file

## The ignore file {#ignore-file}

The ignore file, `.sablefileignore`, sits in the project root and lists paths that sablefile must leave alone. Put one entry on each line. Blank lines are ignored. sync does not write an ignored target, check and diff skip it, and it gets no entry in the lock file. A project without an ignore file ignores nothing. The syntax of each entry depends on the version; see ignore-syntax.

## Syntax of ignore entries {#ignore-syntax}

In 2.0, entries use gitignore syntax. A line such as `*.log` matches at any depth. A trailing `/` makes an entry match only directories. A leading `!` negates an earlier match, so `!keep.log` brings back a file that an earlier line excluded. Lines that start with `#` are comments. The shell glob rules of 1.x no longer apply.

## The double-star pattern {#ignore-recursive}

Version 2.0 supports `**` as gitignore does. It matches zero or more folders, so `docs/**/*.tmp` matches `docs/a.tmp` and `docs/x/y/a.tmp`. A leading `**/` matches at any depth. The `**` pattern can be combined with `!` negation and with a trailing `/`, as described in ignore-syntax.
