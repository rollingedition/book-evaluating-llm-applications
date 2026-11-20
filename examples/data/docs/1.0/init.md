# Init

## What init creates {#init-command}

`sablefile init` creates `sablefile.toml` in the folder where you run it, or in the folder you name. The new file has a `[values]` table with one entry, `project`, set to the folder name, and no `[[file]]` tables. init stops with an error if `sablefile.toml` already exists, so it never overwrites your configuration. It writes no other file.

## Choose the folder for init {#init-directory}

To create the configuration in another folder, give the folder as an argument: `sablefile init path/to/folder`. The folder must already exist. Without an argument, init uses the current folder. A relative path is taken from the folder you run the command in, so check the location after you run init.
