import os
from pathlib import Path


class Config:
    BASE_DIR = Path(__file__).resolve().parent.parent
    INTERMEDIATE_DIR = Path(os.getenv("GDD_INTERMEDIATE_DIR", BASE_DIR / "runtime"))
    FEATURES_DIR = INTERMEDIATE_DIR / "features"
    PREDICTIONS_DIR = INTERMEDIATE_DIR / "predictions"
    CLASSIFIER_SCRIPT = BASE_DIR / "libraries" / "run_gdd_single.py"
    PARSE_SCRIPT = BASE_DIR / "libraries" / "parse_dmp_json.py"
    OUTPUT_SCRIPT = BASE_DIR / "libraries" / "write_output_json.py"
