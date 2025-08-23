# File: AI-testing/.git/hooks/pre-applypatch.sample

- Size: 424 bytes
- Kind: text
- SHA256: e15c5b469ea3e0a695bea6f2c82bcf8e62821074939ddd85b77e0007ff165475

## Head (first 60 lines)

```
#!/bin/sh
#
# An example hook script to verify what is about to be committed
# by applypatch from an e-mail message.
#
# The hook should exit with non-zero status after issuing an
# appropriate message if it wants to stop the commit.
#
# To enable this hook, rename this file to "pre-applypatch".

. git-sh-setup
precommit="$(git rev-parse --git-path hooks/pre-commit)"
test -x "$precommit" && exec "$precommit" ${1+"$@"}
:
```

