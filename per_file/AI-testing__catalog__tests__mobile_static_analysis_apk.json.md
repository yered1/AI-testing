# File: AI-testing/catalog/tests/mobile_static_analysis_apk.json

- Size: 618 bytes
- Kind: text
- SHA256: 909f6db260287bc5e548a7262a84e4e31f96330ff31a6b5affee1011299ce528

## Head (first 60 lines)

```
{
  "id": "mobile.static.analysis.apk",
  "name": "Mobile Static (APK)",
  "category": "Mobile",
  "risk_tier": "recon",
  "description": "Static analysis for Android APKs; manifest, SSL, secrets.",
  "prerequisites": [],
  "exclusive_with": [],
  "requires": {
    "agents": [
      "kali_gateway"
    ],
    "capabilities": [],
    "inputs": [
      "apk_file"
    ]
  },
  "optional_inputs": [],
  "estimator": {
    "time_per_host_sec": 120,
    "cost_units": 4
  },
  "outputs": [
    "mobile_findings"
  ],
  "tool_adapter": "mobile-apk-analyzer@0.2.0",
  "evidence_retention": "standard",
  "policy_tags": []
}
```

