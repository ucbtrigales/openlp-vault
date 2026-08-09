# Contributing to OpenLP Vault

English | [Español](CONTRIBUTING.es.md)

## License of contributions

OpenLP Vault is licensed under `GPL-3.0-or-later`.

By submitting a contribution, you certify that you have the right to submit
it and agree that it is provided under the GNU General Public License,
version 3 or, at the recipient's option, any later version. No copyright
assignment is required: contributors retain copyright in their work.

Do not submit code, translations, images, documentation, or other material
that cannot be distributed under `GPL-3.0-or-later`. Clearly identify
third-party material and its license in the contribution.

## Authorship

Use your own identity in Git commits and preserve existing authorship and
copyright notices. The Git history is the project's primary contribution
record. Do not rewrite another contributor's authorship.

## Before submitting

Run the automated checks:

```bash
.venv/bin/python -m pytest
git diff --check
```

Keep English and Spanish documentation synchronized when behavior or user
instructions change.
