# File: AI-testing/.git/hooks/pre-merge-commit.sample

- Size: 416 bytes
- Kind: text
- SHA256: d3825a70337940ebbd0a5c072984e13245920cdf8898bd225c8d27a6dfc9cb53

## Head (first 60 lines)

```
#!/bin/sh
#
# An example hook script to verify what is about to be committed.
# Called by "git merge" with no arguments.  The hook should
# exit with non-zero status after issuing an appropriate message to
# stderr if it wants to stop the merge commit.
#
# To enable this hook, rename this file to "pre-merge-commit".

. git-sh-setup
test -x "$GIT_DIR/hooks/pre-commit" &&
        exec "$GIT_DIR/hooks/pre-commit"
:
```

