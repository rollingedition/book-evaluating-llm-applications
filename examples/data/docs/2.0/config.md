# Configuration

## The configuration file {#config-file}

Each project has one configuration file, `sablefile.toml`, in its root folder. It holds the values for the placeholders and the list of files to generate. sablefile reads the file at the start of every command, so a change takes effect on the next command you run. Apart from this file and the ignore file described in ignore-file, sablefile reads no settings from the project folder.

## The values table {#config-values}

The `[values]` table maps names to strings. Each name can be used as a placeholder in a template. For example, `project = "example-service"` fills `${project}` wherever it appears in a template. Values are always strings, so write numbers and other text in quotes. Each name can appear only once in the table, because TOML does not allow a repeated key.

## The file tables {#config-files-table}

Each `[[file]]` table describes one generated file and has two keys. `template` is the path of the template file, or an https URL for a remote template. `target` is the path of the file to write. Both paths are relative to the project folder. A project can have any number of `[[file]]` tables. Each target should appear in only one table. Targets are written in the order the tables appear.
