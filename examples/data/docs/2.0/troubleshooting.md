# Troubleshooting

## Investigate unexpected drift {#troubleshoot-drift}

If check reports `DRIFT` for a file you did not mean to edit, look at the change before you act. Run `sablefile diff` to see how the file differs from its template. If the change is wanted, move it into the template so that the next sync keeps it, then run `sablefile sync --apply`. If the change is not wanted, revert the file and run `sablefile check` again.

## The command is not found {#troubleshoot-command-not-found}

If the shell reports that `sablefile` is not found, the command is not installed in the environment that is active. Run `python3 -m pip show sablefile` in the same shell. If pip reports nothing, install the archive again. If pip reports a location but the command still does not run, the scripts folder of that environment is not on your path. Once the fault is fixed, run `sablefile --version`; see install-check-version.
