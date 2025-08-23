# File: AI-testing/orchestrator/Services/report_generator.py

- Size: 8876 bytes
- Kind: text
- SHA256: 98387b214c901a78ac73018f8332090e6d32acc6cf4053d6ad0500810910840c

## Python Imports

```
datetime, jinja2, json, models, os, pathlib, typing
```

## Head (first 60 lines)

```
"""Report generation service"""

import os
import json
from datetime import datetime
from pathlib import Path
from typing import Optional
import jinja2

from models import get_db, Run, Finding, ReportFormat

class ReportGenerator:
    """Generate security reports in various formats"""
    
    def __init__(self):
        self.template_dir = Path("templates")
        self.output_dir = Path(os.getenv("EVIDENCE_DIR", "/tmp/evidence")) / "reports"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Setup Jinja2
        self.jinja_env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(str(self.template_dir))
        )
    
    async def generate(self, run_id: str, format: ReportFormat) -> str:
        """Generate report for a run"""
        
        # Get run data
        report_data = self._get_report_data(run_id)
        
        if format == ReportFormat.JSON:
            return self._generate_json(run_id, report_data)
        elif format == ReportFormat.HTML:
            return self._generate_html(run_id, report_data)
        elif format == ReportFormat.MARKDOWN:
            return self._generate_markdown(run_id, report_data)
        elif format == ReportFormat.PDF:
            # PDF generation would require additional libraries like weasyprint
            html_path = self._generate_html(run_id, report_data)
            return self._html_to_pdf(html_path)
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def _get_report_data(self, run_id: str) -> dict:
        """Gather all data for report"""
        with get_db() as db:
            run = db.query(Run).filter(Run.id == run_id).first()
            if not run:
                raise ValueError(f"Run not found: {run_id}")
            
            findings = db.query(Finding).filter(Finding.run_id == run_id).all()
            
            # Build report data
            data = {
                "report_date": datetime.utcnow().isoformat(),
                "run": {
                    "id": run.id,
                    "status": run.status.value,
                    "started_at": run.started_at.isoformat() if run.started_at else None,
                    "completed_at": run.completed_at.isoformat() if run.completed_at else None,
```

## Tail (last 60 lines)

```
"""
        
        with open(output_path, 'w') as f:
            f.write(md_content)
        
        return str(output_path)
    
    def _html_to_pdf(self, html_path: str) -> str:
        """Convert HTML to PDF (placeholder - requires weasyprint or similar)"""
        # This would require additional setup
        # For now, just return the HTML path
        return html_path
    
    def _get_default_html_template(self) -> str:
        """Default HTML template"""
        return """<!DOCTYPE html>
<html>
<head>
    <title>Security Test Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        h1 { color: #333; }
        .critical { color: #d32f2f; }
        .high { color: #f57c00; }
        .medium { color: #fbc02d; }
        .low { color: #388e3c; }
        .info { color: #1976d2; }
        table { width: 100%; border-collapse: collapse; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #f2f2f2; }
    </style>
</head>
<body>
    <h1>Security Test Report</h1>
    
    <h2>Summary</h2>
    <p><strong>Date</strong>: {{ report_date }}</p>
    <p><strong>Engagement</strong>: {{ engagement.name }}</p>
    
    <h2>Findings Statistics</h2>
    <ul>
        <li class="critical">Critical: {{ statistics.critical }}</li>
        <li class="high">High: {{ statistics.high }}</li>
        <li class="medium">Medium: {{ statistics.medium }}</li>
        <li class="low">Low: {{ statistics.low }}</li>
        <li class="info">Informational: {{ statistics.info }}</li>
    </ul>
    
    <h2>Detailed Findings</h2>
    {% for finding in findings %}
    <div>
        <h3 class="{{ finding.severity }}">{{ finding.title }}</h3>
        <p><strong>Severity</strong>: {{ finding.severity }}</p>
        <p><strong>Component</strong>: {{ finding.component }}</p>
        <p>{{ finding.description }}</p>
    </div>
    <hr>
    {% endfor %}
</body>
</html>"""
```

