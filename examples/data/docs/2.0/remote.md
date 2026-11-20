# Remote templates

## Remote templates {#remote-templates}

The `template` key can name an https URL instead of a path in the project. sablefile fetches the URL when a command renders the template, and it renders the fetched text in the same way as a local file. A remote template is not copied into the project. A change on the server changes what the next sync writes and what diff shows, but check does not see it.

## Retries for remote fetches {#remote-retries}

When a fetch of a remote template fails, sablefile retries it up to 5 times by default before it gives up. Use `--retries N` to set another count; see retries-flag. Each retry is a new request for the same URL. Retries apply to `sync` and `diff`. `check` does not fetch anything and never retries.

## When a remote fetch fails {#remote-fetch-failure}

If a remote template still cannot be fetched after the last retry, the command stops with an error that names the URL, and it exits with status 1. Targets that were not written keep their earlier lock entries. Check the URL and your network connection, then run the command again.

## The `--retries` flag {#retries-flag}

`--retries N` sets how many times `sync` and `diff` retry a failed fetch of a remote template, in place of the default of 5. N is a whole number, and 0 means no retries. The flag applies only to the command it is given to. Use it on a slow or unreliable network, where a higher count gives the server more chances to answer.
