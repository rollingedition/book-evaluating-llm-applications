# Install

## Install from the archive {#install-archive}

Download the archive for the version you want, named `sablefile-2.0.tar.gz`, from `https://downloads.example.org/sablefile/`. Then install it with pip:

```
python3 -m pip install sablefile-2.0.tar.gz
```

pip installs the `sablefile` command into the Python environment that is active in your shell. To keep the tool with one project, create a virtual environment first and install into it. Use the archive for the version whose docs you are reading, because commands and their behaviour differ between versions.

## Check the installed version {#install-check-version}

Run `sablefile --version` to see the installed version. The output has the form `sablefile 2.0`. Check that the number matches the docs you are reading, since the docs for one version do not describe another. If the shell reports that the command is not found, the archive went into a different Python environment from the one you are using. Activate that environment and run the check again.

## Remove sablefile {#install-uninstall}

To remove sablefile, run `python3 -m pip uninstall sablefile`. This removes the `sablefile` command and its package. It does not change your project. The configuration file, templates, generated files and lock file stay where they are. Remove them yourself when you no longer need them.

## Upgrade to a newer version {#install-upgrade}

To move to a newer version, install its archive with `--upgrade`, for example `python3 -m pip install --upgrade sablefile-NEWER.tar.gz`. Before you upgrade, read the changelog in the newer version's folder. It lists each section whose behaviour changed, by section ID. Installing a new version does not write any project file.

Version 2.0 moves the lock file to a new place. The first 2.0 command that reads an older lock file handles it as described in lock-migration.
