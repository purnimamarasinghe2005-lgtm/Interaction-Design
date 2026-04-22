# ResetU Insights Backend Prototype (Professional Version)

This version is designed to look more academic and transparent.

## What it does
- Reads raw check-in answers from `checkins_raw.csv`
- Converts qualitative answers into numeric scores
- Calculates a daily wellbeing score out of 10
- Builds a weekly summary
- Outputs:
  - overall wellbeing
  - classification
  - average screen time
  - best focus time
  - peak notifications
  - reflection
  - daily breakdown
  - chart data

## How to run
```bash
python3 insights_backend.py
```

## Why the JSON file already contains results
`insights_output.json` is not input data.
It is the generated output file created after the calculations are performed.
