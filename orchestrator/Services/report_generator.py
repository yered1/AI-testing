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
                    "duration": (run.completed_at - run.started_at).total_seconds() if run.completed_at and run.started_at else None
                },
                "engagement": {
                    "id": run.plan.engagement.id,
                    "name": run.plan.engagement.name,
                    "type": run.plan.engagement.type.value,
                    "scope": run.plan.engagement.scope
                },
                "plan": {
                    "id": run.plan.id,
                    "name": run.plan.name,
                    "tests": [
                        {
                            "id": test.test_id,
                            "name": test.name,
                            "parameters": test.parameters
                        }
                        for test in run.plan.tests
                    ]
                },
                "statistics": {
                    "total_findings": len(findings),
                    "critical": len([f for f in findings if f.severity.value == "critical"]),
                    "high": len([f for f in findings if f.severity.value == "high"]),
                    "medium": len([f for f in findings if f.severity.value == "medium"]),
                    "low": len([f for f in findings if f.severity.value == "low"]),
                    "info": len([f for f in findings if f.severity.value == "info"])
                },
                "findings": [
                    {
                        "id": f.id,
                        "title": f.title,
                        "description": f.description,
                        "severity": f.severity.value,
                        "status": f.status.value,
                        "type": f.vulnerability_type,
                        "component": f.affected_component,
                        "evidence": f.evidence,
                        "remediation": f.remediation,
                        "cvss_score": f.cvss_score,
                        "cvss_vector": f.cvss_vector,
                        "references": f.references
                    }
                    for f in sorted(findings, key=lambda x: ["critical", "high", "medium", "low", "info"].index(x.severity.value))
                ]
            }
            
            return data
    
    def _generate_json(self, run_id: str, data: dict) -> str:
        """Generate JSON report"""
        output_path = self.output_dir / f"report_{run_id}.json"
        
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        
        return str(output_path)
    
    def _generate_html(self, run_id: str, data: dict) -> str:
        """Generate HTML report"""
        output_path = self.output_dir / f"report_{run_id}.html"
        
        # Create default template if not exists
        template_path = self.template_dir / "report.html"
        if not template_path.exists():
            template_path.parent.mkdir(parents=True, exist_ok=True)
            template_path.write_text(self._get_default_html_template())
        
        template = self.jinja_env.get_template("report.html")
        html_content = template.render(**data)
        
        with open(output_path, 'w') as f:
            f.write(html_content)
        
        return str(output_path)
    
    def _generate_markdown(self, run_id: str, data: dict) -> str:
        """Generate Markdown report"""
        output_path = self.output_dir / f"report_{run_id}.md"
        
        md_content = f"""# Security Test Report

**Date**: {data['report_date']}  
**Run ID**: {data['run']['id']}  
**Status**: {data['run']['status']}

## Engagement Details
- **Name**: {data['engagement']['name']}
- **Type**: {data['engagement']['type']}
- **Targets**: {', '.join(data['engagement']['scope'].get('targets', []))}

## Test Execution
- **Started**: {data['run']['started_at']}
- **Completed**: {data['run']['completed_at']}
- **Duration**: {data['run']['duration']} seconds

## Findings Summary
- **Critical**: {data['statistics']['critical']}
- **High**: {data['statistics']['high']}
- **Medium**: {data['statistics']['medium']}
- **Low**: {data['statistics']['low']}
- **Informational**: {data['statistics']['info']}

## Detailed Findings

"""
        
        for finding in data['findings']:
            md_content += f"""### {finding['severity'].upper()}: {finding['title']}

**Component**: {finding.get('component', 'N/A')}  
**Type**: {finding.get('type', 'N/A')}  

**Description**:  
{finding.get('description', 'No description available')}

**Remediation**:  
{finding.get('remediation', 'No remediation provided')}

---

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