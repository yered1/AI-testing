# File: AI-testing/orchestrator/ui/templates/base.html

- Size: 626 bytes
- Kind: text
- SHA256: 27ef76522cbbe29f21ec2b51ec146f071f3cb1aba9c7c543d891dde3d6285e50

## Head (first 60 lines)

```
<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>AI Testing Orchestrator</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <link href="/ui/static/app.css" rel="stylesheet">
</head>
<body>
  <header>
    <h1>AI Testing Orchestrator</h1>
    <nav>
      <a href="/ui">Home</a>
      <a href="/ui/new">New Engagement</a>
      <a href="/ui/admin">Admin</a>
    </nav>
  </header>
  <main>
    {% block content %}{% endblock %}
  </main>
  <footer>
    <small>v0.9.7 UI — uses your existing API & auth</small>
  </footer>
  <script src="/ui/static/app.js"></script>
</body>
</html>
```

