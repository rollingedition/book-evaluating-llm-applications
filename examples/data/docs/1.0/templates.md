# Templates

## Placeholders {#placeholders}

A placeholder is a name in double braces, such as `{{project}}`. When a template is rendered, each placeholder is replaced with the matching string from the `[values]` table in `sablefile.toml`. The name must match a key in `[values]`. Text outside placeholders is copied unchanged.

## How a template is rendered {#template-render}

Rendering reads a template file as text and produces the target content. Every placeholder is replaced by its value, and every other character is kept as written. Values are inserted exactly as they appear in `sablefile.toml`, with no escaping. Rendering does not run code in the template. The same template and the same `[values]` table always produce the same output.

## Where templates live {#templates-location}

Template files are ordinary text files, and they can sit in any folder of the project. The `template` key in a `[[file]]` table gives the path from the project folder. Keep templates under version control with the rest of the project. sablefile reads a template only when a command renders it, so a template that no `[[file]]` table names is never used.
