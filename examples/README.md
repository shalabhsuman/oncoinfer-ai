# Example Data

Place representative request/response artifacts here for documentation and demos.

Pipeline example files:

- `examples/input/sample_request.json` - API request payload (JSON input)
- `examples/intermediate/model_input_features.csv` - parsed model input features
- `examples/intermediate/model_output_predictions.csv` - raw model output table
- `examples/output/sample_response.json` - final API response payload

Keep examples de-identified and safe for public sharing.

## De-identification Checklist

Before committing examples, remove or replace:

- Patient IDs, MRNs, accession numbers, encounter/order IDs
- Sample IDs that map back to internal systems
- Dates, timestamps, locations, provider names, free-text notes
- Any direct or indirect identifiers in nested metadata fields

Use synthetic placeholders like `SAMPLE_DEMO_001`, `PATIENT_DEMO_001`, and scrub all UUID-like values unless they are generated demo values.
