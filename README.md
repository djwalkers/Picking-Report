
# Picking Performance Dashboard

A Streamlit app to visualize warehouse picking performance.

## Features

- Upload a CSV performance report
- Filter by user and workstation
- Visual dashboards with Plotly
- Download filtered data

## How to Run

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Example CSV Format

| Date               | Username          | Workstations | SourceTotes | DestinationTotes | TotalRefills |
|--------------------|-------------------|--------------|-------------|------------------|---------------|
| 25 Mar 2025 15:00  | JOHN DOE          | GTP-2-01     | 10          | 20               | 30            |

