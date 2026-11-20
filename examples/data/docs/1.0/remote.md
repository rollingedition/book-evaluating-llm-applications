# Remote templates

## Remote templates {#remote-templates}

The `template` key can name an https URL instead of a path in the project. sablefile fetches the URL when a command renders the template, and it renders the fetched text in the same way as a local file. A remote template is not copied into the project. A change on the server changes what the next sync writes and what diff shows, but check does not see it.

## Retries for remote fetches {#remote-retries}

When a fetch of a remote template fails, sablefile retries it up to 3 times before it gives up. The count is fixed in 1.0, and no flag or setting changes it. Each retry is a new request for the same URL. Retries apply to `sync` and `diff`. `check` does not fetch anything and never retries.

## When a remote fetch fails {#remote-fetch-failure}

If a remote template still cannot be fetched after the last retry, the command stops with an error that names the URL, and it exits with status 1. Targets that were not written keep their earlier lock entries. Check the URL and your network connection, then run the command again.
