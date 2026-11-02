# GRC Maturity Scorer — NIST CSF 2.0

A small, dependency-free Python tool that turns a NIST CSF 2.0 self-assessment into a maturity summary: weighted score per Function (Govern, Identify, Protect, Detect, Respond, Recover), gap against target, and a prioritized list of categories to improve.

Built as a personal side project to show how routine GRC assessment work can be automated. It contains **no client data** — the sample file is fictional.

## Why

In maturity assessments, the scoring and roll-up step is repetitive and error-prone when done by hand in spreadsheets. Automating it makes results reproducible, lets reviewers work asynchronously on the output, and keeps the focus on judgment and remediation planning.

## Usage

```bash
python csf_score.py sample_assessment.csv          # text summary
python csf_score.py sample_assessment.csv --json   # JSON for dashboards
python -m unittest -v                              # run tests
```

Input CSV columns: `function` (GV/ID/PR/DE/RS/RC), `category` (e.g. `GV.OC`), `current` and `target` (0–4), optional `weight`.

## Example output

```
NIST CSF 2.0 maturity summary
================================
Overall: current 1.75 / target 3.02 (gap 1.27)

Function      Cat.  Current  Target   Gap
GV Govern        3     1.79    3.00  1.21
ID Identify      2     1.40    3.00  1.60
PR Protect       3     2.21    3.21  1.00
DE Detect        1     1.50    3.00  1.50
RS Respond       1     2.00    3.00  1.00
RC Recover       1     1.00    2.50  1.50

Top 5 priorities (by weighted gap):
  - ID.AM: gap 2.00 (weighted 3.00)
  - DE.CM: gap 1.50 (weighted 2.25)
  - GV.RM: gap 1.50 (weighted 2.25)
  - PR.AA: gap 1.00 (weighted 1.50)
  - RC.RP: gap 1.50 (weighted 1.50)
```

## Notes

- Scores use a 0–4 scale, which you can map to your own maturity model.
- Weights let you reflect business criticality per category.
- Input is validated: unknown functions, out-of-range scores and categories outside their function are rejected.

## License

MIT
