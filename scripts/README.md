# Scripts

Collection, validation, cleaning, and chart-generation scripts belong here. Scripts should be rerunnable, document their inputs and outputs, and avoid embedding credentials.

The report entry point is:

```bash
python3 scripts/build_gilligan_report.py
```

It reads the canonical yearly processed catalogs, writes derived metrics to `reports/gilligan_report_metrics.json`, and writes the finished PDF to `output/pdf/`.
