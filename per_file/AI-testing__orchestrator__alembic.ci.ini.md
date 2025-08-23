# File: AI-testing/orchestrator/alembic.ci.ini

- Size: 698 bytes
- Kind: text
- SHA256: 7f04d081e3cdad4ea8ca82ca1361c45c8c2e1911641f1824607a9d608549f266

## Head (first 60 lines)

```
[alembic]
script_location = alembic
prepend_sys_path = .
# default; will be overridden by env var if present
sqlalchemy.url = postgresql+psycopg2://postgres:postgres@db:5432/aitest

# Logging config (avoid KeyError: formatter_generic)
[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console

[logger_sqlalchemy]
level = WARN
handlers = console
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers = console
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
```

