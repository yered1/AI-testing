# File: AI-testing/.git/hooks/applypatch-msg.sample

- Size: 478 bytes
- Kind: text
- SHA256: 0223497a0b8b033aa58a3a521b8629869386cf7ab0e2f101963d328aa62193f7

## Head (first 60 lines)

```
#!/bin/sh
#
# An example hook script to check the commit log message taken by
# applypatch from an e-mail message.
#
# The hook should exit with non-zero status after issuing an
# appropriate message if it wants to stop the commit.  The hook is
# allowed to edit the commit message file.
#
# To enable this hook, rename this file to "applypatch-msg".

. git-sh-setup
commitmsg="$(git rev-parse --git-path hooks/commit-msg)"
test -x "$commitmsg" && exec "$commitmsg" ${1+"$@"}
:
```

