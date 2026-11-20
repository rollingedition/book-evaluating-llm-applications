# Quickstart

## Create the configuration file {#quickstart-init}

Change to your project folder and run `sablefile init`. The command writes `sablefile.toml` into the folder. The file has a `[values]` table with one entry, `project`, set to the name of the folder. Open the file and check it. Every later command reads this file, so it is the first place to look when the output is not what you expect.

## Add a template and a file entry {#quickstart-edit-template}

Create a template file, for example `templates/README.md`, with `${project}` where the project name should appear. Then add a `[[file]]` table to `sablefile.toml`:

```
[[file]]
template = "templates/README.md"
target = "README.md"
```

Both paths are relative to the project folder. The target is the file that sync writes.

## Run the first sync {#quickstart-first-sync}

Run `sablefile sync`. Without a flag it prints the plan and writes nothing, so you can read what would change. When the plan is right, run `sablefile sync --apply`. It writes each target and records the SHA-256 hash and mode of each file in `.sablefile/lock.json`. Open `README.md` and check that the project name appears where the placeholder was.

## Check for drift {#quickstart-check}

Run `sablefile check` after a sync. If no output appears, no generated file has drifted since the last sync. To see what drift looks like, open a generated file, change one line, and run the check again. The check prints `DRIFT` and the path of the file. Revert your edit to clear the message. The exit status for drift is described in check-exit-status.
